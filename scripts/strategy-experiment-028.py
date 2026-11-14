"""Fixed 30-scenario development replay; never annual validation or execution."""
import argparse
from collections import Counter
import csv
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import sys
import time
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from forex_demo_lab.model import Config
from forex_demo_lab.strategy_experiment_028 import CANDIDATES, Experiment028Simulator
from forex_demo_lab.tick_dataset import read_ticks

PRIOR = ROOT/'reports/strategy-diagnosis-027-final-source.json'
LEDGER = ROOT/'reports/strategy-experiment-028-ledger.json'
HANDOFF = {'README.md', 'docs/CONTEXT.md', 'docs/PLAN.md', 'docs/VERIFICATION.md'}
SAMPLES = {'january': ('data/research-004-january-mt5', 'reports/research-quality-004.json'),
           'april': ('data/research-005-april-new-york', 'reports/research-quality-005.json'),
           'july': ('data/research-004-july-new-york', 'reports/research-quality-004.json')}


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()


def load(path):
    return json.loads(path.read_text())


def write(path, value):
    with path.open('x') as f:
        json.dump(value, f, indent=2, sort_keys=True, allow_nan=False)
        f.write('\n')
    with path.with_suffix('.sha256').open('x') as f:
        f.write(sha(path)+'\n')


def sealed(path):
    assert sha(path) == path.with_suffix('.sha256').read_text().strip(), path
    return load(path)


def prior_verify(allow_handoff=False):
    assert sha(PRIOR) == 'bfba54543c5d3a95fa43e7c96ec096ff5b72f0f8cd80929e86167a04d565efa6'
    prior = sealed(PRIOR)
    bindings, changes = {}, {}
    for group, values in prior.items():
        if not group.endswith('_bindings') or group == 'archive_external_bindings':
            continue
        for name, expected in values.items():
            assert name not in bindings
            current = sha(ROOT/name)
            if current != expected:
                assert allow_handoff and group == 'source_bindings' and name in HANDOFF, name
                changes[name] = dict(previous_sha256=expected, current_sha256=current)
            bindings[name] = expected
    external = prior['archive_external_bindings']
    assert len(bindings) == 700 and len(external) == 33
    assert all(bindings[n] == h for n, h in external.items())
    assert sha(PRIOR.with_suffix('.zip')) == prior['archive_sha256']
    with zipfile.ZipFile(PRIOR.with_suffix('.zip')) as z:
        assert z.testzip() is None and len(z.infolist()) == 667
        assert set(z.namelist()) == set(bindings)-set(external)
        for name in z.namelist():
            assert hashlib.sha256(z.read(name)).hexdigest() == bindings[name], name
    return dict(bindings_verified=700, archived_members_verified=667,
                external_bindings_verified=33, allowed_handoff_changes=changes)


