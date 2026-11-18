"""Replay BRK3 and FXR setup decisions on invented hourly data."""
import argparse

from forex_demo_lab.trendline import breaks, context, data, engine, entries


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("descriptor")
    parser.add_argument("hours")
    parser.add_argument("new_output_directory")
    parser.add_argument("--tick-size", required=True)
    parser.add_argument("--profile", choices=breaks.PROFILES, default=breaks.PROFILES[0])
    parser.add_argument("--cost-profile", choices=("base", "adverse"), default="base")
    parser.add_argument("--as-of", type=int)
    parser.add_argument("--unlock-receipt")
    parser.add_argument("--restore-checkpoint")
    args = parser.parse_args()

    source, hours = data.load_dataset(args.descriptor, args.hours, args.unlock_receipt)
    as_of = args.as_of if args.as_of is not None else hours[-1].available_at
    stream = data.BarStream(source)
    visible_hours = []
    for hour in hours:
        if hour.available_at > as_of:
            break
        stream.observe(hour)
        visible_hours.append(hour)
    stream.advance(as_of)
    frames = ("H4", "D1") if args.profile == context.PROFILE else ("H4",)
    bars = tuple(bar for bar in stream.bars() if bar.timeframe in frames)

    replay = breaks.BreakReplay(source, args.tick_size, args.profile)
    start = 0
    if args.restore_checkpoint:
        checkpoint, _ = data.read_json(args.restore_checkpoint, limit=engine.MAX_CHECKPOINT_BYTES)
        restored = breaks.BreakReplay.restore(source, checkpoint)
        start = len(restored.publications)
        if (checkpoint["profile"], checkpoint["tick"], restored.publications) != (
                args.profile, replay.report()["tick"], bars[:start]):
            raise ValueError("setup checkpoint must match supplied profile, tick and prefix")
        replay = restored
    for bar in bars[start:]:
        replay.observe(bar)
    report, checkpoint = replay.report(), replay.checkpoint()
    entry_report = entries.evaluate(replay, visible_hours, as_of=as_of, cost_profile=args.cost_profile)
    output = data.no_links(args.new_output_directory)
    output.mkdir(exist_ok=False)
    data.write_new(output / "setups.json", report)
    data.write_new(output / "checkpoint.json", checkpoint)
    data.write_new(output / "entries.json", entry_report)


if __name__ == "__main__":
    main()
