#include <string>
#include <iostream>
#include <cstdlib>
using string=std::string;
using ulong=unsigned long;
static_assert(sizeof(long)==8 && sizeof(ulong)==8,"Native decision widths");
#include "../Scripts/TimingRun130.mqh"
int checks=0;
void expect(bool ok) {++checks;if(!ok) {std::cerr<<"timing check "<<checks<<" failed\n";std::exit(1);}}
int main()
{
   TimingClock130 s;InitTiming130(s,100,1000);
   expect(PollReady130(s,1000));expect(CheckTimingClock130(s,100,1000,"2026.10.15")==0);
   expect(MarkPollStart130(s,1000)==19);
   for(int poll=0;poll<60;poll++)
   {
      ulong start=1000+(ulong)poll*1000000;
      if(poll) {expect(!PollReady130(s,start-1));expect(PollReady130(s,start));}
      expect(NextTimingQuery130(s)==0);expect(MarkPollStart130(s,start)==0);
      expect(CheckTimingClock130(s,100+poll,start,"2026.10.15")==0);
      expect(NextTimingQuery130(s)==0);expect(MarkPollStart130(s,start)==19);
      expect(NextTimingQuery130(s)==0);
   }
   expect(s.queries==180);expect(NextTimingQuery130(s)==20);
   InitTiming130(s,100,1000);expect(NextTimingQuery130(s)==0);expect(MarkPollStart130(s,1000)==0);
   expect(NextTimingQuery130(s)==0);expect(NextTimingQuery130(s)==0);expect(NextTimingQuery130(s)==0);
   expect(MarkPollStart130(s,1000999)==19);expect(s.last_poll_start_us==1000);
   expect(MarkPollStart130(s,3001000)==0);expect(!PollReady130(s,3001001)); // Delay does not catch up.
   expect(!PollReady130(s,3000999));expect(PollReady130(s,4001000));
   InitTiming130(s,100,1000);expect(CheckTimingClock130(s,160,60001000,"2026.10.15")==0);
   expect(CheckTimingClock130(s,160,60001001,"2026.10.15")==13);
   InitTiming130(s,100,1000);expect(CheckTimingClock130(s,100,1000,"2026.10.14")==11);
   expect(CheckTimingClock130(s,100,1000,"2026.10.16")==11);
   expect(CheckTimingClock130(s,99,1000,"2026.10.15")==12);
   expect(CheckTimingClock130(s,100,999,"2026.10.15")==12);
   expect(CheckTimingClock130(s,103,1000,"2026.10.15")==12);
   expect(CheckTimingClock130(s,100,3001000,"2026.10.15")==12);
   expect(CheckTimingClock130(s,102,1000,"2026.10.15")==0);
   expect(CheckTimingClock130(s,101,2000,"2026.10.15")==12);
   InitTiming130(s,0,0);expect(CheckTimingClock130(s,0,0,"2026.10.15")==12);
   InitTiming130(s,100,1000);s.queries=-1;expect(NextTimingQuery130(s)==20);
   std::cout<<checks<<" timing boundary and schedule checks passed\n";
}
