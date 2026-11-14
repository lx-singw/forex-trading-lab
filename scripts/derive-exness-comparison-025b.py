"""Version the checker archive guard while retaining all comparison arithmetic."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
ORIGINAL=ROOT/'scripts/check-exness-comparison-025.py'
TARGET=ROOT/'scripts/check-exness-comparison-025b.py'
LEDGER=ROOT/'reports/exness-comparison-025b-ledger.json'
HELPER='''def check_hist_members(archive,member):
    notes=member[:-4]+'.txt'
    assert archive.namelist()==[member,notes]
    entries=archive.infolist()
    assert all(not entry.flag_bits&1 for entry in entries)
    assert sum(entry.file_size for entry in entries)<=128*1024*1024
    note=archive.getinfo(notes)
    assert note.file_size<=65536
    with archive.open(note) as stream:
        content=stream.read(65537)
    assert len(content)==note.file_size and len(content)<=65536


'''
SUPPLEMENT='''    supplemental_path=ROOT/'reports/exness-comparison-025b-ledger.json'
    assert sha(supplemental_path)==supplemental_path.with_suffix('.sha256').read_text().strip()
    supplemental=json.loads(supplemental_path.read_text())
    for name,digest in supplemental['bindings'].items():assert sha(ROOT/name)==digest,name
'''


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def transformed():
    source=ORIGINAL.read_text()
    replacements=(('        assert archive.namelist()==[member]\n',
                   '        check_hist_members(archive,member)\n'),
                  ('def source_events(window,source):\n',HELPER+'def source_events(window,source):\n'),
                  ('def main():\n','def main():\n'+SUPPLEMENT),
                  ("kind='independent_original_coverage_comparison_025'", "kind='independent_original_coverage_comparison_025b'"),
                  ("path=ROOT/'reports/exness-comparison-025-checks.json'", "path=ROOT/'reports/exness-comparison-025b-checks.json'"),
                  ('ledger_sha256=sha(ledger_path),review_sha256=sha(report_path)',
                   'supplemental_ledger_sha256=sha(supplemental_path),ledger_sha256=sha(ledger_path),review_sha256=sha(report_path)'))
    # The ZIP assertion also appears in the reference reader, with different
    # indentation plus a size condition; this exact replacement is HistData only.
    for before,after in replacements:
        assert source.count(before)==1,(before,source.count(before))
        source=source.replace(before,after)
    return source


def verify_derivation():
    assert TARGET.read_text()==transformed()
    return True


def generate():
    assert sha(ORIGINAL)=='5d642a7b488fd228e3ad615bda9e32781ae4e44986f296121c7a10bf7459b04d'
    with TARGET.open('x') as stream:stream.write(transformed())
    assert verify_derivation()
    print('025B checker derived; original unchanged')


def freeze():
    assert verify_derivation()
    old_path=ROOT/'reports/exness-comparison-025-ledger.json'
    assert sha(old_path)==old_path.with_suffix('.sha256').read_text().strip()
    old=json.loads(old_path.read_text())
    bindings=dict(old['bindings'])
    for name,expected in bindings.items():assert sha(ROOT/name)==expected,name
    for name in ('docs/EXNESS-COMPARISON-025B-PLAN.md','scripts/derive-exness-comparison-025b.py',
                 'scripts/check-exness-comparison-025b.py','scripts/inspect-histdata-025.py',
                 'tests/test_coverage_comparison_b.py','reports/exness-comparison-025-ledger.json',
                 'reports/exness-comparison-025-ledger.sha256','reports/exness-comparison-025-review.json',
                 'reports/exness-comparison-025-review.sha256','reports/exness-comparison-025-lineage.csv',
                 'reports/exness-comparison-025-check-attempt.json','reports/exness-comparison-025-check-attempt.sha256'):
        bindings[name]=sha(ROOT/name)
    with LEDGER.open('x') as stream:
        json.dump(dict(kind='frozen_independent_archive_supplement_025b',bindings=bindings,
                       original_failure_preserved=True,annual_eligible=False,orders_available=False),stream,indent=2,sort_keys=True)
        stream.write('\n')
    with LEDGER.with_suffix('.sha256').open('x') as stream:stream.write(sha(LEDGER)+'\n')
    print('025B checker and evidence frozen')


def verify():
    assert verify_derivation()
    assert sha(LEDGER)==LEDGER.with_suffix('.sha256').read_text().strip()
    ledger=json.loads(LEDGER.read_text())
    for name,expected in ledger['bindings'].items():assert sha(ROOT/name)==expected,name
    return True


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('action',choices=('generate','freeze','verify'))
    action=parser.parse_args().action
    {'generate':generate,'freeze':freeze,'verify':verify}[action]()
