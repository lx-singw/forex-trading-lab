"""Original051 runtime, shared049 proof, stopped evidence and strict budgets."""
import json
from pathlib import Path
import runpy
ROOT=Path(__file__).resolve().parents[1];API=runpy.run_path(str(ROOT/'scripts/native-pipe-051.py'))

def check():
    ledger=API['verify']();sha,sealed,write=API['sha'],API['sealed'],API['write']
    prep=sealed(ROOT/'reports/native-pipe-051-preparation-checks.json');assert prep['checker_passed']
    rp=ROOT/'reports/native-pipe-051-runtime.json';r=sealed(rp)
    assert r['ledger_sha256']==sha(API['LEDGER']) and r['declared_date']==ledger['declared_date']=='2026-10-07'
    assert r['reservation_sha256']==sha(ROOT/'reports/native-pipe-051-runtime-reservation.json')
    assert r['native_connections_attempted'] in (0,1) and r['script_arms']==['enabled','repeat'][:len(r['script_arms'])]
    assert len(r['records'])<=len(r['script_arms'])<=2 and r['permissions_consumed'] in (0,1)
    assert r['shared_disabled_proof_phase']=='049' and r['native051_disabled_run_executed'] is False
    assert r['shared_disabled_proof_sha256']==ledger['shared_disabled_proof_sha256'] and API['verify_disabled_proof']()
    original=[]
    for step in ('enabled','repeat'):
        n=f'reports/native-pipe-051-{step}-records.json'
        if n in r['record_bindings']:
            assert sha(ROOT/n)==r['record_bindings'][n];d=sealed(ROOT/n)
            assert d['ledger_sha256']==r['ledger_sha256'] and d['read_bytes']<=1048576
            original+=d['records']
    stopped=[]
    if r['stopped_evidence']:
        assert len(r['stopped_evidence'])==1 and not r['completed']
        for n,h in r['stopped_evidence'].items():
            assert sha(ROOT/n)==h;d=sealed(ROOT/n);assert d['ledger_sha256']==r['ledger_sha256'] and d['read_bytes']<=1048576
            assert d['sdk_connections']==0 and d['quote_reads']==0 and d['orders_available'] is False
            assert d['step']==r['anchors'][-1]['step'] and d['anchor']==r['anchors'][-1]
            stopped+=d['records']
    for row in original+stopped:
        assert set(row)=={'version','reason_code','requests','receipt_valid','quote_reads','orders'}
        assert row['version']=='pipe_fixture_051_v1' and row['quote_reads']==row['orders']==0
        assert type(row['reason_code']) is int and type(row['requests']) is int and type(row['receipt_valid']) is bool
    if r['completed']:
        assert r['stop_reason'] is None and r['sdk_shutdown_called'] and r['elapsed_seconds']<=901 and not stopped
        assert r['records']==original and len(original)==2 and r['permissions_consumed']==1 and r['guard_checks']>=9
        assert [x['step'] for x in r['log_save_acknowledgments']]==['baseline','enabled','repeat']
        for step in ('baseline','enabled','repeat'):
            name='baseline-saved' if step=='baseline' else step+'-logs-saved'
            ack=sealed(ROOT/f'reports/native-pipe-051-{name}.json')
            assert ack['user_acknowledgment'] is True and ack['ledger_sha256']==r['ledger_sha256']
        for row,expected in zip(original,((0,1,True),(20,0,False))):
            assert (row['reason_code'],row['requests'],row['receipt_valid'])==expected
        assert all(r['transport'][k] for k in ('peer_verified','request_valid','response_written','closed')) and not r['transport']['error']
        consumed=sealed(ROOT/'reports/native-pipe-051-consumption.json')
        assert consumed['permissions_consumed']==1 and consumed['phase']==ledger['phase']
    if r['deployment']:
        d=sealed(ROOT/'reports/native-pipe-051-deployment.json');assert d['artifact_binding']==r['deployment']['artifact_binding']
        for n,h in d['artifact_binding'].items():assert sha(API['bound'](n))==h==d['compiled_artifact_sha256']
    assert r['cooperating_pipe_owner_assumption'] and not r['independent_mql_server_pid_authentication']
    for k in ('sdk_quote_reads','native_quote_reads','historical_reads','http_requests','strategy_replays'):assert r[k]==0
    for k in ('orders_available','fresh_performance_eligible','annual_eligible'):assert r[k] is False
    write(ROOT/'reports/native-pipe-051-runtime-checks.json',dict(checker_passed=True,runtime_completed=r['completed'],
        runtime_sha256=sha(rp),ledger_sha256=sha(API['LEDGER']),native_records=len(original),stopped_records=len(stopped),
        permissions_consumed=r['permissions_consumed'],quote_reads=0,orders_available=False,
        fresh_performance_eligible=False,annual_eligible=False))
    print(json.dumps(dict(checker_passed=True,runtime_completed=r['completed'])))

if __name__=='__main__':check()
