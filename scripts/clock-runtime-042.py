"""One guarded existing-terminal session; UI launches scripts, never this helper."""
import json
import os
from pathlib import Path,PureWindowsPath
import runpy
import sys
import time
import uuid

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
API=runpy.run_path(str(ROOT/'scripts/native-compiler-042.py'))
sha,write,sealed=API['sha'],API['write'],API['sealed']
from forex_demo_lab.compiler_launch_039 import ps_quote
from forex_demo_lab.clock_observer_042 import (DATE,VERSION,date_guard,runtime_guard,RuntimeSequence,records_from_log,comparison)
RESERVATION=ROOT/'reports/clock-observer-042-runtime-reservation.json'
OUTPUT=ROOT/'reports/clock-observer-042-runtime.json'

def deploy(shell,data_root,artifact):
    token=uuid.uuid4().hex;root=PureWindowsPath(data_root)
    if not root.is_absolute() or len(root.drive)!=2:raise ValueError('terminal_data_root_invalid')
    scripts=root/'MQL5'/'Scripts';folder='ForexDemoLab042-'+token
    text="""$ErrorActionPreference='Stop'
$r="""+ps_quote(str(scripts))+"""
$cursor=$r
while($cursor) {
 if(Test-Path -LiteralPath $cursor) {
  if((Get-Item -LiteralPath $cursor -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) {throw 'reparse_root_rejected'}
 }
 $cursor=Split-Path -Parent $cursor
}
if(-not [IO.Directory]::Exists($r)) {throw 'missing_scripts_root'}
$b=Join-Path $r """+ps_quote(folder)+"""
New-Item -ItemType Directory -Path $b | Out-Null
$f=Join-Path $b 'ForexDemoClockObserver042.ex5'
[IO.File]::Copy("""+ps_quote(str(artifact))+""",$f,$false)
ConvertTo-Json -Compress @{path=$f;sha256=(Get-FileHash -LiteralPath $f -Algorithm SHA256).Hash.ToLower()}
"""
    result=API['command'](shell,text)
    if result.returncode!=0:raise ValueError('exclusive_deployment_failed')
    value=json.loads(result.stdout);expected=scripts/folder/'ForexDemoClockObserver042.ex5'
    if set(value)!={'path','sha256'} or PureWindowsPath(value['path'])!=expected or value['sha256']!=sha(artifact) or sha(Path(str(expected)))!=sha(artifact):
        raise ValueError('deployment_hash_or_path_invalid')
    return dict(folder=folder,artifact_binding={API['external_name'](value['path']):value['sha256']})

def running(shell,terminal):
    result=API['command'](shell,"ConvertTo-Json -Compress -InputObject @(Get-Process terminal64 -ErrorAction SilentlyContinue | ForEach-Object {$_.Path})")
    if result.returncode!=0:return False
    paths=json.loads(result.stdout)
    return sum(os.path.normcase(p)==os.path.normcase(str(terminal)) for p in paths if p)==1

