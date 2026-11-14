#ifndef FXDL_SYNCHRONIZATION_083
#define FXDL_SYNCHRONIZATION_083
// Pure decisions only. No MQL transport, launch, files, quotes or orders.
int SynchronizationWindow083(const int kind,const long issued,const long deadline,
    const long hold_start,const long hold_end,const long now,
    const long expected_deadline,const long release)
{
   if(kind<1 || kind>4 || issued<0 || deadline<0 || hold_start<0 || hold_end<0 ||
      now<0 || expected_deadline<0 || release<0 || issued>9007199254740991 ||
      deadline>9007199254740991 || hold_start>9007199254740991 ||
      hold_end>9007199254740991 || now>9007199254740991 ||
      expected_deadline>9007199254740991 || release>9007199254740991)return 1;
   if(issued>now || now-issued>2000)return 2;
   if(deadline!=expected_deadline || issued>=deadline || now>=deadline)return 3;
   if(kind==1 || kind==2)return hold_start==0 && hold_end==0 ? 0 : 4;
   if(release<=0 || hold_start<release || hold_start>release+10000 || hold_start>issued)return 4;
   if(kind==3)return hold_end==0 && now<hold_start+29750 ? 0 : 5;
   return hold_end>=hold_start+30000 && hold_end<=hold_start+31000 && hold_end<=issued ? 0 : 6;
}
int SynchronizationControl083(const long start,const long end,const long guard_end,const long hold_start)
{
   if(start<0 || end<0 || guard_end<0 || hold_start<0 || start>9007199254740991 ||
      end>9007199254740991 || guard_end>9007199254740991 || hold_start>9007199254740991)return 1;
   return hold_start>0 && start>hold_start+250 && start<=end && end<=guard_end &&
      guard_end<hold_start+29750 ? 0 : 5;
}
#endif
