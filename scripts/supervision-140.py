"""Run built-in invented supervisor cases. No native/market-input option."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from forex_demo_lab.supervision_fixture_140 import run_demo, markdown


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--format', choices=('json', 'markdown'), default='json')
    args = parser.parse_args()
    try:
        report = run_demo()
    except (OSError, ValueError, RuntimeError):
        print('Invented supervision exercise failed.', file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2, sort_keys=True, allow_nan=False) if args.format == 'json'
          else markdown(report), end='\n' if args.format == 'json' else '')
    return 0


if __name__ == '__main__': raise SystemExit(main())