def run():
    ledger=API['verify']();date_guard();assert os.name=='nt' and not RESERVATION.exists() and not OUTPUT.exists()
    build=sealed(API['OUTPUT']);checks=sealed(ROOT/'reports/native-compiler-042-checks.json')
    assert build['compiled'] and checks['checker_passed'] and checks['build_sha256']==sha(API['OUTPUT'])
    outputs=build['compile_output_bindings'];artifact_name=next(n for n in outputs if n.endswith('/ForexDemoClockObserver042.ex5'))
    artifact=API['bound_path'](artifact_name);assert sha(artifact)==outputs[artifact_name]
    terminal=API['bound_path']('/mnt/c/Program Files/MetaTrader 5/terminal64.exe');shell=API['bound_path'](ledger['powershell_path'])
    write(RESERVATION,dict(ledger_sha256=sha(API['LEDGER']),build_sha256=sha(API['OUTPUT']),declared_date=DATE,
        maximum_native_connections=1,maximum_script_arms=2,maximum_quote_reads=1,maximum_sdk_quote_reads=0,
        terminal_launch_authorized=False,orders_available=False,started_monotonic_ns=time.monotonic_ns()))
    state=RuntimeSequence();api=None;connection_calls=0;deployment=None;reason=None;anchors=[];start=time.monotonic()
    guard_checks=0;offset=None;log=None;receipts=[]
    try:
        if not running(shell,terminal):raise ValueError('existing_terminal_not_unique_or_running')
        import MetaTrader5 as mt5
        if mt5.__version__!='5.0.6231':raise ValueError('sdk_version_changed')
        connection_calls=1;api=mt5
        if not api.initialize(str(terminal),timeout=15000):raise ValueError('existing_terminal_connection_failed')
        identity=runtime_guard(api);guard_checks+=1
        info=api.terminal_info()
        if info is None or os.path.normcase(info.path)!=os.path.normcase(str(terminal.parent)):raise ValueError('terminal_path_changed')
        data_root=info.data_path;log=Path(data_root)/'MQL5'/'Logs'/'20261006.log'
        date_guard();runtime_guard(api,identity);guard_checks+=1
        deployment=deploy(shell,data_root,artifact)
        write(ROOT/'reports/clock-observer-042-deployment.json',dict(**deployment,ledger_sha256=sha(API['LEDGER']),
            compiled_artifact_sha256=sha(artifact),actual_demo_usd_algo_off_verified=True,market_requests=0,orders_available=False))
        print(json.dumps(dict(status='prepared',folder=deployment['folder'],actual_demo_usd_algo_off_verified=True,quote_reads=0)),flush=True)
        for command in sys.stdin:
            command=command.strip();date_guard()
            if time.monotonic()-start>900:raise ValueError('runtime_session_deadline_exceeded')
            if command=='finish':break
            if command not in ('arm-disabled','collect-disabled','arm-enabled','collect-enabled'):raise ValueError('undeclared_runtime_command')
            runtime_guard(api,identity);guard_checks+=1
            if command.startswith('arm-'):
                enabled=command=='arm-enabled';state.arm(enabled)
                offset=log.stat().st_size if log.exists() else 0
                if offset%2:raise ValueError('native_log_anchor_unaligned')
                anchors.append(dict(enabled=enabled,offset_bytes=offset,armed_utc_ms=time.time_ns()//1000000))
                write(ROOT/('reports/clock-observer-042-'+('enabled' if enabled else 'disabled')+'-started.json'),
                    dict(ledger_sha256=sha(API['LEDGER']),enabled=enabled,script_arm_consumed=True,
                         maximum_quote_reads=1 if enabled else 0,anchor=anchors[-1]))
                print(json.dumps(dict(status='armed',enabled=enabled,actual_demo_usd_algo_off_verified=True)),flush=True)
            else:
                enabled=command=='collect-enabled'
                if state.pending is not enabled or offset is None:raise ValueError('runtime_collect_order_invalid')
                if not log.exists():raise ValueError('native_log_missing')
                size=log.stat().st_size
                if size<offset or size-offset>1048576:raise ValueError('native_log_truncated_or_budget_exceeded')
                with log.open('rb') as f:f.seek(offset);raw=f.read(1048577)
                rows=records_from_log(raw)
                # Only these whitelisted records leave memory, never whole logs.
                write(ROOT/('reports/clock-observer-042-'+('enabled' if enabled else 'disabled')+'-records.json'),
                    dict(records=rows,anchor=anchors[-1],read_bytes=len(raw),ledger_sha256=sha(API['LEDGER'])))
                record=state.collect(rows);receipts.append(time.time_ns()//1000000)
                runtime_guard(api,identity);guard_checks+=1;date_guard()
                print(json.dumps(dict(status='collected',enabled=enabled,record=record)),flush=True)
    except Exception as exc:
        allowed={'existing_terminal_not_unique_or_running','sdk_version_changed','existing_terminal_connection_failed',
            'terminal_path_changed','declared_date_expired','runtime_session_deadline_exceeded','native_observer_guard_rejected',
            'disconnected','actual_account_not_demo','account_currency_not_usd','algo_trading_enabled','account_changed_or_invalid',
            'symbol_not_supported_or_visible','exactly_one_native_record_required','disabled_run_read_or_reason_invalid',
            'native_log_missing','native_log_truncated_or_budget_exceeded','exclusive_deployment_failed'}
        reason=str(exc) if str(exc) in allowed else 'runtime_failure_details_redacted'
    finally:
        if api is not None:api.shutdown()
    complete=len(state.records)==2 and state.records[1]['accepted'] and state.pending is None and reason is None
    if not complete and reason is None:reason='runtime_observation_incomplete'
    write(OUTPUT,dict(version=VERSION,declared_date=DATE,ledger_sha256=sha(API['LEDGER']),
        reservation_sha256=sha(RESERVATION),build_sha256=sha(API['OUTPUT']),completed=complete,stop_reason=reason,
        native_connections_attempted=connection_calls,sdk_quote_reads=0,script_arms=state.arms,records=state.records,
        quote_reads=sum(r['quote_reads'] for r in state.records),guard_checks=guard_checks,anchors=anchors,
        collection_receipts_utc_ms=receipts,deployment=deployment,
        comparison=comparison(state.records[-1]) if complete else None,elapsed_seconds=time.monotonic()-start,
        http_requests=0,historical_reads=0,strategy_replays=0,orders_available=False,
        fresh_performance_eligible=False,annual_eligible=False,local_clock_certified=False,historical_clock_certified=False))
    print(json.dumps(dict(status='finished',completed=complete,stop_reason=reason,quote_reads=sum(r['quote_reads'] for r in state.records))),flush=True)

if __name__=='__main__':run()
