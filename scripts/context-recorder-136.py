"""Inspect a closed136 export offline. Does not start a terminal or submit orders."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from forex_demo_lab.context_recorder_136 import MAX_BYTES, quality_report, markdown


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('closed_export', type=Path)
    parser.add_argument('--format', choices=('json', 'markdown'), default='json')
    args = parser.parse_args()
    try:
        path = args.closed_export
        if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_BYTES:
            raise ValueError('file')
        with path.open('rb') as stream: raw = stream.read(MAX_BYTES + 1)
        report = quality_report(raw)
    except (OSError, ValueError, OverflowError):
        print(json.dumps(dict(reason='invalid_or_unreadable_context136_export', orders_available=False)))
        return 1
    print(markdown(report) if args.format == 'markdown' else json.dumps(report, sort_keys=True, indent=2, allow_nan=False),
          end='' if args.format == 'markdown' else '\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
