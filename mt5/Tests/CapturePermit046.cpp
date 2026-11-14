// Synthetic shared MQL receipt predicates; no terminal APIs or quotes.
#include <iostream>
#include <stdexcept>
#include <limits>
#include "../Scripts/CapturePermit046.mqh"
static_assert(sizeof(long)==8,"64-bit MQL long shim required");
int checks=0;
void require(bool b){++checks;if(!b)throw std::runtime_error("receipt_case_failed");}
int main(int argc,char**){
   if(argc==2){
      bool schema,phase,date;int permission;long issued,expires,expiry,now,wall;
      while(std::cin>>schema>>phase>>date>>permission>>issued>>expires>>expiry>>now>>wall)
         std::cout<<ReceiptValid046(schema,phase,date,permission,issued,expires,expiry,now,wall)<<"\n";
      return std::cin.eof()?0:1;
   }
   long utc=1791312961000,boot=100000;
   auto valid=[&](bool schema,bool phase,bool date,int permission,long issued,long expires,long expiry,long now,long wall){
      return ReceiptValid046(schema,phase,date,permission,issued,expires,expiry,now,wall);
   };
   require(valid(true,true,true,1,boot,boot+2000,utc+2000,boot,utc));
   require(valid(true,true,true,1,boot,boot+2000,utc+2000,boot+1999,utc+1999));
   require(!valid(false,true,true,1,boot,boot+2000,utc+2000,boot,utc));
   require(!valid(true,false,true,1,boot,boot+2000,utc+2000,boot,utc));
   require(!valid(true,true,false,1,boot,boot+2000,utc+2000,boot,utc));
   for(int p:{0,2,-1})require(!valid(true,true,true,p,boot,boot+2000,utc+2000,boot,utc));
   require(!valid(true,true,true,1,boot,boot+2000,utc+2000,boot+2000,utc+2000));
   require(!valid(true,true,true,1,boot,boot+2000,utc+2000,boot-1,utc));
   require(!valid(true,true,true,1,boot,boot+2001,utc+2000,boot,utc));
   require(!valid(true,true,true,1,boot,boot,utc+2000,boot,utc));
   require(!valid(true,true,true,1,boot,boot+2000,utc+2001,boot,utc));
   require(!valid(true,true,true,1,boot,boot+2000,utc,boot,utc));
   require(!valid(true,true,true,1,-1,boot+2000,utc+2000,boot,utc));
   require(!valid(true,true,true,1,boot,std::numeric_limits<long>::max(),utc+2000,boot,utc));
   require(!valid(true,true,true,1,boot,boot+2000,std::numeric_limits<long>::max(),boot,utc));
   require(!valid(true,true,true,1,boot,boot+2000,utc+2000,boot,0));
   std::cout<<"{\"receipt_checks\":"<<checks<<",\"passed\":true}\n";
}
