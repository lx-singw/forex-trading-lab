"""Invented hierarchical H1 observations for shared entry acceptance, not prices.

All H4/D1 observations are subsequently derived by shared.py. The pattern template
is used only to construct test prices; no count/signal/context is supplied to replay.
"""
from dataclasses import replace
import argparse
import json
from forex_demo_lab.elliott_full import shared as s
from forex_demo_lab.elliott_full.contracts import Bar,Quote,D,precise
from test_elliott_full_policy import counts,history,source_pivots


@precise
def shape(kind="EW3",extra=40,compression=D(1)):
    count=counts(kind)
    rows=history(count,extra)
    for i in range(10):
        value=count.origin+D(".0001")*(10-i)/10
        rows[i]=replace(rows[i],open=value,close=value,high=value+D(".00001"),low=value-D(".00001"))
    if compression!=1:
        points={int((D(p.index)*compression).to_integral_value()):p.price for p in source_pivots(count)}
        terminal=max(points);knots=sorted(points);compressed=[]
        for i in range(terminal+extra+1):
            if i<knots[0]:value=count.origin+D(".0001")*(knots[0]-i)/knots[0]
            elif i>knots[-1]:value=(count.trigger+count.terminal.price)/2
            else:
                a=max(j for j in knots if j<=i);b=min(j for j in knots if j>=i)
                value=points[a] if a==b else points[a]+(points[b]-points[a])*(i-a)/(b-a)
            compressed.append(replace(rows[0],close=value,open=value,high=value+D(".00001"),low=value-D(".00001")))
        rows=compressed
    return rows,count


@precise
def fixture(side=1,outcome="gap",kind="EW3",h4offset=D(".25"),h1offset=D(".02"),compression=D(".9"),phase=0):
    if type(side) is not int or side not in (-1,1) or outcome not in ("gap","target") or kind not in ("EW3","EW5"):
        raise ValueError("shared entry case")
    start=978307200000;warm=253
    daily,dc=shape("EW3",40)
    h4,hc=shape("EW3",40)
    h1,c=shape(kind,8,compression)
    d0=warm
    h40=(d0+dc.terminal.index+5)*24
    h10=h40+(hc.terminal.index+5)*4+phase
    trigger_hour=h10+len(h1)
    total_days=max(warm+len(daily)+2,(trigger_hour+60)//24+2)
    values=[dc.origin+D(".0001")]* (total_days*24)
    for i,row in enumerate(daily):
        for j in range(24):values[(d0+i)*24+j]=dc.origin+(row.close-dc.origin)*100
    dmid=dc.origin+((dc.trigger+dc.terminal.price)/2-dc.origin)*100
    h4origin=dmid+h4offset
    for i,row in enumerate(h4):
        for j in range(4):values[h40+4*i+j]=h4origin+(row.close-hc.origin)*10
    h4mid=h4origin+((hc.trigger+hc.terminal.price)/2-hc.origin)*10
    h1origin=h4mid+h1offset
    for i,row in enumerate(h1):values[h10+i]=h1origin+row.close-c.origin
    price=h1origin+c.trigger-c.origin+D(".0002")
    values[trigger_hour]=price
    case=("long" if side==1 else "short")+"_"+kind.lower()+"_"+outcome
    sessions=[{"session_id":i,"start_msc":start+i*s.DAY,"end_msc":start+(i+1)*s.DAY,"status":"trading"} for i in range(total_days+1)]
    hours=[]
    for i,value in enumerate(values):
        value=(D("2.2")-value if side==-1 else value).quantize(D(".00001"))
        t=start+i*s.HOUR
        bar=Bar("H1",t,t+s.HOUR,t+s.HOUR+2000,value,value+D(".00001"),value-D(".00001"),value,"temporary")
        row={**bar.record(),"observation":bar.end-1}
        row["lineage"]=s.hour_lineage(case,row);hours.append(row)
    t=start+(trigger_hour+1)*s.HOUR+4000
    price=(D("2.2")-price if side==-1 else price).quantize(D(".00001"))
    bid=price if side==1 else price-D(".0001")
    exit_bid=bid+side*D("-.02" if outcome=="gap" else ".02")
    quotes=[Quote(t,t,0,bid,bid+D(".0001")).record(),Quote(t+1000,t+1000,1,exit_bid,exit_bid+D(".0001")).record(),
            Quote(t+s.DAY,t+s.DAY,2,bid,bid+D(".0001")).record(),Quote(t+s.DAY+1000,t+s.DAY+1000,3,bid,bid+D(".0001")).record()]
    for q in quotes:
        row=hours[(q["source"]-start)//s.HOUR];mid=(D(q["bid"])+D(q["ask"]))/2
        row["high"]=str(max(D(row["high"]),mid));row["low"]=str(min(D(row["low"]),mid))
        row["lineage"]=s.hour_lineage(case,row)
    return {"kind":"invented_shared_hourly_v1","clock":"invented_utc_milliseconds","symbol":"EURUSD","case":case,
            "calendar":{"kind":"invented_calendar","calendar_id":"shared_hierarchical_invention","available_msc":start-1,"sessions":sessions},
            "hours":hours,"quotes":quotes,"partitions":[{"name":name,"start_msc":when-1,"end_msc":when+1001,"endpoint_source_msc":when+1000}
                      for name,when in (("development",t),("later_validation",t+s.DAY))]}


def main():
    parser=argparse.ArgumentParser()
    commands=parser.add_subparsers(dest="command",required=True)
    make=commands.add_parser("fixture");make.add_argument("output")
    make.add_argument("--side",type=int,choices=(-1,1),default=1)
    make.add_argument("--outcome",choices=("gap","target"),default="gap")
    make.add_argument("--setup",choices=("EW3","EW5"),default="EW3")
    freeze=commands.add_parser("freeze");freeze.add_argument("input");freeze.add_argument("manifest")
    replay=commands.add_parser("replay");replay.add_argument("input");replay.add_argument("manifest");replay.add_argument("output")
    args=parser.parse_args()
    if args.command=="fixture":
        s.c.daily.write_new(args.output,fixture(args.side,args.outcome,args.setup))
        result={"status":"invented_shared_entry_fixture_created","orders_available":False}
    elif args.command=="freeze":
        s.freeze(args.input,args.manifest);result={"status":"invented_shared_entry_frozen","orders_available":False}
    else:
        report=s.evaluate(args.input,args.manifest,args.output)
        result={k:report[k] for k in ("computed_invented_cells","market_cells_run","orders_available")}
    print(json.dumps(result))


if __name__=="__main__":main()
