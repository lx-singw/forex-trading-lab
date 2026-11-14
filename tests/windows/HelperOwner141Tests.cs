using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Security.Cryptography;
using System.Text;
using System.Threading;
using System.Web.Script.Serialization;
using ForexDemoLab.HelperOwner141;
using OwnerTrace = ForexDemoLab.HelperOwner141.Trace;

namespace ForexDemoLab.HelperOwner141Testing
{
    public sealed class NativeReport
    {
        public string Schema = "helper_owner141_native_check_v1", Failure = "none";
        public bool Passed, PowerConfigurationUnchanged;
        public string PowerBeforeSha256, PowerAfterSha256;
        public int PureCases, NativeCases, OwnedProcessesRemaining;
        public bool GlobalRequestRemovalObserved = false, IdleSleepSuppressionTested = false;
        public int TerminalStarts = 0, QuotesRead = 0, AccountQueries = 0, Orders = 0;
        public List<object> Cases = new List<object>();
    }
    public static class Suite
    {
        private sealed class PartialStream : MemoryStream
        {
            public int Writes;
            public override void Write(byte[] bytes, int offset, int count)
            { Writes++; base.Write(bytes, offset, count / 2); throw new IOException(); }
        }
        private sealed class Owned : IDisposable
        {
            public Process Owner, Helper;
            public EventWaitHandle Cancel, Gate;
            public string Journal;
            public List<Dictionary<string, object>> Lines = new List<Dictionary<string, object>>();
            public void StopAll()
            {
                if (Owner != null && !Owner.HasExited) { Owner.Kill(); Owner.WaitForExit(5000); }
                if (Helper != null && !Helper.HasExited) { Helper.Kill(); Helper.WaitForExit(5000); }
            }
            public void Dispose()
            {
                StopAll();
                if (Owner != null) Owner.Dispose(); if (Helper != null) Helper.Dispose();
                if (Cancel != null) Cancel.Dispose(); if (Gate != null) Gate.Dispose();
            }
        }
        private static void Check(bool value) { if (!value) throw new InvalidOperationException(); }
        private static string Q(string text)
        { if (text.IndexOf('"') >= 0) throw new ArgumentException(); return "\"" + text + "\""; }
        private static Owned Start(string owner, string helper, string sha, string folder, int seconds, bool enabled, bool gate, List<Owned> owned)
        {
            Owned item = new Owned();
            string tag = Guid.NewGuid().ToString("N");
            item.Journal = Path.Combine(folder, "Owner141-" + tag + ".journal");
            string cancel = @"Local\ForexDemoLab141Cancel-" + tag;
            item.Cancel = new EventWaitHandle(false, EventResetMode.ManualReset, cancel);
            string args = "--seconds " + seconds + " --helper " + Q(helper) + " --sha256 " + sha + " --journal " + Q(item.Journal) + " --cancel-event " + cancel;
            if (enabled) args += " --enable";
            if (gate)
            {
                string name = @"Local\ForexDemoLab141Gate-" + tag;
                item.Gate = new EventWaitHandle(false, EventResetMode.ManualReset, name); args += " --gate-event " + name;
            }
            item.Owner = new Process { StartInfo = new ProcessStartInfo(owner, args) {
                UseShellExecute = false, CreateNoWindow = true, RedirectStandardOutput = true, RedirectStandardError = true } };
            Check(item.Owner.Start()); owned.Add(item); return item;
        }
        private static Dictionary<string, object> ReadLine(Owned item)
        {
            var line = item.Owner.StandardOutput.ReadLineAsync();
            if (!line.Wait(10000) || line.Result == null || line.Result.Length > 2048) throw new InvalidOperationException();
            var value = new JavaScriptSerializer().Deserialize<Dictionary<string, object>>(line.Result);
            item.Lines.Add(value); return value;
        }
        private static void Until(Owned item, string kind)
        {
            for (int i = 0; i < 10; i++)
            {
                var line = ReadLine(item);
                if ((string)line["Schema"] == "helper_owner141_result_v1") throw new InvalidOperationException();
                if ((string)line["Event"] == "child_created_suspended")
                {
                    int pid = Convert.ToInt32(line["HelperPid"]);
                    item.Helper = Process.GetProcessById(pid);
                    IntPtr bound = item.Helper.Handle; Check(bound != IntPtr.Zero); // Retain this exact process, not a reused PID.
                }
                if ((string)line["Event"] == kind) return;
            }
            throw new InvalidOperationException();
        }
        private static Receipt Finish(Owned item)
        {
            Receipt result = null;
            for (int i = 0; i < 12; i++)
            {
                var value = ReadLine(item);
                if ((string)value["Schema"] == "helper_owner141_result_v1")
                { result = new JavaScriptSerializer().ConvertToType<Receipt>(value); break; }
            }
            Check(result != null && item.Owner.WaitForExit(5000) && item.Owner.ExitCode == result.ExitCode);
            item.Owner.StandardError.ReadToEnd();
            return result;
        }
        private static string Snapshot()
        {
            StringBuilder text = new StringBuilder();
            foreach (string arg in new string[] { "/getactivescheme", "/query SCHEME_CURRENT SUB_SLEEP", "/query SCHEME_CURRENT SUB_VIDEO" })
            {
                string tool = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.System), "powercfg.exe");
                using (Process p = new Process { StartInfo = new ProcessStartInfo(tool, arg) {
                    UseShellExecute = false, CreateNoWindow = true, RedirectStandardOutput = true, RedirectStandardError = true } })
                {
                    Check(p.Start()); var stdout = p.StandardOutput.ReadToEndAsync(); var stderr = p.StandardError.ReadToEndAsync();
                    if (!p.WaitForExit(5000)) { p.Kill(); throw new InvalidOperationException(); }
                    Check(p.ExitCode == 0); text.Append(stdout.GetAwaiter().GetResult()); stderr.GetAwaiter().GetResult();
                }
            }
            using (SHA256 sha = SHA256.Create()) return BitConverter.ToString(sha.ComputeHash(Encoding.UTF8.GetBytes(text.ToString()))).Replace("-", "").ToLowerInvariant();
        }
        public static NativeReport Run(string owner, string helper, string sha, string folder)
        {
            NativeReport report = new NativeReport(); List<Owned> owned = new List<Owned>(); string stage = "pure";
            try
            {
                foreach (int seconds in new int[] { 0, -1, 14401, Int32.MaxValue })
                { Check(!Options.Valid(new Options { Seconds = seconds })); report.PureCases++; }
                Check(Options.Valid(new Options { Seconds = 1 })); report.PureCases++;
                Check(Options.Valid(new Options { Seconds = 14400 })); report.PureCases++;
                Check(!Options.Valid(new Options { CancelEvent = "invalid" })); report.PureCases++;
                Check(!Options.Valid(new Options { GateEvent = "invalid" })); report.PureCases++;
                Check(!Options.Valid(new Options { Helper = null })); report.PureCases++;
                Check(Child.ExtendedSize == 144 && Child.StartupSize == 112); report.PureCases++;
                Check(Owner.Run(new Options()).Status == "off"); report.PureCases++;
                using (MemoryStream data = new MemoryStream())
                using (OwnerTrace trace = new OwnerTrace(data, delegate { throw new IOException(); }))
                {
                    bool failed = false; try { trace.Emit("owner_started", 0, 0, false, false, false); } catch (IOException) { failed = true; }
                    long length = data.Length; Check(failed && trace.Sequence == 0);
                    try { trace.Emit("owner_started", 0, 0, false, false, false); } catch (IOException) { }
                    Check(data.Length == length); report.PureCases++;
                }
                using (PartialStream data = new PartialStream())
                using (OwnerTrace trace = new OwnerTrace(data, delegate { }))
                {
                    try { trace.Emit("owner_started", 0, 0, false, false, false); } catch (IOException) { }
                    try { trace.Emit("owner_started", 0, 0, false, false, false); } catch (IOException) { }
                    Check(data.Writes == 1 && trace.Sequence == 0); report.PureCases++;
                }
                using (MemoryStream data = new MemoryStream())
                using (OwnerTrace trace = new OwnerTrace(data, delegate { }))
                {
                    bool eventRejected = false; try { trace.Emit("arbitrary_text", 0, 0, false, false, false); } catch (ArgumentException) { eventRejected = true; }
                    Check(eventRejected && data.Length == 0); report.PureCases++;
                }
                report.PowerBeforeSha256 = Snapshot();
                stage = "default_off";
                Owned off = Start(owner, helper, sha, folder, 1, false, false, owned); Receipt offResult = Finish(off);
                Check(offResult.Status == "off" && !offResult.ChildCreated && !File.Exists(off.Journal));
                report.Cases.Add(new { Name = stage, Passed = true, Receipt = offResult }); report.NativeCases++;
                stage = "hash_rejected";
                Owned rejected = Start(owner, helper, new String('0', 64), folder, 1, true, false, owned); Receipt rejectedResult = Finish(rejected);
                Check(rejectedResult.ExitCode == 2 && !rejectedResult.ChildCreated && !File.Exists(rejected.Journal));
                report.Cases.Add(new { Name = stage, Passed = true, Receipt = rejectedResult }); report.NativeCases++;
                stage = "graceful_deadline";
                Owned expiry = Start(owner, helper, sha, folder, 2, true, false, owned); Until(expiry, "invented_triple_begin");
                Receipt expired = Finish(expiry);
                Check(expired.Status == "deadline" && expired.ExitCode == 0 && expired.HelperExitObserved && expired.HelperClearAcknowledged == true && expired.HelperCloseAcknowledged == true);
                Check(expiry.Helper.WaitForExit(5000));
                report.Cases.Add(new { Name = stage, Passed = true, Journal = Path.GetFileName(expiry.Journal), Receipt = expired }); report.NativeCases++;
                stage = "owner_cancellation";
                Owned cancelled = Start(owner, helper, sha, folder, 30, true, false, owned); Until(cancelled, "invented_triple_begin");
                cancelled.Cancel.Set(); Receipt cancelledResult = Finish(cancelled);
                Check(cancelledResult.Status == "cancelled" && cancelledResult.ExitCode == 0 && cancelledResult.HelperExitObserved && cancelledResult.HelperClearAcknowledged == true);
                report.Cases.Add(new { Name = stage, Passed = true, Journal = Path.GetFileName(cancelled.Journal), Receipt = cancelledResult }); report.NativeCases++;
                stage = "helper_killed_after_ready";
                Owned helperKilled = Start(owner, helper, sha, folder, 30, true, false, owned); Until(helperKilled, "invented_triple_begin");
                helperKilled.Helper.Kill(); Check(helperKilled.Helper.WaitForExit(5000)); Receipt lost = Finish(helperKilled);
                Check(lost.Status == "helper_exited" && lost.ExitCode == 2 && lost.HelperExitObserved && lost.HelperClearAcknowledged == null);
                report.Cases.Add(new { Name = stage, Passed = true, Journal = Path.GetFileName(helperKilled.Journal), Receipt = lost }); report.NativeCases++;
                foreach (bool beforeResume in new bool[] { true, false })
                {
                    stage = beforeResume ? "owner_killed_before_resume" : "owner_killed_after_pending";
                    Owned killed = Start(owner, helper, sha, folder, 30, true, beforeResume, owned);
                    Until(killed, beforeResume ? "child_created_suspended" : "invented_triple_begin");
                    Check(!killed.Helper.HasExited); killed.Owner.Kill(); Check(killed.Owner.WaitForExit(5000));
                    Check(killed.Helper.WaitForExit(5000));
                    report.Cases.Add(new { Name = stage, Passed = true, Journal = Path.GetFileName(killed.Journal), OwnerExited = true,
                        HelperExited = true, SuspendedAtOwnerDeath = beforeResume, ManagedCleanupReceiptAvailable = false });
                    report.NativeCases++;
                }
                stage = "suspended_gate_timeout";
                Owned gated = Start(owner, helper, sha, folder, 1, true, true, owned); Until(gated, "child_created_suspended"); Receipt timeout = Finish(gated);
                Check(timeout.Status == "gate_timeout" && !timeout.ChildResumed && timeout.HelperExitObserved && timeout.ForcedJobClosure);
                report.Cases.Add(new { Name = stage, Passed = true, Journal = Path.GetFileName(gated.Journal), Receipt = timeout }); report.NativeCases++;
                report.Passed = true;
            }
            catch { report.Failure = stage; report.Passed = false; }
            finally
            {
                foreach (Owned item in owned) { try { item.StopAll(); } catch { report.Passed = false; } }
                foreach (Owned item in owned)
                {
                    if (item.Owner != null && !item.Owner.HasExited) report.OwnedProcessesRemaining++;
                    if (item.Helper != null && !item.Helper.HasExited) report.OwnedProcessesRemaining++;
                }
                try { report.PowerAfterSha256 = Snapshot(); report.PowerConfigurationUnchanged = report.PowerBeforeSha256 == report.PowerAfterSha256; }
                catch { report.PowerConfigurationUnchanged = false; }
                report.Passed = report.Passed && report.PowerConfigurationUnchanged && report.OwnedProcessesRemaining == 0;
                foreach (Owned item in owned) item.Dispose();
            }
            return report;
        }
    }
    public static class TestProgram
    {
        public static int Main(string[] args)
        {
            if (args.Length != 4) return 2;
            NativeReport r = Suite.Run(args[0], args[1], args[2], args[3]);
            Console.WriteLine(new JavaScriptSerializer().Serialize(r)); return r.Passed ? 0 : 2;
        }
    }
}
