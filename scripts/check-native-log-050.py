"""Independent fixed-range count/schema/budget check; no log reread."""
import json
from pathlib import Path
import runpy
ROOT=Path(__file__).resolve().parents[1];API=runpy.run_path(str(ROOT/'scripts/native-log-050.py'))

def check():
    sha,sealed,write=API['sha'],API['sealed'],API['write']
    ledger=sealed(API['LEDGER']);p=sealed(API['OUTPUT'])
    for n,h in ledger['bindings'].items():assert sha(API['bound'](n))==h,n
    assert ledger['start_byte']==364 and ledger['end_byte']==726 and ledger['maximum_content_reads']==1
    assert p['ledger_sha256']==sha(API['LEDGER']) and p['original_runtime_sha256']==sha(ROOT/'reports/native-pipe-049-runtime.json')
    assert p['content_reads'] in (0,1) and 0<=p['read_bytes']<=362
    expected=dict(version='pipe_fixture_049_v1',reason_code=17,requests=0,receipt_valid=False,quote_reads=0,orders=0)
    assert p['disabled_proof_passed'] is (p['records']==[expected])
    if p['disabled_proof_passed']:
        assert p['stop_reason'] is None and p['content_reads']==1 and p['read_bytes']==362 and len(p['range_sha256'])==64
    r=sealed(ROOT/'reports/native-pipe-049-runtime.json')
    assert r['completed'] is False and r['stop_reason']=='exactly_one_fixture_record_required'
    assert r['script_arms']==['disabled'] and r['records']==[] and r['permissions_consumed']==0 and r['sdk_shutdown_called']
    assert all(v is False for v in r['transport'].values())
    assert not (ROOT/'reports/native-pipe-049-consumption.json').exists()
    for k in ('quote_reads','sdk_connections','permissions_consumed'):assert p[k]==0
    for k in ('orders_available','fresh_performance_eligible','annual_eligible','original_runtime_completed'):assert p[k] is False
    write(ROOT/'reports/native-log-050-checks.json',dict(checker_passed=True,audit_sha256=sha(API['OUTPUT']),
        ledger_sha256=sha(API['LEDGER']),disabled_proof_passed=p['disabled_proof_passed'],original_runtime_completed=False,
        original_runtime_collected_records=0,quote_reads=0,orders_available=False,fresh_performance_eligible=False,annual_eligible=False))
    print(json.dumps(dict(checker_passed=True,disabled_proof_passed=p['disabled_proof_passed'])))

if __name__=='__main__':check()
