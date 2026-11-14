#property copyright "Forex Demo Lab"
#property version "1.000"
#property strict
#property script_show_inputs
#property description "Private demo snapshot diagnostics. No order capability."
#include "PrivateGuard107.mqh"

input bool RecordDiagnosticSnapshots = false;

union NativeDouble107 { double value; ulong bits; };
int guards107 = 0, attempts107 = 0, observed107 = 0;
string chain107 = "0000000000000000000000000000000000000000000000000000000000000000";

string NativeHex107(const double value)
{
   NativeDouble107 u; u.value=value;
   return StringFormat("%.16I64X",u.bits);
}

string Digest107(const string text)
{
   uchar src[],key[],dst[];
   if(StringToCharArray(text,src,0,StringLen(text),CP_UTF8) != StringLen(text)) return "";
   ResetLastError();
   if(CryptEncode(CRYPT_HASH_SHA256,src,key,dst) != 32 || GetLastError()!=0) return "";
   string result="";
   for(int i=0;i<32;i++) result+=StringFormat("%.2X",dst[i]);
   return result;
}

bool Append107(const int handle, const string payload)
{
   string next=Digest107(chain107+"\t"+payload+"\n");
   if(StringLen(next)!=64) return false;
   string line=payload+"\t"+next+"\r\n";
   ResetLastError(); ulong length=FileSize(handle); int size_error=GetLastError();
   if(size_error!=0 || StringLen(line)>2048 || length+StringLen(line)>262144) return false;
   ResetLastError();
   uint written=FileWriteString(handle,line);
   if(written!=(uint)StringLen(line) || GetLastError()!=0) return false;
   ResetLastError(); FileFlush(handle);
   if(GetLastError()!=0) return false;
   chain107=next;
   return true;
}

void Status107(const int reason, const bool file_created)
{
   PrintFormat("FXDL107 {\"reason_code\":%d,\"attempts\":%d,\"observations\":%d,\"guard_checks\":%d,\"file_created\":%s}",
      reason,attempts107,observed107,guards107,file_created?"true":"false");
}

