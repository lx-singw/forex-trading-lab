"""Separate frozen native054 error record; one existing range, no SDK or rerun."""
import hashlib
import json
from pathlib import Path
import runpy
import zipfile

ROOT=Path(__file__).resolve().parents[1]
API=runpy.run_path(str(ROOT/'scripts/native-pipe-054.py'))
sha,sealed,write,bound=API['sha'],API['sealed'],API['write'],API['bound']
PRIOR=ROOT/'reports/native-pipe-054-final-source.json'
LEDGER=ROOT/'reports/native-log-055-ledger.json'
OUTPUT=ROOT/'reports/native-log-055-audit.json'
PATTERNS=('scripts/*052.py','docs/*052*.md')

def prior_verify():
    assert sha(PRIOR)=='16282400c79901ded9bddd0c632382291564c4f070304fcd664d6d1a1cb3339f'
    p=sealed(PRIOR);bindings=p['source_and_evidence_bindings']
    assert len(bindings)==1748 and p['runtime_completed'] is False and p['native_mt5_transport_verified'] is False
    for n,h in bindings.items():assert sha(bound(n))==h,n
    assert sha(PRIOR.with_suffix('.zip'))==p['archive_sha256']
    internal=set(bindings)-set(p['archive_external_bindings'])
    with zipfile.ZipFile(PRIOR.with_suffix('.zip')) as z:
        assert z.testzip() is None and len(z.infolist())==1629 and set(z.namelist())==internal
        for n in internal:assert hashlib.sha256(z.read(n)).hexdigest()==bindings[n]
    return p

def original_failure():
    r=sealed(ROOT/'reports/native-pipe-054-runtime.json')
    s=sealed(ROOT/'reports/native-pipe-054-stopped-records.json')
    assert r['completed'] is False and r['stop_reason']=='native_transport_rejected'
    assert r['script_arms']==['disabled','enabled'] and r['permissions_consumed']==1
    assert len(r['records'])==1 and r['records'][0]['reason_code']==17
    assert r['sdk_shutdown_called'] and r['cancellation_drained']
    assert r['transport']==dict(peer_verified=True,request_valid=True,response_written=False,closed=True,error=True)
    assert s['records']==[] and s['read_bytes']==0 and s['anchor']['offset_bytes']==1520
    d=r['diagnostic_trace'][0]
    assert d['stop_reason']=='io_operation_rejected' and d['cleanup_reason'] is None
    assert d['events'][-3]['stage']=='reply_write' and d['events'][-3]['elapsed_us']==94
    assert d['events'][-3]['byte_count']==84 and d['closed'] and not d['pending_retained']
    return r

def run():
    prior=prior_verify();r=original_failure()
    name=next(iter(r['deployment']['artifact_binding']))
    log=bound(name).parents[2]/'Logs'/'20261007.log'
    inputs={n:h for n,h in prior['source_and_evidence_bindings'].items() if n not in API['HANDOFF']}
    for suffix in ('.json','.sha256','.zip'):
        p=PRIOR.with_suffix(suffix);inputs[p.relative_to(ROOT).as_posix()]=sha(p)
    for pattern in PATTERNS:
        for p in ROOT.glob(pattern):inputs[p.relative_to(ROOT).as_posix()]=sha(p)
    write(LEDGER,dict(bindings=inputs,start_byte=1520,end_byte=1950,maximum_content_reads=1,
        prior_bindings_verified=1748,prior_archive_members_verified=1629,
        observed_later_file_bytes=1950,observed_later_last_write_utc='2026-10-07T07:45:10.234384+00:00',
        original_runtime_completed=False,original_permissions_consumed=1,sdk_connections=0,quote_reads=0,orders_available=False))
    rows=[];size=0;digest=None;reason=None;reads=0
    try:
        for n,h in inputs.items():assert sha(bound(n))==h,n
        if log.stat().st_size<1950:raise ValueError('frozen_log_range_unavailable')
        reads=1
        with log.open('rb') as f:f.seek(1520);raw=f.read(430)
        size=len(raw);digest=hashlib.sha256(raw).hexdigest()
        if size!=430:raise ValueError('frozen_log_range_partial')
        from forex_demo_lab.native_pipe_054 import records_from_log
        rows=records_from_log(raw)
        if len(rows)!=1:raise ValueError('one_native_record_required')
    except Exception as exc:
        allowed={'frozen_log_range_unavailable','frozen_log_range_partial','one_native_record_required',
            'fixture_schema_rejected','fixture_log_ambiguous','fixture_log_bound_rejected'}
        reason=str(exc) if str(exc) in allowed else 'offline_log_audit_failed_details_redacted'
    write(OUTPUT,dict(ledger_sha256=sha(LEDGER),original_runtime_sha256=sha(ROOT/'reports/native-pipe-054-runtime.json'),
        audit_passed=reason is None,records=rows,read_bytes=size,range_sha256=digest,content_reads=reads,stop_reason=reason,
        original_runtime_completed=False,original_runtime_collected_records=1,original_permissions_consumed=1,
        sdk_connections=0,new_permissions=0,quote_reads=0,orders_available=False,fresh_performance_eligible=False,annual_eligible=False))
    print(json.dumps(dict(audit_passed=reason is None,records=rows,stop_reason=reason)))

if __name__=='__main__':run()
