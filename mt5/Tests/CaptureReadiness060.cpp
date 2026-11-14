#include <iostream>
#define FXDL060_PURE_TEST
#include "../Scripts/CaptureReadiness060.mqh"
int main()
{
   int code;
   while(std::cin>>code)std::cout<<ReadErrorCategory060(code)<<"\n";
}
