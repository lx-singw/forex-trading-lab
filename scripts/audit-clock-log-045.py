"""One offline append-region audit; no SDK or script execution."""
import hashlib
import json
from pathlib import Path
import runpy
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
API=runpy.run_path(str(ROOT/'scripts/clock-session-044.py'))
sha,write,sealed=API['sha'],API['write'],API['sealed']
from forex_demo_lab.clock_observer_042 import records_from_log,comparison

def run():
    API['verify']()
    prior_path=ROOT/'reports/clock-session-044-completion-final-source.json'
    prior=sealed(prior_path)
    assert prior['native_runtime_completed'] is False
    groups={g:v for g,v in prior.items() if g.endswith('_bindings') and g!='archive_external_bindings'}
    bindings={n:h for v in groups.values() for n,h in v.items()}
    for n,h in bindings.items():assert sha(API['bound_path'](n))==h,n
    archive=prior_path.with_suffix('.zip')
    assert sha(archive)==prior['archive_sha256']
    internal={n:h for n,h in bindings.items() if n not in prior['archive_external_bindings']}
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None and set(z.namelist())==set(internal)
        for n,h in internal.items():assert hashlib.sha256(z.read(n)).hexdigest()==h
    runtime=sealed(ROOT/'reports/clock-observer-044-runtime.json')
    anchor=sealed(ROOT/'reports/clock-observer-044-enabled-started.json')['anchor']
    assert runtime['stop_reason']=='runtime_session_deadline_exceeded'
    assert runtime['anchors'][-1]==anchor and anchor['enabled'] is True
    assert runtime['script_arms']==[False,True] and len(runtime['records'])==1
    names=['docs/CLOCK-LOG-AUDIT-045-PLAN.md','scripts/audit-clock-log-045.py',
        'src/forex_demo_lab/clock_observer_042.py','reports/clock-observer-044-runtime.json',
        'reports/clock-observer-044-enabled-started.json',prior_path.relative_to(ROOT).as_posix()]
    frozen={n:sha(ROOT/n) for n in names}
    reservation=ROOT/'reports/clock-log-audit-045-reservation.json'
    output=ROOT/'reports/clock-log-audit-045.json'
    assert not reservation.exists() and not output.exists()
    write(reservation,dict(input_bindings=frozen,prior_bindings_verified=len(bindings),
        prior_archive_members_verified=len(internal),maximum_log_reads=1,maximum_log_bytes=1048576,
        sdk_connections=0,new_quote_reads=0,script_invocations=0,orders_available=False))
    for n,h in frozen.items():assert sha(ROOT/n)==h
    name=next(iter(runtime['deployment']['artifact_binding']))
    assert name.count('/MQL5/Scripts/')==1
    log=API['bound_path'](name.split('/MQL5/Scripts/')[0]+'/MQL5/Logs/20261006.log')
    offset=anchor['offset_bytes']
    assert type(offset) is int and offset>=0 and offset%2==0
    rows=[];reason=None;raw=None;reads=0
    try:
        size=log.stat().st_size
        if size<offset or size-offset>1048576:raise ValueError('log_region_size_rejected')
        with log.open('rb') as f:
            reads=1;f.seek(offset);raw=f.read(1048577)
        rows=records_from_log(raw)
    except Exception:
        reason='bounded_log_read_or_schema_rejected'
    diag=comparison(rows[0]) if len(rows)==1 and rows[0]['accepted'] else None
    if diag is not None:
        r=rows[0];lo=r['gmt_before_s']*1000;hi=r['gmt_after_s']*1000+999
        assert diag['raw_tick_minus_gmt_interval_ms']==[r['tick_time_msc']-hi,r['tick_time_msc']-lo]
        for source in ('time_current','calculated_server','local'):
            assert diag[source+'_minus_gmt_interval_ms']==[r[source+'_before_s']*1000-hi,r[source+'_after_s']*1000+999-lo]
        assert r['tick_time_s']==r['tick_time_msc']//1000
    write(output,dict(reservation_sha256=sha(reservation),input_bindings=frozen,original_anchor=anchor,
        log_reads=reads,read_bytes=len(raw) if raw is not None else None,
        region_sha256=hashlib.sha256(raw).hexdigest() if raw is not None else None,
        records=rows,record_count=len(rows),stop_reason=reason,
        recorded_native_quote_reads=sum(r['quote_reads'] for r in rows),
        extra_records_detected=len(rows)>1,exactly_one_accepted_record=len(rows)==1 and rows[0]['accepted'],
        relative_clock_diagnostic=diag,arithmetic_checks_passed=diag is not None,
        original_044_session_completed=False,post_expiry_audit=True,companion_completion_guard_available=False,
        sdk_connections=0,new_quote_reads=0,script_invocations=0,http_requests=0,historical_reads=0,
        orders_available=False,fresh_performance_eligible=False,annual_eligible=False,
        historical_clock_certified=False,offset_correction_authorized=False))
    assert sealed(output)['reservation_sha256']==sha(reservation)
    print(json.dumps(dict(record_count=len(rows),records=rows,stop_reason=reason,relative_clock_diagnostic=diag)))

if __name__=='__main__':run()
