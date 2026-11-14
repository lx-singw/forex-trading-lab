"""Freeze a fresh persistent session; reuse sealed042 source and compiled artifact."""
import argparse
import hashlib
import json
from pathlib import Path
import runpy
import zipfile
ROOT=Path(__file__).resolve().parents[1]
BUILD=runpy.run_path(str(ROOT/'scripts/native-compiler-042.py'))
sha,write,sealed=BUILD['sha'],BUILD['write'],BUILD['sealed'];HANDOFF=BUILD['HANDOFF'];bound_path=BUILD['bound_path']
command,external_name=BUILD['command'],BUILD['external_name'];OUTPUT=BUILD['OUTPUT']
PRIOR=ROOT/'reports/clock-observer-042-final-source.json'
LEDGER=ROOT/'reports/clock-session-043-ledger.json'
RESERVATION=ROOT/'reports/clock-observer-043-runtime-reservation.json'

def prior_verify(allow_handoff=False):
    assert sha(PRIOR)=='6cbdd147ebc2ea561a7754af866673d44a6ded0a3bd711ec0191170684c48449'
    prior=sealed(PRIOR);bindings={};changes={}
    for group,values in prior.items():
        if not group.endswith('_bindings') or group=='archive_external_bindings':continue
        for n,h in values.items():
            assert n not in bindings;actual=sha(bound_path(n))
            if actual!=h:
                assert allow_handoff and group=='source_bindings' and n in HANDOFF,n
                changes[n]=dict(previous_sha256=h,current_sha256=actual)
            bindings[n]=h
    external=prior['archive_external_bindings']
    assert len(bindings)==1303 and len(external)==70 and all(bindings[n]==h for n,h in external.items())
    assert sha(PRIOR.with_suffix('.zip'))==prior['archive_sha256']
    with zipfile.ZipFile(PRIOR.with_suffix('.zip')) as z:
        assert z.testzip() is None and len(z.infolist())==1233 and set(z.namelist())==set(bindings)-set(external)
        for n in z.namelist():assert hashlib.sha256(z.read(n)).hexdigest()==bindings[n],n
    assert prior['observer_compiled'] and not prior['observer_runtime_executed'] and not prior['orders_available']
    return dict(bindings_verified=1303,archived_members_verified=1233,external_bindings_verified=70,allowed_handoff_changes=changes)

def freeze():
    previous=prior_verify();tests=sealed(ROOT/'reports/clock-session-043-regression.json')
    assert tests['passed'] and tests['tests_run']==tests['tests_passed']==612 and tests['new_tests']==8
    old=BUILD['verify']();bindings=dict(old['bindings'])
    for pattern in ('scripts/*043*','tests/*043*.py','docs/*043*.md','src/forex_demo_lab/*043.py',
                    'reports/clock-session-043-regression*','reports/clock-observer-042-*','reports/native-compiler-042-*'):
        for p in ROOT.glob(pattern):bindings[p.relative_to(ROOT).as_posix()]=sha(p)
    for n,h in sealed(ROOT/'reports/clock-observer-042-deployment.json')['artifact_binding'].items():
        assert sha(bound_path(n))==h;bindings[n]=h
    required={'scripts/clock-runtime-043.py','scripts/check-clock-runtime-043.py','scripts/finalize-clock-session-043.py',
        'scripts/clock-session-043.py','tests/test_clock_session_043.py','docs/CLOCK-SESSION-043-PROTOCOL.md'}
    assert required<=set(bindings) and not LEDGER.exists() and not RESERVATION.exists()
    write(LEDGER,dict(bindings=bindings,prior_snapshot_verification=previous,
        powershell_path=old['powershell_path'],declared_date='2026-10-06',interactive_required=True,
        maximum_native_connections=1,maximum_script_arms=2,maximum_quote_reads=1,maximum_sdk_quote_reads=0,
        maximum_compiler_invocations=0,maximum_deployments=0,orders_available=False,
        fresh_performance_eligible=False,annual_eligible=False))
    print(json.dumps(dict(frozen=True,bindings=len(bindings),prior_verified=previous)))

def verify():
    ledger=sealed(LEDGER)
    for n,h in ledger['bindings'].items():assert sha(bound_path(n))==h,n
    return ledger

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=('freeze','verify'))
    {'freeze':freeze,'verify':lambda:print(json.dumps(dict(verified=len(verify()['bindings']))))}[p.parse_args().action]()
