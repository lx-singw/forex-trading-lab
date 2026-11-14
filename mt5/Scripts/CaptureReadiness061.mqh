#ifndef FXDL_READINESS_061
#define FXDL_READINESS_061
#include "CaptureReadiness060.mqh"
// Pure diagnostic decisions; a read candidate is NEVER message-boundary proof.
int ReadinessDecision061(const long size,const int error,const int attempt,const long elapsed)
{
   if(size<0 || error<0 || attempt<1 || elapsed<0)return 4;
   if(error!=0)return 2;
   if(elapsed>=900000000)return 5;
   if(attempt>901)return 6;
   if(size>84)return 3;
   return size==84?1:0;
}
#ifndef FXDL061_PURE_TEST
// One uncompiled observation; a future caller must cap attempts at901, check
// session clocks and full account/identity guards and wait only between calls.
// Does not read/accept a receipt, ACK, flush, close, or promise call interruption.
int ObserveReadiness061(const int handle,const int attempt,const ulong started,
                        int &category,long &call_elapsed,long &session_elapsed)
{
   ResetLastError();
   ulong call_start=GetMicrosecondCount();
   ulong size=FileSize(handle);
   int error=GetLastError();
   ulong end=GetMicrosecondCount();
   category=ReadErrorCategory060(error);
   call_elapsed=(end<call_start || end-call_start>900000000)?-1:(long)(end-call_start);
   session_elapsed=(end<started || end-started>900000000)?-1:(long)(end-started);
   if(call_elapsed<0 || session_elapsed<0 || size>2147483647)return 4;
   return ReadinessDecision061((long)size,error,attempt,session_elapsed);
}
#endif
#endif
