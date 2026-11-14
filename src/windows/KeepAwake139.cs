using System;
using System.Runtime.InteropServices;
using System.Threading;

namespace ForexDemoLab.KeepAwake139
{
    public enum AcState { Battery = 0, Mains = 1, Unknown = 255 }
    public interface IPowerBackend
    {
        AcState ReadPower();
        bool Create();
        bool Set();
        bool Clear();
        bool Close();
    }
    public interface IClock { long NowMs { get; } void Wait(int milliseconds); }
    public interface ICancellation { bool Requested { get; } }

    public sealed class Result
    {
        public string Schema = "keep_awake139_result_v1";
        public string Status = "off";
        public int ExitCode = 0;
        public long RequestedMs;
        public long ElapsedMs;
        public string LastPower = "unqueried";
        public int PowerSamples;
        public bool CreateAttempted, CreateAcknowledged, SetAttempted, SetAcknowledged;
        public bool ClearAttempted, ClearAcknowledged, CloseAttempted, CloseAcknowledged;
        public bool ReadySignalled;
        public bool NativeBackend;
        public bool PowerPlanWrites = false, DisplayRequest = false, ExecutionRequest = false;
        public bool TerminalStarted = false, AccountQueried = false, QuotesRead = false, OrdersAvailable = false;
    }

    public static class Runner
    {
        public const long MaxDurationMs = 14400000;
        public const int PollMs = 250;
        private sealed class ClockFault : Exception { }
        private static long Elapsed(IClock clock, long start, ref long previous)
        {
            long now = clock.NowMs;
            if (now < 0 || now < previous || now < start) throw new ClockFault();
            previous = now;
            return now - start;
        }
        private static bool Mains(IPowerBackend backend, Result result)
        {
            AcState state = backend.ReadPower();
            result.PowerSamples++;
            result.LastPower = state == AcState.Mains ? "mains" : state == AcState.Battery ? "battery" : "unknown";
            return state == AcState.Mains;
        }
        public static Result Run(bool enabled, long durationMs, IPowerBackend backend, IClock clock, ICancellation cancel,
                                 Func<bool> acquired = null)
        {
            Result r = new Result { RequestedMs = durationMs };
            if (durationMs < 1 || durationMs > MaxDurationMs || backend == null || clock == null || cancel == null)
            { r.Status = "invalid_configuration"; r.ExitCode = 2; return r; }
            if (!enabled) return r; // No backend, clock or cancellation calls when disabled.
            long start = 0, previous = 0;
            bool clockStarted = false;
            try
            {
                start = clock.NowMs; previous = start;
                if (start < 0) throw new ClockFault();
                clockStarted = true;
                if (cancel.Requested) { r.Status = "cancelled"; return r; }
                if (!Mains(backend, r)) { r.Status = "mains_required"; r.ExitCode = 2; return r; }
                r.ElapsedMs = Elapsed(clock, start, ref previous);
                if (r.ElapsedMs >= durationMs) { r.Status = "deadline"; return r; }
                r.CreateAttempted = true;
                r.CreateAcknowledged = backend.Create();
                if (!r.CreateAcknowledged) { r.Status = "create_failed"; r.ExitCode = 2; return r; }
                r.ElapsedMs = Elapsed(clock, start, ref previous);
                if (r.ElapsedMs >= durationMs) { r.Status = "deadline"; return r; }
                if (cancel.Requested) { r.Status = "cancelled"; return r; }
                if (!Mains(backend, r)) { r.Status = "mains_lost"; r.ExitCode = 2; return r; }
                r.ElapsedMs = Elapsed(clock, start, ref previous);
                if (r.ElapsedMs >= durationMs) { r.Status = "deadline"; return r; }
                if (cancel.Requested) { r.Status = "cancelled"; return r; }
                r.SetAttempted = true;
                r.SetAcknowledged = backend.Set();
                if (!r.SetAcknowledged) { r.Status = "set_failed"; r.ExitCode = 2; return r; }
                if (acquired != null)
                {
                    r.ReadySignalled = acquired();
                    if (!r.ReadySignalled) { r.Status = "readiness_failed"; r.ExitCode = 2; return r; }
                }
                while (true)
                {
                    r.ElapsedMs = Elapsed(clock, start, ref previous);
                    if (r.ElapsedMs >= durationMs) { r.Status = "deadline"; break; }
                    if (cancel.Requested) { r.Status = "cancelled"; break; }
                    if (!Mains(backend, r)) { r.Status = "mains_lost"; r.ExitCode = 2; break; }
                    clock.Wait((int)Math.Min(PollMs, durationMs - r.ElapsedMs));
                }
            }
            catch (ClockFault) { r.Status = "unsafe_clock"; r.ExitCode = 2; }
            catch (Exception) { r.Status = "helper_failure"; r.ExitCode = 2; }
            finally
            {
                if (r.SetAcknowledged)
                {
                    r.ClearAttempted = true;
                    try { r.ClearAcknowledged = backend.Clear(); }
                    catch (Exception) { r.ClearAcknowledged = false; }
                    if (!r.ClearAcknowledged) { r.Status = "cleanup_failed"; r.ExitCode = 2; }
                }
                // Close even when create/set threw after allocating a handle.
                if (r.CreateAttempted)
                {
                    r.CloseAttempted = true;
                    try { r.CloseAcknowledged = backend.Close(); }
                    catch (Exception) { r.CloseAcknowledged = false; }
                    if (!r.CloseAcknowledged) { r.Status = "cleanup_failed"; r.ExitCode = 2; }
                }
                if (clockStarted)
                {
                    try { r.ElapsedMs = Elapsed(clock, start, ref previous); }
                    catch (Exception) { r.Status = "unsafe_clock"; r.ExitCode = 2; }
                }
            }
            return r;
        }
    }

