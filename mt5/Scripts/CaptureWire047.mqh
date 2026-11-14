#ifndef FXDL_WIRE_047
#define FXDL_WIRE_047
#include "CapturePermit046.mqh"
struct Wire047 { int size; uchar bytes[84]; };
int Hex047(const int c) { if(c>=48 && c<=57) return c-48; if(c>=97 && c<=102) return c-87; return -1; }
bool Binding047(const Wire047 &w,const int offset,const string hex)
{
   for(int i=0;i<StringLen(hex)/2;i++) {
      int a=Hex047(StringGetCharacter(hex,2*i)), b=Hex047(StringGetCharacter(hex,2*i+1));
      if(a<0 || b<0 || w.bytes[offset+i] != a*16+b) return false;
   }
   return true;
}
ulong U64047(const Wire047 &w,const int offset,const int count)
{
   ulong n=0;for(int i=0;i<count;i++)n |= ((ulong)w.bytes[offset+i]) << (8*i);return n;
}
bool Decode047(const Wire047 &w,const string phase,const string digest,const long utc,const long boot,const bool date_ok)
{
   if(w.size!=84 || StringLen(phase)!=32 || StringLen(digest)!=64) return false;
   for(int i=0;i<8;i++)if(w.bytes[i]!=StringGetCharacter("FXDL047R",i))return false;
   if(!Binding047(w,8,phase) || !Binding047(w,24,digest) || U64047(w,56,4)!=1) return false;
   ulong issued=U64047(w,60,8),expires=U64047(w,68,8),expiry=U64047(w,76,8);
   if(issued>9007199254740991 || expires>9007199254740991 || expiry>32535215999999)return false;
   return ReceiptValid046(true,true,date_ok,1,(long)issued,(long)expires,(long)expiry,boot,utc);
}
#endif
