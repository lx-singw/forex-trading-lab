"""Independently verify059 sanitized record and unchanged original failure."""
import json
from pathlib import Path
import runpy
ROOT=Path(__file__).resolve().parents[1]
API=runpy.run_path(str(ROOT/'scripts/native-log-059.py'))
def check():
    sha,sealed,write=API['sha'],API['sealed'],API['write']
    l=sealed(API['LEDGER']);r=sealed(API['OUTPUT'])
    for n,h in l['bindings'].items():assert sha(API['bound'](n))==h,n
    assert r['ledger_sha256']==sha(API['LEDGER']) and r['audit_passed']
    assert r['content_reads']==1 and r['read_bytes']==558 and len(r['records'])==1
    from forex_demo_lab.native_pipe_057 import PREFIX,parse_record
    row=r['records'][0];assert parse_record(PREFIX+json.dumps(row))==row
    for k in ('sdk_connections','new_permissions','quote_reads'):assert r[k]==l[k]==0
    assert not r['original_runtime_completed'] and not r['orders_available']
    runtime=sealed(ROOT/'reports/native-pipe-057-runtime.json')
    assert not runtime['completed'] and runtime['permissions_consumed']==1 and runtime['script_arms']==['disabled','enabled']
    assert runtime['diagnostic_trace'][0]['windows_operations'][-1]['events'][1]['category']=='pipe_closing'
    for n in ('reports/fresh-context-033-checks.json','reports/fresh-replication-035-checks.json'):
        assert not sealed(ROOT/n)['diagnostic_passed']
    write(ROOT/'reports/native-log-059-checks.json',dict(checker_passed=True,audit_sha256=sha(API['OUTPUT']),
        ledger_sha256=sha(API['LEDGER']),native_record=row,original_runtime_completed=False,
        sdk_connections=0,quote_reads=0,orders_available=False))
    print(json.dumps(dict(checker_passed=True,record=row)))
if __name__=='__main__':check()
