"""Source-bound corrected Windows synthetic runner; separate070 policy gate.

No prices/history/receipt/order capability.069 preparation does not run this.
"""
import ctypes as C
import importlib
import json
import os
from pathlib import Path
from queue import Queue,Empty
import runpy
import sys
from threading import Thread
import time
import uuid

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from forex_demo_lab.sharing_runtime_069 import (Meter069,Reservation069,Resources069,Trace069,
    Runtime069,ObservedCompanion069,bootstrap,deploy_owned069,no_reparse069,close_owned069,PHASE)
from forex_demo_lab.sharing_companion_065 import Companion065
from forex_demo_lab.image_guard_068 import NativeIdentity068,HelperChain068
from forex_demo_lab.native_files_065 import NativeFiles065,H,D
from forex_demo_lab.private_guard_065 import FullGuard065,Metadata065
from forex_demo_lab.sharing_probe_062 import ProbeRejected
from forex_demo_lab.mql_sharing_064 import DATE,PHASE as MQL_PHASE


def authorization(value,preparation_hash,policy_hash,profile_hash):
    from forex_demo_lab.sharing_runtime_066 import digest
    expected=dict(version='sharing_native_070_v1',preparation_sha256=digest(preparation_hash),
        policy_sha256=digest(policy_hash),helper_profile_sha256=digest(profile_hash),phase=PHASE,date=DATE,
        maximum_sdk_connections=1,maximum_launches=2,maximum_log_reads=1,maximum_log_bytes=65536,
        maximum_market_reads=0,maximum_orders=0,maximum_receipt_permissions=0)
    if type(value) is not dict or set(value)!=set(expected) or any(type(value[k]) is not type(v) or value[k]!=v for k,v in expected.items()):
        raise ProbeRejected('runtime_authorization_rejected')


def signatures(api,meter):
    native=runpy.run_path(str(ROOT/'scripts/native-compiler-042.py'))
    settings=api['sealed'](ROOT/'reports/native-compiler-042-ledger.json')
    meter.consume('trust_queries')
    command=r"""$ErrorActionPreference='Stop'
$s=@('C:\Program Files\MetaTrader 5\terminal64.exe','C:\Program Files\MetaTrader 5\metaeditor64.exe') | ForEach-Object { Get-AuthenticodeSignature -LiteralPath $_ }
$ok=@($s | Where-Object { $_.Status.ToString() -ne 'Valid' -or $null -eq $_.SignerCertificate -or $_.SignerCertificate.Subject -notmatch 'MetaQuotes' }).Count -eq 0
ConvertTo-Json -Compress @{valid=$ok;count=@($s).Count;policy=(Get-ExecutionPolicy).ToString()}
"""
    result=native['command'](api['bound'](settings['powershell_path']),command);meter.check()
    if result.returncode!=0 or json.loads(result.stdout)!=dict(valid=True,count=2,policy='Restricted'):
        raise ProbeRejected('runtime_trust_rejected')
    return True


def loaded_library(files):
    handle_fn=files.bind(files.k,'GetModuleHandleW',[C.c_wchar_p],H)
    name_fn=files.bind(files.k,'GetModuleFileNameW',[H,C.c_wchar_p,D],D)
    handle,error=files._call(handle_fn,'python313.dll')
    if not handle or error:raise ProbeRejected('runtime_library_rejected')
    buf=C.create_unicode_buffer(32768);n,error=files._call(name_fn,handle,buf,len(buf))
    if not 0<n<len(buf) or error:raise ProbeRejected('runtime_library_rejected')
    return buf.value # A loaded module is not an owned handle to close.


