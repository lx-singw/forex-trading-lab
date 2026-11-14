"""Separately gated Windows interactive synthetic sharing entry point.

066 preparation never runs this. A frozen067 authorization is required BEFORE
reservation/native/SDK/deployment work. No prices, history, grants or orders.
"""
import ctypes as C
import json
import os
from pathlib import Path
from queue import Queue, Empty
import runpy
import sys
from threading import Thread
import time
import uuid

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from forex_demo_lab.sharing_runtime_066 import (Meter066,Reservation066,PrivateReader066,
    Runtime066,attach_existing,deploy_owned,no_reparse,digest,PHASE)
from forex_demo_lab.sharing_companion_065 import Companion065
from forex_demo_lab.native_files_065 import NativeFiles065
from forex_demo_lab.private_guard_065 import NativeIdentity065,FullGuard065,Metadata065
from forex_demo_lab.sharing_probe_062 import ProbeRejected
from forex_demo_lab.mql_sharing_064 import DATE


def authorization(value,preparation_hash,policy_hash):
    expected=dict(version='sharing_native_067_v1',preparation_sha256=digest(preparation_hash),
        policy_sha256=digest(policy_hash),phase=PHASE,date=DATE,maximum_sdk_connections=1,
        maximum_launches=2,maximum_log_reads=1,maximum_log_bytes=65536,
        maximum_market_reads=0,maximum_orders=0,maximum_receipt_permissions=0)
    if type(value) is not dict or set(value)!=set(expected):raise ProbeRejected('runtime_authorization_rejected')
    if any(type(value[k]) is not type(v) or value[k]!=v for k,v in expected.items()):
        raise ProbeRejected('runtime_authorization_rejected')


def signatures(api,meter,terminal,editor):
    # Fixed known installed paths, never interpolate private/user supplied text.
    if str(terminal).casefold()!=r'c:\program files\metatrader 5\terminal64.exe' or str(editor).casefold()!=r'c:\program files\metatrader 5\metaeditor64.exe':
        raise ProbeRejected('runtime_binding_rejected')
    native=runpy.run_path(str(ROOT/'scripts/native-compiler-042.py'))
    settings=api['sealed'](ROOT/'reports/native-compiler-042-ledger.json')
    meter.consume('trust_queries')
    text=r"""$ErrorActionPreference='Stop'
$s=@('C:\Program Files\MetaTrader 5\terminal64.exe','C:\Program Files\MetaTrader 5\metaeditor64.exe') | ForEach-Object { Get-AuthenticodeSignature -LiteralPath $_ }
$ok=@($s | Where-Object { $_.Status.ToString() -ne 'Valid' -or $null -eq $_.SignerCertificate -or $_.SignerCertificate.Subject -notmatch 'MetaQuotes' }).Count -eq 0
ConvertTo-Json -Compress @{valid=$ok;count=@($s).Count;policy=(Get-ExecutionPolicy).ToString()}
"""
    result=native['command'](api['bound'](settings['powershell_path']),text);meter.check()
    try:
        r=json.loads(result.stdout)
        if result.returncode!=0 or r!=dict(valid=True,count=2,policy='Restricted'):raise ValueError()
    except Exception:raise ProbeRejected('runtime_trust_rejected') from None


