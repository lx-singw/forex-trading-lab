"""One reserved native argument fixture and isolated compilation; never deploys."""
import argparse
import hashlib
import json
import os
from pathlib import Path,PureWindowsPath
import runpy
import subprocess
import sys
import uuid
import zipfile

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
OLD=runpy.run_path(str(ROOT/'scripts/clock-semantics-038.py'))
sha,write,sealed=OLD['sha'],OLD['write'],OLD['sealed'];HANDOFF=OLD['HANDOFF'];bound_path=OLD['bound_path']
from forex_demo_lab.compiler_launch_039 import (VERSION,SOURCE,HEADER,INVOKER,FIXTURE,ECHO,
    staging_command,ps_quote,invoke_args,sanitized_process,validated_result)

PRIOR=ROOT/'reports/clock-semantics-038-final-source.json'
LEDGER=ROOT/'reports/compiler-launch-039-ledger.json'
RESERVATION=ROOT/'reports/compiler-launch-039-reservation.json'
OUTPUT=ROOT/'reports/compiler-launch-039-build.json'
RUNTIME=ROOT/'reports/compiler-launch-039-runtime.json'
MQL='mt5/Scripts/'+SOURCE;GUARD='mt5/Scripts/'+HEADER


def prior_verify(allow_handoff=False):
    assert sha(PRIOR)=='34c557394ffa2f1dbd9a34331ea2de8c26c0c4d4fb9d098830b37711ee1c344d'
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
    assert len(bindings)==1145 and len(external)==49 and all(bindings[n]==h for n,h in external.items())
    assert sha(PRIOR.with_suffix('.zip'))==prior['archive_sha256']
    with zipfile.ZipFile(PRIOR.with_suffix('.zip')) as z:
        assert z.testzip() is None and len(z.infolist())==1096 and set(z.namelist())==set(bindings)-set(external)
        for n in z.namelist():assert hashlib.sha256(z.read(n)).hexdigest()==bindings[n],n
    assert prior['observer_compiled'] is prior['observer_runtime_executed'] is prior['orders_available'] is False
    return dict(bindings_verified=1145,archived_members_verified=1096,external_bindings_verified=49,allowed_handoff_changes=changes)


def external_name(value):
    p=PureWindowsPath(value)
    if len(p.drive)!=2 or p.drive[1]!=':':raise ValueError('absolute_windows_drive_required')
    return '/mnt/'+p.drive[0].lower()+p.as_posix()[2:]


def freeze():
    assert os.name!='nt';previous=prior_verify();tests=sealed(ROOT/'reports/compiler-launch-039-tests.json')
    assert tests['passed'] and tests['tests_run']==tests['tests_passed']==566 and tests['new_tests']==20
    runtime=sealed(RUNTIME);bindings={}
    for pattern in ('src/**/*.py','scripts/*039*','tests/*039*.py','docs/*039*.md','reports/compiler-launch-039-runtime*',
                    'reports/compiler-launch-039-tests*','reports/clock-semantics-038-*',
                    MQL,GUARD,'mt5/Tests/ClockGuard038.cpp'):
        for p in ROOT.glob(pattern):bindings[p.relative_to(ROOT).as_posix()]=sha(p)
    editor='/mnt/c/Program Files/MetaTrader 5/metaeditor64.exe'
    shell='/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe'
    native_files=[editor,shell,external_name(runtime['executable']),external_name(runtime['python_dll']),
                  external_name(str(PureWindowsPath(runtime['python_dll']).parent/'python.exe'))]
    for n in native_files:bindings[n]=sha(bound_path(n))
    for stem in ('ledger','reservation','build','checks','review','final-source'):
        assert not (ROOT/('reports/compiler-launch-039-'+stem+'.json')).exists()
    write(LEDGER,dict(version=VERSION,bindings=bindings,prior_snapshot_verification=previous,
        editor_path=editor,powershell_path=shell,python_path=external_name(runtime['executable']),
        build_root=str(PureWindowsPath(runtime['local_app_data'])/'ForexDemoLab'/'builds'),
        maximum_argument_fixture_invocations=1,maximum_compiler_invocations=1,
        maximum_market_requests=0,maximum_native_connections=0,maximum_external_requests=0,
        observer_runtime_authorized=False,fresh_performance_eligible=False,annual_eligible=False,orders_available=False))
    write(RESERVATION,dict(version=VERSION,ledger_sha256=sha(LEDGER),maximum_argument_fixture_invocations=1,
        maximum_compiler_invocations=1,maximum_market_requests=0,observer_runtime_authorized=False,
        execution_policy_change_authorized=False,orders_available=False))
    print(json.dumps(dict(frozen=True,bindings=len(bindings))))


