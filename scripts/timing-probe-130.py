"""Offline inspector only; no terminal connection or execution interface."""
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from forex_demo_lab.timing_probe_130 import inspect_file

if __name__ == '__main__':
    try:
        if len(sys.argv) != 2:
            raise ValueError('arguments')
        result = inspect_file(sys.argv[1])
    except (ValueError, OSError):
        print(json.dumps({'reason': 'invalid_or_unreadable_timing_export', 'orders_available': False}))
        sys.exit(1)
    print(json.dumps(result, sort_keys=True, indent=2))
