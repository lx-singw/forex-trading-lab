"""Freeze/test/build the no-market transport fixture; never attach or launch MT5."""
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
OLD=runpy.run_path(str(ROOT/'scripts/capture-budget-046.py'))
API=OLD['API'];sha,write,sealed=API['sha'],API['write'],API['sealed'];HANDOFF=API['HANDOFF']
PRIOR=ROOT/'reports/capture-budget-046-final-source.json';LEDGER=ROOT/'reports/capture-transport-047-ledger-r3.json'
PATTERNS=('docs/*047*.md','scripts/*047.py','src/forex_demo_lab/*047.py','tests/*047.py','mt5/Scripts/*047*','mt5/Tests/*047*')

def bound(name):
    if os.name=='nt' and name.startswith('/') and not name.startswith('/mnt/c/'):
        return Path('\\\\wsl.localhost\\Ubuntu'+name.replace('/','\\'))
    return API['bound_path'](name)

def prior_verify(allow_handoff=False):
    assert sha(PRIOR)=='13f03bb324da51b2464b3084eb62802b04dd35c6bce8abda7565efdae4bf1056'
    prior=sealed(PRIOR);bindings={n:h for g,v in prior.items() if g.endswith('_bindings') and g!='archive_external_bindings' for n,h in v.items()}
    assert len(bindings)==1395
    for n,h in bindings.items():assert sha(bound(n))==h or allow_handoff and n in HANDOFF,n
    assert sha(PRIOR.with_suffix('.zip'))==prior['archive_sha256']
    internal={n:h for n,h in bindings.items() if n not in prior['archive_external_bindings']}
    with zipfile.ZipFile(PRIOR.with_suffix('.zip')) as z:
        assert z.testzip() is None and len(z.infolist())==1320 and set(z.namelist())==set(internal)
        for n,h in internal.items():assert hashlib.sha256(z.read(n)).hexdigest()==h
    return prior,bindings

def freeze():
    prior,bindings=prior_verify();inputs={n:h for n,h in bindings.items() if n not in HANDOFF}
    for suffix in ('.json','.sha256','.zip'):
        p=PRIOR.with_suffix(suffix);inputs[p.relative_to(ROOT).as_posix()]=sha(p)
    for pattern in PATTERNS:
        for p in ROOT.glob(pattern):inputs[p.relative_to(ROOT).as_posix()]=sha(p)
    for pattern in ('reports/capture-transport-047-preflight*','reports/capture-transport-047-ledger.json','reports/capture-transport-047-ledger.sha256'):
        for p in ROOT.glob(pattern):inputs[p.relative_to(ROOT).as_posix()]=sha(p)
    for pattern in ('reports/capture-transport-047-ledger-r2.*','reports/capture-transport-047-native.json','reports/capture-transport-047-native.sha256'):
        for p in ROOT.glob(pattern):inputs[p.relative_to(ROOT).as_posix()]=sha(p)
    required={'scripts/capture-transport-047.py','scripts/test-windows-pipe-047.py','src/forex_demo_lab/windows_pipe_047.py',
        'src/forex_demo_lab/capture_budget_047.py','src/forex_demo_lab/capture_wire_047.py',
        'tests/test_capture_transport_047.py','mt5/Scripts/ForexDemoPipeFixture047.mq5','mt5/Scripts/CaptureWire047.mqh',
        'mt5/Tests/CaptureWire047.cpp','docs/CAPTURE-TRANSPORT-047-PROTOCOL.md'}
    assert required<=set(inputs) and not LEDGER.exists()
    write(LEDGER,dict(bindings=inputs,prior_bindings_verified=1395,prior_archive_members_verified=1320,
        prior_external_bindings_verified=75,new_tests=12,expected_tests=666,wire_differential_frames=100,
        maximum_native_suites=1,maximum_compiler_invocations=1,mt5_runtime_authorized=False,declared_date='2026-10-07',
        sdk_connections=0,quote_reads=0,orders_available=False))
    print(json.dumps(dict(frozen=True,input_bindings=len(inputs))))

def verify():
    ledger=sealed(LEDGER)
    for n,h in ledger['bindings'].items():assert sha(bound(n))==h,n
    return ledger

