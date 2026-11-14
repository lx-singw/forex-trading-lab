"""Explicit6244 fresh fixture preparation, fixed date/phase, no market actions."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys
import time
import unittest
import uuid
import zipfile
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
OLD=runpy.run_path(str(ROOT/'scripts/capture-transport-047.py'))
sha,write,sealed,bound=OLD['sha'],OLD['write'],OLD['sealed'],OLD['bound']
HANDOFF=OLD['HANDOFF'];LEDGER=ROOT/'reports/native-pipe-051-ledger.json'
PRIOR=ROOT/'reports/native-log-050-final-source.json'
PATTERNS=('scripts/*051.py','src/forex_demo_lab/*051.py','tests/*051.py','docs/*051*.md',
    'mt5/Scripts/*051*','mt5/Tests/*051*')
CURRENT={
 '/mnt/c/Program Files/MetaTrader 5/metaeditor64.exe':'7d6e42249722888429bb3d4e90e4a810d745f195cfeda9c99a06f24605b29428',
 '/mnt/c/Program Files/MetaTrader 5/terminal64.exe':'eec25399ebd3171422d954fa01b75127c0356c94fe1d45d80dc27c3d0deb4ba1'}

def prior_verify():
    assert sha(PRIOR)=='3558994af5ed1dfb38ad38b35f1563fd17a39a06237e35c5c30de50f5d0ecf39'
    p=sealed(PRIOR);review=sealed(ROOT/'reports/native-log-050-completion-review.json')
    assert review['review_passed'] and review['frozen_input_coverage_complete'] and review['final_source_sha256']==sha(PRIOR)
    assert not p['original049_runtime_completed'] and not p['native_mt5_transport_verified'] and p['disabled049_proof_passed']
    bindings=dict(p['source_and_evidence_bindings']);assert len(bindings)==1569
    for n,h in bindings.items():
        assert sha(bound(n))==h,n
        if n in CURRENT:assert h==CURRENT[n]
    assert sha(PRIOR.with_suffix('.zip'))==p['archive_sha256']
    internal=set(bindings)-set(p['archive_external_bindings'])
    with zipfile.ZipFile(PRIOR.with_suffix('.zip')) as z:
        assert z.testzip() is None and len(z.infolist())==1472 and set(z.namelist())==internal
        for n in internal:assert hashlib.sha256(z.read(n)).hexdigest()==bindings[n]
    change=sealed(ROOT/'reports/native-pipe-048-installed-change.json')
    assert len(change['signatures'])==2
    for s in change['signatures']:
        assert s['signature_status']=='Valid' and s['version']=='5.0.0.6244'
        assert s['subject']=='CN=MetaQuotes Ltd., O=MetaQuotes Ltd., S=Lemesos, C=CY'
        assert s['thumbprint']=='5A64A7AED24C33DED342D01D01FA5286F06DA6DC'
        assert s['sha256']==CURRENT['/mnt/c/Program Files/MetaTrader 5/'+s['file']]
    return p,bindings

def verify_disabled_proof():
    path=ROOT/'reports/native-log-050-audit.json';proof=sealed(path)
    check=sealed(ROOT/'reports/native-log-050-checks.json')
    expected=dict(version='pipe_fixture_049_v1',reason_code=17,requests=0,receipt_valid=False,quote_reads=0,orders=0)
    assert proof['disabled_proof_passed'] is True and proof['records']==[expected]
    assert check['checker_passed'] and check['audit_sha256']==sha(path)
    old=(ROOT/'mt5/Scripts/ForexDemoPipeFixture049.mq5').read_text()
    for a,b in [('PHASE049','PHASE051'),('POLICY049','POLICY051'),('Stop049','Stop051'),('Account049','Account051'),
        ('FXDL_PIPE049','FXDL_PIPE051'),('pipe_fixture_049_v1','pipe_fixture_051_v1'),
        ('49000000000000000000000000000001','51000000000000000000000000000001'),('49'*32,'51'*32)]:old=old.replace(a,b)
    assert old==(ROOT/'mt5/Scripts/ForexDemoPipeFixture051.mq5').read_text()
    return True

def freeze():
    from forex_demo_lab.native_pipe_051 import date_guard
    date_guard(time.time_ns()//1000000);prior,bindings=prior_verify();verify_disabled_proof()
    for n in HANDOFF:bindings.pop(n)
    bindings.update(CURRENT) # New declared phase only; original snapshots unchanged.
    for name in ('native-log-050-final-source.json','native-log-050-final-source.sha256',
        'native-log-050-final-source.zip','native-log-050-completion-review.json','native-log-050-completion-review.sha256'):
        p=ROOT/'reports'/name;bindings[p.relative_to(ROOT).as_posix()]=sha(p)
    for pattern in PATTERNS:
        for p in ROOT.glob(pattern):bindings[p.relative_to(ROOT).as_posix()]=sha(p)
    assert not LEDGER.exists()
    write(LEDGER,dict(bindings=bindings,declared_date='2026-10-07',expected_tests=742,new_tests=24,
        wire_differential_frames=87,prior_snapshot_bindings=1569,prior_snapshot_members=1472,
        installed_build=6244,expected_running_build=6244,shared_disabled_native_phase='049',
        shared_disabled_proof_sha256=sha(ROOT/'reports/native-log-050-audit.json'),native051_disabled_run_executed=False,
        phase='51000000000000000000000000000001',policy_fixture_digest='51'*32,
        maximum_sdk_connections=1,maximum_script_arms=2,maximum_grants=1,maximum_session_seconds=900,
        maximum_io_ms=2000,maximum_native_fixture_suites=1,maximum_compiler_invocations=1,maximum_deployments=1,
        quote_reads=0,orders_available=False,fresh_performance_eligible=False,annual_eligible=False))
    print(json.dumps(dict(frozen=True,bindings=len(bindings),expected_tests=742)))

def verify():
    ledger=sealed(LEDGER)
    for n,h in ledger['bindings'].items():assert sha(bound(n))==h,n
    return ledger

def regression():
    ledger=verify();start=time.monotonic()
    r=unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.discover(str(ROOT/'tests')))
    passed=r.wasSuccessful() and r.testsRun==742 and not r.skipped
    write(ROOT/'reports/native-pipe-051-regression.json',dict(passed=passed,tests_run=r.testsRun,new_tests=24,
        errors=len(r.errors),failures=len(r.failures),skipped=len(r.skipped),wire_differential_frames=87,
        ledger_sha256=sha(LEDGER),elapsed_seconds=time.monotonic()-start,sdk_connections=0,quote_reads=0,orders_available=False))
    if not passed:raise SystemExit(1)

def build():
    verify();assert os.name=='nt'
    assert sealed(ROOT/'reports/native-pipe-051-native-tests.json')['passed']
    assert sealed(ROOT/'reports/native-pipe-051-regression.json')['passed']
    write(ROOT/'reports/native-pipe-051-build-started.json',dict(ledger_sha256=sha(LEDGER),
        maximum_compiler_invocations=1,reservation_consumed=True,sdk_connections=0,quote_reads=0,orders_available=False))
    native=runpy.run_path(str(ROOT/'scripts/native-compiler-042.py'))
    from forex_demo_lab.native_compiler_042 import native_command,compile_evidence
    settings=sealed(ROOT/'reports/native-compiler-042-ledger.json');shell=bound(settings['powershell_path']);editor=bound(settings['editor_path'])
    count=0;reason=None;directory=None;exit_code=None;compiled=False;errors=None;warnings=None;outputs={};before=None;after=None
    try:
        before=native['metadata'](shell)
        if before['editor_processes']!=0:raise ValueError()
        root=Path(settings['build_root'])
        for p in (root,*root.parents):
            if p.is_symlink() or getattr(p.stat(),'st_file_attributes',0)&0x400:raise ValueError()
        directory=root/('compiler051-'+uuid.uuid4().hex);directory.mkdir(exist_ok=False)
        for name in ('ForexDemoPipeFixture051.mq5','CaptureWire047.mqh','CapturePermit046.mqh','ClockGuard042.mqh'):
            source=ROOT/'mt5/Scripts'/name;dest=directory/name
            with source.open('rb') as src,dest.open('xb') as dst:
                for data in iter(lambda:src.read(1048576),b''):dst.write(data)
                dst.flush();os.fsync(dst.fileno())
            assert sha(dest)==sha(source)
        verify();assert native['metadata'](shell)['editor_processes']==0
        count=1
        result=native['hidden_process'](native_command(editor,directory/'ForexDemoPipeFixture051.mq5',directory/'compile.log'),editor,60)
        exit_code=result.returncode;log=(directory/'compile.log').read_text(encoding='utf-16')
        artifact=directory/'ForexDemoPipeFixture051.ex5'
        e=compile_evidence(True,log,artifact.stat().st_size if artifact.exists() else 0)
        compiled,errors,warnings=e['compiled'],e['errors'],e['warnings']
        if not compiled:reason='native_compilation_failed'
    except subprocess.TimeoutExpired:reason='owned_compiler_timeout_no_retry'
    except Exception:reason='native_build_failed_details_redacted'
    try:after=native['metadata'](shell)
    except Exception:after=None
    if directory is not None:
        for p in directory.iterdir():
            if p.is_file():outputs[OLD['API']['external_name'](str(p))]=sha(p)
    write(ROOT/'reports/native-pipe-051-build.json',dict(ledger_sha256=sha(LEDGER),compiler_invocations=count,
        compiler_exit_code=exit_code,compiled=compiled,errors=errors,warnings=warnings,stop_reason=reason,
        output_bindings=outputs,effective_policy_before=before['effective_policy'] if before else None,
        effective_policy_after=after['effective_policy'] if after else None,execution_policy_changed=False,
        fixture_attached=False,fixture_runtime_executed=False,sdk_connections=0,quote_reads=0,orders_available=False))
    print(json.dumps(dict(compiled=compiled,errors=errors,warnings=warnings,compiler_invocations=count,stop_reason=reason)))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=('freeze','verify','test','build'));action=p.parse_args().action
    {'freeze':freeze,'verify':lambda:print(json.dumps(dict(verified=len(verify()['bindings'])))),'test':regression,'build':build}[action]()
