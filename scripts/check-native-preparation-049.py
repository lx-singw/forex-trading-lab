"""Independent preparation counters/artifacts and no-market guards."""
import json
from pathlib import Path
import re
import runpy
ROOT=Path(__file__).resolve().parents[1];API=runpy.run_path(str(ROOT/'scripts/native-pipe-049.py'))

def check():
    ledger=API['verify']();sha,sealed,write=API['sha'],API['sealed'],API['write']
    tests=sealed(ROOT/'reports/native-pipe-049-regression.json');native=sealed(ROOT/'reports/native-pipe-049-native-tests.json')
    build=sealed(ROOT/'reports/native-pipe-049-build.json')
    assert tests['passed'] and tests['tests_run']==718 and tests['new_tests']==36 and tests['wire_differential_frames']==87
    assert native['passed'] and len(native['cases'])==5 and native['cancellation_drained'] and not native['actual_mt5_peer_tested']
    assert build['compiled'] and build['errors']==build['warnings']==0 and build['compiler_invocations']==1
    assert build['effective_policy_before']==build['effective_policy_after']=='Restricted' and not build['execution_policy_changed']
    assert all(p['ledger_sha256']==sha(API['LEDGER']) for p in (tests,native,build))
    outputs=build['output_bindings'];assert len(outputs)==6
    for n,h in outputs.items():
        path=API['bound'](n);assert sha(path)==h
        if path.suffix in ('.mq5','.mqh'):assert sha(ROOT/'mt5/Scripts'/path.name)==h
        if path.name=='compile.log':assert re.search(r'Result:\s*0 errors,\s*0 warnings',path.read_text(encoding='utf-16'))
    assert ledger['phase']=='49000000000000000000000000000001' and ledger['expected_running_build']==6244
    for n in ('reports/fresh-context-033-checks.json','reports/fresh-replication-035-checks.json'):
        assert sealed(ROOT/n)['diagnostic_passed'] is False
    write(ROOT/'reports/native-pipe-049-preparation-checks.json',dict(checker_passed=True,ledger_sha256=sha(API['LEDGER']),
        build_sha256=sha(ROOT/'reports/native-pipe-049-build.json'),output_bindings=outputs,
        tests_passed=718,new_tests=36,native_lifetime_cases=5,wire_differential_frames=87,
        native_mt5_transport_verified=False,sdk_connections=0,quote_reads=0,orders_available=False,
        fresh_performance_eligible=False,annual_eligible=False))
    print(json.dumps(dict(checker_passed=True,tests=718,compiled=True,native_mt5_transport_verified=False)))

if __name__=='__main__':check()