int ReadGuard107(const bool identified, const long login, const string server)
{
   PrivateAccount107 s; s.query_ok=true; guards107++;
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

int Clock107(const long origin_s, const ulong origin_us)
{
   long seconds=(long)TimeGMT(); ulong micros=GetMicrosecondCount();
   return ClockReason107(origin_s,origin_us,seconds,micros,TimeToString((datetime)seconds,TIME_DATE));
}

void Stop107(const int handle, const int reason)
{
   // A failed or interrupted write leaves a visibly incomplete file; never resume it.
   bool saved=Append107(handle,StringFormat("S\t%d\t%d",reason,attempts107));
   FileClose(handle);
   Status107(saved?reason:14,true);
}

void OnStart()
{
   if(!RecordDiagnosticSnapshots) { Status107(1,false); return; }
   if(Digest107("abc")!="BA7816BF8F01CFEA414140DE5DAE2223B00361A396177A9CB410FF61F20015AD" ||
      NativeHex107(1.0)!="3FF0000000000000") { Status107(17,false); return; }
   long origin_s=(long)TimeGMT(); ulong origin_us=GetMicrosecondCount();
   int reason=Clock107(origin_s,origin_us);
   if(reason!=0) { Status107(reason,false); return; }
   reason=ReadGuard107(false,0,"");
   if(reason!=0) { Status107(reason,false); return; }
   // Private baseline is checked again immediately; it is never written or printed.
   ResetLastError(); long login=AccountInfoInteger(ACCOUNT_LOGIN); int identity_error=GetLastError();
   ResetLastError(); string server=AccountInfoString(ACCOUNT_SERVER); identity_error|=GetLastError();
   reason=ReadGuard107(true,login,server);
   if(identity_error!=0 || reason!=0) { Status107(reason!=0?reason:2,false); return; }
   string filename=StringFormat("ForexDemoLab107\\Snapshot107-%I64d-%I64u-%I64u.txt",origin_s,GetTickCount64(),origin_us);
   // READ|WRITE does not truncate existing content; no shared-access flags.
   ResetLastError(); int handle=FileOpen(filename,FILE_READ|FILE_WRITE|FILE_BIN|FILE_ANSI,0,CP_UTF8);
   if(handle==INVALID_HANDLE || GetLastError()!=0) {
      if(handle!=INVALID_HANDLE) FileClose(handle);
      Status107(14,false); return;
   }
   ResetLastError(); ulong existing_size=FileSize(handle); int size_error=GetLastError();
   if(existing_size!=0 || size_error!=0) { FileClose(handle); Status107(14,false); return; }
   if(!Append107(handle,StringFormat("H\tFXDL107_V1\tmarket_declared\t2026.10.12\t120\t60000000\t500000\t%I64d\t%I64u",origin_s,origin_us))) {
      FileClose(handle); Status107(14,true); return;
   }
   long last_s=origin_s; ulong last_us=origin_us, last_read_us=0;
   for(int i=1;i<=120;i++) {
      if(IsStopped()) { Stop107(handle,18); return; }
      reason=Clock107(origin_s,origin_us);
      if(reason!=0) { Stop107(handle,reason); return; }
      if(last_read_us!=0) {
         ulong current=GetMicrosecondCount();
         if(current<last_read_us) { Stop107(handle,12); return; }
         while(current-last_read_us<500000) {
            Sleep(20);
            if(IsStopped()) { Stop107(handle,18); return; }
            reason=Clock107(origin_s,origin_us);
            if(reason!=0) { Stop107(handle,reason); return; }
            current=GetMicrosecondCount();
            if(current<last_read_us) { Stop107(handle,12); return; }
         }
      }
      reason=ReadGuard107(true,login,server);
      if(reason!=0) { Stop107(handle,reason); return; }
      // Persist an attempt before its read; do not falsely stamp the later read here.
      attempts107=i;
      if(!Append107(handle,StringFormat("A\t%d",i))) { FileClose(handle); Status107(14,true); return; }
      reason=ReadGuard107(true,login,server);
      if(reason!=0) { Stop107(handle,reason); return; }
      long before_s=(long)TimeGMT(); ulong before_us=GetMicrosecondCount();
      reason=ClockReason107(origin_s,origin_us,before_s,before_us,TimeToString((datetime)before_s,TIME_DATE));
      if(reason!=0 || before_s<last_s || before_us<last_us) { Stop107(handle,reason!=0?reason:12); return; }
      MqlTick tick; ResetLastError(); bool ok=SymbolInfoTick("EURUSD",tick); int tick_error=GetLastError();
      ulong after_us=GetMicrosecondCount(); long after_s=(long)TimeGMT();
      reason=ReadGuard107(true,login,server);
      ulong guard_us=GetMicrosecondCount(); long guard_s=(long)TimeGMT();
      if(reason!=0) { Stop107(handle,reason); return; } // Discard tick on failed after-guard.
      reason=ClockReason107(origin_s,origin_us,guard_s,guard_us,TimeToString((datetime)guard_s,TIME_DATE));
      if(reason!=0 || after_us<before_us || guard_us<after_us || after_s<before_s || guard_s<after_s) {
         Stop107(handle,reason!=0?reason:12); return;
      }
      last_read_us=before_us; last_us=guard_us; last_s=guard_s;
      string boundary=StringFormat("%d\t%I64d\t%I64d\t%I64d\t%I64u\t%I64u\t%I64u",i,before_s,after_s,guard_s,before_us,after_us,guard_us);
      int quote_reason=(!ok || tick_error!=0)?15:QuoteReason107((long)tick.time,tick.time_msc,tick.bid,tick.ask,tick.last,tick.volume_real,
         MathIsValidNumber(tick.bid) && MathIsValidNumber(tick.ask) && MathIsValidNumber(tick.last) && MathIsValidNumber(tick.volume_real));
      if(quote_reason!=0) {
         if(!Append107(handle,"N\t"+boundary+StringFormat("\t%d",quote_reason))) { FileClose(handle); Status107(14,true); return; }
         Stop107(handle,quote_reason); return;
      }
      string payload="Q\t"+boundary+StringFormat("\t%I64d\t%I64d\t%s\t%s\t%s\t%I64u\t%u\t%s",(long)tick.time,tick.time_msc,
         NativeHex107(tick.bid),NativeHex107(tick.ask),NativeHex107(tick.last),tick.volume,tick.flags,NativeHex107(tick.volume_real));
      if(!Append107(handle,payload)) { FileClose(handle); Status107(14,true); return; }
      observed107++;
   }
   reason=ReadGuard107(true,login,server);
   if(reason!=0) { Stop107(handle,reason); return; }
   reason=Clock107(origin_s,origin_us);
   if(reason!=0) { Stop107(handle,reason); return; }
   ulong finished_us=GetMicrosecondCount(); long finished_s=(long)TimeGMT();
   reason=ClockReason107(origin_s,origin_us,finished_s,finished_us,TimeToString((datetime)finished_s,TIME_DATE));
   if(reason!=0 || finished_us<last_us || finished_s<last_s) { Stop107(handle,reason!=0?reason:12); return; }
   bool complete=Append107(handle,StringFormat("E\t%d\t%d\t%I64d\t%I64u\t%d",attempts107,observed107,finished_s,finished_us,guards107));
   FileClose(handle); Status107(complete?0:14,true);
}
