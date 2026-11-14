"""Offline invented stress checks. No broker connection or orders."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from forex_demo_lab.combination_stress_116 import create_matrix, evaluate_matrix, inspect_capture


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    create = sub.add_parser("create-matrix")
    create.add_argument("directory", type=Path)
    evaluate = sub.add_parser("evaluate")
    evaluate.add_argument("directory", type=Path)
    evaluate.add_argument("output", type=Path)
    capture = sub.add_parser("inspect-capture")
    capture.add_argument("path", type=Path)
    capture.add_argument("--format", choices=("107", "109", "111"), default="111")
    args = parser.parse_args()
    try:
        if args.command == "create-matrix":
            result = create_matrix(args.directory)
            result = {"created": True, "accepted_paths": result["accepted_paths"],
                      "rejected_inputs": result["rejected_inputs"], "checkpoint_faults": result["checkpoint_faults"]}
        elif args.command == "evaluate":
            report = evaluate_matrix(args.directory, args.output)
            result = {k: report[k] for k in ("kind", "verification_passed", "counts_complete", "failures",
                                            "market_validation", "orders_available")}
            result.update(paths=len(report["results"]), rejected_inputs=len(report["rejected_inputs"]),
                          checkpoint_faults=len(report["checkpoint_faults"]))
            print(json.dumps(result, sort_keys=True, indent=2, allow_nan=False))
            return 0 if report["verification_passed"] else 1
        else:
            result = inspect_capture(args.path, args.format)
    except (ValueError, OSError, TypeError, RecursionError):
        print(json.dumps({"accepted": False, "reason": "invalid_unavailable_or_existing_artifact"}))
        return 1
    print(json.dumps(result, sort_keys=True, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