def run():
    if os.name!='nt' or not sys.stdin.isatty():raise ProbeRejected('interactive_windows_required')
    api=runpy.run_path(str(ROOT/'scripts/sharing-integration-069.py'))
    sha,sealed,write,bound=(api[k] for k in ('sha','sealed','write','bound'))
    final=ROOT/'reports/sharing-integration-069-final-source.json'
    policy=ROOT/'docs/NATIVE-SHARING-070-POLICY.md';profile_path=ROOT/'reports/helper-profile-068.json'
    auth_path=ROOT/'reports/native-sharing-070-authorization.json'
    authorization(sealed(auth_path),sha(final),sha(policy),sha(profile_path))
    # Source-bound dispatcher is also one-use, including an early preflight stop.
    write(ROOT/'reports/native-sharing-069-dispatch-started.json',dict(dispatch_consumed=True,
        phase=PHASE,preparation_sha256=sha(final),policy_sha256=sha(policy),authorization_sha256=sha(auth_path),
        maximum_native_sessions=1,orders_available=False))
    trace=Trace069();meter=None;session=None;resources=None;result=None;closed=None
    reason=None;failed_stage=None;trusted=False;private_bootstrap=False;deployed=None;reservation_hash=None
    l=None;bindings=None;commands=Queue()
    try:
        def preflight():
            from datetime import datetime,timezone
            current=api['verify']();review=sealed(ROOT/'reports/sharing-integration-069-completion-review.json')
            if (not review['review_passed'] or review['final_source_sha256']!=sha(final) or
                datetime.now(timezone.utc).date().isoformat()!=DATE or
                sha(Path(sys.executable))!=current['python_sha256'] or
                sealed(final)['source_and_evidence_bindings']['scripts/runtime-native-sharing-069.py']!=sha(Path(__file__))):
                raise ProbeRejected('runtime_preparation_rejected')
            p=sealed(profile_path)
            if not p['profile_verified'] or not p['native_signature_checks_passed'] or p['actual_helper_image_name']!=current['measured_helper_name']:
                raise ProbeRejected('runtime_helper_profile_rejected')
            return current
        l=trace.run('preflight',preflight)
        k=C.WinDLL('kernel32',use_last_error=True);boot=k.GetTickCount64;boot.argtypes=[];boot.restype=C.c_uint64
        meter=Meter069(lambda:(time.time_ns()//1000000,time.monotonic_ns(),int(boot())))
        build=sealed(ROOT/'reports/sharing-companion-065-r2-build.json')
        artifact_name=next(n for n in build['output_bindings'] if n.endswith('/ForexDemoSharing064.ex5'))
        source=ROOT/'mt5/Scripts/ForexDemoSharing064.mq5';artifact=bound(artifact_name)
        terminal=bound('/mnt/c/Program Files/MetaTrader 5/terminal64.exe');editor=bound('/mnt/c/Program Files/MetaTrader 5/metaeditor64.exe')
        bindings=dict(source=sha(source),ex5=sha(artifact),terminal=l['bindings']['/mnt/c/Program Files/MetaTrader 5/terminal64.exe'],
            editor=l['bindings']['/mnt/c/Program Files/MetaTrader 5/metaeditor64.exe'],preparation=sha(final),
            policy=sha(policy),helper_profile=sha(profile_path))
        reservation=ROOT/'reports/native-sharing-069-runtime-reservation.json'
        session=Reservation069(reservation,bindings,meter);reservation_hash=sha(reservation)
        resources=Resources069(session,meter,trace)
        resources.base=NativeFiles065(meter,Path(os.environ['TEMP']),'compatibility')
        native_reader=NativeIdentity068(resources.base)
        p=l['helper_chain']
        def pair(n):return str(bound(n)),l['bindings'][n]
        chain=HelperChain068(pair(p['launcher']),pair(p['config']),tuple(pair(n) for n in p['images']),pair(p['library']),p['base_alias'])
        def trust():
            nonlocal trusted
            trusted=signatures(api,meter);return trusted
        reader,peer=bootstrap(native_reader,(terminal,bindings['terminal']),(editor,bindings['editor']),chain,
            sys.executable,sys._base_executable,lambda:loaded_library(resources.base),os.getpid(),sys.version.split()[0],
            trust,lambda:importlib.import_module('MetaTrader5'),resources,session,meter,trace)
        def metadata_guard():
            info=Metadata065(resources.sdk,meter).terminal_info()
            if info is None or type(info.data_path) is not str or type(info.build) is not int or info.build!=6244:
                raise ProbeRejected('runtime_metadata_rejected')
            root=Path(info.data_path);no_reparse069(root,meter)
            guard=FullGuard065(resources.sdk,reader,peer,root,6244,(editor,bindings['editor']),(artifact,bindings['ex5']),meter)
            guard();return root,guard
        root,guard=trace.run('account_metadata',metadata_guard);private_bootstrap=True
        # Do not deploy if the fixed064 sandbox has already been used.
        meter.consume('startup_path_stats')
        if (root/'MQL5'/'Files'/('ForexDemoSharing064-'+MQL_PHASE)).exists():raise ProbeRejected('runtime_sandbox_already_used')
        folder='ForexDemoLab069-'+uuid.uuid4().hex
        deployed=trace.run('deployment',deploy_owned069,artifact,root/'MQL5'/'Scripts',folder,bindings['ex5'],reader,guard,meter)
        guard.artifact=(deployed,bindings['ex5']);guard()
        resources.files=NativeFiles065(meter,root/'MQL5'/'Files','terminal')
        companion=ObservedCompanion069(Companion065(resources.files,meter,guard),trace)
        resources.runner=Runtime069(companion,session,meter,guard,root/'MQL5'/'Logs'/'20261007.log',lambda ms:time.sleep(ms/1000),trace=trace)
        def inputs():
            for line in sys.stdin:commands.put(line.strip())
            commands.put('eof')
        Thread(target=inputs,daemon=True).start()
        print(json.dumps(dict(status='prepared',folder=folder,script='ForexDemoSharing064',
            input='ReadSyntheticEvidence',maximum_launches=2,quote_reads=0,orders_available=False)),flush=True)
        while resources.runner.stage<6:
            meter.check()
            try:command=commands.get(timeout=1)
            except Empty:continue
            if command in ('eof','cancel'):raise ProbeRejected('runtime_user_stopped')
            print(json.dumps(resources.runner.command(command)),flush=True)
        result=resources.runner.finish()
        if not result['completed']:failed_stage=trace.current;reason='native_final_audit_rejected'
    except (Exception,KeyboardInterrupt):
        failed_stage=trace.current;reason='native_runtime_failed_details_redacted'
        if session is not None:session.stop()
    finally:
        if resources is not None:
            closed=close_owned069(resources)
            if result is None:result=closed['outcome']
            if closed['errors']:reason=reason or 'native_cleanup_unconfirmed';failed_stage=failed_stage or trace.current
        elif meter is not None:
            try:meter.check()
            except Exception:reason=reason or 'native_final_clock_rejected'
    complete=reason is None and result is not None and result['completed'] and private_bootstrap and trusted and closed is not None and closed['sdk_shutdown_called'] and not closed['errors']
    if not complete and reason is None:reason='native_session_incomplete'
    write(ROOT/'reports/native-sharing-069-runtime.json',dict(completed=complete,stop_reason=reason,
        stopped_stage=failed_stage,stage_trace=trace.public(),phase=PHASE,date=DATE,
        preparation_sha256=sha(final),policy_sha256=sha(policy),helper_profile_sha256=sha(profile_path),
        reservation_sha256=reservation_hash,counts=dict(meter.counts) if meter else None,
        sdk_shutdown_called=closed['sdk_shutdown_called'] if closed else False,
        native_signature_checks_passed=trusted,native_private_bootstrap_passed=private_bootstrap,
        native_sharing_observed=complete,native_mql_verified=False,native_publication_verified=False,
        orders_available=False,fresh_performance_eligible=False,annual_eligible=False,
        quote_reads=0,history_reads=0,orders=0,receipt_permissions=0,
        script_arms=session.arms if session else [],records=resources.runner.rows if resources and resources.runner else [],
        probes=[vars(p) for p in resources.runner.c.probes] if resources and resources.runner else [],
        cleanup=closed['file_cleanup'] if closed else None,bootstrap_cleanup=closed['bootstrap_cleanup'] if closed else None,
        cleanup_errors=closed['errors'] if closed else [],deployment_completed=deployed is not None,
        compiled_source_sha256=bindings['source'] if bindings else None,compiled_artifact_sha256=bindings['ex5'] if bindings else None,
        elapsed_us=meter.elapsed_us if meter else None))
    print(json.dumps(dict(completed=complete,stop_reason=reason,stopped_stage=failed_stage,orders_available=False)),flush=True)


if __name__=='__main__':
    try:run()
    except Exception:raise SystemExit('runtime_preflight_rejected_details_redacted') from None
