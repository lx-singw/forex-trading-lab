"""Independent range/schema/source checks; never reread the native log."""
import json
from pathlib import Path
import runpy

ROOT=Path(__file__).resolve().parents[1]
API=runpy.run_path(str(ROOT/'scripts/native-log-055.py'))

def check():
    sha,sealed,write=API['sha'],API['sealed'],API['write']
    ledger=sealed(API['LEDGER']);p=sealed(API['OUTPUT'])
    for n,h in ledger['bindings'].items():assert sha(API['bound'](n))==h,n
    assert (ledger['start_byte'],ledger['end_byte'],ledger['maximum_content_reads'])==(1520,1950,1)
    assert p['ledger_sha256']==sha(API['LEDGER']) and p['original_runtime_sha256']==sha(ROOT/'reports/native-pipe-054-runtime.json')
    assert p['content_reads'] in (0,1) and 0<=p['read_bytes']<=430
    from forex_demo_lab.native_pipe_054 import parse_record,PREFIX
    for row in p['records']:assert parse_record(PREFIX+json.dumps(row))==row
    if p['audit_passed']:
        assert p['stop_reason'] is None and p['content_reads']==1 and p['read_bytes']==430
        assert len(p['records'])==1 and len(p['range_sha256'])==64
    API['original_failure']()
    for k in ('sdk_connections','quote_reads','new_permissions'):assert p[k]==0
    for k in ('orders_available','fresh_performance_eligible','annual_eligible','original_runtime_completed'):assert p[k] is False
    write(ROOT/'reports/native-log-055-checks.json',dict(checker_passed=True,audit_sha256=sha(API['OUTPUT']),
        ledger_sha256=sha(API['LEDGER']),audit_passed=p['audit_passed'],original_runtime_completed=False,
        quote_reads=0,orders_available=False,fresh_performance_eligible=False,annual_eligible=False))
    print(json.dumps(dict(checker_passed=True,audit_passed=p['audit_passed'])))

if __name__=='__main__':check()
