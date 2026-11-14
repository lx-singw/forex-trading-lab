"""Generate, freeze and replay a common invented H1 observation history."""
import argparse
import json
from forex_demo_lab.elliott_full import shared as s
from forex_demo_lab.elliott_full.contracts import Bar, Quote, D


def fixture(side=1,outcome="gap",warmup_days=253):
    if (type(side) is not int or side not in (-1,1) or outcome not in ("gap","target","flat")
            or type(warmup_days) is not int or not 1<=warmup_days<=253):
        raise ValueError("shared_fixture_case")
    start=978307200000
    case=("long" if side==1 else "short")+"_"+outcome
    sessions=[{"session_id":i,"start_msc":start+i*s.DAY,"end_msc":start+(i+1)*s.DAY,"status":"trading"} for i in range(warmup_days+5)]
    hours=[]
    for day in range(warmup_days+4):
        price=D("1.1")+side*D(".00001")*day if outcome!="flat" else D("1.1")
        for hour in range(24):
            t=start+day*s.DAY+hour*s.HOUR
            b=Bar("H1",t,t+s.HOUR,t+s.HOUR+2000,price,price+D(".0005"),price-D(".0005"),price,"temporary")
            row={**b.record(),"observation":b.end-1}
            row["lineage"]=s.hour_lineage(case,row)
            hours.append(row)
    quotes=[];parts=[]
    for name,day in (("development",warmup_days),("later_validation",warmup_days+2)):
        t=start+day*s.DAY
        bid=D("1.1")+side*D(".00001")*day if outcome!="flat" else D("1.1")
        exit_bid=bid+side*D(".02" if outcome=="target" else "-.01") if outcome!="flat" else bid
        for source,price in ((t+3000,bid),(t+s.DAY-1000,exit_bid)):
            quotes.append(Quote(source+2,source,len(quotes),price,price+D(".0001")).record())
        parts.append({"name":name,"start_msc":t+2000,"end_msc":t+s.DAY,"endpoint_source_msc":t+s.DAY-1000})
    by_start={r["start"]:r for r in hours}
    for record in quotes:
        q=Quote(**record);row=by_start[q.source//s.HOUR*s.HOUR];mid=(q.bid+q.ask)/2
        row["high"]=str(max(D(row["high"]),mid));row["low"]=str(min(D(row["low"]),mid))
        row["lineage"]=s.hour_lineage(case,row)
    return {"kind":"invented_shared_hourly_v1","clock":"invented_utc_milliseconds","symbol":"EURUSD","case":case,
            "calendar":{"kind":"invented_calendar","calendar_id":"shared_continuous_invention","available_msc":start-1,"sessions":sessions},
            "hours":hours,"quotes":quotes,"partitions":parts}


def main():
    parser=argparse.ArgumentParser()
    commands=parser.add_subparsers(dest="command",required=True)
    make=commands.add_parser("fixture");make.add_argument("output")
    make.add_argument("--side",type=int,choices=(-1,1),default=1)
    make.add_argument("--outcome",choices=("gap","target","flat"),default="gap")
    freeze=commands.add_parser("freeze");freeze.add_argument("input");freeze.add_argument("manifest")
    replay=commands.add_parser("replay");replay.add_argument("input");replay.add_argument("manifest");replay.add_argument("output")
    args=parser.parse_args()
    if args.command=="fixture":
        s.c.daily.write_new(args.output,fixture(args.side,args.outcome))
        result={"status":"invented_hourly_fixture_created","orders_available":False}
    elif args.command=="freeze":
        s.freeze(args.input,args.manifest)
        result={"status":"invented_shared_hourly_frozen","orders_available":False}
    else:
        full=s.evaluate(args.input,args.manifest,args.output)
        result={k:full[k] for k in ("computed_invented_cells","market_cells_run","orders_available")}
    print(json.dumps(result))


if __name__=="__main__":
    main()
