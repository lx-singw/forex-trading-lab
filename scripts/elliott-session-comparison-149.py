"""Create/freeze/replay common invented sessions; no market or account reader."""
import argparse
from copy import deepcopy
import importlib.util
import json
from pathlib import Path

from forex_demo_lab import elliott_session_comparison_149 as s

ROOT=Path(__file__).resolve().parents[1]


def fixture(case="trend",warmup_days=253):
    if case not in ("trend","wave","shifted"):raise ValueError("invented_comparison_case")
    source=ROOT/"scripts"/("elliott-full-shared-entry.py" if case=="wave" else "elliott-full-shared.py")
    spec=importlib.util.spec_from_file_location("session_comparison_example149",source)
    example=importlib.util.module_from_spec(spec);spec.loader.exec_module(example)
    value=example.fixture(1,"gap","EW3") if case=="wave" else example.fixture(1,"gap",warmup_days)
    old_start=value["calendar"]["sessions"][0]["start_msc"]
    cursor=old_start+(2*s.observations.HOUR if case=="shifted" else 0);start=cursor;rows=[];opens=[]
    days=len(value["calendar"]["sessions"])
    for i in range(days):
        opens.append(cursor);end=cursor+s.DAY
        rows.append({"kind":"session","label":f"session_{i}","start":cursor,"end":end,
                     "h1":list(range(cursor,end,s.observations.HOUR))+[end],
                     "h4":list(range(cursor,end,4*s.observations.HOUR))+[end],"partial":False})
        cursor=end
        if i<days-1 and i%5==4:
            rows.append({"kind":"closure","start":cursor,"end":cursor+2*s.DAY,"reason":"invented"});cursor+=2*s.DAY
    calendar={"kind":"invented_session_calendar_146","scope":{"start":start,"end":cursor},"finalization_delay_ms":2000,"segments":rows}
    calendar_sha=s.observations.Calendar.from_record(calendar).sha256
    result={"kind":"invented_session_comparison_149","symbol":"EURUSD","case":"common_"+case,
            "calendar":calendar,"hours":[],"quotes":[],"partitions":[]}
    def remap(when):
        day,offset=divmod(when-old_start,s.DAY)
        return opens[day]+offset
    for row in value["hours"]:
        clone=deepcopy(row);clone["start"]=remap(row["start"]);clone["end"]=clone["start"]+row["end"]-row["start"]
        clone["available"]=clone["end"]+row["available"]-row["end"]
        clone["observation"]=clone["start"]+row["observation"]-row["start"]
        clone["lineage"]=s.hour_lineage(result["case"],calendar_sha,clone);result["hours"].append(clone)
    for row in value["quotes"]:
        result["quotes"].append({**row,"time":remap(row["time"]),"source":remap(row["source"])})
    for part in value["partitions"]:
        # End may be precisely a trading-session close before a declared closure.
        # Preserve that boundary rather than mapping it to the next session open.
        end_day,end_offset=divmod(part["end_msc"]-old_start,s.DAY)
        end=opens[end_day-1]+s.DAY if end_offset==0 else remap(part["end_msc"])
        result["partitions"].append({"name":part["name"],"start_msc":remap(part["start_msc"]),
                                     "end_msc":end,"endpoint_source_msc":remap(part["endpoint_source_msc"])})
    return s.validate(result)


def main():
    parser=argparse.ArgumentParser(description=__doc__);commands=parser.add_subparsers(dest="command",required=True)
    create=commands.add_parser("fixture");create.add_argument("output");create.add_argument("--case",choices=("trend","wave","shifted"),default="trend")
    freeze=commands.add_parser("freeze");freeze.add_argument("input");freeze.add_argument("manifest")
    run=commands.add_parser("replay");run.add_argument("input");run.add_argument("manifest");run.add_argument("output")
    args=parser.parse_args()
    if args.command=="fixture":
        s.write(args.output,fixture(args.case));result={"status":"INVENTED_SESSION_FIXTURE_CREATED","orders_available":False}
    elif args.command=="freeze":
        s.freeze(args.input,args.manifest);result={"status":"FROZEN_INVENTED_NOT_ADMISSION","orders_available":False}
    else:
        report=s.evaluate(args.input,args.manifest,args.output)
        result={key:report[key] for key in ("computed_invented_cells","market_cells_run","orders_available")}
    print(json.dumps(result))


if __name__=="__main__":main()
