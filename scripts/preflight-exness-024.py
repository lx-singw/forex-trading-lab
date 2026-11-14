"""Verify the complete 023 snapshot before reserving any 024 GET."""
import hashlib
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def main():
    snapshot = ROOT / 'reports/source-metadata-023-final-source.json'
    assert digest(snapshot) == 'cfd6eec4e1079c547b31123a766f8ec78dffdb64ac8739c9a518f24a4f965d83'
    prior = json.loads(snapshot.read_text())
    groups = ('source_bindings', 'report_bindings', 'synthetic_input_bindings', 'access_evidence_bindings')
    # Working handoff docs are bound too; acquisition occurs before changing them.
    counts = {}
    bindings = {}
    for group in groups:
        for name, expected in prior[group].items():
            assert digest(ROOT / name) == expected, name
            bindings[name] = expected
        counts[group] = len(prior[group])
    archive = snapshot.with_suffix('.zip')
    assert digest(archive) == prior['archive_sha256']
    with zipfile.ZipFile(archive) as z:
        assert len(z.infolist()) == prior['archive_members_verified']
        assert z.testzip() is None
        for entry in z.infolist():
            assert hashlib.sha256(z.read(entry)).hexdigest() == bindings[entry.filename], entry.filename
    bindings['reports/source-metadata-023-final-source.json'] = digest(snapshot)
    bindings['reports/source-metadata-023-final-source.zip'] = digest(archive)
    for name in ('scripts/download-exness-024.ps1', 'scripts/preflight-exness-024.py'):
        bindings[name] = digest(ROOT / name)
    report = {'kind': 'pre_get_snapshot_check_024', 'passed': True, 'prior_counts': counts,
              'previous_archive_members_verified': len(bindings) - 4,
              'network_requests': 0, 'bindings': bindings}
    output = ROOT / 'reports/exness-024-acquisition-preflight.json'
    with output.open('x') as f:
        json.dump(report, f, indent=2, sort_keys=True)
        f.write('\n')
    print(json.dumps({'passed': True, 'prior_counts': counts, 'network_requests': 0}))


if __name__ == '__main__':
    main()
