"""Read-only offline CLI. No terminal or broker interface."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from forex_demo_lab.paired_replay_133 import markdown, replay_manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--manifest', type=Path, default=ROOT / 'config/paired-replay-133.json')
    parser.add_argument('--format', choices=('json', 'markdown'), default='json')
    args = parser.parse_args()
    try:
        if args.manifest.is_symlink():
            raise ValueError('manifest_symlink')
        with args.manifest.open('rb') as stream:
            manifest = stream.read(65_537)
        bundle = replay_manifest(args.root, manifest)
    except (OSError, ValueError, OverflowError):
        print('Offline replay rejected the input or manifest.', file=sys.stderr)
        return 2
    print(json.dumps(bundle, sort_keys=True, indent=2, allow_nan=False) if args.format == 'json'
          else markdown(bundle), end='\n' if args.format == 'json' else '')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
