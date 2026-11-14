"""Interactive actual-demo no-market fixture. No price/history/order capability."""
import json
import os
from pathlib import Path
from queue import Queue, Empty
import runpy
import sys
from threading import Thread, Event, RLock
import time
import uuid
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
API=runpy.run_path(str(ROOT/'scripts/native-pipe-049.py'))
sha,write,sealed,bound=API['sha'],API['write'],API['sealed'],API['bound']
from forex_demo_lab.native_pipe_049 import (Session049,ManualWindowsPipe049,require_interactive,date_guard,records_from_log,
    Readiness049,collect_stopped_record)
from forex_demo_lab.clock_observer_042 import runtime_guard
from forex_demo_lab.capture_budget_047 import Policy,start_authority,PermitRejected
from forex_demo_lab.capture_wire_047 import decode_request,encode_response
from forex_demo_lab.windows_pipe_047 import _PENDING
RESERVATION=ROOT/'reports/native-pipe-049-runtime-reservation.json'
OUTPUT=ROOT/'reports/native-pipe-049-runtime.json'

class MetadataOnly:
    """Only these SDK methods reach the helper; no quote/order methods exposed."""
    def __init__(self,api):
        self.ACCOUNT_TRADE_MODE_DEMO=api.ACCOUNT_TRADE_MODE_DEMO
        self.terminal_info=api.terminal_info;self.account_info=api.account_info;self.symbol_info=api.symbol_info

def reject_reparse(path):
    for p in (path,*path.parents):
        if p.is_symlink() or getattr(p.stat(),'st_file_attributes',0)&0x400:raise ValueError('reparse_path_rejected')

def terminal_process():
    old=API['OLD']['API'];settings=sealed(ROOT/'reports/native-compiler-042-ledger.json')
    cmd="ConvertTo-Json -Compress -InputObject @(Get-Process terminal64 -ErrorAction SilentlyContinue | ForEach-Object { [pscustomobject]@{pid=$_.Id;path=$_.Path} })"
    result=old['command'](bound(settings['powershell_path']),cmd)
    if result.returncode!=0:raise ValueError('existing_terminal_not_unique')
    rows=json.loads(result.stdout)
    if len(rows)!=1 or rows[0]['path'].casefold()!=str(bound('/mnt/c/Program Files/MetaTrader 5/terminal64.exe')).casefold():
        raise ValueError('existing_terminal_not_unique')
    return rows[0]['pid']

def read_append(log,offset):
    if not log.exists():raise ValueError('native_log_missing')
    size=log.stat().st_size
    if size<offset or size-offset>1049576:raise ValueError('native_log_truncated_or_budget_exceeded')
    with log.open('rb') as f:f.seek(offset);raw=f.read(1049577)
    return records_from_log(raw),size,len(raw)

