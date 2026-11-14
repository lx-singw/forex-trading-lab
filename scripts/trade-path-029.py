"""Frozen all-trade path extraction on already reviewed cached development ticks."""
import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import runpy
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from forex_demo_lab.trade_path import TradePath

API = runpy.run_path(str(ROOT/'scripts/strategy-experiment-028.py'))
sha, write, sealed, load = API['sha'], API['write'], API['sealed'], API['load']
PRIOR = ROOT/'reports/strategy-experiment-028-final-source.json'
LEDGER = ROOT/'reports/trade-path-029-ledger.json'


def prior_verify(allow_handoff=False):
    assert sha(PRIOR) == 'be317de1f1a1294441d0b48eff0cd22db524b693858d988e53b5cfb6ccde9b63'
    previous = sealed(PRIOR)
    bindings, changes = {}, {}
    for group, values in previous.items():
        if not group.endswith('_bindings') or group == 'archive_external_bindings':
            continue
        for name, expected in values.items():
            assert name not in bindings
            current = sha(ROOT/name)
            if current != expected:
                assert allow_handoff and group == 'source_bindings' and name in API['HANDOFF'], name
                changes[name] = dict(previous_sha256=expected, current_sha256=current)
            bindings[name] = expected
    external = previous['archive_external_bindings']
    assert len(bindings) == 786 and len(external) == 34
    assert all(bindings[n] == h for n, h in external.items())
    assert sha(PRIOR.with_suffix('.zip')) == previous['archive_sha256']
    with zipfile.ZipFile(PRIOR.with_suffix('.zip')) as z:
        assert z.testzip() is None and len(z.infolist()) == 752
        assert set(z.namelist()) == set(bindings)-set(external)
        for name in z.namelist():
            assert hashlib.sha256(z.read(name)).hexdigest() == bindings[name], name
    API['verify']()
    return dict(bindings_verified=786, archive_members_verified=752,
                external_bindings_verified=34, allowed_handoff_changes=changes)


def freeze():
    checked = prior_verify()
    old = API['verify']()
    tests = sealed(ROOT/'reports/trade-path-029-tests.json')
    assert tests['passed'] and tests['tests_passed'] == 368
    bindings = dict(old['bindings'])
    for name in ('src/forex_demo_lab/trade_path.py', 'tests/test_trade_path.py',
                 'scripts/trade-path-029.py', 'scripts/check-trade-path-029.py',
                 'scripts/test-trade-path-029.py', 'docs/TRADE-PATH-029-PLAN.md',
                 'docs/TRADE-PATH-029-PROTOCOL.md', 'reports/trade-path-029-tests.json',
                 'reports/trade-path-029-tests.sha256', 'reports/strategy-experiment-028-checks.json',
                 'reports/strategy-experiment-028-checks.sha256', 'reports/strategy-experiment-028-summary.json',
                 'reports/strategy-experiment-028-summary.sha256', 'reports/strategy-experiment-028-ledger.json',
                 'reports/strategy-experiment-028-ledger.sha256',
                 'reports/strategy-experiment-028-final-source.json', 'reports/strategy-experiment-028-final-source.sha256'):
        bindings[name] = sha(ROOT/name)
    selected = {}
    trade_count = 0
    for s in old['scenarios']:
        name = 'reports/strategy-experiment-028-'+s['id']+'.json'
        r = sealed(ROOT/name)
        assert r['scenario'] == s['id'] and r['ledger_sha256'] == sha(API['LEDGER'])
        bindings[name] = sha(ROOT/name)
        bindings[name.replace('.json', '.sha256')] = sha(ROOT/name.replace('.json', '.sha256'))
        n = len(r['trades'])
        assert len(r['fill_lineage']) == n
        assert [f['trade_index'] for f in r['fill_lineage']] == list(range(n))
        selected[s['id']] = sorted({0, n-1}) if n else []
        trade_count += n
    assert trade_count == 266
    write(LEDGER, dict(kind='frozen_path_attribution_029', bindings=bindings,
        prior_snapshot_verification=checked, scenarios=old['scenarios'], datasets=old['datasets'],
        independent_full_path_indices=selected, trades_expected=266,
        formula='signed side*(liquidation-entry)*lots*contract - full commission + accrued swap; modeled final fill',
        thresholds_r=[.5, 1], new_strategy_runs=0, annual_eligible=False, orders_available=False))
    print(json.dumps(dict(frozen=True, bindings=len(bindings), trades=266,
                         independent_paths=sum(map(len, selected.values())))))


def verify():
    ledger = sealed(LEDGER)
    for name, expected in ledger['bindings'].items():
        assert sha(ROOT/name) == expected, name
    return ledger


