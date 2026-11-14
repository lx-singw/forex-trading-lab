#ifndef FXDL_WIRE_DIAGNOSTICS_053
#define FXDL_WIRE_DIAGNOSTICS_053
#include "CaptureWire047.mqh"
// Pure diagnostics only: no IPC, account, quote or order functions.
int DecodeReason053(const Wire047 &w,const string phase,const string digest,const long utc,const long boot,const bool date_ok)
{
   if(w.size!=84)return 1;
   if(StringLen(phase)!=32 || StringLen(digest)!=64)return 2;
   for(int i=0;i<8;i++)if(w.bytes[i]!=StringGetCharacter("FXDL047R",i))return 3;
   if(!Binding047(w,8,phase))return 4;
   if(!Binding047(w,24,digest))return 5;
   if(U64047(w,56,4)!=1)return 6;
   ulong issued=U64047(w,60,8),expires=U64047(w,68,8),expiry=U64047(w,76,8);
   if(issued>9007199254740991 || expires>9007199254740991 || expiry>32535215999999)return 7;
   if(!date_ok)return 8;
   if(boot<(long)issued)return 9;
   if(boot>=(long)expires)return 10;
   if(boot>9007199254740991 || utc<=0 || utc>32535215999999 || expiry==0)return 11;
   if(expires-issued>2000)return 12;
   if((long)expiry<=utc)return 13;
   if((long)expiry-utc>2000)return 14;
   return 0;
}
#endif
