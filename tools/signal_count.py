"""Count development opportunities and check historical input eligibility."""
import argparse

from forex_demo_lab.trendline import data, historical_count, historical_input, quotes, signal_count


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
    historical = commands.add_parser("historical-input", help="verify reviewed Level B development input")
    reviewed_count = commands.add_parser("historical-count", help="count opportunities on reviewed Level B development")
    for command in (historical, reviewed_count):
        command.add_argument("manifest")
        command.add_argument("output")
    for command in (bars, historical, reviewed_count):
        command.add_argument("--delayed-entry", action="store_true", help="use the Sprint 230 Level B variant")
    args = parser.parse_args()
    if args.command == "status":
        result = signal_count.admission_status(data.read_json(args.plan)[0])
    elif args.command in ("historical-input", "historical-count"):
        try:
            if args.command == "historical-input":
                result = historical_input.load_level_b(args.manifest, delayed_entry=args.delayed_entry).receipt
            else:
                result = historical_count.count(args.manifest, delayed_entry=args.delayed_entry)
        except (OSError, ValueError) as error:
            parser.error(str(error))
    else:
        options = {"tick": args.tick_size, "as_of": args.as_of, "profiles": args.profile or signal_count.PROFILES,
                   "costs": args.cost_profile or signal_count.COSTS}
        if args.command == "bars":
            source, hours = data.load_dataset(args.descriptor, args.hours)
            result = signal_count.count_b(source, hours, liquidation_at=args.liquidation_at,
                                          delayed_entry=args.delayed_entry, **options)
        else:
            raw, _ = data.read_json(args.tape)
            if type(raw) is not dict or raw.get("partition") != "development":
                parser.error("only invented development quotes can be counted")
            result = signal_count.count_q(quotes.Tape(raw), **options)
    data.write_new(args.output, result)


if __name__ == "__main__":
    main()
