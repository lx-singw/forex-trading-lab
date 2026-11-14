using System;
using System.Collections.Generic;
using System.IO;
using System.Runtime.InteropServices;
using System.Security.Cryptography;
using System.Text;
using System.Threading;
using System.Web.Script.Serialization;
using Microsoft.Win32.SafeHandles;

namespace ForexDemoLab.HelperOwner141
{
    public sealed class Options
    {
        public bool Enabled;
        public int Seconds = 60;
        public string Helper = "", Sha256 = "", Journal = "", CancelEvent = "", GateEvent = "";
        public static bool Valid(Options o)
        {
            return o != null && o.Helper != null && o.Sha256 != null && o.Journal != null && o.CancelEvent != null && o.GateEvent != null &&
                o.Seconds >= 1 && o.Seconds <= 14400 &&
                (o.CancelEvent == "" || System.Text.RegularExpressions.Regex.IsMatch(o.CancelEvent, @"\ALocal\\ForexDemoLab141Cancel-[a-f0-9]{32}\z")) &&
                (o.GateEvent == "" || System.Text.RegularExpressions.Regex.IsMatch(o.GateEvent, @"\ALocal\\ForexDemoLab141Gate-[a-f0-9]{32}\z"));
        }
    }
    public sealed class Receipt
    {
        public string Schema = "helper_owner141_result_v1", Status = "off";
        public int ExitCode, ChildExitCode;
        public bool ChildCreated, AtomicJobAssignment, ChildResumed, ReadyAcknowledged, HelperExitObserved;
        public bool CancelRequested, JobCloseAcknowledged, ForcedJobClosure;
        public bool? HelperClearAcknowledged, HelperCloseAcknowledged;
        public bool InventedPending, JournalFailed;
        public int JournalFrames;
        public bool NativeQuotesAvailable = false, OrdersAvailable = false, PowerPlanWrites = false;
    }
    public sealed class Trace : IDisposable
    {
        private readonly Stream file;
        private readonly Action sync;
        private bool poisoned;
        private string head = new String('0', 64);
        private readonly string job = Guid.NewGuid().ToString("N");
        public int Sequence { get; private set; }
        public Trace(string path)
        {
            string full = Path.GetFullPath(path);
            if (!System.Text.RegularExpressions.Regex.IsMatch(Path.GetFileName(full), @"\AOwner141-[a-f0-9]{32}\.journal\z"))
                throw new ArgumentException();
            for (DirectoryInfo p = new DirectoryInfo(Path.GetDirectoryName(full)); p != null; p = p.Parent)
                if ((p.Attributes & FileAttributes.ReparsePoint) != 0) throw new ArgumentException();
            file = new FileStream(full, FileMode.CreateNew, FileAccess.Write, FileShare.Read);
            sync = delegate { ((FileStream)file).Flush(true); };
        }
        internal Trace(Stream file, Action sync) { this.file = file; this.sync = sync; }
        public void Emit(string kind, long elapsed, int childPid, bool contained, bool ready, bool pending)
        {
            if (poisoned || Sequence >= 32 || elapsed < 0 || childPid < 0) throw new IOException();
            if (kind != "owner_started" && kind != "child_created_suspended" && kind != "child_resumed" &&
                kind != "helper_ready" && kind != "invented_triple_begin" && kind != "invented_triple_abort" && kind != "owner_stopped")
                throw new ArgumentException();
            var frame = new { Schema = "invented_owner141_event_v1", Job = job, Sequence = Sequence + 1,
                Previous = head, Event = kind, ElapsedMs = elapsed, HelperPid = childPid,
                Contained = contained, Ready = ready, InventedPending = pending };
            string payload = new JavaScriptSerializer().Serialize(frame);
            string checksum;
            using (SHA256 hash = SHA256.Create()) checksum = BitConverter.ToString(hash.ComputeHash(Encoding.UTF8.GetBytes(payload))).Replace("-", "").ToLowerInvariant();
            byte[] line = Encoding.UTF8.GetBytes(payload + "\t" + checksum + "\n");
            try
            {
                if (line.Length > 1024 || file.Length + line.Length > 32768) throw new IOException();
                file.Write(line, 0, line.Length); sync();
                head = checksum; Sequence++;
                Console.WriteLine(payload); Console.Out.Flush();
            }
            catch { poisoned = true; throw; }
        }
        public void Dispose() { file.Dispose(); }
    }

