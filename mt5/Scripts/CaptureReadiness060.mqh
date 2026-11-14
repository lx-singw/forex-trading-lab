#ifndef FXDL_READINESS_060
#define FXDL_READINESS_060
// Offline candidate only. Not an executable script, acceptance or timeout proof.
int ReadErrorCategory060(const int code)
{
   if(code<0)return 7;
   if(code==0)return 0;
   if(code==5007)return 2;
   if(code==5010)return 3;
   if(code==5011)return 4;
   if(code==5015)return 5;
   if(code>=5001 && code<=5027)return 10+code-5001;
   return 6;
}
#ifndef FXDL060_PURE_TEST
// Article503 suggests availability observation before a read. FileSize is not
// proof of message boundary or future suffix absence. Calls may block internally.
ulong ObserveAvailability060(const int handle,int &category,long &elapsed)
{
   ResetLastError();
   ulong start=GetMicrosecondCount();
   ulong available=FileSize(handle);
   int error=GetLastError();
   ulong end=GetMicrosecondCount();
   category=ReadErrorCategory060(error);
   elapsed=(end<start || end-start>900000000)?-1:(long)(end-start);
   return available;
}
// Integer return is a value, NOT a byte count. Zero is a valid byte; never infer
// readiness from it. Kept only for a future diagnostic comparison, not a reader.
int ObserveByteValue060(const int handle,int &category,long &elapsed)
{
   ResetLastError();
   ulong start=GetMicrosecondCount();
   int value=FileReadInteger(handle,CHAR_VALUE);
   int error=GetLastError();
   ulong end=GetMicrosecondCount();
   category=ReadErrorCategory060(error);
   elapsed=(end<start || end-start>900000000)?-1:(long)(end-start);
   return value;
}
#endif
#endif
