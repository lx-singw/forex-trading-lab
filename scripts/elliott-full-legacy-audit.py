"""Save declared invented component comparisons against frozen120/125 arithmetic."""
import argparse
import json
from pathlib import Path
from forex_demo_lab.elliott_full.contracts import bindings
from forex_demo_lab.elliott_full.crosscheck import audit,legacy_bindings


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("output")
    args=parser.parse_args()
    root=Path(args.output);root.mkdir(parents=True,exist_ok=False)
    declaration={"kind":"invented_component_differential_audit","current_sources":bindings(),
                 "legacy_sources":legacy_bindings(),"sides":[1,-1],"profiles":["base","adverse"],
                 "sizing_distances":[".00003",".00100",".00300",".01000"],
                 "sizing_equities":["20","10000","100000"],
                 "accounting_outcomes":["target","gap","wide_exit","wednesday","weekend","stale"],
                 "timing_difference_case":"stale_rollover","orders_available":False,"market_validation":"UNAVAILABLE"}
    (root/"declaration.json").write_text(json.dumps(declaration,indent=2),encoding="utf-8")
    result=audit()
    (root/"results.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
    print(json.dumps({"matched_sizing":len(result["sizing"]),"matched_accounting":len(result["accounting"]),
                      "known_timing_differences":len(result["timing_differences"]),"orders_available":False}))


if __name__=="__main__":
    main()
