"""Offline invented-input contract demonstration; stdout only."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from forex_demo_lab.fresh_input_135 import MAX_BYTES, Replay, invented_cases, markdown
from forex_demo_lab.paired_replay_133 import canonical


def read(path, limit):
    if path.is_symlink(): raise ValueError('symlink')
    with path.open('rb') as stream: return stream.read(limit + 1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, help='A strictly invented135 JSON fixture; native captures reject.')
    parser.add_argument('--policy', type=Path, default=ROOT / 'config/fresh-input-135.json')
    parser.add_argument('--format', choices=('json', 'markdown'), default='json')
    args = parser.parse_args()
    try:
        policy = read(args.policy, 65_536)
        sources = {'input': read(args.input, MAX_BYTES)} if args.input else {k: canonical(v) for k, v in invented_cases().items()}
        reports = {k: Replay(raw, policy).run() for k, raw in sources.items()}
    except (OSError, ValueError, TypeError, OverflowError, RecursionError):
        print('Invented contract check rejected the input or policy.', file=sys.stderr)
        return 2
    print(json.dumps(reports, sort_keys=True, indent=2, allow_nan=False) if args.format == 'json'
          else markdown(reports), end='\n' if args.format == 'json' else '')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
