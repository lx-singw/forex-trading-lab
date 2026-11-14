"""One frozen existing-log range. No SDK, native run or new market data."""
import hashlib
import json
from pathlib import Path
import re
import runpy
import zipfile
ROOT=Path(__file__).resolve().parents[1];API=runpy.run_path(str(ROOT/'scripts/native-pipe-049.py'))
sha,sealed,write,bound=API['sha'],API['sealed'],API['write'],API['bound']
PRIOR=ROOT/'reports/native-pipe-049-final-source.json'
LEDGER=ROOT/'reports/native-log-050-ledger.json';OUTPUT=ROOT/'reports/native-log-050-audit.json'
PATTERNS=('scripts/*050.py','docs/*050*.md')

def prior_verify():
    assert sha(PRIOR)=='f81a2d1d280f6b054d4525d182a9df956df1a564bbe7bbca932f1291c065a0ee'
    p=sealed(PRIOR);bindings=p['source_and_evidence_bindings'];assert len(bindings)==1554
    for n,h in bindings.items():assert sha(bound(n))==h,n
    assert not p['runtime_completed'] and not p['native_mt5_transport_verified']
    assert sha(PRIOR.with_suffix('.zip'))==p['archive_sha256']
    internal=set(bindings)-set(p['archive_external_bindings'])
    with zipfile.ZipFile(PRIOR.with_suffix('.zip')) as z:
        assert z.testzip() is None and len(z.infolist())==1458 and set(z.namelist())==internal
        for n in internal:assert hashlib.sha256(z.read(n)).hexdigest()==bindings[n]
    return p

def run():
    prior=prior_verify();r=sealed(ROOT/'reports/native-pipe-049-runtime.json')
    collected=sealed(ROOT/'reports/native-pipe-049-disabled-records.json')
    assert r['stop_reason']=='exactly_one_fixture_record_required' and r['records']==[] and r['permissions_consumed']==0
    assert r['sdk_shutdown_called'] and collected['records']==[] and collected['read_bytes']==0
    assert collected['anchor']['offset_bytes']==364 and r['script_arms']==['disabled']
    d=sealed(ROOT/'reports/native-pipe-049-deployment.json');assert len(d['artifact_binding'])==1
    name=next(iter(d['artifact_binding']));assert re.fullmatch('ForexDemoLab049-[0-9a-f]{32}',d['folder'])
    assert name.endswith('/MQL5/Scripts/'+d['folder']+'/ForexDemoPipeFixture049.ex5')
    log=bound(name).parents[2]/'Logs'/'20261007.log'
    inputs={n:h for n,h in prior['source_and_evidence_bindings'].items() if n not in API['HANDOFF']}
    for suffix in ('.json','.sha256','.zip'):
        p=PRIOR.with_suffix(suffix);inputs[p.relative_to(ROOT).as_posix()]=sha(p)
    for pattern in PATTERNS:
        for p in ROOT.glob(pattern):inputs[p.relative_to(ROOT).as_posix()]=sha(p)
    write(LEDGER,dict(bindings=inputs,start_byte=364,end_byte=726,maximum_content_reads=1,
        prior_bindings_verified=1554,prior_archive_members_verified=1458,original_runtime_collected_records=0,
        observed_later_file_bytes=726,observed_later_last_write_utc='2026-10-07T06:32:20.2458262Z',
        user_confirmed_exact_script_launch=True,research_search_queries=2,primary_reference_urls=[
            'https://www.metatrader5.com/en/terminal/help/start_advanced/journal',
            'https://www.mql5.com/en/book/common/output/output_print'],sdk_connections=0,quote_reads=0,orders_available=False))
    rows=[];size=0;digest=None;reason=None;reads=0;proof=False
    try:
        for n,h in inputs.items():assert sha(bound(n))==h,n
        if log.stat().st_size<726:raise ValueError('frozen_log_range_unavailable')
        reads=1
        with log.open('rb') as f:f.seek(364);raw=f.read(362)
        size=len(raw);digest=hashlib.sha256(raw).hexdigest()
        if size!=362:raise ValueError('frozen_log_range_partial')
        from forex_demo_lab.native_pipe_049 import records_from_log
        rows=records_from_log(raw)
        expected=dict(version='pipe_fixture_049_v1',reason_code=17,requests=0,receipt_valid=False,quote_reads=0,orders=0)
        proof=rows==[expected]
        if not proof:reason='disabled_log_proof_missing_extra_or_unexpected'
    except Exception as exc:
        safe={'frozen_log_range_unavailable','frozen_log_range_partial','fixture_schema_rejected','fixture_log_ambiguous','fixture_log_bound_rejected'}
        reason=str(exc) if str(exc) in safe else 'offline_log_audit_failed_details_redacted'
    write(OUTPUT,dict(ledger_sha256=sha(LEDGER),original_runtime_sha256=sha(ROOT/'reports/native-pipe-049-runtime.json'),
        disabled_proof_passed=proof,records=rows,read_bytes=size,range_sha256=digest,content_reads=reads,stop_reason=reason,
        original_runtime_completed=False,original_runtime_collected_records=0,permissions_consumed=0,
        sdk_connections=0,quote_reads=0,orders_available=False,fresh_performance_eligible=False,annual_eligible=False))
    print(json.dumps(dict(disabled_proof_passed=proof,records=len(rows),stop_reason=reason)))

if __name__=='__main__':run()
