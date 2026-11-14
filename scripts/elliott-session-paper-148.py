"""Embedded common-H1 paper example; invented prices, no terminal/source input."""
import argparse
import hashlib
import importlib.util
from itertools import groupby
import json
from pathlib import Path

from forex_demo_lab import elliott_sessions_146 as o
from forex_demo_lab import elliott_session_paper_148 as p
from forex_demo_lab.elliott_full.contracts import Bar, Quote, D, digest

ROOT=Path(__file__).resolve().parents[1]


def fixture(outcome="target"):
    if outcome not in ("target","gap"):raise ValueError("invented outcome")
    generator_files=(Path(__file__),ROOT/"scripts/elliott-full-shared-entry.py",ROOT/"tests/test_elliott_full_policy.py")
    generators={path.relative_to(ROOT).as_posix():hashlib.sha256(path.read_bytes()).hexdigest() for path in generator_files}
    spec=importlib.util.spec_from_file_location("entry148",ROOT/"scripts/elliott-full-shared-entry.py")
    examples=importlib.util.module_from_spec(spec);spec.loader.exec_module(examples)
    value=examples.fixture(1,"target","EW3")
    cursor=o.START+22*o.HOUR;start=cursor;rows=[]
    days=len(value["hours"])//24
    for i in range(days):
        end=cursor+24*o.HOUR
        rows.append({"kind":"session","label":f"session_paper_{i}","start":cursor,"end":end,
                     "h1":list(range(cursor,end,o.HOUR))+[end],"h4":list(range(cursor,end,4*o.HOUR))+[end],"partial":False})
        cursor=end
        if i<days-1 and i%5==4:
            rows.append({"kind":"closure","start":cursor,"end":cursor+48*o.HOUR,"reason":"invented"})
            cursor+=48*o.HOUR
    calendar=o.Calendar.from_record({"kind":"invented_session_calendar_146","scope":{"start":start,"end":cursor},
                                     "finalization_delay_ms":2000,"segments":rows})
    calendar_sha=calendar.sha256;raw=o.Observations(calendar);windows=calendar.frame("H1")
    cutoff=value["quotes"][0]["time"]
    for i,row in enumerate(value["hours"]):
        if row["available"]>cutoff:break
        w=windows[i]
        raw.observe(Bar("H1",w.start,w.end,w.end+calendar.delay,row["open"],row["high"],row["low"],row["close"],
                        digest([row["lineage"],calendar_sha,i])))
    bars=raw.bars()
    last=next(b for b in reversed(bars) if b.timeframe=="H1")
    when=last.available+2000;bid=last.close
    quotes=(Quote(when,when,0,bid,bid+D(".0001")),
            Quote(when+1000,when+1000,1,bid+(D(".02") if outcome=="target" else -D(".02")),
                  bid+(D(".02") if outcome=="target" else -D(".02"))+D(".0001")))
    freeze={"kind":"invented_session_paper_freeze_not_admission","case":"EW3_long_"+outcome,
            "calendar_sha256":calendar_sha,"bars_sha256":digest([b.record() for b in bars]),
            "quotes_sha256":digest([q.record() for q in quotes]),"generators":generators,"sources":p.source_bindings(),
            "outcome_selection":"predetermined_software_target_or_gap_not_market_selection",
            "market_cells_run":0,"orders_available":False}
    return calendar,bars,quotes,freeze


def run(output,profile="base",outcome="target"):
    output=Path(output)
    if output.exists() or output.is_symlink():raise FileExistsError("new paper output directory required")
    calendar,bars,quotes,freeze=fixture(outcome)
    replay=p.PaperReplay(calendar,profile)
    for _,group in groupby(bars,key=lambda b:b.available):replay.step({"kind":"bars","value":[b.record() for b in group]})
    if replay.pending is None:raise AssertionError("automatic paper setup missing")
    signal=p.setup_record(replay.pending)
    pending=replay.checkpoint()
    entry=replay.step({"kind":"quote","value":quotes[0].record()})
    if entry!="entered":raise AssertionError(entry)
    held=replay.checkpoint()
    replay.step({"kind":"quote","value":quotes[1].record()})
    replay.step({"kind":"finish","value":quotes[1].record()})
    if len(replay.ledger.trades)!=1:raise AssertionError("invented exit missing")
    report={"kind":"invented_session_paper_example_148","freeze":freeze,"profile":profile,"signal":signal,
            "report":replay.state(),"market_cells_run":0,"orders_available":False}
    output.mkdir(parents=True,exist_ok=False)
    for name,value in (("report.json",report),("pending.json",pending),("held.json",held)):
        with (output/name).open("x",encoding="utf-8") as out:json.dump(value,out,indent=2);out.write("\n")
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("output")
    parser.add_argument("--profile",choices=("base","adverse"),default="base")
    parser.add_argument("--outcome",choices=("target","gap"),default="target")
    args=parser.parse_args();report=run(args.output,args.profile,args.outcome)
    print(json.dumps({"kind":report["kind"],"paper_trades":len(report["report"]["ledger"]["trades"]),
                      "market_cells_run":0,"orders_available":False}))


if __name__=="__main__":main()
