"""Fresh081 metadata entry. Importing this file never imports/attaches the SDK."""
import ast
import ctypes as C
from datetime import datetime,timezone
import hashlib
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from forex_demo_lab.native_timing_081 import (Spec081,Hooks081,authorization081,
    validate_authorization081,reserve_dispatch081,run_entry081)
from forex_demo_lab.sharing_adapter_076 import VerifiedBuild076,encoded076,exact076
from forex_demo_lab.sharing_integration_072 import SOURCE_INPUTS
from forex_demo_lab.image_guard_068 import NativeIdentity068,HelperChain068
from forex_demo_lab.native_files_065 import NativeFiles065,H,D
from forex_demo_lab.native_compiler_042 import module_environment
from forex_demo_lab.sharing_probe_062 import ProbeRejected
from forex_demo_lab.timing_profile_077 import DATE
from forex_demo_lab.public_preflight_080 import PublicInputs080
from forex_demo_lab.public_trace_081 import (PublicTrace081,PublicFailure081,
    reserve_invocation081,category081)


def dependency_files081(root):
    """Static closure of local Python imports; excludes historic data/log files."""
    root=Path(root);todo=['native_timing_081','native_compiler_042'];seen=set()
    while todo:
        name=todo.pop()
        if name in seen: continue
        path=root/'src/forex_demo_lab'/f'{name}.py'
        if not path.is_file(): raise ProbeRejected('timing_source_rejected')
        seen.add(name)
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node,ast.ImportFrom):
                if node.level==1 and node.module: todo.append(node.module.split('.')[0])
                elif node.module and node.module.startswith('forex_demo_lab.'):
                    todo.append(node.module.split('.')[1])
    return tuple(sorted(['scripts/runtime-native-timing-081.py','src/forex_demo_lab/__init__.py',
        *(f'src/forex_demo_lab/{n}.py' for n in seen)]))


def bound081(name):
    if name.startswith('/mnt/c/'): return Path('C:/')/name[7:]
    if name.startswith('/') or '..' in Path(name).parts: raise ProbeRejected('timing_path_rejected')
    return ROOT/name


def loaded_library081(files):
    module=files.bind(files.k,'GetModuleHandleW',[C.c_wchar_p],H)
    filename=files.bind(files.k,'GetModuleFileNameW',[H,C.c_wchar_p,D],D)
    handle,error=files._call(module,'python313.dll')
    if not handle or error: raise ProbeRejected('timing_library_rejected')
    buf=C.create_unicode_buffer(32768);n,error=files._call(filename,handle,buf,len(buf))
    if not 0<n<len(buf) or error: raise ProbeRejected('timing_library_rejected')
    return buf.value


SIGNATURE_COMMAND=r"""$ErrorActionPreference='Stop'
$terminal='C:\Program Files\MetaTrader 5\terminal64.exe'
$editor='C:\Program Files\MetaTrader 5\metaeditor64.exe'
$python='C:\Program Files\WindowsApps\PythonSoftwareFoundation.Python.3.13_3.13.3824.0_x64__qbz5n2kfra8p0'
$mt=@(@($terminal,$editor) | ForEach-Object { Get-AuthenticodeSignature -LiteralPath $_ })
$py=@(@('python.exe','python3.13.exe','python313.dll') | ForEach-Object { Get-AuthenticodeSignature -LiteralPath (Join-Path $python $_) })
$valid=@($mt | Where-Object { $_.Status.ToString() -ne 'Valid' -or $null -eq $_.SignerCertificate -or $_.SignerCertificate.Subject -notmatch 'MetaQuotes' }).Count -eq 0
$valid=$valid -and @($py | Where-Object { $_.Status.ToString() -ne 'Valid' -or $null -eq $_.SignerCertificate -or $_.SignerCertificate.Subject -notmatch 'Python Software Foundation' }).Count -eq 0
ConvertTo-Json -Compress @{valid=$valid;count=(@($mt).Count+@($py).Count);policy=(Get-ExecutionPolicy).ToString();terminal_build=(Get-Item -LiteralPath $terminal).VersionInfo.FilePrivatePart;editor_build=(Get-Item -LiteralPath $editor).VersionInfo.FilePrivatePart}
"""


