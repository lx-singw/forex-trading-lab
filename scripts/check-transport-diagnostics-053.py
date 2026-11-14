"""Independent counters, closure/source and preserved failure checks; no log read."""
import json
from pathlib import Path
import runpy

ROOT=Path(__file__).resolve().parents[1];API=runpy.run_path(str(ROOT/'scripts/transport-diagnostics-053.py'))

def check():
    ledger=API['verify']();sha,sealed,write=API['sha'],API['sealed'],API['write']
    t=sealed(ROOT/'reports/transport-diagnostics-053-r2-tests.json')
    assert t['ledger_sha256']==sha(API['LEDGER']) and t['passed']
    assert (t['tests_run'],t['new_tests'],t['differential_cases'],t['errors'],t['failures'],t['skipped'])==(774,32,99,0,0,0)
    API['API']['original_failure']()
    assert sealed(ROOT/'reports/native-log-052-audit.json')['records'][0]['reason_code']==23
    for n in ('reports/fresh-context-033-checks.json','reports/fresh-replication-035-checks.json'):
        assert sealed(ROOT/n)['diagnostic_passed'] is False
    for k in ('sdk_connections','market_reads','native_fixture_invocations','native_metatrader_compiler_invocations'):
        assert t[k]==ledger[k]==0
    for k in ('orders_available','fresh_performance_eligible','annual_eligible'):assert ledger[k] is False
    first=sealed(ROOT/'reports/transport-diagnostics-053-tests.json')
    assert first['passed'] is False and first['tests_run']==774 and first['errors']==26
    assert ledger['revision']==2 and ledger['first_failure_preserved'] is True
    write(ROOT/'reports/transport-diagnostics-053-checks.json',dict(checker_passed=True,tests_sha256=sha(ROOT/'reports/transport-diagnostics-053-r2-tests.json'),
        ledger_sha256=sha(API['LEDGER']),tests_passed=774,new_tests=32,differential_cases=99,
        original051_runtime_completed=False,root_cause_proven=False,actual_mt5_repair_verified=False,
        sdk_connections=0,market_reads=0,orders_available=False,fresh_performance_eligible=False,annual_eligible=False))
    print(json.dumps(dict(checker_passed=True,tests_passed=774,actual_mt5_repair_verified=False)))

if __name__=='__main__':check()
