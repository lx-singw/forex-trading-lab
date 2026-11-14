"""Standalone invented Elliott accounting; no connection or actual orders."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from forex_demo_lab import elliott_execution_125 as execution
from forex_demo_lab.elliott_execution_fixture_125 import CASES, fixture


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
    evaluate.add_argument("output_root", type=Path)
    args = parser.parse_args()
    try:
        if args.command == "create-fixture":
            execution.daily.write_new(args.output, fixture(args.case))
            result = {"created": True, "case": args.case}
        elif args.command == "freeze":
            result = {"frozen": True, "case": execution.freeze_fixture(args.fixture, args.manifest)["case"]}
        else:
            report = execution.evaluate_fixture(args.fixture, args.manifest, args.output_root)
            result = {"case": report["case"], "planned_separate_accounts": 8,
                      "partitions": [{"name": p["partition"]["name"], "status": p["status"], "reason": p["reason"], "computed_accounts": p["computed_accounts"]} for p in report["partitions"]]}
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
