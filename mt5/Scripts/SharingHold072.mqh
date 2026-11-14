#ifndef FXDL_SHARING_HOLD_072
#define FXDL_SHARING_HOLD_072
// Pure decisions only; test shim is not a MetaTrader runtime/compiler.
int HoldReason072(const long start,const long end,const long elapsed,
                  const int iterations,const bool stopped,const bool date_ok)
{
   if(start<=0 || end<start || end>9007199254740991 || elapsed<0)return 19;
   if(stopped)return 18;
   if(!date_ok)return 10;
   if(iterations<1 || iterations>601)return 20;
   if(end-start<30000 || end-start>31000 || elapsed<30000000 || elapsed>31000000)return 21;
   long delta=(end-start)*1000-elapsed;
   if(delta < -1000000 || delta > 1000000)return 19;
   return 0;
}
int SyntheticByte072(const int index)
{
   return index<0 || index>=84 ? -1 : (index*41+23)%256;
}
#endif
