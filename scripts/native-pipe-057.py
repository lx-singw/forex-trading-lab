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
HANDOFF=OLD['HANDOFF'];LEDGER=ROOT/'reports/native-pipe-057-ledger.json'
PRIOR=ROOT/'reports/transport-diagnostics-056-final-source.json'
PATTERNS=('scripts/*057.py','src/forex_demo_lab/*057.py','tests/*057.py','docs/*057*.md',
    'mt5/Scripts/*057*','mt5/Tests/*057*')
CURRENT={
 '/mnt/c/Program Files/MetaTrader 5/metaeditor64.exe':'7d6e42249722888429bb3d4e90e4a810d745f195cfeda9c99a06f24605b29428',
 '/mnt/c/Program Files/MetaTrader 5/terminal64.exe':'eec25399ebd3171422d954fa01b75127c0356c94fe1d45d80dc27c3d0deb4ba1'}

def prior_verify():
    assert sha(PRIOR)=='255d91cc3823a9744cb051e5b0274a05241a2ce4b404c1277112f0d69b665dab'
    p=sealed(PRIOR);review=sealed(ROOT/'reports/transport-diagnostics-056-completion-review.json')
    assert review['review_passed'] and review['frozen_input_coverage_complete'] and review['final_source_sha256']==sha(PRIOR)
    assert review['next_plan_sha256']==sha(ROOT/'docs/NATIVE-TRANSPORT-057-PLAN.md')
    bindings=dict(p['source_and_evidence_bindings']);assert len(bindings)==1789
    for n,h in bindings.items():assert sha(bound(n))==h,n
    helper=runpy.run_path(str(ROOT/'scripts/transport-diagnostics-056.py'))
    helper['verify_archive'](PRIOR,p,1667)
    helper['API']['original_failure']()
    assert p['tests_passed']==842 and not p['actual_mt5_repair_verified']
    return p,bindings

def freeze():
    assert sealed(ROOT/'reports/native-pipe-057-installed-pins.json')['pins_match']
    from forex_demo_lab.native_pipe_057 import date_guard
    date_guard(time.time_ns()//1000000);prior,bindings=prior_verify()
    for n in HANDOFF:bindings.pop(n)
    bindings.update(CURRENT) # New declared phase only; original snapshots unchanged.
    for name in ('transport-diagnostics-056-final-source.json','transport-diagnostics-056-final-source.sha256',
        'transport-diagnostics-056-final-source.zip','transport-diagnostics-056-completion-review.json','transport-diagnostics-056-completion-review.sha256'):
        p=ROOT/'reports'/name;bindings[p.relative_to(ROOT).as_posix()]=sha(p)
    for pattern in (*PATTERNS,'reports/native-pipe-057-installed-pins.json','reports/native-pipe-057-installed-pins.sha256'):
        for p in ROOT.glob(pattern):bindings[p.relative_to(ROOT).as_posix()]=sha(p)
    assert not LEDGER.exists()
    write(LEDGER,dict(bindings=bindings,declared_date='2026-10-07',expected_tests=874,new_tests=32,
        wire_differential_frames=87,prior_snapshot_bindings=1789,prior_snapshot_members=1667,
        installed_build=6244,expected_running_build=6244,native_disabled_proof_required=True,
        phase='57000000000000000000000000000001',policy_fixture_digest='57'*32,
        maximum_sdk_connections=0,maximum_script_arms=0,maximum_grants=0,maximum_session_seconds=900,
        maximum_io_ms=2000,maximum_native_fixture_suites=1,maximum_compiler_invocations=1,maximum_deployments=0,
        quote_reads=0,orders_available=False,fresh_performance_eligible=False,annual_eligible=False))
    selected={n:h for n,h in bindings.items() if not n.startswith('/') and any((ROOT/n).match(p) for p in PATTERNS)}
    archive=ROOT/'reports/native-pipe-057-initial-source.zip'
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED) as z:
        for n in sorted(selected):z.write(ROOT/n,n)
    write(ROOT/'reports/native-pipe-057-initial-source.json',dict(bindings=selected,archive_sha256=sha(archive),ledger_sha256=sha(LEDGER)))
    print(json.dumps(dict(frozen=True,bindings=len(bindings),expected_tests=874)))

def verify():
    ledger=sealed(LEDGER)
    for n,h in ledger['bindings'].items():assert sha(bound(n))==h,n
    return ledger

def regression():
    ledger=verify();write(ROOT/'reports/native-pipe-057-regression-started.json',dict(ledger_sha256=sha(LEDGER),suite_consumed=True));start=time.monotonic()
    r=unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.discover(str(ROOT/'tests')))
    passed=r.wasSuccessful() and r.testsRun==874 and not r.skipped
    write(ROOT/'reports/native-pipe-057-regression.json',dict(passed=passed,tests_run=r.testsRun,new_tests=32,
        errors=len(r.errors),failures=len(r.failures),skipped=len(r.skipped),wire_differential_frames=87,
        ledger_sha256=sha(LEDGER),elapsed_seconds=time.monotonic()-start,sdk_connections=0,quote_reads=0,orders_available=False))
    if not passed:raise SystemExit(1)

def build():
    verify();assert os.name=='nt'
    assert sealed(ROOT/'reports/native-pipe-057-native-tests.json')['passed']
    assert sealed(ROOT/'reports/native-pipe-057-regression.json')['passed']
    write(ROOT/'reports/native-pipe-057-build-started.json',dict(ledger_sha256=sha(LEDGER),
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
        directory=root/('compiler057-'+uuid.uuid4().hex);directory.mkdir(exist_ok=False)
        for name in ('ForexDemoPipeFixture057.mq5','CaptureReadDiagnostics056.mqh','CaptureWireDiagnostics053.mqh','CaptureWire047.mqh','CapturePermit046.mqh','ClockGuard042.mqh'):
            source=ROOT/'mt5/Scripts'/name;dest=directory/name
            with source.open('rb') as src,dest.open('xb') as dst:
                for data in iter(lambda:src.read(1048576),b''):dst.write(data)
                dst.flush();os.fsync(dst.fileno())
            assert sha(dest)==sha(source)
        verify();assert native['metadata'](shell)['editor_processes']==0
        count=1
        result=native['hidden_process'](native_command(editor,directory/'ForexDemoPipeFixture057.mq5',directory/'compile.log'),editor,60)
        exit_code=result.returncode;log=(directory/'compile.log').read_text(encoding='utf-16')
        artifact=directory/'ForexDemoPipeFixture057.ex5'
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
    write(ROOT/'reports/native-pipe-057-build.json',dict(ledger_sha256=sha(LEDGER),compiler_invocations=count,
        compiler_exit_code=exit_code,compiled=compiled,errors=errors,warnings=warnings,stop_reason=reason,
        output_bindings=outputs,effective_policy_before=before['effective_policy'] if before else None,
        effective_policy_after=after['effective_policy'] if after else None,execution_policy_changed=False,
        fixture_attached=False,fixture_runtime_executed=False,sdk_connections=0,quote_reads=0,orders_available=False))
    print(json.dumps(dict(compiled=compiled,errors=errors,warnings=warnings,compiler_invocations=count,stop_reason=reason)))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=('freeze','verify','test','build'));action=p.parse_args().action
    {'freeze':freeze,'verify':lambda:print(json.dumps(dict(verified=len(verify()['bindings'])))),'test':regression,'build':build}[action]()
