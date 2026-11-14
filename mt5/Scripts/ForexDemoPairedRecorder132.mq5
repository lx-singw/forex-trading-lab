#property copyright "Forex Demo Lab"
#property version "1.000"
#property strict
#property script_show_inputs
#property description "Private demo one-hour paired quote recorder. No orders or history."
#include "PrivateGuard107.mqh"
#include "PairedRun132.mqh"

input bool CollectEvidence = false;
union NativeDouble132 { double value; ulong bits; };
PairedClock132 clock132;
long private_login132=0;
string private_server132="";
int file132=INVALID_HANDLE;
int guard_checks132=0;
int open_reason132=14;
ulong bytes132=0;
string chain132="0000000000000000000000000000000000000000000000000000000000000000";
long bs132=0,as132=0,gs132=0;
ulong bu132=0,au132=0,gu132=0;

string Hex132(const double value)
{
   NativeDouble132 u;u.value=value;return StringFormat("%.16I64X",u.bits);
}
string Digest132(const string text)
{
   uchar src[],key[],dst[];
   if(StringToCharArray(text,src,0,StringLen(text),CP_UTF8)!=StringLen(text)) return "";
   ResetLastError();
   if(CryptEncode(CRYPT_HASH_SHA256,src,key,dst)!=32 || GetLastError()!=0) return "";
   string result="";
   for(int i=0;i<32;i++) result+=StringFormat("%.2X",dst[i]);
   return result;
}
int Guard132(const bool identified)
{
   PrivateAccount107 s;s.query_ok=true;guard_checks132++;
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
   return GuardReason107(s,identified,private_login132,private_server132);
}
int Now132()
{
   long seconds=(long)TimeGMT();ulong micros=GetMicrosecondCount();
   return CheckPairedClock132(clock132,seconds,micros,TimeToString((datetime)seconds,TIME_DATE));
}
void Status132(const int reason)
{
   PrintFormat("FXDL132 {\"reason_code\":%d,\"queries\":%d,\"guard_checks\":%d,\"bytes\":%I64u}",
               reason,clock132.queries,guard_checks132,bytes132);
}
bool Append132(const string payload)
{
   string next=Digest132(chain132+"\t"+payload+"\n");
   if(StringLen(next)!=64) return false;
   string line=payload+"\t"+next+"\r\n";
   if(ReservePairedBytes132(clock132,(ulong)StringLen(line))!=0) return false;
   ResetLastError();ulong size=FileSize(file132);int error=GetLastError();
   if(error!=0 || size!=bytes132) return false;
   ResetLastError();uint written=FileWriteString(file132,line);
   if(written!=(uint)StringLen(line) || GetLastError()!=0) return false;
   ResetLastError();FileFlush(file132);
   if(GetLastError()!=0) return false;
   bytes132+=written;chain132=next;return true;
}
bool Stop132(const int reason)
{
   bool saved=false;
   if(file132!=INVALID_HANDLE)
   {
      saved=reason!=14 && Append132(StringFormat("S\t%d\t%d",reason,clock132.queries));
      FileClose(file132);file132=INVALID_HANDLE;
   }
   EndPaired132(clock132);Status132(saved?reason:14);return false;
}
bool Begin132(const string tag,const string key)
{
   int reason=IsStopped()?18:Guard132(true);
   if(reason==0) reason=Now132();
   if(reason==0) reason=NextPairedQuery132(clock132);
   if(reason!=0) return Stop132(reason);
   if(!Append132(StringFormat("A\t%d\t%s\t%s",clock132.queries,tag,key))) return Stop132(14);
   reason=Guard132(true);
   bs132=(long)TimeGMT();bu132=GetMicrosecondCount();
   if(reason==0) reason=CheckPairedClock132(clock132,bs132,bu132,TimeToString((datetime)bs132,TIME_DATE));
   if(reason==0 && tag=="C" && key=="before") reason=MarkPollStart132(clock132,bu132);
   if(reason!=0) return Stop132(reason);
   return true;
}
bool After132()
{
   au132=GetMicrosecondCount();as132=(long)TimeGMT();
   int reason=IsStopped()?18:Guard132(true);
   gu132=GetMicrosecondCount();gs132=(long)TimeGMT();
   if(reason==0) reason=CheckPairedClock132(clock132,as132,au132,TimeToString((datetime)as132,TIME_DATE));
   if(reason==0) reason=CheckPairedClock132(clock132,gs132,gu132,TimeToString((datetime)gs132,TIME_DATE));
   if(reason!=0) return Stop132(reason); // Queried value is never serialized on a failed after-read guard.
   return true;
}
bool Record132(const string tag,const string key,const bool ok,const int error,const string value)
{
   string row=StringFormat("%s\t%d\t%s\t%I64d\t%I64d\t%I64d\t%I64u\t%I64u\t%I64u\t%d\t%d\t%s",
                          tag,clock132.queries,key,bs132,as132,gs132,bu132,au132,gu132,ok?1:0,error,value);
   if(!Append132(row)) return Stop132(14);
   if(CompletePairedQuery132(clock132)!=0) return Stop132(19);
   return true;
}
bool Clocks132(const string key)
{
   if(!Begin132("C",key)) return false;
   ResetLastError();long tc=(long)TimeCurrent(),ts=(long)TimeTradeServer(),tg=(long)TimeGMT(),tl=(long)TimeLocal();
   long go=(long)TimeGMTOffset(),ds=(long)TimeDaylightSavings();int error=GetLastError();
   if(!After132()) return false;
   if(error!=0) return Stop132(12);
   return Record132("C",key,true,0,StringFormat("%I64d\t%I64d\t%I64d\t%I64d\t%I64d\t%I64d",tc,ts,tg,tl,go,ds));
}
bool Tick132()
{
   if(!Begin132("T","quote")) return false;
   MqlTick tick;
   ResetLastError();bool ok=SymbolInfoTick("EURUSD",tick);int error=GetLastError();
   if(!After132()) return false;
   if(!ok || error!=0) return Stop132(15);
   bool finite=MathIsValidNumber(tick.bid) && MathIsValidNumber(tick.ask) &&
               MathIsValidNumber(tick.last) && MathIsValidNumber(tick.volume_real);
   int reason=QuoteReason107((long)tick.time,tick.time_msc,tick.bid,tick.ask,tick.last,tick.volume_real,finite);
   if(reason!=0) return Stop132(reason);
   return Record132("T","quote",true,0,StringFormat("%I64d\t%I64d\t%s\t%s\t%s\t%I64u\t%u\t%s",
      (long)tick.time,tick.time_msc,Hex132(tick.bid),Hex132(tick.ask),Hex132(tick.last),
      tick.volume,tick.flags,Hex132(tick.volume_real)));
}
bool WaitPoll132()
{
   while(true)
   {
      int reason=IsStopped()?18:Guard132(true);
      if(reason==0) reason=Now132();
      if(reason==0) reason=WaitState132(clock132);
      if(reason!=0) return Stop132(reason);
      if(PollReady132(clock132,GetMicrosecondCount())) return true;
      Sleep(50); // No catch-up; deadline and guards are checked after returning.
   }
}
bool Open132()
{
   ResetLastError();bool root_file=FileIsExist("ForexDemoLab132",0);int error=GetLastError();
   if(root_file || (error!=0 && error!=5018 && error!=5019)) return false;
   if(error!=5018)
   {
      ResetLastError();if(!FolderCreate("ForexDemoLab132",0) || GetLastError()!=0) return false;
   }
   string folder=StringFormat("ForexDemoLab132\\Run132-%I64d-%I64u-%I64u",clock132.origin_s,GetTickCount64(),clock132.origin_us);
   ResetLastError();bool exists=FileIsExist(folder,0);error=GetLastError();
   if(exists || (error!=0 && error!=5019)) return false;
   ResetLastError();if(!FolderCreate(folder,0) || GetLastError()!=0) return false;
   int reason=Guard132(true);if(reason==0) reason=Now132();
   if(reason!=0) {open_reason132=reason;return false;}
   string filename=folder+"\\Paired132.txt";
   ResetLastError();exists=FileIsExist(filename,0);error=GetLastError();
   if(exists || (error!=0 && error!=5019)) return false;
   ResetLastError();file132=FileOpen(filename,FILE_READ|FILE_WRITE|FILE_BIN|FILE_ANSI,0,CP_UTF8);
   if(file132==INVALID_HANDLE || GetLastError()!=0) return false;
   ResetLastError();ulong size=FileSize(file132);error=GetLastError();
   if(size!=0 || error!=0) {FileClose(file132);file132=INVALID_HANDLE;return false;}
   return Append132(StringFormat("H\tFXDL_PAIRED132_V1\tmarket_declared\t%s\t%I64d\t%I64u",TimeToString((datetime)clock132.origin_s,TIME_DATE),clock132.origin_s,clock132.origin_us));
}
void OnStart()
{
   InitPaired132(clock132,0,0);
   if(!CollectEvidence) {Status132(1);return;}
   if(Digest132("abc")!="BA7816BF8F01CFEA414140DE5DAE2223B00361A396177A9CB410FF61F20015AD" || Hex132(1.0)!="3FF0000000000000") {Status132(17);return;}
   int reason=Guard132(false);
   if(reason!=0) {Status132(reason);return;}
   ResetLastError();private_login132=AccountInfoInteger(ACCOUNT_LOGIN);int error=GetLastError();
   ResetLastError();private_server132=AccountInfoString(ACCOUNT_SERVER);error|=GetLastError();
   reason=Guard132(true);
   if(error!=0 || reason!=0) {Status132(reason!=0?reason:2);return;}
   InitPaired132(clock132,(long)TimeGMT(),GetMicrosecondCount());
   reason=Now132();if(reason!=0) {Status132(reason);return;}
   if(!Open132()) {if(file132!=INVALID_HANDLE) {FileClose(file132);file132=INVALID_HANDLE;}Status132(open_reason132);return;}
   for(int poll=0;poll<3600;poll++)
   {
      if(!WaitPoll132() || !Clocks132("before") || !Tick132() || !Clocks132("after")) return;
   }
   reason=Guard132(true);if(reason==0) reason=Now132();
   if(reason!=0) {Stop132(reason);return;}
   if(!Append132(StringFormat("E\t%d\t%I64d\t%I64u",clock132.queries,clock132.last_s,clock132.last_us))) {Stop132(14);return;}
   EndPaired132(clock132);FileClose(file132);file132=INVALID_HANDLE;Status132(0);
}
