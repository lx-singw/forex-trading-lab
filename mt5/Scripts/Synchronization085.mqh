// Pure autonomous-close priority policy. No file/pipe/DLL/account/order calls.
// Future fresh MQL entry point must query this BEFORE any pipe polling.
#ifndef FXDL_SYNCHRONIZATION085_MQH
#define FXDL_SYNCHRONIZATION085_MQH
int CloseAction085(const long now,const long release,const long start)
{
   if(now<0 || release<=0 || start<release || start>9007199254740991LL ||
      release>9007199254740991LL || now>9007199254740991LL ||
      start-release>10000 || now<start) return 3;
   if(now-start<30000) return 0;
   return now-start<=31000 ? 1 : 2;
}
#endif
