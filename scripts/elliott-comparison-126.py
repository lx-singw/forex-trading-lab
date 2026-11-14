"""Compare five fixed hypotheses on invented quotes, without broker connections."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from forex_demo_lab import elliott_comparison_126 as comparison
from forex_demo_lab.comparison_fixture_126 import CASES, fixture


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    create = commands.add_parser("create-fixture")
    create.add_argument("case", choices=CASES)
    create.add_argument("output", type=Path)
    freeze = commands.add_parser("freeze")
    freeze.add_argument("fixture", type=Path)
    freeze.add_argument("manifest", type=Path)
    for name in ("evaluate", "verify"):
        sub = commands.add_parser(name)
        sub.add_argument("fixture", type=Path)
        sub.add_argument("manifest", type=Path)
        sub.add_argument("output_root", type=Path)
    args = parser.parse_args()
    try:
        if args.command == "create-fixture":
            comparison.daily.write_new(args.output, fixture(args.case))
            result = {"created": True, "case": args.case}
        elif args.command == "freeze":
            result = {"frozen": True, "case": comparison.freeze_fixture(args.fixture, args.manifest)["case"]}
        else:
            method = comparison.evaluate_fixture if args.command == "evaluate" else comparison.verify_fixture
            report = method(args.fixture, args.manifest, args.output_root)
            result = {"case": report["case"], "verified": args.command == "verify", "planned_separate_accounts": 20,
                      "computed_accounts": report["computed_accounts"], "unavailable_accounts": 20 - report["computed_accounts"]}
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
