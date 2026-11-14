"""Inspect a closed cost128 export offline; never launch MT5 or connect to a broker."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from forex_demo_lab.cost_probe_128 import inspect_file

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("export", type=Path)
    args = parser.parse_args()
    try:
        result = inspect_file(args.export)
    except (ValueError, OSError, OverflowError):
        print(json.dumps({"accepted": False, "reason": "invalid_or_unreadable_cost_export"}))
        sys.exit(1)
    print(json.dumps(result, sort_keys=True, indent=2, allow_nan=False))
