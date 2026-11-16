"""Inspect exact indicators from explicit invented163 files; no market reader."""
import argparse
import json

from forex_demo_lab.trendline import data, geometry


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("descriptor");parser.add_argument("hours");parser.add_argument("new_output_directory")
    parser.add_argument("--timeframe",choices=("H4","D1","both"),default="both")
    parser.add_argument("--as-of",type=int);parser.add_argument("--unlock-receipt")
    args = parser.parse_args()
    source,hours = data.load_dataset(args.descriptor,args.hours,args.unlock_receipt)
    stream = data.BarStream(source)
    now = args.as_of if args.as_of is not None else hours[-1].available_at
    if not source.calendar.start <= now <= source.calendar.end+60000:raise ValueError("as-of outside invented scope")
    for hour in hours:
        if hour.available_at > now:break
        stream.observe(hour)
    stream.advance(now)
    frames = ("H4","D1") if args.timeframe == "both" else (args.timeframe,)
    observers = {f:geometry.GeometryStream(source,f) for f in frames}
    for bar in stream.bars():
        if bar.timeframe in observers:observers[bar.timeframe].observe(bar)
    for observer in observers.values():observer.advance(now)
    result = {"schema":geometry.VERSION,"kind":"invented_geometry_inspection","data_level":"B",
              "frames":{f:observer.report() for f,observer in observers.items()},
              "market_cells_run":0,"orders_available":False,"demo_eligible":False}
    output = data.no_links(args.new_output_directory);output.mkdir(exist_ok=False)
    data.write_new(output/"geometry.json",result)
    print(json.dumps({"kind":result["kind"],"frames":list(frames),"orders_available":False}))


if __name__ == "__main__":main()
