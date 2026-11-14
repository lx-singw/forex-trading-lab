"""Offline invented fill/financing ledger checks; orders are unavailable."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from forex_demo_lab.daily_features_118 import write_new
from forex_demo_lab.daily_fills_120 import evaluate_fixture, freeze_fixture
from forex_demo_lab.daily_fills_fixture_120 import CASES, fixture


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    create = commands.add_parser("create-fixture")
    create.add_argument("case", choices=CASES)
    create.add_argument("output", type=Path)
    freeze = commands.add_parser("freeze")
    freeze.add_argument("fixture", type=Path)
    freeze.add_argument("manifest", type=Path)
    evaluate = commands.add_parser("evaluate")
    evaluate.add_argument("fixture", type=Path)
    evaluate.add_argument("manifest", type=Path)
    evaluate.add_argument("report", type=Path)
    args = parser.parse_args()
    try:
        if args.command == "create-fixture":
            write_new(args.output, fixture(args.case))
            result = {"created": True, "case": args.case}
        elif args.command == "freeze":
            result = {"frozen": True, "case": freeze_fixture(args.fixture, args.manifest)["case"]}
        else:
            report = evaluate_fixture(args.fixture, args.manifest, args.report)
            result = {"comparisons": len(report["results"]), "kind": report["kind"],
                      "results": [{"profile": r["profile"], "candidate": r["candidate"], **r["summary"]}
                                  for r in report["results"]]}
        result["orders_available"] = False
    except FileExistsError:
        print(json.dumps({"accepted": False, "reason": "artifact_exists"}))
        return 1
    except ValueError as exc:
        print(json.dumps({"accepted": False, "reason": str(exc)}))
        return 1
    except OSError:
        print(json.dumps({"accepted": False, "reason": "artifact_io_error"}))
        return 1
    print(json.dumps(result, sort_keys=True, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