def run():
    # No stdin thread, native constructor or SDK import before these gates.
    if os.name!='nt' or not sys.stdin.isatty():raise ProbeRejected('interactive_windows_required')
    api=runpy.run_path(str(ROOT/'scripts/native-sharing-066.py'))
    sha,sealed,write,bound=(api[k] for k in ('sha','sealed','write','bound'))
    l=api['verify']()
    final=ROOT/'reports/native-sharing-066-final-source.json'
    review=sealed(ROOT/'reports/native-sharing-066-completion-review.json')
    if not review['review_passed'] or review['final_source_sha256']!=sha(final):
        raise ProbeRejected('runtime_preparation_rejected')
    authorization(sealed(ROOT/'reports/native-sharing-067-authorization.json'),sha(final),
        sha(ROOT/'docs/NATIVE-SHARING-067-POLICY.md'))
    if sha(Path(__file__))!=sealed(final)['source_and_evidence_bindings']['scripts/runtime-native-sharing-066.py']:
        raise ProbeRejected('runtime_binding_rejected')
    if sha(Path(sys.executable))!=l['python_sha256']:raise ProbeRejected('runtime_binding_rejected')
    k=C.WinDLL('kernel32',use_last_error=True);boot=k.GetTickCount64;boot.argtypes=[];boot.restype=C.c_uint64
    meter=Meter066(lambda:(time.time_ns()//1000000,time.monotonic_ns(),int(boot())))
    build=sealed(ROOT/'reports/sharing-companion-065-r2-build.json')
    artifact_name=next(n for n in build['output_bindings'] if n.endswith('/ForexDemoSharing064.ex5'))
    source=ROOT/'mt5/Scripts/ForexDemoSharing064.mq5';artifact=bound(artifact_name)
    terminal=bound('/mnt/c/Program Files/MetaTrader 5/terminal64.exe')
    editor=bound('/mnt/c/Program Files/MetaTrader 5/metaeditor64.exe')
    bindings=dict(source=sha(source),ex5=sha(artifact),terminal=l['bindings']['/mnt/c/Program Files/MetaTrader 5/terminal64.exe'],
        editor=l['bindings']['/mnt/c/Program Files/MetaTrader 5/metaeditor64.exe'],preparation=sha(final),
        policy=sha(ROOT/'docs/NATIVE-SHARING-067-POLICY.md'))
    session=Reservation066(ROOT/'reports/native-sharing-066-runtime-reservation.json',bindings,meter)
    sdk=None;base=None;files=None;runner=None;reason=None;outcome=None;shutdown=False
    deployed=None;trusted=False;private_bootstrap=False;queue=Queue()
    def inputs():
        for line in sys.stdin:queue.put(line.strip())
        queue.put('eof')
    try:
        base=NativeFiles065(meter,Path(os.environ['TEMP']),'compatibility') # No setup/file creation.
        reader=NativeIdentity065(base)
        if reader.hash_file(terminal)!=bindings['terminal'] or reader.hash_file(editor)!=bindings['editor']:
            raise ProbeRejected('runtime_binding_rejected')
        signatures(api,meter,terminal,editor);trusted=True
        pid=reader.unique_pid();peer=reader.identity(pid);helper=reader.identity(os.getpid())
        if (peer.image!=str(terminal).casefold() or peer.digest!=bindings['terminal'] or
            helper.image!=str(Path(sys.executable)).casefold() or helper.digest!=l['python_sha256'] or
            peer.session!=helper.session or peer.logon!=helper.logon):
            raise ProbeRejected('runtime_identity_rejected')
        reader=PrivateReader066(reader,helper)
        import MetaTrader5 as sdk
        attach_existing(sdk,session,reader,peer,meter)
        metadata=Metadata065(sdk,meter);info=metadata.terminal_info()
        if info is None or type(info.data_path) is not str or type(info.build) is not int or info.build!=6244:
            raise ProbeRejected('runtime_metadata_rejected')
        root=Path(info.data_path);no_reparse(root)
        guard=FullGuard065(sdk,reader,peer,root,info.build,(editor,bindings['editor']),(artifact,bindings['ex5']),meter)
        guard();private_bootstrap=True
        folder='ForexDemoLab066-'+uuid.uuid4().hex
        deployed=deploy_owned(artifact,root/'MQL5'/'Scripts',folder,bindings['ex5'],reader,guard,meter)
        guard.artifact=(deployed,bindings['ex5']);guard()
        files=NativeFiles065(meter,root/'MQL5'/'Files','terminal')
        companion=Companion065(files,meter,guard)
        log=root/'MQL5'/'Logs'/'20261007.log'
        runner=Runtime066(companion,session,meter,guard,log,lambda ms:time.sleep(ms/1000))
        Thread(target=inputs,daemon=True).start()
        print(json.dumps(dict(status='prepared',folder=folder,script='ForexDemoSharing064',
            input='ReadSyntheticEvidence',maximum_launches=2,quote_reads=0,orders_available=False)),flush=True)
        while runner.stage<6:
            meter.check()
            try:command=queue.get(timeout=1)
            except Empty:continue
            if command in ('eof','cancel'):raise ProbeRejected('runtime_user_stopped')
            print(json.dumps(runner.command(command)),flush=True)
        outcome=runner.finish()
    except (Exception,KeyboardInterrupt):reason='native_runtime_failed_details_redacted';session.stop()
    finally:
        if runner is not None and not runner.closed:outcome=runner.finish()
        elif runner is None and files is not None:
            try:
                fc=files.finish()
                if not fc['all_handles_closed'] or not fc['allocations_released']:reason='native_cleanup_unconfirmed'
            except Exception:reason='native_cleanup_unconfirmed'
        base_cleanup=None
        if base is not None:
            try:
                base_cleanup=base.finish()
                if not base_cleanup['all_handles_closed'] or not base_cleanup['allocations_released']:reason='native_cleanup_unconfirmed'
            except Exception:reason='native_cleanup_unconfirmed'
        if session.spent and sdk is not None:
            meter.cleanup('sdk_shutdowns')
            try:sdk.shutdown();shutdown=True
            except Exception:reason='sdk_cleanup_unconfirmed'
        try:meter.check()
        except Exception:reason='native_final_clock_rejected'
        if meter.cleanup_exceeded:reason='native_cleanup_budget_rejected'
    complete=reason is None and outcome is not None and outcome['completed'] and trusted and private_bootstrap and shutdown
    write(ROOT/'reports/native-sharing-066-runtime.json',dict(completed=complete,stop_reason=reason or
        (outcome.get('stop_reason') if outcome else 'native_session_incomplete'),phase=PHASE,date=DATE,
        preparation_sha256=sha(final),policy_sha256=bindings['policy'],counts=dict(meter.counts),
        sdk_shutdown_called=shutdown,native_signature_checks_passed=trusted,
        native_private_bootstrap_passed=private_bootstrap,native_sharing_observed=complete,
        # Readiness/publication/ACK and financial eligibility are not promoted.
        native_mql_verified=False,native_publication_verified=False,orders_available=False,
        fresh_performance_eligible=False,annual_eligible=False,quote_reads=0,history_reads=0,orders=0,
        receipt_permissions=0,script_arms=session.arms,records=runner.rows if runner else [],
        probes=[vars(p) for p in runner.c.probes] if runner else [],
        cleanup=outcome.get('cleanup') if outcome else None,bootstrap_cleanup=base_cleanup,
        compiled_source_sha256=bindings['source'],compiled_artifact_sha256=bindings['ex5'],
        deployment_completed=deployed is not None,elapsed_us=meter.elapsed_us))
    print(json.dumps(dict(completed=complete,stop_reason=reason,quote_reads=0,orders_available=False)),flush=True)


if __name__=='__main__':
    try:run()
    except Exception:raise SystemExit('runtime_preflight_rejected_details_redacted') from None