    public sealed class Child : IDisposable
    {
        [StructLayout(LayoutKind.Sequential)] private struct BasicLimits
        { public long ProcessTime, JobTime; public uint Flags; public UIntPtr MinWorking, MaxWorking; public uint Active; public UIntPtr Affinity; public uint Priority, Scheduling; }
        [StructLayout(LayoutKind.Sequential)] private struct IoCounters
        { public ulong ReadOps, WriteOps, OtherOps, ReadBytes, WriteBytes, OtherBytes; }
        [StructLayout(LayoutKind.Sequential)] private struct ExtendedLimits
        { public BasicLimits Basic; public IoCounters Io; public UIntPtr ProcessMemory, JobMemory, PeakProcess, PeakJob; }
        [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)] private struct Startup
        {
            public uint Size; public IntPtr Reserved, Desktop, Title;
            public uint X, Y, Width, Height, XChars, YChars, Fill, Flags;
            public ushort Show, ReservedSize; public IntPtr ReservedBytes, StdIn, StdOut, StdErr;
        }
        [StructLayout(LayoutKind.Sequential)] private struct StartupEx { public Startup Startup; public IntPtr Attributes; }
        [StructLayout(LayoutKind.Sequential)] private struct ProcessInfo { public IntPtr Process, Thread; public uint Pid, Tid; }
        [StructLayout(LayoutKind.Sequential)] private struct Security
        { public int Size; public IntPtr Descriptor; [MarshalAs(UnmanagedType.Bool)] public bool Inherit; }
        [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)] private static extern IntPtr CreateJobObjectW(IntPtr security, string name);
        [DllImport("kernel32.dll", SetLastError = true)] [return: MarshalAs(UnmanagedType.Bool)] private static extern bool SetInformationJobObject(IntPtr job, int kind, ref ExtendedLimits limits, uint size);
        [DllImport("kernel32.dll", SetLastError = true)] [return: MarshalAs(UnmanagedType.Bool)] private static extern bool InitializeProcThreadAttributeList(IntPtr list, int count, uint flags, ref IntPtr bytes);
        [DllImport("kernel32.dll", SetLastError = true)] [return: MarshalAs(UnmanagedType.Bool)] private static extern bool UpdateProcThreadAttribute(IntPtr list, uint flags, UIntPtr key, IntPtr value, IntPtr size, IntPtr previous, IntPtr returned);
        [DllImport("kernel32.dll")] private static extern void DeleteProcThreadAttributeList(IntPtr list);
        [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)] [return: MarshalAs(UnmanagedType.Bool)] private static extern bool CreateProcessW(string application, StringBuilder command, IntPtr processSecurity, IntPtr threadSecurity, bool inherit, uint flags, IntPtr environment, string directory, ref StartupEx startup, out ProcessInfo process);
        [DllImport("kernel32.dll", SetLastError = true)] [return: MarshalAs(UnmanagedType.Bool)] private static extern bool IsProcessInJob(IntPtr process, IntPtr job, out bool result);
        [DllImport("kernel32.dll", SetLastError = true)] [return: MarshalAs(UnmanagedType.Bool)] private static extern bool CreatePipe(out IntPtr reader, out IntPtr writer, ref Security security, uint size);
        [DllImport("kernel32.dll", SetLastError = true)] [return: MarshalAs(UnmanagedType.Bool)] private static extern bool SetHandleInformation(IntPtr handle, uint mask, uint value);
        [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)] private static extern IntPtr CreateFileW(string name, uint access, uint share, ref Security security, uint creation, uint attributes, IntPtr template);
        [DllImport("kernel32.dll")] private static extern uint ResumeThread(IntPtr thread);
        [DllImport("kernel32.dll")] private static extern uint WaitForSingleObject(IntPtr handle, uint timeout);
        [DllImport("kernel32.dll")] [return: MarshalAs(UnmanagedType.Bool)] private static extern bool GetExitCodeProcess(IntPtr process, out uint code);
        [DllImport("kernel32.dll")] [return: MarshalAs(UnmanagedType.Bool)] private static extern bool TerminateProcess(IntPtr process, uint code);
        [DllImport("kernel32.dll")] [return: MarshalAs(UnmanagedType.Bool)] private static extern bool CloseHandle(IntPtr handle);
        [DllImport("kernel32.dll")] private static extern ulong GetTickCount64();
        public static long Now { get { return checked((long)GetTickCount64()); } }
        public static int ExtendedSize { get { return Marshal.SizeOf(typeof(ExtendedLimits)); } }
        public static int StartupSize { get { return Marshal.SizeOf(typeof(StartupEx)); } }
        private IntPtr job, process, thread;
        private StreamReader output;
        public int Pid { get; private set; }
        public bool Contained { get; private set; }
        public bool Resumed { get; private set; }
        public bool JobCloseAcknowledged { get; private set; }

        public void Create(string application, string commandArguments)
        {
            IntPtr attributes = IntPtr.Zero, jobArray = IntPtr.Zero, handles = IntPtr.Zero;
            IntPtr reader = IntPtr.Zero, writer = IntPtr.Zero, nul = IntPtr.Zero;
            bool initialized = false;
            try
            {
                job = CreateJobObjectW(IntPtr.Zero, null); if (job == IntPtr.Zero) throw new IOException();
                ExtendedLimits limits = new ExtendedLimits(); limits.Basic.Flags = 0x2000 | 8; limits.Basic.Active = 1;
                if (!SetInformationJobObject(job, 9, ref limits, (uint)Marshal.SizeOf(typeof(ExtendedLimits)))) throw new IOException();
                Security security = new Security { Size = Marshal.SizeOf(typeof(Security)), Inherit = true };
                if (!CreatePipe(out reader, out writer, ref security, 4096) || !SetHandleInformation(reader, 1, 0)) throw new IOException();
                nul = CreateFileW("NUL", 0x80000000, 3, ref security, 3, 0, IntPtr.Zero);
                if (nul == new IntPtr(-1)) { nul = IntPtr.Zero; throw new IOException(); }
                IntPtr size = IntPtr.Zero; InitializeProcThreadAttributeList(IntPtr.Zero, 2, 0, ref size);
                if (size == IntPtr.Zero) throw new IOException();
                attributes = Marshal.AllocHGlobal(size);
                if (!InitializeProcThreadAttributeList(attributes, 2, 0, ref size)) throw new IOException();
                initialized = true;
                jobArray = Marshal.AllocHGlobal(IntPtr.Size); Marshal.WriteIntPtr(jobArray, job);
                handles = Marshal.AllocHGlobal(2 * IntPtr.Size); Marshal.WriteIntPtr(handles, writer); Marshal.WriteIntPtr(handles, IntPtr.Size, nul);
                // Job membership is assigned inside CreateProcess, not in a racy post-launch attach.
                if (!UpdateProcThreadAttribute(attributes, 0, new UIntPtr(0x2000d), jobArray, new IntPtr(IntPtr.Size), IntPtr.Zero, IntPtr.Zero) ||
                    !UpdateProcThreadAttribute(attributes, 0, new UIntPtr(0x20002), handles, new IntPtr(2 * IntPtr.Size), IntPtr.Zero, IntPtr.Zero)) throw new IOException();
                StartupEx startup = new StartupEx(); startup.Startup.Size = (uint)Marshal.SizeOf(typeof(StartupEx));
                startup.Startup.Flags = 0x100; startup.Startup.StdIn = nul; startup.Startup.StdOut = writer; startup.Startup.StdErr = writer;
                startup.Attributes = attributes;
                ProcessInfo info;
                if (!CreateProcessW(application, new StringBuilder("\"" + application + "\" " + commandArguments), IntPtr.Zero, IntPtr.Zero,
                    true, 0x80000 | 0x08000000 | 4, IntPtr.Zero, Path.GetDirectoryName(application), ref startup, out info)) throw new IOException();
                process = info.Process; thread = info.Thread; Pid = checked((int)info.Pid);
                bool member; Contained = IsProcessInJob(process, job, out member) && member;
                if (!Contained) throw new IOException();
                SafeFileHandle ownedReader = new SafeFileHandle(reader, true); reader = IntPtr.Zero;
                try { output = new StreamReader(new FileStream(ownedReader, FileAccess.Read)); }
                catch { ownedReader.Dispose(); throw; }
            }
            catch { Dispose(); throw; }
            finally
            {
                if (writer != IntPtr.Zero) CloseHandle(writer); if (reader != IntPtr.Zero) CloseHandle(reader); if (nul != IntPtr.Zero) CloseHandle(nul);
                if (initialized) DeleteProcThreadAttributeList(attributes);
                if (attributes != IntPtr.Zero) Marshal.FreeHGlobal(attributes);
                if (jobArray != IntPtr.Zero) Marshal.FreeHGlobal(jobArray); if (handles != IntPtr.Zero) Marshal.FreeHGlobal(handles);
            }
        }
        public void Resume()
        { if (!Contained || ResumeThread(thread) != 1) throw new IOException(); Resumed = true; CloseHandle(thread); thread = IntPtr.Zero; }
        public bool Exited(int milliseconds)
        { return process != IntPtr.Zero && WaitForSingleObject(process, (uint)milliseconds) == 0; }
        public int ExitCode()
        { uint code; if (!GetExitCodeProcess(process, out code)) throw new IOException(); return unchecked((int)code); }
        public Dictionary<string, object> ReadReceipt()
        {
            if (!Exited(0)) return null;
            char[] buffer = new char[4097]; int used = 0, count;
            while (used < buffer.Length && (count = output.Read(buffer, used, buffer.Length - used)) > 0) used += count;
            if (used >= buffer.Length) return null;
            try
            {
                var parsed = new JavaScriptSerializer().Deserialize<Dictionary<string, object>>(new string(buffer, 0, used));
                if (parsed == null || !parsed.ContainsKey("Schema") || (string)parsed["Schema"] != "keep_awake139_result_v1") return null;
                return parsed;
            }
            catch { return null; }
        }
        public void CloseJob()
        { if (job != IntPtr.Zero) { IntPtr owned = job; job = IntPtr.Zero; JobCloseAcknowledged = CloseHandle(owned); } }
        public void Dispose()
        {
            CloseJob();
            if (process != IntPtr.Zero && !Exited(5000)) { TerminateProcess(process, 2); Exited(5000); }
            if (thread != IntPtr.Zero) { CloseHandle(thread); thread = IntPtr.Zero; }
            if (process != IntPtr.Zero) { CloseHandle(process); process = IntPtr.Zero; }
            if (output != null) { output.Dispose(); output = null; }
        }
    }

    public static class Owner
    {
        private static FileStream Verify(Options o)
        {
            if (!Path.IsPathRooted(o.Helper) || o.Helper.StartsWith(@"\\") || o.Helper.IndexOfAny(new char[] { '"', '\r', '\n', '\0' }) >= 0 ||
                Path.GetFileName(o.Helper) != "ForexDemoKeepAwake139.exe" ||
                !System.Text.RegularExpressions.Regex.IsMatch(o.Sha256, @"\A[a-f0-9]{64}\z")) throw new ArgumentException();
            FileStream input = new FileStream(o.Helper, FileMode.Open, FileAccess.Read, FileShare.Read);
            try
            {
                using (SHA256 sha = SHA256.Create())
                    if (BitConverter.ToString(sha.ComputeHash(input)).Replace("-", "").ToLowerInvariant() != o.Sha256) throw new ArgumentException();
                return input; // Keep write/replacement excluded through process creation.
            }
            catch { input.Dispose(); throw; }
        }
        private static bool? Flag(Dictionary<string, object> receipt, string name)
        { return receipt != null && receipt.ContainsKey(name) && receipt[name] is bool ? (bool?)receipt[name] : null; }
        public static Receipt Run(Options o)
        {
            Receipt r = new Receipt();
            if (!Options.Valid(o)) { r.Status = "invalid_configuration"; r.ExitCode = 2; return r; }
            if (!o.Enabled) return r;
            if (IntPtr.Size != 8 || Environment.OSVersion.Platform != PlatformID.Win32NT)
            { r.Status = "windows_x64_required"; r.ExitCode = 2; return r; }
            long start = Child.Now; Child child = new Child(); Trace trace = null;
            EventWaitHandle helperCancel = null, ready = null, externalCancel = null, gate = null;
            Action<string> emit = delegate(string kind) {
                trace.Emit(kind, Child.Now - start, child.Pid, child.Contained, r.ReadyAcknowledged, r.InventedPending);
            };
            try
            {
                if (o.CancelEvent != "") externalCancel = EventWaitHandle.OpenExisting(o.CancelEvent);
                if (o.GateEvent != "") gate = EventWaitHandle.OpenExisting(o.GateEvent);
                using (FileStream pinned = Verify(o))
                {
                    trace = new Trace(o.Journal); emit("owner_started");
                    string token = Guid.NewGuid().ToString("N");
                    string cancelName = @"Local\ForexDemoLab139Cancel-" + token, readyName = @"Local\ForexDemoLab139Ready-" + token;
                    helperCancel = new EventWaitHandle(false, EventResetMode.ManualReset, cancelName);
                    ready = new EventWaitHandle(false, EventResetMode.ManualReset, readyName);
                    child.Create(o.Helper, "--enable --seconds " + o.Seconds + " --cancel-event " + cancelName + " --ready-event " + readyName);
                    r.ChildCreated = true; r.AtomicJobAssignment = child.Contained; emit("child_created_suspended");
                    long pauseEnd = Math.Min(10000, (long)o.Seconds * 1000);
                    while (gate != null && !gate.WaitOne(0))
                    {
                        if (externalCancel != null && externalCancel.WaitOne(0)) { r.Status = "cancelled"; return r; }
                        if (Child.Now - start >= pauseEnd) { r.Status = "gate_timeout"; r.ExitCode = 2; return r; }
                        Thread.Sleep(25);
                    }
                    if (Child.Now - start >= (long)o.Seconds * 1000) { r.Status = "deadline"; return r; }
                    child.Resume(); r.ChildResumed = true; emit("child_resumed");
                }
                while (true)
                {
                    if (child.Exited(0)) { r.Status = "helper_exited"; break; }
                    if (externalCancel != null && externalCancel.WaitOne(0)) { r.Status = "cancelled"; break; }
                    long elapsed = Child.Now - start;
                    if (elapsed >= (long)o.Seconds * 1000) { r.Status = "deadline"; break; }
                    if (!r.ReadyAcknowledged && elapsed >= 10000) { r.Status = "readiness_timeout"; r.ExitCode = 2; break; }
                    if (!r.ReadyAcknowledged && ready.WaitOne(0))
                    { r.ReadyAcknowledged = true; emit("helper_ready"); r.InventedPending = true; emit("invented_triple_begin"); }
                    Thread.Sleep(25);
                }
            }
            catch (Exception) { r.Status = "setup_or_io_failed"; r.ExitCode = 2; }
            finally
            {
                if (trace != null && r.InventedPending)
                {
                    r.InventedPending = false;
                    try { emit("invented_triple_abort"); } catch { r.JournalFailed = true; r.ExitCode = 2; }
                }
                if (child.Pid != 0)
                {
                    if (!child.Exited(0) && child.Resumed && helperCancel != null)
                    { try { r.CancelRequested = helperCancel.Set(); } catch { r.ExitCode = 2; } }
                    if (!child.Exited(1000)) { r.ForcedJobClosure = true; child.CloseJob(); }
                    r.HelperExitObserved = child.Exited(5000);
                    if (r.HelperExitObserved)
                    {
                        r.ChildExitCode = child.ExitCode();
                        var receipt = child.ReadReceipt();
                        r.HelperClearAcknowledged = Flag(receipt, "ClearAcknowledged"); r.HelperCloseAcknowledged = Flag(receipt, "CloseAcknowledged");
                        if (!r.ReadyAcknowledged || r.HelperClearAcknowledged != true || r.HelperCloseAcknowledged != true) r.ExitCode = 2;
                    }
                    else r.ExitCode = 2;
                }
                child.CloseJob(); r.JobCloseAcknowledged = child.JobCloseAcknowledged;
                if (trace != null)
                {
                    try { emit("owner_stopped"); }
                    catch { r.JournalFailed = true; r.ExitCode = 2; }
                    finally
                    {
                        r.JournalFrames = trace.Sequence;
                        try { trace.Dispose(); } catch { r.JournalFailed = true; r.ExitCode = 2; }
                    }
                }
                child.Dispose();
                if (helperCancel != null) helperCancel.Dispose(); if (ready != null) ready.Dispose();
                if (externalCancel != null) externalCancel.Dispose(); if (gate != null) gate.Dispose();
            }
            return r;
        }
    }
    public static class Program
    {
        public static int Main(string[] args)
        {
            Options o = new Options();
            try
            {
                for (int i = 0; i < args.Length; i++)
                {
                    if (args[i] == "--enable" && !o.Enabled) o.Enabled = true;
                    else if (args[i] == "--seconds" && i + 1 < args.Length) o.Seconds = Int32.Parse(args[++i]);
                    else if (args[i] == "--helper" && i + 1 < args.Length) o.Helper = args[++i];
                    else if (args[i] == "--sha256" && i + 1 < args.Length) o.Sha256 = args[++i];
                    else if (args[i] == "--journal" && i + 1 < args.Length) o.Journal = args[++i];
                    else if (args[i] == "--cancel-event" && i + 1 < args.Length) o.CancelEvent = args[++i];
                    else if (args[i] == "--gate-event" && i + 1 < args.Length) o.GateEvent = args[++i];
                    else throw new ArgumentException();
                }
                Receipt result = Owner.Run(o); Console.WriteLine(new JavaScriptSerializer().Serialize(result)); return result.ExitCode;
            }
            catch { Console.WriteLine("{\"Schema\":\"helper_owner141_result_v1\",\"Status\":\"invalid_configuration\",\"ExitCode\":2}"); return 2; }
        }
    }
}
