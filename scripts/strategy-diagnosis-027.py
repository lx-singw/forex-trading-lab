"""Versioned preservation preflight and frozen-report diagnosis; no quote reads."""
import argparse
import csv
import hashlib
import json
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from forex_demo_lab.strategy_diagnosis import diagnose, paired_paths

PRIOR = ROOT/'reports/evidence-026-final-source.json'
LEDGER = ROOT/'reports/strategy-diagnosis-027-ledger.json'
OUTPUT = ROOT/'reports/strategy-diagnosis-027.json'
HANDOFF = {'README.md', 'docs/CONTEXT.md', 'docs/PLAN.md', 'docs/VERIFICATION.md'}
GROUPS = ('source_bindings', 'report_bindings', 'synthetic_input_bindings',
          'access_evidence_bindings', 'market_input_bindings', 'comparison_input_bindings')
SAMPLES = {'january': ('data/research-004-january-mt5', 'reports/research-quality-004.json'),
           'april': ('data/research-005-april-new-york', 'reports/research-quality-005.json'),
           'july': ('data/research-004-july-new-york', 'reports/research-quality-004.json')}
SOURCES = ('docs/STRATEGY-DIAGNOSIS-027-PLAN.md', 'docs/STRATEGY-DIAGNOSIS-027-PROTOCOL.md',
           'src/forex_demo_lab/strategy_diagnosis.py', 'tests/test_strategy_diagnosis.py',
           'scripts/strategy-diagnosis-027.py', 'scripts/check-strategy-diagnosis-027.py')


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


def prior_verify(allow_handoff=False):
    assert sha(PRIOR) == 'e61ceb03c4262e56c915d2f47f6d0c04fe19147718a7bc21d7d5f04ef29e80ca'
    assert sha(PRIOR) == PRIOR.with_suffix('.sha256').read_text().strip()
    prior = load(PRIOR)
    bindings, changes = {}, {}
    for group in GROUPS:
        for name, expected in prior[group].items():
            assert name not in bindings
            current = sha(ROOT/name)
            if current != expected:
                assert allow_handoff and group == 'source_bindings' and name in HANDOFF, name
                changes[name] = dict(previous=expected, current=current)
            bindings[name] = expected
    external = prior['archive_external_bindings']
    assert len(external) == prior['external_bindings_verified']
    assert all(bindings[n] == h for n, h in external.items())
    assert sha(PRIOR.with_suffix('.zip')) == prior['archive_sha256']
    with zipfile.ZipFile(PRIOR.with_suffix('.zip')) as z:
        assert z.testzip() is None
        assert len(z.infolist()) == prior['archive_members_verified']
        assert set(z.namelist()) == set(bindings)-set(external)
        for name in z.namelist():
            assert hashlib.sha256(z.read(name)).hexdigest() == bindings[name], name
    return dict(bindings_verified=len(bindings), archived_members_verified=len(bindings)-len(external),
                external_bindings_verified=len(external), allowed_handoff_changes=changes)


