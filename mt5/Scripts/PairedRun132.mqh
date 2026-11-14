#ifndef FXDL_PAIRED_RUN132
#define FXDL_PAIRED_RUN132
// Pure state decisions shared with C++ tests. Native reads and IO stay outside.
struct PairedClock132
{
   long origin_s,last_s;
   ulong origin_us,last_us,last_poll_start_us,reserved_bytes;
   int queries;
   bool pending,ended;
};
bool DateAllowed132(const string date)
{
   return date=="2026.10.19" || date=="2026.10.20" || date=="2026.10.21" ||
          date=="2026.10.22" || date=="2026.10.23";
}
void InitPaired132(PairedClock132 &s,const long seconds,const ulong micros)
{
   s.origin_s=seconds;s.last_s=seconds;s.origin_us=micros;s.last_us=micros;
   s.last_poll_start_us=0;s.reserved_bytes=0;s.queries=0;s.pending=false;s.ended=false;
}
int CheckPairedClock132(PairedClock132 &s,const long seconds,const ulong micros,const string date)
{
   if(s.ended) return 19;
   if(!DateAllowed132(date)) return 11;
   if(s.origin_s<=0 || s.origin_us==0 || seconds<s.last_s || micros<s.last_us || micros<s.origin_us) return 12;
   if(micros-s.origin_us>3600000000) return 13;
   long drift=(seconds-s.origin_s)-(long)((micros-s.origin_us)/1000000);
   if(drift < -2 || drift > 2) return 12;
   s.last_s=seconds;s.last_us=micros;return 0;
}
int NextPairedQuery132(PairedClock132 &s)
{
   if(s.ended || s.pending) return 19;
   if(s.queries<0 || s.queries>=10800) return 20;
   s.queries++;s.pending=true;return 0;
}
int CompletePairedQuery132(PairedClock132 &s)
{
   if(s.ended || !s.pending) return 19;
   s.pending=false;return 0;
}
int WaitState132(const PairedClock132 &s)
{
   if(s.ended || s.pending || s.queries<0 || s.queries%3!=0) return 19;
   if(s.queries>=10800) return 20;
   return 0;
}
bool PollReady132(const PairedClock132 &s,const ulong micros)
{
   return WaitState132(s)==0 && micros>=s.origin_us &&
          (s.queries==0 || (micros>=s.last_poll_start_us && micros-s.last_poll_start_us>=1000000));
}
int MarkPollStart132(PairedClock132 &s,const ulong micros)
{
   if(s.ended || !s.pending || s.queries<1 || s.queries>10798 || (s.queries-1)%3!=0 || micros<s.origin_us) return 19;
   if(s.queries>1 && (micros<s.last_poll_start_us || micros-s.last_poll_start_us<1000000)) return 19;
   s.last_poll_start_us=micros;return 0;
}
int ReservePairedBytes132(PairedClock132 &s,const ulong length)
{
   if(s.ended) return 19;
   if(length==0 || length>2048 || s.reserved_bytes>8388608 || length>8388608-s.reserved_bytes) return 14;
   s.reserved_bytes+=length;return 0; // Reserve before IO; never refund/retry a failed write.
}
void EndPaired132(PairedClock132 &s) {s.ended=true;}
#endif
