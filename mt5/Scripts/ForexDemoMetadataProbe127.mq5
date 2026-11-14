#property copyright "Forex Demo Lab"
#property version "1.000"
#property strict
#property script_show_inputs
#property description "Private current demo metadata/clock probe. No orders or history."
#include "PrivateGuard107.mqh"
#include "MetadataClock127.mqh"

input bool CollectEvidence = false;
union NativeDouble127 { double value; ulong bits; };
MetadataClock127 clock127;
long private_login127=0;
string private_server127="";
int file127=INVALID_HANDLE;
int guard_checks127=0;
int open_reason127=14;
ulong bytes127=0;
string chain127="0000000000000000000000000000000000000000000000000000000000000000";
long bs127=0,as127=0,gs127=0;
ulong bu127=0,au127=0,gu127=0;

string Hex127(const double value)
{
   NativeDouble127 u;u.value=value;return StringFormat("%.16I64X",u.bits);
}
string Digest127(const string text)
{
   uchar src[],key[],dst[];
   if(StringToCharArray(text,src,0,StringLen(text),CP_UTF8)!=StringLen(text)) return "";
   ResetLastError();
   if(CryptEncode(CRYPT_HASH_SHA256,src,key,dst)!=32 || GetLastError()!=0) return "";
   string result="";
   for(int i=0;i<32;i++) result+=StringFormat("%.2X",dst[i]);
   return result;
}
int Guard127(const bool identified)
{
   PrivateAccount107 s;s.query_ok=true;guard_checks127++;
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
   return GuardReason107(s,identified,private_login127,private_server127);
}
int Now127()
{
   long seconds=(long)TimeGMT();ulong micros=GetMicrosecondCount();
   return CheckClock127(clock127,seconds,micros,TimeToString((datetime)seconds,TIME_DATE));
}
void Status127(const int reason)
{
   PrintFormat("FXDL127 {\"reason_code\":%d,\"queries\":%d,\"guard_checks\":%d,\"bytes\":%I64u}",
               reason,clock127.queries,guard_checks127,bytes127);
}
bool Append127(const string payload)
{
   string next=Digest127(chain127+"\t"+payload+"\n");
   if(StringLen(next)!=64) return false;
   string line=payload+"\t"+next+"\r\n";
   if(StringLen(line)>2048 || bytes127+(ulong)StringLen(line)>65536) return false;
   ResetLastError();ulong size=FileSize(file127);int error=GetLastError();
   if(error!=0 || size!=bytes127) return false;
   ResetLastError();uint written=FileWriteString(file127,line);
   if(written!=(uint)StringLen(line) || GetLastError()!=0) return false;
   ResetLastError();FileFlush(file127);
   if(GetLastError()!=0) return false;
   bytes127+=written;chain127=next;return true;
}
bool Stop127(const int reason)
{
   bool saved=false;
   if(file127!=INVALID_HANDLE)
   {
      saved=Append127(StringFormat("S\t%d\t%d",reason,clock127.queries));
      FileClose(file127);file127=INVALID_HANDLE;
   }
   Status127(saved?reason:14);return false;
}
bool Begin127(const string tag,const string key)
{
   int reason=IsStopped()?18:Guard127(true);
   if(reason==0) reason=Now127();
   if(reason==0) reason=NextQuery127(clock127);
   if(reason!=0) return Stop127(reason);
   if(!Append127(StringFormat("A\t%d\t%s\t%s",clock127.queries,tag,key))) return Stop127(14);
   reason=Guard127(true);
   bs127=(long)TimeGMT();bu127=GetMicrosecondCount();
   if(reason==0) reason=CheckClock127(clock127,bs127,bu127,TimeToString((datetime)bs127,TIME_DATE));
   if(reason!=0) return Stop127(reason);
   return true;
}
bool After127()
{
   au127=GetMicrosecondCount();as127=(long)TimeGMT();
   int reason=Guard127(true);
   gu127=GetMicrosecondCount();gs127=(long)TimeGMT();
   if(reason==0) reason=CheckClock127(clock127,as127,au127,TimeToString((datetime)as127,TIME_DATE));
   if(reason==0) reason=CheckClock127(clock127,gs127,gu127,TimeToString((datetime)gs127,TIME_DATE));
   if(reason!=0) return Stop127(reason); // Queried value is never serialized on a failed after-read guard.
   return true;
}
bool Record127(const string tag,const string key,const bool ok,const int error,const string value)
{
   string row=StringFormat("%s\t%d\t%s\t%I64d\t%I64d\t%I64d\t%I64u\t%I64u\t%I64u\t%d\t%d\t%s",
                          tag,clock127.queries,key,bs127,as127,gs127,bu127,au127,gu127,ok?1:0,error,value);
   if(!Append127(row)) return Stop127(14);
   return true;
}
bool Integer127(const string key,const ENUM_SYMBOL_INFO_INTEGER prop,const bool account=false)
{
   if(!Begin127("I",key)) return false;
   long value=0;ResetLastError();
   bool ok=true;
   if(account) value=AccountInfoInteger(ACCOUNT_LEVERAGE);
   else ok=SymbolInfoInteger("EURUSD",prop,value);
   int error=GetLastError();ok=ok && error==0;
   if(!After127()) return false;
   return Record127("I",key,ok,error,StringFormat("%I64d",ok?value:0));
}
bool Double127(const string key,const ENUM_SYMBOL_INFO_DOUBLE prop)
{
   if(!Begin127("D",key)) return false;
   double value=0;ResetLastError();bool ok=SymbolInfoDouble("EURUSD",prop,value);
   int error=GetLastError();ok=ok && error==0;
   if(!After127()) return false;
   if(ok && !MathIsValidNumber(value)) return Stop127(16);
   return Record127("D",key,ok,error,Hex127(ok?value:0));
}
bool Currency127()
{
   if(!Begin127("V","currency_margin")) return false;
   ResetLastError();string value=SymbolInfoString("EURUSD",SYMBOL_CURRENCY_MARGIN);int error=GetLastError();
   bool ok=error==0;
   if(!After127()) return false;
   if(ok)
   {
      if(StringLen(value)!=3) return Stop127(16);
      for(int i=0;i<3;i++) if(StringGetCharacter(value,i)<65 || StringGetCharacter(value,i)>90) return Stop127(16);
   }
   return Record127("V","currency_margin",ok,error,ok?value:"NA");
}
bool Tick127(const string key)
{
   if(!Begin127("T",key)) return false;
   MqlTick t;ResetLastError();bool ok=SymbolInfoTick("EURUSD",t);int error=GetLastError();
   if(!After127()) return false;
   if(!ok || error!=0) return Stop127(15);
   int reason=QuoteReason107((long)t.time,t.time_msc,t.bid,t.ask,t.last,t.volume_real,
                            MathIsValidNumber(t.bid) && MathIsValidNumber(t.ask) && MathIsValidNumber(t.last) && MathIsValidNumber(t.volume_real));
   if(reason!=0) return Stop127(reason);
   string value=StringFormat("%I64d\t%I64d\t%s\t%s\t%s\t%I64u\t%u\t%s",(long)t.time,t.time_msc,
                            Hex127(t.bid),Hex127(t.ask),Hex127(t.last),t.volume,t.flags,Hex127(t.volume_real));
   return Record127("T",key,true,0,value);
}
bool Clocks127(const string key)
{
   if(!Begin127("C",key)) return false;
   ResetLastError();long tc=(long)TimeCurrent(),ts=(long)TimeTradeServer(),tg=(long)TimeGMT(),tl=(long)TimeLocal();
   long go=(long)TimeGMTOffset(),ds=(long)TimeDaylightSavings();int error=GetLastError();
   if(!After127()) return false;
   if(error!=0) return Stop127(12);
   return Record127("C",key,true,0,StringFormat("%I64d\t%I64d\t%I64d\t%I64d\t%I64d\t%I64d",tc,ts,tg,tl,go,ds));
}
bool Sessions127()
{
   for(int day=0;day<7;day++)
      for(uint index=0;index<9;index++)
      {
         string key=StringFormat("%d:%u",day,index);
         if(!Begin127("W",key)) return false;
         datetime from=0,to=0;ResetLastError();bool ok=SymbolInfoSessionTrade("EURUSD",(ENUM_DAY_OF_WEEK)day,index,from,to);
         int error=GetLastError();ok=ok && error==0;
         if(!After127()) return false;
         if(!Record127("W",key,ok,error,StringFormat("%I64d\t%I64d",ok?(long)from:0,ok?(long)to:0))) return false;
         if(!ok) break; // API absence/failure is not declared a historical market closure.
      }
   return true;
}
bool Open127()
{
   ResetLastError();bool root_file=FileIsExist("ForexDemoLab127",0);int error=GetLastError();
   if(root_file || (error!=0 && error!=5018 && error!=5019)) return false;
   if(error!=5018)
   {
      ResetLastError();if(!FolderCreate("ForexDemoLab127",0) || GetLastError()!=0) return false;
   }
   string folder=StringFormat("ForexDemoLab127\\Run127-%I64d-%I64u-%I64u",clock127.origin_s,GetTickCount64(),clock127.origin_us);
   ResetLastError();bool exists=FileIsExist(folder,0);error=GetLastError();
   if(exists || (error!=0 && error!=5019)) return false;
   ResetLastError();if(!FolderCreate(folder,0) || GetLastError()!=0) return false;
   int reason=Guard127(true);if(reason==0) reason=Now127();
   if(reason!=0) {open_reason127=reason;return false;}
   string filename=folder+"\\Metadata127.txt";
   ResetLastError();exists=FileIsExist(filename,0);error=GetLastError();
   if(exists || (error!=0 && error!=5019)) return false;
   ResetLastError();file127=FileOpen(filename,FILE_READ|FILE_WRITE|FILE_BIN|FILE_ANSI,0,CP_UTF8);
   if(file127==INVALID_HANDLE || GetLastError()!=0) return false;
   ResetLastError();ulong size=FileSize(file127);error=GetLastError();
   if(size!=0 || error!=0) {FileClose(file127);file127=INVALID_HANDLE;return false;}
   return Append127(StringFormat("H\tFXDL127_V1\tmarket_declared\t2026.10.14\t%I64d\t%I64u",clock127.origin_s,clock127.origin_us));
}
void OnStart()
{
   InitMetadata127(clock127,0,0);
   if(!CollectEvidence) {Status127(1);return;}
   if(Digest127("abc")!="BA7816BF8F01CFEA414140DE5DAE2223B00361A396177A9CB410FF61F20015AD" || Hex127(1.0)!="3FF0000000000000") {Status127(17);return;}
   int reason=Guard127(false);
   if(reason!=0) {Status127(reason);return;}
   ResetLastError();private_login127=AccountInfoInteger(ACCOUNT_LOGIN);int error=GetLastError();
   ResetLastError();private_server127=AccountInfoString(ACCOUNT_SERVER);error|=GetLastError();
   reason=Guard127(true);
   if(error!=0 || reason!=0) {Status127(reason!=0?reason:2);return;}
   InitMetadata127(clock127,(long)TimeGMT(),GetMicrosecondCount());
   reason=Now127();if(reason!=0) {Status127(reason);return;}
   if(!Open127()) {if(file127!=INVALID_HANDLE) {FileClose(file127);file127=INVALID_HANDLE;}Status127(open_reason127);return;}
   if(!Clocks127("clock_before") || !Tick127("tick_before")) return;
   if(!Integer127("account_leverage",SYMBOL_DIGITS,true)) return;
   ENUM_SYMBOL_INFO_INTEGER ip[]={SYMBOL_DIGITS,SYMBOL_TRADE_CALC_MODE,SYMBOL_SWAP_MODE,SYMBOL_SWAP_ROLLOVER3DAYS,
                                 SYMBOL_TRADE_STOPS_LEVEL,SYMBOL_TRADE_FREEZE_LEVEL,SYMBOL_TRADE_EXEMODE,SYMBOL_ORDER_MODE,
                                 SYMBOL_CUSTOM,SYMBOL_SUBSCRIPTION_DELAY,SYMBOL_CHART_MODE};
   string ik[]={"digits","trade_calc_mode","swap_mode","swap_rollover3days","stops_level","freeze_level","execution_mode","order_mode",
                "custom_symbol","subscription_delay","chart_mode"};
   for(int i=0;i<ArraySize(ip);i++) if(!Integer127(ik[i],ip[i])) return;
   ENUM_SYMBOL_INFO_DOUBLE dp[]={SYMBOL_POINT,SYMBOL_TRADE_TICK_SIZE,SYMBOL_TRADE_CONTRACT_SIZE,SYMBOL_TRADE_TICK_VALUE_PROFIT,
      SYMBOL_TRADE_TICK_VALUE_LOSS,SYMBOL_VOLUME_MIN,SYMBOL_VOLUME_MAX,SYMBOL_VOLUME_STEP,SYMBOL_VOLUME_LIMIT,
      SYMBOL_MARGIN_INITIAL,SYMBOL_MARGIN_MAINTENANCE,SYMBOL_SWAP_LONG,SYMBOL_SWAP_SHORT,SYMBOL_SWAP_SUNDAY,
      SYMBOL_SWAP_MONDAY,SYMBOL_SWAP_TUESDAY,SYMBOL_SWAP_WEDNESDAY,SYMBOL_SWAP_THURSDAY,SYMBOL_SWAP_FRIDAY,SYMBOL_SWAP_SATURDAY};
   string dk[]={"point","tick_size","contract_size","tick_value_profit","tick_value_loss","volume_min","volume_max",
      "volume_step","volume_limit","margin_initial","margin_maintenance","swap_long","swap_short","swap_sunday",
      "swap_monday","swap_tuesday","swap_wednesday","swap_thursday","swap_friday","swap_saturday"};
   for(int i=0;i<ArraySize(dp);i++) if(!Double127(dk[i],dp[i])) return;
   if(!Currency127() || !Sessions127() || !Tick127("tick_after") || !Clocks127("clock_after")) return;
   reason=Guard127(true);if(reason==0) reason=Now127();
   if(reason!=0) {Stop127(reason);return;}
   if(!Append127(StringFormat("E\t%d\t%I64d\t%I64u",clock127.queries,clock127.last_s,clock127.last_us))) {Stop127(14);return;}
   FileClose(file127);file127=INVALID_HANDLE;Status127(0);
}
