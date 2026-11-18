"""Count development opportunities from invented inputs or report source admission status."""
import argparse

from forex_demo_lab.trendline import data, quotes, signal_count


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    bars = commands.add_parser("bars", help="invented Level B hourly observations")
    bars.add_argument("descriptor")
    bars.add_argument("hours")
    bars.add_argument("--liquidation-at", type=int)
    tape = commands.add_parser("quotes", help="invented Level Q synchronized tape")
    tape.add_argument("tape")
    for command in (bars, tape):
        command.add_argument("output")
        command.add_argument("--tick-size", required=True)
        command.add_argument("--as-of", type=int)
        command.add_argument("--profile", choices=signal_count.PROFILES, action="append")
        command.add_argument("--cost-profile", choices=signal_count.COSTS, action="append")
    status = commands.add_parser("status", help="current metadata-only source admission status")
    status.add_argument("plan")
    status.add_argument("output")
    args = parser.parse_args()
    if args.command == "status":
        result = signal_count.admission_status(data.read_json(args.plan)[0])
    else:
        options = {"tick": args.tick_size, "as_of": args.as_of, "profiles": args.profile or signal_count.PROFILES,
                   "costs": args.cost_profile or signal_count.COSTS}
        if args.command == "bars":
            source, hours = data.load_dataset(args.descriptor, args.hours)
            result = signal_count.count_b(source, hours, liquidation_at=args.liquidation_at, **options)
        else:
            raw, _ = data.read_json(args.tape)
            if type(raw) is not dict or raw.get("partition") != "development":
                parser.error("only invented development quotes can be counted")
            result = signal_count.count_q(quotes.Tape(raw), **options)
    data.write_new(args.output, result)


if __name__ == "__main__":
    main()
