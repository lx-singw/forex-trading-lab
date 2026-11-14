#property strict
#property version "1.000"
#property script_show_inputs
#property description "No-market pipe fixture. Disabled by default. Cannot read quotes or place orders."
#include "CaptureWire047.mqh"
#include "ClockGuard042.mqh"
input bool ExerciseTransport=false;
const string PHASE049="49000000000000000000000000000001";
const string POLICY049="4949494949494949494949494949494949494949494949494949494949494949";
void Stop049(const int reason,const int requests,const bool valid)
{
   PrintFormat("FXDL_PIPE049 {\"version\":\"pipe_fixture_049_v1\",\"reason_code\":%d,\"requests\":%d,\"receipt_valid\":%s,\"quote_reads\":0,\"orders\":0}",reason,requests,valid?"true":"false");
}
void Account049(ClockAccount042 &s)
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
   if(!ExerciseTransport){Stop049(17,0,false);return;}
   if(TimeToString(TimeGMT(),TIME_DATE)!="2026.10.07"){Stop049(10,0,false);return;}
   ClockAccount042 s;Account049(s);int reason=AccountReason042(s,false,0,"");
   if(reason!=0){Stop049(reason,0,false);return;}
   long login=s.login;string server=s.server;
   // The fixture does not select/change instruments or read any quote.
   bool symbol_ok=true;
   ResetLastError();bool visible=(bool)SymbolInfoInteger("EURUSD",SYMBOL_VISIBLE);symbol_ok=symbol_ok && GetLastError()==0;
   ResetLastError();string base=SymbolInfoString("EURUSD",SYMBOL_CURRENCY_BASE);symbol_ok=symbol_ok && GetLastError()==0;
   ResetLastError();string profit=SymbolInfoString("EURUSD",SYMBOL_CURRENCY_PROFIT);symbol_ok=symbol_ok && GetLastError()==0;
   reason=SymbolReason042(symbol_ok,visible,base,profit,_Symbol);
   if(reason!=0){Stop049(reason,0,false);return;}
   int h=FileOpen("\\\\.\\pipe\\ForexDemoFixture047-"+PHASE049,FILE_READ|FILE_WRITE|FILE_BIN);
   if(h==INVALID_HANDLE){Stop049(20,0,false);return;}
   uchar request[56];for(int i=0;i<8;i++)request[i]=(uchar)StringGetCharacter("FXDL047Q",i);
   for(int i=0;i<16;i++)request[8+i]=(uchar)(Hex047(StringGetCharacter(PHASE049,2*i))*16+Hex047(StringGetCharacter(PHASE049,2*i+1)));
   for(int i=0;i<32;i++)request[24+i]=(uchar)(Hex047(StringGetCharacter(POLICY049,2*i))*16+Hex047(StringGetCharacter(POLICY049,2*i+1)));
   Account049(s);reason=AccountReason042(s,true,login,server);
   if(reason!=0){FileClose(h);Stop049(reason,0,false);return;}
   if(FileWriteArray(h,request,0,56)!=56){FileClose(h);Stop049(21,1,false);return;}
   FileFlush(h);if(!FileSeek(h,0,SEEK_SET)){FileClose(h);Stop049(22,1,false);return;}
   uchar reply[85];uint count=FileReadArray(h,reply,0,85);FileClose(h);
   Wire047 wire;wire.size=(int)count;for(int i=0;i<84;i++)wire.bytes[i]=i<(int)count?reply[i]:0;
   Account049(s);reason=AccountReason042(s,true,login,server);
   if(reason!=0){Stop049(reason,1,false);return;}
   // Conservative upper end of GMT's whole-second precision, not UTC certification.
   bool valid=Decode047(wire,PHASE049,POLICY049,(long)TimeGMT()*1000+999,(long)GetTickCount64(),TimeToString(TimeGMT(),TIME_DATE)=="2026.10.07");
   Stop049(valid?0:23,1,valid);
}
