"""Freeze and inspect the separate invented Elliott-inspired daily hypothesis."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from forex_demo_lab import elliott_waves_124 as waves
from forex_demo_lab.elliott_fixture_124 import CASES, fixture


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
    evaluate.add_argument("output", type=Path)
    args = parser.parse_args()
    try:
        if args.command == "create-fixture":
            waves.daily.write_new(args.output, fixture(args.case))
            result = {"created": True, "case": args.case}
        elif args.command == "freeze":
            result = {"frozen": True, "case": waves.freeze_fixture(args.fixture, args.manifest)["case"]}
        else:
            report = waves.evaluate_fixture(args.fixture, args.manifest, args.output)
            result = {"case": report["case"], "confirmed_pivots": report["confirmed_pivots"],
                      "signal_observations": report["signal_observations"], "trades": None, "returns": None}
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
