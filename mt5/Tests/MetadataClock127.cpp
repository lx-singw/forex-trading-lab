#include <iostream>
#include <string>
#include <stdexcept>
using string=std::string;
using ulong=unsigned long;
const long ACCOUNT_TRADE_MODE_DEMO=0;
#include "../Scripts/PrivateGuard107.mqh"
#include "../Scripts/MetadataClock127.mqh"
static_assert(sizeof(long)==8 && sizeof(ulong)==8,"64-bit shim required");
int checks=0;
void require(bool ok) {++checks;if(!ok) throw std::runtime_error("metadata_guard_failed");}
MetadataClock127 fresh() {MetadataClock127 s;InitMetadata127(s,100,1000);return s;}
PrivateAccount107 good() {return {true,true,false,false,true,0,42,"invented_identity","USD","EURUSD","EUR","USD"};}
int main()
{
   auto s=fresh();require(CheckClock127(s,100,1000,"2026.10.14")==0);
   require(CheckClock127(s,160,60001000,"2026.10.14")==0);
   require(CheckClock127(s,160,60001001,"2026.10.14")==13);
   s=fresh();require(CheckClock127(s,99,1001,"2026.10.14")==12);
   s=fresh();require(CheckClock127(s,100,999,"2026.10.14")==12);
   s=fresh();require(CheckClock127(s,103,1001,"2026.10.14")==12);
   s=fresh();require(CheckClock127(s,100,3001000,"2026.10.14")==12);
   s=fresh();require(CheckClock127(s,100,1001,"2026.10.12")==11);
   s=fresh();require(CheckClock127(s,100,1001,"2026.10.15")==11);
   s=fresh();require(CheckClock127(s,101,1001000,"2026.10.14")==0);
   require(CheckClock127(s,100,1002000,"2026.10.14")==12);
   s=fresh();for(int i=0;i<128;i++) require(NextQuery127(s)==0 && s.queries==i+1);
   require(NextQuery127(s)==20 && s.queries==128);
   s=fresh();s.queries=-1;require(NextQuery127(s)==20);
   for(int stage=0;stage<4;stage++)
   {
      auto a=good();require(GuardReason107(a,true,42,"invented_identity")==0);
      a.mode=2;a.server="label_contains_demo";require(GuardReason107(a,false,0,"")==5);
      a=good();a.mode=1;require(GuardReason107(a,false,0,"")==5);
      a=good();a.mode=-1;require(GuardReason107(a,false,0,"")==5);
      a=good();a.query_ok=false;require(GuardReason107(a,false,0,"")==2);
      a=good();a.login++;require(GuardReason107(a,true,42,"invented_identity")==9);
      a=good();a.server="changed_identity";require(GuardReason107(a,true,42,"invented_identity")==9);
      a=good();a.algo=true;require(GuardReason107(a,true,42,"invented_identity")==7);
      a=good();a.connected=false;require(GuardReason107(a,true,42,"invented_identity")==3);
   }
   require(QuoteReason107(100,100123,1.1,1.1001,0,0,true)==0);
   require(QuoteReason107(100,100123,1.2,1.1,0,0,true)==16);
   std::cout<<"{\"passed\":true,\"checks\":"<<checks<<"}\n";
}
