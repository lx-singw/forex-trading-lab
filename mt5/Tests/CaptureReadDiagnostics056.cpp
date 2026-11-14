#include <iostream>
#define FXDL056_PURE_TEST
using ulong = unsigned long;
#include "../Scripts/CaptureReadDiagnostics056.mqh"
int main()
{
   int code; ulong start,end;
   while(std::cin>>code>>start>>end)
      std::cout<<ReadErrorCategory056(code)<<" "<<ReadDuration056(start,end)<<"\n";
}
