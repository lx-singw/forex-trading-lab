#ifndef FXDL_RECORDER_PORT156
#define FXDL_RECORDER_PORT156
// Shared pure decisions. No native APIs, IO, permissions or account identifiers.
struct PortState156
{
   ulong origin,last,reserved,queries,requests;
   bool pending,ended;
};
struct LeaseState156
{
   ulong sequence,tick,owner,observed,flags;
   bool seen;
};
void InitPort156(PortState156 &s,const ulong now)
{
   s.origin=now;s.last=now;s.reserved=0;s.queries=0;s.requests=0;s.pending=false;s.ended=false;
}
void InitLease156(LeaseState156 &s)
{
   s.sequence=0;s.tick=0;s.owner=0;s.observed=0;s.flags=0;s.seen=false;
}
int PortClock156(PortState156 &s,const ulong now)
{
   if(s.ended) return 106;
   if(now<s.last || now<s.origin) {s.ended=true;return 103;}
   if(now-s.origin>=30000000) {s.ended=true;return 104;}
   s.last=now;return 0;
}
int ReservePort156(PortState156 &s,const ulong bytes)
{
   if(s.ended || bytes==0 || bytes>4096 || s.reserved>1048576 || bytes>1048576-s.reserved)
   {s.ended=true;return 107;}
   s.reserved+=bytes;return 0;
}
int BeginQuery156(PortState156 &s)
{
   if(s.ended || s.pending) return 106;
   if(s.queries>=128) {s.ended=true;return 108;}
   s.queries++;s.pending=true;return 0;
}
int CompleteQuery156(PortState156 &s)
{
   if(s.ended || !s.pending) return 106;
   s.pending=false;return 0;
}
int NewRequest156(PortState156 &s)
{
   if(s.ended || s.requests>=512) {s.ended=true;return 108;}
   s.requests++;return 0;
}
int AcceptLease156(LeaseState156 &s,const ulong sent,const ulong now,const ulong sequence,
                   const ulong tick,const ulong owner,const ulong flags)
{
   if(now<sent || now-sent>1000000 || sequence==0 || tick>owner || flags!=255) return 105;
   ulong age=owner-tick;
   if(age>1000 || sent<age*1000) return 105;
   ulong observed=sent-age*1000;
   if(s.seen)
   {
      if(sequence<s.sequence || tick<s.tick || owner<s.owner) return 106;
      if(sequence==s.sequence)
      {
         if(tick!=s.tick || flags!=s.flags) return 106;
         observed=s.observed; // A repeated sample never acquires a fresh local timestamp.
      }
      else if(observed<s.observed) return 106;
   }
   if(now<observed || now-observed>1000000) return 105;
   s.sequence=sequence;s.tick=tick;s.owner=owner;s.observed=observed;s.flags=flags;s.seen=true;
   return 0;
}
int LeaseFresh156(const LeaseState156 &s,const ulong now)
{
   return !s.seen || now<s.observed || now-s.observed>1000000 ? 105:0;
}
#endif
