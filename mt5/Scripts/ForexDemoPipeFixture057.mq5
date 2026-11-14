#property strict
#property version "1.001"
#property script_show_inputs
#property description "No-market pipe fixture. Disabled by default. Cannot read quotes or place orders."
#include "CaptureWireDiagnostics053.mqh"
#include "ClockGuard042.mqh"
#include "CaptureReadDiagnostics056.mqh"
input bool ExerciseTransport=false;
const string PHASE057="57000000000000000000000000000001";
const string POLICY057="5757575757575757575757575757575757575757575757575757575757575757";
void Stop057(const int reason,const int requests,const bool valid,const int count=0,const int decode=-1,const int read_error=-1,const long read_us=-1)
{
   PrintFormat("FXDL_PIPE057 {\"version\":\"pipe_fixture_057_v1\",\"reason_code\":%d,\"requests\":%d,\"receipt_valid\":%s,\"reply_bytes\":%d,\"decode_reason\":%d,\"read_error_category\":%d,\"read_elapsed_us\":%I64d,\"read_timing\":%d,\"quote_reads\":0,\"orders\":0}",reason,requests,valid?"true":"false",count,decode,read_error,read_us,read_error<0?-1:(read_us<0?1:0));
}
void Account057(ClockAccount042 &s)
{
   s.query_ok=true;
   ResetLastError();s.connected=(bool)TerminalInfoInteger(TERMINAL_CONNECTED);s.query_ok=s.query_ok && GetLastError()==0;
   ResetLastError();s.algo_allowed=(bool)TerminalInfoInteger(TERMINAL_TRADE_ALLOWED);s.query_ok=s.query_ok && GetLastError()==0;
   ResetLastError();s.tester=(bool)MQLInfoInteger(MQL_TESTER);s.query_ok=s.query_ok && GetLastError()==0;
   ResetLastError();s.mode=AccountInfoInteger(ACCOUNT_TRADE_MODE);s.query_ok=s.query_ok && GetLastError()==0;
   ResetLastError();s.currency=AccountInfoString(ACCOUNT_CURRENCY);s.query_ok=s.query_ok && GetLastError()==0;
   ResetLastError();s.login=AccountInfoInteger(ACCOUNT_LOGIN);s.query_ok=s.query_ok && GetLastError()==0;
   ResetLastError();s.server=AccountInfoString(ACCOUNT_SERVER);s.query_ok=s.query_ok && GetLastError()==0;
}
void OnStart()
{
   if(!ExerciseTransport){Stop057(17,0,false);return;}
   if(TimeToString(TimeGMT(),TIME_DATE)!="2026.10.07"){Stop057(10,0,false);return;}
   ClockAccount042 s;Account057(s);int reason=AccountReason042(s,false,0,"");
   if(reason!=0){Stop057(reason,0,false);return;}
   long login=s.login;string server=s.server;
   // The fixture does not select/change instruments or read any quote.
   bool symbol_ok=true;
   ResetLastError();bool visible=(bool)SymbolInfoInteger("EURUSD",SYMBOL_VISIBLE);symbol_ok=symbol_ok && GetLastError()==0;
   ResetLastError();string base=SymbolInfoString("EURUSD",SYMBOL_CURRENCY_BASE);symbol_ok=symbol_ok && GetLastError()==0;
   ResetLastError();string profit=SymbolInfoString("EURUSD",SYMBOL_CURRENCY_PROFIT);symbol_ok=symbol_ok && GetLastError()==0;
   reason=SymbolReason042(symbol_ok,visible,base,profit,_Symbol);
   if(reason!=0){Stop057(reason,0,false);return;}
   int h=FileOpen("\\\\.\\pipe\\ForexDemoFixture047-"+PHASE057,FILE_READ|FILE_WRITE|FILE_BIN);
   if(h==INVALID_HANDLE){Stop057(20,0,false);return;}
   uchar request[56];for(int i=0;i<8;i++)request[i]=(uchar)StringGetCharacter("FXDL047Q",i);
   for(int i=0;i<16;i++)request[8+i]=(uchar)(Hex047(StringGetCharacter(PHASE057,2*i))*16+Hex047(StringGetCharacter(PHASE057,2*i+1)));
   for(int i=0;i<32;i++)request[24+i]=(uchar)(Hex047(StringGetCharacter(POLICY057,2*i))*16+Hex047(StringGetCharacter(POLICY057,2*i+1)));
   Account057(s);reason=AccountReason042(s,true,login,server);
   if(reason!=0){FileClose(h);Stop057(reason,0,false);return;}
   if(FileWriteArray(h,request,0,56)!=56){FileClose(h);Stop057(21,1,false);return;}
   FileFlush(h);if(!FileSeek(h,0,SEEK_SET)){FileClose(h);Stop057(22,1,false);return;}
   uchar reply[85];ResetLastError();ulong read_start=GetMicrosecondCount();
   uint count=FileReadArray(h,reply,0,85);
   int read_error=GetLastError();ulong read_end=GetMicrosecondCount();
   int read_category=ReadErrorCategory056(read_error);
   long read_us=ReadDuration056(read_start,read_end);FileClose(h);
   Wire047 wire;wire.size=(int)count;for(int i=0;i<84;i++)wire.bytes[i]=i<(int)count?reply[i]:0;
   Account057(s);reason=AccountReason042(s,true,login,server);
   if(reason!=0){Stop057(reason,1,false,(int)count,-1,read_category,read_us);return;}
   // Conservative upper end of GMT's whole-second precision, not UTC certification.
   long utc=(long)TimeGMT()*1000+999,boot=(long)GetTickCount64();
   bool date_ok=TimeToString(TimeGMT(),TIME_DATE)=="2026.10.07";
   int decode=DecodeReason053(wire,PHASE057,POLICY057,utc,boot,date_ok);
   bool valid=Decode047(wire,PHASE057,POLICY057,utc,boot,date_ok);
   bool diagnostic_ok=read_category==0 && read_us>=0 && read_us<900000000;
   Stop057(valid?(diagnostic_ok?0:24):23,1,valid && diagnostic_ok,(int)count,decode,read_category,read_us);
}
