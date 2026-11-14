"""Review frozen path diagnostics and preserve the next declared research step."""
import argparse
import hashlib
import json
from pathlib import Path
import runpy
import zipfile
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
API = runpy.run_path(str(ROOT/'scripts/trade-path-029.py'))
sha, write, sealed = API['sha'], API['write'], API['sealed']
REVIEW = ROOT/'reports/trade-path-029-review.json'
FINAL = ROOT/'reports/trade-path-029-final-source.json'


def review():
    previous = API['prior_verify'](allow_handoff=True)
    ledger = API['verify']()
    checks = sealed(ROOT/'reports/trade-path-029-checks.json')
    summary = sealed(ROOT/'reports/trade-path-029-summary.json')
    tests = sealed(ROOT/'reports/trade-path-029-tests.json')
    assert checks['passed'] and tests['passed']
    assert checks['ledger_sha256'] == summary['ledger_sha256'] == sha(API['LEDGER'])
    assert checks['summary_sha256'] == sha(ROOT/'reports/trade-path-029-summary.json')
    assert checks['table_sha256'] == sha(ROOT/'reports/trade-path-029-table.csv')
    assert checks['endpoints_checked'] == ledger['trades_expected'] == 266
    assert checks['preselected_full_paths_checked'] == 60
    assert tests['tests_run'] == tests['tests_passed'] == 368 and tests['new_tests'] == 12
    assert len(summary['scenarios']) == 30
    assert not list(ROOT.glob('reports/trade-path-029-*-failure.json'))
    outputs = {}
    for sample in API['API']['SAMPLES']:
        path = ROOT/f'reports/trade-path-029-{sample}.json'
        data = sealed(path)
        assert data['ledger_sha256'] == sha(API['LEDGER'])
        assert data['source_ticks_read'] == checks['sample_source_ticks_checked'][sample] == ledger['datasets'][sample]['ticks']
        outputs[path.relative_to(ROOT).as_posix()] = sha(path)
    for row in summary['scenarios']:
        assert 0 <= row['stops_prior_one_r'] <= row['stops_prior_half_r'] <= row['stops_prior_positive'] <= row['stops'] <= row['trades']
        old = sealed(ROOT/f'reports/strategy-experiment-028-{row["scenario"]}.json')
        assert abs(row['net_pnl']-old['metrics']['net_pnl']) <= 1e-8
    documents = ('docs/TRADE-PATH-029-RESULTS.md', 'docs/EXIT-EXPERIMENT-030-PLAN.md',
                 'scripts/finalize-trade-path-029.py')
    for name in API['API']['HANDOFF']:
        assert 'TRADE-PATH-029-RESULTS.md' in (ROOT/name).read_text(), name
    assert 'not executed' in (ROOT/documents[1]).read_text()
    write(REVIEW, dict(kind='post_independent_path_review_029', passed=True,
        prior_snapshot_verification=previous, input_bindings_verified=len(ledger['bindings']),
        output_bindings=outputs, documentation_bindings={name: sha(ROOT/name) for name in documents},
        endpoints_checked=266, witnesses_checked=checks['witnesses_checked'],
        preselected_full_paths_checked=60, software_tests_passed=368,
        new_strategy_runs=0, annual_eligible=False, market_profitability_established=False,
        orders_available=False, next_plan=documents[1], next_plan_executed=False))
    print(json.dumps(dict(passed=True, endpoints=266, full_paths=60, tests=368)))


def snapshot():
    checked = sealed(REVIEW)
    assert checked['passed']
    API['prior_verify'](allow_handoff=True)
    ledger = API['verify']()
    for name, expected in (checked['documentation_bindings']|checked['output_bindings']).items():
        assert sha(ROOT/name) == expected, name
    prior_path = API['PRIOR']
    prior = sealed(prior_path)
    groups = {g: dict(v) for g, v in prior.items() if g.endswith('_bindings') and g != 'archive_external_bindings'}
    for name in API['API']['HANDOFF']:
        groups['source_bindings'][name] = sha(ROOT/name)
    for pattern in ('docs/*029*.md', 'docs/EXIT-EXPERIMENT-030-PLAN.md', 'scripts/*029*.py',
                    'src/forex_demo_lab/trade_path.py', 'tests/test_trade_path.py'):
        for path in ROOT.glob(pattern):
            groups['source_bindings'][path.relative_to(ROOT).as_posix()] = sha(path)
    for path in ROOT.glob('reports/trade-path-029*'):
        assert 'final-source' not in path.name
        groups['report_bindings'][path.relative_to(ROOT).as_posix()] = sha(path)
    for suffix in ('.json', '.sha256', '.zip'):
        path = prior_path.with_suffix(suffix)
        groups['report_bindings'][path.relative_to(ROOT).as_posix()] = sha(path)
    already = {n: h for values in groups.values() for n, h in values.items()}
    groups['path_input_bindings'] = {}
    for name, expected in ledger['bindings'].items():
        if name in already:
            assert already[name] == expected, name
        else:
            groups['path_input_bindings'][name] = expected
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
    write(FINAL, dict(kind='post_trade_path_source_snapshot_029', **groups,
        archive_external_bindings=external, archive_members_verified=len(internal), external_bindings_verified=len(external),
        archive_sha256=sha(archive_path), archive_bytes=archive_path.stat().st_size,
        snapshot_scope='Sources/reports/small fixtures archived; prior ZIPs, cached market gzip/ZIPs and timezone files externally hash-bound, verified and required for rerun',
        previous_snapshot=prior_path.relative_to(ROOT).as_posix(), previous_snapshot_sha256=sha(prior_path),
        completed_utc=datetime.now(timezone.utc).isoformat(), software_tests_passed=368,
        endpoints_checked=266, preselected_full_paths_checked=60, new_strategy_runs=0,
        annual_eligible=False, market_profitability_established=False, orders_available=False,
        next_plan=checked['next_plan'], next_plan_executed=False))
    print(json.dumps(dict(counts={g: len(v) for g, v in groups.items()}, archived_members=len(internal),
                         external_bindings=len(external), manifest_sha256=sha(FINAL))))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('review', 'snapshot'))
    {'review': review, 'snapshot': snapshot}[parser.parse_args().action]()
