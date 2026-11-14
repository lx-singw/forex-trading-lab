"""Inspect a closed paired132 export offline; never starts MT5 or submits orders."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from forex_demo_lab.paired_capture_132 import MAX_BYTES, quality_report, quality_markdown

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('closed_export', type=Path)
    parser.add_argument('--format', choices=('json', 'markdown'), default='json')
    args = parser.parse_args()
    try:
        p = args.closed_export
        if p.is_symlink() or not p.is_file() or p.stat().st_size > MAX_BYTES:
            raise ValueError('file')
        with p.open('rb') as stream:
            data = stream.read(MAX_BYTES+1)
        result = quality_report(data)
        output = quality_markdown(result) if args.format == 'markdown' else json.dumps(result, sort_keys=True, indent=2, allow_nan=False)
    except (ValueError, OSError, OverflowError):
        print(json.dumps({'reason': 'invalid_or_unreadable_paired_export', 'orders_available': False}))
        sys.exit(1)
    print(output)
