#include <iostream>
#include "../Scripts/SharingHold064.mqh"
int main()
{
   long start,end,elapsed;int iterations,stopped,date_ok;
   while(std::cin>>start>>end>>elapsed>>iterations>>stopped>>date_ok)
      std::cout<<HoldReason064(start,end,elapsed,iterations,stopped!=0,date_ok!=0)<<"\n";
   for(int i=-1;i<=84;i++)std::cout<<SyntheticByte064(i)<<" ";
   std::cout<<"\n";
}