def regression():
    verify();started=time.monotonic()
    result=unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.discover(str(ROOT/'tests')))
    passed=result.wasSuccessful() and result.testsRun==666 and not result.skipped
    write(ROOT/'reports/capture-transport-047-regression-r3.json',dict(passed=passed,tests_run=result.testsRun,
        tests_passed=result.testsRun-len(result.errors)-len(result.failures)-len(result.skipped),new_tests=12,
        errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped),elapsed_seconds=time.monotonic()-started,
        ledger_sha256=sha(LEDGER),wire_differential_frames=100,sdk_connections=0,quote_reads=0,orders_available=False))
    if not passed:raise SystemExit(1)

def build():
    verify();assert os.name=='nt'
    assert sealed(ROOT/'reports/capture-transport-047-native-r3.json')['passed']
    assert sealed(ROOT/'reports/capture-transport-047-regression-r3.json')['passed']
    write(ROOT/'reports/capture-transport-047-build-started.json',dict(ledger_sha256=sha(LEDGER),maximum_compiler_invocations=1,
        reservation_consumed=True,mt5_runtime_authorized=False,orders_available=False))
    native=runpy.run_path(str(ROOT/'scripts/native-compiler-042.py'))
    from forex_demo_lab.native_compiler_042 import native_command,compile_evidence
    settings=sealed(ROOT/'reports/native-compiler-042-ledger.json');shell=bound(settings['powershell_path']);editor=bound(settings['editor_path'])
    count=0;reason=None;directory=None;exit_code=None;compiled=False;errors=None;warnings=None;outputs={}
    before=None;after=None
    try:
        before=native['metadata'](shell)
        if before['editor_processes']!=0:raise ValueError()
        root=Path(settings['build_root'])
        for p in (root,*root.parents):
            if p.is_symlink() or getattr(p.stat(),'st_file_attributes',0)&0x400:raise ValueError()
        directory=root/('compiler047-'+uuid.uuid4().hex);directory.mkdir(exist_ok=False)
        for name in ('ForexDemoPipeFixture047.mq5','CaptureWire047.mqh','CapturePermit046.mqh','ClockGuard042.mqh'):
            source=ROOT/'mt5/Scripts'/name;dest=directory/name
            with source.open('rb') as src,dest.open('xb') as dst:
                for data in iter(lambda:src.read(1048576),b''):dst.write(data)
                dst.flush();os.fsync(dst.fileno())
            assert sha(dest)==sha(source)
        verify();assert native['metadata'](shell)['editor_processes']==0
        count=1
        result=native['hidden_process'](native_command(editor,directory/'ForexDemoPipeFixture047.mq5',directory/'compile.log'),editor,60)
        exit_code=result.returncode
        log=(directory/'compile.log').read_text(encoding='utf-16')
        artifact=directory/'ForexDemoPipeFixture047.ex5'
        evidence=compile_evidence(True,log,artifact.stat().st_size if artifact.exists() else 0)
        compiled,errors,warnings=evidence['compiled'],evidence['errors'],evidence['warnings']
        if not compiled:reason='native_compilation_failed'
    except subprocess.TimeoutExpired:reason='owned_compiler_timeout_no_retry'
    except Exception:reason='native_build_failed_details_redacted'
    try:after=native['metadata'](shell)
    except Exception:after=None
    if directory is not None:
        for p in directory.iterdir():
            if p.is_file():outputs[API['external_name'](str(p))]=sha(p)
    write(ROOT/'reports/capture-transport-047-build.json',dict(ledger_sha256=sha(LEDGER),compiler_invocations=count,
        compiler_exit_code=exit_code,compiled=compiled,errors=errors,warnings=warnings,stop_reason=reason,
        output_bindings=outputs,effective_policy_before=before['effective_policy'] if before else None,
        effective_policy_after=after['effective_policy'] if after else None,execution_policy_changed=False,
        fixture_attached=False,fixture_runtime_executed=False,sdk_connections=0,quote_reads=0,orders_available=False))
    print(json.dumps(dict(compiled=compiled,errors=errors,warnings=warnings,compiler_invocations=count,stop_reason=reason)))

