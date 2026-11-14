"""Freeze and replay six invented public-input discovery cases; no market access."""
import argparse
import importlib.util
import json
from pathlib import Path
from forex_demo_lab.elliott_full.contracts import bindings,digest
from forex_demo_lab.elliott_full.replay import write_report


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("output")
    args=parser.parse_args()
    root=Path(args.output);root.mkdir(parents=True,exist_ok=False)
    path=Path(__file__).with_name("elliott-full-bar-demo.py")
    spec=importlib.util.spec_from_file_location("bar_examples",path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    cases=[(kind,side,"base") for kind in ("EW3","EW5") for side in (1,-1)]
    cases += [(kind,-1,"adverse") for kind in ("EW3","EW5")]
    frozen=[]
    for kind,side,profile in cases:
        name=f"{kind}-{'long' if side==1 else 'short'}-{profile}"
        bundle=module.fixture(kind,side)
        (root/f"{name}-fixture.json").write_text(json.dumps(bundle,indent=2),encoding="utf-8")
        frozen.append({"name":name,"kind":kind,"side":side,"profile":profile,"input_digest":digest(bundle),"bundle":bundle})
    declaration={"kind":"invented_public_bar_discovery","bindings":bindings(),
                 "cases":[{k:v for k,v in c.items() if k!="bundle"} for c in frozen],
                 "limitations":["Timeframe histories are independently invented, not certified aggregation from a single quote feed",
                                 "Deliberately constructed gap exits are software evidence, not market returns"],
                 "orders_available":False,"market_validation":"UNAVAILABLE"}
    (root/"declaration.json").write_text(json.dumps(declaration,indent=2),encoding="utf-8")
    outcomes=[]
    for case in frozen:
        result=write_report(case["bundle"],root/case["name"],case["profile"])
        row={"case":case["name"],"signals":sum(len(s["signals"]) for s in result["snapshots"]),
             "trades":len(result["ledger"]["trades"]),"kind":"invented_public_bar_discovery",
             "market_validation":result["market_validation"],"orders_available":result["orders_available"]}
        outcomes.append(row)
        (root/"results.json").write_text(json.dumps(outcomes,indent=2),encoding="utf-8")
        print(json.dumps(row),flush=True)
        if row["signals"]!=1 or row["trades"]!=1:
            raise AssertionError("declared discovery coverage failed; outcome retained")


if __name__=="__main__":
    main()
