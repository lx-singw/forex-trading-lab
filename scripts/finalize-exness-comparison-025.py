"""Review comparisons and snapshot sources; bind large cached inputs externally."""
import argparse
import hashlib
import json
import runpy
import sys
import zipfile
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
RUNNER=runpy.run_path(str(ROOT/'scripts/exness-comparison-025.py'))
sha=RUNNER['digest']
write=RUNNER['write']
PRIOR=ROOT/'reports/exness-024-final-source.json'
REVIEW=ROOT/'reports/exness-comparison-025-final-review.json'
FINAL=ROOT/'reports/exness-comparison-025-final-source.json'


def sealed(path):
    assert sha(path)==path.with_suffix('.sha256').read_text().strip()
    return json.loads(path.read_text())


def review():
    dependencies=RUNNER['preflight'](allow_handoff=True)
    RUNNER['verify']()
    assert runpy.run_path(str(ROOT/'scripts/derive-exness-comparison-025b.py'))['verify']()
    original=sealed(ROOT/'reports/exness-comparison-025-review.json')
    checked=sealed(ROOT/'reports/exness-comparison-025b-checks.json')
    failed=sealed(ROOT/'reports/exness-comparison-025-check-attempt.json')
    assert failed['original_check_completed'] is False
    assert checked['passed'] and checked['review_sha256']==sha(ROOT/'reports/exness-comparison-025-review.json')
    assert checked['supplemental_ledger_sha256']==sha(ROOT/'reports/exness-comparison-025b-ledger.json')
    assert original['questions']==checked['questions']
    assert sha(ROOT/original['lineage_path'])==original['lineage_sha256']==checked['lineage_sha256']
    assert len(original['windows'])==2 and len(checked['sources'])==8
    assert all(row['matched'] for row in checked['sources'])
    records=sum(row['selected_records'] for row in checked['sources'])
    assert records==checked['lineage_records_checked']==20069
    assert checked['aggregate_bins_checked']==320 and checked['pairwise_hour_distances_checked']==30
    assert all(original[key] is False for key in ('annual_eligible','absolute_utc_certified',
               'historical_sessions_certified','upstream_independence_verified','performance_evaluation_ready',
               'market_profitability_established','orders_available'))
    tests=json.loads((ROOT/'reports/exness-comparison-025-tests.json').read_text())
    assert tests['tests_passed']==330 and tests['new_tests']==12
    output=dict(kind='post_independent_coverage_comparison_review_025',passed=True,
                dependency_verification=dependencies,original_check_failure_preserved=True,
                checker_exact_derivation=True,selected_original_events_checked=records,
                aggregate_bins_checked=320,pairwise_hour_distances_checked=30,
                questions=checked['questions'],software_tests_passed=330,
                annual_eligible=False,performance_evaluation_ready=False,
                market_profitability_established=False,orders_available=False,
                network_requests=0,next_evidence_review_executed=False)
    write(REVIEW,output)
    print(json.dumps(dict(passed=True,selected_original_events_checked=records,
                          software_tests_passed=330,questions=checked['questions'])))


def snapshot():
    review=sealed(REVIEW)
    assert review['passed']
    RUNNER['prior_check'](allow_handoff=True)
    prior=json.loads(PRIOR.read_text())
    groups={group:dict(prior[group]) for group in RUNNER['PRIOR_GROUPS']}
    for name in RUNNER['HANDOFF']:groups['source_bindings'][name]=sha(ROOT/name)
    for pattern in ('scripts/*025*.py','src/forex_demo_lab/coverage_comparison.py',
                    'tests/test_coverage_comparison*.py','docs/*025*.md','docs/EXNESS-EVIDENCE-026-PLAN.md'):
        for path in ROOT.glob(pattern):groups['source_bindings'][path.relative_to(ROOT).as_posix()]=sha(path)
    for path in ROOT.glob('reports/exness-comparison-025*'):
        assert 'final-source' not in path.name
        groups['report_bindings'][path.relative_to(ROOT).as_posix()]=sha(path)
    for suffix in ('.json','.sha256','.zip'):
        path=PRIOR.with_suffix(suffix)
        groups['report_bindings'][path.relative_to(ROOT).as_posix()]=sha(path)
    already={name:expected for bindings in groups.values() for name,expected in bindings.items()}
    ledger=sealed(ROOT/'reports/exness-comparison-025-ledger.json')
    supplemental=sealed(ROOT/'reports/exness-comparison-025b-ledger.json')
    groups['comparison_input_bindings']={}
    for name,expected in (ledger['bindings']|supplemental['bindings']).items():
        if name in already:assert already[name]==expected,name
        else:groups['comparison_input_bindings'][name]=expected
    bindings={name:expected for group in groups.values() for name,expected in group.items()}
    assert len(bindings)==sum(map(len,groups.values()))
    # Keep existing large quote inputs and earlier complete source ZIPs in place.
    # The manifest binds them explicitly; this new archive is not self-contained.
    external={name:expected for name,expected in bindings.items()
              if name.startswith('/') or name.endswith('.zip')
              or (name.startswith('data/') and name.endswith('.gz') and 'synthetic' not in name and 'walk-forward' not in name)}
    internal={name:expected for name,expected in bindings.items() if name not in external}
    archive_path=FINAL.with_suffix('.zip')
    for name,expected in bindings.items():assert sha(ROOT/name)==expected,name
    with zipfile.ZipFile(archive_path,'x',compression=zipfile.ZIP_DEFLATED) as archive:
        for name in sorted(internal):archive.write(ROOT/name,name)
    with zipfile.ZipFile(archive_path) as archive:
        assert archive.testzip() is None and len(archive.infolist())==len(internal)
        for entry in archive.infolist():assert hashlib.sha256(archive.read(entry)).hexdigest()==internal[entry.filename]
    output=dict(kind='post_review_fixed_coverage_snapshot_025',**groups,
                archive_external_bindings=external,archive_members_verified=len(internal),
                external_bindings_verified=len(external),archive_sha256=sha(archive_path),
                archive_bytes=archive_path.stat().st_size,
                snapshot_scope='Source/reports/small fixtures in ZIP; cached market ZIP/gzip inputs, timezone files and earlier source ZIPs externally hash-bound and verified; requires cached files for rerun',
                previous_snapshot=PRIOR.relative_to(ROOT).as_posix(),previous_snapshot_sha256=sha(PRIOR),
                completed_utc=datetime.now(timezone.utc).isoformat(),software_tests_passed=330,
                selected_original_events_checked=20069,network_requests=0,
                original_failure_preserved=True,annual_eligible=False,performance_evaluation_ready=False,
                market_profitability_established=False,orders_available=False,
                next_evidence_review_plan='docs/EXNESS-EVIDENCE-026-PLAN.md',next_evidence_review_executed=False)
    write(FINAL,output)
    print(json.dumps(dict(counts={g:len(v) for g,v in groups.items()},
                          archived_members=len(internal),external_bindings_verified=len(external),
                          manifest_sha256=sha(FINAL))))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('action',choices=('review','snapshot'))
    action=parser.parse_args().action
    {'review':review,'snapshot':snapshot}[action]()
