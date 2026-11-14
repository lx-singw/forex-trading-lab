"""Verify archival lineage with exactly two declared installed-file exceptions."""
import argparse
import hashlib
import json
from pathlib import Path
import runpy
import sys
import zipfile
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
OLD=runpy.run_path(str(ROOT/'scripts/clock-session-043.py'))
sha,write,sealed=OLD['sha'],OLD['write'],OLD['sealed'];HANDOFF=OLD['HANDOFF'];bound_path=OLD['bound_path']
command,external_name=OLD['command'],OLD['external_name'];OUTPUT=OLD['OUTPUT']
from forex_demo_lab.clock_session_044 import ROLLOVER,allowed_rollover,validate_signatures
PRIOR=ROOT/'reports/clock-session-043-preparation-final-source.json'
LEDGER=ROOT/'reports/clock-session-044-ledger.json'
RESERVATION=ROOT/'reports/clock-observer-044-runtime-reservation.json'

def prior_verify(allow_handoff=False):
    assert sha(PRIOR)=='6d9ca99a92407be6f2c456635442a2c8725c06194647acafeee24ced1288fd62'
    prior=sealed(PRIOR);bindings={};changes={};rollover={}
    for group,values in prior.items():
        if not group.endswith('_bindings') or group=='archive_external_bindings':continue
        for n,h in values.items():
            assert n not in bindings;actual=sha(bound_path(n))
            if actual!=h:
                if allowed_rollover(n,h,actual):rollover[n]=dict(previous_sha256=h,current_sha256=actual)
                else:
                    assert allow_handoff and group=='source_bindings' and n in HANDOFF,n
                    changes[n]=dict(previous_sha256=h,current_sha256=actual)
            bindings[n]=h
    external=prior['archive_external_bindings']
    assert len(bindings)==1324 and len(external)==71 and set(rollover)==set(ROLLOVER)
    assert all(bindings[n]==h for n,h in external.items()) and sha(PRIOR.with_suffix('.zip'))==prior['archive_sha256']
    with zipfile.ZipFile(PRIOR.with_suffix('.zip')) as z:
        assert z.testzip() is None and len(z.infolist())==1253 and set(z.namelist())==set(bindings)-set(external)
        for n in z.namelist():assert hashlib.sha256(z.read(n)).hexdigest()==bindings[n],n
    assert prior['observer_compiled'] and not prior['observer_runtime_executed'] and not prior['orders_available']
    return dict(original_bindings=1324,unchanged_bindings_verified=1322,archived_members_verified=1253,
        external_bindings=71,installed_file_rollover=rollover,old_installed_bytes_available=False,allowed_handoff_changes=changes)

def freeze():
    previous=prior_verify();tests=sealed(ROOT/'reports/clock-session-044-regression.json')
    assert tests['passed'] and tests['tests_run']==tests['tests_passed']==622 and tests['new_tests']==10
    signature=sealed(ROOT/'reports/clock-session-043-installed-version-diagnostic.json');validate_signatures(signature)
    old=sealed(OLD['LEDGER']);bindings=dict(old['bindings'])
    for n,(before,after) in ROLLOVER.items():assert bindings[n]==before and sha(bound_path(n))==after;bindings[n]=after
    for pattern in ('scripts/*044*','tests/*044*.py','docs/*044*.md','src/forex_demo_lab/*044.py',
                    'reports/clock-session-044-regression*','reports/clock-session-043-*'):
        for p in ROOT.glob(pattern):bindings[p.relative_to(ROOT).as_posix()]=sha(p)
    required={'scripts/clock-runtime-044.py','scripts/check-clock-runtime-044.py','scripts/finalize-clock-session-044.py',
        'scripts/clock-session-044.py','tests/test_clock_session_044.py','docs/CLOCK-DEPENDENCY-044-PROTOCOL.md'}
    assert required<=set(bindings) and not LEDGER.exists() and not RESERVATION.exists()
    write(LEDGER,dict(bindings=bindings,prior_snapshot_verification=previous,powershell_path=old['powershell_path'],
        declared_date='2026-10-06',interactive_required=True,maximum_native_connections=1,maximum_script_arms=2,
        maximum_quote_reads=1,maximum_sdk_quote_reads=0,maximum_compiler_invocations=0,maximum_deployments=0,
        orders_available=False,fresh_performance_eligible=False,annual_eligible=False))
    print(json.dumps(dict(frozen=True,bindings=len(bindings),archived_members_verified=1253,installed_files_rebound=2)))

def verify():
    ledger=sealed(LEDGER)
    for n,h in ledger['bindings'].items():assert sha(bound_path(n))==h,n
    return ledger

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=('freeze','verify'))
    {'freeze':freeze,'verify':lambda:print(json.dumps(dict(verified=len(verify()['bindings']))))}[p.parse_args().action]()
