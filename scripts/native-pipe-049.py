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
HANDOFF=OLD['HANDOFF'];LEDGER=ROOT/'reports/native-pipe-049-ledger.json'
PRIOR=ROOT/'reports/native-pipe-048-final-source.json'
PATTERNS=('scripts/*049.py','src/forex_demo_lab/*049.py','tests/*049.py','docs/*049*.md',
    'mt5/Scripts/*049*','mt5/Tests/*049*')
CURRENT={
 '/mnt/c/Program Files/MetaTrader 5/metaeditor64.exe':'7d6e42249722888429bb3d4e90e4a810d745f195cfeda9c99a06f24605b29428',
 '/mnt/c/Program Files/MetaTrader 5/terminal64.exe':'eec25399ebd3171422d954fa01b75127c0356c94fe1d45d80dc27c3d0deb4ba1'}

def prior_verify():
    assert sha(PRIOR)=='a4c3050f45d2563a0e6a4d08fa7e19edddb97b9bf3990934c0ca795a86f4a51a'
    p=sealed(PRIOR);review=sealed(ROOT/'reports/native-pipe-048-completion-review.json')
    assert review['review_passed'] and review['frozen_input_coverage_complete'] and review['final_source_sha256']==sha(PRIOR)
    assert not p['runtime_completed'] and not p['original_checker_passed'] and p['disabled_proof_passed']
    bindings=dict(p['source_and_evidence_bindings']);assert len(bindings)==1496
    for n,h in bindings.items():
        if n in CURRENT:
            pair=p['installed_dependency_mismatches'][n]
            assert pair['frozen_sha256']==h and pair['observed_sha256']==CURRENT[n]==sha(bound(n))
        else:assert sha(bound(n))==h,n
    assert sha(PRIOR.with_suffix('.zip'))==p['archive_sha256']
    internal=set(bindings)-set(p['archive_external_bindings'])
    with zipfile.ZipFile(PRIOR.with_suffix('.zip')) as z:
        assert z.testzip() is None and len(z.infolist())==1409 and set(z.namelist())==internal
        for n in internal:assert hashlib.sha256(z.read(n)).hexdigest()==bindings[n]
    change=sealed(ROOT/'reports/native-pipe-048-installed-change.json')
    assert len(change['signatures'])==2
    for s in change['signatures']:
        assert s['signature_status']=='Valid' and s['version']=='5.0.0.6244'
        assert s['subject']=='CN=MetaQuotes Ltd., O=MetaQuotes Ltd., S=Lemesos, C=CY'
        assert s['thumbprint']=='5A64A7AED24C33DED342D01D01FA5286F06DA6DC'
        assert s['sha256']==CURRENT['/mnt/c/Program Files/MetaTrader 5/'+s['file']]
    return p,bindings

def freeze():
    from forex_demo_lab.native_pipe_049 import date_guard
    date_guard(time.time_ns()//1000000);prior,bindings=prior_verify()
    for n in HANDOFF:bindings.pop(n)
    bindings.update(CURRENT) # New declared phase only; original snapshots unchanged.
    for name in ('native-pipe-048-final-source.json','native-pipe-048-final-source.sha256',
        'native-pipe-048-final-source.zip','native-pipe-048-completion-review.json','native-pipe-048-completion-review.sha256'):
        p=ROOT/'reports'/name;bindings[p.relative_to(ROOT).as_posix()]=sha(p)
    for pattern in PATTERNS:
        for p in ROOT.glob(pattern):bindings[p.relative_to(ROOT).as_posix()]=sha(p)
    assert not LEDGER.exists()
    write(LEDGER,dict(bindings=bindings,declared_date='2026-10-07',expected_tests=718,new_tests=36,
        wire_differential_frames=87,prior_snapshot_bindings=1496,prior_snapshot_members=1409,
        installed_dependency_rollover=prior['installed_dependency_mismatches'],expected_running_build=6244,
        phase='49000000000000000000000000000001',policy_fixture_digest='49'*32,
        maximum_sdk_connections=1,maximum_script_arms=3,maximum_grants=1,maximum_session_seconds=900,
        maximum_io_ms=2000,maximum_native_fixture_suites=1,maximum_compiler_invocations=1,maximum_deployments=1,
        quote_reads=0,orders_available=False,fresh_performance_eligible=False,annual_eligible=False))
    print(json.dumps(dict(frozen=True,bindings=len(bindings),expected_tests=718)))

def verify():
    ledger=sealed(LEDGER)
    for n,h in ledger['bindings'].items():assert sha(bound(n))==h,n
    return ledger

def regression():
    ledger=verify();start=time.monotonic()
    r=unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.discover(str(ROOT/'tests')))
    passed=r.wasSuccessful() and r.testsRun==718 and not r.skipped
    write(ROOT/'reports/native-pipe-049-regression.json',dict(passed=passed,tests_run=r.testsRun,new_tests=36,
        errors=len(r.errors),failures=len(r.failures),skipped=len(r.skipped),wire_differential_frames=87,
        ledger_sha256=sha(LEDGER),elapsed_seconds=time.monotonic()-start,sdk_connections=0,quote_reads=0,orders_available=False))
    if not passed:raise SystemExit(1)

def build():
    verify();assert os.name=='nt'
    assert sealed(ROOT/'reports/native-pipe-049-native-tests.json')['passed']
    assert sealed(ROOT/'reports/native-pipe-049-regression.json')['passed']
    write(ROOT/'reports/native-pipe-049-build-started.json',dict(ledger_sha256=sha(LEDGER),
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
        directory=root/('compiler049-'+uuid.uuid4().hex);directory.mkdir(exist_ok=False)
        for name in ('ForexDemoPipeFixture049.mq5','CaptureWire047.mqh','CapturePermit046.mqh','ClockGuard042.mqh'):
            source=ROOT/'mt5/Scripts'/name;dest=directory/name
            with source.open('rb') as src,dest.open('xb') as dst:
                for data in iter(lambda:src.read(1048576),b''):dst.write(data)
                dst.flush();os.fsync(dst.fileno())
            assert sha(dest)==sha(source)
        verify();assert native['metadata'](shell)['editor_processes']==0
        count=1
        result=native['hidden_process'](native_command(editor,directory/'ForexDemoPipeFixture049.mq5',directory/'compile.log'),editor,60)
        exit_code=result.returncode;log=(directory/'compile.log').read_text(encoding='utf-16')
        artifact=directory/'ForexDemoPipeFixture049.ex5'
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
    write(ROOT/'reports/native-pipe-049-build.json',dict(ledger_sha256=sha(LEDGER),compiler_invocations=count,
        compiler_exit_code=exit_code,compiled=compiled,errors=errors,warnings=warnings,stop_reason=reason,
        output_bindings=outputs,effective_policy_before=before['effective_policy'] if before else None,
        effective_policy_after=after['effective_policy'] if after else None,execution_policy_changed=False,
        fixture_attached=False,fixture_runtime_executed=False,sdk_connections=0,quote_reads=0,orders_available=False))
    print(json.dumps(dict(compiled=compiled,errors=errors,warnings=warnings,compiler_invocations=count,stop_reason=reason)))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=('freeze','verify','test','build'));action=p.parse_args().action
    {'freeze':freeze,'verify':lambda:print(json.dumps(dict(verified=len(verify()['bindings'])))),'test':regression,'build':build}[action]()
