"""One frozen existing-log audit; no SDK, pipe, compiler or runtime retries."""
import hashlib
import json
from pathlib import Path
import runpy
import zipfile
ROOT=Path(__file__).resolve().parents[1]
API=runpy.run_path(str(ROOT/'scripts/native-pipe-057.py'))
sha,sealed,write,bound=API['sha'],API['sealed'],API['write'],API['bound']
PRIOR=ROOT/'reports/native-pipe-057-final-source.json'
LEDGER=ROOT/'reports/native-log-059-ledger.json'
OUTPUT=ROOT/'reports/native-log-059-audit.json'

def prior_verify():
    assert sha(PRIOR)=='d5cc7e30f4adcbc5cbacc5ace5484bf2c52da74ff2c93e37a942944e030a1e93'
    f=sealed(PRIOR);b=f['source_and_evidence_bindings'];assert len(b)==1882
    review=sealed(ROOT/'reports/native-pipe-058-completion-review.json')
    assert review['review_passed'] and review['frozen_input_coverage_complete'] and review['final_source_sha256']==sha(PRIOR)
    for n,h in b.items():assert sha(bound(n))==h,n
    helper=runpy.run_path(str(ROOT/'scripts/transport-diagnostics-056.py'))
    assert helper['verify_archive'](PRIOR,f)==1748
    runtime=sealed(ROOT/'reports/native-pipe-057-runtime.json')
    assert not runtime['completed'] and runtime['stop_reason']=='native_transport_rejected'
    assert runtime['script_arms']==['disabled','enabled'] and runtime['permissions_consumed']==1
    assert runtime['sdk_shutdown_called'] and runtime['cancellation_drained'] and runtime['transport']['closed']
    d=runtime['diagnostic_trace'][0]
    assert d['windows_operations'][-1]['events'][1]['category']=='pipe_closing'
    assert d['windows_operations'][-1]['transferred_bytes'] is None and not d['reply_written']
    stopped=sealed(ROOT/'reports/native-pipe-057-stopped-records.json')
    assert stopped['read_bytes']==0 and stopped['records']==[] and stopped['anchor']['offset_bytes']==2508
    return b,runtime

def run():
    b,runtime=prior_verify();b={n:h for n,h in b.items() if n not in API['HANDOFF']}
    for suffix in ('.json','.sha256','.zip'):
        p=PRIOR.with_suffix(suffix);b[p.relative_to(ROOT).as_posix()]=sha(p)
    for pattern in ('scripts/*059.py','docs/*059*.md','reports/native-pipe-058-completion-review.*'):
        for p in ROOT.glob(pattern):b[p.relative_to(ROOT).as_posix()]=sha(p)
    write(LEDGER,dict(bindings=b,start_byte=2508,end_byte=3066,maximum_content_reads=1,
        prior_bindings_verified=1882,prior_archive_members_verified=1748,user_enabled_log_saved=True,
        original_runtime_completed=False,sdk_connections=0,new_permissions=0,quote_reads=0,orders_available=False))
    rows=[];count=0;digest=None;reads=0;reason=None
    try:
        for n,h in b.items():assert sha(bound(n))==h,n
        name=next(iter(runtime['deployment']['artifact_binding']))
        log=bound(name).parents[2]/'Logs'/'20261007.log'
        if log.stat().st_size<3066:raise ValueError('frozen_log_range_unavailable')
        reads=1
        with log.open('rb') as stream:stream.seek(2508);raw=stream.read(558)
        count=len(raw);digest=hashlib.sha256(raw).hexdigest()
        if count!=558:raise ValueError('frozen_log_range_partial')
        from forex_demo_lab.native_pipe_057 import records_from_log
        rows=records_from_log(raw)
        if len(rows)!=1:raise ValueError('one_native_record_required')
    except Exception as exc:
        allowed={'frozen_log_range_unavailable','frozen_log_range_partial','one_native_record_required',
            'fixture_schema_rejected','fixture_log_ambiguous','fixture_log_bound_rejected'}
        reason=str(exc) if str(exc) in allowed else 'offline_audit_failed_details_redacted'
    write(OUTPUT,dict(ledger_sha256=sha(LEDGER),audit_passed=reason is None,content_reads=reads,read_bytes=count,
        range_sha256=digest,records=rows,stop_reason=reason,original_runtime_completed=False,
        original_permissions_consumed=1,sdk_connections=0,new_permissions=0,quote_reads=0,
        orders_available=False,fresh_performance_eligible=False,annual_eligible=False))
    print(json.dumps(dict(audit_passed=reason is None,records=rows,stop_reason=reason)))

if __name__=='__main__':run()
