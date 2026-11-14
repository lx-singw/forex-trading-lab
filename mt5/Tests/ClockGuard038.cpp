// Executes the exact pure MQL header; native terminal APIs are not simulated.
#include <iostream>
#include <string>
#include <cmath>
#include <limits>
#include <stdexcept>
using string=std::string;
using ulong=unsigned long;
const long ACCOUNT_TRADE_MODE_DEMO=0;
int StringLen(const string &s) { return static_cast<int>(s.size()); }
#include "../Scripts/ClockGuard038.mqh"
static_assert(sizeof(long)==8 && sizeof(ulong)==8, "64-bit MQL integer shim required");

int checks=0;
void require(bool passed) { ++checks; if(!passed) throw std::runtime_error("guard_case_failed"); }
ClockAccount038 account() { return {true,true,false,false,0,"USD",123,"PRIVATE"}; }
int main()
{
   auto s=account(); require(AccountReason038(s,false,0,"")==0);
   for(long mode: {1L,2L,-1L,99L}) {s=account();s.mode=mode;require(AccountReason038(s,false,0,"")==4);}
   s=account();s.query_ok=false;require(AccountReason038(s,false,0,"")==1);
   s=account();s.connected=false;require(AccountReason038(s,false,0,"")==2);
   s=account();s.tester=true;require(AccountReason038(s,false,0,"")==3);
   s=account();s.currency="EUR";require(AccountReason038(s,false,0,"")==5);
   s=account();s.algo_allowed=true;require(AccountReason038(s,false,0,"")==6);
   for(long id: {0L,-1L}) {s=account();s.login=id;require(AccountReason038(s,false,0,"")==7);}
   s=account();s.server="";require(AccountReason038(s,false,0,"")==7);
   s=account();require(AccountReason038(s,true,123,"PRIVATE")==0);
   require(AccountReason038(s,true,124,"PRIVATE")==8);
   require(AccountReason038(s,true,123,"CHANGED")==8);
   // Repeated checks before and after a sample reject mode, identity or Algo changes.
   for(int stage=0;stage<5;++stage) {
      s=account();require(AccountReason038(s,true,123,"PRIVATE")==0);
      s.login+=stage+1;require(AccountReason038(s,true,123,"PRIVATE")==8);
      s=account();s.mode=2;require(AccountReason038(s,true,123,"PRIVATE")==4);
      s=account();s.algo_allowed=true;require(AccountReason038(s,true,123,"PRIVATE")==6);
   }
   require(SymbolReason038(true,true,"EUR","USD","EURUSD")==0);
   require(SymbolReason038(false,true,"EUR","USD","EURUSD")==9);
   require(SymbolReason038(true,false,"EUR","USD","EURUSD")==9);
   require(SymbolReason038(true,true,"GBP","USD","EURUSD")==9);
   require(SymbolReason038(true,true,"EUR","EUR","EURUSD")==9);
   require(SymbolReason038(true,true,"EUR","USD","EURUSD.a")==9);
   ClockReading038 b={1791306000,1791306000,1791295200,1791302400};
   auto a=b;
   auto test=[&](ClockReading038 before,ClockReading038 after,ulong bu,ulong au,long ts,long tm,
                 double bid,double ask,bool finite,string bd="2026.10.06",string ad="2026.10.06") {
      return ReadingReason038(before,after,bu,au,ts,tm,bid,ask,finite,bd,ad);
   };
   const long ts=b.current_s,tm=ts*1000;
   require(test(b,a,100,200,ts,tm,1,1.1,true)==0);
   require(test(b,a,100,200,ts,tm,1,1.1,true,"2026.10.05")==10);
   require(test(b,a,100,200,ts,tm,1,1.1,true,"2026.10.06","2026.10.07")==10);
   for(int i=0;i<4;++i) {
      auto bad=b;
      if(i==0) bad.current_s=0;
      if(i==1) bad.calculated_server_s=0;
      if(i==2) bad.gmt_s=0;
      if(i==3) bad.local_s=0;
      require(test(bad,a,100,200,ts,tm,1,1.1,true)==11);
   }
   for(int i=0;i<4;++i) {
      auto bad=a;
      if(i==0) --bad.current_s;
      if(i==1) --bad.calculated_server_s;
      if(i==2) --bad.gmt_s;
      if(i==3) --bad.local_s;
      require(test(b,bad,100,200,ts,tm,1,1.1,true)==11);
   }
   require(test(b,a,200,100,ts,tm,1,1.1,true)==11);
   require(test(b,a,0,15000001,ts,tm,1,1.1,true)==12);
   require(test(b,a,0,1,ts,tm,0,1.1,true)==13);
   require(test(b,a,0,1,ts,tm,2,1,true)==13);
   require(test(b,a,0,1,ts,tm,1,1.1,false)==13);
   require(test(b,a,0,1,0,tm,1,1.1,true)==13);
   require(test(b,a,0,1,ts,0,1,1.1,true)==13);
   require(test(b,a,0,1,ts+1,tm,1,1.1,true)==13);
   require(test(b,a,0,1,ts,tm+999,1,1.1,true)==0);
   require(test(b,a,0,1,ts-60,tm-60000,1,1.1,true)==0);
   require(test(b,a,0,1,ts-61,tm-60001,1,1.1,true)==14);
   require(test(b,a,0,1,ts+2,tm+2000,1,1.1,true)==0);
   require(test(b,a,0,1,ts+2,tm+2001,1,1.1,true)==14);
   auto far=a;far.current_s=a.gmt_s+86401;
   auto fb=far;
   require(test(fb,far,0,1,far.current_s,far.current_s*1000,1,1.1,true)==15);
   far.current_s=a.gmt_s-86401;fb=far;
   require(test(fb,far,0,1,far.current_s,far.current_s*1000,1,1.1,true)==15);
   auto wall=a;wall.gmt_s+=3;
   require(test(b,wall,0,1,ts,tm,1,1.1,true)==16);
   require(test(b,a,0,3000000,ts,tm,1,1.1,true)==16);
   wall=a;wall.gmt_s+=15;
   require(test(b,wall,0,15000000,ts,tm,1,1.1,true)==0);
   auto huge=a;huge.current_s=std::numeric_limits<long>::max();
   require(test(b,huge,0,1,ts,tm,1,1.1,true)==11);
   require(test(b,a,0,1,ts,std::numeric_limits<long>::max(),1,1.1,true)==11);
   std::cout << "{\"guard_checks\":" << checks << ",\"passed\":true}\n";
}
