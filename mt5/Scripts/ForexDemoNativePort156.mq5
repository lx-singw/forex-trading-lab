#property copyright "Forex Demo Lab"
#property version "1.000"
#property strict
#property script_show_inputs
#property description "Closed-entry read-only native port prototype. No orders or history."
#include "PrivateGuard107.mqh"
#include "CostBounds128.mqh"
#include "RecorderPort156.mqh"
#include "RunPermit156.mqh"

input bool CollectEvidence=false;
input string JobToken156=""; // A folder binding, never collection permission or peer authentication.
union NativeDouble156 { double value; ulong bits; };
PortState156 clock156;
LeaseState156 lease156;
long private_login156=0;
string private_server156="",folder156="";
int file156=INVALID_HANDLE,guard_checks156=0;
ulong bytes156=0;
string chain156="0000000000000000000000000000000000000000000000000000000000000000";
long bs156=0,as156=0,gs156=0;
ulong bu156=0,au156=0,gu156=0;

// Read/serialization functions derived from136 are inserted below this transport.
string Hex156(const double value)
{
   NativeDouble156 u;u.value=value;return StringFormat("%.16I64X",u.bits);
}
string Digest156(const string text)
{
   uchar src[],key[],dst[];
   if(StringToCharArray(text,src,0,StringLen(text),CP_UTF8)!=StringLen(text)) return "";
   ResetLastError();
   if(CryptEncode(CRYPT_HASH_SHA256,src,key,dst)!=32 || GetLastError()!=0) return "";
   string result="";
   for(int i=0;i<32;i++) result+=StringFormat("%.2X",dst[i]);
   return result;
}
bool Identifier156(const string value)
{
   if(StringLen(value)!=32) return false;
   for(int i=0;i<32;i++)
   {
      ushort c=StringGetCharacter(value,i);
      if(!((c>=48 && c<=57) || (c>=97 && c<=102))) return false;
   }
   return true;
}
bool Number156(const string text,ulong &value)
{
   int n=StringLen(text);value=0;
   if(n<1 || n>19 || (n>1 && StringGetCharacter(text,0)==48)) return false;
   for(int i=0;i<n;i++)
   {
      ushort c=StringGetCharacter(text,i);
      if(c<48 || c>57 || value>922337203685477580 || (value==922337203685477580 && c>55)) return false;
      value=value*10+(c-48);
   }
   return true;
}
int Guard156(const bool identified)
{
   PrivateAccount107 s;s.query_ok=true;guard_checks156++;
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
   return GuardReason107(s,identified,private_login156,private_server156);
}
int Now156() {return PortClock156(clock156,GetMicrosecondCount());}
void Status156(const int reason)
{
   PrintFormat("FXDL156 {\"reason_code\":%d,\"queries\":%I64u,\"requests\":%I64u,\"guard_checks\":%d,\"bytes\":%I64u}",
               reason,clock156.queries,clock156.requests,guard_checks156,bytes156);
}
bool Stop156(const int reason)
{
   clock156.ended=true;
   if(file156!=INVALID_HANDLE) {FileClose(file156);file156=INVALID_HANDLE;}
   // Incomplete files are retained; there is no recovery, append or admission path.
   Status156(reason);return false;
}
bool Append156(const string payload)
{
   string next=Digest156(chain156+"\t"+payload+"\n");
   if(StringLen(next)!=64 || file156==INVALID_HANDLE) return false;
   string line=payload+"\t"+next+"\n";
   if(ReservePort156(clock156,(ulong)StringLen(line))!=0 || Now156()!=0) return false;
   ResetLastError();ulong size=FileSize(file156);int error=GetLastError();
   if(error!=0 || size!=bytes156) return false;
   ResetLastError();uint written=FileWriteString(file156,line);
   if(written!=(uint)StringLen(line) || GetLastError()!=0) return false;
   ResetLastError();FileFlush(file156);
   if(GetLastError()!=0) return false; // Flush is not crash-durability proof.
   bytes156+=written;chain156=next;return true;
}
int NewFile156(const string name)
{
   if(FileIsExist(name,0)) return INVALID_HANDLE;
   ResetLastError();int handle=FileOpen(name,FILE_READ|FILE_WRITE|FILE_BIN|FILE_ANSI,0,CP_UTF8);
   if(handle==INVALID_HANDLE) return INVALID_HANDLE;
   int error=GetLastError();
   ResetLastError();ulong size=FileSize(handle);error|=GetLastError();
   if(error!=0 || size!=0) {FileClose(handle);return INVALID_HANDLE;}
   // MQL has no proven atomic CREATE_NEW here. Same-user races remain a runtime gate.
   return handle;
}
bool Lease156()
{
   int reason=IsStopped()?18:Guard156(true);
   if(reason==0) reason=Now156();
   if(reason==0) reason=NewRequest156(clock156);
   if(reason!=0) return Stop156(reason);
   ulong sent=GetMicrosecondCount();
   string challenge=StringSubstr(Digest156(JobToken156+StringFormat(":%I64u:%I64u",clock156.requests,sent)),0,32);
   StringToLower(challenge);
   if(!Identifier156(challenge)) return Stop156(109);
   string request=StringFormat("FXDL_REQUEST156_V1\t%s\t%I64u\t%s\n",JobToken156,clock156.requests,challenge);
   if(ReservePort156(clock156,(ulong)StringLen(request))!=0 || ReservePort156(clock156,512)!=0) return Stop156(107);
   string stem=StringFormat("%04d",(int)clock156.requests);
   int handle=NewFile156(folder156+"\\Request"+stem+".txt");
   if(handle==INVALID_HANDLE) return Stop156(109);
   ResetLastError();uint written=FileWriteString(handle,request);int error=GetLastError();
   FileFlush(handle);error|=GetLastError();FileClose(handle);
   if(written!=(uint)StringLen(request) || error!=0) return Stop156(109);
   string name=folder156+"\\Reply"+stem+".txt";
   while(!FileIsExist(name,0))
   {
      reason=IsStopped()?18:Guard156(true);
      if(reason==0) reason=Now156();
      ulong now=GetMicrosecondCount();
      if(reason!=0 || now<sent || now-sent>1000000) return Stop156(reason!=0?reason:105);
      Sleep(10);
   }
   ResetLastError();handle=FileOpen(name,FILE_READ|FILE_BIN|FILE_ANSI,0,CP_UTF8);
   if(handle==INVALID_HANDLE || GetLastError()!=0) return Stop156(109);
   ResetLastError();ulong size=FileSize(handle);error=GetLastError();
   if(error!=0 || size<1 || size>512) {FileClose(handle);return Stop156(109);}
   ResetLastError();string reply=FileReadString(handle,(int)size);error=GetLastError();FileClose(handle);
   if(error!=0 || StringLen(reply)!=(int)size || StringGetCharacter(reply,(int)size-1)!=10) return Stop156(109);
   for(int i=0;i<(int)size-1;i++)
   {
      ushort c=StringGetCharacter(reply,i);
      if(c!=9 && (c<32 || c>126)) return Stop156(109);
   }
   string parts[];
   if(StringSplit(StringSubstr(reply,0,(int)size-1),9,parts)!=8 || parts[0]!="FXDL_REPLY156_V1" ||
      parts[1]!=JobToken156 || parts[3]!=challenge) return Stop156(109);
   ulong ordinal,sequence,tick,owner,flags;
   if(!Number156(parts[2],ordinal) || ordinal!=clock156.requests || !Number156(parts[4],sequence) ||
      !Number156(parts[5],tick) || !Number156(parts[6],owner) || !Number156(parts[7],flags)) return Stop156(109);
   ulong received=GetMicrosecondCount();reason=PortClock156(clock156,received);
   if(reason==0) reason=AcceptLease156(lease156,sent,received,sequence,tick,owner,flags);
   if(reason==0) reason=Guard156(true);
   if(reason!=0) return Stop156(reason);
   if(!Append156(StringFormat("J\t%I64u\t%s\t%I64u\t%I64u\t%I64u\t%I64u\t%I64u\t%I64u",
      ordinal,challenge,sent,received,sequence,tick,owner,flags))) return Stop156(109);
   return true;
}
bool SerializeGuard156()
{
   int reason=IsStopped()?18:Guard156(true);
   if(reason==0) reason=Now156();
   if(reason==0) reason=LeaseFresh156(lease156,GetMicrosecondCount());
   if(reason!=0) return Stop156(reason);
   return true;
}
bool Begin156(const string tag,const string key)
{
   if(!Lease156()) return false;
   int reason=BeginQuery156(clock156);
   if(reason!=0) return Stop156(reason);
   if(!Append156(StringFormat("A\t%I64u\t%s\t%s",clock156.queries,tag,key))) return Stop156(109);
   if(!SerializeGuard156()) return false;
   bs156=(long)TimeGMT();bu156=GetMicrosecondCount();
   return SerializeGuard156(); // Intent IO cannot hide an expired lease.
}
bool After156()
{
   au156=GetMicrosecondCount();as156=(long)TimeGMT();
   if(!Lease156()) return false; // A failed after-read guard discards the local value.
   gu156=GetMicrosecondCount();gs156=(long)TimeGMT();return SerializeGuard156();
}
bool Record156(const string tag,const string key,const bool ok,const int error,const string value,const bool complete=true)
{
   if(!SerializeGuard156()) return false;
   string row=StringFormat("%s\t%I64u\t%s\t%I64d\t%I64d\t%I64d\t%I64u\t%I64u\t%I64u\t%d\t%d\t%s",
                          tag,clock156.queries,key,bs156,as156,gs156,bu156,au156,gu156,ok?1:0,error,value);
   if(!Append156(row)) return Stop156(109);
   if(complete && CompleteQuery156(clock156)!=0) return Stop156(106);
   return true;
}
bool Clocks156(const string key)
{
   if(!Begin156("C",key)) return false;
   ResetLastError();long tc=(long)TimeCurrent(),ts=(long)TimeTradeServer(),tg=(long)TimeGMT(),tl=(long)TimeLocal();
   long go=(long)TimeGMTOffset(),ds=(long)TimeDaylightSavings();int error=GetLastError();
   if(!After156()) return false;
   if(error!=0) return Stop156(12);
   return Record156("C",key,true,0,StringFormat("%I64d\t%I64d\t%I64d\t%I64d\t%I64d\t%I64d",tc,ts,tg,tl,go,ds));
}

