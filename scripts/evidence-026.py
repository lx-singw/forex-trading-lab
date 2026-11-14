"""Integrity checks for the bounded documentation review; no network or trading."""
import argparse
import hashlib
import json
import runpy
import sys
import zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
PRIOR=ROOT/'reports/exness-comparison-025-final-source.json'
HANDOFF={'README.md','docs/CONTEXT.md','docs/PLAN.md','docs/VERIFICATION.md'}
GROUPS=('source_bindings','report_bindings','synthetic_input_bindings',
        'access_evidence_bindings','market_input_bindings','comparison_input_bindings')


def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()


def write(path,value):
    with path.open('x') as f:json.dump(value,f,indent=2,sort_keys=True);f.write('\n')
    with path.with_suffix('.sha256').open('x') as f:f.write(sha(path)+'\n')


def verify_previous(allow_handoff=False):
    assert sha(PRIOR)=='4302d16dab9c929b2c1bd2b1c439ce855d2a23aa2169d5e9f9ce9aab312f3342'
    assert sha(PRIOR)==PRIOR.with_suffix('.sha256').read_text().strip()
    previous=json.loads(PRIOR.read_text())
    all_bindings={}
    changes={}
    for group in GROUPS:
        for name,expected in previous[group].items():
            current=sha(ROOT/name)
            if current!=expected:
                assert allow_handoff and group=='source_bindings' and name in HANDOFF,name
                changes[name]=dict(previous_sha256=expected,current_sha256=current)
            assert name not in all_bindings
            all_bindings[name]=expected
    external=previous['archive_external_bindings']
    assert len(external)==previous['external_bindings_verified']
    assert all(all_bindings[name]==expected for name,expected in external.items())
    archive_path=PRIOR.with_suffix('.zip')
    assert sha(archive_path)==previous['archive_sha256']
    with zipfile.ZipFile(archive_path) as archive:
        assert archive.testzip() is None
        assert len(archive.infolist())==previous['archive_members_verified']
        assert set(archive.namelist())==set(all_bindings)-set(external)
        for entry in archive.infolist():
            assert hashlib.sha256(archive.read(entry)).hexdigest()==all_bindings[entry.filename]
    runpy.run_path(str(ROOT/'scripts/exness-comparison-025.py'))['verify']()
    assert runpy.run_path(str(ROOT/'scripts/derive-exness-comparison-025b.py'))['verify']()
    return dict(counts={group:len(previous[group]) for group in GROUPS},
                archived_members_verified=previous['archive_members_verified'],
                external_bindings_verified=len(external),allowed_handoff_changes=changes)


def preflight():
    verified=verify_previous()
    paths=('docs/EXNESS-EVIDENCE-026-PLAN.md','docs/EXNESS-EVIDENCE-026-DISCOVERY.md',
           'scripts/evidence-026.py','reports/exness-comparison-025-final-source.json',
           'reports/exness-comparison-025-final-source.sha256')
    bindings={name:sha(ROOT/name) for name in paths}
    output=dict(kind='pre_browse_integrity_026',passed=True,previous_snapshot=verified,
                bindings=bindings,network_requests=0,quote_rows_read=0,
                annual_eligible=False,orders_available=False)
    write(ROOT/'reports/evidence-026-preflight.json',output)
    print(json.dumps(dict(passed=True,previous_snapshot=verified,network_requests=0)))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('action',choices=('preflight',))
    action=parser.parse_args().action
    {'preflight':preflight}[action]()
