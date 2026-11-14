"""Independent diagnostic fixture preparation; no terminal runtime."""
import json
from pathlib import Path
import re
import runpy
ROOT=Path(__file__).resolve().parents[1];API=runpy.run_path(str(ROOT/'scripts/native-pipe-057.py'))

def check():
    ledger=API['verify']();sha,sealed,write=API['sha'],API['sealed'],API['write']
    t=sealed(ROOT/'reports/native-pipe-057-regression.json');n=sealed(ROOT/'reports/native-pipe-057-native-tests.json')
    b=sealed(ROOT/'reports/native-pipe-057-build.json')
    assert t['passed'] and (t['tests_run'],t['new_tests'],t['wire_differential_frames'])==(874,32,87)
    assert n['passed'] and len(n['cases'])==6 and n['cancellation_drained'] and n['actual_mt5_peer_tested'] is False
    assert b['compiled'] and b['errors']==b['warnings']==0 and b['compiler_invocations']==1
    assert b['effective_policy_before']==b['effective_policy_after']=='Restricted' and not b['execution_policy_changed']
    assert all(p['ledger_sha256']==sha(API['LEDGER']) for p in (t,n,b))
    outputs=b['output_bindings'];assert len(outputs)==8
    for name,h in outputs.items():
        p=API['bound'](name);assert sha(p)==h
        if p.suffix in ('.mq5','.mqh'):assert sha(ROOT/'mt5/Scripts'/p.name)==h
        if p.name=='compile.log':assert re.search(r'Result:\s*0 errors,\s*0 warnings',p.read_text(encoding='utf-16'))
    assert ledger['phase']=='57000000000000000000000000000001' and ledger['native_disabled_proof_required'] is True
    assert ledger['maximum_script_arms']==0 and ledger['expected_running_build']==6244
    assert sealed(ROOT/'reports/native-pipe-054-runtime.json')['completed'] is False
    assert sealed(ROOT/'reports/native-pipe-051-runtime.json')['completed'] is False
    assert sealed(ROOT/'reports/native-pipe-057-installed-pins.json')['pins_match']
    assert ledger['maximum_sdk_connections']==ledger['maximum_grants']==ledger['maximum_deployments']==0
    assert sealed(ROOT/'reports/native-log-052-audit.json')['records'][0]['reason_code']==23
    for name in ('reports/fresh-context-033-checks.json','reports/fresh-replication-035-checks.json'):
        assert sealed(ROOT/name)['diagnostic_passed'] is False
    write(ROOT/'reports/native-pipe-057-preparation-checks.json',dict(checker_passed=True,ledger_sha256=sha(API['LEDGER']),
        build_sha256=sha(ROOT/'reports/native-pipe-057-build.json'),output_bindings=outputs,tests_passed=874,new_tests=32,
        native_lifetime_cases=6,wire_differential_frames=87,native_disabled_proof_required=True,
        native_mt5_transport_verified=False,sdk_connections=0,quote_reads=0,orders_available=False,
        fresh_performance_eligible=False,annual_eligible=False))
    print(json.dumps(dict(checker_passed=True,tests=874,compiled=True)))

if __name__=='__main__':check()
