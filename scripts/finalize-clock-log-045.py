"""Offline independent audit checks and exclusive final evidence snapshot."""
import hashlib
import json
from pathlib import Path
import runpy
import zipfile
ROOT=Path(__file__).resolve().parents[1]
API=runpy.run_path(str(ROOT/'scripts/clock-session-044.py'))
sha,write,sealed=API['sha'],API['write'],API['sealed']

def run():
    API['verify']()
    prior_path=ROOT/'reports/clock-session-044-completion-final-source.json'
    prior=sealed(prior_path)
    audit_path=ROOT/'reports/clock-log-audit-045.json';audit=sealed(audit_path)
    reservation=ROOT/'reports/clock-log-audit-045-reservation.json';frozen=sealed(reservation)
    assert audit['reservation_sha256']==sha(reservation)
    assert audit['input_bindings']==frozen['input_bindings']
    for n,h in audit['input_bindings'].items():assert sha(ROOT/n)==h
    assert audit['original_anchor']==sealed(ROOT/'reports/clock-observer-044-enabled-started.json')['anchor']
    assert audit['log_reads']==1 and audit['read_bytes']==6626 and audit['stop_reason'] is None
    assert len(audit['region_sha256'])==64
    rows=audit['records'];assert audit['record_count']==len(rows)==6
    base={'version','accepted','reason_code','quote_reads','guard_checks','bid','ask','tick_flags','elapsed_us','tick_time_s','tick_time_msc'}
    fields={source+'_'+suffix+'_s' for source in ('time_current','calculated_server','gmt','local') for suffix in ('before','after')}
    for r in rows:
        assert set(r)==base|fields
        assert r['version']=='clock_observer_042_v1' and r['accepted'] is True
        assert r['reason_code']==0 and r['quote_reads']==1 and r['guard_checks']==5
        assert r['tick_time_s']==r['tick_time_msc']//1000 and 0<r['bid']<=r['ask']
        assert 0<=r['elapsed_us']<=15000000
    count=sum(r['quote_reads'] for r in rows)
    assert count==audit['recorded_native_quote_reads']==6
    assert audit['extra_records_detected'] is True and audit['exactly_one_accepted_record'] is False
    assert audit['relative_clock_diagnostic'] is None and audit['arithmetic_checks_passed'] is False
    for n in ('sdk_connections','new_quote_reads','script_invocations','http_requests','historical_reads'):assert audit[n]==0
    for n in ('orders_available','fresh_performance_eligible','annual_eligible','historical_clock_certified',
              'offset_correction_authorized','original_044_session_completed','companion_completion_guard_available'):assert audit[n] is False
    assert audit['post_expiry_audit'] is True
    runtime=sealed(ROOT/'reports/clock-observer-044-runtime.json')
    assert runtime['quote_reads']==0 and runtime['completed'] is False and runtime['stop_reason']=='runtime_session_deadline_exceeded'
    checks=ROOT/'reports/clock-log-audit-045-checks.json'
    write(checks,dict(checker_passed=True,evidence_integrity_passed=True,audit_sha256=sha(audit_path),
        recorded_native_quote_reads=count,maximum_declared_native_quote_reads=1,acquisition_budget_compliant=False,
        original_044_collected_quote_reads=0,original_044_runtime_completed=False,
        audit_new_quote_reads=0,orders_available=False,fresh_performance_eligible=False,annual_eligible=False))
    groups={g:dict(v) for g,v in prior.items() if g.endswith('_bindings') and g!='archive_external_bindings'}
    for values in groups.values():
        for n,h in values.items():assert sha(API['bound_path'](n))==h,n
    text=('Latest — 2026-10-06: offline clock audit045 sealed; read CLOCK-LOG-AUDIT-045-RESULTS.md. '
        'Capture=true worked: six accepted native records/six quote reads exceed044 maximum one; acquisition budget compliance false. '
        'Original044 timeout/incomplete and zero companion-collected count preserved, not total native reads. '
        'One bounded existing-log read, no new SDK/quote/script/HTTP/history/strategy/order calls. '
        'No relative comparison selected or historical correction/qualification. 622 pre-runtime software tests remain; '
        'all six sanitized records and audit independently checked/sealed. Defaults may reappear on new script launch. '
        'Do not rerun042. Next CLOCK-UI-SAFETY-046-PLAN.md design/tests native cross-invocation budget before any new runtime. '
        'Clock/coverage/cost/flags/033/035 failures and consumed2025/reservedNov–Dec2026/provider stops unchanged; '
        'fresh/annual eligibility and orders false. Earlier entries are historical.\n\n')
    for n in API['HANDOFF']:
        p=ROOT/n;old=p.read_text();i=old.index('\n')+1;p.write_text(old[:i]+'\n'+text+old[i:]);groups['source_bindings'][n]=sha(p)
    for pattern in ('docs/*045*.md','docs/CLOCK-UI-SAFETY-046-PLAN.md','scripts/*045.py'):
        for p in ROOT.glob(pattern):groups['source_bindings'][p.relative_to(ROOT).as_posix()]=sha(p)
    for pattern in ('reports/clock-log-audit-045*.json','reports/clock-log-audit-045*.sha256'):
        for p in ROOT.glob(pattern):groups['report_bindings'][p.relative_to(ROOT).as_posix()]=sha(p)
    for suffix in ('.json','.sha256','.zip'):
        p=prior_path.with_suffix(suffix);groups['report_bindings'][p.relative_to(ROOT).as_posix()]=sha(p)
    bindings={n:h for v in groups.values() for n,h in v.items()}
    assert len(bindings)==sum(map(len,groups.values()))
    external={n:h for n,h in bindings.items() if n.startswith('/') or n.endswith('.zip') or
        n.startswith('data/') and n.endswith('.gz') and 'synthetic' not in n and 'walk-forward' not in n}
    internal={n:h for n,h in bindings.items() if n not in external}
    for n,h in bindings.items():assert sha(API['bound_path'](n))==h,n
    final=ROOT/'reports/clock-log-audit-045-final-source.json';archive=final.with_suffix('.zip')
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED) as z:
        for n in sorted(internal):z.write(ROOT/n,n)
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None and set(z.namelist())==set(internal)
        for n,h in internal.items():assert hashlib.sha256(z.read(n)).hexdigest()==h
    write(final,dict(**groups,archive_external_bindings=external,archive_sha256=sha(archive),
        archive_members_verified=len(internal),external_bindings_verified=len(external),
        evidence_integrity_passed=True,acquisition_budget_compliant=False,recorded_native_quote_reads=count,
        original_044_runtime_completed=False,orders_available=False,fresh_performance_eligible=False,annual_eligible=False,
        next_plan='docs/CLOCK-UI-SAFETY-046-PLAN.md',next_plan_executed=False))
    assert sealed(final)['archive_sha256']==sha(archive)
    print(json.dumps(dict(bindings=len(bindings),members=len(internal),external=len(external),sha256=sha(final),
        integrity_passed=True,acquisition_budget_compliant=False,recorded_native_quote_reads=count)))

if __name__=='__main__':run()
