"""One reserved direct native compiler process; no PowerShell script execution."""
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
OLD=runpy.run_path(str(ROOT/'scripts/native-compiler-041.py'))
sha,write,sealed=OLD['sha'],OLD['write'],OLD['sealed'];HANDOFF=OLD['HANDOFF'];bound_path=OLD['bound_path']
external_name=OLD['external_name'];output_bindings=OLD['output_bindings']
from forex_demo_lab.native_compiler_042 import (SOURCE,HEADER,ECHO,VERSION,native_command,
    module_environment,staging_command,fixture_expected,compile_evidence,owned_directory)
PRIOR=ROOT/'reports/native-compiler-041-final-source.json'
LEDGER=ROOT/'reports/native-compiler-042-ledger.json'
RESERVATION=ROOT/'reports/native-compiler-042-reservation.json'
OUTPUT=ROOT/'reports/native-compiler-042-build.json'
STARTED=ROOT/'reports/native-compiler-042-started.json'
MQL='mt5/Scripts/'+SOURCE;GUARD='mt5/Scripts/'+HEADER

def prior_verify(allow_handoff=False):
    assert sha(PRIOR)=='6e2d5f7cea92d989a3fb211051e1300a55dabbf55f0a4fe26dbbad65c9dba16a'
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
    assert len(bindings)==1251 and len(external)==62 and all(bindings[n]==h for n,h in external.items())
    assert sha(PRIOR.with_suffix('.zip'))==prior['archive_sha256']
    with zipfile.ZipFile(PRIOR.with_suffix('.zip')) as z:
        assert z.testzip() is None and len(z.infolist())==1189 and set(z.namelist())==set(bindings)-set(external)
        for n in z.namelist():assert hashlib.sha256(z.read(n)).hexdigest()==bindings[n],n
    assert prior['observer_compiled'] is True and prior['observer_runtime_executed'] is prior['orders_available'] is False
    return dict(bindings_verified=1251,archived_members_verified=1189,external_bindings_verified=62,allowed_handoff_changes=changes)

def freeze():
    assert os.name!='nt';previous=prior_verify();tests=sealed(ROOT/'reports/native-compiler-042-regression.json')
    assert tests['passed'] and tests['tests_run']==tests['tests_passed']==604 and tests['new_tests']==20
    runtime=sealed(ROOT/'reports/compiler-launch-039-runtime.json');bindings={}
    for pattern in ('src/**/*.py','scripts/*042*','tests/*042*.py','docs/*042*.md','reports/native-compiler-042-tests*','reports/native-compiler-042-regression*',
                    'reports/native-compiler-041-*','scripts/finalize-clock-observer-042.py',MQL,GUARD,'mt5/Tests/ClockGuard042.cpp'):
        for p in ROOT.glob(pattern):bindings[p.relative_to(ROOT).as_posix()]=sha(p)
    old=sealed(OLD['LEDGER'])
    for n,h in old['bindings'].items():
        if n.startswith('/'):assert sha(bound_path(n))==h;bindings[n]=h
    for module in ('Microsoft.PowerShell.Security','Microsoft.PowerShell.Management'):
        n='/mnt/c/Windows/System32/WindowsPowerShell/v1.0/Modules/'+module+'/'+module+'.psd1'
        bindings[n]=sha(bound_path(n))
    required={'scripts/native-compiler-042.py','scripts/check-native-compiler-042.py','scripts/clock-runtime-042.py',
        'scripts/check-clock-runtime-042.py','scripts/finalize-clock-observer-042.py','tests/test_clock_observer_042.py',
        'docs/CLOCK-OBSERVER-042-PLAN.md','docs/CLOCK-OBSERVER-042-PROTOCOL.md',MQL,GUARD,'mt5/Tests/ClockGuard042.cpp'}
    assert required<=set(bindings)
    sdk=sealed(ROOT/'reports/fresh-replication-035-ledger.json')
    for n,h in sdk['bindings'].items():
        if '/MetaTrader5/' in n:assert sha(bound_path(n))==h;bindings[n]=h
    terminal=external_name(sdk['terminal']);bindings[terminal]=sha(bound_path(terminal))
    for stem in ('ledger','reservation','started','build','fixture','checks','review','final-source'):
        assert not (ROOT/('reports/native-compiler-042-'+stem+'.json')).exists()
    write(LEDGER,dict(version=VERSION,bindings=bindings,prior_snapshot_verification=previous,
        editor_path=old['editor_path'],powershell_path=old['powershell_path'],python_path=old['python_path'],
        build_root=old['build_root'],maximum_fixture_invocations=1,maximum_compiler_invocations=1,
        maximum_external_requests=0,maximum_market_requests=0,observer_runtime_authorized=False,
        orders_available=False,fresh_performance_eligible=False,annual_eligible=False))
    write(RESERVATION,dict(version=VERSION,ledger_sha256=sha(LEDGER),maximum_fixture_invocations=1,
        maximum_compiler_invocations=1,maximum_market_requests=0,execution_policy_change_authorized=False,
        observer_runtime_authorized=False,orders_available=False))
    print(json.dumps(dict(frozen=True,bindings=len(bindings),prior_verified=previous)))

