"""Offline assessment of saved inputs; stdout only, no terminal or broker access."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from forex_demo_lab.forward_eligibility_134 import assess, markdown


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--manifest', type=Path, default=ROOT / 'config/forward-eligibility-134.json')
    parser.add_argument('--format', choices=('json', 'markdown'), default='json')
    args = parser.parse_args()
    try:
        if args.manifest.is_symlink():
            raise ValueError('manifest_symlink')
        with args.manifest.open('rb') as stream:
            raw = stream.read(65_537)
        report = assess(args.root, raw)
    except (OSError, ValueError, OverflowError):
        print('Offline eligibility assessment rejected the input or manifest.', file=sys.stderr)
        return 2
    print(json.dumps(report, sort_keys=True, indent=2, allow_nan=False) if args.format == 'json'
          else markdown(report), end='\n' if args.format == 'json' else '')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
