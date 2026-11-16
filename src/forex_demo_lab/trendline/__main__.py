"""Explicit-file, offline Phase 2 commands; no implicit market discovery."""
import argparse
import json
from pathlib import Path

from .data import (BarStream, Declaration, assess_plan, draft_plan, load_dataset,
                   no_links, read_json, unlock_record, write_new)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    draft = sub.add_parser("draft-plan")
    draft.add_argument("output")
    assess = sub.add_parser("assess-plan")
    assess.add_argument("plan")
    unlock = sub.add_parser("unlock-invented-validation")
    unlock.add_argument("descriptor")
    unlock.add_argument("receipt")
    replay = sub.add_parser("inspect-invented")
    replay.add_argument("descriptor")
    replay.add_argument("hours")
    replay.add_argument("output")
    replay.add_argument("--unlock-receipt")
    replay.add_argument("--as-of", type=int)
    args = parser.parse_args()
    if args.command == "draft-plan":
        write_new(args.output, draft_plan())
    elif args.command == "assess-plan":
        value, _ = read_json(args.plan, 1024 * 1024)
        print(json.dumps(assess_plan(value), indent=2))
    elif args.command == "unlock-invented-validation":
        value, _ = read_json(args.descriptor, 1024 * 1024)
        write_new(args.receipt, unlock_record(Declaration.from_record(value)))
    else:
        source, hours = load_dataset(args.descriptor, args.hours, args.unlock_receipt)
        stream = BarStream(source)
        now = args.as_of if args.as_of is not None else hours[-1].available_at
        if now < source.calendar.start or now > source.calendar.end + 60000:
            raise ValueError("as-of outside declared invented scope")
        for hour in hours:
            if hour.available_at > now:
                break
            stream.observe(hour)
        stream.advance(now)
        report = stream.report()
        output = no_links(args.output)
        output.mkdir(exist_ok=False)
        write_new(output / "report.json", report)
        print(json.dumps({"kind":report["kind"], "data_level":"B",
                          "observed_hours":report["observed_hours"], "bars":len(report["bars"]),
                          "market_cells_run":0,"orders_available":False}))


if __name__ == "__main__":
    main()
