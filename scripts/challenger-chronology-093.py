"""Invented-fixture-only CLI; cannot accept market inputs or place orders."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from forex_demo_lab import challenger_chronology_093 as wf


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='action', required=True)
    f = sub.add_parser('synthetic-fixture'); f.add_argument('destination', type=Path)
    f = sub.add_parser('freeze'); f.add_argument('bundle', type=Path); f.add_argument('destination', type=Path)
    for action in ('verify', 'run'):
        f = sub.add_parser(action); f.add_argument('destination', type=Path)
    args = p.parse_args()
    if args.action == 'synthetic-fixture':
        result = dict(bundle=str(wf.synthetic_fixture(args.destination)), synthetic=True)
    elif args.action == 'freeze':
        result = dict(frozen=True, scenarios=wf.freeze(args.bundle, args.destination)['maximum_scenarios'])
    elif args.action == 'verify':
        wf.verify(args.destination); result = dict(verified=True, synthetic=True)
    else:
        summary = wf.run(args.destination)
        result = dict(scenarios=len(summary['scenario_bindings']), choices=len(summary['selection_bindings']),
            synthetic=True, status=summary['status'], market_profitability_established=False, orders_available=False)
    print(json.dumps(result))
