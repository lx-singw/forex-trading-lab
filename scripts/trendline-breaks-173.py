"""Replay break and bounce setup decisions on invented hourly data."""
import argparse

from forex_demo_lab.trendline import breaks, context, data, engine, entries, exits, ledger, lines, risk


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("descriptor")
    parser.add_argument("hours")
    parser.add_argument("new_output_directory")
    parser.add_argument("--tick-size", required=True)
    parser.add_argument("--profile", choices=breaks.PROFILES, default=breaks.PROFILES[0])
    parser.add_argument("--enable-dly", action="store_true", help="opt in to invented DLY replay")
    parser.add_argument("--cost-profile", choices=("base", "adverse"), default="base")
    parser.add_argument("--as-of", type=int)
    parser.add_argument("--liquidation-at", type=int, help="declared H1 opening in receipt-clock milliseconds")
    account = parser.add_mutually_exclusive_group()
    account.add_argument("--risk-snapshots", help="invented opening equity and margin declarations")
    account.add_argument("--ledger", action="store_true", help="derive a hypothetical USD account from the replay")
    parser.add_argument("--unlock-receipt")
    parser.add_argument("--restore-checkpoint")
    args = parser.parse_args()
    if args.enable_dly != (args.profile == lines.DLY_PROFILE):
        parser.error("DLY profile and --enable-dly must be used together")

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
    frames = ("H4", "D1") if args.profile in (context.PROFILE, breaks.FXR_PROFILE) else ("H4",)
    bars = tuple(bar for bar in stream.bars() if bar.timeframe in frames)

    replay = breaks.BreakReplay(source, args.tick_size, args.profile, enable_dly=args.enable_dly)
    start = 0
    if args.restore_checkpoint:
        checkpoint, _ = data.read_json(args.restore_checkpoint, limit=engine.MAX_CHECKPOINT_BYTES)
        restored = breaks.BreakReplay.restore(source, checkpoint, enable_dly=args.enable_dly)
        start = len(restored.publications)
        if (checkpoint["profile"], checkpoint["tick"], restored.publications) != (
                args.profile, replay.report()["tick"], bars[:start]):
            raise ValueError("setup checkpoint must match supplied profile, tick and prefix")
        replay = restored
    for bar in bars[start:]:
        replay.observe(bar)
    report, checkpoint = replay.report(as_of=as_of), replay.checkpoint()
    entry_report = entries.evaluate(replay, visible_hours, as_of=as_of, cost_profile=args.cost_profile)
    exit_report = exits._evaluate(replay, visible_hours, entry_report, args.liquidation_at)
    admission = None
    if args.risk_snapshots:
        snapshots, _ = data.read_json(args.risk_snapshots)
        admission = risk._evaluate(source, visible_hours, entry_report, exit_report, snapshots)
    accounting = None
    if args.ledger:
        accounting = ledger._evaluate(source, visible_hours, entry_report, exit_report)
    output = data.no_links(args.new_output_directory)
    output.mkdir(exist_ok=False)
    data.write_new(output / "setups.json", report)
    data.write_new(output / "checkpoint.json", checkpoint)
    data.write_new(output / "entries.json", entry_report)
    data.write_new(output / "exits.json", exit_report)
    if admission is not None:
        data.write_new(output / "risk.json", admission)
    if accounting is not None:
        data.write_new(output / "ledger.json", accounting)


if __name__ == "__main__":
    main()