def signature081(shell,meter,invoke=subprocess.run):
    meter.consume('trust_queries')
    kwargs=dict(env=module_environment(shell),capture_output=True,text=True,timeout=15)
    if os.name=='nt':
        startup=subprocess.STARTUPINFO();startup.dwFlags|=subprocess.STARTF_USESHOWWINDOW;startup.wShowWindow=0
        kwargs.update(startupinfo=startup,creationflags=subprocess.CREATE_NO_WINDOW)
    result=invoke([str(shell),'-NoProfile','-NonInteractive','-Command',SIGNATURE_COMMAND],**kwargs)
    meter.check()
    expected=dict(valid=True,count=5,policy='Restricted',terminal_build=6244,editor_build=6244)
    if result.returncode!=0 or len(result.stdout)>4096 or result.stderr or not exact076(json.loads(result.stdout),expected):
        raise ProbeRejected('timing_signature_rejected')
    return True


def write_result081(path,value):
    raw=(json.dumps(value,indent=2,sort_keys=True)+'\n').encode('ascii')
    if len(raw)>65536:raise PublicFailure081('budget_rejected')
    with Path(path).open('xb') as stream: stream.write(raw);stream.flush();os.fsync(stream.fileno())
    with Path(path).with_suffix('.sha256').open('xb') as stream:
        stream.write(hashlib.sha256(raw).hexdigest().encode('ascii')+b'\n');stream.flush();os.fsync(stream.fileno())
    return hashlib.sha256(raw).hexdigest()


def prepare081(trace,executable):
    ledger,lsha=trace.record('ledger',ROOT/'reports/native-timing-081-ledger.json')
    checks,csha=trace.record('checks',ROOT/'reports/native-timing-081-checks.json')
    final,fsha=trace.record('final',ROOT/'reports/native-timing-081-final-source.json')
    review,rsha=trace.record('review',ROOT/'reports/native-timing-081-completion-review.json')
    profile,psha=trace.record('helper_profile',ROOT/'reports/helper-profile-068.json')
    auth_raw,auth_sha=trace.authority(ROOT/'reports/native-timing-081-authorization.json')
    trace.step('preparation','validate')
    if (checks['checker_passed'] is not True or checks['ledger_sha256']!=lsha or
        review['review_passed'] is not True or review['final_source_sha256']!=fsha or
        review['frozen_input_coverage_complete'] is not True or profile['profile_verified'] is not True or
        profile['native_signature_checks_passed'] is not True or psha!=ledger['helper_profile_sha256']):
        raise PublicFailure081('binding_rejected')
    policy_sha=ledger['policy_sha256'];bindings=ledger['runtime_bindings']
    if final['source_and_evidence_bindings'].get('docs/NATIVE-TIMING-081-POLICY.md')!=policy_sha:
        raise PublicFailure081('binding_rejected')
    trace.step('spec','validate')
    def pair(name):return str(bound081(name)),bindings[name]
    p=ledger['helper_chain']
    chain=HelperChain068(pair(p['launcher']),pair(p['config']),tuple(pair(n) for n in p['images']),pair(p['library']),p['base_alias'])
    build=VerifiedBuild076(encoded076(ledger['build_record']))
    spec=Spec081(build,fsha,policy_sha,psha,chain,pair(ledger['terminal_name']),pair(ledger['editor_name']),
        pair(ledger['artifact_name']),tuple((n,str(ROOT/n)) for n in SOURCE_INPUTS),
        tuple(pair(n) for n in ledger['sdk_bindings']))
    expected=authorization081(fsha,policy_sha,psha,lsha,bindings['scripts/runtime-native-timing-081.py'],
        build.sha256,spec.component_sha256)
    trace.step('authorization','validate')
    try:auth=validate_authorization081(auth_raw,expected,auth_sha)
    except ProbeRejected:raise PublicFailure081('authorization_rejected') from None
    trace.authority_validated=True
    trace.step('source_schema','validate')
    sources=ledger['runtime_sources']
    if (type(sources) is not list or not 1<len(sources)<64 or
        any(type(n) is not str or '..' in Path(n).parts or not n.endswith('.py') or
            not (n=='scripts/runtime-native-timing-081.py' or n.startswith('src/forex_demo_lab/')) for n in sources) or
        len(set(sources))!=len(sources) or 'scripts/runtime-native-timing-081.py' not in sources):
        raise PublicFailure081('schema_rejected')
    for index,n in enumerate(sorted(sources)):
        trace.source(ROOT/n,bindings[n],index)
        if final['source_and_evidence_bindings'].get(n)!=bindings[n]:raise PublicFailure081('binding_rejected')
    trace.source(Path(executable),bindings[p['launcher']],launcher=True)
    trace.source_pins_verified=True
    return dict(spec=spec,ledger=ledger,auth=auth,auth_raw=auth_raw,auth_sha=auth_sha,
        expected=expected,checks_sha256=csha,completion_review_sha256=rsha)


