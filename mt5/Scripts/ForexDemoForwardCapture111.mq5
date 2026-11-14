#property copyright "Forex Demo Lab"
#property version "1.000"
#property strict
#property script_show_inputs
#property description "One-hour private demo quote capture. No order capability."
#include "PrivateGuard107.mqh"
#include "PrivateRun111.mqh"

input bool CollectOneHour = false;
union NativeDouble111 { double value; ulong bits; };
Run111 run111;
int guards111=0;
ulong segment_bytes111=0;
string chain111="0000000000000000000000000000000000000000000000000000000000000000";
string NativeHex111(const double value)
{
   NativeDouble111 u; u.value=value;
   return StringFormat("%.16I64X",u.bits);
}

string Digest111(const string text)
{
   uchar src[],key[],dst[];
   if(StringToCharArray(text,src,0,StringLen(text),CP_UTF8) != StringLen(text)) return "";
   ResetLastError();
   if(CryptEncode(CRYPT_HASH_SHA256,src,key,dst) != 32 || GetLastError()!=0) return "";
   string result="";
   for(int i=0;i<32;i++) result+=StringFormat("%.2X",dst[i]);
   return result;
}

int ReadGuard111(const bool identified, const long login, const string server)
{
   PrivateAccount107 s; s.query_ok=true; guards111++;
   ResetLastError(); s.connected=(bool)TerminalInfoInteger(TERMINAL_CONNECTED); s.query_ok=s.query_ok && GetLastError()==0;
   ResetLastError(); s.algo=(bool)TerminalInfoInteger(TERMINAL_TRADE_ALLOWED); s.query_ok=s.query_ok && GetLastError()==0;
   ResetLastError(); s.tester=(bool)MQLInfoInteger(MQL_TESTER); s.query_ok=s.query_ok && GetLastError()==0;
   ResetLastError(); s.mode=AccountInfoInteger(ACCOUNT_TRADE_MODE); s.query_ok=s.query_ok && GetLastError()==0;
   ResetLastError(); s.currency=AccountInfoString(ACCOUNT_CURRENCY); s.query_ok=s.query_ok && GetLastError()==0;
   ResetLastError(); s.login=AccountInfoInteger(ACCOUNT_LOGIN); s.query_ok=s.query_ok && GetLastError()==0;
   ResetLastError(); s.server=AccountInfoString(ACCOUNT_SERVER); s.query_ok=s.query_ok && GetLastError()==0;
   s.symbol=_Symbol;
   ResetLastError(); s.visible=(bool)SymbolInfoInteger("EURUSD",SYMBOL_VISIBLE); s.query_ok=s.query_ok && GetLastError()==0;
   ResetLastError(); s.base=SymbolInfoString("EURUSD",SYMBOL_CURRENCY_BASE); s.query_ok=s.query_ok && GetLastError()==0;
   ResetLastError(); s.quote=SymbolInfoString("EURUSD",SYMBOL_CURRENCY_PROFIT); s.query_ok=s.query_ok && GetLastError()==0;
   return GuardReason107(s,identified,login,server);
}