    public sealed class NativePower : IPowerBackend
    {
        public const string ReasonText = "ForexDemoLab139 bounded diagnostic";
        private IntPtr handle = IntPtr.Zero;
        [StructLayout(LayoutKind.Sequential)]
        private struct DetailedReason { public IntPtr Module; public uint Id, Count; public IntPtr Strings; }
        [StructLayout(LayoutKind.Explicit)]
        private struct ReasonUnion
        {
            [FieldOffset(0)] public IntPtr Simple;
            [FieldOffset(0)] public DetailedReason Detailed;
        }
        [StructLayout(LayoutKind.Sequential)]
        private struct ReasonContext { public uint Version, Flags; public ReasonUnion Reason; }
        [StructLayout(LayoutKind.Sequential)]
        private struct PowerStatus
        { public byte Ac, BatteryFlag, BatteryPercent, SystemStatus; public uint Life, FullLife; }
        [DllImport("kernel32.dll", SetLastError = true)]
        private static extern IntPtr PowerCreateRequest(ref ReasonContext reason);
        [DllImport("kernel32.dll", SetLastError = true)]
        [return: MarshalAs(UnmanagedType.Bool)]
        private static extern bool PowerSetRequest(IntPtr request, uint type);
        [DllImport("kernel32.dll", SetLastError = true)]
        [return: MarshalAs(UnmanagedType.Bool)]
        private static extern bool PowerClearRequest(IntPtr request, uint type);
        [DllImport("kernel32.dll", SetLastError = true)]
        [return: MarshalAs(UnmanagedType.Bool)]
        private static extern bool CloseHandle(IntPtr handle);
        [DllImport("kernel32.dll", SetLastError = true)]
        [return: MarshalAs(UnmanagedType.Bool)]
        private static extern bool GetSystemPowerStatus(out PowerStatus status);

        public static int ReasonContextSize { get { return Marshal.SizeOf(typeof(ReasonContext)); } }
        public AcState ReadPower()
        {
            PowerStatus status;
            if (!GetSystemPowerStatus(out status)) return AcState.Unknown;
            return status.Ac == 1 ? AcState.Mains : status.Ac == 0 ? AcState.Battery : AcState.Unknown;
        }
        public bool Create()
        {
            if (handle != IntPtr.Zero) return false;
            IntPtr text = Marshal.StringToHGlobalUni(ReasonText);
            try
            {
                ReasonContext context = new ReasonContext { Version = 0, Flags = 1,
                    Reason = new ReasonUnion { Simple = text } };
                handle = PowerCreateRequest(ref context);
                if (handle == new IntPtr(-1)) { handle = IntPtr.Zero; return false; }
                return handle != IntPtr.Zero;
            }
            finally { Marshal.FreeHGlobal(text); }
        }
        public bool Set() { return handle != IntPtr.Zero && PowerSetRequest(handle, 1); } // SystemRequired only.
        public bool Clear() { return handle != IntPtr.Zero && PowerClearRequest(handle, 1); }
        public bool Close()
        {
            IntPtr owned = Interlocked.Exchange(ref handle, IntPtr.Zero);
            return owned == IntPtr.Zero || CloseHandle(owned);
        }
    }

