"""Seal the bounded document review; no requests, quotes or strategy evaluation."""
import argparse
import hashlib
import json
import re
import runpy
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEPENDENCY = runpy.run_path(str(ROOT / 'scripts/evidence-026.py'))
sha, write = DEPENDENCY['sha'], DEPENDENCY['write']
PRIOR = DEPENDENCY['PRIOR']
REVIEW = ROOT / 'reports/evidence-026-review.json'
FINAL = ROOT / 'reports/evidence-026-final-source.json'
NEW_SOURCE = (
    'docs/EXNESS-EVIDENCE-026-DISCOVERY.md',
    'docs/EXNESS-EVIDENCE-026-RESULTS.md',
    'docs/STRATEGY-DIAGNOSIS-027-PLAN.md',
    'scripts/evidence-026.py', 'scripts/finalize-evidence-026.py',
)
NEW_REPORT = ('reports/evidence-026-notes.json',
              'reports/evidence-026-primary-resolutions.json')


def sealed(path):
    assert sha(path) == path.with_suffix('.sha256').read_text().strip(), path
    return json.loads(path.read_text())


def review():
    previous = DEPENDENCY['verify_previous'](allow_handoff=True)
    preflight = sealed(ROOT / 'reports/evidence-026-preflight.json')
    assert preflight['passed']
    for name, expected in preflight['bindings'].items():
        assert sha(ROOT / name) == expected, name
    notes = json.loads((ROOT / NEW_REPORT[0]).read_text())
    resolved = json.loads((ROOT / NEW_REPORT[1]).read_text())
    declaration = (ROOT / 'docs/EXNESS-EVIDENCE-026-DISCOVERY.md').read_text()
    queries = re.findall(r'^\d+\. `(site:.*)`$', declaration, re.M)
    urls = re.findall(r'^\d+\. (https://\S+)$', declaration, re.M)
    assert len(queries) == 6 and notes['search_queries'] == queries
    assert len(urls) == 10
    assert [r['slot'] for r in resolved['resolutions']] == [11, 12]
    urls += [r['url'] for r in resolved['resolutions']]
    rows = notes['sources']
    assert len(rows) == 12 and len(set(urls)) == 12
    assert [r['slot'] for r in rows] == list(range(1, 13))
    assert [r['url'] for r in rows] == urls
    assert [r['slot'] for r in rows if r['status'] == 'failed'] == [6, 11]
    assert all(r['status'] in ('opened', 'failed') for r in rows)
    assert all(r.get('failure') for r in rows if r['status'] == 'failed')
    assert all(r['target_limit'] and 'content_date' in r for r in rows)
    assert len(notes['finds']) == 8
    assert [(r['source_slot'], r['pattern']) for r in notes['finds']] == [
        (3, 'Timestamp'), (4, 'GMT'), (4, '2026'), (8, 'Published'),
        (8, 'UTC'), (7, 'Legal documents'), (10, 'commission'), (10, 'trading hours')]
    assert notes['budget_used'] == dict(search_queries=6, primary_opens=12,
        primary_successes=10, primary_failures=2, finds=8, archive_snapshot_opens=0)
    assert notes['archive_snapshots'] == resolved['archive_snapshots_resolved'] == []
    assert notes['actions'] and all(value == 0 for value in notes['actions'].values())
    for flag in ('annual_eligible', 'historical_clock_certified',
                 'historical_sessions_certified', 'upstream_independence_verified',
                 'historical_execution_costs_verified',
                 'market_profitability_established', 'orders_available'):
        assert notes[flag] is False
    results = (ROOT / NEW_SOURCE[1]).read_text()
    plan = (ROOT / NEW_SOURCE[2]).read_text()
    assert 'all 30' in results and 'all 30' in plan
    for name in DEPENDENCY['HANDOFF']:
        text = (ROOT / name).read_text()
        assert 'STRATEGY-DIAGNOSIS-027-PLAN.md' in text, name
    assert 'not executed' in plan
    tests = json.loads((ROOT / 'reports/exness-comparison-025-tests.json').read_text())
    assert tests['tests_passed'] == 330
    # Seal narrow notes after every consistency check; never replace a prior seal.
    for name in NEW_REPORT:
        with (ROOT / name).with_suffix('.sha256').open('x') as handle:
            handle.write(sha(ROOT / name) + '\n')
    output = dict(kind='bounded_document_consistency_review_026', passed=True,
        previous_snapshot_verified=previous,
        bindings={name: sha(ROOT / name) for name in (*NEW_SOURCE, *NEW_REPORT)},
        budget_used=notes['budget_used'], primary_failures_preserved=[6, 11],
        software_tests_last_recorded=330, software_suite_rerun=False,
        new_application_code=False, quote_archive_requests=0, quote_rows_read=0,
        performance_runs=0, annual_eligible=False, orders_available=False,
        next_plan='docs/STRATEGY-DIAGNOSIS-027-PLAN.md', next_plan_executed=False,
        review_limit='Checks declared records and preservation; not independent provider-claim verification')
    write(REVIEW, output)
    print(json.dumps(dict(passed=True, budget_used=notes['budget_used'],
                         previous_archived_members=previous['archived_members_verified'])))


