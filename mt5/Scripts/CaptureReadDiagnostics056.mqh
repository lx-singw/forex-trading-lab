#ifndef FXDL_READ_DIAGNOSTICS_056
#define FXDL_READ_DIAGNOSTICS_056
// Closed integer categories: 0 none, 2 invalid handle, 3 not opened for reading,
// 4 nonbinary, 5 read error, 6 other code, 7 unknown. No raw code exported.
int ReadErrorCategory056(const int code)
{
   if(code<0)return 7;
   if(code==0)return 0;
   if(code==5007)return 2;
   if(code==5010)return 3;
   if(code==5011)return 4;
   if(code==5015)return 5;
   return 6;
}
long ReadDuration056(const ulong start,const ulong end)
{
   if(end<start || end-start>900000000)return -1;
   return (long)(end-start);
}
#ifndef FXDL056_PURE_TEST
// Experimental read wrapper only. Not compiled/deployed or permission proof.
// Caller retains the handle through validation and any bounded acknowledgment.
// MQL FileReadArray has no documented caller-specified timeout; this wrapper
// measures its duration. It cannot enforce a deadline while the call blocks.
uint ReadCandidate056(const int handle,uchar &reply[],int &category,long &elapsed)
{
   ArrayResize(reply,84);
   ResetLastError();
   ulong start=GetMicrosecondCount();
   uint count=FileReadArray(handle,reply,0,84);
   int error=GetLastError(); // Before close, print, guard or other file operations.
   ulong end=GetMicrosecondCount();
   category=ReadErrorCategory056(error);
   elapsed=ReadDuration056(start,end);
   return count;
}
#endif
#endif
