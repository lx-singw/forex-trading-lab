using System;
using System.Web.Script.Serialization;

namespace ForexDemoLab.KeepAwake139
{
    public static class Program
    {
        public static int Main(string[] args)
        {
            bool enabled = false;
            int seconds = 60;
            string cancel = "", ready = "";
            try
            {
                for (int i = 0; i < args.Length; i++)
                {
                    if (args[i] == "--enable" && !enabled) enabled = true;
                    else if (args[i] == "--seconds" && i + 1 < args.Length)
                    {
                        if (!Int32.TryParse(args[++i], out seconds) || seconds < 1 || seconds > 14400)
                            throw new ArgumentException();
                    }
                    else if (args[i] == "--cancel-event" && i + 1 < args.Length && cancel == "") cancel = args[++i];
                    else if (args[i] == "--ready-event" && i + 1 < args.Length && ready == "") ready = args[++i];
                    else throw new ArgumentException();
                }
                Result result = NativeHost.Execute(enabled, (long)seconds * 1000, cancel, ready);
                Console.WriteLine(new JavaScriptSerializer().Serialize(result));
                return result.ExitCode;
            }
            catch (Exception)
            {
                Console.WriteLine("{\"Schema\":\"keep_awake139_result_v1\",\"Status\":\"invalid_configuration\",\"ExitCode\":2,\"OrdersAvailable\":false}");
                return 2;
            }
        }
    }
}
