#include <cassert>
#include <string>
#include <iostream>
using ulong = unsigned long;
using string = std::string;
const long ACCOUNT_TRADE_MODE_DEMO=0;
#include "../mt5/Scripts/RecorderPort156.mqh"
#include "../mt5/Scripts/PrivateGuard107.mqh"
#include "../mt5/Scripts/RunPermit156.mqh"

int main(int argc,char **argv) {
    assert(argc==2);string test=argv[1];
    PortState156 p;InitPort156(p,2000000);LeaseState156 s;InitLease156(s);
    if(test=="authority") {assert(!RunGranted156());}
    else if(test=="account") {
        PrivateAccount107 a{true,true,false,false,true,ACCOUNT_TRADE_MODE_DEMO,17,"invented","USD","EURUSD","EUR","USD"};
        assert(GuardReason107(a,true,17,"invented")==0);
        for(long mode: {1L,2L,3L,-1L}) {a.mode=mode;assert(GuardReason107(a,true,17,"invented")==5);}
        a.mode=ACCOUNT_TRADE_MODE_DEMO;a.server="changed";assert(GuardReason107(a,true,17,"invented")==9);
        a.server="invented";a.login=18;assert(GuardReason107(a,true,17,"invented")==9);
        a.login=17;a.algo=true;assert(GuardReason107(a,true,17,"invented")==7);
        a.algo=false;a.connected=false;assert(GuardReason107(a,true,17,"invented")==3);
        a.connected=true;a.query_ok=false;assert(GuardReason107(a,true,17,"invented")==2);
        a.query_ok=true;a.tester=true;assert(GuardReason107(a,true,17,"invented")==4);
    }
    else if(test=="deadline") {
        assert(PortClock156(p,31999999)==0);assert(PortClock156(p,32000000)==104);
        assert(PortClock156(p,31999999)==106);
        InitPort156(p,10);assert(PortClock156(p,9)==103);
    }
    else if(test=="storage") {
        for(int i=0;i<256;i++) assert(ReservePort156(p,4096)==0);
        assert(p.reserved==1048576);assert(ReservePort156(p,1)==107);assert(ReservePort156(p,1)==107);
        InitPort156(p,0);assert(ReservePort156(p,4097)==107);
        InitPort156(p,0);assert(ReservePort156(p,0)==107);
    }
    else if(test=="query") {
        assert(CompleteQuery156(p)==106);
        for(int i=0;i<128;i++) {assert(BeginQuery156(p)==0);assert(BeginQuery156(p)==106);assert(CompleteQuery156(p)==0);}
        assert(BeginQuery156(p)==108);assert(CompleteQuery156(p)==106);
        InitPort156(p,0);for(int i=0;i<512;i++) assert(NewRequest156(p)==0);assert(NewRequest156(p)==108);
    }
    else if(test=="freshness") {
        assert(LeaseFresh156(s,2000000)==105);
        assert(AcceptLease156(s,2000000,2030000,1,100,120,255)==0);assert(s.observed==1980000);
        assert(LeaseFresh156(s,2980000)==0);assert(LeaseFresh156(s,2980001)==105);
        assert(AcceptLease156(s,2500000,2510000,1,100,620,255)==0);assert(s.observed==1980000);
        assert(AcceptLease156(s,3000000,3010000,1,100,1120,255)==105);
    }
    else if(test=="replay") {
        assert(AcceptLease156(s,2000000,2010000,1,100,120,255)==0);
        assert(AcceptLease156(s,2100000,2110000,1,101,121,255)==106);
        assert(AcceptLease156(s,2250000,2260000,2,350,360,255)==0);
        assert(AcceptLease156(s,2300000,2310000,1,350,360,255)==106);
        assert(AcceptLease156(s,2300000,2310000,3,349,360,255)==106);
        assert(AcceptLease156(s,2300000,2310000,3,350,359,255)==106);
    }
    else if(test=="health") {
        for(ulong bit=1;bit<=128;bit*=2) assert(AcceptLease156(s,2000000,2010000,1,100,120,255^bit)==105);
        assert(AcceptLease156(s,2000000,2010000,1,121,120,255)==105);
        assert(AcceptLease156(s,2000000,1999999,1,100,120,255)==105);
        assert(AcceptLease156(s,2000000,3000001,1,100,120,255)==105);
        assert(AcceptLease156(s,0,1,1,100,120,255)==105);
        assert(AcceptLease156(s,2000000,2010000,0,100,120,255)==105);
    }
    else if(test=="restart") {
        assert(AcceptLease156(s,2000000,2010000,1,100,120,255)==0);
        InitLease156(s);assert(LeaseFresh156(s,2000000)==105);
        InitPort156(p,0);assert(!p.pending && !p.ended && p.queries==0 && p.requests==0 && p.reserved==0);
    }
    else return 2;
    std::cout<<test<<" passed\n";
}
