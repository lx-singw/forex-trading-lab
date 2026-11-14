#include <iostream>
#include "../Scripts/SharingHold072.mqh"
int main()
{
   long start,end,elapsed;int iterations,stopped,date_ok;
   while(std::cin>>start>>end>>elapsed>>iterations>>stopped>>date_ok)
      std::cout<<HoldReason072(start,end,elapsed,iterations,stopped!=0,date_ok!=0)<<"\n";
   for(int i=-1;i<=84;i++)std::cout<<SyntheticByte072(i)<<" ";
   std::cout<<"\n";
}