def freeze():
    verified = prior_verify()
    original = load(ROOT/'reports/comparison-008-ledger.json')
    spec = load(ROOT/'config/research-candidates-028.json')
    assert tuple(spec['candidates']) == CANDIDATES and spec['scenario_budget'] == 30
    tests = sealed(ROOT/'reports/strategy-experiment-028-tests.json')
    assert tests['passed'] and tests['tests_passed'] == 356
    synthetic = sealed(ROOT/'reports/strategy-experiment-028-synthetic-checks.json')
    assert synthetic['passed'] and synthetic['cases_checked'] == 12
    bindings = {}
    def bind(name, expected=None):
        digest = sha(ROOT/name)
        if expected is not None:
            assert digest == expected, name
        bindings[name] = digest
    # All application modules: no hidden behavior changes between freeze and replay.
    for path in sorted((ROOT/'src').rglob('*.py')):
        bind(path.relative_to(ROOT).as_posix())
    for name in ('config/research-candidates-028.json', 'docs/STRATEGY-EXPERIMENT-028-PLAN.md',
                 'docs/STRATEGY-EXPERIMENT-028-PROTOCOL.md', 'scripts/strategy-experiment-028.py',
                 'scripts/check-strategy-experiment-028.py', 'scripts/test-strategy-experiment-028.py',
                 'tests/test_strategy_experiment_028.py', 'reports/strategy-experiment-028-tests.json',
                 'reports/strategy-experiment-028-tests.sha256', 'reports/comparison-008-ledger.json',
                 'reports/strategy-experiment-028-synthetic-checks.json', 'reports/strategy-experiment-028-synthetic-checks.sha256',
                 'reports/comparison-008-summary.json', 'reports/strategy-diagnosis-027-ledger.json',
                 'reports/strategy-diagnosis-027-final-source.json', 'reports/strategy-diagnosis-027-final-source.sha256'):
        bind(name)
    bind('reports/comparison-008-source.zip', original['archive_sha256'])
    archive_members = {}
    with zipfile.ZipFile(ROOT/'reports/comparison-008-source.zip') as z:
        assert z.testzip() is None
        for name in z.namelist():
            digest = hashlib.sha256(z.read(name)).hexdigest()
            bind(name, digest)
            archive_members[name] = digest
    for sample, (folder, review_name) in SAMPLES.items():
        ds = original['datasets'][sample]
        bind(folder+'/provenance.json', ds['provenance_sha256'])
        bind(folder+'/ticks.csv.gz', ds['data_sha256'])
        bind(review_name, ds['quality_sha256'])
        quality = load(ROOT/review_name)
        matches = [d for d in quality['datasets'] if d.get('provenance_sha256') == ds['provenance_sha256']]
        assert quality['performance_evaluation_ready'] is True and len(matches) == 1
        assert matches[0]['status'] == 'ready_for_development_research'
        assert load(ROOT/folder/'provenance.json')['data_sha256'] == ds['data_sha256']
    configs = {}
    for cost in ('base', 'adverse'):
        name = 'config/tick-pilot-003'+('-adverse' if cost == 'adverse' else '')+'.json'
        bind(name)
        configs[cost] = asdict(Config(**load(ROOT/name)))
        assert all(s['config'] == configs[cost] for s in original['scenarios'] if s['cost'] == cost)
    old_summary = load(ROOT/'reports/comparison-008-summary.json')
    for row in old_summary['scenarios']:
        bind('reports/comparison-008-'+row['scenario']+'.json', row['report_sha256'])
    scenarios = [dict(id=f'{sample}-{candidate}-{cost}', sample=sample, candidate=candidate,
                      cost=cost, config=configs[cost])
                 for sample in SAMPLES for candidate in CANDIDATES for cost in configs]
    assert len(scenarios) == 30
    outputs = ['reports/strategy-experiment-028-'+s['id']+'.json' for s in scenarios]
    assert not any((ROOT/name).exists() for name in outputs)
    write(LEDGER, dict(kind='fixed_development_replay_028', bindings=bindings,
        original_archive_members=archive_members, prior_snapshot_verification=verified,
        scenarios=scenarios, expected_outputs=outputs, datasets=original['datasets'],
        scenario_budget=30, cash_reference_net_pnl=0, independent_monthly_capital=True,
        data_role='reused_2024_development_not_validation', selection_authorized=False,
        annual_eligible=False, orders_available=False))
    print(json.dumps(dict(frozen=True, scenarios=30, bindings=len(bindings))))


def verify():
    ledger = sealed(LEDGER)
    for name, expected in ledger['bindings'].items():
        assert sha(ROOT/name) == expected, name
    return ledger


def reconcile(report, config, start):
    t = report['trades']
    m = report['metrics']
    for trade in t:
        assert int(datetime.fromisoformat(trade['opened']).timestamp()*1000) >= start
        assert math.isclose(trade['gross_pnl']-trade['commission']+trade['swap'], trade['net_pnl'], abs_tol=1e-8)
    for key in ('net_pnl', 'commission', 'swap'):
        assert math.isclose(sum(x[key] for x in t), m[key], abs_tol=1e-8)
    assert len(t) == m['closed_trades'] == len(report['fill_lineage'])
    assert math.isclose(config['initial_equity']+m['net_pnl'], report['equity'][-1]['equity'], abs_tol=1e-8)


def control_parity(report):
    old = load(ROOT/('reports/comparison-008-'+report['scenario']+'.json'))
    assert old['trades'] == report['trades'], 'Control trade mismatch'
    assert old['flat_account_decisions'] == report['flat_account_decisions'], 'Control signal mismatch'
    excluded = {'max_tick_drawdown', 'max_close_drawdown'}
    assert {k: v for k, v in old['metrics'].items() if k not in excluded} == {
        k: v for k, v in report['metrics'].items() if k not in excluded}, 'Control cash/cost/state mismatch'
    assert [(p['time'], p['paused']) for p in old['equity']] == [(p['time'], p['paused']) for p in report['equity']]
    return dict(passed=True, original_report_sha256=sha(ROOT/('reports/comparison-008-'+report['scenario']+'.json')),
                corrected_tick_drawdown=report['metrics']['max_tick_drawdown'],
                legacy_tick_drawdown=old['metrics']['max_tick_drawdown'])


