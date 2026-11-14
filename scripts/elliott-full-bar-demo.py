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
from test_elliott_full_policy import counts, history, HOUR


def fixture():
    c=counts()
    shape=history(c)
    for i in range(10):
        value=c.origin+D(".0001")*(10-i)/10
        shape[i]=replace(shape[i],open=value,close=value,high=value+D(".00001"),low=value-D(".00001"))
    values=[(c.origin+D(".0001"),)*4]*253
    values += [(b.open,b.high,b.low,b.close) for b in shape]
    # Initial warmup candles must also have consistent OHLC (flat is allowed).
    T=400*86400000
    bars=[]
    for frame,period in (("D1",86400000),("H4",4*HOUR),("H1",HOUR)):
        start=T-len(values)*period
        for i,(o,hi,lo,cl) in enumerate(values):
            bars.append(Bar(frame,start+i*period,start+(i+1)*period,start+(i+1)*period,o,hi,lo,cl,f"invented-{frame}-{i}").record())
    price=c.trigger+D(".0002")
    bars.append(Bar("H1",T,T+HOUR,T+HOUR,price,price+D(".00001"),price-D(".00001"),price,"invented-H1-trigger").record())
    bars.sort(key=lambda b:(b["available"],{"D1":0,"H4":1,"H1":2}[b["timeframe"]],b["start"]))
    t=T+HOUR+2000
    quotes=[Quote(t,t,1,price,price+D(".0001")).record(),
            Quote(t+1000,t+1000,2,D("1.08"),D("1.0801")).record()]
    return {"kind":"invented_ew_full_v1","symbol":"EURUSD","bars":bars,"quotes":quotes}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("output")
    args=parser.parse_args()
    bundle=fixture()
    result=write_report(bundle,args.output)
    (Path(args.output)/"fixture.json").write_text(json.dumps(bundle,indent=2),encoding="utf-8")
    print(json.dumps({"snapshots":len(result["snapshots"]),"signals":sum(len(s["signals"]) for s in result["snapshots"]),
                      "trades":len(result["ledger"]["trades"]),"market_validation":result["market_validation"]}))


if __name__=="__main__":
    main()