bool Tick156()
{
   if(!Begin156("T","quote")) return false;
   MqlTick tick;
   ResetLastError();bool ok=SymbolInfoTick("EURUSD",tick);int error=GetLastError();
   if(!After156()) return false;
   if(!ok || error!=0) return Stop156(15);
   bool finite=MathIsValidNumber(tick.bid) && MathIsValidNumber(tick.ask) &&
               MathIsValidNumber(tick.last) && MathIsValidNumber(tick.volume_real);
   int reason=QuoteReason107((long)tick.time,tick.time_msc,tick.bid,tick.ask,tick.last,tick.volume_real,finite);
   if(reason!=0) return Stop156(reason);
   return Record156("T","quote",true,0,StringFormat("%I64d\t%I64d\t%s\t%s\t%s\t%I64u\t%u\t%s",
      (long)tick.time,tick.time_msc,Hex156(tick.bid),Hex156(tick.ask),Hex156(tick.last),
      tick.volume,tick.flags,Hex156(tick.volume_real)));
}

bool Integer156(const string key,const ENUM_SYMBOL_INFO_INTEGER prop,const bool account=false)
{
   if(!Begin156("I",key)) return false;
   long value=0;ResetLastError();
   bool ok=true;
   if(account) value=AccountInfoInteger(ACCOUNT_LEVERAGE);
   else ok=SymbolInfoInteger("EURUSD",prop,value);
   int error=GetLastError();ok=ok && error==0;
   if(!After156()) return false;
   return Record156("I",key,ok,error,StringFormat("%I64d",ok?value:0));
}

