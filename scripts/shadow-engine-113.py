"""Local invented-data checks and read-only native diagnostics; no MT5 connection."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from forex_demo_lab.shadow_engine_113 import evaluate_fixture, freeze_fixture, inspect_capture, write_new
from forex_demo_lab.shadow_fixture_113 import fixture


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subs = parser.add_subparsers(dest="command", required=True)
    create = subs.add_parser("create-fixture")
    create.add_argument("case", choices=("continuation", "reversal"))
    create.add_argument("output", type=Path)
    freeze = subs.add_parser("freeze")
    freeze.add_argument("fixture", type=Path)
    freeze.add_argument("manifest", type=Path)
    evaluate = subs.add_parser("evaluate")
    evaluate.add_argument("fixture", type=Path)
    evaluate.add_argument("manifest", type=Path)
    evaluate.add_argument("report", type=Path)
    capture = subs.add_parser("inspect-capture")
    capture.add_argument("path", type=Path)
    capture.add_argument("--format", choices=("107", "109", "111"), default="111")
    args = parser.parse_args()
    try:
        if args.command == "create-fixture":
            write_new(args.output, fixture(args.case))
            result = {"created": True, "kind": "invented_fixture", "case": args.case}
        elif args.command == "freeze":
            m = freeze_fixture(args.fixture, args.manifest)
            result = {"frozen": True, "kind": m["kind"], "events": m["events"], "fixture_sha256": m["fixture_sha256"]}
        elif args.command == "evaluate":
            report = evaluate_fixture(args.fixture, args.manifest, args.report)
            result = {"kind": report["kind"], "cases": len(report["results"]), "market_validation": False,
                      "orders_available": False, "results": [{k: r[k] for k in ("case", "scenario", "partition", "metrics", "cost_totals")} for r in report["results"]]}
        else:
            result = inspect_capture(args.path, args.format)
    except (ValueError, OSError, TypeError, RecursionError):
        print(json.dumps({"accepted": False, "reason": "invalid_unavailable_or_existing_artifact"}))
        return 1
    print(json.dumps(result, sort_keys=True, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
