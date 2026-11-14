#include <string>
#include <iostream>
#include <cassert>
using string=std::string;
using ulong=unsigned long;
static_assert(sizeof(long)==8 && sizeof(ulong)==8,"64-bit shim required");
#include "../Scripts/CostBounds128.mqh"
int main()
{
   int checks=0;
   auto check=[&](bool value){assert(value);++checks;};
   CostClock128 s;
   InitCost128(s,1791996000,1000);
   check(CheckCostClock128(s,1791996000,1000,"2026.10.14")==0);
   for(int i=0;i<5;i++) check(NextCostQuery128(s)==0);
   check(NextCostQuery128(s)==20 && s.queries==5);
   check(CheckCostClock128(s,1791996000,1001,"2026.10.15")==11);
   check(CheckCostClock128(s,1791995999,1002,"2026.10.14")==12);
   check(CheckCostClock128(s,1791996000,999,"2026.10.14")==12);
   check(CheckCostClock128(s,1791996003,1002,"2026.10.14")==12);
   check(CheckCostClock128(s,1791996060,60001000,"2026.10.14")==0);
   check(CheckCostClock128(s,1791996060,60001001,"2026.10.14")==13);
   InitCost128(s,0,1000);
   check(CheckCostClock128(s,1,1001,"2026.10.14")==12);
   InitCost128(s,1791996000,1000);s.queries=-1;
   check(NextCostQuery128(s)==20);
   for(int n=0;n<=8;n++) {
      check(CostRuleCountReason128(n,n)==0);
      check(CostRuleCountReason128(n,n+1)==16);
   }
   check(CostRuleCountReason128(-1,0)==16);
   check(CostRuleCountReason128(9,9)==21);
   check(CostRuleCountReason128(2147483647,2147483647)==21);
   for(int count=0;count<=16;count++) {
      check(CostTierCountReason128(count,0)==0);
      check(CostTierCountReason128(count,128-count)==0);
      check(CostTierCountReason128(count,129-count)==22);
   }
   check(CostTierCountReason128(-1,0)==16);
   check(CostTierCountReason128(0,-1)==16);
   check(CostTierCountReason128(17,0)==22);
   check(CostTierCountReason128(1,2147483647)==22);
   check(CostTierCountReason128(2147483647,0)==22);
   std::cout<<"{\"checks\":"<<checks<<",\"passed\":true}\n";
}