def verify():
    ledger=sealed(LEDGER)
    for n,h in ledger['bindings'].items():assert sha(bound_path(n))==h,n
    assert sealed(RESERVATION)['ledger_sha256']==sha(LEDGER)
    return ledger


def command(shell,text,timeout=15):
    return subprocess.run([str(shell),'-NoProfile','-NonInteractive','-Command',text],capture_output=True,text=True,timeout=timeout)


def metadata(shell,script):
    text='''$ErrorActionPreference='Stop'
$f=Get-Item -LiteralPath '''+ps_quote(str(script))+'''
$tokens=$null;$errors=$null
[Management.Automation.Language.Parser]::ParseFile($f.FullName,[ref]$tokens,[ref]$errors) | Out-Null
ConvertTo-Json -Compress @{parser_errors=@($errors).Count;effective_policy=(Get-ExecutionPolicy).ToString();
signature_status=(Get-AuthenticodeSignature -LiteralPath $f.FullName).Status.ToString();
local_app_data=[Environment]::GetFolderPath('LocalApplicationData');editor_processes=@(Get-Process metaeditor64 -ErrorAction SilentlyContinue).Count}
'''
    result=command(shell,text)
    if result.returncode!=0:return None,sanitized_process(result)
    value=json.loads(result.stdout)
    assert set(value)=={'parser_errors','effective_policy','signature_status','local_app_data','editor_processes'}
    assert type(value['parser_errors']) is int and type(value['editor_processes']) is int
    assert value['effective_policy'] in ('Restricted','AllSigned','RemoteSigned','Unrestricted','Bypass','Undefined','Default')
    assert value['signature_status'] in ('Valid','UnknownError','NotSigned','HashMismatch','NotTrusted','NotSupportedFileFormat','Incompatible')
    return value,sanitized_process(result)


def stage(shell,root,token,files,fixture=False):
    result=command(shell,staging_command(root,token,files,fixture))
    if result.returncode!=0:raise ValueError('native_staging_failed')
    value=json.loads(result.stdout)
    assert set(value)=={'outcome','directory','hashes'} and value['outcome']=='staged'
    wanted=PureWindowsPath(root)/('compiler039-'+('fixture-' if fixture else '')+token)
    assert PureWindowsPath(value['directory'])==wanted and set(value['hashes'])==set(files)
    for name,source in files.items():assert value['hashes'][name]==sha(source) and sha(Path(str(wanted/name)))==sha(source),name
    return Path(str(wanted))


def output_bindings(directory,allowed):
    if directory is None:return {}
    out={}
    for name in allowed:
        path=directory/name
        if path.is_file():out[external_name(str(path))]=sha(path)
    return out