    public sealed class NativeClock : IClock
    {
        [DllImport("kernel32.dll")] private static extern ulong GetTickCount64();
        public long NowMs { get { return checked((long)GetTickCount64()); } }
        public void Wait(int milliseconds) { Thread.Sleep(milliseconds); }
    }

    public sealed class NativeCancellation : ICancellation, IDisposable
    {
        private EventWaitHandle signal;
        private EventWaitHandle ready;
        private int cancelled;
        private readonly ConsoleCancelEventHandler handler;
        public NativeCancellation(string eventName, string readyName)
        {
            handler = delegate(object sender, ConsoleCancelEventArgs e)
            { Interlocked.Exchange(ref cancelled, 1); e.Cancel = true; };
            try
            {
                if (!String.IsNullOrEmpty(eventName)) signal = EventWaitHandle.OpenExisting(eventName);
                if (!String.IsNullOrEmpty(readyName)) ready = EventWaitHandle.OpenExisting(readyName);
                Console.CancelKeyPress += handler;
            }
            catch
            {
                if (signal != null) signal.Dispose();
                if (ready != null) ready.Dispose();
                throw;
            }
        }
        public bool Requested { get { return cancelled != 0 || signal != null && signal.WaitOne(0); } }
        public bool HasReady { get { return ready != null; } }
        public bool SignalReady() { return ready != null && ready.Set(); }
        public void Dispose()
        {
            Console.CancelKeyPress -= handler;
            if (signal != null) { signal.Dispose(); signal = null; }
            if (ready != null) { ready.Dispose(); ready = null; }
        }
    }

    public static class NativeHost
    {
        public const string MutexName = @"Local\ForexDemoLab139.SingleOwner";
        public static Result Execute(bool enabled, long durationMs, string cancelEventName, string readyEventName = "")
        {
            if (durationMs < 1 || durationMs > Runner.MaxDurationMs)
                return new Result { Status = "invalid_configuration", ExitCode = 2, RequestedMs = durationMs };
            if (!enabled) return new Result { RequestedMs = durationMs };
            if (Environment.OSVersion.Platform != PlatformID.Win32NT)
                return new Result { Status = "windows_required", ExitCode = 2, RequestedMs = durationMs };
            if (!String.IsNullOrEmpty(cancelEventName) &&
                !System.Text.RegularExpressions.Regex.IsMatch(cancelEventName, @"\ALocal\\ForexDemoLab139Cancel-[a-f0-9]{32}\z"))
                return new Result { Status = "invalid_cancellation", ExitCode = 2, RequestedMs = durationMs };
            if (!String.IsNullOrEmpty(readyEventName) &&
                !System.Text.RegularExpressions.Regex.IsMatch(readyEventName, @"\ALocal\\ForexDemoLab139Ready-[a-f0-9]{32}\z"))
                return new Result { Status = "invalid_readiness", ExitCode = 2, RequestedMs = durationMs };
            bool owned = false;
            try
            {
                using (Mutex mutex = new Mutex(false, MutexName))
                {
                    try
                    {
                        try { owned = mutex.WaitOne(0); }
                        catch (AbandonedMutexException) { owned = true; }
                        if (!owned) return new Result { Status = "already_running", ExitCode = 2, RequestedMs = durationMs };
                        using (NativeCancellation cancel = new NativeCancellation(cancelEventName, readyEventName))
                        {
                            Result r = Runner.Run(true, durationMs, new NativePower(), new NativeClock(), cancel,
                                                  cancel.HasReady ? new Func<bool>(cancel.SignalReady) : null);
                            r.NativeBackend = true;
                            return r;
                        }
                    }
                    finally { if (owned) mutex.ReleaseMutex(); }
                }
            }
            catch (Exception)
            { return new Result { Status = "host_setup_failed", ExitCode = 2, RequestedMs = durationMs }; }
        }
    }
}
