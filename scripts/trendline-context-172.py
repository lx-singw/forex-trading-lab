"""Export Phase 5 diagnostics from an invented hourly replay."""
import argparse

from forex_demo_lab.trendline import context, data, lines


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("descriptor")
    parser.add_argument("hours")
    parser.add_argument("new_output_file")
    parser.add_argument("--profile", choices=lines.STRATEGIES, default=context.PROFILE)
    parser.add_argument("--as-of", type=int)
    parser.add_argument("--unlock-receipt")
    args = parser.parse_args()
    source, hours = data.load_dataset(args.descriptor, args.hours, args.unlock_receipt)
    as_of = args.as_of if args.as_of is not None else hours[-1].available_at
    stream = data.BarStream(source)
    for hour in hours:
        if hour.available_at > as_of:
            break
        stream.observe(hour)
    stream.advance(as_of)
    publications = [bar for bar in stream.bars() if bar.timeframe in ("D1", "H4")]
    result = context.replay(source, publications, profile=args.profile, as_of=as_of)
    data.write_new(args.new_output_file, result)


if __name__ == "__main__":
    main()
