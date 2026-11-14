#include <iostream>
#include <string>
#include <stdexcept>
using string=std::string;
using ulong=unsigned long;
const long ACCOUNT_TRADE_MODE_DEMO=0;
#include "../Scripts/PrivateGuard107.mqh"
static_assert(sizeof(long)==8 && sizeof(ulong)==8,"64-bit shim required");
int checks=0;
void require(bool result) { ++checks; if(!result) throw std::runtime_error("guard_failed"); }
PrivateAccount107 good() { return {true,true,false,false,true,0,42,"invented","USD","EURUSD","EUR","USD"}; }
int main()
{
   auto s=good(); require(GuardReason107(s,false,0,"")==0);
   require(GuardReason107(s,true,42,"invented")==0);
   for(long mode:{1L,2L,-1L,99L}) { s=good();s.mode=mode; require(GuardReason107(s,false,0,"")==5); }
   s=good();s.query_ok=false;require(GuardReason107(s,false,0,"")==2);
   s=good();s.connected=false;require(GuardReason107(s,false,0,"")==3);
   s=good();s.tester=true;require(GuardReason107(s,false,0,"")==4);
   s=good();s.currency="EUR";require(GuardReason107(s,false,0,"")==6);
   s=good();s.algo=true;require(GuardReason107(s,false,0,"")==7);
   for(long id:{0L,-1L}) { s=good();s.login=id;require(GuardReason107(s,false,0,"")==8); }
   s=good();s.server="";require(GuardReason107(s,false,0,"")==8);
   s=good();require(GuardReason107(s,true,43,"invented")==9);
   require(GuardReason107(s,true,42,"changed")==9);
   s=good();s.visible=false;require(GuardReason107(s,false,0,"")==10);
   s=good();s.symbol="EURUSD.a";require(GuardReason107(s,false,0,"")==10);
   s=good();s.base="GBP";require(GuardReason107(s,false,0,"")==10);
   s=good();s.quote="EUR";require(GuardReason107(s,false,0,"")==10);
   // Identity/mode/Algo transitions reject at every surrounding guard.
   for(int stage=0;stage<3;++stage) {
      s=good();s.login++;require(GuardReason107(s,true,42,"invented")==9);
      s=good();s.mode=2;require(GuardReason107(s,true,42,"invented")==5);
      s=good();s.algo=true;require(GuardReason107(s,true,42,"invented")==7);
   }
   require(ClockReason107(100,1000,100,1000,"2026.10.12")==0);
   require(ClockReason107(100,1000,160,60001000,"2026.10.12")==0);
   require(ClockReason107(100,1000,160,60001001,"2026.10.12")==13);
   require(ClockReason107(100,1000,100,999,"2026.10.12")==12);
   require(ClockReason107(100,1000,99,1001,"2026.10.12")==12);
   require(ClockReason107(0,1000,100,1001,"2026.10.12")==12);
   require(ClockReason107(100,1000,103,1001,"2026.10.12")==12);
   require(ClockReason107(100,1000,100,3001000,"2026.10.12")==12);
   require(ClockReason107(100,1000,100,1001,"2026.10.13")==11);
   require(QuoteReason107(100,100123,1,1.1,0,0,true)==0);
   require(QuoteReason107(100,100123,1,1,0,0,true)==0);
   require(QuoteReason107(100,99123,1,1.1,0,0,true)==16);
   require(QuoteReason107(0,0,1,1.1,0,0,true)==16);
   require(QuoteReason107(32535216000,32535216000000,1,1.1,0,0,true)==16);
   require(QuoteReason107(100,100123,0,1.1,0,0,true)==16);
   require(QuoteReason107(100,100123,2,1.1,0,0,true)==16);
   require(QuoteReason107(100,100123,1,1.1,-1,0,true)==16);
   require(QuoteReason107(100,100123,1,1.1,0,-1,true)==16);
   require(QuoteReason107(100,100123,1,1.1,0,0,false)==16);
   std::cout << "{\"guard_checks\":" << checks << ",\"passed\":true}\n";
}