def verify():
    ledger=sealed(LEDGER)
    for n,h in ledger['bindings'].items():assert sha(bound_path(n))==h,n
    assert sealed(RESERVATION)['ledger_sha256']==sha(LEDGER)
    return ledger

def command(shell,text):
    return subprocess.run([str(shell),'-NoProfile','-NonInteractive','-Command',text],
        env=module_environment(shell),capture_output=True,text=True,timeout=15)

def metadata(shell):
    text="""$ErrorActionPreference='Stop'
$policy=(Get-ExecutionPolicy).ToString()
ConvertTo-Json -Compress @{effective_policy=$policy;security_module_version=(Get-Module Microsoft.PowerShell.Security).Version.ToString();
local_app_data=[Environment]::GetFolderPath('LocalApplicationData');editor_processes=@(Get-Process metaeditor64 -ErrorAction SilentlyContinue).Count}
"""
    result=command(shell,text)
    if result.returncode!=0:raise ValueError('metadata_failed')
    value=json.loads(result.stdout)
    assert set(value)=={'effective_policy','security_module_version','local_app_data','editor_processes'}
    assert value['effective_policy']=='Restricted' and value['security_module_version']=='3.0.0.0'
    assert type(value['editor_processes']) is int and value['editor_processes']>=0
    return value

def stage(shell,root,files,fixture=False):
    token=uuid.uuid4().hex;result=command(shell,staging_command(root,token,files,fixture))
    if result.returncode!=0:raise ValueError('staging_failed')
    value=json.loads(result.stdout)
    assert set(value)=={'outcome','directory','hashes'} and value['outcome']=='staged'
    directory=owned_directory(value['directory'],root,fixture)
    assert directory.name=='compiler042-'+('fixture-' if fixture else '')+token
    assert set(value['hashes'])==set(files)
    path=Path(str(directory))
    for n,source in files.items():assert value['hashes'][n]==sha(source)==sha(path/n),n
    return path

def hidden_process(command_line,executable,timeout):
    startup=subprocess.STARTUPINFO();startup.dwFlags|=subprocess.STARTF_USESHOWWINDOW;startup.wShowWindow=0
    return subprocess.run(command_line,executable=str(executable),shell=False,capture_output=True,text=True,
        timeout=timeout,startupinfo=startup,creationflags=subprocess.CREATE_NO_WINDOW)