bool Double156(const string key,const ENUM_SYMBOL_INFO_DOUBLE prop)
{
   if(!Begin156("D",key)) return false;
   double value=0;ResetLastError();bool ok=SymbolInfoDouble("EURUSD",prop,value);
   int error=GetLastError();ok=ok && error==0;
   if(!After156()) return false;
   if(ok && !MathIsValidNumber(value)) return Stop156(16);
   return Record156("D",key,ok,error,Hex156(ok?value:0));
}

bool Currency156()
{
   if(!Begin156("V","currency_margin")) return false;
   ResetLastError();string value=SymbolInfoString("EURUSD",SYMBOL_CURRENCY_MARGIN);int error=GetLastError();
   bool ok=error==0;
   if(!After156()) return false;
   if(ok)
   {
      if(StringLen(value)!=3) return Stop156(16);
      for(int i=0;i<3;i++) if(StringGetCharacter(value,i)<65 || StringGetCharacter(value,i)>90) return Stop156(16);
   }
   return Record156("V","currency_margin",ok,error,ok?value:"NA");
}

bool Sessions156()
{
   for(int day=0;day<7;day++)
      for(uint index=0;index<9;index++)
      {
         string key=StringFormat("%d:%u",day,index);
         if(!Begin156("W",key)) return false;
         datetime from=0,to=0;ResetLastError();bool ok=SymbolInfoSessionTrade("EURUSD",(ENUM_DAY_OF_WEEK)day,index,from,to);
         int error=GetLastError();ok=ok && error==0;
         if(!After156()) return false;
         if(!Record156("W",key,ok,error,StringFormat("%I64d\t%I64d",ok?(long)from:0,ok?(long)to:0))) return false;
         if(!ok) break; // API absence/failure is not declared a historical market closure.
      }
   return true;
}

