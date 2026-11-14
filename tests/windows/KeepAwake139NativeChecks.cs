using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Security.Cryptography;
using System.Text;
using System.Threading;
using System.Web.Script.Serialization;
using ForexDemoLab.KeepAwake139;

namespace ForexDemoLab.KeepAwake139Testing
{
    public sealed class NativeReport
    {
        public string Schema = "keep_awake139_native_check_v1";
        public bool Passed;
        public List<object> Cases = new List<object>();
        public int OwnedHelpersRemaining;
        public string PowerConfigurationBeforeSha256, PowerConfigurationAfterSha256;
        public bool PowerConfigurationUnchanged, GlobalRequestListAvailable;
        public bool IdleSleepSuppressionTested = false, CtrlCTested = false;
        public int PowerPlanWrites = 0, TerminalStarts = 0, AccountQueries = 0, QuoteReads = 0, Orders = 0;
        public string Failure = "none";
    }
    public static class NativeChecks
    {
        private sealed class Owned : IDisposable
        {
            public Process Process;
            public EventWaitHandle Ready, Cancel;
            public void Dispose()
            {
                if (!Process.HasExited) { Process.Kill(); Process.WaitForExit(5000); }
                if (Ready != null) Ready.Dispose();
                if (Cancel != null) Cancel.Dispose();
                Process.Dispose();
            }
        }
        private static ProcessInfo ReadTool(string arguments)
        {
            string command = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.System), "powercfg.exe");
            using (Process p = new Process())
            {
                p.StartInfo = new ProcessStartInfo(command, arguments) { UseShellExecute = false,
                    CreateNoWindow = true, RedirectStandardOutput = true, RedirectStandardError = true };
                p.Start();
                var output = p.StandardOutput.ReadToEndAsync();
                var error = p.StandardError.ReadToEndAsync();
                if (!p.WaitForExit(5000)) { p.Kill(); throw new InvalidOperationException(); }
                return new ProcessInfo { Code = p.ExitCode, Output = output.GetAwaiter().GetResult(),
                    ErrorBytes = Encoding.UTF8.GetByteCount(error.GetAwaiter().GetResult()) };
            }
        }
        private sealed class ProcessInfo { public int Code, ErrorBytes; public string Output; }
        private static string PowerHash()
        {
            StringBuilder all = new StringBuilder();
            foreach (string arg in new string[] { "/getactivescheme", "/query SCHEME_CURRENT SUB_SLEEP", "/query SCHEME_CURRENT SUB_VIDEO" })
            {
                ProcessInfo info = ReadTool(arg);
                if (info.Code != 0) throw new InvalidOperationException();
                all.Append(info.Output);
            }
            using (SHA256 sha = SHA256.Create())
                return BitConverter.ToString(sha.ComputeHash(Encoding.UTF8.GetBytes(all.ToString()))).Replace("-", "").ToLowerInvariant();
        }
        private static Owned Start(string executable, bool enabled, int seconds, bool signals, List<Owned> children)
        {
            Owned child = new Owned();
            string arguments = "--seconds " + seconds;
            if (enabled) arguments += " --enable";
            if (signals)
            {
                string tag = Guid.NewGuid().ToString("N");
                string ready = @"Local\ForexDemoLab139Ready-" + tag, cancel = @"Local\ForexDemoLab139Cancel-" + tag;
                child.Ready = new EventWaitHandle(false, EventResetMode.ManualReset, ready);
                child.Cancel = new EventWaitHandle(false, EventResetMode.ManualReset, cancel);
                arguments += " --ready-event " + ready + " --cancel-event " + cancel;
            }
            child.Process = new Process { StartInfo = new ProcessStartInfo(executable, arguments) {
                UseShellExecute = false, CreateNoWindow = true, RedirectStandardOutput = true, RedirectStandardError = true } };
            if (!child.Process.Start()) throw new InvalidOperationException();
            children.Add(child);
            return child;
        }
        private static Result Finish(Owned child)
        {
            if (!child.Process.WaitForExit(10000)) throw new InvalidOperationException();
            string output = child.Process.StandardOutput.ReadToEnd();
            child.Process.StandardError.ReadToEnd(); // Never print unrelated paths or exception strings.
            Result result = new JavaScriptSerializer().Deserialize<Result>(output);
            if (result == null || result.Schema != "keep_awake139_result_v1" || result.ExitCode != child.Process.ExitCode)
                throw new InvalidOperationException();
            return result;
        }
        private static void Check(bool condition) { if (!condition) throw new InvalidOperationException(); }
        private static void Add(NativeReport report, string name, Result result)
        { report.Cases.Add(new { Name = name, Passed = true, Receipt = result }); }

        public static NativeReport Run(string executable)
        {
            NativeReport report = new NativeReport();
            List<Owned> children = new List<Owned>();
            string stage = "power_snapshot";
            try
            {
                report.PowerConfigurationBeforeSha256 = PowerHash();
                report.GlobalRequestListAvailable = ReadTool("/requests").Code == 0;
                stage = "default_off";
                Result off = Finish(Start(executable, false, 1, false, children));
                Check(off.Status == "off" && !off.CreateAttempted); Add(report, stage, off);
                stage = "native_expiry";
                Owned expiry = Start(executable, true, 2, true, children);
                bool acquired = expiry.Ready.WaitOne(10000);
                Result expired = Finish(expiry);
                if (expired.Status == "mains_required")
                {
                    Add(report, "native_mains_rejection_activation_not_tested", expired);
                }
                else
                {
                    Check(acquired && expired.Status == "deadline" && expired.ExitCode == 0 && expired.SetAcknowledged
                          && expired.ClearAcknowledged && expired.CloseAcknowledged); Add(report, stage, expired);
                    stage = "named_cancellation";
                    Owned owner = Start(executable, true, 30, true, children);
                    Check(owner.Ready.WaitOne(10000) && !owner.Process.HasExited);
                    Result duplicate = Finish(Start(executable, true, 1, false, children));
                    Check(duplicate.Status == "already_running" && !duplicate.CreateAttempted);
                    Add(report, "duplicate_owner_rejected", duplicate);
                    owner.Cancel.Set();
                    Result cancelled = Finish(owner);
                    Check(cancelled.Status == "cancelled" && cancelled.ClearAcknowledged && cancelled.CloseAcknowledged && cancelled.ExitCode == 0);
                    Add(report, stage, cancelled);
                    stage = "forced_owned_exit";
                    Owned killed = Start(executable, true, 30, true, children);
                    Check(killed.Ready.WaitOne(10000) && !killed.Process.HasExited);
                    killed.Process.Kill(); // Exact process returned by our own Start call; no process-name search.
                    Check(killed.Process.WaitForExit(5000));
                    report.Cases.Add(new { Name = stage, Passed = true, SetAcknowledgedByReadyEvent = true,
                        ProcessExited = true, ManagedCleanupReceiptAvailable = false, GlobalRequestRemovalDirectlyObserved = false });
                    stage = "new_owner_after_forced_exit";
                    Result after = Finish(Start(executable, true, 1, false, children));
                    Check(after.Status == "deadline" && after.ClearAcknowledged && after.CloseAcknowledged);
                    Add(report, stage, after);
                }
                report.Passed = true;
            }
            catch (Exception) { report.Passed = false; report.Failure = stage; }
            finally
            {
                foreach (Owned child in children)
                {
                    if (!child.Process.HasExited)
                    {
                        try { child.Process.Kill(); child.Process.WaitForExit(5000); }
                        catch (Exception) { }
                    }
                    if (!child.Process.HasExited) report.OwnedHelpersRemaining++;
                }
                try
                {
                    report.PowerConfigurationAfterSha256 = PowerHash();
                    report.PowerConfigurationUnchanged = report.PowerConfigurationBeforeSha256 == report.PowerConfigurationAfterSha256;
                }
                catch (Exception) { report.PowerConfigurationUnchanged = false; }
                report.Passed = report.Passed && report.PowerConfigurationUnchanged && report.OwnedHelpersRemaining == 0;
                foreach (Owned child in children) child.Dispose();
            }
            return report;
        }
    }
    public static class TestProgram
    {
        public static int Main(string[] args)
        {
            try
            {
                if (args.Length == 0)
                {
                    Summary summary = Suite.RunAll(); Console.WriteLine(new JavaScriptSerializer().Serialize(summary));
                    return summary.Passed ? 0 : 2;
                }
                if (args.Length == 2 && args[0] == "--native-check")
                {
                    NativeReport report = NativeChecks.Run(args[1]); Console.WriteLine(new JavaScriptSerializer().Serialize(report));
                    return report.Passed ? 0 : 2;
                }
            }
            catch (Exception) { Console.WriteLine("{\"Passed\":false,\"Failure\":\"test_runner\"}"); }
            return 2;
        }
    }
}
