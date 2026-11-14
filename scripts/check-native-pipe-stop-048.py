"""Independent original stopped-session record and permission-budget proof."""
import json
from pathlib import Path
import runpy
ROOT=Path(__file__).resolve().parents[1];API=runpy.run_path(str(ROOT/'scripts/native-pipe-048.py'))
OFFLINE=runpy.run_path(str(ROOT/'scripts/offline-native-pipe-stop-048.py'))

def check():
    sha,sealed,write=API['sha'],API['sealed'],API['write'];OFFLINE['verify_offline']()
    p=ROOT/'reports/native-pipe-048-disabled-stop-records.json';audit=sealed(p)
    reservation=ROOT/'reports/native-pipe-048-stop-audit-reservation.json';plan=sealed(reservation)
    for n,h in plan['bindings'].items():assert sha(ROOT/n)==h
    rpath=ROOT/'reports/native-pipe-048-runtime.json';r=sealed(rpath)
    assert audit['reservation_sha256']==sha(reservation) and audit['runtime_sha256']==sha(rpath)
    assert audit['anchor']==plan['anchor']==r['anchors'][0]
    assert 0<=audit['log_reads']<=1 and 0<=audit['read_bytes']<=1048576
    assert r['completed'] is False and r['stop_reason']=='disconnected' and r['records']==[]
    assert r['script_arms']==['disabled'] and r['permissions_consumed']==0 and r['sdk_shutdown_called']
    assert all(r['transport'][k] is False for k in r['transport'])
    original_checks=sealed(ROOT/'reports/native-pipe-048-checks.json')
    assert original_checks['checker_passed'] is False and original_checks['stop_reason']=='original_preflight_dependency_changed'
    regression=sealed(ROOT/'reports/native-pipe-048-regression.json')
    native=sealed(ROOT/'reports/native-pipe-048-native-tests.json')
    assert regression['passed'] and regression['tests_run']==682 and native['passed'] and len(native['cases'])==5
    assert native['cancellation_drained'] and not native['actual_mt5_peer_tested']
    assert not (ROOT/'reports/native-pipe-048-consumption.json').exists()
    expected={'version':'pipe_fixture_047_v1','reason_code':17,'requests':0,'receipt_valid':False,'quote_reads':0,'orders':0}
    assert audit['disabled_proof_passed'] is (audit['records']==[expected])
    for row in audit['records']:
        assert set(row)==set(expected) and row['quote_reads']==row['orders']==0
        assert type(row['reason_code']) is int and type(row['requests']) is int and type(row['receipt_valid']) is bool
    if audit['disabled_proof_passed']:assert audit['stop_reason'] is None
    for k in ('sdk_connections','quote_reads'):assert audit[k]==0
    for k in ('orders_available','fresh_performance_eligible','annual_eligible'):assert audit[k] is False
    write(ROOT/'reports/native-pipe-048-stop-audit-checks.json',dict(checker_passed=True,
        audit_sha256=sha(p),runtime_sha256=sha(rpath),disabled_proof_passed=audit['disabled_proof_passed'],
        original_runtime_completed=False,original_runtime_collected_records=0,permissions_consumed=0,
        original_checker_passed=False,installed_file_changes_accounted_for=2,tests_passed_before_change=682,
        native_lifetime_cases=5,quote_reads=0,orders_available=False,fresh_performance_eligible=False,annual_eligible=False))
    print(json.dumps(dict(checker_passed=True,disabled_proof_passed=audit['disabled_proof_passed'])))

if __name__=='__main__':check()
