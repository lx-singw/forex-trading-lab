#ifndef FXDL_TIMING_RUN130
#define FXDL_TIMING_RUN130
// Pure decisions shared with C++ tests; no renewed authority for old probes.
struct TimingClock130
{
   long origin_s,last_s;
   ulong origin_us,last_us,last_poll_start_us;
   int queries;
};
void InitTiming130(TimingClock130 &s,const long seconds,const ulong micros)
{
   s.origin_s=seconds;s.last_s=seconds;s.origin_us=micros;s.last_us=micros;
   s.last_poll_start_us=0;s.queries=0;
}
int CheckTimingClock130(TimingClock130 &s,const long seconds,const ulong micros,const string date)
{
   if(date!="2026.10.15") return 11;
   if(s.origin_s<=0 || seconds<s.last_s || micros<s.last_us || micros<s.origin_us) return 12;
   if(micros-s.origin_us>60000000) return 13;
   long drift=(seconds-s.origin_s)-(long)((micros-s.origin_us)/1000000);
   if(drift < -2 || drift > 2) return 12;
   s.last_s=seconds;s.last_us=micros;return 0;
}
int NextTimingQuery130(TimingClock130 &s)
{
   if(s.queries<0 || s.queries>=180) return 20;
   s.queries++;return 0;
}
bool PollReady130(const TimingClock130 &s,const ulong micros)
{
   return s.queries==0 || (micros>=s.last_poll_start_us && micros-s.last_poll_start_us>=1000000);
}
int MarkPollStart130(TimingClock130 &s,const ulong micros)
{
   if(s.queries<1 || s.queries>178 || (s.queries-1)%3!=0 || micros<s.origin_us) return 19;
   if(s.queries>1 && (micros<s.last_poll_start_us || micros-s.last_poll_start_us<1000000)) return 19;
   s.last_poll_start_us=micros;return 0;
}
#endif
