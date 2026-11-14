"""Review the fixed batch and seal sources; no parameter selection or new replay."""
import argparse
import hashlib
import json
import runpy
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API = runpy.run_path(str(ROOT/'scripts/strategy-experiment-028.py'))
sha, write, sealed = API['sha'], API['write'], API['sealed']
REVIEW = ROOT/'reports/strategy-experiment-028-review.json'
FINAL = ROOT/'reports/strategy-experiment-028-final-source.json'


def entry_comparisons(ledger):
    comparisons = []
    for sample in API['SAMPLES']:
        for cost in ('base', 'adverse'):
            for new, control in (('C05', 'C04'), ('C06', 'C02')):
                a = sealed(ROOT/f'reports/strategy-experiment-028-{sample}-{control}-{cost}.json')
                b = sealed(ROOT/f'reports/strategy-experiment-028-{sample}-{new}-{cost}.json')
                aa = {(t['opened'], t['side']) for t in a['trades']}
                bb = {(t['opened'], t['side']) for t in b['trades']}
                comparisons.append(dict(sample=sample, cost=cost, challenger=new, control=control,
                    shared_entries=len(aa&bb), control_only_entries=len(aa-bb), new_only_entries=len(bb-aa),
                    net_pnl_difference=b['metrics']['net_pnl']-a['metrics']['net_pnl']))
    return comparisons


def review():
    prior = API['prior_verify'](allow_handoff=True)
    ledger = API['verify']()
    summary = sealed(ROOT/'reports/strategy-experiment-028-summary.json')
    checks = sealed(ROOT/'reports/strategy-experiment-028-checks.json')
    tests = sealed(ROOT/'reports/strategy-experiment-028-tests.json')
    synthetic = sealed(ROOT/'reports/strategy-experiment-028-synthetic-checks.json')
    assert checks['passed'] and tests['passed'] and synthetic['passed']
    assert checks['summary_sha256'] == sha(ROOT/'reports/strategy-experiment-028-summary.json')
    assert checks['ledger_sha256'] == summary['ledger_sha256'] == sha(API['LEDGER'])
    assert len(summary['scenarios']) == checks['scenarios_checked'] == 30
    assert checks['controls_matching_original'] == 18
    assert tests['tests_run'] == tests['tests_passed'] == 356 and tests['new_tests'] == 14
    assert synthetic['cases_checked'] == 12
    assert sum(r['trades'] for r in summary['scenarios']) == checks['trades_checked']
    for sample, checked in checks['sample_checks'].items():
        assert checked['ticks_checked'] == ledger['datasets'][sample]['ticks']
    assert not list(ROOT.glob('reports/strategy-experiment-028-*-failure.json'))
    for s in ledger['scenarios']:
        r = sealed(ROOT/('reports/strategy-experiment-028-'+s['id']+'.json'))
        assert r['annual_eligible'] is r['orders_available'] is False
        if s['candidate'] in ('C00', 'C02', 'C04'):
            API['control_parity'](r)
    documents = ['docs/STRATEGY-EXPERIMENT-028-RESULTS.md', 'docs/TRADE-PATH-029-PLAN.md', 'scripts/finalize-strategy-experiment-028.py']
    for name in API['HANDOFF']:
        assert 'STRATEGY-EXPERIMENT-028-RESULTS.md' in (ROOT/name).read_text(), name
    write(REVIEW, dict(kind='post_independent_development_review_028', passed=True,
        prior_snapshot_verified=prior, input_bindings_verified=len(ledger['bindings']),
        scenarios_checked=30, controls_matching_original=18, trades_checked=checks['trades_checked'],
        sample_checks=checks['sample_checks'], entry_comparisons=entry_comparisons(ledger),
        software_tests_passed=356, synthetic_checker_cases=12,
        documentation_bindings={name: sha(ROOT/name) for name in documents},
        table_sha256=sha(ROOT/'reports/strategy-experiment-028-table.csv'),
        annual_eligible=False, market_profitability_established=False,
        selection_authorized=False, orders_available=False,
        next_plan='docs/TRADE-PATH-029-PLAN.md', next_plan_executed=False))
    print(json.dumps(dict(passed=True, controls=18, tests_passed=356, trades=checks['trades_checked'])))


