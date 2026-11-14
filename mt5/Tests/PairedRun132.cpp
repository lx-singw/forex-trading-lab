#include <string>
#include <iostream>
#include <cstdlib>
using string=std::string;
using ulong=unsigned long;
const long ACCOUNT_TRADE_MODE_DEMO=0;
static_assert(sizeof(long)==8 && sizeof(ulong)==8,"Native decision widths");
#include "../Scripts/PrivateGuard107.mqh"
#include "../Scripts/PairedRun132.mqh"
int checks=0;
void expect(bool ok) {++checks;if(!ok) {std::cerr<<"paired check "<<checks<<" failed\n";std::exit(1);}}
PrivateAccount107 account()
{
   PrivateAccount107 a;a.query_ok=true;a.connected=true;a.algo=false;a.tester=false;a.visible=true;
   a.mode=ACCOUNT_TRADE_MODE_DEMO;a.login=123;a.server="invented";a.currency="USD";
   a.symbol="EURUSD";a.base="EUR";a.quote="USD";return a;
}
int main()
{
   PairedClock132 s;InitPaired132(s,100,1000);
   expect(ReservePairedBytes132(s,100)==0);
   for(int poll=0;poll<3600;poll++)
   {
      ulong start=1000+(ulong)poll*1000000;
      expect(WaitState132(s)==0);expect(PollReady132(s,start));
      if(poll) expect(!PollReady132(s,start-1));
      for(int part=0;part<3;part++)
      {
         expect(NextPairedQuery132(s)==0);expect(NextPairedQuery132(s)==19);
         expect(WaitState132(s)==19);expect(!PollReady132(s,start));
         expect(CheckPairedClock132(s,100+poll,start+(ulong)part*100,"2026.10.19")==0);
         expect(MarkPollStart132(s,start)==(part==0?0:19));
         expect(ReservePairedBytes132(s,100)==0);expect(ReservePairedBytes132(s,500)==0);
         expect(CompletePairedQuery132(s)==0);expect(CompletePairedQuery132(s)==19);
      }
   }
   expect(s.queries==10800);expect(NextPairedQuery132(s)==20);expect(WaitState132(s)==20);
   expect(ReservePairedBytes132(s,100)==0);EndPaired132(s);
   expect(NextPairedQuery132(s)==19);expect(CompletePairedQuery132(s)==19);
   expect(ReservePairedBytes132(s,1)==19);expect(MarkPollStart132(s,s.last_us)==19);
   expect(CheckPairedClock132(s,s.last_s,s.last_us,"2026.10.19")==19);
   expect(!PollReady132(s,s.last_us));

   const string dates[]={"2026.10.19","2026.10.20","2026.10.21","2026.10.22","2026.10.23"};
   for(const string &date:dates) {InitPaired132(s,100,1000);expect(CheckPairedClock132(s,100,1000,date)==0);}
   for(const string &date:{string("2026.10.18"),string("2026.10.24"),string("2026.11.01")})
      {InitPaired132(s,100,1000);expect(CheckPairedClock132(s,100,1000,date)==11);}
   InitPaired132(s,100,1000);expect(CheckPairedClock132(s,101,1001000,"2026.10.20")==0);
   expect(CheckPairedClock132(s,102,2001000,"2026.10.24")==11);
   InitPaired132(s,100,1000);expect(CheckPairedClock132(s,3700,3600001000,"2026.10.19")==0);
   expect(CheckPairedClock132(s,3700,3600001001,"2026.10.19")==13);
   InitPaired132(s,100,1000);expect(CheckPairedClock132(s,99,1000,"2026.10.19")==12);
   expect(CheckPairedClock132(s,100,999,"2026.10.19")==12);
   expect(CheckPairedClock132(s,103,1000,"2026.10.19")==12);
   expect(CheckPairedClock132(s,100,3001000,"2026.10.19")==12);
   expect(CheckPairedClock132(s,102,1000,"2026.10.19")==0);
   expect(CheckPairedClock132(s,101,2000,"2026.10.19")==12);
   InitPaired132(s,100,0);expect(CheckPairedClock132(s,100,1000,"2026.10.19")==12);

   InitPaired132(s,100,1000);expect(CompletePairedQuery132(s)==19);expect(MarkPollStart132(s,1000)==19);
   expect(NextPairedQuery132(s)==0);expect(MarkPollStart132(s,1000)==0);
   expect(CompletePairedQuery132(s)==0);expect(WaitState132(s)==19);
   for(int i=0;i<2;i++) {expect(NextPairedQuery132(s)==0);expect(CompletePairedQuery132(s)==0);}
   expect(NextPairedQuery132(s)==0);expect(MarkPollStart132(s,1000999)==19);
   expect(s.last_poll_start_us==1000);expect(MarkPollStart132(s,3001000)==0);
   expect(CompletePairedQuery132(s)==0);
   for(int i=0;i<2;i++) {expect(NextPairedQuery132(s)==0);expect(CompletePairedQuery132(s)==0);}
   expect(!PollReady132(s,3001001));expect(!PollReady132(s,3000999));expect(PollReady132(s,4001000));
   InitPaired132(s,100,1000);expect(ReservePairedBytes132(s,0)==14);expect(ReservePairedBytes132(s,2049)==14);
   s.reserved_bytes=8388607;expect(ReservePairedBytes132(s,1)==0);expect(ReservePairedBytes132(s,1)==14);
   expect(s.reserved_bytes==8388608);s.reserved_bytes=(ulong)-1;expect(ReservePairedBytes132(s,1)==14);
   InitPaired132(s,100,1000);expect(ReservePairedBytes132(s,200)==0);
   EndPaired132(s);expect(s.reserved_bytes==200);expect(ReservePairedBytes132(s,200)==19); // Failed IO has no refund/retry.

   const int expected[]={2,3,4,5,5,6,7,8,8,9,10,10};
   for(int fault=0;fault<12;fault++) for(int phase=0;phase<3;phase++) for(int after=0;after<2;after++)
   {
      PrivateAccount107 a=account();
      switch(fault) {
         case 0:a.query_ok=false;break;case 1:a.connected=false;break;case 2:a.tester=true;break;
         case 3:a.mode=1;break;case 4:a.mode=2;break;case 5:a.currency="EUR";break;
         case 6:a.algo=true;break;case 7:a.login=0;break;case 8:a.server="";break;
         case 9:a.login=456;break;case 10:a.symbol="GBPUSD";break;case 11:a.visible=false;break;
      }
      InitPaired132(s,100,1000);int recorded=0;
      for(int i=0;i<phase;i++) {expect(NextPairedQuery132(s)==0);expect(CompletePairedQuery132(s)==0);recorded++;}
      if(after) expect(NextPairedQuery132(s)==0);
      expect(GuardReason107(a,true,123,"invented")==expected[fault]);
      // Runtime must stop before recording the failed group's value.
      EndPaired132(s);expect(recorded==phase);expect(s.pending==(after!=0));
      expect(NextPairedQuery132(s)==19);expect(CompletePairedQuery132(s)==19);
   }
   InitPaired132(s,100,1000);expect(s.queries==0 && !s.pending && !s.ended && s.reserved_bytes==0);
   std::cout<<"{\"passed\":true,\"checks\":"<<checks<<",\"polls\":3600,\"guard_fault_paths\":72,\"native_calls\":0}\n";
}
