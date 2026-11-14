#include <iostream>
#include <limits>
#include <stdexcept>
using ulong=unsigned long;
#include "../Scripts/PrivateSchedule109.mqh"
static_assert(sizeof(ulong)==8,"64-bit shim required");
int checks=0;
void require(bool result) { ++checks; if(!result) throw std::runtime_error("schedule_failed"); }
struct Capture { int observed=0,reason=0;ulong elapsed=0,min_gap=0,max_gap=0; };

// Invented timing model. No sleep, market data or broker calls.
Capture simulate(bool adaptive,ulong jitter,ulong stall)
{
   Capture result;const ulong origin=1000;ulong now=origin,last=0;
   for(int i=1;i<=120;++i) {
      for(;;) {
         bool ready=false;int pause=0;
         int reason=Schedule109(origin,last,now,ready,pause);
         if(reason!=0) { result.reason=reason;result.elapsed=now-origin;return result; }
         if(ready) break;
         if(!adaptive) pause=20;
         now+=pause>0?(ulong)pause*1000+jitter:100;
      }
      if(i==60) now+=stall; // A single invented preemption, not measured OS proof.
      now+=250; // Modeled pre-read account/attempt IO cost.
      bool ready=false;int pause=0;
      int reason=Schedule109(origin,last,now,ready,pause);
      if(reason!=0) { result.reason=reason;result.elapsed=now-origin;return result; }
      require(ready);
      if(last!=0) {
         ulong gap=now-last;
         require(gap>=500000);
         if(result.min_gap==0 || gap<result.min_gap) result.min_gap=gap;
         if(gap>result.max_gap) result.max_gap=gap;
      }
      last=now;result.observed++;now+=100; // Modeled quote/after-guard/outcome cost.
   }
   result.elapsed=now-origin;return result;
}
void emit(const char *name,const Capture &r)
{
   std::cout<<"\""<<name<<"\":{\"observed\":"<<r.observed<<",\"reason\":"<<r.reason
      <<",\"elapsed_us\":"<<r.elapsed<<",\"min_gap_us\":"<<r.min_gap<<",\"max_gap_us\":"<<r.max_gap<<"}";
}
int main()
{
   bool ready=true;int pause=99;
   require(Schedule109(1000,0,1000,ready,pause)==0 && ready && pause==0);
   require(Schedule109(1000,1000,1000,ready,pause)==0 && !ready && pause==20);
   require(Schedule109(1000,1000,476000,ready,pause)==0 && !ready && pause==0);
   require(Schedule109(1000,1000,474999,ready,pause)==0 && !ready && pause==1);
   require(Schedule109(1000,1000,500999,ready,pause)==0 && !ready && pause==0);
   require(Schedule109(1000,1000,501000,ready,pause)==0 && ready && pause==0);
   require(Schedule109(1000,1000,900000,ready,pause)==0 && ready && pause==0);
   require(Schedule109(1000,0,999,ready,pause)==12 && !ready && pause==0);
   require(Schedule109(1000,999,1001,ready,pause)==12 && !ready && pause==0);
   require(Schedule109(1000,2000,1999,ready,pause)==12 && !ready && pause==0);
   require(Schedule109(1000,0,60001000,ready,pause)==0 && ready && pause==0);
   require(Schedule109(1000,0,60001001,ready,pause)==13 && !ready && pause==0);
   ulong top=std::numeric_limits<ulong>::max();
   require(Schedule109(top-60000000,top-500000,top,ready,pause)==0 && ready && pause==0);
   require(Schedule109(1000,1000,top,ready,pause)==13 && !ready && pause==0);
   require(Schedule109(top-1000,top,0,ready,pause)==12 && !ready && pause==0);
   int boundary_checks=checks;
   Capture ideal=simulate(true,0,0),old=simulate(false,1500,437000);
   Capture improved=simulate(true,1500,437000),stalled=simulate(true,1500,3000000);
   Capture oversleep=simulate(true,500000,0);
   require(ideal.observed==120 && ideal.reason==0 && ideal.elapsed<=60000000);
   require(old.observed<120 && old.reason==13);
   require(improved.observed==120 && improved.reason==0 && improved.elapsed<=60000000);
   require(stalled.observed<120 && stalled.reason==13);
   require(oversleep.observed<120 && oversleep.reason==13);
   std::cout<<"{\"passed\":true,\"boundary_checks\":"<<boundary_checks<<",\"checks\":"<<checks<<",";
   emit("ideal",ideal);std::cout<<",";emit("coarse_wait",old);std::cout<<",";
   emit("adaptive_wait",improved);std::cout<<",";emit("long_stall",stalled);std::cout<<",";
   emit("unbounded_sleep_delay",oversleep);std::cout<<"}\n";
}
