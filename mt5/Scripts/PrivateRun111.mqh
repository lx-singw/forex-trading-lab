#ifndef FXDL_PRIVATE_RUN111
#define FXDL_PRIVATE_RUN111

struct Run111 {
   long origin_s,last_s;
   ulong origin_us,last_read_us,last_guard_us,bytes;
   int attempts,observed,segments,segment_attempts,fault;
   bool pending,ended;
};
void Init111(Run111 &s,const long seconds,const ulong micros)
{
   s.origin_s=seconds;s.last_s=seconds;s.origin_us=micros;s.last_guard_us=micros;
   s.last_read_us=0;s.bytes=0;s.attempts=0;s.observed=0;s.segments=0;
   s.segment_attempts=0;s.fault=0;s.pending=false;s.ended=false;
}
int Clock111(const Run111 &s,const long seconds,const ulong micros,const string date)
{
   if(s.ended) return 19;
   if(date!="2026.10.12") return 11;
   if(s.origin_s<=0 || s.origin_us==0 || seconds<s.last_s || micros<s.last_guard_us ||
      seconds<s.origin_s || micros<s.origin_us) return 12;
   ulong elapsed=micros-s.origin_us;
   if(elapsed>3600000000) return 13;
   long drift=(seconds-s.origin_s)-(long)(elapsed/1000000);
   if(drift < -2 || drift > 2) return 12;
   return 0;
}
int Wait111(const Run111 &s,const ulong now,bool &ready,int &pause_ms)
{
   ready=false;pause_ms=0;
   if(s.ended || s.fault!=0 || s.pending) return 19;
   if(now<s.origin_us || now<s.last_guard_us || (s.last_read_us!=0 && now<s.last_read_us)) return 12;
   if(now-s.origin_us>3600000000) return 13;
   if(s.last_read_us==0 || now-s.last_read_us>=500000) { ready=true;return 0; }
   ulong remaining=500000-(now-s.last_read_us);
   if(remaining>25000) {
      ulong milliseconds=(remaining-25000)/1000;
      pause_ms=(int)(milliseconds>20?20:milliseconds);
   }
   return 0;
}
int Segment111(Run111 &s)
{
   if(s.ended || s.fault!=0 || s.pending ||
      (s.segments!=0 && s.segment_attempts!=120)) return 19;
   if(s.segments>=64 || s.attempts>=7200) return 20;
   s.segments++;s.segment_attempts=0;return 0;
}
int Attempt111(Run111 &s)
{
   if(s.ended || s.fault!=0 || s.pending || s.segments==0 || s.segment_attempts>=120) return 19;
   if(s.attempts>=7200) return 20;
   s.attempts++;s.segment_attempts++;s.pending=true;return 0;
}
int Receipt111(Run111 &s,const long bs,const long ats,const long gs,
               const ulong bu,const ulong au,const ulong gu,const string date)
{
   if(!s.pending || s.ended || s.fault!=0) return 19;
   if(bs>ats || ats>gs || bu>au || au>gu) return 12;
   int reason=Clock111(s,bs,bu,date);
   if(reason==0) reason=Clock111(s,ats,au,date);
   if(reason==0) reason=Clock111(s,gs,gu,date);
   if(reason!=0) return reason;
   if(s.last_read_us!=0 && (bu<s.last_read_us || bu-s.last_read_us<500000)) return 12;
   s.last_read_us=bu;s.last_guard_us=gu;s.last_s=gs;return 0;
}
int Outcome111(Run111 &s,const int quote_reason)
{
   if(s.ended || s.fault!=0 || !s.pending) return 19;
   if(quote_reason!=0 && quote_reason!=15 && quote_reason!=16) return 19;
   s.pending=false;
   if(quote_reason==0) s.observed++;else s.fault=quote_reason;
   return 0;
}
int Reserve111(Run111 &s,const ulong length,const ulong segment_bytes)
{
   if(s.ended) return 19;
   if(length==0 || length>2048 || segment_bytes>262144 || length>262144-segment_bytes ||
      s.bytes>4194304 || length>4194304-s.bytes) return 14;
   s.bytes+=length;return 0; // Reserve before IO. No refund/retry on a failed write.
}
void End111(Run111 &s) { s.ended=true; }
#endif