void Status111(const int reason)
{
   PrintFormat("FXDL111 {\"reason_code\":%d,\"attempts\":%d,\"observations\":%d,\"segments\":%d,\"reserved_bytes\":%I64u,\"guard_checks\":%d}",
      reason,run111.attempts,run111.observed,run111.segments,run111.bytes,guards111);
}
int Now111()
{
   long seconds=(long)TimeGMT();ulong micros=GetMicrosecondCount();
   return Clock111(run111,seconds,micros,TimeToString((datetime)seconds,TIME_DATE));
}
bool Append111(const int handle,const string payload)
{
   string next=Digest111(chain111+"\t"+payload+"\n");
   if(StringLen(next)!=64) return false;
   string line=payload+"\t"+next+"\r\n";
   ResetLastError();ulong size=FileSize(handle);int error=GetLastError();
   if(error!=0 || size!=segment_bytes111) return false;
   if(Reserve111(run111,(ulong)StringLen(line),size)!=0) return false;
   ResetLastError();uint written=FileWriteString(handle,line);
   if(written!=(uint)StringLen(line) || GetLastError()!=0) return false;
   ResetLastError();FileFlush(handle);
   if(GetLastError()!=0) return false;
   segment_bytes111+=written;chain111=next;return true;
}
void Stop111(const int handle,const int reason)
{
   bool saved=false;
   if(handle!=INVALID_HANDLE) {
      saved=Append111(handle,StringFormat("S\t%d\t%d\t%d",reason,run111.attempts,run111.observed));
      FileClose(handle);
   }
   End111(run111);Status111(saved?reason:14);
}
bool FreshFolder111(const string path)
{
   ResetLastError();bool exists=FileIsExist(path,0);int error=GetLastError();
   if(exists || (error!=0 && error!=5019)) return false; // Includes an existing directory (5018).
   ResetLastError();return FolderCreate(path,0) && GetLastError()==0;
}
int Open111(const string folder,const long login,const string server)
{
   int reason=ReadGuard111(true,login,server);
   if(reason==0) reason=Now111();
   if(reason!=0) { Status111(reason);return INVALID_HANDLE; }
   reason=Segment111(run111);
   if(reason!=0) { Status111(reason);return INVALID_HANDLE; }
   string filename=folder+StringFormat("\\Segment111-%03d.txt",run111.segments);
   ResetLastError();bool exists=FileIsExist(filename,0);int error=GetLastError();
   if(exists || (error!=0 && error!=5019)) { Status111(14);return INVALID_HANDLE; }
   ResetLastError();int handle=FileOpen(filename,FILE_READ|FILE_WRITE|FILE_BIN|FILE_ANSI,0,CP_UTF8);
   if(handle==INVALID_HANDLE || GetLastError()!=0) {
      if(handle!=INVALID_HANDLE) FileClose(handle);
      Status111(14);return INVALID_HANDLE;
   }
   ResetLastError();ulong size=FileSize(handle);error=GetLastError();
   if(size!=0 || error!=0) { FileClose(handle);Status111(14);return INVALID_HANDLE; }
   segment_bytes111=0;
   string previous=chain111;
   string header=StringFormat("H\tFXDL111_V1\tmarket_declared\t2026.10.12\t%d\t%I64d\t%I64u\t%d\t%d\t%I64u\t%I64d\t%I64u\t%s",
      run111.segments,run111.origin_s,run111.origin_us,run111.attempts,run111.observed,
      run111.last_read_us,run111.last_s,run111.last_guard_us,previous);
   if(!Append111(handle,header)) { FileClose(handle);Status111(14);return INVALID_HANDLE; }
   reason=ReadGuard111(true,login,server);
   if(reason==0) reason=Now111();
   if(reason!=0) { Stop111(handle,reason);return INVALID_HANDLE; }
   return handle;
}
void OnStart()
{
   Init111(run111,0,0);
   if(!CollectOneHour) { Status111(1);return; }
   if(Digest111("abc")!="BA7816BF8F01CFEA414140DE5DAE2223B00361A396177A9CB410FF61F20015AD" ||
      NativeHex111(1.0)!="3FF0000000000000") { Status111(17);return; }
   int reason=ReadGuard111(false,0,"");
   if(reason!=0) { Status111(reason);return; }
   ResetLastError();long login=AccountInfoInteger(ACCOUNT_LOGIN);int error=GetLastError();
   ResetLastError();string server=AccountInfoString(ACCOUNT_SERVER);error|=GetLastError();
   reason=ReadGuard111(true,login,server);
   if(error!=0 || reason!=0) { Status111(reason!=0?reason:2);return; }
   long seconds=(long)TimeGMT();ulong micros=GetMicrosecondCount();
   Init111(run111,seconds,micros);
   reason=Now111();
   if(reason!=0) { Status111(reason);return; }
   ResetLastError();bool root_file=FileIsExist("ForexDemoLab111",0);int root_error=GetLastError();
   if(root_file || (root_error!=0 && root_error!=5018 && root_error!=5019)) { Status111(14);return; }
   if(root_error!=5018) {
      ResetLastError();
      if(!FolderCreate("ForexDemoLab111",0) || GetLastError()!=0) { Status111(14);return; }
   }
   string folder=StringFormat("ForexDemoLab111\\Run111-%I64d-%I64u-%I64u",seconds,GetTickCount64(),micros);
   if(!FreshFolder111(folder)) { Status111(14);return; }
   int handle=Open111(folder,login,server);
   if(handle==INVALID_HANDLE) { End111(run111);return; }
   while(true) {
      if(IsStopped()) { Stop111(handle,18);return; }
      reason=Now111();
      if(reason!=0) { Stop111(handle,reason);return; }
      if(run111.attempts==7200 || run111.segment_attempts==120) {
         reason=ReadGuard111(true,login,server);
         if(reason==0) reason=Now111();
         if(reason!=0) { Stop111(handle,reason);return; }
         ulong final_us=GetMicrosecondCount();long final_s=(long)TimeGMT();
         reason=Clock111(run111,final_s,final_us,TimeToString((datetime)final_s,TIME_DATE));
         if(reason!=0) { Stop111(handle,reason);return; }
         bool complete=run111.attempts==7200;
         string footer=StringFormat("%s\t%d\t%d\t%I64d\t%I64u",complete?"E":"R",
            run111.attempts,run111.observed,final_s,final_us);
         if(!Append111(handle,footer)) { FileClose(handle);End111(run111);Status111(14);return; }
         FileClose(handle);
         run111.last_s=final_s;run111.last_guard_us=final_us;
         if(complete) { End111(run111);Status111(0);return; }
         handle=Open111(folder,login,server);
         if(handle==INVALID_HANDLE) { End111(run111);return; }
      }
      while(true) {
         if(IsStopped()) { Stop111(handle,18);return; }
         reason=Now111();
         if(reason!=0) { Stop111(handle,reason);return; }
         bool ready=false;int pause_ms=0;
         reason=Wait111(run111,GetMicrosecondCount(),ready,pause_ms);
         if(reason!=0) { Stop111(handle,reason);return; }
         if(ready) break;
         if(pause_ms>0) Sleep(pause_ms);
      }
      reason=ReadGuard111(true,login,server);
      if(reason!=0) { Stop111(handle,reason);return; }
      reason=Attempt111(run111);
      if(reason!=0) { Stop111(handle,reason);return; }
      if(!Append111(handle,StringFormat("A\t%d",run111.attempts))) { FileClose(handle);End111(run111);Status111(14);return; }
      reason=ReadGuard111(true,login,server);
      if(reason!=0) { Stop111(handle,reason);return; }
      long bs=(long)TimeGMT();ulong bu=GetMicrosecondCount();
      reason=Clock111(run111,bs,bu,TimeToString((datetime)bs,TIME_DATE));
      if(reason!=0) { Stop111(handle,reason);return; }
      MqlTick tick;ResetLastError();bool ok=SymbolInfoTick("EURUSD",tick);int tick_error=GetLastError();
      ulong au=GetMicrosecondCount();long ats=(long)TimeGMT();
      reason=ReadGuard111(true,login,server);
      ulong gu=GetMicrosecondCount();long gs=(long)TimeGMT();
      if(reason!=0) { Stop111(handle,reason);return; } // Never serialize this discarded tick.
      reason=Receipt111(run111,bs,ats,gs,bu,au,gu,TimeToString((datetime)gs,TIME_DATE));
      if(reason!=0) { Stop111(handle,reason);return; }
      int quote_reason=(!ok || tick_error!=0)?15:QuoteReason107((long)tick.time,tick.time_msc,
         tick.bid,tick.ask,tick.last,tick.volume_real,MathIsValidNumber(tick.bid) &&
         MathIsValidNumber(tick.ask) && MathIsValidNumber(tick.last) && MathIsValidNumber(tick.volume_real));
      string boundary=StringFormat("%d\t%I64d\t%I64d\t%I64d\t%I64u\t%I64u\t%I64u",
         run111.attempts,bs,ats,gs,bu,au,gu);
      string payload=quote_reason==0?
         "Q\t"+boundary+StringFormat("\t%I64d\t%I64d\t%s\t%s\t%s\t%I64u\t%u\t%s",
         (long)tick.time,tick.time_msc,NativeHex111(tick.bid),NativeHex111(tick.ask),
         NativeHex111(tick.last),tick.volume,tick.flags,NativeHex111(tick.volume_real)):
         "N\t"+boundary+StringFormat("\t%d",quote_reason);
      if(!Append111(handle,payload)) { FileClose(handle);End111(run111);Status111(14);return; }
      reason=Outcome111(run111,quote_reason);
      if(reason!=0) { Stop111(handle,reason);return; }
      if(quote_reason!=0) { Stop111(handle,quote_reason);return; }
   }
}
