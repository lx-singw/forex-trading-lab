"""Run, resume or verify the fixed local invented forex demonstration."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from forex_demo_lab import engine_demo_123 as demo


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("demo", "resume", "verify"))
    parser.add_argument("output", type=Path, help="new demo directory beneath this repository's data/")
    args = parser.parse_args()
    try:
        if args.command == "verify":
            result = demo.verify(args.output)
        else:
            report = demo.create(args.output) if args.command == "demo" else demo.resume(args.output)
            result = {"report": str(demo._root(args.output) / "REPORT.md"),
                      "planned_toy_cells": report["planned_toy_cells"], "available_accounts": report["available_accounts"],
                      "unavailable_cells": report["unavailable_cells"], "market_cells_run": 0,
                      "orders_available": False, "real_money_execution_available": False}
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
