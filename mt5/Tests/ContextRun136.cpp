#include <string>
#include <iostream>
#include <cstdlib>
using string=std::string;
using ulong=unsigned long;
const long ACCOUNT_TRADE_MODE_DEMO=0;
string IntegerToString(int value) {return std::to_string(value);}
static_assert(sizeof(long)==8 && sizeof(ulong)==8,"64-bit decision widths");
#include "../Scripts/ContextRun136.mqh"
#include "../Scripts/PrivateGuard107.mqh"
#include "../Scripts/CostBounds128.mqh"
long checks=0;
void expect(bool condition) {++checks;if(!condition) {std::cerr<<"context check "<<checks<<" failed\n";std::exit(1);}}
void query(ContextRun136 &s,ulong &micros,bool success=true)
{
   string tag,key;Expected136(s,tag,key);expect(tag!="");
   expect(NextQuery136(s,tag,key)==0);expect(NextQuery136(s,tag,key)==19);
   expect(CheckCollectorClock136(s,100+(long)((micros-1000)/1000000),micros,"2026.10.26")==0);
   if(!s.in_context && s.poll_part==0) expect(MarkPollStart136(s,micros)==0);
   else expect(MarkPollStart136(s,micros)==19);
   expect(ReserveCollectorBytes136(s,100)==0);expect(ReserveCollectorBytes136(s,500)==0);
   bool completed=(tag=="C" || tag=="T")?true:success;
   expect(CompleteQuery136(s,completed)==0);expect(CompleteQuery136(s,completed)==19);micros+=100;
}
PrivateAccount107 account()
{
   PrivateAccount107 a;a.query_ok=true;a.connected=true;a.algo=false;a.tester=false;a.visible=true;
   a.mode=ACCOUNT_TRADE_MODE_DEMO;a.login=123;a.server="invented-demo-label";a.currency="USD";
   a.symbol="EURUSD";a.base="EUR";a.quote="USD";return a;
}
int main()
{
   ContextRun136 s;InitCollector136(s,100,1000);ulong micros=1000;
   expect(ContextDue136(s));expect(NextQuery136(s,"C","before")==19);
   for(int poll=0;poll<14400;poll++)
   {
      if(ContextDue136(s))
      {
         expect(BeginContext136(s)==0);expect(EndContext136(s)==19);expect(WaitState136(s)==19);
         while(s.phase!=7) query(s,micros,true); // All9 session indices: maximum101 queries/context.
         expect(EndContext136(s)==0);expect(EndContext136(s)==19);
      }
      expect(WaitState136(s)==0);
      if(poll) {expect(!PollReady136(s,s.last_poll_us+999999));micros=s.last_poll_us+1000000;}
      expect(PollReady136(s,micros));
      for(int part=0;part<3;part++) query(s,micros);
      expect(s.polls==poll+1);
   }
   expect(s.polls==14400 && s.contexts==4 && s.queries==43604);
   expect(WaitState136(s)==20);expect(!ContextDue136(s));expect(BeginContext136(s)==19);
   expect(NextQuery136(s,"C","before")==20);EndCollector136(s);
   expect(ReserveCollectorBytes136(s,1)==19);expect(CompleteQuery136(s,true)==19);
   expect(CheckCollectorClock136(s,s.last_s,s.last_us,"2026.10.26")==19);
   expect(MarkPollStart136(s,s.last_us)==19);
   for(int day=26;day<=30;day++) {InitCollector136(s,100,1000);expect(CheckCollectorClock136(s,100,1000,"2026.10."+IntegerToString(day))==0);}
   for(const string &date:{string("2026.10.24"),string("2026.10.25"),string("2026.10.31"),string("2026.11.01")})
      {InitCollector136(s,100,1000);expect(CheckCollectorClock136(s,100,1000,date)==11);}
   InitCollector136(s,100,1000);expect(CheckCollectorClock136(s,101,1001000,"2026.10.27")==0);
   expect(CheckCollectorClock136(s,102,2001000,"2026.10.31")==11);
   InitCollector136(s,100,1000);expect(CheckCollectorClock136(s,14500,14400001000UL,"2026.10.26")==0);
   expect(CheckCollectorClock136(s,14500,14400001001UL,"2026.10.26")==13);
   InitCollector136(s,100,1000);expect(CheckCollectorClock136(s,99,1000,"2026.10.26")==12);
   expect(CheckCollectorClock136(s,100,999,"2026.10.26")==12);
   expect(CheckCollectorClock136(s,103,1000,"2026.10.26")==12);
   expect(CheckCollectorClock136(s,100,3001000,"2026.10.26")==12);
   InitCollector136(s,100,1000);expect(BeginContext136(s)==0);micros=1000;
   while(s.phase!=7) query(s,micros,false); // Only one absent/failed session index per day:45 queries.
   expect(s.queries==45);expect(EndContext136(s)==0);query(s,micros);
   expect(WaitState136(s)==19);query(s,micros);query(s,micros);
   expect(!PollReady136(s,s.last_poll_us+1));expect(PollReady136(s,s.last_poll_us+1000000));
   InitCollector136(s,100,1000);expect(ReserveCollectorBytes136(s,0)==14);expect(ReserveCollectorBytes136(s,2049)==14);
   s.reserved_bytes=33554431;expect(ReserveCollectorBytes136(s,1)==0);expect(ReserveCollectorBytes136(s,1)==14);
   s.reserved_bytes=(ulong)-1;expect(ReserveCollectorBytes136(s,1)==14);
   InitCollector136(s,100,1000);expect(ReserveCollectorBytes136(s,100)==0);EndCollector136(s);
   expect(s.reserved_bytes==100 && ReserveCollectorBytes136(s,100)==19); // No failed-write refund/retry.
   const int expected[]={2,3,4,5,5,6,7,8,8,9,10,10};
   for(int fault=0;fault<12;fault++) for(int position=0;position<5;position++) for(int after=0;after<2;after++)
   {
      PrivateAccount107 a=account();
      switch(fault) {
         case 0:a.query_ok=false;break;case 1:a.connected=false;break;case 2:a.tester=true;break;
         case 3:a.mode=1;break;case 4:a.mode=2;break;case 5:a.currency="EUR";break;
         case 6:a.algo=true;break;case 7:a.login=0;break;case 8:a.server="";break;
         case 9:a.login=456;break;case 10:a.symbol="GBPUSD";break;case 11:a.visible=false;break;
      }
      expect(GuardReason107(a,true,123,"invented-demo-label")==expected[fault]);
      InitCollector136(s,100,1000);expect(BeginContext136(s)==0);
      micros=1000;
      if(position==0) query(s,micros,false); // Metadata stage.
      else if(position==1) {while(s.phase!=3) query(s,micros,false);} // Commission stage.
      else
      {
         while(s.phase!=7) query(s,micros,false);
         expect(EndContext136(s)==0);
         for(int i=0;i<position-2;i++) query(s,micros); // Clock-before, quote or clock-after.
      }
      if(after) {string tag,key;Expected136(s,tag,key);expect(NextQuery136(s,tag,key)==0);}
      EndCollector136(s);expect(s.pending==(after!=0));expect(CompleteQuery136(s,true)==19);
   }
   expect(CostRuleCountReason128(8,8)==0);expect(CostRuleCountReason128(9,9)==21);
   expect(CostTierCountReason128(16,112)==0);expect(CostTierCountReason128(17,0)==22);
   expect(CostTierCountReason128(1,128)==22);
   InitCollector136(s,100,1000);expect(BeginContext136(s)==0);
   expect(NextQuery136(s,"C","context_before")==0);
   expect(CompleteQuery136(s,false)==19);expect(s.pending && s.phase==0);
   InitCollector136(s,100,1000);expect(s.queries==0 && s.polls==0 && s.contexts==0 && !s.pending && !s.ended);
   std::cout<<"{\"passed\":true,\"checks\":"<<checks<<",\"polls\":14400,\"max_queries\":43604,\"contexts\":4,\"guard_fault_paths\":120,\"native_calls\":0}\n";
}