bool CurrencyToken156(const string value)
{
   if(value=="") return true;
   if(StringLen(value)!=3) return false;
   for(int i=0;i<3;i++) if(StringGetCharacter(value,i)<65 || StringGetCharacter(value,i)>90) return false;
   return true;
}

string CurrencyText156(const string value) {return value==""?"EMPTY":value;}

bool Margin156(const string key,const ENUM_ORDER_TYPE side)
{
   if(!Begin156("M",key)) return false;
   double initial=0,maintenance=0;
   ResetLastError();bool ok=SymbolInfoMarginRate("EURUSD",side,initial,maintenance);
   int error=GetLastError();ok=ok && error==0;
   if(!After156()) return false;
   if(ok && (!MathIsValidNumber(initial) || !MathIsValidNumber(maintenance) || initial<0 || maintenance<0)) return Stop156(16);
   return Record156("M",key,ok,error,Hex156(ok?initial:0)+"\t"+Hex156(ok?maintenance:0));
}

bool Commissions156()
{
   if(!Begin156("K","commissions")) return false;
   MqlCommission rules[];
   ResetLastError();int count=SymbolInfoCommissions("EURUSD",rules);int error=GetLastError();
   if(!After156()) return false;
   if(count < -1) return Stop156(16);
   bool ok=count>=0 && error==0;
   if(ok)
   {
      int reason=CostRuleCountReason128(count,ArraySize(rules));
      if(reason!=0) return Stop156(reason);
      int total_tiers=0;
      for(int i=0;i<count;i++)
      {
         int tiers=ArraySize(rules[i].tiers);
         reason=CostTierCountReason128(tiers,total_tiers);
         if(reason!=0) return Stop156(reason);
         total_tiers+=tiers;
         if(!CurrencyToken156(rules[i].currency)) return Stop156(16);
         for(int j=0;j<tiers;j++)
         {
            if(!CurrencyToken156(rules[i].tiers[j].currency) ||
               !MathIsValidNumber(rules[i].tiers[j].value) ||
               !MathIsValidNumber(rules[i].tiers[j].min_value) ||
               !MathIsValidNumber(rules[i].tiers[j].max_value) ||
               !MathIsValidNumber(rules[i].tiers[j].range_from) ||
               !MathIsValidNumber(rules[i].tiers[j].range_to)) return Stop156(16);
         }
      }
   }
   if(!SerializeGuard156()) return false;
   if(!Record156("K","commissions",ok,error,StringFormat("%d",count),false)) return false;
   if(!ok) {if(CompleteQuery156(clock156)!=0) return Stop156(19);return true;} // Failed return/error is preserved; no rule payload is trusted.
   for(int i=0;i<count;i++)
   {
      if(!SerializeGuard156()) return false;
      string rule=StringFormat("R\t%d\t%d\t%s\t%d\t%d\t%d\t%d\t%d\t%d",
         (int)clock156.queries,i,CurrencyText156(rules[i].currency),(int)rules[i].mode_range,
         (int)rules[i].mode_charge,(int)rules[i].mode_entry,(int)rules[i].mode_direction,
         (int)rules[i].mode_profit,ArraySize(rules[i].tiers));
      if(!Append156(rule)) return Stop156(14);
      for(int j=0;j<ArraySize(rules[i].tiers);j++)
      {
         if(!SerializeGuard156()) return false;
         string tier=StringFormat("L\t%d\t%d\t%d\t%d\t%d\t%s\t%s\t%s\t%s\t%s\t%s",
            (int)clock156.queries,i,j,(int)rules[i].tiers[j].mode,(int)rules[i].tiers[j].volume_type,
            Hex156(rules[i].tiers[j].value),Hex156(rules[i].tiers[j].min_value),
            Hex156(rules[i].tiers[j].max_value),Hex156(rules[i].tiers[j].range_from),
            Hex156(rules[i].tiers[j].range_to),CurrencyText156(rules[i].tiers[j].currency));
         if(!Append156(tier)) return Stop156(14);
      }
   }
   if(CompleteQuery156(clock156)!=0) return Stop156(19);
   return true;
}

