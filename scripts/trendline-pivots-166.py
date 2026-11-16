"""Inspect causal pivots from explicitly named invented163 source/hour files."""
import argparse
import json

from forex_demo_lab.trendline import data, pivots


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("descriptor")
    parser.add_argument("hours")
    parser.add_argument("new_output_directory")
    parser.add_argument("--timeframe",choices=("H4","D1","both"),default="both")
    parser.add_argument("--as-of",type=int)
    parser.add_argument("--unlock-receipt")
    args = parser.parse_args()
    source,hours = data.load_dataset(args.descriptor,args.hours,args.unlock_receipt)
    stream = data.BarStream(source)
    now = args.as_of if args.as_of is not None else hours[-1].available_at
    if not source.calendar.start <= now <= source.calendar.end+60000:
        raise ValueError("as-of outside invented scope")
    for hour in hours:
        if hour.available_at > now:
            break
        stream.observe(hour)
    stream.advance(now)
    frames = ("H4","D1") if args.timeframe == "both" else (args.timeframe,)
    observers = {frame:pivots.PivotStream(source,frame) for frame in frames}
    for bar in stream.bars():
        if bar.timeframe in observers:
            observers[bar.timeframe].observe(bar)
    for observer in observers.values():
        observer.advance(now)
    report = {"schema":pivots.VERSION,"kind":"invented_trendline_pivot_inspection",
              "data_level":"B","geometry_basis":source.record()["geometry_basis"],
              "frames":{frame:observer.report() for frame,observer in observers.items()},
              "market_cells_run":0,"orders_available":False,"demo_eligible":False}
    output = data.no_links(args.new_output_directory)
    output.mkdir(exist_ok=False)
    data.write_new(output/"pivots.json",report)
    print(json.dumps({"kind":report["kind"],"confirmed":{f:len(r["pivots"]) for f,r in report["frames"].items()},
                      "orders_available":False}))


if __name__ == "__main__":
    main()
