#property copyright "Forex Demo Lab"
#property version "1.000"
#property strict
#property script_show_inputs
#property description "Private demo four-hour quote/context recorder. No orders or history."
#include "PrivateGuard107.mqh"
#include "ContextRun136.mqh"
#include "CostBounds128.mqh"

input bool CollectEvidence = false;
union NativeDouble136 { double value; ulong bits; };
ContextRun136 clock136;
long private_login136=0;
string private_server136="";
int file136=INVALID_HANDLE;
int guard_checks136=0;
int open_reason136=14;
ulong bytes136=0;
string chain136="0000000000000000000000000000000000000000000000000000000000000000";
long bs136=0,as136=0,gs136=0;
ulong bu136=0,au136=0,gu136=0;

string Hex136(const double value)
{
   NativeDouble136 u;u.value=value;return StringFormat("%.16I64X",u.bits);
}
string Digest136(const string text)
{
   uchar src[],key[],dst[];
   if(StringToCharArray(text,src,0,StringLen(text),CP_UTF8)!=StringLen(text)) return "";
   ResetLastError();
   if(CryptEncode(CRYPT_HASH_SHA256,src,key,dst)!=32 || GetLastError()!=0) return "";
   string result="";
   for(int i=0;i<32;i++) result+=StringFormat("%.2X",dst[i]);
   return result;
}
int Guard136(const bool identified)
{
   PrivateAccount107 s;s.query_ok=true;guard_checks136++;
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
   return GuardReason107(s,identified,private_login136,private_server136);
}
int Now136()
{
   long seconds=(long)TimeGMT();ulong micros=GetMicrosecondCount();
   return CheckCollectorClock136(clock136,seconds,micros,TimeToString((datetime)seconds,TIME_DATE));
}
void Status136(const int reason)
{
   PrintFormat("FXDL136 {\"reason_code\":%d,\"queries\":%d,\"guard_checks\":%d,\"bytes\":%I64u}",
               reason,clock136.queries,guard_checks136,bytes136);
}
bool Append136(const string payload)
{
   string next=Digest136(chain136+"\t"+payload+"\n");
   if(StringLen(next)!=64) return false;
   string line=payload+"\t"+next+"\r\n";
   if(ReserveCollectorBytes136(clock136,(ulong)StringLen(line))!=0) return false;
   ResetLastError();ulong size=FileSize(file136);int error=GetLastError();
   if(error!=0 || size!=bytes136) return false;
   ResetLastError();uint written=FileWriteString(file136,line);
   if(written!=(uint)StringLen(line) || GetLastError()!=0) return false;
   ResetLastError();FileFlush(file136);
   if(GetLastError()!=0) return false;
   bytes136+=written;chain136=next;return true;
}
bool Stop136(const int reason)
{
   bool saved=false;
   if(file136!=INVALID_HANDLE)
   {
      saved=reason!=14 && Append136(StringFormat("S\t%d\t%d\t%d",reason,clock136.queries,clock136.polls));
      FileClose(file136);file136=INVALID_HANDLE;
   }
   EndCollector136(clock136);Status136(saved?reason:14);return false;
}
bool Begin136(const string tag,const string key)
{
   int reason=IsStopped()?18:Guard136(true);
   if(reason==0) reason=Now136();
   if(reason==0) reason=NextQuery136(clock136,tag,key);
   if(reason!=0) return Stop136(reason);
   if(!Append136(StringFormat("A\t%d\t%s\t%s",clock136.queries,tag,key))) return Stop136(14);
   reason=Guard136(true);
   bs136=(long)TimeGMT();bu136=GetMicrosecondCount();
   if(reason==0) reason=CheckCollectorClock136(clock136,bs136,bu136,TimeToString((datetime)bs136,TIME_DATE));
   if(reason==0 && tag=="C" && key=="before") reason=MarkPollStart136(clock136,bu136);
   if(reason!=0) return Stop136(reason);
   return true;
}
bool After136()
{
   au136=GetMicrosecondCount();as136=(long)TimeGMT();
   int reason=IsStopped()?18:Guard136(true);
   gu136=GetMicrosecondCount();gs136=(long)TimeGMT();
   if(reason==0) reason=CheckCollectorClock136(clock136,as136,au136,TimeToString((datetime)as136,TIME_DATE));
   if(reason==0) reason=CheckCollectorClock136(clock136,gs136,gu136,TimeToString((datetime)gs136,TIME_DATE));
   if(reason!=0) return Stop136(reason); // Queried value is never serialized on a failed after-read guard.
   return true;
}
bool Record136(const string tag,const string key,const bool ok,const int error,const string value,const bool complete=true)
{
   string row=StringFormat("%s\t%d\t%s\t%I64d\t%I64d\t%I64d\t%I64u\t%I64u\t%I64u\t%d\t%d\t%s",
                          tag,clock136.queries,key,bs136,as136,gs136,bu136,au136,gu136,ok?1:0,error,value);
   if(!Append136(row)) return Stop136(14);
   if(complete && CompleteQuery136(clock136,ok)!=0) return Stop136(19);
   return true;
}
bool Clocks136(const string key)
{
   if(!Begin136("C",key)) return false;
   ResetLastError();long tc=(long)TimeCurrent(),ts=(long)TimeTradeServer(),tg=(long)TimeGMT(),tl=(long)TimeLocal();
   long go=(long)TimeGMTOffset(),ds=(long)TimeDaylightSavings();int error=GetLastError();
   if(!After136()) return false;
   if(error!=0) return Stop136(12);
   return Record136("C",key,true,0,StringFormat("%I64d\t%I64d\t%I64d\t%I64d\t%I64d\t%I64d",tc,ts,tg,tl,go,ds));
}
bool Tick136()
{
   if(!Begin136("T","quote")) return false;
   MqlTick tick;
   ResetLastError();bool ok=SymbolInfoTick("EURUSD",tick);int error=GetLastError();
   if(!After136()) return false;
   if(!ok || error!=0) return Stop136(15);
   bool finite=MathIsValidNumber(tick.bid) && MathIsValidNumber(tick.ask) &&
               MathIsValidNumber(tick.last) && MathIsValidNumber(tick.volume_real);
   int reason=QuoteReason107((long)tick.time,tick.time_msc,tick.bid,tick.ask,tick.last,tick.volume_real,finite);
   if(reason!=0) return Stop136(reason);
   return Record136("T","quote",true,0,StringFormat("%I64d\t%I64d\t%s\t%s\t%s\t%I64u\t%u\t%s",
      (long)tick.time,tick.time_msc,Hex136(tick.bid),Hex136(tick.ask),Hex136(tick.last),
      tick.volume,tick.flags,Hex136(tick.volume_real)));
}
bool WaitPoll136()
{
   while(true)
   {
      int reason=IsStopped()?18:Guard136(true);
      if(reason==0) reason=Now136();
      if(reason==0) reason=WaitState136(clock136);
      if(reason!=0) return Stop136(reason);
      if(PollReady136(clock136,GetMicrosecondCount())) return true;
      Sleep(50); // No catch-up; deadline and guards are checked after returning.
   }
}
bool Integer136(const string key,const ENUM_SYMBOL_INFO_INTEGER prop,const bool account=false)
{
   if(!Begin136("I",key)) return false;
   long value=0;ResetLastError();
   bool ok=true;
   if(account) value=AccountInfoInteger(ACCOUNT_LEVERAGE);
   else ok=SymbolInfoInteger("EURUSD",prop,value);
   int error=GetLastError();ok=ok && error==0;
   if(!After136()) return false;
   return Record136("I",key,ok,error,StringFormat("%I64d",ok?value:0));
}
bool Double136(const string key,const ENUM_SYMBOL_INFO_DOUBLE prop)
{
   if(!Begin136("D",key)) return false;
   double value=0;ResetLastError();bool ok=SymbolInfoDouble("EURUSD",prop,value);
   int error=GetLastError();ok=ok && error==0;
   if(!After136()) return false;
   if(ok && !MathIsValidNumber(value)) return Stop136(16);
   return Record136("D",key,ok,error,Hex136(ok?value:0));
}
bool Currency136()
{
   if(!Begin136("V","currency_margin")) return false;
   ResetLastError();string value=SymbolInfoString("EURUSD",SYMBOL_CURRENCY_MARGIN);int error=GetLastError();
   bool ok=error==0;
   if(!After136()) return false;
   if(ok)
   {
      if(StringLen(value)!=3) return Stop136(16);
      for(int i=0;i<3;i++) if(StringGetCharacter(value,i)<65 || StringGetCharacter(value,i)>90) return Stop136(16);
   }
   return Record136("V","currency_margin",ok,error,ok?value:"NA");
}
bool Sessions136()
{
   for(int day=0;day<7;day++)
      for(uint index=0;index<9;index++)
      {
         string key=StringFormat("%d:%u",day,index);
         if(!Begin136("W",key)) return false;
         datetime from=0,to=0;ResetLastError();bool ok=SymbolInfoSessionTrade("EURUSD",(ENUM_DAY_OF_WEEK)day,index,from,to);
         int error=GetLastError();ok=ok && error==0;
         if(!After136()) return false;
         if(!Record136("W",key,ok,error,StringFormat("%I64d\t%I64d",ok?(long)from:0,ok?(long)to:0))) return false;
         if(!ok) break; // API absence/failure is not declared a historical market closure.
      }
   return true;
}
bool CurrencyToken136(const string value)
{
   if(value=="") return true;
   if(StringLen(value)!=3) return false;
   for(int i=0;i<3;i++) if(StringGetCharacter(value,i)<65 || StringGetCharacter(value,i)>90) return false;
   return true;
}
string CurrencyText136(const string value) {return value==""?"EMPTY":value;}
bool SerializeGuard136()
{
   int reason=IsStopped()?18:Guard136(true);
   if(reason==0) reason=Now136();
   if(reason!=0) return Stop136(reason);
   return true;
}
bool Margin136(const string key,const ENUM_ORDER_TYPE side)
{
   if(!Begin136("M",key)) return false;
   double initial=0,maintenance=0;
   ResetLastError();bool ok=SymbolInfoMarginRate("EURUSD",side,initial,maintenance);
   int error=GetLastError();ok=ok && error==0;
   if(!After136()) return false;
   if(ok && (!MathIsValidNumber(initial) || !MathIsValidNumber(maintenance) || initial<0 || maintenance<0)) return Stop136(16);
   return Record136("M",key,ok,error,Hex136(ok?initial:0)+"\t"+Hex136(ok?maintenance:0));
}
bool Commissions136()
{
   if(!Begin136("K","commissions")) return false;
   MqlCommission rules[];
   ResetLastError();int count=SymbolInfoCommissions("EURUSD",rules);int error=GetLastError();
   if(!After136()) return false;
   if(count < -1) return Stop136(16);
   bool ok=count>=0 && error==0;
   if(ok)
   {
      int reason=CostRuleCountReason128(count,ArraySize(rules));
      if(reason!=0) return Stop136(reason);
      int total_tiers=0;
      for(int i=0;i<count;i++)
      {
         int tiers=ArraySize(rules[i].tiers);
         reason=CostTierCountReason128(tiers,total_tiers);
         if(reason!=0) return Stop136(reason);
         total_tiers+=tiers;
         if(!CurrencyToken136(rules[i].currency)) return Stop136(16);
         for(int j=0;j<tiers;j++)
         {
            if(!CurrencyToken136(rules[i].tiers[j].currency) ||
               !MathIsValidNumber(rules[i].tiers[j].value) ||
               !MathIsValidNumber(rules[i].tiers[j].min_value) ||
               !MathIsValidNumber(rules[i].tiers[j].max_value) ||
               !MathIsValidNumber(rules[i].tiers[j].range_from) ||
               !MathIsValidNumber(rules[i].tiers[j].range_to)) return Stop136(16);
         }
      }
   }
   if(!SerializeGuard136()) return false;
   if(!Record136("K","commissions",ok,error,StringFormat("%d",count),false)) return false;
   if(!ok) {if(CompleteQuery136(clock136,false)!=0) return Stop136(19);return true;} // Failed return/error is preserved; no rule payload is trusted.
   for(int i=0;i<count;i++)
   {
      if(!SerializeGuard136()) return false;
      string rule=StringFormat("R\t%d\t%d\t%s\t%d\t%d\t%d\t%d\t%d\t%d",
         clock136.queries,i,CurrencyText136(rules[i].currency),(int)rules[i].mode_range,
         (int)rules[i].mode_charge,(int)rules[i].mode_entry,(int)rules[i].mode_direction,
         (int)rules[i].mode_profit,ArraySize(rules[i].tiers));
      if(!Append136(rule)) return Stop136(14);
      for(int j=0;j<ArraySize(rules[i].tiers);j++)
      {
         if(!SerializeGuard136()) return false;
         string tier=StringFormat("L\t%d\t%d\t%d\t%d\t%d\t%s\t%s\t%s\t%s\t%s\t%s",
            clock136.queries,i,j,(int)rules[i].tiers[j].mode,(int)rules[i].tiers[j].volume_type,
            Hex136(rules[i].tiers[j].value),Hex136(rules[i].tiers[j].min_value),
            Hex136(rules[i].tiers[j].max_value),Hex136(rules[i].tiers[j].range_from),
            Hex136(rules[i].tiers[j].range_to),CurrencyText136(rules[i].tiers[j].currency));
         if(!Append136(tier)) return Stop136(14);
      }
   }
   if(CompleteQuery136(clock136,true)!=0) return Stop136(19);
   return true;
}
bool Snapshot136()
{
   if(BeginContext136(clock136)!=0) return Stop136(19);
   if(!Append136(StringFormat("B\t%d\t%d",clock136.contexts,clock136.polls))) return Stop136(14);
   if(!Clocks136("context_before")) return false;
   if(!Integer136("account_leverage",SYMBOL_DIGITS,true)) return false;
   ENUM_SYMBOL_INFO_INTEGER ip[]={SYMBOL_DIGITS,SYMBOL_TRADE_CALC_MODE,SYMBOL_SWAP_MODE,SYMBOL_SWAP_ROLLOVER3DAYS,
                                 SYMBOL_TRADE_STOPS_LEVEL,SYMBOL_TRADE_FREEZE_LEVEL,SYMBOL_TRADE_EXEMODE,SYMBOL_ORDER_MODE,
                                 SYMBOL_CUSTOM,SYMBOL_SUBSCRIPTION_DELAY,SYMBOL_CHART_MODE};
   string ik[]={"digits","trade_calc_mode","swap_mode","swap_rollover3days","stops_level","freeze_level","execution_mode","order_mode",
                "custom_symbol","subscription_delay","chart_mode"};
   for(int i=0;i<ArraySize(ip);i++) if(!Integer136(ik[i],ip[i])) return false;
   ENUM_SYMBOL_INFO_DOUBLE dp[]={SYMBOL_POINT,SYMBOL_TRADE_TICK_SIZE,SYMBOL_TRADE_CONTRACT_SIZE,SYMBOL_TRADE_TICK_VALUE_PROFIT,
      SYMBOL_TRADE_TICK_VALUE_LOSS,SYMBOL_VOLUME_MIN,SYMBOL_VOLUME_MAX,SYMBOL_VOLUME_STEP,SYMBOL_VOLUME_LIMIT,
      SYMBOL_MARGIN_INITIAL,SYMBOL_MARGIN_MAINTENANCE,SYMBOL_SWAP_LONG,SYMBOL_SWAP_SHORT,SYMBOL_SWAP_SUNDAY,
      SYMBOL_SWAP_MONDAY,SYMBOL_SWAP_TUESDAY,SYMBOL_SWAP_WEDNESDAY,SYMBOL_SWAP_THURSDAY,SYMBOL_SWAP_FRIDAY,SYMBOL_SWAP_SATURDAY};
   string dk[]={"point","tick_size","contract_size","tick_value_profit","tick_value_loss","volume_min","volume_max",
      "volume_step","volume_limit","margin_initial","margin_maintenance","swap_long","swap_short","swap_sunday",
      "swap_monday","swap_tuesday","swap_wednesday","swap_thursday","swap_friday","swap_saturday"};
   for(int i=0;i<ArraySize(dp);i++) if(!Double136(dk[i],dp[i])) return false;
   if(!Currency136() || !Sessions136() || !Commissions136() ||
      !Margin136("buy",ORDER_TYPE_BUY) || !Margin136("sell",ORDER_TYPE_SELL) || !Clocks136("context_after")) return false;
   int reason=IsStopped()?18:Guard136(true);
   if(reason==0) reason=Now136();
   if(reason!=0) return Stop136(reason);
   if(!Append136(StringFormat("Z\t%d\t%d",clock136.contexts,clock136.queries))) return Stop136(14);
   if(EndContext136(clock136)!=0) return Stop136(19);
   return true;
}
bool Open136()
{
   ResetLastError();bool root_file=FileIsExist("ForexDemoLab136",0);int error=GetLastError();
   if(root_file || (error!=0 && error!=5018 && error!=5019)) return false;
   if(error!=5018)
   {
      ResetLastError();if(!FolderCreate("ForexDemoLab136",0) || GetLastError()!=0) return false;
   }
   string folder=StringFormat("ForexDemoLab136\\Run136-%I64d-%I64u-%I64u",clock136.origin_s,GetTickCount64(),clock136.origin_us);
   ResetLastError();bool exists=FileIsExist(folder,0);error=GetLastError();
   if(exists || (error!=0 && error!=5019)) return false;
   ResetLastError();if(!FolderCreate(folder,0) || GetLastError()!=0) return false;
   int reason=Guard136(true);if(reason==0) reason=Now136();
   if(reason!=0) {open_reason136=reason;return false;}
   string filename=folder+"\\Context136.txt";
   ResetLastError();exists=FileIsExist(filename,0);error=GetLastError();
   if(exists || (error!=0 && error!=5019)) return false;
   ResetLastError();file136=FileOpen(filename,FILE_READ|FILE_WRITE|FILE_BIN|FILE_ANSI,0,CP_UTF8);
   if(file136==INVALID_HANDLE || GetLastError()!=0) return false;
   ResetLastError();ulong size=FileSize(file136);error=GetLastError();
   if(size!=0 || error!=0) {FileClose(file136);file136=INVALID_HANDLE;return false;}
   return Append136(StringFormat("H\tFXDL_CONTEXT136_V1\tmarket_declared\t%s\t%I64d\t%I64u",TimeToString((datetime)clock136.origin_s,TIME_DATE),clock136.origin_s,clock136.origin_us));
}
void OnStart()
{
   InitCollector136(clock136,0,0);
   if(!CollectEvidence) {Status136(1);return;}
   if(Digest136("abc")!="BA7816BF8F01CFEA414140DE5DAE2223B00361A396177A9CB410FF61F20015AD" || Hex136(1.0)!="3FF0000000000000") {Status136(17);return;}
   int reason=Guard136(false);
   if(reason!=0) {Status136(reason);return;}
   ResetLastError();private_login136=AccountInfoInteger(ACCOUNT_LOGIN);int error=GetLastError();
   ResetLastError();private_server136=AccountInfoString(ACCOUNT_SERVER);error|=GetLastError();
   reason=Guard136(true);
   if(error!=0 || reason!=0) {Status136(reason!=0?reason:2);return;}
   InitCollector136(clock136,(long)TimeGMT(),GetMicrosecondCount());
   reason=Now136();if(reason!=0) {Status136(reason);return;}
   if(!Open136()) {if(file136!=INVALID_HANDLE) {FileClose(file136);file136=INVALID_HANDLE;}Status136(open_reason136);return;}
   for(int poll=0;poll<14400;poll++)
   {
      if(ContextDue136(clock136) && !Snapshot136()) return;
      if(!WaitPoll136() || !Clocks136("before") || !Tick136() || !Clocks136("after")) return;
   }
   reason=Guard136(true);if(reason==0) reason=Now136();
   if(reason!=0) {Stop136(reason);return;}
   if(!Append136(StringFormat("E\t%d\t%d\t%I64d\t%I64u",clock136.queries,clock136.polls,clock136.last_s,clock136.last_us))) {Stop136(14);return;}
   EndCollector136(clock136);FileClose(file136);file136=INVALID_HANDLE;Status136(0);
}
