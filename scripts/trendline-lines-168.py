"""Inspect bounded profile-valid lines from explicit invented163 files."""
import argparse
import json

from forex_demo_lab.trendline import data, lines


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("descriptor");parser.add_argument("hours");parser.add_argument("new_output_directory")
    parser.add_argument("--profile",choices=lines.PROFILES,default="TRL_BRK3_E1")
    parser.add_argument("--role",choices=("full","action_break"),default="full")
    parser.add_argument("--as-of",type=int);parser.add_argument("--unlock-receipt")
    args = parser.parse_args()
    frame = "D1" if args.profile == "D1_BRK3" else "H4"
    lines.validate_profile(args.profile,frame,args.role)
    source,hours = data.load_dataset(args.descriptor,args.hours,args.unlock_receipt)
    stream = data.BarStream(source)
    now = args.as_of if args.as_of is not None else hours[-1].available_at
    if not source.calendar.start <= now <= source.calendar.end+60000:raise ValueError("as-of outside invented scope")
    for hour in hours:
        if hour.available_at > now:break
        stream.observe(hour)
    stream.advance(now)
    bars = tuple(b for b in stream.bars() if b.timeframe == frame)
    result = lines.inspect(source,bars,timeframe=frame,profile=args.profile,role=args.role,as_of=now)
    output = data.no_links(args.new_output_directory);output.mkdir(exist_ok=False)
    data.write_new(output/"lines.json",result)
    print(json.dumps({"kind":result["kind"],"candidate_count":len(result["candidates"]),
                      "profile_valid_count":len(result["profile_valid_ids"]),"orders_available":False}))


if __name__ == "__main__":main()
