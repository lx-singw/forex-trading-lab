"""Differential arithmetic checks against frozen120/125; no market replay.

Uses the old pure sizer and ledger arithmetic on explicitly supplied invented
state. It does not instantiate an old market strategy, relabel data, or qualify a
source. Differences in trigger, tick-rounding and boundary admission are separate.
"""
from copy import deepcopy
from datetime import datetime,timezone
from decimal import localcontext
import hashlib
from pathlib import Path
from .contracts import D,Quote,precise
from .execution import Ledger,Setup
from .. import elliott_execution_125 as legacy
from .. import daily_fills_120 as fills
from .. import daily_risk_119 as risk


def legacy_bindings():
    root=Path(__file__).resolve().parents[3]
    names=("src/forex_demo_lab/elliott_execution_125.py","src/forex_demo_lab/daily_fills_120.py",
           "src/forex_demo_lab/daily_risk_119.py","src/forex_demo_lab/daily_features_118.py",
           "src/forex_demo_lab/model.py","config/research-candidates-117.json")
    return {name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in names}


def old_event(q):
    return {"sequence":q.sequence,"source_msc":q.source,"receipt_msc":q.time,
            "bid":str(q.bid),"ask":str(q.ask),"feature":{"session_id":0}}


@precise
def sizing_case(side,profile,distance,equity="10000",anchor=None):
    q=Quote(2000,2000,1,D("1.10000"),D("1.10010"))
    stop=D("1.10000")-side*D(distance)
    s=Setup("sizing-reference",side,"EW3",0,60000,D("1.10000"),stop)
    new=Ledger(profile);new.cash=new.mark=new.anchor=D(equity)
    if anchor is not None:
        new.anchor=D(anchor)
    proposal,reason=legacy.structural_size({"side":side,"prospective_invalidation":str(stop),"pattern_id":"invented"},
                                          old_event(q),risk.profiles()[profile],str(new.mark),str(new.cash),
                                          str(new.anchor*D(".99")),"invented-binding")
    actual=new.on_quote(q,s)
    if (proposal is not None)!=(actual=="entered"):
        raise AssertionError(("admission",side,profile,distance,equity,reason,actual))
    if proposal:
        p=new.position
        for new_key,old_key in (("lots","lots"),("entry","entry"),("stop","stop"),("target","target"),("risk","estimated_stop_risk_usd")):
            if p[new_key]!=D(proposal[old_key]):
                raise AssertionError(("sizing",new_key,str(p[new_key]),proposal[old_key]))
        if new.cash!=D(equity)-D(proposal["entry_fee_usd"]):
            raise AssertionError("entry commission mismatch")
    return {"side":side,"profile":profile,"distance":str(distance),"equity":str(equity),
            "admitted":proposal is not None,"new_reason":actual,"legacy_reason":reason,"matched":True}


