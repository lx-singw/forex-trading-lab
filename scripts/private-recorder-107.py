"""Inspect a closed107 diagnostic export read-only; never starts MT5."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from forex_demo_lab.private_recorder_107 import inspect_file, summary

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    args = parser.parse_args()
    try:
        result = summary(inspect_file(args.input))
    except (ValueError, OSError):
        print(json.dumps({"accepted": False, "reason": "invalid_or_unreadable_export"}))
        sys.exit(1)
    print(json.dumps(result, sort_keys=True, indent=2))
