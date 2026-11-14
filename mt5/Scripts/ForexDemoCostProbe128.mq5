#property copyright "Forex Demo Lab"
#property version "1.000"
#property strict
#property script_show_inputs
#property description "Private current demo commission/margin probe. No orders or history."
#include "PrivateGuard107.mqh"
#include "CostBounds128.mqh"

input bool CollectEvidence = false;
union NativeDouble128 { double value; ulong bits; };
CostClock128 clock128;
long private_login128=0;
string private_server128="";
int file128=INVALID_HANDLE;
int guard_checks128=0;
int open_reason128=14;
ulong bytes128=0;
string chain128="0000000000000000000000000000000000000000000000000000000000000000";
long bs128=0,as128=0,gs128=0;
ulong bu128=0,au128=0,gu128=0;

string Hex128(const double value)
{
   NativeDouble128 u;u.value=value;return StringFormat("%.16I64X",u.bits);
}
string Digest128(const string text)
{
   uchar src[],key[],dst[];
   if(StringToCharArray(text,src,0,StringLen(text),CP_UTF8)!=StringLen(text)) return "";
   ResetLastError();
   if(CryptEncode(CRYPT_HASH_SHA256,src,key,dst)!=32 || GetLastError()!=0) return "";
   string result="";
   for(int i=0;i<32;i++) result+=StringFormat("%.2X",dst[i]);
   return result;
}
int Guard128(const bool identified)
{
   PrivateAccount107 s;s.query_ok=true;guard_checks128++;
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
   return GuardReason107(s,identified,private_login128,private_server128);
}
int Now128()
{
   long seconds=(long)TimeGMT();ulong micros=GetMicrosecondCount();
   return CheckCostClock128(clock128,seconds,micros,TimeToString((datetime)seconds,TIME_DATE));
}
void Status128(const int reason)
{
   PrintFormat("FXDL128 {\"reason_code\":%d,\"queries\":%d,\"guard_checks\":%d,\"bytes\":%I64u}",
               reason,clock128.queries,guard_checks128,bytes128);
}
bool Append128(const string payload)
{
   string next=Digest128(chain128+"\t"+payload+"\n");
   if(StringLen(next)!=64) return false;
   string line=payload+"\t"+next+"\r\n";
   if(StringLen(line)>2048 || bytes128+(ulong)StringLen(line)>65536) return false;
   ResetLastError();ulong size=FileSize(file128);int error=GetLastError();
   if(error!=0 || size!=bytes128) return false;
   ResetLastError();uint written=FileWriteString(file128,line);
   if(written!=(uint)StringLen(line) || GetLastError()!=0) return false;
   ResetLastError();FileFlush(file128);
   if(GetLastError()!=0) return false;
   bytes128+=written;chain128=next;return true;
}
bool Stop128(const int reason)
{
   bool saved=false;
   if(file128!=INVALID_HANDLE)
   {
      saved=Append128(StringFormat("S\t%d\t%d",reason,clock128.queries));
      FileClose(file128);file128=INVALID_HANDLE;
   }
   Status128(saved?reason:14);return false;
}
bool Begin128(const string tag,const string key)
{
   int reason=IsStopped()?18:Guard128(true);
   if(reason==0) reason=Now128();
   if(reason==0) reason=NextCostQuery128(clock128);
   if(reason!=0) return Stop128(reason);
   if(!Append128(StringFormat("A\t%d\t%s\t%s",clock128.queries,tag,key))) return Stop128(14);
   reason=Guard128(true);
   bs128=(long)TimeGMT();bu128=GetMicrosecondCount();
   if(reason==0) reason=CheckCostClock128(clock128,bs128,bu128,TimeToString((datetime)bs128,TIME_DATE));
   if(reason!=0) return Stop128(reason);
   return true;
}
bool After128()
{
   au128=GetMicrosecondCount();as128=(long)TimeGMT();
   int reason=Guard128(true);
   gu128=GetMicrosecondCount();gs128=(long)TimeGMT();
   if(reason==0) reason=CheckCostClock128(clock128,as128,au128,TimeToString((datetime)as128,TIME_DATE));
   if(reason==0) reason=CheckCostClock128(clock128,gs128,gu128,TimeToString((datetime)gs128,TIME_DATE));
   if(reason!=0) return Stop128(reason); // Queried value is never serialized on a failed after-read guard.
   return true;
}
bool Record128(const string tag,const string key,const bool ok,const int error,const string value)
{
   string row=StringFormat("%s\t%d\t%s\t%I64d\t%I64d\t%I64d\t%I64u\t%I64u\t%I64u\t%d\t%d\t%s",
                          tag,clock128.queries,key,bs128,as128,gs128,bu128,au128,gu128,ok?1:0,error,value);
   if(!Append128(row)) return Stop128(14);
   return true;
}
bool Clocks128(const string key)
{
   if(!Begin128("C",key)) return false;
   ResetLastError();long tc=(long)TimeCurrent(),ts=(long)TimeTradeServer(),tg=(long)TimeGMT(),tl=(long)TimeLocal();
   long go=(long)TimeGMTOffset(),ds=(long)TimeDaylightSavings();int error=GetLastError();
   if(!After128()) return false;
   if(error!=0) return Stop128(12);
   return Record128("C",key,true,0,StringFormat("%I64d\t%I64d\t%I64d\t%I64d\t%I64d\t%I64d",tc,ts,tg,tl,go,ds));
}
bool CurrencyToken128(const string value)
{
   if(value=="") return true;
   if(StringLen(value)!=3) return false;
   for(int i=0;i<3;i++) if(StringGetCharacter(value,i)<65 || StringGetCharacter(value,i)>90) return false;
   return true;
}
string CurrencyText128(const string value) {return value==""?"EMPTY":value;}
bool SerializeGuard128()
{
   int reason=IsStopped()?18:Guard128(true);
   if(reason==0) reason=Now128();
   if(reason!=0) return Stop128(reason);
   return true;
}
bool Margin128(const string key,const ENUM_ORDER_TYPE side)
{
   if(!Begin128("M",key)) return false;
   double initial=0,maintenance=0;
   ResetLastError();bool ok=SymbolInfoMarginRate("EURUSD",side,initial,maintenance);
   int error=GetLastError();ok=ok && error==0;
   if(!After128()) return false;
   if(ok && (!MathIsValidNumber(initial) || !MathIsValidNumber(maintenance) || initial<0 || maintenance<0)) return Stop128(16);
   return Record128("M",key,ok,error,Hex128(ok?initial:0)+"\t"+Hex128(ok?maintenance:0));
}
bool Commissions128()
{
   if(!Begin128("K","commissions")) return false;
   MqlCommission rules[];
   ResetLastError();int count=SymbolInfoCommissions("EURUSD",rules);int error=GetLastError();
   if(!After128()) return false;
   if(count < -1) return Stop128(16);
   bool ok=count>=0 && error==0;
   if(ok)
   {
      int reason=CostRuleCountReason128(count,ArraySize(rules));
      if(reason!=0) return Stop128(reason);
      int total_tiers=0;
      for(int i=0;i<count;i++)
      {
         int tiers=ArraySize(rules[i].tiers);
         reason=CostTierCountReason128(tiers,total_tiers);
         if(reason!=0) return Stop128(reason);
         total_tiers+=tiers;
         if(!CurrencyToken128(rules[i].currency)) return Stop128(16);
         for(int j=0;j<tiers;j++)
         {
            if(!CurrencyToken128(rules[i].tiers[j].currency) ||
               !MathIsValidNumber(rules[i].tiers[j].value) ||
               !MathIsValidNumber(rules[i].tiers[j].min_value) ||
               !MathIsValidNumber(rules[i].tiers[j].max_value) ||
               !MathIsValidNumber(rules[i].tiers[j].range_from) ||
               !MathIsValidNumber(rules[i].tiers[j].range_to)) return Stop128(16);
         }
      }
   }
   if(!SerializeGuard128()) return false;
   if(!Record128("K","commissions",ok,error,StringFormat("%d",count))) return false;
   if(!ok) return true; // Failed return/error is preserved; no rule payload is trusted.
   for(int i=0;i<count;i++)
   {
      if(!SerializeGuard128()) return false;
      string rule=StringFormat("R\t%d\t%d\t%s\t%d\t%d\t%d\t%d\t%d\t%d",
         clock128.queries,i,CurrencyText128(rules[i].currency),(int)rules[i].mode_range,
         (int)rules[i].mode_charge,(int)rules[i].mode_entry,(int)rules[i].mode_direction,
         (int)rules[i].mode_profit,ArraySize(rules[i].tiers));
      if(!Append128(rule)) return Stop128(14);
      for(int j=0;j<ArraySize(rules[i].tiers);j++)
      {
         if(!SerializeGuard128()) return false;
         string tier=StringFormat("T\t%d\t%d\t%d\t%d\t%d\t%s\t%s\t%s\t%s\t%s\t%s",
            clock128.queries,i,j,(int)rules[i].tiers[j].mode,(int)rules[i].tiers[j].volume_type,
            Hex128(rules[i].tiers[j].value),Hex128(rules[i].tiers[j].min_value),
            Hex128(rules[i].tiers[j].max_value),Hex128(rules[i].tiers[j].range_from),
            Hex128(rules[i].tiers[j].range_to),CurrencyText128(rules[i].tiers[j].currency));
         if(!Append128(tier)) return Stop128(14);
      }
   }
   return true;
}
bool Open128()
{
   ResetLastError();bool root_file=FileIsExist("ForexDemoLab128",0);int error=GetLastError();
   if(root_file || (error!=0 && error!=5018 && error!=5019)) return false;
   if(error!=5018)
   {
      ResetLastError();if(!FolderCreate("ForexDemoLab128",0) || GetLastError()!=0) return false;
   }
   string folder=StringFormat("ForexDemoLab128\\Run128-%I64d-%I64u-%I64u",clock128.origin_s,GetTickCount64(),clock128.origin_us);
   ResetLastError();bool exists=FileIsExist(folder,0);error=GetLastError();
   if(exists || (error!=0 && error!=5019)) return false;
   ResetLastError();if(!FolderCreate(folder,0) || GetLastError()!=0) return false;
   int reason=Guard128(true);if(reason==0) reason=Now128();
   if(reason!=0) {open_reason128=reason;return false;}
   string filename=folder+"\\Costs128.txt";
   ResetLastError();exists=FileIsExist(filename,0);error=GetLastError();
   if(exists || (error!=0 && error!=5019)) return false;
   ResetLastError();file128=FileOpen(filename,FILE_READ|FILE_WRITE|FILE_BIN|FILE_ANSI,0,CP_UTF8);
   if(file128==INVALID_HANDLE || GetLastError()!=0) return false;
   ResetLastError();ulong size=FileSize(file128);error=GetLastError();
   if(size!=0 || error!=0) {FileClose(file128);file128=INVALID_HANDLE;return false;}
   return Append128(StringFormat("H\tFXDL_COST128_V1\tmarket_declared\t2026.10.14\t%I64d\t%I64u",clock128.origin_s,clock128.origin_us));
}
void OnStart()
{
   InitCost128(clock128,0,0);
   if(!CollectEvidence) {Status128(1);return;}
   if(Digest128("abc")!="BA7816BF8F01CFEA414140DE5DAE2223B00361A396177A9CB410FF61F20015AD" || Hex128(1.0)!="3FF0000000000000") {Status128(17);return;}
   int reason=Guard128(false);
   if(reason!=0) {Status128(reason);return;}
   ResetLastError();private_login128=AccountInfoInteger(ACCOUNT_LOGIN);int error=GetLastError();
   ResetLastError();private_server128=AccountInfoString(ACCOUNT_SERVER);error|=GetLastError();
   reason=Guard128(true);
   if(error!=0 || reason!=0) {Status128(reason!=0?reason:2);return;}
   InitCost128(clock128,(long)TimeGMT(),GetMicrosecondCount());
   reason=Now128();if(reason!=0) {Status128(reason);return;}
   if(!Open128()) {if(file128!=INVALID_HANDLE) {FileClose(file128);file128=INVALID_HANDLE;}Status128(open_reason128);return;}
   if(!Clocks128("clock_before") || !Commissions128() ||
      !Margin128("buy",ORDER_TYPE_BUY) || !Margin128("sell",ORDER_TYPE_SELL) ||
      !Clocks128("clock_after")) return;
   reason=Guard128(true);if(reason==0) reason=Now128();
   if(reason!=0) {Stop128(reason);return;}
   if(!Append128(StringFormat("E\t%d\t%I64d\t%I64u",clock128.queries,clock128.last_s,clock128.last_us))) {Stop128(14);return;}
   FileClose(file128);file128=INVALID_HANDLE;Status128(0);
}
