"""Review all frozen-report diagnosis outputs and preserve an exact source snapshot."""
import argparse
import hashlib
import json
import runpy
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API = runpy.run_path(str(ROOT/'scripts/strategy-diagnosis-027.py'))
sha, write = API['sha'], API['write']
REVIEW = ROOT/'reports/strategy-diagnosis-027-review.json'
FINAL = ROOT/'reports/strategy-diagnosis-027-final-source.json'


def sealed(path):
    assert sha(path) == path.with_suffix('.sha256').read_text().strip(), path
    return json.loads(path.read_text())


def review():
    previous = API['prior_verify'](allow_handoff=True)
    ledger = API['verify']()
    output = sealed(ROOT/'reports/strategy-diagnosis-027.json')
    checks = sealed(ROOT/'reports/strategy-diagnosis-027-checks.json')
    tests = sealed(ROOT/'reports/strategy-diagnosis-027-tests.json')
    assert checks['passed'] and tests['passed']
    assert checks['output_sha256'] == sha(ROOT/'reports/strategy-diagnosis-027.json')
    assert checks['table_sha256'] == sha(ROOT/'reports/strategy-diagnosis-027-table.csv')
    assert checks['ledger_sha256'] == tests['ledger_sha256'] == output['ledger_sha256'] == sha(API['LEDGER'])
    assert tests['tests_run'] == tests['tests_passed'] == 342 and tests['new_tests'] == 12
    assert len(output['scenarios']) == checks['scenarios_checked'] == 30
    assert sum(r['trades'] for r in output['scenarios']) == checks['trades_checked'] == 245
    assert sum(r['decisions'] for r in output['scenarios']) == checks['decisions_checked'] == 5072
    assert all(r['match_counts'] == {'matched': r['trades']} for r in output['scenarios'])
    assert checks['future_log_withholding_checks'] == 245
    assert len(output['cost_path_comparisons']) == checks['cost_pairs_checked'] == 15
    assert sum(r['net_pnl'] < 0 for r in output['scenarios']) == 18
    assert sum(r['gross_pnl'] < 0 for r in output['scenarios']) == 16
    assert sum(r['gross_pnl'] > 0 and r['net_pnl'] < 0 for r in output['scenarios']) == 2
    assert all(r['net_pnl'] < 0 for r in output['scenarios'] if r['candidate'] == 'C02')
    assert all(p['net_pnl_difference'] < 0 for p in output['cost_path_comparisons'])
    assert output['quote_rows_read'] == output['new_strategy_runs'] == 0
    assert output['annual_eligible'] is output['orders_available'] is False
    for name in API['HANDOFF']:
        assert 'STRATEGY-EXPERIMENT-028-PLAN.md' in (ROOT/name).read_text(), name
    assert 'not executed' in (ROOT/'docs/STRATEGY-EXPERIMENT-028-PLAN.md').read_text()
    documents = ('docs/STRATEGY-DIAGNOSIS-027-RESULTS.md', 'docs/STRATEGY-EXPERIMENT-028-PLAN.md',
                 'scripts/test-strategy-diagnosis-027.py', 'scripts/finalize-strategy-diagnosis-027.py')
    write(REVIEW, dict(kind='post_independent_diagnosis_review_027', passed=True,
        previous_snapshot_verification=previous, input_bindings_verified=len(ledger['bindings']),
        original_archive_members_verified=len(ledger['archived_original_members']),
        scenarios_checked=30, trades_checked=245, decisions_checked=5072,
        future_log_withholding_checks=245, software_tests_passed=342,
        documentation_bindings={name: sha(ROOT/name) for name in documents},
        quote_rows_read=0, new_strategy_runs=0, network_requests=0,
        annual_eligible=False, market_profitability_established=False, orders_available=False,
        next_plan='docs/STRATEGY-EXPERIMENT-028-PLAN.md', next_plan_executed=False))
    print(json.dumps(dict(passed=True, scenarios=30, trades=245, tests_passed=342)))


def snapshot():
    checked = sealed(REVIEW)
    assert checked['passed']
    API['prior_verify'](allow_handoff=True)
    ledger = API['verify']()
    for name, expected in checked['documentation_bindings'].items():
        assert sha(ROOT/name) == expected, name
    prior_path = API['PRIOR']
    prior = sealed(prior_path)
    groups = {g: dict(prior[g]) for g in API['GROUPS']}
    for name in API['HANDOFF']:
        groups['source_bindings'][name] = sha(ROOT/name)
    for pattern in ('docs/*027*.md', 'docs/STRATEGY-EXPERIMENT-028-PLAN.md',
                    'scripts/*027*.py', 'src/forex_demo_lab/strategy_diagnosis.py',
                    'tests/test_strategy_diagnosis.py'):
        for path in ROOT.glob(pattern):
            groups['source_bindings'][path.relative_to(ROOT).as_posix()] = sha(path)
    for path in ROOT.glob('reports/strategy-diagnosis-027*'):
        assert 'final-source' not in path.name
        groups['report_bindings'][path.relative_to(ROOT).as_posix()] = sha(path)
    for suffix in ('.json', '.sha256', '.zip'):
        path = prior_path.with_suffix(suffix)
        groups['report_bindings'][path.relative_to(ROOT).as_posix()] = sha(path)
    already = {name: expected for group in groups.values() for name, expected in group.items()}
    groups['diagnostic_input_bindings'] = {}
    for name, expected in ledger['bindings'].items():
        if name in already:
            assert already[name] == expected, name
        else:
            groups['diagnostic_input_bindings'][name] = expected
    bindings = {name: expected for group in groups.values() for name, expected in group.items()}
    assert len(bindings) == sum(map(len, groups.values()))
    external = {name: expected for name, expected in bindings.items()
                if name.startswith('/') or name.endswith('.zip') or
                (name.startswith('data/') and name.endswith('.gz') and
                 'synthetic' not in name and 'walk-forward' not in name)}
    internal = {name: expected for name, expected in bindings.items() if name not in external}
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
    write(FINAL, dict(kind='post_diagnosis_source_snapshot_027', **groups,
        archive_external_bindings=external, archive_members_verified=len(internal),
        external_bindings_verified=len(external), archive_sha256=sha(archive_path),
        archive_bytes=archive_path.stat().st_size,
        snapshot_scope='Source/reports/small fixtures in ZIP; prior ZIPs, cached market gzip/ZIPs and timezone files externally hash-bound, verified and required for rerun',
        previous_snapshot=prior_path.relative_to(ROOT).as_posix(), previous_snapshot_sha256=sha(prior_path),
        completed_utc=datetime.now(timezone.utc).isoformat(), software_tests_passed=342,
        scenarios_checked=30, trades_checked=245, decisions_checked=5072,
        quote_rows_read=0, new_strategy_runs=0, annual_eligible=False,
        market_profitability_established=False, orders_available=False,
        next_plan=checked['next_plan'], next_plan_executed=False))
    print(json.dumps(dict(counts={g: len(v) for g, v in groups.items()},
        archive_members=len(internal), external_bindings=len(external), manifest_sha256=sha(FINAL))))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('review', 'snapshot'))
    {'review': review, 'snapshot': snapshot}[parser.parse_args().action]()
