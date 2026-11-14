using System;
using System.IO;
using System.IO.MemoryMappedFiles;
using System.Web.Script.Serialization;
using ForexDemoLab.KeepAwake139;
using ForexDemoLab.HelperHealth142;

namespace ForexDemoLab.HelperHealth142Testing
{
    public sealed class FakePower : IPowerBackend
    {
        public AcState Power = AcState.Mains;
        public bool SetOk = true;
        public bool Create() { return true; }
        public bool Set() { return SetOk; }
        public bool Clear() { return true; }
        public bool Close() { return true; }
        public AcState ReadPower() { return Power; }
    }
    public static class Program
    {
        private static void Check(bool ok) { if (!ok) throw new InvalidOperationException(); }
        public static int Main()
        {
            int cases = 0; bool passed = false;
            try
            {
                Check(!Slot.Token(null) && !Slot.Token("invalid") && Slot.Token(new string('a',32))); cases++;
                string token = Guid.NewGuid().ToString("N");
                using (Slot owner = new Slot(token, true))
                using (Slot publisher = new Slot(token, false))
                {
                    long sequence, tick, flags;
                    Check(!owner.Read(out sequence,out tick,out flags)); cases++;
                    publisher.Publish(100, 31); Check(owner.Read(out sequence,out tick,out flags) && sequence==1 && tick==100 && flags==31); cases++;
                    publisher.Publish(101, 16); Check(owner.Read(out sequence,out tick,out flags) && sequence==2 && tick==101 && flags==16); cases++;
                    foreach (long invalid in new long[] {-1,32})
                    { bool rejected=false;try { publisher.Publish(102,invalid); } catch(IOException) { rejected=true; } Check(rejected); cases++; }
                    using (MemoryMappedFile map=MemoryMappedFile.OpenExisting(@"Local\ForexDemoLab142Status-"+token))
                    using (MemoryMappedViewAccessor view=map.CreateViewAccessor())
                    { view.Write(0,5L); Check(!owner.Read(out sequence,out tick,out flags)); cases++; }
                }
                token=Guid.NewGuid().ToString("N");
                using (Slot owner=new Slot(token,true))
                using (Slot publisher=new Slot(token,false))
                {
                    FakePower fake=new FakePower(); PublishingPower power=new PublishingPower(fake,publisher);
                    long sequence,tick,flags;
                    power.ReadPower(); power.Create(); fake.SetOk=false; power.Set();
                    Check(owner.Read(out sequence,out tick,out flags) && flags==25); cases++;
                    fake.SetOk=true; power.Set(); power.Ready(delegate{return true;});
                    Check(owner.Read(out sequence,out tick,out flags) && flags==31); cases++;
                    fake.Power=AcState.Battery;power.ReadPower();
                    Check(owner.Read(out sequence,out tick,out flags) && flags==23); cases++;
                    power.Clear();Check(owner.Read(out sequence,out tick,out flags) && flags==17);cases++;
                    power.Close();Check(owner.Read(out sequence,out tick,out flags) && flags==0);cases++;
                }
                passed=true;
            }
            catch { passed=false; }
            Console.WriteLine(new JavaScriptSerializer().Serialize(new {schema="health142_slot_tests_v1",passed=passed,cases=cases,native_power_requests=0}));
            return passed?0:2;
        }
    }
}