def run():
    ledger=verify();assert os.name=='nt' and not OUTPUT.exists() and not STARTED.exists()
    # An interrupted run consumes its reservation even if no outcome was saved.
    write(STARTED,dict(ledger_sha256=sha(LEDGER),reservation_sha256=sha(RESERVATION),
        reservation_consumed=True,maximum_fixture_invocations=1,maximum_compiler_invocations=1))
    shell=bound_path(ledger['powershell_path']);editor=bound_path(ledger['editor_path']);python=bound_path(ledger['python_path'])
    before=None;after=None;fixture_dir=None;build_dir=None;fixture_calls=0;compiler_calls=0
    fixture_passed=False;compiler_started=False;compiler_completed=False;timeout_cleanup=False
    exit_code=None;fixture_exit=None;reason=None;log_text='';ex5_bytes=0
    try:
        before=metadata(shell)
        if before['editor_processes']!=0:raise ValueError('existing_editor_rejected')
        if PureWindowsPath(before['local_app_data'])/'ForexDemoLab'/'builds'!=PureWindowsPath(ledger['build_root']):
            raise ValueError('native_root_changed')
        fixture_dir=stage(shell,ledger['build_root'],{ECHO:ROOT/'scripts/argument-echo-042.py'},True)
        expected=fixture_expected(str(fixture_dir));fixture_calls=1
        result=hidden_process(native_command(python,expected[0][9:],expected[1][5:],fixture_dir/ECHO),python,10)
        fixture_exit=result.returncode
        witness=json.loads(result.stdout);fixture_passed=fixture_exit==0 and witness==dict(argv=expected)
        write(ROOT/'reports/native-compiler-042-fixture.json',dict(argv=witness.get('argv'),expected=expected,
            fixture_passed=fixture_passed,return_code=fixture_exit,ledger_sha256=sha(LEDGER),shell_used=False))
        if not fixture_passed:raise ValueError('argument_fixture_failed')
        build_dir=stage(shell,ledger['build_root'],{SOURCE:ROOT/MQL,HEADER:ROOT/GUARD})
        # Recheck exact inputs and reject existing editor immediately before native launch.
        verify();assert metadata(shell)['editor_processes']==0
        compiler_calls=1
        try:
            result=hidden_process(native_command(editor,build_dir/SOURCE,build_dir/'compile.log'),editor,60)
            compiler_started=True;compiler_completed=True;exit_code=result.returncode
        except subprocess.TimeoutExpired:
            compiler_started=True;timeout_cleanup=True;raise
        if (build_dir/'compile.log').is_file():log_text=(build_dir/'compile.log').read_text(encoding='utf-16')
        if (build_dir/'ForexDemoClockObserver042.ex5').is_file():ex5_bytes=(build_dir/'ForexDemoClockObserver042.ex5').stat().st_size
    except subprocess.TimeoutExpired:
        reason='owned_process_timeout_no_retry'
    except ValueError as exc:
        allowed={'metadata_failed','staging_failed','existing_editor_rejected','native_root_changed','argument_fixture_failed'}
        reason=str(exc) if str(exc) in allowed else 'native_validation_failed_details_redacted'
    except Exception:
        reason='native_driver_failed_details_redacted'
    try:after=metadata(shell)
    except Exception:after=None
    evidence=compile_evidence(compiler_completed,log_text,ex5_bytes)
    if compiler_completed and not evidence['compiled'] and reason is None:reason='native_compilation_failed'
    write(OUTPUT,dict(version=VERSION,ledger_sha256=sha(LEDGER),reservation_sha256=sha(RESERVATION),
        metadata_before=before,metadata_after=after,observed_policy_unchanged=before is not None and after is not None and
        before['effective_policy']==after['effective_policy'],stop_reason=reason,
        fixture_invocations=fixture_calls,fixture_passed=fixture_passed,fixture_exit_code=fixture_exit,
        compiler_invocations=compiler_calls,compiler_started=compiler_started,compiler_completed=compiler_completed,
        compiler_exit_code=exit_code,owned_timeout_cleanup=timeout_cleanup,**evidence,ex5_bytes=ex5_bytes,
        fixture_output_bindings=output_bindings(fixture_dir,(ECHO,)),
        compile_output_bindings=output_bindings(build_dir,(SOURCE,HEADER,'compile.log','ForexDemoClockObserver042.ex5')),
        powershell_script_executions=0,execution_policy_changed=False,global_environment_changed=False,
        observer_attached=False,observer_runtime_executed=False,market_requests=0,native_connections=0,
        external_requests=0,historical_downloads=0,strategy_replays=0,orders_available=False,
        fresh_performance_eligible=False,annual_eligible=False))
    print(json.dumps(dict(fixture_invocations=fixture_calls,fixture_passed=fixture_passed,compiler_invocations=compiler_calls,
        compiler_started=compiler_started,compiler_exit_code=exit_code,**evidence,stop_reason=reason,observer_runtime_executed=False)))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=('freeze','verify','run'))
    {'freeze':freeze,'verify':lambda:print(json.dumps(dict(verified=len(verify()['bindings'])))),'run':run}[p.parse_args().action]()