def run(sample):
    ledger = verify()
    scenarios = [s for s in ledger['scenarios'] if s['sample'] == sample]
    accounts = []
    for s in scenarios:
        r = sealed(ROOT/('reports/strategy-experiment-028-'+s['id']+'.json'))
        paths = [TradePath(t, f, s['config']) for t, f in zip(r['trades'], r['fill_lineage'], strict=True)]
        accounts.append(dict(spec=s, paths=paths, index=0))
    count = 0
    for tick in API['read_ticks'](ROOT/API['SAMPLES'][sample][0]):
        assert tick['sequence'] == count
        for a in accounts:
            if a['index'] >= len(a['paths']):
                continue
            path = a['paths'][a['index']]
            if path.start <= count <= path.end:
                path.step(tick)
            if count == path.end:
                path.finish()
                a['index'] += 1
        count += 1
        if count % 1000000 == 0:
            print(json.dumps(dict(sample=sample, ticks=count)), flush=True)
    assert count == ledger['datasets'][sample]['ticks']
    rows = []
    for a in accounts:
        assert a['index'] == len(a['paths'])
        rows.append(dict(scenario=a['spec']['id'], sample=sample, candidate=a['spec']['candidate'],
                         cost=a['spec']['cost'], trades=[p.finish() for p in a['paths']]))
    write(ROOT/f'reports/trade-path-029-{sample}.json', dict(kind='all_trade_paths_029',
        ledger_sha256=sha(LEDGER), source_ticks_read=count, scenarios=rows,
        new_strategy_runs=0, annual_eligible=False, orders_available=False))
    print(json.dumps(dict(sample=sample, completed=True, trades=sum(len(r['trades']) for r in rows))))


def summarize():
    ledger = verify()
    rows = []
    for sample in API['SAMPLES']:
        out = sealed(ROOT/f'reports/trade-path-029-{sample}.json')
        assert out['ledger_sha256'] == sha(LEDGER)
        for scenario in out['scenarios']:
            trades = scenario['trades']
            stops = [t for t in trades if t['exit_reason'] == 'stop_tick']
            wins = [t['net_pnl'] for t in trades if t['net_pnl'] > 0]
            rows.append(dict(scenario=scenario['scenario'], candidate=scenario['candidate'],
                sample=sample, cost=scenario['cost'], trades=len(trades), stops=len(stops),
                stops_prior_positive=sum(t['prior_positive'] for t in stops),
                stops_prior_half_r=sum(t['prior_half_r'] for t in stops),
                stops_prior_one_r=sum(t['prior_one_r'] for t in stops),
                stops_never_positive=sum(not t['prior_positive'] for t in stops),
                mean_maximum_net_r=sum(t['maximum_net_r'] for t in trades)/len(trades),
                mean_minimum_net_r=sum(t['minimum_net_r'] for t in trades)/len(trades),
                net_pnl=sum(t['net_pnl'] for t in trades),
                net_excluding_largest_winner=sum(t['net_pnl'] for t in trades)-max(wins, default=0),
                largest_winner_share_of_positive_pnl=max(wins)/sum(wins) if wins else None,
                path_quotes=sum(t['quote_count'] for t in trades),
                exits=dict(Counter(t['exit_reason'] for t in trades))))
    assert len(rows) == 30 and sum(r['trades'] for r in rows) == 266
    write(ROOT/'reports/trade-path-029-summary.json', dict(kind='all30_path_summary_029',
        ledger_sha256=sha(LEDGER), scenarios=rows, no_new_returns=True,
        not_independent_trials=True, annual_eligible=False, orders_available=False))
    fields = tuple(k for k in rows[0] if k != 'exits')
    with (ROOT/'reports/trade-path-029-table.csv').open('x', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows({k: row[k] for k in fields} for row in rows)
    print(json.dumps(dict(scenarios=30, trades=266, stops=sum(r['stops'] for r in rows))))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('freeze', 'verify', 'run', 'summary'))
    parser.add_argument('sample', nargs='?', choices=tuple(API['SAMPLES']))
    args = parser.parse_args()
    if args.action == 'run':
        if args.sample is None:
            parser.error('run requires declared sample')
        try:
            run(args.sample)
        except Exception as exc:
            write(ROOT/f'reports/trade-path-029-{args.sample}-failure.json',
                  dict(passed=False, action='path extraction', error_type=type(exc).__name__, message=str(exc), orders_available=False))
            raise
    else:
        {'freeze': freeze, 'verify': verify, 'summary': summarize}[args.action]()
