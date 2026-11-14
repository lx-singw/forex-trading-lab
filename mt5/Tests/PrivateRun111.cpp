#include <iostream>
#include <string>
#include <stdexcept>
#include <limits>
using string=std::string;
using ulong=unsigned long;
const long ACCOUNT_TRADE_MODE_DEMO=0;
#include "../Scripts/PrivateGuard107.mqh"
#include "../Scripts/PrivateRun111.mqh"
static_assert(sizeof(ulong)==8 && sizeof(long)==8,"64-bit shim required");
int checks=0;
void require(bool value) { ++checks;if(!value) throw std::runtime_error("run_failed"); }
Run111 fresh() { Run111 s;Init111(s,100,1000);return s; }
PrivateAccount107 good() { return {true,true,false,false,true,0,42,"invented","USD","EURUSD","EUR","USD"}; }
void sample(Run111 &s,ulong us)
{
   bool ready=false;int pause=0;
   require(Wait111(s,us,ready,pause)==0 && ready);
   require(Attempt111(s)==0);
   require(Reserve111(s,80,0)==0); // Invented committed attempt bytes.
   long seconds=100+(long)((us-1000)/1000000);
   require(Receipt111(s,seconds,seconds,seconds,us,us+10,us+20,"2026.10.12")==0);
   require(Reserve111(s,300,80)==0);
   require(Outcome111(s,0)==0);
}
int main()
{
   auto s=fresh();bool ready=true;int pause=99;
   require(Clock111(s,100,1000,"2026.10.12")==0);
   require(Clock111(s,3700,3600001000UL,"2026.10.12")==0);
   require(Clock111(s,3700,3600001001UL,"2026.10.12")==13);
   require(Clock111(s,99,1000,"2026.10.12")==12);
   require(Clock111(s,100,999,"2026.10.12")==12);
   require(Clock111(s,103,1001,"2026.10.12")==12);
   require(Clock111(s,100,1000,"2026.10.13")==11);
   require(Wait111(s,999,ready,pause)==12 && !ready && pause==0);
   require(Wait111(s,3600001001UL,ready,pause)==13 && !ready && pause==0);
   require(Attempt111(s)==19);
   require(Segment111(s)==0);
   sample(s,1000);
   require(Wait111(s,476000,ready,pause)==0 && !ready && pause==0);
   require(Wait111(s,501000,ready,pause)==0 && ready);
   require(Segment111(s)==19); // No premature rotation.
   for(int i=2;i<=120;++i) sample(s,1000+(ulong)(i-1)*500000);
   ulong bytes=s.bytes;ulong last=s.last_read_us;
   require(Segment111(s)==0 && s.attempts==120 && s.observed==120 && s.bytes==bytes && s.last_read_us==last);
   require(Wait111(s,last+499999,ready,pause)==0 && !ready);
   require(Attempt111(s)==0);
   require(Receipt111(s,s.last_s,s.last_s,s.last_s,last+499999,last+499999,last+499999,"2026.10.12")==12);
   require(Attempt111(s)==19); // Pending attempt is never overwritten.
   End111(s);require(Attempt111(s)==19 && Segment111(s)==19 && Reserve111(s,1,0)==19);
   require(s.pending && s.attempts==121 && s.observed==120);

   s=fresh();require(Segment111(s)==0);require(Attempt111(s)==0);
   require(Reserve111(s,80,0)==0); // Simulated partial outcome write.
   require(Reserve111(s,300,80)==0);ulong reserved=s.bytes;
   End111(s);require(s.pending && s.observed==0 && s.bytes==reserved);
   auto restarted=fresh();require(Segment111(restarted)==0 && restarted.attempts==0 && s.ended && s.bytes==reserved);
   s=fresh();require(Segment111(s)==0);require(Attempt111(s)==0);
   require(Outcome111(s,15)==0 && s.fault==15 && !s.pending);
   require(Attempt111(s)==19 && Segment111(s)==19 && Wait111(s,1000,ready,pause)==19);
   s=fresh();s.bytes=4194304-80;require(Reserve111(s,80,0)==0);
   require(Reserve111(s,1,0)==14 && s.bytes==4194304);
   s=fresh();require(Reserve111(s,1,262144)==14);
   require(Reserve111(s,2049,0)==14 && Reserve111(s,0,0)==14);
   require(Reserve111(s,1,std::numeric_limits<ulong>::max())==14);
   s=fresh();s.segments=64;s.segment_attempts=120;require(Segment111(s)==20);
   s=fresh();s.segments=60;s.attempts=7200;require(Attempt111(s)==20);
   s=fresh();Init111(s,100,0);require(Clock111(s,100,0,"2026.10.12")==12);
   s=fresh();require(Wait111(s,std::numeric_limits<ulong>::max(),ready,pause)==13);

   // Inject actual guard decisions before read, after read and at rotation.
   for(int stage=0;stage<3;++stage) {
      for(int fault=0;fault<4;++fault) {
         s=fresh();require(Segment111(s)==0);
         if(stage==2) for(int i=1;i<=120;++i) sample(s,1000+(ulong)(i-1)*500000);
         if(stage==1) { require(Attempt111(s)==0);require(Reserve111(s,80,0)==0); }
         auto account=good();
         if(fault==0) account.mode=2;
         if(fault==1) account.mode=1;
         if(fault==2) account.connected=false;
         if(fault==3) account.login++;
         int reason=GuardReason107(account,true,42,"invented");require(reason!=0);
         int observed=s.observed;End111(s);
         require(Attempt111(s)==19 && Segment111(s)==19 && s.observed==observed);
         if(stage==1) require(s.pending && s.observed==0); // Discarded read is never committed.
      }
   }
   Run111 ideal=fresh();require(Segment111(ideal)==0);
   for(int i=1;i<=7200;++i) {
      if(ideal.segment_attempts==120) { bytes=ideal.bytes;require(Segment111(ideal)==0 && ideal.bytes==bytes); }
      sample(ideal,1000+(ulong)(i-1)*500000);
   }
   require(ideal.attempts==7200 && ideal.observed==7200 && ideal.segments==60);
   require(Attempt111(ideal)==19 || Attempt111(ideal)==20);
   require(Clock111(ideal,3699,3599501020UL,"2026.10.12")==0);
   End111(ideal);require(Segment111(ideal)==19);
   std::cout<<"{\"passed\":true,\"core_checks\":"<<checks
      <<",\"ideal_attempts\":"<<ideal.attempts<<",\"ideal_observed\":"<<ideal.observed
      <<",\"ideal_segments\":"<<ideal.segments<<",\"ideal_reserved_bytes\":"<<ideal.bytes
      <<",\"account_fault_scenarios\":12,\"native_calls\":0}\n";
}
