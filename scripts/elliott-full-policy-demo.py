"""Declared-count component examples; requires PYTHONPATH=src:tests.

This deliberately exercises policy/accounting separately from automatic bar
discovery. Parent contexts and resolved nodes are invented fixture assumptions.
"""
import argparse
import copy
import csv
import hashlib
import json
from itertools import product
from pathlib import Path
from forex_demo_lab.elliott_full.contracts import D, Quote, bindings
from forex_demo_lab.elliott_full.execution import Ledger
from forex_demo_lab.elliott_full.setups import Policy
from forex_demo_lab.elliott_full.report import render
from test_elliott_full_policy import counts, mirrored, history, append


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("output")
    args=parser.parse_args()
    output=Path(args.output)
    output.mkdir(parents=True,exist_ok=False)
    cases=list(product(("EW3","EW5"),(1,-1),("target","gap_stop","context_skip"),("base","adverse")))
    declaration={"kind":"invented_declared_count_component_examples","cases":cases,"bindings":bindings(),
                 "fixture_source_sha256":hashlib.sha256(Path("tests/test_elliott_full_policy.py").read_bytes()).hexdigest(),
                 "limitations":["Parent contexts and resolved counts supplied as invented fixture assumptions",
                                 "Not end-to-end automatic discovery or market evidence"],"orders_available":False}
    (output/"declaration.json").write_text(json.dumps(declaration,indent=2),encoding="utf-8")
    rows=[]
    for kind,side,outcome,profile in cases:
        name=f"{kind}-{'long' if side==1 else 'short'}-{outcome}-{profile}"
        c=counts(kind)
        if side==-1:
            c=mirrored(c)
        h=history(c);policy=Policy();ledger=Ledger(profile)
        context=(side,None) if outcome=="context_skip" else (side,side)
        policy.update([c],h,context)
        snapshots=[]
        def snapshot(time):
            snapshots.append({"time":time,"frame":"H1","reason":policy.reason,
                              "counts":[n.record() for n in c.legs],"context":context,
                              "policy":copy.deepcopy(policy.record())})
        snapshot(h[-1].available)
        append(h,c.trigger+side*D(".0002"))
        signals=policy.update([c],h,context)
        snapshot(h[-1].available)
        if signals:
            signal=signals[0];t=signal.formed+2000
            bid=c.trigger+(D(".0002") if side==1 else -D(".0003"))
            result=ledger.on_quote(Quote(t,t,1,bid,bid+D(".0001")),signal)
            if result!="entered":
                raise AssertionError((name,result))
            snapshot(t)
            position=ledger.position
            price=position["target"]+side*D(".001") if outcome=="target" else position["stop"]-side*D(".01")
            bid=price if side==1 else price-D(".0001")
            ledger.on_quote(Quote(t+1000,t+1000,2,bid,bid+D(".0001")))
            snapshot(t+1000)
            assert Ledger.restore(ledger.checkpoint()).state()==ledger.state()
        report={"kind":declaration["kind"],"limitations":declaration["limitations"],"orders_available":False,
                "bars":[b.record() for b in h],"snapshots":snapshots,"ledger":ledger.state()}
        (output/f"{name}.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
        page=render(report).replace("<h1>Elliott research replay</h1>",
                                   "<h1>Declared-count component example</h1><p>Resolved counts and parent contexts are supplied invented assumptions. This is not automatic discovery from bars or market evidence.</p>")
        (output/f"{name}.html").write_text(page,encoding="utf-8")
        net=ledger.trades[0]["net"] if ledger.trades else None
        rows.append({"case":name,"trades":len(ledger.trades),"net":net,"reason":policy.reason})
    with (output/"summary.csv").open("w",newline="",encoding="utf-8") as stream:
        writer=csv.DictWriter(stream,fieldnames=("case","trades","net","reason"))
        writer.writeheader();writer.writerows(rows)
    (output/"summary.json").write_text(json.dumps(rows,indent=2),encoding="utf-8")
    print(json.dumps({"cases":len(rows),"trades":sum(r["trades"] for r in rows),"kind":declaration["kind"],"orders_available":False}))


if __name__=="__main__":
    main()