def hooks081(ledger):
    kernel=C.WinDLL('kernel32',use_last_error=True);boot=kernel.GetTickCount64
    boot.argtypes=[];boot.restype=C.c_uint64
    def importer():
        sdk=importlib.import_module('MetaTrader5');core=importlib.import_module('MetaTrader5._core')
        if (str(Path(sdk.__file__)).casefold()!=str(bound081(ledger['sdk_bindings'][0])).casefold() or
            str(Path(core.__file__)).casefold()!=str(bound081(ledger['sdk_bindings'][1])).casefold()):
            raise ProbeRejected('timing_sdk_import_rejected')
        return sdk
    return Hooks081(lambda:(time.time_ns()//1000000,time.monotonic_ns(),int(boot())),
        lambda meter:NativeFiles065(meter,Path(os.environ['TEMP']),'compatibility'),NativeIdentity068,
        lambda meter:signature081(bound081(ledger['shell_name']),meter),importer,loaded_library081,
        os.getpid(),sys.executable,sys._base_executable,sys.version.split()[0])


def run():
    public=PublicInputs080();trace=PublicTrace081(public);reserved=False
    try:
        trace.step('platform','validate')
        if os.name!='nt':raise PublicFailure081('unsupported_platform')
        if datetime.now(timezone.utc).date().isoformat()!=DATE:raise PublicFailure081('expired_date')
        trace.step('invocation','reserve')
        reserve_invocation081(ROOT/'reports/native-timing-081-invocation-started.json');reserved=True
        inputs=prepare081(trace,sys.executable)
        trace.step('dispatch','reserve')
        dispatch=reserve_dispatch081(ROOT/'reports/native-timing-081-dispatch-started.json',inputs['auth'],inputs['auth_sha'])
        trace.dispatch_reserved=True;public.check()
        outcome=trace.outcome(True)
        public_outcome_sha=write_result081(ROOT/'reports/native-timing-081-public-outcome.json',outcome)
    except (Exception,KeyboardInterrupt) as error:
        # No native backend/SDK construction exists before this boundary.
        # The first invocation stays spent even for a malformed or missing grant.
        if reserved and not trace.captured:
            outcome=trace.outcome(False,error)
            write_result081(ROOT/'reports/native-timing-081-public-outcome.json',outcome)
        print(json.dumps(dict(public_completed=False,invocation_consumed=reserved,
            stopped_stage=trace.stage,stopped_operation=trace.operation,
            stop_reason=category081(error),orders_available=False)),flush=True)
        return False
    try:
        value=run_entry081(inputs['spec'],hooks081(inputs['ledger']),inputs['auth_raw'],
            inputs['expected'],inputs['auth_sha'],dispatch,ROOT/'reports/native-timing-081-sdk-reservation.json')
    except (Exception,KeyboardInterrupt):
        # No guessed SDK/counter/cleanup proof when no owned entry report returns.
        print(json.dumps(dict(public_completed=True,entry_report_returned=False,
            stop_reason='native_startup_failed_details_redacted',orders_available=False)),flush=True)
        return False
    value.update(native_entry_invoked=True,public_outcome_sha256=public_outcome_sha,
        checks_sha256=inputs['checks_sha256'],completion_review_sha256=inputs['completion_review_sha256'])
    write_result081(ROOT/'reports/native-timing-081-runtime.json',value)
    print(json.dumps(dict(public_completed=True,entry_completed=value['entry_completed'],
        stop_reason=value['stop_reason'],stopped_stage=value['stopped_stage'],
        samples_completed=value['observation']['samples_completed'] if value['observation'] else 0,
        orders_available=False)),flush=True)
    return value['entry_completed']


if __name__=='__main__':
    try:raise SystemExit(0 if run() else 1)
    except (Exception,KeyboardInterrupt):raise SystemExit('timing_entry_output_unconfirmed_details_redacted') from None
