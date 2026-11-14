"""Generate a small, explicitly invented observational replay; no market data."""
import argparse
import json
from pathlib import Path
from forex_demo_lab.elliott_full.contracts import Bar, D
from forex_demo_lab.elliott_full.replay import write_report


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("output")
    args=parser.parse_args()
    # Repeated varying-width swings, deliberately shorter than required warmup.
    anchors=["1.100","1.112","1.106","1.130","1.118","1.142","1.110","1.132","1.092","1.120","1.101","1.140"]
    values=[]
    for a,b in zip(anchors,anchors[1:]):
        values.extend(D(a)+(D(b)-D(a))*i/5 for i in range(5))
    bars=[]
    for frame,period in (("D1",86400000),("H4",14400000),("H1",3600000)):
        for i,value in enumerate(values):
            bars.append(Bar(frame,i*period,(i+1)*period,(i+1)*period,value,value+D(".00005"),value-D(".00005"),value,f"invented-{frame}-{i}").record())
    bars.sort(key=lambda b:(b["available"],{"D1":0,"H4":1,"H1":2}[b["timeframe"]],b["start"]))
    bundle={"kind":"invented_ew_full_v1","symbol":"EURUSD","bars":bars,"quotes":[]}
    result=write_report(bundle,args.output)
    (Path(args.output)/"fixture.json").write_text(json.dumps(bundle,indent=2),encoding="utf-8")
    print(json.dumps({"snapshots":len(result["snapshots"]),"market_validation":result["market_validation"],"orders_available":False}))


if __name__=="__main__":
    main()
