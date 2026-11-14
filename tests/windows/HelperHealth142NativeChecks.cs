using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Threading;
using System.Web.Script.Serialization;

namespace ForexDemoLab.HelperHealth142NativeTesting
{
    public static class Program
    {
        private static readonly JavaScriptSerializer Json = new JavaScriptSerializer();
        private static void Check(bool value) { if (!value) throw new InvalidOperationException(); }
        private static string Q(string text) { if (text.IndexOf('"') >= 0) throw new ArgumentException(); return "\""+text+"\""; }
        private static Dictionary<string,object> Read(Process owner)
        {
            var task=owner.StandardOutput.ReadLineAsync();
            Check(task.Wait(10000) && task.Result!=null && task.Result.Length<=2048);
            return Json.Deserialize<Dictionary<string,object>>(task.Result);
        }
        private static Dictionary<string,object> Request(Process owner,string operation)
        {
            string challenge=Guid.NewGuid().ToString("N");owner.StandardInput.WriteLine(operation+" "+challenge);owner.StandardInput.Flush();
            var packet=Read(owner);Check((string)packet["challenge"]==challenge);return packet;
        }
        public static int Main(string[] args)
        {
            if(args.Length!=3)return 2;
            var cases=new List<object>();bool passed=false;string stage="start";int remaining=0;
            try
            {
                foreach(string name in new string[]{"native_status_progress","exact_helper_loss","actual_owner_loss","stdin_eof"})
                {
                    stage=name;Process owner=null,helper=null;
                    try
                    {
                        string token=Guid.NewGuid().ToString("N");
                        owner=new Process{StartInfo=new ProcessStartInfo(args[0],"--enable --seconds 15 --token "+token+" --helper "+Q(args[1])+" --sha256 "+args[2]){
                            UseShellExecute=false,CreateNoWindow=true,RedirectStandardInput=true,RedirectStandardOutput=true,RedirectStandardError=true}};
                        Check(owner.Start());owner.StandardInput.NewLine="\n";
                        var start=Read(owner);Check((bool)start["contained"] && (bool)start["resumed"]);
                        helper=Process.GetProcessById(Convert.ToInt32(start["helper_pid"]));IntPtr retained=helper.Handle;Check(retained!=IntPtr.Zero);
                        Dictionary<string,object> packet=null;
                        for(int i=0;i<40;i++)
                        {
                            packet=Request(owner,"POLL");if((bool)packet["ready_signal"])break;Thread.Sleep(25);
                        }
                        Check((bool)packet["ready_signal"] && (bool)packet["create_ack"] && (bool)packet["set_ack"] && (bool)packet["mains"]);
                        if(name=="actual_owner_loss")
                        {
                            Check(!helper.HasExited);owner.Kill();Check(owner.WaitForExit(5000) && helper.WaitForExit(5000));
                            cases.Add(new {name=name,passed=true,helper_exit_observed=true,managed_cleanup_receipt=false});
                        }
                        else
                        {
                            if(name=="native_status_progress")
                            {
                                long before=Convert.ToInt64(packet["sample_sequence"]);Thread.Sleep(600);packet=Request(owner,"POLL");
                                Check(Convert.ToInt64(packet["sample_sequence"])>before);
                                long age=Convert.ToInt64(packet["owner_tick_ms"])-Convert.ToInt64(packet["sample_tick_ms"]);Check(age>=0 && age<=1000);
                            }
                            if(name=="exact_helper_loss")
                            {helper.Kill();Check(helper.WaitForExit(5000));packet=Request(owner,"POLL");Check(!(bool)packet["running"]);}
                            Dictionary<string,object> exit;
                            if(name=="stdin_eof"){owner.StandardInput.Close();exit=Read(owner);}
                            else{Request(owner,"CANCEL");exit=Request(owner,"EXIT");}
                            Check((string)exit["schema"]=="native_health142_exit_v1" && (bool)exit["exit_observed"] && (bool)exit["job_closed"]);
                            Check(owner.WaitForExit(5000) && helper.WaitForExit(5000));
                            if(name=="exact_helper_loss")Check(exit["clear_ack"]==null && exit["close_ack"]==null);
                            else Check((bool)exit["clear_ack"] && (bool)exit["close_ack"]);
                            cases.Add(new {name=name,passed=true,exit_receipt=exit});
                        }
                    }
                    finally
                    {
                        if(owner!=null && !owner.HasExited){owner.Kill();owner.WaitForExit(5000);}
                        if(helper!=null && !helper.HasExited){helper.WaitForExit(5000);if(!helper.HasExited){helper.Kill();helper.WaitForExit(5000);}}
                        if(owner!=null){if(!owner.HasExited)remaining++;owner.Dispose();}
                        if(helper!=null){if(!helper.HasExited)remaining++;helper.Dispose();}
                    }
                }
                passed=remaining==0;
            }
            catch {passed=false;}
            Console.WriteLine(Json.Serialize(new {schema="health142_native_checks_v1",passed=passed,stage=stage,cases=cases,owned_processes_remaining=remaining,quotes=0,orders=0}));
            return passed?0:2;
        }
    }
}
