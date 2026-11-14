#ifndef FXDL_METADATA_CLOCK127
#define FXDL_METADATA_CLOCK127
// Separate fresh metadata diagnostic. Does not renew107/111/090 runtime dates.
struct MetadataClock127
{
   long origin_s, last_s;
   ulong origin_us, last_us;
   int queries;
};
void InitMetadata127(MetadataClock127 &s,const long seconds,const ulong micros)
{
   s.origin_s=seconds;s.last_s=seconds;s.origin_us=micros;s.last_us=micros;s.queries=0;
}
int CheckClock127(MetadataClock127 &s,const long seconds,const ulong micros,const string date)
{
   if(date!="2026.10.14") return 11;
   if(s.origin_s<=0 || seconds<s.last_s || micros<s.last_us || micros<s.origin_us) return 12;
   if(micros-s.origin_us>60000000) return 13;
   long drift=(seconds-s.origin_s)-(long)((micros-s.origin_us)/1000000);
   if(drift < -2 || drift > 2) return 12;
   s.last_s=seconds;s.last_us=micros;return 0;
}
int NextQuery127(MetadataClock127 &s)
{
   if(s.queries<0 || s.queries>=128) return 20;
   s.queries++;return 0;
}
#endif
