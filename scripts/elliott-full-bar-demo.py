"""Full public invented-bar replay; no supplied signals, counts or context states.

The three timeframe histories are independently invented observations. This does
not certify aggregation from one underlying quote feed or any market source.
"""
import argparse
import json
from dataclasses import replace
from pathlib import Path
from forex_demo_lab.elliott_full.contracts import Bar, D, Quote
from forex_demo_lab.elliott_full.replay import write_report
from test_elliott_full_policy import counts, mirrored, history, HOUR


def fixture(kind="EW3",side=1,outcome="gap_stop"):
    if kind not in ("EW3","EW5") or type(side) is not int or side not in (-1,1) or outcome not in ("gap_stop","target"):
        raise ValueError("invented case")
    c=counts(kind)
    if side==-1:
        c=mirrored(c)
    shape=history(c)
    for i in range(10):
        value=c.origin+side*D(".0001")*(10-i)/10
        shape[i]=replace(shape[i],open=value,close=value,high=value+D(".00001"),low=value-D(".00001"))
    values=[(c.origin+side*D(".0001"),)*4]*253
    values += [(b.open,b.high,b.low,b.close) for b in shape]
    # Initial warmup candles must also have consistent OHLC (flat is allowed).
    T=600*86400000
    bars=[]
    for frame,period in (("D1",86400000),("H4",4*HOUR),("H1",HOUR)):
        start=T-len(values)*period
        for i,(o,hi,lo,cl) in enumerate(values):
            bars.append(Bar(frame,start+i*period,start+(i+1)*period,start+(i+1)*period,o,hi,lo,cl,f"invented-{frame}-{i}").record())
    price=c.trigger+side*D(".0002")
    bars.append(Bar("H1",T,T+HOUR,T+HOUR,price,price+D(".00001"),price-D(".00001"),price,"invented-H1-trigger").record())
    bars.sort(key=lambda b:(b["available"],{"D1":0,"H4":1,"H1":2}[b["timeframe"]],b["start"]))
    t=T+HOUR+2000
    bid=price if side==1 else price-D(".0001")
    exit_bid=D("1.08") if side==1 else D("1.12")
    if outcome=="target":
        exit_bid=D("1.25") if side==1 else D(".95")
    quotes=[Quote(t,t,1,bid,bid+D(".0001")).record(),
            Quote(t+1000,t+1000,2,exit_bid,exit_bid+D(".0001")).record()]
    return {"kind":"invented_ew_full_v1","symbol":"EURUSD","bars":bars,"quotes":quotes}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("output")
    parser.add_argument("--setup",choices=("EW3","EW5"),default="EW3")
    parser.add_argument("--side",type=int,choices=(-1,1),default=1)
    parser.add_argument("--outcome",choices=("gap_stop","target"),default="gap_stop")
    parser.add_argument("--profile",choices=("base","adverse"),default="base")
    args=parser.parse_args()
    bundle=fixture(args.setup,args.side,args.outcome)
    result=write_report(bundle,args.output,args.profile)
    (Path(args.output)/"fixture.json").write_text(json.dumps(bundle,indent=2),encoding="utf-8")
    print(json.dumps({"snapshots":len(result["snapshots"]),"signals":sum(len(s["signals"]) for s in result["snapshots"]),
                      "trades":len(result["ledger"]["trades"]),"market_validation":result["market_validation"]}))


if __name__=="__main__":
    main()