def snapshot():
    checked = sealed(REVIEW)
    assert checked['passed']
    DEPENDENCY['verify_previous'](allow_handoff=True)
    for name, expected in checked['bindings'].items():
        assert sha(ROOT / name) == expected, name
    prior = sealed(PRIOR)
    groups = {group: dict(prior[group]) for group in DEPENDENCY['GROUPS']}
    for name in DEPENDENCY['HANDOFF'] | set(NEW_SOURCE):
        groups['source_bindings'][name] = sha(ROOT / name)
    for path in ROOT.glob('reports/evidence-026-*'):
        assert 'final-source' not in path.name
        groups['report_bindings'][path.relative_to(ROOT).as_posix()] = sha(path)
    for suffix in ('.json', '.sha256', '.zip'):
        path = PRIOR.with_suffix(suffix)
        groups['report_bindings'][path.relative_to(ROOT).as_posix()] = sha(path)
    bindings = {name: expected for group in groups.values() for name, expected in group.items()}
    assert len(bindings) == sum(map(len, groups.values()))
    external = dict(prior['archive_external_bindings'])
    prior_archive = PRIOR.with_suffix('.zip').relative_to(ROOT).as_posix()
    external[prior_archive] = bindings[prior_archive]
    assert all(bindings[name] == expected for name, expected in external.items())
    internal = {name: expected for name, expected in bindings.items() if name not in external}
    for name, expected in bindings.items():
        assert sha(ROOT / name) == expected, name
    archive_path = FINAL.with_suffix('.zip')
    with zipfile.ZipFile(archive_path, 'x', compression=zipfile.ZIP_DEFLATED) as archive:
        for name in sorted(internal):
            archive.write(ROOT / name, name)
    with zipfile.ZipFile(archive_path) as archive:
        assert archive.testzip() is None
        assert len(archive.infolist()) == len(internal)
        assert set(archive.namelist()) == set(internal)
        for entry in archive.infolist():
            assert hashlib.sha256(archive.read(entry)).hexdigest() == internal[entry.filename]
    output = dict(kind='bounded_evidence_snapshot_026', **groups,
        archive_external_bindings=external, archive_members_verified=len(internal),
        external_bindings_verified=len(external), archive_sha256=sha(archive_path),
        archive_bytes=archive_path.stat().st_size,
        snapshot_scope='Sources/reports/small fixtures in ZIP; prior source ZIPs and cached market/timezone inputs externally hash-bound, verified and required for rerun',
        previous_snapshot=PRIOR.relative_to(ROOT).as_posix(), previous_snapshot_sha256=sha(PRIOR),
        completed_utc=datetime.now(timezone.utc).isoformat(),
        budget_used=checked['budget_used'], software_tests_last_recorded=330,
        software_suite_rerun=False, annual_eligible=False,
        market_profitability_established=False, orders_available=False,
        next_plan=checked['next_plan'], next_plan_executed=False)
    write(FINAL, output)
    print(json.dumps(dict(counts={group: len(value) for group, value in groups.items()},
        archived_members=len(internal), external_bindings_verified=len(external),
        manifest_sha256=sha(FINAL))))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('review', 'snapshot'))
    {'review': review, 'snapshot': snapshot}[parser.parse_args().action]()
