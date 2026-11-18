"""Replay an invented EURUSD Level Q quote tape."""
import argparse

from forex_demo_lab.trendline import breaks, data, lines, quote_replay, quotes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tape")
    parser.add_argument("new_output_directory")
    parser.add_argument("--tick-size", required=True)
    parser.add_argument("--profile", choices=breaks.PROFILES, default=breaks.PROFILES[0])
    parser.add_argument("--cost-profile", choices=("base", "adverse"), default="base")
    parser.add_argument("--enable-dly", action="store_true")
    parser.add_argument("--as-of", type=int)
    parser.add_argument("--unlock-receipt")
    parser.add_argument("--restore-checkpoint")
    args = parser.parse_args()
    if args.enable_dly != (args.profile == lines.DLY_PROFILE):
        parser.error("DLY profile and --enable-dly must be used together")
    document, _ = data.read_json(args.tape)
    unlock = None if args.unlock_receipt is None else data.read_json(args.unlock_receipt)[0]
    tape = quotes.Tape(document, unlock)
    settings = {"as_of": tape.calendar.end if args.as_of is None else args.as_of, "tick": args.tick_size,
                "profile": args.profile, "cost": args.cost_profile, "enable_dly": args.enable_dly}
    if args.restore_checkpoint:
        saved, _ = data.read_json(args.restore_checkpoint)
        report = quote_replay.restore(tape, saved, **settings)
    else:
        report = quote_replay.evaluate(tape, **settings)
    output = data.no_links(args.new_output_directory)
    output.mkdir(exist_ok=False)
    data.write_new(output / "quote-ledger.json", report)
    data.write_new(output / "checkpoint.json", quote_replay.checkpoint(report))


if __name__ == "__main__":
    main()
