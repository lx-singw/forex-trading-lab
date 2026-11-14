#include <iostream>
#define FXDL060_PURE_TEST
#define FXDL061_PURE_TEST
#include "../Scripts/CaptureReadiness061.mqh"
int main()
{
   long size,elapsed; int error,attempt;
   while(std::cin>>size>>error>>attempt>>elapsed)
      std::cout<<ReadinessDecision061(size,error,attempt,elapsed)<<"\n";
}