@precise
def accounting_case(side,profile,outcome):
    if outcome not in ("target","gap","wide_exit","wednesday","weekend","stale","stale_rollover"):
        raise ValueError("audit case")
    rollover=outcome in ("wednesday","weekend","stale_rollover")
    start=int(datetime(2001,1,3 if outcome in ("wednesday","stale_rollover") else 5,
                       23 if rollover else 12,59,58,tzinfo=timezone.utc).timestamp()*1000)
    q=Quote(start,start,1,D("1.10000"),D("1.10010"))
    s=Setup("accounting-reference",side,"EW3",start-2000,start+60000,D("1.10000"),D("1.09900") if side==1 else D("1.10100"))
    new=Ledger(profile)
    if new.on_quote(q,s)!="entered":
        raise AssertionError("audit entry")
    proposal,_=legacy.structural_size({"side":side,"prospective_invalidation":str(s.stop),"pattern_id":"invented"},
                                      old_event(q),risk.profiles()[profile],"10000","10000","9900","invented-binding")
    # Invoke the frozen accounting primitives without bypassing their schemas in
    # a market runner. This is a declared component harness, not a legacy replay.
    old=object.__new__(fills.Replay);old.profile=profile
    state={"balance_usd":str(new.cash),"held":{**proposal,"position_id":"invented-position",
            "financing_usd":"0","financed_through_day":start//86400000},"reservation":{},"ledger":[],
           "last_quote":old_event(q),"peak_equity_usd":"10000","max_drawdown":"0",
           "day_start_equity":"10000","paused":False}
    old._mark(state)
    trace=[]
    def check():
        old._mark(state)
        if D(state["balance_usd"])!=new.cash or D(state["equity_usd"])!=new.mark:
            raise AssertionError(("cash/mark",state["balance_usd"],str(new.cash),state["equity_usd"],str(new.mark)))
        if bool(state["held"])!=bool(new.position):
            raise AssertionError("held mismatch")
        if state["held"] and D(state["held"]["financing_usd"])!=-new.position["financing"]:
            raise AssertionError("financing mismatch")
        exits=[e for e in state["ledger"] if e["kind"]=="exit_fill"]
        if new.trades and D(exits[-1]["net_trade_usd"])!=D(new.trades[-1]["net"]):
            raise AssertionError("net trade mismatch")
        trace.append({"cash":str(new.cash),"observed_equity":str(new.mark),"held":bool(new.position)})
    check()
    dt=2*86400000+2000 if outcome=="weekend" else 2000 if outcome=="wednesday" else 1000
    bid=D("1.10000");ask=D("1.10010")
    if outcome=="target":
        bid=D("1.12000") if side==1 else D("1.08000");ask=bid+D(".00010")
    elif outcome=="gap":
        bid=D("1.08000") if side==1 else D("1.12000");ask=bid+D(".00010")
    elif outcome=="wide_exit":
        bid=D("1.10020");ask=D("1.12000")
    t=start+dt
    tail=Quote(t,t,2,bid,ask)
    if outcome in ("stale","stale_rollover"):
        tail=Quote(start+10000,start,2,bid,ask)
    event=old_event(tail)
    old._financing(state,event)
    executable=tail.source>q.source and tail.time-tail.source<=2000 and tail.session_open
    if executable:
        state["last_quote"]=event
        bid,ask,_=fills._quote(event,risk.profiles()[profile])
        held=state["held"]
        price=bid if side==1 else ask
        if side*(price-D(held["stop"]))<=0:
            old._exit(state,event,"stop",price-side*new.slip)
        elif side*(price-D(held["target"]))>=0:
            old._exit(state,event,"target",D(held["target"]))
    new.on_quote(tail)
    if outcome=="stale_rollover":
        rate=D("3" if profile=="base" else "4.5") if side==1 else D("1.5" if profile=="base" else "2.25")
        expected=rate*3*new.position["lots"]
        if D(state["held"]["financing_usd"])!=0 or new.position["financing"]!=expected:
            raise AssertionError("known rollover difference changed")
        return {"side":side,"profile":profile,"outcome":outcome,"status":"known_timing_difference",
                "legacy_financing_debit":"0","new_financing_debit":str(expected),
                "reason":"legacy financing uses source day; new invented ledger accrues through receipt day even on a stale quote"}
    check()
    if executable and new.position:
        bid,ask,_=fills._quote(event,risk.profiles()[profile])
        old._exit(state,event,"boundary",(bid if side==1 else ask)-side*new.slip)
        new.finish(tail)
        check()
    return {"side":side,"profile":profile,"outcome":outcome,"matched":True,"trace":trace,
            "scope":"cash, executable mark, sizing, financing and exit net; not signal/clock/calendar admission parity"}


def audit():
    before=legacy_bindings()
    sizing=[sizing_case(side,profile,distance,equity) for side in (1,-1) for profile in ("base","adverse")
            for distance in (".00003",".00100",".00300",".01000") for equity in ("20","10000","100000")]
    accounting=[accounting_case(side,profile,outcome) for side in (1,-1) for profile in ("base","adverse")
                for outcome in ("target","gap","wide_exit","wednesday","weekend","stale")]
    differences=[accounting_case(side,profile,"stale_rollover") for side in (1,-1) for profile in ("base","adverse")]
    if before!=legacy_bindings():
        raise AssertionError("frozen legacy source changed during audit")
    return {"kind":"invented_component_differential_audit","legacy_bindings":before,"sizing":sizing,"accounting":accounting,
            "timing_differences":differences,
            "orders_available":False,"market_validation":"UNAVAILABLE",
            "limitations":["Aligned-tick fixtures only; rounding differences are intentional outside this domain",
                           "Stale quotes crossing UTC rollover expose a retained source-day/receipt-day financing difference",
                           "No strategy, clock/calendar admission or full frozen replay parity claimed"]}
