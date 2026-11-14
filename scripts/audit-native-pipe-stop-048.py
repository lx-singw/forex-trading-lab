"""One frozen post-stop existing-log audit. No SDK, prices or native execution."""
import json
from pathlib import Path
import re
import runpy
ROOT=Path(__file__).resolve().parents[1]
API=runpy.run_path(str(ROOT/'scripts/native-pipe-048.py'))
OFFLINE=runpy.run_path(str(ROOT/'scripts/offline-native-pipe-stop-048.py'))
RUNTIME=ROOT/'reports/native-pipe-048-runtime.json'
START=ROOT/'reports/native-pipe-048-disabled-started.json'
DEPLOY=ROOT/'reports/native-pipe-048-deployment.json'
RESERVATION=ROOT/'reports/native-pipe-048-stop-audit-reservation.json'
OUTPUT=ROOT/'reports/native-pipe-048-disabled-stop-records.json'

def run():
    OFFLINE['verify_offline']();sha,sealed,write=API['sha'],API['sealed'],API['write']
    r=sealed(RUNTIME);arm=sealed(START);d=sealed(DEPLOY)
    assert not r['completed'] and r['stop_reason']=='disconnected' and r['sdk_shutdown_called']
    assert r['script_arms']==['disabled'] and r['records']==[] and r['permissions_consumed']==0
    assert r['anchors']==[arm['anchor']] and r['deployment']['artifact_binding']==d['artifact_binding']
    assert re.fullmatch('ForexDemoLab048-[0-9a-f]{32}',d['folder'])
    name=next(iter(d['artifact_binding']));assert len(d['artifact_binding'])==1
    assert name.endswith('/MQL5/Scripts/'+d['folder']+'/ForexDemoPipeFixture047.ex5')
    assert sha(API['bound'](name))==d['compiled_artifact_sha256']==d['artifact_binding'][name]
    log=API['bound'](name).parents[2]/'Logs'/'20261007.log'
    offset=arm['anchor']['offset_bytes'];assert type(offset) is int and offset>=0 and offset%2==0
    sources=('scripts/audit-native-pipe-stop-048.py','docs/NATIVE-PIPE-048-STOP-AUDIT.md',
        'src/forex_demo_lab/native_pipe_048.py','scripts/check-native-pipe-stop-048.py',
        'scripts/offline-native-pipe-stop-048.py','scripts/seal-native-pipe-stop-048.py',
        'docs/NATIVE-PIPE-049-PLAN.md')
    originals=(RUNTIME,START,DEPLOY,API['LEDGER'],ROOT/'reports/native-pipe-048-stop-audit-preflight.json',
        ROOT/'reports/native-pipe-048-installed-change.json',ROOT/'reports/native-pipe-048-stop-audit-r1-source.zip',
        ROOT/'reports/native-pipe-048-checks.json')
    bindings={n:sha(ROOT/n) for n in sources}
    bindings.update({p.relative_to(ROOT).as_posix():sha(p) for p in originals})
    write(RESERVATION,dict(bindings=bindings,anchor=arm['anchor'],maximum_log_reads=1,maximum_read_bytes=1048576,
        sdk_connections=0,quote_reads=0,orders_available=False,reservation_consumed=True))
    rows=[];read_bytes=0;reason=None;log_reads=0;proof=False
    try:
        for n,h in bindings.items():assert sha(ROOT/n)==h
        if not log.exists():raise ValueError('native_log_missing')
        size=log.stat().st_size
        if size<offset or size-offset>1048576:raise ValueError('native_log_truncated_or_budget_exceeded')
        from forex_demo_lab.native_pipe_048 import records_from_log
        log_reads=1
        with log.open('rb') as f:f.seek(offset);raw=f.read(1048577)
        read_bytes=len(raw);rows=records_from_log(raw)
        expected=dict(version='pipe_fixture_047_v1',reason_code=17,requests=0,receipt_valid=False,quote_reads=0,orders=0)
        proof=rows==[expected]
        if not proof:reason='disabled_proof_missing_extra_or_unexpected'
    except Exception as exc:
        safe={'native_log_missing','native_log_truncated_or_budget_exceeded','fixture_schema_rejected',
            'fixture_log_bound_rejected','fixture_log_ambiguous'}
        reason=str(exc) if str(exc) in safe else 'stop_log_audit_failed_details_redacted'
    write(OUTPUT,dict(disabled_proof_passed=proof,records=rows,read_bytes=read_bytes,log_reads=log_reads,
        stop_reason=reason,anchor=arm['anchor'],reservation_sha256=sha(RESERVATION),runtime_sha256=sha(RUNTIME),
        original_runtime_completed=False,original_runtime_collected_records=0,
        sdk_connections=0,quote_reads=0,orders_available=False,fresh_performance_eligible=False,annual_eligible=False))
    print(json.dumps(dict(disabled_proof_passed=proof,records=len(rows),stop_reason=reason)))

if __name__=='__main__':run()
