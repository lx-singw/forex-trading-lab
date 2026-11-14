#property strict
#property version "1.000"
#property script_show_inputs
#property description "Synthetic sharing reader. Disabled by default; no quotes, grants or orders."
#include "ClockGuard042.mqh"
#define FXDL060_PURE_TEST
#include "CaptureReadiness060.mqh"
#include "SharingHold064.mqh"
input bool ReadSyntheticEvidence=false;
const string PHASE064="64000000000000000000000000000001";

struct Status064
{
   int reason,opens,reads,closes,count,open_cat,read_cat,close_cat,iterations;
   long size_before,size_after,pos_before,pos_after,hold_start,hold_end,hold_us;
   bool pattern;
};
struct Private064
{
   bool identified;
   long login,build;
   string server,path,data;
   ulong first_boot,first_us,last_boot,last_us;
   datetime first_utc,last_utc;
};
void Init064(Status064 &r)
{
   r.reason=17;r.opens=0;r.reads=0;r.closes=0;r.count=0;r.iterations=0;r.pattern=false;
   r.open_cat=-1;r.read_cat=-1;r.close_cat=-1;
   r.size_before=-1;r.size_after=-1;r.pos_before=-1;r.pos_after=-1;
   r.hold_start=-1;r.hold_end=-1;r.hold_us=-1;
}
void Report064(const Status064 &r)
{
   PrintFormat("FXDL_SHARE064 {\"version\":\"sharing_fixture_064_v1\",\"phase\":\"%s\",\"reason_code\":%d,\"opens\":%d,\"reads\":%d,\"closes\":%d,\"read_bytes\":%d,\"size_before\":%I64d,\"size_after\":%I64d,\"position_before\":%I64d,\"position_after\":%I64d,\"pattern_ok\":%s,\"open_category\":%d,\"read_category\":%d,\"close_category\":%d,\"hold_start_boot_ms\":%I64d,\"hold_end_boot_ms\":%I64d,\"hold_elapsed_us\":%I64d,\"hold_iterations\":%d,\"quote_reads\":0,\"history_reads\":0,\"orders\":0,\"receipt_permissions\":0}",
      PHASE064,r.reason,r.opens,r.reads,r.closes,r.count,r.size_before,r.size_after,
      r.pos_before,r.pos_after,r.pattern?"true":"false",r.open_cat,r.read_cat,r.close_cat,
      r.hold_start,r.hold_end,r.hold_us,r.iterations);
}
void Account064(ClockAccount042 &s)
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
int Guard064(Private064 &p)
{
   if(IsStopped())return 18;
   ClockAccount042 s;Account064(s);
   int reason=AccountReason042(s,p.identified,p.login,p.server);if(reason!=0)return reason;
   bool ok=true;
   ResetLastError();bool visible=(bool)SymbolInfoInteger("EURUSD",SYMBOL_VISIBLE);ok=ok && GetLastError()==0;
   ResetLastError();string base=SymbolInfoString("EURUSD",SYMBOL_CURRENCY_BASE);ok=ok && GetLastError()==0;
   ResetLastError();string profit=SymbolInfoString("EURUSD",SYMBOL_CURRENCY_PROFIT);ok=ok && GetLastError()==0;
   reason=SymbolReason042(ok,visible,base,profit,_Symbol);if(reason!=0)return reason;
   ResetLastError();long build=TerminalInfoInteger(TERMINAL_BUILD);ok=GetLastError()==0 && build>0;
   ResetLastError();string path=TerminalInfoString(TERMINAL_PATH);ok=ok && GetLastError()==0 && StringLen(path)>0;
   ResetLastError();string data=TerminalInfoString(TERMINAL_DATA_PATH);ok=ok && GetLastError()==0 && StringLen(data)>0;
   if(!ok)return 1;
   if(p.identified && (build!=p.build || path!=p.path || data!=p.data))return 26;
   ResetLastError();datetime utc=TimeGMT();if(GetLastError()!=0 || utc<=0)return 1;
   if(TimeToString(utc,TIME_DATE)!="2026.10.07")return 10;
   ulong boot=GetTickCount64(),us=GetMicrosecondCount();
   if(boot>9007199254740991 || boot<p.last_boot || us<p.last_us || utc<p.last_utc)return 19;
   if(boot-p.first_boot>=900000 || us-p.first_us>=900000000)return 21;
   long boot_delta=(long)(boot-p.first_boot),us_delta=(long)((us-p.first_us)/1000);
   long wall_delta=(long)(utc-p.first_utc)*1000;
   if(boot_delta-us_delta>1000 || us_delta-boot_delta>1000 ||
      wall_delta-boot_delta>2000 || boot_delta-wall_delta>2000)return 19;
   p.identified=true;p.login=s.login;p.server=s.server;p.build=build;p.path=path;p.data=data;
   p.last_boot=boot;p.last_us=us;p.last_utc=utc;return 0;
}
int Property064(const int h,const bool position,Private064 &p,long &value)
{
   int reason=Guard064(p);if(reason!=0)return reason;
   ResetLastError();ulong observed=position?FileTell(h):FileSize(h);int error=GetLastError();
   value=observed>85?85:(long)observed;
   reason=Guard064(p);if(reason!=0)return reason;
   return error==0?0:23;
}
void OnStart()
{
   Status064 r;Init064(r);
   // Default-off returns before account, clock, file or hold operations.
   if(!ReadSyntheticEvidence){Report064(r);return;}
   Private064 p;p.identified=false;p.login=0;p.server="";p.build=0;p.path="";p.data="";
   p.first_boot=GetTickCount64();p.last_boot=p.first_boot;
   p.first_us=GetMicrosecondCount();p.last_us=p.first_us;
   p.first_utc=TimeGMT();p.last_utc=p.first_utc;
   r.reason=Guard064(p);if(r.reason!=0){Report064(r);return;}
   r.opens=1;ResetLastError();
   int h=FileOpen("ForexDemoSharing064-"+PHASE064+"\\synthetic.bin",FILE_READ|FILE_BIN|FILE_SHARE_READ);
   int open_error=GetLastError();r.open_cat=ReadErrorCategory060(open_error);
   if(h==INVALID_HANDLE){r.reason=22;Report064(r);return;}
   do
   {
      r.reason=Guard064(p);if(r.reason!=0)break;
      if(r.open_cat!=0){r.reason=22;break;}
      r.reason=Property064(h,false,p,r.size_before);if(r.reason!=0)break;
      r.reason=Property064(h,true,p,r.pos_before);if(r.reason!=0)break;
      if(r.size_before!=84 || r.pos_before!=0){r.reason=23;break;}
      r.reason=Guard064(p);if(r.reason!=0)break;
      uchar bytes[84];r.reads=1;ResetLastError();
      uint count=FileReadArray(h,bytes,0,84);int read_error=GetLastError();
      r.read_cat=ReadErrorCategory060(read_error);r.count=count>84?84:(int)count;
      r.reason=Guard064(p);if(r.reason!=0)break;
      if(count!=84 || r.read_cat!=0){r.reason=24;break;}
      r.pattern=true;for(int i=0;i<84;i++)if((int)bytes[i]!=SyntheticByte064(i))r.pattern=false;
      if(!r.pattern){r.reason=24;break;}
      r.reason=Property064(h,false,p,r.size_after);if(r.reason!=0)break;
      r.reason=Property064(h,true,p,r.pos_after);if(r.reason!=0)break;
      if(r.size_after!=84 || r.pos_after!=84){r.reason=23;break;}
      r.hold_start=(long)GetTickCount64();ulong hold_us=GetMicrosecondCount();
      for(int i=0;i<601;i++)
      {
         r.reason=Guard064(p);if(r.reason!=0)break;
         if(GetTickCount64()-(ulong)r.hold_start>=30000)break;
         r.iterations++;Sleep(50);
         r.reason=Guard064(p);if(r.reason!=0)break;
      }
      r.hold_end=(long)GetTickCount64();ulong end_us=GetMicrosecondCount();
      r.hold_us=end_us<hold_us || end_us-hold_us>900000000?-1:(long)(end_us-hold_us);
      if(r.reason!=0)break;
      r.reason=HoldReason064(r.hold_start,r.hold_end,r.hold_us,r.iterations,IsStopped(),
                            TimeToString(TimeGMT(),TIME_DATE)=="2026.10.07");
      if(r.reason!=0)break;
      r.reason=Property064(h,false,p,r.size_after);if(r.reason!=0)break;
      r.reason=Property064(h,true,p,r.pos_after);if(r.reason!=0)break;
      if(r.size_after!=84 || r.pos_after!=84){r.reason=23;break;}
   }while(false);
   // Cleanup runs even when a guard/deadline failed. Void FileClose plus native
   // error0 is diagnostic only; companion post controls must corroborate release.
   int final_guard=Guard064(p);if(r.reason==0 && final_guard!=0)r.reason=final_guard;
   r.closes=1;ResetLastError();FileClose(h);int close_error=GetLastError();
   r.close_cat=ReadErrorCategory060(close_error);
   if(r.reason==0 && r.close_cat!=0)r.reason=25;
   final_guard=Guard064(p);if(r.reason==0 && final_guard!=0)r.reason=final_guard;
   Report064(r);
}