def finalize():
    verify();prior,bindings=prior_verify();tests=sealed(ROOT/'reports/capture-transport-047-regression-r3.json')
    native=sealed(ROOT/'reports/capture-transport-047-native-r3.json');build=sealed(ROOT/'reports/capture-transport-047-build.json')
    assert tests['passed'] and tests['tests_passed']==666 and native['passed'] and native['cases_passed']==14
    assert native['cancellation_drained'] and not native['actual_mt5_peer_tested']
    assert build['compiler_invocations']<=1 and not build['fixture_runtime_executed']
    for n,h in build['output_bindings'].items():assert sha(bound(n))==h
    assert (ROOT/'docs/CAPTURE-TRANSPORT-047-RESULTS.md').is_file()
    assert (ROOT/'docs/NATIVE-PIPE-048-PLAN.md').is_file()
    text=(f'Latest — 2026-10-07: transport047 preparation sealed; read CAPTURE-TRANSPORT-047-RESULTS.md. '
        f'666 tests (12 new)/100 shared MQL wire frames,14 Windows no-market pipe cases pass; MT5 fixture compiled {build["compiled"]}, '
        f'errors {build["errors"]}, warnings {build["warnings"]}, compiler calls {build["compiler_invocations"]}. '
        'Explicit logon DACL/first instance/remote rejection/both Windows peer checks/IO cancellation; synthetic guards only. '
        'Actual MT5 peer/MQL runtime untested; no attachment/deployment, SDK/quotes/history/strategy/orders/settings changes. '
        'New dated047 fixture never reads prices; old042 prohibited. Six045 captures/044 timeout unchanged. '
        'Next NATIVE-PIPE-048-PLAN.md separate bounded no-market MQL fixture session, not executed. '
        'Clock/coverage/cost/flags/033/035 failures, consumed2025/reservedNov–Dec2026/provider stops retained; '
        'fresh/annual eligibility/orders false. Earlier entries are historical.\n\n')
    groups={g:dict(v) for g,v in prior.items() if g.endswith('_bindings') and g!='archive_external_bindings'}
    for n in HANDOFF:
        p=ROOT/n;old=p.read_text();i=old.index('\n')+1;p.write_text(old[:i]+'\n'+text+old[i:]);groups['source_bindings'][n]=sha(p)
    prior_verify(True)
    for pattern in (*PATTERNS,'docs/NATIVE-PIPE-048-PLAN.md'):
        for p in ROOT.glob(pattern):groups['source_bindings'][p.relative_to(ROOT).as_posix()]=sha(p)
    for pattern in ('reports/capture-transport-047-*.json','reports/capture-transport-047-*.sha256'):
        for p in ROOT.glob(pattern):groups['report_bindings'][p.relative_to(ROOT).as_posix()]=sha(p)
    for suffix in ('.json','.sha256','.zip'):
        p=PRIOR.with_suffix(suffix);groups['report_bindings'][p.relative_to(ROOT).as_posix()]=sha(p)
    groups['capture_transport_047_native_bindings']=build['output_bindings']
    bindings={n:h for v in groups.values() for n,h in v.items()};assert len(bindings)==sum(map(len,groups.values()))
    external={n:h for n,h in bindings.items() if n.startswith('/') or n.endswith('.zip') or
        n.startswith('data/') and n.endswith('.gz') and 'synthetic' not in n and 'walk-forward' not in n}
    internal={n:h for n,h in bindings.items() if n not in external}
    for n,h in bindings.items():assert sha(bound(n))==h,n
    final=ROOT/'reports/capture-transport-047-final-source.json';archive=final.with_suffix('.zip')
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED) as z:
        for n in sorted(internal):z.write(ROOT/n,n)
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None and set(z.namelist())==set(internal)
        for n,h in internal.items():assert hashlib.sha256(z.read(n)).hexdigest()==h
    write(final,dict(**groups,archive_external_bindings=external,archive_sha256=sha(archive),
        archive_members_verified=len(internal),external_bindings_verified=len(external),tests_passed=666,
        native_windows_cases_passed=14,fixture_compiled=build['compiled'],native_mt5_runtime_verified=False,
        sdk_connections=0,quote_reads=0,orders_available=False,fresh_performance_eligible=False,annual_eligible=False,
        next_plan='docs/NATIVE-PIPE-048-PLAN.md',next_plan_executed=False))
    print(json.dumps(dict(bindings=len(bindings),members=len(internal),external=len(external),sha256=sha(final))))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=('freeze','test','build','finalize'));a=p.parse_args()
    {'freeze':freeze,'test':regression,'build':build,'finalize':finalize}[a.action]()
