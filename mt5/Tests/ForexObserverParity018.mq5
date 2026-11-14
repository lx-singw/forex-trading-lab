#property strict
#property version "1.000"
#property description "Synthetic observation diagnostics. No trading or broker API calls."
input string OutputFile="ForexDemoLab\\observer018\\UNCONFIGURED.csv";

bool gConnected,gTickOK,gGuard,gRemoved,gCopyContract;
long gMode,gSwitchMode;
int gQueryError,gError,gSwitchRead,gSwitchError,gReads,gCopyCount,gPositions,gOrders;
int gPhase,gRepeats,gObservations;
string gName,gSymbol,gSide;
ENUM_TIMEFRAMES gPeriod;
datetime gInitClosed,gCurrentOpen;
double gBid,gAsk,gStop;
MqlRates gBars[51];

long H018TerminalInfo(ENUM_TERMINAL_INFO_INTEGER property)
{
   return property==TERMINAL_CONNECTED && gConnected ? 1 : 0;
}
long H018AccountInfo(ENUM_ACCOUNT_INFO_INTEGER property)
{
   gReads++;
   if(property!=ACCOUNT_TRADE_MODE) { gError=4014; return -999; }
   if(gSwitchRead>0 && gReads>=gSwitchRead)
   { gError=gSwitchError; return gSwitchMode; }
   gError=gQueryError;
   return gMode;
}
void H018ResetError() { gError=0; }
int H018GetError() { return gError; }
datetime H018Time(string symbol,ENUM_TIMEFRAMES period,int shift)
{
   if(symbol!=gSymbol || period!=PERIOD_H1) return 0;
   if(shift==1) return gPhase==0 ? gInitClosed : gBars[50].time;
   if(shift==0) return gCurrentOpen;
   return 0;
}
int H018Copy(string symbol,ENUM_TIMEFRAMES period,int shift,int count,MqlRates &bars[])
{
   gCopyContract=gCopyContract && symbol==gSymbol && period==PERIOD_H1 && shift==1 && count==51;
   if(!gCopyContract || gCopyCount<0) return -1;
   ArrayResize(bars,gCopyCount);
   for(int i=0;i<gCopyCount && i<51;i++) bars[i]=gBars[i];
   return gCopyCount;
}
bool H018Quote(string symbol,MqlTick &tick)
{
   if(symbol!=gSymbol || !gTickOK) return false;
   ZeroMemory(tick); tick.bid=gBid; tick.ask=gAsk; return true;
}
int H018Positions() { return gPositions; }
int H018Orders() { return gOrders; }
void H018Remove() { gRemoved=true; }
void H018Print(string message) { /* No journal output or account identifiers. */ }
void H018PrintFormat(string format,string side,string closed,double distance)
{ gObservations++; gSide=side; gStop=distance; }

#define TerminalInfoInteger H018TerminalInfo
#define AccountInfoInteger H018AccountInfo
#define ResetLastError H018ResetError
#define GetLastError H018GetError
#define iTime H018Time
#define CopyRates H018Copy
#define SymbolInfoTick H018Quote
#define PositionsTotal H018Positions
#define OrdersTotal H018Orders
#define ExpertRemove H018Remove
#define Print H018Print
#define PrintFormat H018PrintFormat
#define _Symbol gSymbol
#define _Period gPeriod
#define OnInit Observer018Init
#define OnTick Observer018Tick
#include "OriginalObserver018.mqh"
#undef TerminalInfoInteger
#undef AccountInfoInteger
#undef ResetLastError
#undef GetLastError
#undef iTime
#undef CopyRates
#undef SymbolInfoTick
#undef PositionsTotal
#undef OrdersTotal
#undef ExpertRemove
#undef Print
#undef PrintFormat
#undef _Symbol
#undef _Period
#undef OnInit
#undef OnTick
#include "Fixtures018.mqh"

int OnInit()
{
   string prefix="ForexDemoLab\\observer018\\";
   if(StringFind(OutputFile,prefix)!=0 || StringFind(OutputFile,"..")>=0 ||
      StringFind(OutputFile,"UNCONFIGURED")>=0 || FileIsExist(OutputFile,FILE_COMMON))
      return INIT_PARAMETERS_INCORRECT;
   return INIT_SUCCEEDED;
}
double OnTester()
{
   if(FileIsExist(OutputFile,FILE_COMMON)) return -1;
   int handle=FileOpen(OutputFile,FILE_WRITE|FILE_CSV|FILE_ANSI|FILE_COMMON,',');
   if(handle==INVALID_HANDLE) return -1;
   FileWrite(handle,"case_id","kind","init","observations","side","stop","removed",
             "account_reads","last_closed","copy_contract");
   for(int index=0;index<CASES018;index++)
   {
      gReads=0; gPhase=0; gObservations=0; gRemoved=false; gCopyContract=true;
      gSide=""; gStop=0; last_closed=0;
      Load018(index);
      int init=-99;
      if(gGuard) gObservations=IsDemoAccount() ? 1 : 0;
      else
      {
         init=Observer018Init(); gPhase=1;
         if(init==INIT_SUCCEEDED)
            for(int repeat=0;repeat<gRepeats && !gRemoved;repeat++) Observer018Tick();
      }
      FileWrite(handle,gName,gGuard ? "guard" : "observation",init,gObservations,gSide,
                DoubleToString(gStop,16),(int)gRemoved,gReads,(long)last_closed,(int)gCopyContract);
   }
   FileFlush(handle); FileClose(handle);
   return CASES018;
}
