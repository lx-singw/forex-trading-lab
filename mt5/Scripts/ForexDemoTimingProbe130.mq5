#property copyright "Forex Demo Lab"
#property version "1.000"
#property strict
#property script_show_inputs
#property description "Private demo quote and clock timing diagnostic. No orders or history."
#include "PrivateGuard107.mqh"
#include "TimingRun130.mqh"

input bool CollectEvidence = false;
union NativeDouble130 { double value; ulong bits; };
TimingClock130 clock130;
long private_login130=0;
string private_server130="";
int file130=INVALID_HANDLE;
int guard_checks130=0;
int open_reason130=14;
ulong bytes130=0;
string chain130="0000000000000000000000000000000000000000000000000000000000000000";
long bs130=0,as130=0,gs130=0;
ulong bu130=0,au130=0,gu130=0;

string Hex130(const double value)
{
   NativeDouble130 u;u.value=value;return StringFormat("%.16I64X",u.bits);
}
string Digest130(const string text)
{
   uchar src[],key[],dst[];
   if(StringToCharArray(text,src,0,StringLen(text),CP_UTF8)!=StringLen(text)) return "";
   ResetLastError();
   if(CryptEncode(CRYPT_HASH_SHA256,src,key,dst)!=32 || GetLastError()!=0) return "";
   string result="";
   for(int i=0;i<32;i++) result+=StringFormat("%.2X",dst[i]);
   return result;
}
int Guard130(const bool identified)
{
   PrivateAccount107 s;s.query_ok=true;guard_checks130++;
   ResetLastError();s.connected=(bool)TerminalInfoInteger(TERMINAL_CONNECTED);s.query_ok=s.query_ok && GetLastError()==0;
   ResetLastError();s.algo=(bool)TerminalInfoInteger(TERMINAL_TRADE_ALLOWED);s.query_ok=s.query_ok && GetLastError()==0;
   ResetLastError();s.tester=(bool)MQLInfoInteger(MQL_TESTER);s.query_ok=s.query_ok && GetLastError()==0;
   ResetLastError();s.mode=AccountInfoInteger(ACCOUNT_TRADE_MODE);s.query_ok=s.query_ok && GetLastError()==0;
   ResetLastError();s.currency=AccountInfoString(ACCOUNT_CURRENCY);s.query_ok=s.query_ok && GetLastError()==0;
   ResetLastError();s.login=AccountInfoInteger(ACCOUNT_LOGIN);s.query_ok=s.query_ok && GetLastError()==0;
   ResetLastError();s.server=AccountInfoString(ACCOUNT_SERVER);s.query_ok=s.query_ok && GetLastError()==0;
   s.symbol=_Symbol;
   ResetLastError();s.visible=(bool)SymbolInfoInteger("EURUSD",SYMBOL_VISIBLE);s.query_ok=s.query_ok && GetLastError()==0;
   ResetLastError();s.base=SymbolInfoString("EURUSD",SYMBOL_CURRENCY_BASE);s.query_ok=s.query_ok && GetLastError()==0;
   ResetLastError();s.quote=SymbolInfoString("EURUSD",SYMBOL_CURRENCY_PROFIT);s.query_ok=s.query_ok && GetLastError()==0;
   return GuardReason107(s,identified,private_login130,private_server130);
}
int Now130()
{
   long seconds=(long)TimeGMT();ulong micros=GetMicrosecondCount();
   return CheckTimingClock130(clock130,seconds,micros,TimeToString((datetime)seconds,TIME_DATE));
}
void Status130(const int reason)
{
   PrintFormat("FXDL130 {\"reason_code\":%d,\"queries\":%d,\"guard_checks\":%d,\"bytes\":%I64u}",
               reason,clock130.queries,guard_checks130,bytes130);
}
bool Append130(const string payload)
{
   string next=Digest130(chain130+"\t"+payload+"\n");
   if(StringLen(next)!=64) return false;
   string line=payload+"\t"+next+"\r\n";
   if(StringLen(line)>2048 || bytes130+(ulong)StringLen(line)>131072) return false;
   ResetLastError();ulong size=FileSize(file130);int error=GetLastError();
   if(error!=0 || size!=bytes130) return false;
   ResetLastError();uint written=FileWriteString(file130,line);
   if(written!=(uint)StringLen(line) || GetLastError()!=0) return false;
   ResetLastError();FileFlush(file130);
   if(GetLastError()!=0) return false;
   bytes130+=written;chain130=next;return true;
}
bool Stop130(const int reason)
{
   bool saved=false;
   if(file130!=INVALID_HANDLE)
   {
      saved=Append130(StringFormat("S\t%d\t%d",reason,clock130.queries));
      FileClose(file130);file130=INVALID_HANDLE;
   }
   Status130(saved?reason:14);return false;
}
bool Begin130(const string tag,const string key)
{
   int reason=IsStopped()?18:Guard130(true);
   if(reason==0) reason=Now130();
   if(reason==0) reason=NextTimingQuery130(clock130);
   if(reason!=0) return Stop130(reason);
   if(!Append130(StringFormat("A\t%d\t%s\t%s",clock130.queries,tag,key))) return Stop130(14);
   reason=Guard130(true);
   bs130=(long)TimeGMT();bu130=GetMicrosecondCount();
   if(reason==0) reason=CheckTimingClock130(clock130,bs130,bu130,TimeToString((datetime)bs130,TIME_DATE));
   if(reason==0 && tag=="C" && key=="before") reason=MarkPollStart130(clock130,bu130);
   if(reason!=0) return Stop130(reason);
   return true;
}
bool After130()
{
   au130=GetMicrosecondCount();as130=(long)TimeGMT();
   int reason=IsStopped()?18:Guard130(true);
   gu130=GetMicrosecondCount();gs130=(long)TimeGMT();
   if(reason==0) reason=CheckTimingClock130(clock130,as130,au130,TimeToString((datetime)as130,TIME_DATE));
   if(reason==0) reason=CheckTimingClock130(clock130,gs130,gu130,TimeToString((datetime)gs130,TIME_DATE));
   if(reason!=0) return Stop130(reason); // Queried value is never serialized on a failed after-read guard.
   return true;
}
bool Record130(const string tag,const string key,const bool ok,const int error,const string value)
{
   string row=StringFormat("%s\t%d\t%s\t%I64d\t%I64d\t%I64d\t%I64u\t%I64u\t%I64u\t%d\t%d\t%s",
                          tag,clock130.queries,key,bs130,as130,gs130,bu130,au130,gu130,ok?1:0,error,value);
   if(!Append130(row)) return Stop130(14);
   return true;
}
bool Clocks130(const string key)
{
   if(!Begin130("C",key)) return false;
   ResetLastError();long tc=(long)TimeCurrent(),ts=(long)TimeTradeServer(),tg=(long)TimeGMT(),tl=(long)TimeLocal();
   long go=(long)TimeGMTOffset(),ds=(long)TimeDaylightSavings();int error=GetLastError();
   if(!After130()) return false;
   if(error!=0) return Stop130(12);
   return Record130("C",key,true,0,StringFormat("%I64d\t%I64d\t%I64d\t%I64d\t%I64d\t%I64d",tc,ts,tg,tl,go,ds));
}
bool Tick130()
{
   if(!Begin130("T","quote")) return false;
   MqlTick tick;
   ResetLastError();bool ok=SymbolInfoTick("EURUSD",tick);int error=GetLastError();
   if(!After130()) return false;
   if(!ok || error!=0) return Stop130(15);
   bool finite=MathIsValidNumber(tick.bid) && MathIsValidNumber(tick.ask) &&
               MathIsValidNumber(tick.last) && MathIsValidNumber(tick.volume_real);
   int reason=QuoteReason107((long)tick.time,tick.time_msc,tick.bid,tick.ask,tick.last,tick.volume_real,finite);
   if(reason!=0) return Stop130(reason);
   return Record130("T","quote",true,0,StringFormat("%I64d\t%I64d\t%s\t%s\t%s\t%I64u\t%u\t%s",
      (long)tick.time,tick.time_msc,Hex130(tick.bid),Hex130(tick.ask),Hex130(tick.last),
      tick.volume,tick.flags,Hex130(tick.volume_real)));
}
bool WaitPoll130()
{
   while(true)
   {
      int reason=IsStopped()?18:Guard130(true);
      if(reason==0) reason=Now130();
      if(reason!=0) return Stop130(reason);
      if(PollReady130(clock130,GetMicrosecondCount())) return true;
      Sleep(50); // No catch-up; deadline and guards are checked after returning.
   }
}
bool Open130()
{
   ResetLastError();bool root_file=FileIsExist("ForexDemoLab130",0);int error=GetLastError();
   if(root_file || (error!=0 && error!=5018 && error!=5019)) return false;
   if(error!=5018)
   {
      ResetLastError();if(!FolderCreate("ForexDemoLab130",0) || GetLastError()!=0) return false;
   }
   string folder=StringFormat("ForexDemoLab130\\Run130-%I64d-%I64u-%I64u",clock130.origin_s,GetTickCount64(),clock130.origin_us);
   ResetLastError();bool exists=FileIsExist(folder,0);error=GetLastError();
   if(exists || (error!=0 && error!=5019)) return false;
   ResetLastError();if(!FolderCreate(folder,0) || GetLastError()!=0) return false;
   int reason=Guard130(true);if(reason==0) reason=Now130();
   if(reason!=0) {open_reason130=reason;return false;}
   string filename=folder+"\\Timing130.txt";
   ResetLastError();exists=FileIsExist(filename,0);error=GetLastError();
   if(exists || (error!=0 && error!=5019)) return false;
   ResetLastError();file130=FileOpen(filename,FILE_READ|FILE_WRITE|FILE_BIN|FILE_ANSI,0,CP_UTF8);
   if(file130==INVALID_HANDLE || GetLastError()!=0) return false;
   ResetLastError();ulong size=FileSize(file130);error=GetLastError();
   if(size!=0 || error!=0) {FileClose(file130);file130=INVALID_HANDLE;return false;}
   return Append130(StringFormat("H\tFXDL_TIMING130_V1\tmarket_declared\t2026.10.15\t%I64d\t%I64u",clock130.origin_s,clock130.origin_us));
}
void OnStart()
{
   InitTiming130(clock130,0,0);
   if(!CollectEvidence) {Status130(1);return;}
   if(Digest130("abc")!="BA7816BF8F01CFEA414140DE5DAE2223B00361A396177A9CB410FF61F20015AD" || Hex130(1.0)!="3FF0000000000000") {Status130(17);return;}
   int reason=Guard130(false);
   if(reason!=0) {Status130(reason);return;}
   ResetLastError();private_login130=AccountInfoInteger(ACCOUNT_LOGIN);int error=GetLastError();
   ResetLastError();private_server130=AccountInfoString(ACCOUNT_SERVER);error|=GetLastError();
   reason=Guard130(true);
   if(error!=0 || reason!=0) {Status130(reason!=0?reason:2);return;}
   InitTiming130(clock130,(long)TimeGMT(),GetMicrosecondCount());
   reason=Now130();if(reason!=0) {Status130(reason);return;}
   if(!Open130()) {if(file130!=INVALID_HANDLE) {FileClose(file130);file130=INVALID_HANDLE;}Status130(open_reason130);return;}
   for(int poll=0;poll<60;poll++)
   {
      if(!WaitPoll130() || !Clocks130("before") || !Tick130() || !Clocks130("after")) return;
   }
   reason=Guard130(true);if(reason==0) reason=Now130();
   if(reason!=0) {Stop130(reason);return;}
   if(!Append130(StringFormat("E\t%d\t%I64d\t%I64u",clock130.queries,clock130.last_s,clock130.last_us))) {Stop130(14);return;}
   FileClose(file130);file130=INVALID_HANDLE;Status130(0);
}
