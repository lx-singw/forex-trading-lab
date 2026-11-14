"""Invented daily admission/sizing checks; no fills, returns or automated orders."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from forex_demo_lab.daily_features_118 import write_new
from forex_demo_lab.daily_risk_119 import evaluate_fixture, freeze_fixture
from forex_demo_lab.daily_risk_fixture_119 import CASES, fixture


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
            result = {"created": True, "kind": "invented_daily_risk_fixture", "case": args.case}
        elif args.command == "freeze":
            manifest = freeze_fixture(args.fixture, args.manifest)
            result = {"frozen": True, "case": manifest["case"], "orders_available": False}
        else:
            report = evaluate_fixture(args.fixture, args.manifest, args.report)
            result = {"returns": None, "orders_available": False, "comparisons": len(report["results"]),
                      "results": [{"profile": r["profile"], "candidate": r["candidate"],
                                   "reasons": [o["reason"] for o in r["outcomes"]],
                                   "proposed_lots": [o["proposal"]["lots"] for o in r["outcomes"] if o["proposal"]]}
                                  for r in report["results"]]}
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