bool Snapshot156()
{
   if(!Append156("B\t1")) return Stop156(14);
   if(!Clocks156("context_before")) return false;
   if(!Integer156("account_leverage",SYMBOL_DIGITS,true)) return false;
   ENUM_SYMBOL_INFO_INTEGER ip[]={SYMBOL_DIGITS,SYMBOL_TRADE_CALC_MODE,SYMBOL_SWAP_MODE,SYMBOL_SWAP_ROLLOVER3DAYS,
                                 SYMBOL_TRADE_STOPS_LEVEL,SYMBOL_TRADE_FREEZE_LEVEL,SYMBOL_TRADE_EXEMODE,SYMBOL_ORDER_MODE,
                                 SYMBOL_CUSTOM,SYMBOL_SUBSCRIPTION_DELAY,SYMBOL_CHART_MODE};
   string ik[]={"digits","trade_calc_mode","swap_mode","swap_rollover3days","stops_level","freeze_level","execution_mode","order_mode",
                "custom_symbol","subscription_delay","chart_mode"};
   for(int i=0;i<ArraySize(ip);i++) if(!Integer156(ik[i],ip[i])) return false;
   ENUM_SYMBOL_INFO_DOUBLE dp[]={SYMBOL_POINT,SYMBOL_TRADE_TICK_SIZE,SYMBOL_TRADE_CONTRACT_SIZE,SYMBOL_TRADE_TICK_VALUE_PROFIT,
      SYMBOL_TRADE_TICK_VALUE_LOSS,SYMBOL_VOLUME_MIN,SYMBOL_VOLUME_MAX,SYMBOL_VOLUME_STEP,SYMBOL_VOLUME_LIMIT,
      SYMBOL_MARGIN_INITIAL,SYMBOL_MARGIN_MAINTENANCE,SYMBOL_SWAP_LONG,SYMBOL_SWAP_SHORT,SYMBOL_SWAP_SUNDAY,
      SYMBOL_SWAP_MONDAY,SYMBOL_SWAP_TUESDAY,SYMBOL_SWAP_WEDNESDAY,SYMBOL_SWAP_THURSDAY,SYMBOL_SWAP_FRIDAY,SYMBOL_SWAP_SATURDAY};
   string dk[]={"point","tick_size","contract_size","tick_value_profit","tick_value_loss","volume_min","volume_max",
      "volume_step","volume_limit","margin_initial","margin_maintenance","swap_long","swap_short","swap_sunday",
      "swap_monday","swap_tuesday","swap_wednesday","swap_thursday","swap_friday","swap_saturday"};
   for(int i=0;i<ArraySize(dp);i++) if(!Double156(dk[i],dp[i])) return false;
   if(!Currency156() || !Sessions156() || !Commissions156() ||
      !Margin156("buy",ORDER_TYPE_BUY) || !Margin156("sell",ORDER_TYPE_SELL) || !Clocks156("context_after")) return false;
   if(!SerializeGuard156()) return false;
   if(!Append156(StringFormat("Z\t1\t%I64u",clock156.queries))) return Stop156(14);
   return true;
}
bool Open156()
{
   // Explicit job only. No terminal scanning, FILE_COMMON, pipe, DLL or SDK.
   FolderCreate("ForexDemoLab156",0);
   folder156="ForexDemoLab156\\Job156-"+JobToken156;
   ResetLastError();bool exists=FileIsExist(folder156,0);int error=GetLastError();
   if(exists || (error!=0 && error!=5019)) return false;
   ResetLastError();if(!FolderCreate(folder156,0) || GetLastError()!=0) return false;
   file156=NewFile156(folder156+"\\NativePort156.txt");
   if(file156==INVALID_HANDLE) return false;
   return Append156("H\tFXDL_NATIVE_PORT156_V1\tnon_admitted_prototype\t"+JobToken156);
}
void OnStart()
{
   if(!CollectEvidence) {Status156(100);return;}
   if(!RunGranted156()) {Status156(101);return;} // Hard closed before account, clock, file or price reads.
   if(!Identifier156(JobToken156)) {Status156(102);return;}
   InitPort156(clock156,GetMicrosecondCount());InitLease156(lease156);
   if(Digest156("abc")!="BA7816BF8F01CFEA414140DE5DAE2223B00361A396177A9CB410FF61F20015AD" || Hex156(1.0)!="3FF0000000000000") {Stop156(109);return;}
   int reason=Guard156(false);
   if(reason!=0) {Stop156(reason);return;}
   ResetLastError();private_login156=AccountInfoInteger(ACCOUNT_LOGIN);int error=GetLastError();
   ResetLastError();private_server156=AccountInfoString(ACCOUNT_SERVER);error|=GetLastError();
   reason=Guard156(true);
   if(error!=0 || reason!=0) {Stop156(reason!=0?reason:2);return;}
   if(!Open156()) {Stop156(109);return;}
   if(!Snapshot156() || !Clocks156("before") || !Tick156() || !Clocks156("after") || !Lease156() || !SerializeGuard156()) return;
   if(clock156.pending || !Append156(StringFormat("E\t%I64u\t%I64u",clock156.queries,clock156.requests))) {Stop156(106);return;}
   ResetLastError();FileClose(file156);error=GetLastError();
   file156=INVALID_HANDLE;clock156.ended=true;Status156(error==0?0:109);
}
