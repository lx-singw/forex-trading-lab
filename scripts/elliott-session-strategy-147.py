"""Embedded invented session/strategy example; no external source or order input."""
import argparse
from decimal import Decimal
from itertools import groupby
import json
from pathlib import Path

from forex_demo_lab import elliott_sessions_146 as o
from forex_demo_lab import elliott_session_strategy_147 as s
from forex_demo_lab.elliott_full.contracts import Bar, digest


def demonstration():
    start=o.START+22*o.HOUR
    cursor=start;rows=[]
    for i,hours in enumerate((23,25)):
        end=cursor+hours*o.HOUR
        rows.append({"kind":"session","label":f"session_demo_{i}","start":cursor,"end":end,
                     "h1":list(range(cursor,end,o.HOUR))+[end],
                     "h4":list(range(cursor,end,4*o.HOUR))+[end],"partial":False})
        cursor=end
        if i==0:
            rows.append({"kind":"closure","start":cursor,"end":cursor+48*o.HOUR,"reason":"invented"})
            cursor+=48*o.HOUR
    c=o.Calendar.from_record({"kind":"invented_session_calendar_146","scope":{"start":start,"end":cursor},
                              "finalization_delay_ms":2000,"segments":rows})
    freeze={"kind":"invented_decision_freeze_not_admission","calendar":c.record(),
            "calendar_sha256":c.sha256,"sources":s.source_bindings()}
    raw=o.Observations(c);delayed=o.Observations(c)
    late_index=24
    for i,w in enumerate(c.frame("H1")):
        p=Decimal("1.1")+Decimal(i)/10000
        bar=Bar("H1",w.start,w.end,w.end+c.delay,p,p+Decimal(".0003"),p-Decimal(".0002"),p+Decimal(".0001"),digest(["invented147",i]))
        raw.observe(bar)
        if i!=late_index:delayed.observe(bar)
        else:late=bar
    replay=s.DecisionReplay(c)
    for _,group in groupby(raw.bars(),key=lambda b:b.available):replay.publish_batch(tuple(group))
    checkpoint=replay.checkpoint();restart=s.DecisionReplay.restore(checkpoint)
    failed=s.DecisionReplay(c)
    before_bars=delayed.bars()
    for _,group in groupby(before_bars,key=lambda b:b.available):failed.publish_batch(tuple(group))
    prior=failed.checkpoint()
    late_record=late.record();late_record["available"]=c.end+5000
    delayed.observe(Bar(**late_record))
    known={(b.timeframe,b.start) for b in before_bars}
    batch=tuple(b for b in delayed.bars() if (b.timeframe,b.start) not in known)
    try:failed.publish_batch(batch)
    except ValueError as error:rejected=str(error)
    else:raise AssertionError("source backfill was not rejected")
    return {"kind":"invented_session_strategy_demonstration_147","freeze":freeze,
            "continuous":replay.state(),"checkpoint":checkpoint,"restart_equal":restart.state()==replay.state(),
            "late_backfill":{"rejected":True,"reason":rejected,"batch_unchanged":prior==failed.checkpoint()},
            "orders_available":False,"market_cells_run":0,"returns_computed":False}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("output",type=Path);args=parser.parse_args()
    result=demonstration();args.output.mkdir(parents=True,exist_ok=False)
    with (args.output/"demonstration.json").open("x",encoding="utf-8") as out:json.dump(result,out,indent=2);out.write("\n")
    print(json.dumps({k:result[k] for k in ("kind","restart_equal","late_backfill","orders_available")}))


if __name__=="__main__":main()
