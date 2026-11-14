"""Local invented chronology demonstration or integrity-only JSON inspection."""

import argparse
from datetime import date, datetime
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from forex_demo_lab.daily_reference_098 import (SCHEMA, SyntheticSeries, integrity_summary,
    load_bundle, parse_bundle, save_bundle, select_as_of, synthetic_fixture)


def demonstration(bundle):
    if type(bundle) is not SyntheticSeries:
        raise ValueError("Demonstration requires fixed invented input")
    cases = [
        ("publication_boundary", "2030-01-07", "2030-01-07T16:00:00+00:00"),
        ("after_publication", "2030-01-07", "2030-01-07T16:00:00.000001+00:00"),
        ("revision_boundary", "2030-01-07", "2030-01-08T17:00:00+00:00"),
        ("after_revision", "2030-01-07", "2030-01-08T17:00:00.000001+00:00"),
        ("second_release_boundary", "2030-01-08", "2030-01-08T16:00:00+00:00"),
        ("invented_holiday", "2030-01-09", "2030-01-09T18:00:00+00:00"),
        ("missing_expected_day", "2030-01-11", "2030-01-11T18:00:00+00:00"),
        ("third_observation", "2030-01-10", "2030-01-10T18:00:00+00:00"),
    ]
    records = []
    for name, observed, decision in cases:
        result = select_as_of(bundle, date.fromisoformat(observed), datetime.fromisoformat(decision))
        records.append(dict(case=name, observation_date=observed, decision_at=decision,
                            reason=result.reason.value, vintage_id=result.version.vintage_id if result.version else None))
    return dict(**integrity_summary(bundle), synthetic_only=True, cases=records,
                selected_cases=sum(r["vintage_id"] is not None for r in records),
                missing_cases=sum(r["vintage_id"] is None for r in records))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    fixture = commands.add_parser("fixture", help="Write exact invented local input")
    fixture.add_argument("output", type=Path)
    demo = commands.add_parser("demo", help="Select fixed invented records by availability")
    demo.add_argument("input", type=Path)
    demo.add_argument("output", type=Path)
    inspect = commands.add_parser("inspect", help="Inspect local integrity without historical qualification")
    inspect.add_argument("input", type=Path)
    args = parser.parse_args()
    if args.command == "fixture":
        save_bundle(args.output, parse_bundle(synthetic_fixture()))
        print(json.dumps(dict(schema=SCHEMA, invented_fixture_written=True)))
    elif args.command == "demo":
        report = demonstration(load_bundle(args.input))
        with args.output.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(report, sort_keys=True, indent=2, allow_nan=False) + "\n")
        print(json.dumps({k: report[k] for k in ("unique_versions", "observation_dates", "selected_cases", "missing_cases", "orders_available")}))
    else:
        print(json.dumps(integrity_summary(load_bundle(args.input)), sort_keys=True))


if __name__ == "__main__":
    main()
