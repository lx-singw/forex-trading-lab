"""Bind audit evidence and preserve the previous snapshot without changing it."""
import argparse
import hashlib
import json
import runpy
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PREVIOUS = ROOT / 'reports/source-metadata-023-final-source.json'
HANDOFF = {'README.md', 'docs/CONTEXT.md', 'docs/PLAN.md', 'docs/VERIFICATION.md'}
GROUPS = ('source_bindings', 'report_bindings', 'synthetic_input_bindings', 'access_evidence_bindings')


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def write(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write('\n')
    with path.with_suffix('.sha256').open('x') as stream:
        stream.write(digest(path) + '\n')


def sealed(path):
    fields = path.with_suffix('.sha256').read_text().split()
    assert len(fields) in (1, 2), path.name
    assert digest(path) == fields[0], path.name
    if len(fields) == 2:
        assert fields[1] == path.name, path.name
    return json.loads(path.read_text())


def previous_check():
    assert digest(PREVIOUS) == 'cfd6eec4e1079c547b31123a766f8ec78dffdb64ac8739c9a518f24a4f965d83'
    previous = sealed(PREVIOUS)
    changes = {}
    for group in GROUPS:
        for name, expected in previous[group].items():
            current = digest(ROOT / name)
            if current != expected:
                assert group == 'source_bindings' and name in HANDOFF, name
                changes[name] = dict(previous_sha256=expected, current_sha256=current)
    archive_path = PREVIOUS.with_suffix('.zip')
    assert digest(archive_path) == previous['archive_sha256']
    all_bindings = {name: sha for group in GROUPS for name, sha in previous[group].items()}
    with zipfile.ZipFile(archive_path) as archive:
        assert archive.testzip() is None
        assert len(archive.infolist()) == previous['archive_members_verified']
        for entry in archive.infolist():
            assert hashlib.sha256(archive.read(entry)).hexdigest() == all_bindings[entry.filename]
    return previous, changes


def review():
    previous, changes = previous_check()
    for name in ('scripts/exness-024.py', 'scripts/exness-024b.py'):
        runpy.run_path(str(ROOT / name))['verify']()
    original = sealed(ROOT / 'reports/exness-024-audit.json')
    original_check = sealed(ROOT / 'reports/exness-024-checks.json')
    supplemental = sealed(ROOT / 'reports/exness-024b-audit.json')
    supplemental_check = sealed(ROOT / 'reports/exness-024b-checks.json')
    assert not original['diagnostic_pass'] and original_check['passed']
    assert supplemental['diagnostic_pass'] and supplemental_check['passed']
    assert original_check['audit_sha256'] == digest(ROOT / 'reports/exness-024-audit.json')
    assert supplemental_check['audit_sha256'] == digest(ROOT / 'reports/exness-024b-audit.json')
    total = 0
    summaries = []
    previous_end = None
    for month, strict, full, checked in zip(('03', '07'), original['months'], supplemental['months'], supplemental_check['months']):
        receipt_path = ROOT / f'data/exness-024/exness-2023-{month}-get.json'
        receipt = json.loads(receipt_path.read_text(encoding='utf-8-sig'))
        assert receipt['status'] == 200 and receipt['retries'] == 0
        assert receipt['outcome'] == 'complete_original_preserved'
        assert not any(receipt[key] for key in ('redirects_allowed', 'cookies_enabled', 'credentials_used', 'custom_identity'))
        original_path = ROOT / receipt['original_path']
        assert digest(original_path) == receipt['sha256'] == full['source_sha256']
        assert original_path.stat().st_size == receipt['stored_bytes'] == receipt['body_bytes_read'] == receipt['content_length']
        assert receipt['stored_bytes'] <= 25 * 1024 * 1024
        begin = datetime.fromisoformat(receipt['started_utc'])
        end = datetime.fromisoformat(receipt['ended_utc'])
        assert 0 <= (end - begin).total_seconds() <= 60
        if previous_end is not None:
            assert begin >= previous_end
        previous_end = end
        total += receipt['stored_bytes']
        assert strict['errors'] == {'provider_or_symbol': strict['rows']}
        assert strict['rows'] == full['rows'] == checked['original_records']
        assert full['valid_rows'] == full['rows'] and not full['errors']
        assert sum(full['hour_counts'].values()) == full['rows']
        assert full['observed_hours'] + full['empty_hours'] == 744
        assert checked['passed'] and all(checked['matches'].values())
        assert not any(full[key] for key in ('annual_eligible', 'performance_evaluation_ready', 'orders_available', 'market_profitability_established'))
        summaries.append({key: full[key] for key in ('month', 'rows', 'first', 'last', 'observed_hours', 'empty_hours', 'tied_timestamps', 'exact_duplicate_records', 'backward_timestamps', 'uncompressed_bytes')})
    assert total <= 50 * 1024 * 1024
    assert sum(m['uncompressed_bytes'] for m in supplemental['months']) <= 512 * 1024 * 1024
    tests = json.loads((ROOT / 'reports/exness-024-tests.json').read_text())
    assert tests['tests_passed'] == 318 and tests['new_tests'] == 19
    output = dict(kind='diagnostic_exness_acquisition_and_audit_review_024', passed=True,
                  previous_counts={g: len(previous[g]) for g in GROUPS},
                  previous_archive_members_verified=previous['archive_members_verified'],
                  allowed_handoff_changes=changes, get_requests=2, downloaded_bytes=total,
                  network_retries=0, original_failure_preserved=True,
                  exact_version_derivation_passed=True, months=summaries,
                  software_tests_passed=318, annual_eligible=False,
                  performance_evaluation_ready=False, market_profitability_established=False,
                  orders_available=False, next_comparison_executed=False)
    write(ROOT / 'reports/exness-024-review.json', output)
    print(json.dumps(dict(passed=True, get_requests=2, downloaded_bytes=total,
                          original_rows=sum(m['rows'] for m in summaries), software_tests_passed=318)))


def snapshot():
    previous, _ = previous_check()
    review_report = sealed(ROOT / 'reports/exness-024-review.json')
    assert review_report['passed']
    groups = {g: dict(previous[g]) for g in GROUPS}
    for name in HANDOFF:
        groups['source_bindings'][name] = digest(ROOT / name)
    for pattern in ('scripts/*exness*024*', 'src/forex_demo_lab/exness_diagnostics*.py',
                    'tests/test_exness_diagnostics*.py', 'docs/*024*.md',
                    'docs/EXNESS-COMPARISON-025-PLAN.md'):
        for path in ROOT.glob(pattern):
            groups['source_bindings'][path.relative_to(ROOT).as_posix()] = digest(path)
    for path in ROOT.glob('reports/exness-024*'):
        assert 'final-source' not in path.name
        groups['report_bindings'][path.relative_to(ROOT).as_posix()] = digest(path)
    for suffix in ('.json', '.sha256', '.zip'):
        path = PREVIOUS.with_suffix(suffix)
        groups['report_bindings'][path.relative_to(ROOT).as_posix()] = digest(path)
    for path in ROOT.glob('data/exness-024/*-get.json'):
        groups['access_evidence_bindings'][path.relative_to(ROOT).as_posix()] = digest(path)
    groups['market_input_bindings'] = {path.relative_to(ROOT).as_posix(): digest(path)
                                       for path in ROOT.glob('data/exness-024/*.zip')}
    all_bindings = {name: sha for bindings in groups.values() for name, sha in bindings.items()}
    assert len(all_bindings) == sum(map(len, groups.values()))
    archive_path = ROOT / 'reports/exness-024-final-source.zip'
    with zipfile.ZipFile(archive_path, 'x', compression=zipfile.ZIP_DEFLATED) as archive:
        for name, sha in sorted(all_bindings.items()):
            assert digest(ROOT / name) == sha, name
            archive.write(ROOT / name, name)
    with zipfile.ZipFile(archive_path) as archive:
        assert archive.testzip() is None
        for entry in archive.infolist():
            assert hashlib.sha256(archive.read(entry)).hexdigest() == all_bindings[entry.filename]
    output = dict(kind='post_review_exness_diagnostic_snapshot_024', **groups,
                  completed_utc=datetime.now(timezone.utc).isoformat(),
                  previous_snapshot=PREVIOUS.relative_to(ROOT).as_posix(),
                  previous_snapshot_sha256=digest(PREVIOUS),
                  archive_sha256=digest(archive_path), archive_bytes=archive_path.stat().st_size,
                  archive_members_verified=len(all_bindings),
                  quote_rows_verified=2537026, software_tests_passed=318,
                  get_requests=2, network_retries=0, original_failure_preserved=True,
                  annual_eligible=False, performance_evaluation_ready=False,
                  market_profitability_established=False, orders_available=False,
                  next_comparison_plan='docs/EXNESS-COMPARISON-025-PLAN.md',
                  next_comparison_executed=False)
    write(ROOT / 'reports/exness-024-final-source.json', output)
    print(json.dumps(dict(counts={key:len(value) for key,value in groups.items()},
                          archive_members_verified=len(all_bindings), manifest_sha256=digest(ROOT / 'reports/exness-024-final-source.json'))))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['review', 'snapshot'])
    action = parser.parse_args().action
    {'review': review, 'snapshot': snapshot}[action]()
