#ifndef FXDL_SYNCHRONIZATION_WIRE_084
#define FXDL_SYNCHRONIZATION_WIRE_084
#include "Synchronization083.mqh"
// Pure byte codec. FXDL084_CPP is used only by the portable test harness.
#ifdef FXDL084_CPP
#define FXDL084_IN const uchar *
#define FXDL084_OUT uchar *
#else
#define FXDL084_IN const uchar &
#define FXDL084_OUT uchar &
#endif
struct Wire084
{
   int kind,sequence;
   long issued,deadline,start,end;
};
#ifdef FXDL084_CPP
long Number084(const uchar *raw,const int offset,const int count)
#else
long Number084(const uchar &raw[],const int offset,const int count)
#endif
{
   long value=0;
   for(int i=0;i<count;i++)value|=((long)raw[offset+i])<<(8*i);
   return value;
}
#ifdef FXDL084_CPP
void Put084(uchar *raw,const int offset,const int count,const long value)
#else
void Put084(uchar &raw[],const int offset,const int count,const long value)
#endif
{
   for(int i=0;i<count;i++)raw[offset+i]=(uchar)((value>>(8*i))&255);
}
#ifdef FXDL084_CPP
void EncodeWire084(uchar *raw,const uchar *prefix,const Wire084 &s)
#else
void EncodeWire084(uchar &raw[],const uchar &prefix[],const Wire084 &s)
#endif
{
   for(int i=0;i<144;i++)raw[i]=0;
   for(int i=0;i<104;i++)raw[i]=prefix[i];
   Put084(raw,104,4,s.sequence);raw[108]=(uchar)s.kind;
   Put084(raw,112,8,s.issued);Put084(raw,120,8,s.deadline);
   Put084(raw,128,8,s.start);Put084(raw,136,8,s.end);
}
#ifdef FXDL084_CPP
int DecodeWire084(const uchar *raw,const int size,const uchar *prefix,
#else
int DecodeWire084(const uchar &raw[],const int size,const uchar &prefix[],
#endif
   const int kind,const int sequence,const long now,const long deadline,
   const long release,const long request_completed,Wire084 &s,const bool request=false)
{
   if(size!=144 || sequence<1 || sequence>64 || kind<1 || kind>4)return 1;
   for(int i=0;i<104;i++)if(raw[i]!=prefix[i])return 1;
   if(raw[109]!=0 || raw[110]!=0 || raw[111]!=0)return 1;
   s.sequence=(int)Number084(raw,104,4);s.kind=(int)raw[108];
   s.issued=Number084(raw,112,8);s.deadline=Number084(raw,120,8);
   s.start=Number084(raw,128,8);s.end=Number084(raw,136,8);
   if(s.sequence!=sequence || !(s.kind==kind || (!request && s.kind==5 && (kind==3 || kind==4))))return 1;
   if(request && s.kind==5)return 1;
   int code=SynchronizationWindow083(request || s.kind==5?1:s.kind,s.issued,s.deadline,s.start,s.end,now,deadline,release);
   if(code!=0)return code;
   if(request_completed>=0 && (request_completed>9007199254740991 || s.issued<request_completed))return 2;
   return 0;
}
#endif