def run(sample):
    ledger = verify()
    selected = [s for s in ledger['scenarios'] if s['sample'] == sample]
    assert len(selected) == 10
    paths = [ROOT/('reports/strategy-experiment-028-'+s['id']+'.json') for s in selected]
    assert not any(p.exists() for p in paths), 'Frozen output exists; no rerun'
    ds = ledger['datasets'][sample]
    sims = [(s, Experiment028Simulator(Config(**s['config']), s['candidate'], ds['evaluation_start_ms'])) for s in selected]
    started = time.monotonic()
    for count, tick in enumerate(read_ticks(ROOT/SAMPLES[sample][0]), 1):
        for _, sim in sims:
            sim.step_tick(tick)
        if count % 250000 == 0:
            print(json.dumps(dict(sample=sample, ticks=count, total=ds['ticks'], elapsed_seconds=round(time.monotonic()-started, 1))), flush=True)
    assert count == ds['ticks']
    for (s, sim), path in zip(sims, paths, strict=True):
        sim.finish()
        metrics = sim.metrics()
        assert metrics['ticks_processed'] == ds['ticks'] and metrics['warmup_hours'] == 201
        curve = [p for p in sim.curve if int(datetime.fromisoformat(p['time']).timestamp()*1000) >= ds['evaluation_start_ms']]
        report = dict(status='exploratory_reused_development_not_validation', scenario=s['id'],
            ledger_sha256=sha(LEDGER), metrics=metrics, trades=sim.trades, equity=curve,
            flat_account_decisions=sim.decision_log, fill_lineage=sim.fill_lineage,
            execution_metric_version=sim.execution_metric_version, strategy_experiment_version=sim.strategy_experiment_version,
            annual_eligible=False, orders_available=False)
        reconcile(report, s['config'], ds['evaluation_start_ms'])
        report['control_parity'] = control_parity(report) if s['candidate'] in ('C00', 'C02', 'C04') else None
        write(path, report)
        print(json.dumps(dict(scenario=s['id'], trades=metrics['closed_trades'], net_pnl=metrics['net_pnl'])), flush=True)


def summarize():
    ledger = verify()
    rows = []
    for s, name in zip(ledger['scenarios'], ledger['expected_outputs'], strict=True):
        report = sealed(ROOT/name)
        assert report['ledger_sha256'] == sha(LEDGER) and report['scenario'] == s['id']
        reconcile(report, s['config'], ledger['datasets'][s['sample']]['evaluation_start_ms'])
        if s['candidate'] in ('C00', 'C02', 'C04'):
            assert report['control_parity']['passed'] and control_parity(report)['passed']
        m = report['metrics']
        rows.append(dict(scenario=s['id'], sample=s['sample'], candidate=s['candidate'], cost=s['cost'],
            report_sha256=sha(ROOT/name), net_pnl=m['net_pnl'], net_return=m['net_return'],
            trades=m['closed_trades'], net_expectancy=m['net_pnl']/m['closed_trades'] if m['closed_trades'] else None,
            win_rate=m['win_rate'], corrected_tick_drawdown=m['max_tick_drawdown'], exposure=m['bar_exposure'],
            gross_pnl=sum(t['gross_pnl'] for t in report['trades']), commission=m['commission'], swap=m['swap'],
            decision_reasons=dict(Counter(d['reason'] for d in report['flat_account_decisions'])),
            control_parity=report['control_parity']))
    write(ROOT/'reports/strategy-experiment-028-summary.json', dict(kind='all_30_development_scenarios_028',
        ledger_sha256=sha(LEDGER), scenarios=rows, cash_reference_net_pnl=0,
        independent_monthly_capital=True, not_independent_trials=True,
        selection_authorized=False, annual_eligible=False, orders_available=False))
    fields = ('scenario', 'trades', 'net_pnl', 'net_return', 'net_expectancy', 'win_rate',
              'corrected_tick_drawdown', 'exposure', 'gross_pnl', 'commission', 'swap')
    with (ROOT/'reports/strategy-experiment-028-table.csv').open('x', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows({k: r[k] for k in fields} for r in rows)
    print(json.dumps(dict(completed_scenarios=30, control_parity_passes=18)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('freeze', 'verify', 'run', 'summary'))
    parser.add_argument('sample', nargs='?', choices=tuple(SAMPLES))
    args = parser.parse_args()
    if args.action == 'run':
        if args.sample is None:
            parser.error('run requires one declared sample')
        try:
            run(args.sample)
        except Exception as exc:
            write(ROOT/f'reports/strategy-experiment-028-{args.sample}-failure.json',
                  dict(kind='preserved_sample_replay_failure_028', sample=args.sample,
                       error_type=type(exc).__name__, message=str(exc), orders_available=False))
            raise
    else:
        {'freeze': freeze, 'verify': verify, 'summary': summarize}[args.action]()
