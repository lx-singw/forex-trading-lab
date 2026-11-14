"""Freeze and test offline diagnostics; no runtime attachment or market APIs."""
import argparse
import hashlib
import json
from pathlib import Path
import runpy
import time
import unittest
import zipfile

ROOT=Path(__file__).resolve().parents[1]
API=runpy.run_path(str(ROOT/'scripts/native-log-052.py'))
sha,sealed,write,bound=API['sha'],API['sealed'],API['write'],API['bound']
HANDOFF=API['API']['HANDOFF']
PRIOR=ROOT/'reports/native-log-052-final-source.json'
LEDGER=ROOT/'reports/transport-diagnostics-053-r2-ledger.json'
PATTERNS=('scripts/*053.py','src/forex_demo_lab/*053.py','tests/*053.py','docs/*053*.md',
          'mt5/Scripts/*053*','mt5/Tests/*053*')

def prior_verify():
    assert sha(PRIOR)=='c8f2d105adb7901c8f72cc1b8dc436994e0a2a453310679fbe5eed0d6c246efb'
    p=sealed(PRIOR);review=sealed(ROOT/'reports/native-log-052-completion-review.json')
    assert review['review_passed'] and review['frozen_input_coverage_complete'] and review['final_source_sha256']==sha(PRIOR)
    assert review['next_plan_sha256']==sha(ROOT/'docs/NATIVE-TRANSPORT-053-PLAN.md')
    assert p['original051_runtime_completed'] is False and p['native_mt5_transport_verified'] is False
    assert p['native_reason_codes']==[23]
    bindings=dict(p['source_and_evidence_bindings']);assert len(bindings)==1644
    for n,h in bindings.items():assert sha(bound(n))==h,n
    assert sha(PRIOR.with_suffix('.zip'))==p['archive_sha256']
    internal=set(bindings)-set(p['archive_external_bindings'])
    with zipfile.ZipFile(PRIOR.with_suffix('.zip')) as z:
        assert z.testzip() is None and len(z.infolist())==1537 and set(z.namelist())==internal
        for n in internal:assert hashlib.sha256(z.read(n)).hexdigest()==bindings[n]
    return bindings

def freeze():
    bindings=prior_verify()
    for n in HANDOFF:bindings.pop(n)
    for name in ('native-log-052-final-source.json','native-log-052-final-source.sha256','native-log-052-final-source.zip',
                 'native-log-052-completion-review.json','native-log-052-completion-review.sha256'):
        p=ROOT/'reports'/name;bindings[p.relative_to(ROOT).as_posix()]=sha(p)
    first=sealed(ROOT/'reports/transport-diagnostics-053-r1-source.json')
    assert first['first_full_regression_passed'] is False and first['errors']==26
    assert sha(ROOT/'reports/transport-diagnostics-053-r1-source.zip')==first['archive_sha256']
    with zipfile.ZipFile(ROOT/'reports/transport-diagnostics-053-r1-source.zip') as z:
        assert z.testzip() is None and set(z.namelist())==set(first['bindings'])
        for n,h in first['bindings'].items():assert hashlib.sha256(z.read(n)).hexdigest()==h
    for pattern in ('reports/transport-diagnostics-053-*.json','reports/transport-diagnostics-053-*.sha256','reports/transport-diagnostics-053-r1-source.zip'):
        for p in ROOT.glob(pattern):bindings[p.relative_to(ROOT).as_posix()]=sha(p)
    for pattern in PATTERNS:
        for p in ROOT.glob(pattern):bindings[p.relative_to(ROOT).as_posix()]=sha(p)
    write(LEDGER,dict(bindings=bindings,revision=2,first_failure_preserved=True,expected_tests=774,new_tests=32,differential_cases=99,
        prior_bindings_verified=1644,prior_archive_members_verified=1537,maximum_full_regressions=1,
        native_metatrader_compiler_invocations=0,terminal_deployments=0,native_fixture_invocations=0,
        sdk_connections=0,market_reads=0,orders_available=False,fresh_performance_eligible=False,annual_eligible=False))
    print(json.dumps(dict(frozen=True,bindings=len(bindings),expected_tests=774)))

def verify():
    ledger=sealed(LEDGER)
    for n,h in ledger['bindings'].items():assert sha(bound(n))==h,n
    return ledger

def test():
    import sys
    sys.path.insert(0,str(ROOT/'src'))
    verify();write(ROOT/'reports/transport-diagnostics-053-r2-tests-started.json',dict(
        ledger_sha256=sha(LEDGER),suite_consumed=True,sdk_connections=0,market_reads=0,orders_available=False))
    start=time.monotonic()
    result=unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.discover(str(ROOT/'tests')))
    passed=result.wasSuccessful() and result.testsRun==774 and not result.skipped
    write(ROOT/'reports/transport-diagnostics-053-r2-tests.json',dict(passed=passed,tests_run=result.testsRun,new_tests=32,
        differential_cases=99,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped),
        elapsed_seconds=time.monotonic()-start,ledger_sha256=sha(LEDGER),sdk_connections=0,market_reads=0,
        native_fixture_invocations=0,native_metatrader_compiler_invocations=0,orders_available=False))
    if not passed:raise SystemExit(1)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=('freeze','test','verify'));a=p.parse_args().action
    {'freeze':freeze,'test':test,'verify':lambda:print(json.dumps(dict(verified=len(verify()['bindings']))))}[a]()
