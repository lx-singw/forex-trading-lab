"""Check original048 sanitized records, immutable deployment and fixed budgets."""
import json
from pathlib import Path
import runpy
ROOT=Path(__file__).resolve().parents[1];API=runpy.run_path(str(ROOT/'scripts/native-pipe-048.py'))
sha,sealed,write=API['sha'],API['sealed'],API['write']

def check():
    ledger=API['verify']();tests=sealed(ROOT/'reports/native-pipe-048-regression.json')
    native=sealed(ROOT/'reports/native-pipe-048-native-tests.json');r=sealed(ROOT/'reports/native-pipe-048-runtime.json')
    assert tests['passed'] and tests['tests_run']==682 and native['passed'] and len(native['cases'])==5
    assert r['ledger_sha256']==sha(API['LEDGER']) and r['declared_date']==ledger['declared_date']=='2026-10-07'
    assert r['native_connections_attempted'] in (0,1) and r['script_arms']==['disabled','enabled','repeat'][:len(r['script_arms'])]
    assert len(r['records'])<=len(r['script_arms'])<=3 and r['permissions_consumed'] in (0,1)
    original=[]
    for n,h in r['record_bindings'].items():
        assert sha(ROOT/n)==h;data=sealed(ROOT/n)
        assert data['ledger_sha256']==r['ledger_sha256'] and data['read_bytes']<=1048576
        original+=data['records']
    if r['completed']:
        assert r['stop_reason'] is None and r['sdk_shutdown_called'] and r['elapsed_seconds']<=901
        assert r['records']==original and len(original)==3 and r['permissions_consumed']==1
        for record,expect in zip(original,((17,0,False),(0,1,True),(20,0,False))):
            assert set(record)=={'version','reason_code','requests','receipt_valid','quote_reads','orders'}
            assert record['version']=='pipe_fixture_047_v1' and record['quote_reads']==record['orders']==0
            assert (record['reason_code'],record['requests'],record['receipt_valid'])==expect
        assert all(r['transport'][k] for k in ('peer_verified','request_valid','response_written','closed')) and not r['transport']['error']
        assert sealed(ROOT/'reports/native-pipe-048-consumption.json')['permissions_consumed']==1
    if r['deployment']:
        d=sealed(ROOT/'reports/native-pipe-048-deployment.json');assert d['artifact_binding']==r['deployment']['artifact_binding']
        for n,h in d['artifact_binding'].items():assert sha(API['bound'](n))==h==d['compiled_artifact_sha256']
    assert r['cooperating_pipe_owner_assumption'] and not r['independent_mql_server_pid_authentication']
    for k in ('sdk_quote_reads','native_quote_reads','historical_reads','http_requests','strategy_replays'):assert r[k]==0
    for k in ('orders_available','fresh_performance_eligible','annual_eligible'):assert r[k] is False
    write(ROOT/'reports/native-pipe-048-checks.json',dict(checker_passed=True,runtime_completed=r['completed'],
        runtime_sha256=sha(ROOT/'reports/native-pipe-048-runtime.json'),ledger_sha256=sha(API['LEDGER']),
        tests_passed=682,native_lifetime_cases=5,quote_reads=0,orders_available=False,fresh_performance_eligible=False,annual_eligible=False))
    print(json.dumps(dict(checker_passed=True,runtime_completed=r['completed'])))

if __name__=='__main__':check()