def freeze():
    verified = prior_verify()
    original = load(ROOT/'reports/comparison-008-ledger.json')
    summary = load(ROOT/'reports/comparison-008-summary.json')
    bindings = {}
    def bind(name, expected=None):
        digest = sha(ROOT/name)
        if expected is not None:
            assert digest == expected, name
        bindings[name] = digest
        return digest
    for name in SOURCES:
        bind(name)
    for name in ('reports/comparison-008-ledger.json', 'reports/comparison-008-summary.json',
                 'reports/comparison-008-audit.json', 'reports/baseline-diagnosis-008.json',
                 'reports/evidence-026-final-source.json', 'reports/evidence-026-final-source.sha256'):
        bind(name)
    bind('config/research-candidates-008.json', original['spec_sha256'])
    bind('docs/COMPARISON-008-PLAN.md', original['protocol_sha256'])
    bind('scripts/compare-strategies-008.py', original['runner_sha256'])
    bind('reports/comparison-008-source.zip', original['archive_sha256'])
    archived = {}
    with zipfile.ZipFile(ROOT/'reports/comparison-008-source.zip') as z:
        assert z.testzip() is None and len(z.infolist()) == len(set(z.namelist()))
        for name in z.namelist():
            digest = hashlib.sha256(z.read(name)).hexdigest()
            bind(name, digest)
            archived[name] = digest
        h = hashlib.sha256()
        for name in sorted(n for n in z.namelist() if n.startswith('src/forex_demo_lab/') and n.endswith('.py')):
            h.update(Path(name).name.encode())
            h.update(z.read(name))
        assert h.hexdigest() == original['code_sha256']
    for sample, (folder, review_name) in SAMPLES.items():
        ds = original['datasets'][sample]
        bind(folder+'/provenance.json', ds['provenance_sha256'])
        bind(folder+'/ticks.csv.gz', ds['data_sha256'])
        bind(review_name, ds['quality_sha256'])
        provenance = load(ROOT/folder/'provenance.json')
        assert provenance['data_sha256'] == ds['data_sha256']
        quality = load(ROOT/review_name)
        matches = [d for d in quality['datasets'] if d.get('provenance_sha256') == ds['provenance_sha256']]
        assert quality['performance_evaluation_ready'] is True and len(matches) == 1
        assert matches[0]['status'] == 'ready_for_development_research'
    ledger_hash = sha(ROOT/'reports/comparison-008-ledger.json')
    assert summary['ledger_sha256'] == ledger_hash
    rows = {r['scenario']: r for r in summary['scenarios']}
    assert len(rows) == len(original['scenarios']) == 30
    for scenario in original['scenarios']:
        name = 'reports/comparison-008-'+scenario['id']+'.json'
        bind(name, rows[scenario['id']]['report_sha256'])
        report = load(ROOT/name)
        assert report['scenario'] == scenario['id'] and report['ledger_sha256'] == ledger_hash
        assert report['metrics'] == rows[scenario['id']]['metrics']
        assert report['demo_execution_ready'] is False
    write(LEDGER, dict(kind='frozen_report_diagnosis_027', bindings=bindings,
        archived_original_members=archived, prior_snapshot_verification=verified,
        scenarios=original['scenarios'], datasets=original['datasets'],
        quote_rows_read=0, network_requests=0, new_strategy_runs=0,
        annual_eligible=False, orders_available=False, data_role='reused_2024_development'))
    print(json.dumps(dict(frozen=True, bindings=len(bindings), original_archive_members=len(archived), scenarios=30)))


def verify():
    ledger = load(LEDGER)
    assert sha(LEDGER) == LEDGER.with_suffix('.sha256').read_text().strip()
    for name, expected in ledger['bindings'].items():
        assert sha(ROOT/name) == expected, name
    return ledger


def run():
    ledger = verify()
    results = []
    for s in ledger['scenarios']:
        report = load(ROOT/('reports/comparison-008-'+s['id']+'.json'))
        result = diagnose(report, s['config'], s['candidate'], ledger['datasets'][s['sample']]['evaluation_start_ms'])
        result.update(sample=s['sample'], cost=s['cost'])
        results.append(result)
    by_id = {r['scenario']: r for r in results}
    pairs = [paired_paths(by_id[f'{sample}-{c}-base'], by_id[f'{sample}-{c}-adverse'])
             for sample in SAMPLES for c in ('C00', 'C01', 'C02', 'C03', 'C04')]
    write(OUTPUT, dict(kind='descriptive_frozen_entry_risk_diagnosis_027',
        ledger_sha256=sha(LEDGER), scenarios=results, cost_path_comparisons=pairs,
        not_new_performance=True, not_independent_trials=True, quote_rows_read=0,
        new_strategy_runs=0, annual_eligible=False, orders_available=False))
    fields = ('scenario', 'decisions', 'signal_count', 'trades', 'gross_pnl', 'net_pnl',
              'commission', 'swap', 'mean_net_r', 'longest_loss_streak',
              'rapid_reentries', 'rapid_after_losses', 'reported_spread_rejections',
              'stop_overshoot_dollars', 'mean_holding_hours')
    with (ROOT/'reports/strategy-diagnosis-027-table.csv').open('x', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows({key: row[key] for key in fields} for row in results)
    print(json.dumps(dict(scenarios=len(results), trades=sum(r['trades'] for r in results),
                         decisions=sum(r['decisions'] for r in results), quote_rows_read=0)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('freeze', 'verify', 'run'))
    action = parser.parse_args().action
    {'freeze': freeze, 'verify': verify, 'run': run}[action]()
