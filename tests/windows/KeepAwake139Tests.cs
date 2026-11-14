using System;
using System.Collections.Generic;
using ForexDemoLab.KeepAwake139;

namespace ForexDemoLab.KeepAwake139Testing
{
    public sealed class Summary
    {
        public bool Passed;
        public int Tests, Checks;
        public bool NativePowerApiUsed = false;
        public string[] Cases;
    }
    public sealed class FakeClock : IClock
    {
        public long Ticks = 1000, Oversleep;
        public int Reads, Waits, LargestWait, RollbackAt;
        public bool ThrowWait;
        public long NowMs { get { Reads++; return Reads == RollbackAt ? Ticks - 1000 : Ticks; } }
        public void Wait(int milliseconds)
        {
            Waits++; LargestWait = Math.Max(LargestWait, milliseconds);
            if (ThrowWait) throw new InvalidOperationException("invented_wait");
            Ticks += milliseconds + Oversleep;
        }
    }
    public sealed class FakeCancel : ICancellation
    {
        public Func<bool> Test = delegate { return false; };
        public int Reads;
        public bool Requested { get { Reads++; return Test(); } }
    }
    public sealed class FakeBackend : IPowerBackend
    {
        public int PowerCalls, Creates, Sets, Clears, Closes;
        public string FalseAt = "", ThrowAt = "";
        public AcState Initial = AcState.Mains;
        public int LosePowerAt;
        public long CreateCost, SecondPowerCost;
        public FakeClock Clock;
        private bool Step(string operation)
        {
            if (ThrowAt == operation) throw new InvalidOperationException("invented_backend");
            return FalseAt != operation;
        }
        public AcState ReadPower()
        {
            PowerCalls++; Step("power");
            if (Clock != null && PowerCalls == 2) Clock.Ticks += SecondPowerCost;
            return LosePowerAt > 0 && PowerCalls >= LosePowerAt ? AcState.Battery : Initial;
        }
        public bool Create() { Creates++; if (Clock != null) Clock.Ticks += CreateCost; return Step("create"); }
        public bool Set() { Sets++; return Step("set"); }
        public bool Clear() { Clears++; return Step("clear"); }
        public bool Close() { Closes++; return Step("close"); }
    }
    public static class Suite
    {
        private static int checks;
        private static void Check(bool value)
        { checks++; if (!value) throw new InvalidOperationException("keep_awake139_test_assertion"); }
        public static Summary RunAll()
        {
            checks = 0;
            List<string> cases = new List<string>();
            Action<string, Action> test = delegate(string name, Action action)
            {
                try { action(); cases.Add(name); }
                catch (Exception) { throw new InvalidOperationException("keep_awake139_failed_" + name); }
            };
            test("disabled_no_calls", delegate {
                FakeBackend b = new FakeBackend(); FakeClock c = new FakeClock(); FakeCancel x = new FakeCancel();
                Result r = Runner.Run(false, 1000, b, c, x);
                Check(r.Status == "off" && r.ExitCode == 0);
                Check(b.PowerCalls == 0 && b.Creates == 0 && b.Closes == 0 && c.Reads == 0 && x.Reads == 0);
            });
            foreach (long limit in new long[] { 0, -1, Runner.MaxDurationMs + 1, Int64.MaxValue })
            {
                long value = limit;
                test("invalid_duration_" + value, delegate {
                    FakeBackend b = new FakeBackend(); Result r = Runner.Run(true, value, b, new FakeClock(), new FakeCancel());
                    Check(r.Status == "invalid_configuration" && b.PowerCalls == 0 && b.Creates == 0);
                });
            }
            test("exact_deadline_and_release", delegate {
                FakeBackend b = new FakeBackend(); FakeClock c = new FakeClock();
                Result r = Runner.Run(true, 1000, b, c, new FakeCancel());
                Check(r.Status == "deadline" && r.ElapsedMs == 1000 && r.ExitCode == 0);
                Check(b.Creates == 1 && b.Sets == 1 && b.Clears == 1 && b.Closes == 1);
                Check(r.ClearAcknowledged && r.CloseAcknowledged && c.LargestWait <= 250);
            });
            test("maximum_duration_fake_time", delegate {
                FakeClock c = new FakeClock(); Result r = Runner.Run(true, Runner.MaxDurationMs, new FakeBackend(), c, new FakeCancel());
                Check(r.ElapsedMs == Runner.MaxDurationMs && c.Waits == Runner.MaxDurationMs / 250);
                Check(r.SetAcknowledged && r.ClearAcknowledged && r.CloseAcknowledged);
            });
            test("cancellation_before_create", delegate {
                FakeBackend b = new FakeBackend(); FakeCancel x = new FakeCancel { Test = delegate { return true; } };
                Result r = Runner.Run(true, 1000, b, new FakeClock(), x);
                Check(r.Status == "cancelled" && b.PowerCalls == 0 && b.Creates == 0 && b.Closes == 0);
            });
            test("cancellation_after_set", delegate {
                FakeClock c = new FakeClock(); FakeCancel x = new FakeCancel { Test = delegate { return c.Ticks >= 1500; } };
                Result r = Runner.Run(true, 10000, new FakeBackend(), c, x);
                Check(r.Status == "cancelled" && r.ElapsedMs == 500 && r.ClearAcknowledged && r.CloseAcknowledged);
            });
            foreach (AcState power in new AcState[] { AcState.Battery, AcState.Unknown })
            {
                AcState value = power;
                test("initial_power_" + value, delegate {
                    FakeBackend b = new FakeBackend { Initial = value };
                    Result r = Runner.Run(true, 1000, b, new FakeClock(), new FakeCancel());
                    Check(r.Status == "mains_required" && b.Creates == 0 && b.Sets == 0 && b.Closes == 0);
                });
            }
            test("power_lost_before_set", delegate {
                FakeBackend b = new FakeBackend { LosePowerAt = 2 };
                Result r = Runner.Run(true, 1000, b, new FakeClock(), new FakeCancel());
                Check(r.Status == "mains_lost" && b.Creates == 1 && b.Sets == 0 && b.Closes == 1);
            });
            test("power_lost_after_set", delegate {
                FakeBackend b = new FakeBackend { LosePowerAt = 4 };
                Result r = Runner.Run(true, 1000, b, new FakeClock(), new FakeCancel());
                Check(r.Status == "mains_lost" && r.SetAcknowledged && r.ClearAcknowledged && r.CloseAcknowledged);
                Check(r.ElapsedMs == 250);
            });
            foreach (string operation in new string[] { "create", "set", "clear", "close" })
            {
                string op = operation;
                test("false_" + op, delegate {
                    FakeBackend b = new FakeBackend { FalseAt = op };
                    Result r = Runner.Run(true, 1, b, new FakeClock(), new FakeCancel());
                    Check(r.ExitCode == 2 && b.Closes == 1);
                    if (op == "create" || op == "set") Check(b.Clears == 0);
                    if (op == "clear" || op == "close") Check(r.Status == "cleanup_failed");
                });
            }
            foreach (string operation in new string[] { "power", "create", "set", "clear", "close" })
            {
                string op = operation;
                test("throw_" + op, delegate {
                    FakeBackend b = new FakeBackend { ThrowAt = op };
                    Result r = Runner.Run(true, 1, b, new FakeClock(), new FakeCancel());
                    Check(r.ExitCode == 2);
                    Check(b.Closes == (op == "power" ? 0 : 1));
                    if (op == "clear") Check(b.Clears == 1 && b.Closes == 1);
                });
            }
            test("rollback_after_acquire", delegate {
                FakeClock c = new FakeClock { RollbackAt = 6 };
                Result r = Runner.Run(true, 1000, new FakeBackend(), c, new FakeCancel());
                Check(r.Status == "unsafe_clock" && r.ClearAcknowledged && r.CloseAcknowledged);
            });
            test("oversleep_no_renewal", delegate {
                FakeClock c = new FakeClock { Oversleep = 5000 }; FakeBackend b = new FakeBackend();
                Result r = Runner.Run(true, 100, b, c, new FakeCancel());
                Check(r.ElapsedMs == 5100 && c.Waits == 1 && b.Sets == 1 && r.ClearAcknowledged && r.CloseAcknowledged);
            });
            test("slow_create_expires_before_set", delegate {
                FakeClock c = new FakeClock(); FakeBackend b = new FakeBackend { Clock = c, CreateCost = 2000 };
                Result r = Runner.Run(true, 1000, b, c, new FakeCancel());
                Check(r.Status == "deadline" && b.Sets == 0 && b.Closes == 1 && !r.ClearAttempted);
            });
            test("slow_power_recheck_expires_before_set", delegate {
                FakeClock c = new FakeClock(); FakeBackend b = new FakeBackend { Clock = c, SecondPowerCost = 2000 };
                Result r = Runner.Run(true, 1000, b, c, new FakeCancel());
                Check(r.Status == "deadline" && b.Sets == 0 && b.Closes == 1);
            });
            test("wait_exception_releases", delegate {
                Result r = Runner.Run(true, 1000, new FakeBackend(), new FakeClock { ThrowWait = true }, new FakeCancel());
                Check(r.Status == "helper_failure" && r.ClearAcknowledged && r.CloseAcknowledged);
            });
            test("failed_readiness_releases", delegate {
                Result r = Runner.Run(true, 1000, new FakeBackend(), new FakeClock(), new FakeCancel(), delegate { return false; });
                Check(r.Status == "readiness_failed" && r.SetAcknowledged && r.ClearAcknowledged && r.CloseAcknowledged);
            });
            test("throwing_readiness_releases", delegate {
                Result r = Runner.Run(true, 1000, new FakeBackend(), new FakeClock(), new FakeCancel(),
                                      delegate { throw new InvalidOperationException("invented_ready"); });
                Check(r.Status == "helper_failure" && r.ClearAcknowledged && r.CloseAcknowledged);
            });
            test("native_disabled_and_invalid_cancel_no_request", delegate {
                Result off = NativeHost.Execute(false, 1000, "");
                Result invalid = NativeHost.Execute(true, 1000, "not_a_permitted_event");
                Check(off.Status == "off" && !off.NativeBackend && !off.CreateAttempted);
                Check(invalid.Status == "invalid_cancellation" && !invalid.CreateAttempted);
                Check(NativePower.ReasonContextSize == (IntPtr.Size == 8 ? 32 : 24));
            });
            return new Summary { Passed = true, Tests = cases.Count, Checks = checks, Cases = cases.ToArray() };
        }
    }
}