def snapshot():
    checked = sealed(REVIEW)
    assert checked['passed']
    API['prior_verify'](allow_handoff=True)
    ledger = API['verify']()
    for name, expected in checked['documentation_bindings'].items():
        assert sha(ROOT/name) == expected, name
    prior_path = API['PRIOR']
    prior = sealed(prior_path)
    groups = {g: dict(v) for g, v in prior.items() if g.endswith('_bindings') and g != 'archive_external_bindings'}
    for name in API['HANDOFF']:
        groups['source_bindings'][name] = sha(ROOT/name)
    for pattern in ('docs/*028*.md', 'docs/TRADE-PATH-029-PLAN.md', 'config/research-candidates-028.json', 'scripts/*028*.py',
                    'src/forex_demo_lab/strategy_experiment_028.py', 'tests/test_strategy_experiment_028.py'):
        for path in ROOT.glob(pattern):
            groups['source_bindings'][path.relative_to(ROOT).as_posix()] = sha(path)
    for path in ROOT.glob('reports/strategy-experiment-028*'):
        assert 'final-source' not in path.name
        groups['report_bindings'][path.relative_to(ROOT).as_posix()] = sha(path)
    for suffix in ('.json', '.sha256', '.zip'):
        path = prior_path.with_suffix(suffix)
        groups['report_bindings'][path.relative_to(ROOT).as_posix()] = sha(path)
    already = {n: h for values in groups.values() for n, h in values.items()}
    groups['experiment_input_bindings'] = {}
    for name, expected in ledger['bindings'].items():
        if name in already:
            assert already[name] == expected, name
        else:
            groups['experiment_input_bindings'][name] = expected
    bindings = {n: h for values in groups.values() for n, h in values.items()}
    assert len(bindings) == sum(map(len, groups.values()))
    external = {n: h for n, h in bindings.items() if n.startswith('/') or n.endswith('.zip') or
                (n.startswith('data/') and n.endswith('.gz') and 'synthetic' not in n and 'walk-forward' not in n)}
    internal = {n: h for n, h in bindings.items() if n not in external}
    for name, expected in bindings.items():
        assert sha(ROOT/name) == expected, name
    archive_path = FINAL.with_suffix('.zip')
    with zipfile.ZipFile(archive_path, 'x', compression=zipfile.ZIP_DEFLATED) as z:
        for name in sorted(internal):
            z.write(ROOT/name, name)
    with zipfile.ZipFile(archive_path) as z:
        assert z.testzip() is None and len(z.infolist()) == len(internal)
        assert set(z.namelist()) == set(internal)
        for name in z.namelist():
            assert hashlib.sha256(z.read(name)).hexdigest() == internal[name], name
    write(FINAL, dict(kind='post_development_experiment_snapshot_028', **groups,
        archive_external_bindings=external, archive_members_verified=len(internal),
        external_bindings_verified=len(external), archive_sha256=sha(archive_path), archive_bytes=archive_path.stat().st_size,
        snapshot_scope='Source/reports/small fixtures archived; prior ZIPs, market gzip/ZIPs and timezone files externally hash-bound, verified and required for rerun',
        previous_snapshot=prior_path.relative_to(ROOT).as_posix(), previous_snapshot_sha256=sha(prior_path),
        completed_utc=datetime.now(timezone.utc).isoformat(), software_tests_passed=356,
        scenarios_checked=30, controls_matching_original=18,
        annual_eligible=False, market_profitability_established=False, selection_authorized=False, orders_available=False,
        next_plan=checked['next_plan'], next_plan_executed=False))
    print(json.dumps(dict(counts={g: len(v) for g, v in groups.items()}, archive_members=len(internal),
                         external_bindings=len(external), manifest_sha256=sha(FINAL))))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('review', 'snapshot'))
    {'review': review, 'snapshot': snapshot}[parser.parse_args().action]()
