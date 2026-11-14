"""Independent saved-output/counter/source/log/gate check; no native actions."""
import json
from pathlib import Path
import re
import runpy
ROOT=Path(__file__).resolve().parents[1];API=runpy.run_path(str(ROOT/'scripts/capture-transport-047.py'))
sha,write,sealed,bound=API['sha'],API['write'],API['sealed'],API['bound']

def check():
    API['verify']();build_path=ROOT/'reports/capture-transport-047-build.json';b=sealed(build_path)
    t=sealed(ROOT/'reports/capture-transport-047-regression-r3.json');n=sealed(ROOT/'reports/capture-transport-047-native-r3.json')
    assert t['passed'] and t['tests_passed']==t['tests_run']==666 and t['new_tests']==12
    assert t['errors']==t['failures']==t['skipped']==0
    assert n['passed'] and n['cases_passed']==len(n['cases'])==14
    cases={r['case']:r for r in n['cases']};assert len(cases)==14 and all(r['passed'] is True for r in cases.values())
    for name in ('valid','parallel'):assert cases[name]['valid_responses']==cases[name]['permission_consumed']==1
    for name,r in cases.items():
        if name not in ('valid','parallel') and 'valid_responses' in r:assert r['valid_responses']==0
        if 'permission_consumed' in r:assert 0<=r['permission_consumed']<=1 and r['restart_blocked'] and r['repeat_blocked']
    assert n['synthetic_guard_only'] and not n['actual_mt5_peer_tested']
    assert all(n[k] is True for k in ('both_windows_peer_identities_checked','explicit_logon_dacl','remote_clients_rejected','first_instance_only','cancellation_drained'))
    assert b['compiled'] and b['errors']==b['warnings']==0 and b['compiler_invocations']==1 and b['stop_reason'] is None
    assert not b['fixture_attached'] and not b['fixture_runtime_executed'] and not b['execution_policy_changed']
    assert b['effective_policy_before']==b['effective_policy_after']=='Restricted'
    files={Path(name).name:(name,h) for name,h in b['output_bindings'].items()}
    assert set(files)=={'ForexDemoPipeFixture047.mq5','CaptureWire047.mqh','CapturePermit046.mqh','ClockGuard042.mqh','compile.log','ForexDemoPipeFixture047.ex5'}
    for name,(path,h) in files.items():
        assert sha(bound(path))==h
        if name.endswith(('.mq5','.mqh')):assert h==sha(ROOT/'mt5/Scripts'/name)
    log=bound(files['compile.log'][0]).read_text(encoding='utf-16')
    summary=re.findall(r'Result:\s*(\d+)\s+errors?,\s*(\d+)\s+warnings?',log,re.I)
    assert summary==[('0','0')] and bound(files['ForexDemoPipeFixture047.ex5'][0]).stat().st_size>0
    for data in (n,b,t):
        assert data['quote_reads' if 'quote_reads' in data else 'new_quote_reads']==0
        assert data['sdk_connections']==0 and data['orders_available'] is False
    old=sealed(ROOT/'reports/capture-transport-047-native.json');assert old['passed'] is False
    assert not (ROOT/'reports/capture-transport-047-native-started.json').exists()
    assert sealed(ROOT/'reports/clock-log-audit-045-checks.json')['acquisition_budget_compliant'] is False
    assert sealed(ROOT/'reports/clock-log-audit-045-checks.json')['recorded_native_quote_reads']==6
    for p in ('fresh-context-033-checks.json','fresh-replication-035-checks.json'):
        assert sealed(ROOT/'reports'/p)['diagnostic_passed'] is False
    write(ROOT/'reports/capture-transport-047-checks.json',dict(checker_passed=True,
        build_sha256=sha(build_path),ledger_sha256=sha(API['LEDGER']),tests_passed=666,native_cases_passed=14,
        compiler_log_errors=0,compiler_log_warnings=0,compiled=True,output_bindings=b['output_bindings'],
        earlier_prestart_stop_preserved=True,native_mt5_runtime_verified=False,quote_reads=0,sdk_connections=0,
        orders_available=False,fresh_performance_eligible=False,annual_eligible=False))
    print(json.dumps(dict(checker_passed=True,tests_passed=666,native_cases_passed=14,compiled=True)))

if __name__=='__main__':check()
