#include <iostream>
#include <string>
using string=std::string;using uchar=unsigned char;using ulong=unsigned long;
int StringLen(const string&s){return (int)s.size();}
int StringGetCharacter(const string&s,int i){return (unsigned char)s[i];}
#include "../Scripts/CaptureWire047.mqh"
static_assert(sizeof(long)==8 && sizeof(ulong)==8,"64-bit MQL shim required");
int main(){long utc,boot;string hex;while(std::cin>>utc>>boot>>hex){
   Wire047 w{};w.size=hex=="-"?0:(int)hex.size()/2;
   for(int i=0;i<w.size && i<84;i++)w.bytes[i]=(uchar)std::stoul(hex.substr(i*2,2),nullptr,16);
   std::cout<<Decode047(w,"51000000000000000000000000000001","5151515151515151515151515151515151515151515151515151515151515151",utc,boot,true)<<"\n";
}}
