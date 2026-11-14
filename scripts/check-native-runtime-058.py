"""Native057 outcome, diagnostic closure and strict no-market budgets."""
import json
from pathlib import Path
import runpy
ROOT=Path(__file__).resolve().parents[1];API=runpy.run_path(str(ROOT/'scripts/native-pipe-057.py'))

def check():
    runpy.run_path(str(ROOT/'scripts/native-pipe-058.py'))['verify']()
    ledger=API['verify']();sha,sealed,write=API['sha'],API['sealed'],API['write']
    from forex_demo_lab.native_pipe_057 import PREFIX,parse_record
    from forex_demo_lab.transport_diagnostics_053 import validate_report
    rp=ROOT/'reports/native-pipe-057-runtime.json';r=sealed(rp)
    assert r['ledger_sha256']==sha(API['LEDGER']) and r['declared_date']=='2026-10-07'
    assert r['reservation_sha256']==sha(ROOT/'reports/native-pipe-057-runtime-reservation.json')
    assert r['native_connections_attempted'] in (0,1) and r['script_arms']==['disabled','enabled','repeat'][:len(r['script_arms'])]
    assert len(r['records'])<=len(r['script_arms'])<=3 and r['permissions_consumed'] in (0,1)
    assert r['native_disabled_proof_required'] is True and r['cooperating_pipe_owner_assumption'] is True
    assert r['independent_mql_server_pid_authentication'] is False
    primary=[];stopped=[]
    for step in ('disabled','enabled','repeat'):
        name=f'reports/native-pipe-057-{step}-records.json'
        if name in r['record_bindings']:
            assert sha(ROOT/name)==r['record_bindings'][name];p=sealed(ROOT/name)
            assert p['ledger_sha256']==r['ledger_sha256'] and p['read_bytes']<=1048576
            primary+=p['records']
    if r['stopped_evidence']:
        assert len(r['stopped_evidence'])==1 and not r['completed']
        for name,h in r['stopped_evidence'].items():
            assert sha(ROOT/name)==h;p=sealed(ROOT/name)
            assert p['read_bytes']<=1048576 and p['anchor']==r['anchors'][-1]
            assert p['sdk_connections']==0 and p['quote_reads']==0 and p['orders_available'] is False
            stopped+=p['records']
    for row in primary+stopped:assert parse_record(PREFIX+json.dumps(row))==row
    assert len(r['diagnostic_trace'])<=1 and len(r['diagnostic_bindings'])<=1
    for d in r['diagnostic_trace']:
        base=dict(d);operations=base.pop('windows_operations');assert validate_report(base)==base
        from forex_demo_lab.native_pipe_057 import validate_operation
        assert type(operations) is list and len(operations)<=3
        for operation in operations:assert validate_operation(operation)==operation
    for name,h in r['diagnostic_bindings'].items():
        assert sha(ROOT/name)==h;p=sealed(ROOT/name)
        assert p['ledger_sha256']==r['ledger_sha256'] and p['diagnostic']==r['diagnostic_trace'][0]
    if r['completed']:
        assert r['stop_reason'] is None and r['sdk_shutdown_called'] and r['elapsed_seconds']<=901 and not stopped
        assert r['records']==primary and len(primary)==3 and r['permissions_consumed']==1
        assert r['guard_checks']>=10
        expected=((17,0,False,0,-1),(0,1,True,84,0),(20,0,False,0,-1))
        for row,values in zip(primary,expected):
            assert tuple(row[k] for k in ('reason_code','requests','receipt_valid','reply_bytes','decode_reason'))==values
        assert [a['step'] for a in r['log_save_acknowledgments']]==['baseline','disabled','enabled','repeat']
        for step in ('baseline','disabled','enabled','repeat'):
            name='baseline-saved' if step=='baseline' else step+'-logs-saved'
            ack=sealed(ROOT/f'reports/native-pipe-057-{name}.json')
            assert ack['user_acknowledgment'] is True and ack['ledger_sha256']==r['ledger_sha256']
        assert r['cancellation_drained'] and len(r['diagnostic_bindings'])==1
        d=r['diagnostic_trace'][0]
        assert d['reply_written'] and d['closed'] and not d['pending_retained'] and d['stop_reason'] is None and d['cleanup_reason'] is None
        assert d['permissions_consumed']==1
        assert all(r['transport'][k] for k in ('peer_verified','request_valid','response_written','closed')) and not r['transport']['error']
        consumed=sealed(ROOT/'reports/native-pipe-057-consumption.json')
        assert consumed['permissions_consumed']==1 and consumed['phase']==ledger['phase']
    if r['deployment']:
        p=sealed(ROOT/'reports/native-pipe-057-deployment.json')
        assert p['artifact_binding']==r['deployment']['artifact_binding']
        for name,h in p['artifact_binding'].items():assert sha(API['bound'](name))==h==p['compiled_artifact_sha256']
    for k in ('sdk_quote_reads','native_quote_reads','historical_reads','http_requests','strategy_replays'):assert r[k]==0
    for k in ('orders_available','fresh_performance_eligible','annual_eligible'):assert r[k] is False
    write(ROOT/'reports/native-pipe-057-runtime-checks.json',dict(checker_passed=True,runtime_completed=r['completed'],
        runtime_sha256=sha(rp),ledger_sha256=sha(API['LEDGER']),native_records=len(primary),stopped_records=len(stopped),
        permissions_consumed=r['permissions_consumed'],diagnostic_reports=len(r['diagnostic_trace']),quote_reads=0,orders_available=False,
        fresh_performance_eligible=False,annual_eligible=False))
    print(json.dumps(dict(checker_passed=True,runtime_completed=r['completed'])))

if __name__=='__main__':check()