def run():
    require_interactive(sys.stdin) # Before any reservation, SDK import or connection.
    ledger=API['verify']();date_guard(time.time_ns()//1000000)
    assert os.name=='nt' and not RESERVATION.exists() and not OUTPUT.exists()
    assert sealed(ROOT/'reports/native-pipe-049-regression.json')['passed']
    assert sealed(ROOT/'reports/native-pipe-049-native-tests.json')['passed']
    prep=sealed(ROOT/'reports/native-pipe-049-preparation-checks.json')
    assert prep['checker_passed'] and prep['ledger_sha256']==sha(API['LEDGER'])
    build=sealed(ROOT/'reports/native-pipe-049-build.json')
    assert prep['build_sha256']==sha(ROOT/'reports/native-pipe-049-build.json')
    assert prep['output_bindings']==build['output_bindings']
    source_seal=sealed(ROOT/'reports/native-pipe-049-preparation-final-source.json')
    assert source_seal['fixture_compiled'] and not source_seal['native_mt5_transport_verified']
    assert source_seal['source_and_evidence_bindings']['scripts/runtime-native-pipe-049.py']==sha(Path(__file__))
    assert build['compiled'] and build['errors']==build['warnings']==0
    artifact_name=next(n for n in build['output_bindings'] if n.endswith('/ForexDemoPipeFixture049.ex5'))
    artifact=bound(artifact_name);assert sha(artifact)==build['output_bindings'][artifact_name]
    write(RESERVATION,dict(ledger_sha256=sha(API['LEDGER']),declared_date='2026-10-07',
        maximum_sdk_connections=1,maximum_script_arms=3,maximum_grants=1,maximum_session_seconds=900,
        quote_reads=0,orders_available=False,reservation_consumed=True))
    state=Session049();stop=Event();lock=RLock();commands=Queue();server_thread=None;authority=None
    mt5=None;connections=0;deployment=None;reason=None;guards=0;offset=None;anchors=[];record_bindings={}
    transport=dict(peer_verified=False,request_valid=False,response_written=False,closed=False,error=False)
    log=None;log_attempted=set();stopped_evidence=None
    def input_reader():
        for line in sys.stdin:commands.put(line.strip())
        commands.put('eof')
    try:
        win=ManualWindowsPipe049();pid=terminal_process();peer=win.identity(pid);owner=win.identity(os.getpid())
        terminal=bound('/mnt/c/Program Files/MetaTrader 5/terminal64.exe')
        expected=ledger['bindings']['/mnt/c/Program Files/MetaTrader 5/terminal64.exe']
        if peer[3]!=expected or peer[-2:]!=owner[-2:]:raise ValueError('terminal_process_binding_rejected')
        import MetaTrader5 as sdk
        if sdk.__version__!='5.0.6231':raise ValueError('sdk_version_changed')
        if terminal_process()!=pid:raise ValueError('terminal_process_binding_rejected')
        connections=1;mt5=sdk
        if not mt5.initialize(str(terminal),timeout=15000):raise ValueError('existing_terminal_connection_failed')
        metadata=MetadataOnly(mt5)
        readiness=Readiness049(metadata,lambda:win.identity(pid),peer,terminal.parent)
        data_root=Path(readiness.data_root);reject_reparse(data_root)
        log=data_root/'MQL5'/'Logs'/'20261007.log'
        def guard():
            nonlocal guards
            with lock:
                date_guard(win.clock()[0])
                if stop.is_set() or state.remaining_ms()<=2000:raise ValueError('session_deadline_or_clock_reversal')
                readiness.check()
                if deployment is not None:
                    reject_reparse(deployed)
                    if sha(deployed)!=build['output_bindings'][artifact_name]:raise ValueError('deployed_fixture_changed')
                guards+=1
                return True
        guard()
        scripts=data_root/'MQL5'/'Scripts';reject_reparse(scripts)
        directory=scripts/('ForexDemoLab049-'+uuid.uuid4().hex);directory.mkdir(exist_ok=False)
        deployed=directory/'ForexDemoPipeFixture049.ex5'
        with artifact.open('rb') as src,deployed.open('xb') as dst:
            for chunk in iter(lambda:src.read(1049576),b''):dst.write(chunk)
            dst.flush();os.fsync(dst.fileno())
        if sha(deployed)!=build['output_bindings'][artifact_name]:raise ValueError('deployed_fixture_changed')
        deployment=dict(folder=directory.name,artifact_binding={API['OLD']['API']['external_name'](str(deployed)):sha(deployed)})
        guard();write(ROOT/'reports/native-pipe-049-deployment.json',dict(**deployment,ledger_sha256=sha(API['LEDGER']),
            actual_demo_usd_algo_off_verified=True,compiled_artifact_sha256=sha(artifact),quote_reads=0,orders_available=False))
        policy=Policy('49000000000000000000000000000001','49'*32)
        def journal(record):
            write(ROOT/'reports/native-pipe-049-consumption.json',dict(**record,ledger_sha256=sha(API['LEDGER'])))
            return True
        authority=start_authority(ROOT/'reports/native-pipe-049-authority-reservation.json',policy,win.clock,guard,journal)
        Thread(target=input_reader,daemon=True).start()
        print(json.dumps(dict(status='prepared',folder=deployment['folder'],actual_demo_usd_algo_off_verified=True,
            maximum_manual_runs=3,quote_reads=0)),flush=True)
        while True:
            remaining=state.remaining_ms()
            if transport['error']:raise ValueError('native_transport_rejected')
            try:command=commands.get(timeout=min(1,remaining/1000))
            except Empty:continue
            if command in ('finish','eof'):break
            if command not in {verb+'-'+step for verb in ('arm','collect') for step in ('disabled','enabled','repeat')}:
                raise ValueError('undeclared_runtime_command')
            guard();verb,step=command.split('-')
            if verb=='arm':
                if offset is not None:
                    extra,new_offset,_=read_append(log,offset)
                    if extra:raise ValueError('unarmed_extra_fixture_record')
                state.arm(step)
                if step=='repeat' and (server_thread is None or server_thread.is_alive() or not transport['closed']):
                    raise ValueError('server_not_closed_before_repeat')
                offset=log.stat().st_size if log.exists() else 0
                if offset%2:raise ValueError('native_log_anchor_unaligned')
                anchor=dict(step=step,offset_bytes=offset,armed_utc_ms=win.clock()[0]);anchors.append(anchor)
                write(ROOT/f'reports/native-pipe-049-{step}-started.json',dict(anchor=anchor,script_arm_consumed=True,
                    ledger_sha256=sha(API['LEDGER']),quote_reads=0,orders_available=False))
                if step=='enabled':
                    h=win.server('\\\\.\\pipe\\ForexDemoFixture047-'+policy.phase,owner)
                    def serve():
                        try:
                            win.connect_until(h,state.deadline,stop)
                            win.peer(h,'client',peer);transport['peer_verified']=True
                            guard();raw=win.io(h,'read',size=57)
                            try:phase,digest=decode_request(raw,policy)
                            except PermitRejected:
                                authority.issue('invalid','invalid');raise
                            transport['request_valid']=True
                            reply=encode_response(authority.issue(phase,digest))
                            win.io(h,'write',data=reply);transport['response_written']=True
                        except Exception:transport['error']=True
                        finally:
                            authority.close();win.close(h);transport['closed']=True
                    server_thread=Thread(target=serve,daemon=True);server_thread.start()
                print(json.dumps(dict(status='armed',step=step,quote_reads=0)),flush=True)
            else:
                if state.pending!=step or offset is None:raise ValueError('fixture_order_or_budget_rejected')
                if step=='enabled':
                    server_thread.join(3)
                    if server_thread.is_alive() or transport['error']:raise ValueError('native_transport_rejected')
                log_attempted.add(step)
                rows,new_offset,read_bytes=read_append(log,offset)
                p=ROOT/f'reports/native-pipe-049-{step}-records.json'
                write(p,dict(records=rows,anchor=anchors[-1],read_bytes=read_bytes,ledger_sha256=sha(API['LEDGER'])))
                record_bindings[p.relative_to(ROOT).as_posix()]=sha(p)
                record=state.collect(rows);offset=new_offset;guard()
                print(json.dumps(dict(status='collected',step=step,record=record)),flush=True)
    except (Exception,KeyboardInterrupt) as exc:
        allowed={'existing_terminal_not_unique','terminal_process_binding_rejected','existing_terminal_connection_failed',
            'declared_date_expired','session_deadline_or_clock_reversal','terminal_metadata_changed','sdk_version_changed',
            'reparse_path_rejected','deployed_fixture_changed','native_transport_rejected','native_fixture_outcome_rejected',
            'exactly_one_fixture_record_required','fixture_order_or_budget_rejected','unarmed_extra_fixture_record',
            'native_log_missing','native_log_truncated_or_budget_exceeded','fixture_schema_rejected',
            'disconnected','actual_account_not_demo','account_currency_not_usd','algo_trading_enabled',
            'account_changed_or_invalid','symbol_not_supported_or_visible','server_not_closed_before_repeat'}
        reason=str(exc) if str(exc) in allowed else 'runtime_failure_details_redacted'
    finally:
        stop.set()
        if server_thread is not None:server_thread.join(6)
        if authority is not None:authority.close()
        if mt5 is not None:mt5.shutdown()
        if reason is not None and log is not None and offset is not None:
            def save_stopped(data):
                nonlocal stopped_evidence
                p=ROOT/'reports/native-pipe-049-stopped-records.json'
                write(p,dict(**data,ledger_sha256=sha(API['LEDGER']),anchor=anchors[-1]))
                stopped_evidence={p.relative_to(ROOT).as_posix():sha(p)}
            collect_stopped_record(log,offset,state.pending,log_attempted,save_stopped)
    complete=reason is None and len(state.records)==3 and state.pending is None and transport['response_written'] and transport['closed'] and not _PENDING
    if not complete and reason is None:reason='native_fixture_session_incomplete'
    if server_thread is not None and server_thread.is_alive() or _PENDING:
        complete=False;reason='native_io_lifetime_unproven'
    write(OUTPUT,dict(completed=complete,stop_reason=reason,declared_date='2026-10-07',ledger_sha256=sha(API['LEDGER']),
        reservation_sha256=sha(RESERVATION),native_connections_attempted=connections,script_arms=state.arms,
        records=state.records,record_bindings=record_bindings,anchors=anchors,transport=transport,
        permissions_consumed=authority.summary()['permissions_consumed'] if authority else 0,
        sdk_shutdown_called=mt5 is not None,guard_checks=guards,deployment=deployment,stopped_evidence=stopped_evidence,
        elapsed_seconds=time.monotonic()-state.started,cancellation_drained=not bool(_PENDING),
        cooperating_pipe_owner_assumption=True,independent_mql_server_pid_authentication=False,
        sdk_quote_reads=0,native_quote_reads=0,historical_reads=0,http_requests=0,strategy_replays=0,
        orders_available=False,fresh_performance_eligible=False,annual_eligible=False))
    print(json.dumps(dict(status='finished',completed=complete,stop_reason=reason,quote_reads=0)),flush=True)

if __name__=='__main__':run()
