using System;
using System.Collections.Generic;
using System.IO;
using System.IO.MemoryMappedFiles;
using System.Security.Cryptography;
using System.Threading;
using System.Threading.Tasks;
using System.Web.Script.Serialization;
using ForexDemoLab.KeepAwake139;
using ForexDemoLab.HelperOwner141;

namespace ForexDemoLab.HelperHealth142
{
    // One owner-created volatile slot. Never a market-data payload or durable acknowledgement.
    public sealed class Slot : IDisposable
    {
        private readonly MemoryMappedFile mapping;
        private readonly MemoryMappedViewAccessor view;
        private long version;
        public static bool Token(string value)
        { return value != null && System.Text.RegularExpressions.Regex.IsMatch(value, @"\A[a-f0-9]{32}\z"); }
        public Slot(string token, bool create)
        {
            if (!Token(token)) throw new ArgumentException();
            string name = @"Local\ForexDemoLab142Status-" + token;
            mapping = create ? MemoryMappedFile.CreateNew(name, 32) : MemoryMappedFile.OpenExisting(name, MemoryMappedFileRights.ReadWrite);
            try { view = mapping.CreateViewAccessor(0, 32, MemoryMappedFileAccess.ReadWrite); }
            catch { mapping.Dispose(); throw; }
        }
        public void Publish(long tick, long flags)
        {
            if (tick < 0 || flags < 0 || flags > 31 || version > Int64.MaxValue - 2) throw new IOException();
            view.Write(0, version + 1); Thread.MemoryBarrier();
            view.Write(8, tick); view.Write(16, flags); Thread.MemoryBarrier();
            version += 2; view.Write(0, version);
        }
        public bool Read(out long sequence, out long tick, out long flags)
        {
            sequence = tick = flags = 0;
            for (int i = 0; i < 4; i++)
            {
                long first = view.ReadInt64(0); Thread.MemoryBarrier();
                long time = view.ReadInt64(8), bits = view.ReadInt64(16); Thread.MemoryBarrier();
                long last = view.ReadInt64(0);
                if (first > 0 && first == last && first % 2 == 0 && time >= 0 && bits >= 0 && bits <= 31)
                { sequence = first / 2; tick = time; flags = bits; return true; }
            }
            return false;
        }
        public void Dispose() { view.Dispose(); mapping.Dispose(); }
    }
    public sealed class PublishingPower : IPowerBackend
    {
        private readonly IPowerBackend backend;
        private readonly Slot slot;
        private long flags = 16;
        public PublishingPower(IPowerBackend backend, Slot slot) { this.backend = backend; this.slot = slot; }
        private void Publish() { slot.Publish(Child.Now, flags); }
        public AcState ReadPower()
        { AcState state = backend.ReadPower(); flags = state == AcState.Mains ? flags | 8 : flags & ~8L; Publish(); return state; }
        public bool Create() { bool ok = backend.Create(); if (ok) flags |= 1; Publish(); return ok; }
        public bool Set() { bool ok = backend.Set(); if (ok) flags |= 2; Publish(); return ok; }
        public bool Ready(Func<bool> signal) { bool ok = signal(); if (ok) flags |= 4; Publish(); return ok; }
        public bool Clear() { bool ok = backend.Clear(); flags &= ~6L; Publish(); return ok; }
        public bool Close() { bool ok = backend.Close(); flags = 0; Publish(); return ok; }
    }
    public static class HelperProgram
    {
        public static int Main(string[] args)
        {
            bool enabled = false; int seconds = 60; string token = "", cancel = "", ready = "";
            try
            {
                for (int i = 0; i < args.Length; i++)
                {
                    if (args[i] == "--enable" && !enabled) enabled = true;
                    else if (args[i] == "--seconds" && i + 1 < args.Length) seconds = Int32.Parse(args[++i]);
                    else if (args[i] == "--token" && i + 1 < args.Length) token = args[++i];
                    else if (args[i] == "--cancel-event" && i + 1 < args.Length) cancel = args[++i];
                    else if (args[i] == "--ready-event" && i + 1 < args.Length) ready = args[++i];
                    else throw new ArgumentException();
                }
                if (seconds < 1 || seconds > 14400) throw new ArgumentException();
                if (!enabled) { Console.WriteLine(new JavaScriptSerializer().Serialize(new Result())); return 0; }
                if (!Slot.Token(token) || cancel != @"Local\ForexDemoLab139Cancel-" + token || ready != @"Local\ForexDemoLab139Ready-" + token)
                    throw new ArgumentException();
                bool held = false;
                using (Mutex mutex = new Mutex(false, NativeHost.MutexName))
                {
                    try
                    {
                        try { held = mutex.WaitOne(0); } catch (AbandonedMutexException) { held = true; }
                        if (!held) throw new IOException();
                        using (Slot slot = new Slot(token, false))
                        using (NativeCancellation cancellation = new NativeCancellation(cancel, ready))
                        {
                            PublishingPower power = new PublishingPower(new NativePower(), slot);
                            Result result = Runner.Run(true, (long)seconds * 1000, power, new NativeClock(), cancellation,
                                delegate { return power.Ready(cancellation.SignalReady); });
                            result.NativeBackend = true;
                            Console.WriteLine(new JavaScriptSerializer().Serialize(result)); return result.ExitCode;
                        }
                    }
                    finally { if (held) mutex.ReleaseMutex(); }
                }
            }
            catch { Console.WriteLine("{\"Schema\":\"keep_awake139_result_v1\",\"Status\":\"health142_setup_failed\",\"ExitCode\":2}"); return 2; }
        }
    }
    public sealed class ExitReceipt
    {
        public string schema = "native_health142_exit_v1", token, challenge;
        public bool exit_observed, cancel_ack, job_closed;
        public bool? clear_ack, close_ack;
        public bool forced;
    }
    public static class OwnerProgram
    {
        private static readonly JavaScriptSerializer Json = new JavaScriptSerializer();
        private static void Send(object value) { Console.WriteLine(Json.Serialize(value)); Console.Out.Flush(); }
        private static string ReadCommand()
        {
            char[] buffer = new char[64]; int used = 0;
            while (true)
            {
                int next = Console.In.Read(); if (next == -1) return null;
                if (next == '\n') return new string(buffer, 0, used);
                if (used == buffer.Length || next > 127 || next == '\r') throw new IOException();
                buffer[used++] = (char)next;
            }
        }
        private static FileStream Pin(string path, string expected)
        {
            if (!Path.IsPathRooted(path) || path.StartsWith(@"\\") || Path.GetFileName(path) != "ForexDemoHealthHelper142.exe" ||
                path.IndexOfAny(new char[] { '"', '\r', '\n', '\0' }) >= 0 || expected == null ||
                !System.Text.RegularExpressions.Regex.IsMatch(expected, @"\A[a-f0-9]{64}\z")) throw new ArgumentException();
            FileStream input = new FileStream(path, FileMode.Open, FileAccess.Read, FileShare.Read);
            try
            {
                using (SHA256 sha = SHA256.Create())
                    if (BitConverter.ToString(sha.ComputeHash(input)).Replace("-", "").ToLowerInvariant() != expected) throw new IOException();
                return input;
            }
            catch { input.Dispose(); throw; }
        }
        private static bool? Flag(Dictionary<string, object> value, string key)
        { return value != null && value.ContainsKey(key) && value[key] is bool ? (bool?)value[key] : null; }
        public static int Main(string[] args)
        {
            bool enabled = false; string path = "", sha = "", token = ""; int seconds = 60;
            Child child = new Child(); Slot slot = null; EventWaitHandle cancel = null, ready = null;
            ExitReceipt receipt = new ExitReceipt(); int code = 0;
            try
            {
                for (int i = 0; i < args.Length; i++)
                {
                    if (args[i] == "--enable" && !enabled) enabled = true;
                    else if (args[i] == "--seconds" && i + 1 < args.Length) seconds = Int32.Parse(args[++i]);
                    else if (args[i] == "--helper" && i + 1 < args.Length) path = args[++i];
                    else if (args[i] == "--sha256" && i + 1 < args.Length) sha = args[++i];
                    else if (args[i] == "--token" && i + 1 < args.Length) token = args[++i];
                    else throw new ArgumentException();
                }
                if (seconds < 1 || seconds > 14400) throw new ArgumentException();
                if (!enabled) { Send(new { schema = "native_health142_off_v1" }); return 0; }
                if (IntPtr.Size != 8 || !Slot.Token(token)) throw new ArgumentException();
                receipt.token = token; long start = Child.Now;
                using (FileStream pinned = Pin(path, sha))
                {
                    slot = new Slot(token, true);
                    string cancelName = @"Local\ForexDemoLab139Cancel-" + token, readyName = @"Local\ForexDemoLab139Ready-" + token;
                    bool newCancel, newReady;
                    cancel = new EventWaitHandle(false, EventResetMode.ManualReset, cancelName, out newCancel);
                    ready = new EventWaitHandle(false, EventResetMode.ManualReset, readyName, out newReady);
                    if (!newCancel || !newReady) throw new IOException();
                    child.Create(path, "--enable --seconds " + seconds + " --token " + token + " --cancel-event " + cancelName + " --ready-event " + readyName);
                    child.Resume();
                    Send(new { schema = "native_health142_start_v1", token = token, contained = child.Contained, resumed = child.Resumed, helper_pid = child.Pid });
                }
                Task<string> input = Task.Factory.StartNew<string>(ReadCommand);
                while (Child.Now - start < (long)seconds * 1000)
                {
                    if (!input.Wait(25)) continue;
                    string command = input.GetAwaiter().GetResult(); if (command == null) break;
                    string[] parts = command.Split(' ');
                    if (parts.Length != 2 || !Slot.Token(parts[1])) throw new IOException();
                    string operation = parts[0], challenge = parts[1];
                    if (operation == "EXIT") { receipt.challenge = challenge; break; }
                    if (operation != "POLL" && operation != "CANCEL") throw new IOException();
                    bool cancelAck = operation == "CANCEL" && cancel.Set();
                    receipt.cancel_ack |= cancelAck;
                    long sequence, tick, flags; bool valid = slot.Read(out sequence, out tick, out flags);
                    long now = Child.Now; bool running = !child.Exited(0);
                    Send(new { schema = "native_health142_status_v1", token = token, challenge = challenge, operation = operation,
                        contained = child.Contained, running = running, sample_valid = valid, sample_sequence = sequence,
                        sample_tick_ms = tick, owner_tick_ms = now, create_ack = (flags & 1) != 0, set_ack = (flags & 2) != 0,
                        ready_signal = (flags & 4) != 0 && ready.WaitOne(0), mains = (flags & 8) != 0,
                        helper_running_marker = (flags & 16) != 0, cancel_ack = cancelAck });
                    input = Task.Factory.StartNew<string>(ReadCommand);
                }
            }
            catch { code = 2; }
            finally
            {
                try
                {
                    if (child.Pid != 0)
                    {
                        if (!child.Exited(0) && cancel != null) receipt.cancel_ack |= cancel.Set();
                        if (!child.Exited(1000)) { receipt.forced = true; child.CloseJob(); }
                        receipt.exit_observed = child.Exited(5000);
                        if (receipt.exit_observed)
                        {
                            var result = child.ReadReceipt(); receipt.clear_ack = Flag(result, "ClearAcknowledged");
                            receipt.close_ack = Flag(result, "CloseAcknowledged");
                        }
                    }
                    child.CloseJob(); receipt.job_closed = child.JobCloseAcknowledged;
                }
                catch { code = 2; }
                finally
                {
                    child.Dispose(); if (slot != null) slot.Dispose();
                    if (cancel != null) cancel.Dispose(); if (ready != null) ready.Dispose();
                }
                if (enabled) Send(receipt);
            }
            return code;
        }
    }
}