def run():
    ledger=verify();assert os.name=='nt' and not OUTPUT.exists()
    shell=bound_path(ledger['powershell_path']);editor=bound_path(ledger['editor_path']);python=bound_path(ledger['python_path'])
    before=None;after=None;before_process=None;after_process=None;fixture=None;compile=None;fixture_dir=None;build_dir=None
    fixture_process=None;compile_process=None;fixture_calls=0;compiler_calls=0;reason=None
    try:
        before,before_process=metadata(shell,ROOT/'scripts/compile-clock-observer-039.ps1')
        if before is None:raise ValueError('native_metadata_failed')
        if before['parser_errors']!=0:raise ValueError('native_parser_rejected')
        if before['editor_processes']!=0:raise ValueError('existing_editor_rejected')
        if PureWindowsPath(before['local_app_data'])/'ForexDemoLab'/'builds'!=PureWindowsPath(ledger['build_root']):
            raise ValueError('native_build_root_changed')
        fixture_dir=stage(shell,ledger['build_root'],uuid.uuid4().hex,{
            FIXTURE:ROOT/'scripts/argument-fixture-039.ps1',ECHO:ROOT/'scripts/argument-echo-039.py'},True)
        fixture_calls=1
        result=subprocess.run(invoke_args(shell,fixture_dir/FIXTURE,BuildDirectory=fixture_dir,PythonExe=python),
                              capture_output=True,text=True,timeout=25)
        fixture_process=sanitized_process(result)
        if result.returncode!=0:raise ValueError('local_fixture_launch_denied')
        fixture=validated_result(result.stdout,'fixture')
        if not fixture['fixture_passed']:raise ValueError('native_argument_fixture_failed')
        argv=json.loads((fixture_dir/'fixture-argv.json').read_text(encoding='utf-8-sig'))
        assert argv==dict(arguments_equal=True,argv=['/compile:'+str(fixture_dir/'source with spaces.mq5'),
                                                   '/log:'+str(fixture_dir/'log with spaces.log')])
        build_dir=stage(shell,ledger['build_root'],uuid.uuid4().hex,{
            SOURCE:ROOT/MQL,HEADER:ROOT/GUARD,INVOKER:ROOT/'scripts/compile-clock-observer-039.ps1'})
        compiler_calls=1
        result=subprocess.run(invoke_args(shell,build_dir/INVOKER,BuildDirectory=build_dir,MetaEditor=editor),
                              capture_output=True,text=True,timeout=75)
        compile_process=sanitized_process(result)
        if result.returncode!=0:raise ValueError('local_compiler_invoker_denied')
        compile=validated_result(result.stdout,'compile')
    except subprocess.TimeoutExpired:
        reason='parent_watchdog_expired_no_retry'
    except ValueError as exc:
        allowed={'native_metadata_failed','native_parser_rejected','existing_editor_rejected','native_build_root_changed',
                 'native_staging_failed','local_fixture_launch_denied','native_argument_fixture_failed','local_compiler_invoker_denied'}
        reason=str(exc) if str(exc) in allowed else 'native_validation_failed_details_redacted'
    except Exception:
        reason='native_driver_failed_details_redacted'
    try:
        after,after_process=metadata(shell,ROOT/'scripts/compile-clock-observer-039.ps1')
    except Exception:
        after=None
    write(OUTPUT,dict(version=VERSION,ledger_sha256=sha(LEDGER),reservation_sha256=sha(RESERVATION),
        stop_reason=reason,metadata_before=before,metadata_after=after,
        metadata_process_before=before_process,metadata_process_after=after_process,
        observed_policy_unchanged=before is not None and after is not None and before['effective_policy']==after['effective_policy'],
        fixture_invocations=fixture_calls,compiler_invoker_calls=compiler_calls,fixture_result=fixture,compile_result=compile,
        fixture_process=fixture_process,compiler_process=compile_process,
        fixture_output_bindings=output_bindings(fixture_dir,(FIXTURE,ECHO,'fixture-argv.json')),
        compile_output_bindings=output_bindings(build_dir,(SOURCE,HEADER,INVOKER,'compile.log','ForexDemoClockObserver038.ex5')),
        observer_compiled=compile is not None and compile['compiled'],observer_attached=False,observer_runtime_executed=False,
        market_requests=0,native_connections=0,external_requests=0,historical_downloads=0,strategy_replays=0,
        execution_policy_changed=False,fresh_performance_eligible=False,annual_eligible=False,orders_available=False))
    print(json.dumps(dict(fixture_invocations=fixture_calls,compiler_invoker_calls=compiler_calls,fixture_result=fixture,
                         compile_result=compile,stop_reason=reason,observer_runtime_executed=False)))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=('freeze','verify','run'))
    {'freeze':freeze,'verify':lambda:print(json.dumps(dict(verified=len(verify()['bindings'])))),'run':run}[parser.parse_args().action]()
