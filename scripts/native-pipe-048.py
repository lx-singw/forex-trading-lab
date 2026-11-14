"""Freeze and verify048 preparation; preserve047 main and additive closure."""
import argparse
import hashlib
import json
import runpy
import sys
import time
import unittest
import zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
OLD=runpy.run_path(str(ROOT/'scripts/capture-transport-047.py'))
sha,write,sealed,bound=OLD['sha'],OLD['write'],OLD['sealed'],OLD['bound']
PRIOR=ROOT/'reports/capture-transport-047-final-source.json'
REVIEW=ROOT/'reports/capture-transport-047-completion-review.json'
LEDGER=ROOT/'reports/native-pipe-048-ledger.json'
PATTERNS=('scripts/*048.py','src/forex_demo_lab/*048.py','tests/*048.py','docs/*048*.md')

def prior_verify():
    assert sha(PRIOR)=='464ba83f3643a3dab819fd002df9cdcae812f202af8f67c828169cf3b0f12303'
    prior=sealed(PRIOR);review=sealed(REVIEW)
    assert review['review_passed'] and review['frozen_input_coverage_complete'] and review['final_source_sha256']==sha(PRIOR)
    bindings={n:h for g,v in prior.items() if g.endswith('_bindings') and g!='archive_external_bindings' for n,h in v.items()}
    assert len(bindings)==1443
    for n,h in bindings.items():assert sha(bound(n))==h,n
    assert sha(PRIOR.with_suffix('.zip'))==prior['archive_sha256']
    internal=set(bindings)-set(prior['archive_external_bindings'])
    with zipfile.ZipFile(PRIOR.with_suffix('.zip')) as z:
        assert z.testzip() is None and set(z.namelist())==internal and len(z.infolist())==1361
        for n in internal:assert hashlib.sha256(z.read(n)).hexdigest()==bindings[n]
    for n,h in review['additional_frozen_input_bindings'].items():
        assert sha(bound(n))==h
        with zipfile.ZipFile(bound(n)) as z:assert z.testzip() is None and len(z.infolist())==11
        bindings[n]=h
    for p in (REVIEW,REVIEW.with_suffix('.sha256'),PRIOR,PRIOR.with_suffix('.sha256'),PRIOR.with_suffix('.zip')):
        bindings[p.relative_to(ROOT).as_posix()]=sha(p)
    return bindings

def freeze():
    bindings=prior_verify()
    for n in OLD['HANDOFF']:bindings.pop(n)
    for pattern in PATTERNS:
        for p in ROOT.glob(pattern):bindings[p.relative_to(ROOT).as_posix()]=sha(p)
    assert not LEDGER.exists()
    write(LEDGER,dict(bindings=bindings,declared_date='2026-10-07',expected_tests=682,new_tests=16,
        prior_snapshot_bindings=1443,prior_snapshot_members=1361,additive_original_archives=2,
        maximum_sdk_connections=1,maximum_script_arms=3,maximum_grants=1,maximum_session_seconds=900,
        maximum_io_ms=2000,maximum_native_fixture_suites=1,maximum_deployments=1,
        sdk_quote_reads=0,native_quote_reads=0,orders_available=False))
    print(json.dumps(dict(frozen=True,bindings=len(bindings))))

def verify():
    ledger=sealed(LEDGER)
    for n,h in ledger['bindings'].items():assert sha(bound(n))==h,n
    return ledger

def regression():
    ledger=verify();start=time.monotonic()
    result=unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.discover(str(ROOT/'tests')))
    passed=result.wasSuccessful() and result.testsRun==ledger['expected_tests'] and not result.skipped
    write(ROOT/'reports/native-pipe-048-regression.json',dict(passed=passed,tests_run=result.testsRun,new_tests=16,
        errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped),
        ledger_sha256=sha(LEDGER),elapsed_seconds=time.monotonic()-start,sdk_connections=0,quote_reads=0,orders_available=False))
    if not passed:raise SystemExit(1)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=('freeze','verify','test'));action=p.parse_args().action
    {'freeze':freeze,'verify':lambda:print(json.dumps(dict(verified=len(verify()['bindings'])))),'test':regression}[action]()
