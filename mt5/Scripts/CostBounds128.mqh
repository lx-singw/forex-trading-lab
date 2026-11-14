#ifndef FXDL_COST_BOUNDS128
#define FXDL_COST_BOUNDS128
// Separate fresh private diagnostic; no old runtime date is renewed.
struct CostClock128
{
   long origin_s,last_s;
   ulong origin_us,last_us;
   int queries;
};
void InitCost128(CostClock128 &s,const long seconds,const ulong micros)
{
   s.origin_s=seconds;s.last_s=seconds;s.origin_us=micros;s.last_us=micros;s.queries=0;
}
int CheckCostClock128(CostClock128 &s,const long seconds,const ulong micros,const string date)
{
   if(date!="2026.10.14") return 11;
   if(s.origin_s<=0 || seconds<s.last_s || micros<s.last_us || micros<s.origin_us) return 12;
   if(micros-s.origin_us>60000000) return 13;
   long drift=(seconds-s.origin_s)-(long)((micros-s.origin_us)/1000000);
   if(drift < -2 || drift > 2) return 12;
   s.last_s=seconds;s.last_us=micros;return 0;
}
int NextCostQuery128(CostClock128 &s)
{
   if(s.queries<0 || s.queries>=5) return 20;
   s.queries++;return 0;
}
int CostRuleCountReason128(const int count,const int array_size)
{
   if(count<0 || array_size!=count) return 16;
   if(count>8) return 21;
   return 0;
}
int CostTierCountReason128(const int count,const int previous_total)
{
   if(count<0 || previous_total<0) return 16;
   if(count>16 || previous_total>128 || count>128-previous_total) return 22;
   return 0;
}
#endif
