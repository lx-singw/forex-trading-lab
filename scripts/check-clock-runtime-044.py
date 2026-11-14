"""Independent runtime schemas, original records, deployment, budgets and clocks."""
import json
from pathlib import Path
import re
import runpy
ROOT=Path(__file__).resolve().parents[1];API=runpy.run_path(str(ROOT/'scripts/clock-session-044.py'))
sha,write,sealed=API['sha'],API['write'],API['sealed']

def check():
    ledger=API['verify']();build=sealed(API['OUTPUT']);compile_checks=sealed(ROOT/'reports/native-compiler-042-checks.json')
    runtime=sealed(ROOT/'reports/clock-observer-044-runtime.json');reservation=sealed(ROOT/'reports/clock-observer-044-runtime-reservation.json')
    assert compile_checks['checker_passed'] and compile_checks['observer_compiled']==build['compiled']
    assert runtime['ledger_sha256']==reservation['ledger_sha256']==sha(API['LEDGER'])
    assert runtime['build_sha256']==reservation['build_sha256']==sha(API['OUTPUT'])
    assert runtime['reservation_sha256']==sha(ROOT/'reports/clock-observer-044-runtime-reservation.json')
    assert runtime['declared_date']=='2026-10-06' and runtime['version']=='clock_observer_042_v1'
    assert runtime['native_connections_attempted'] in (0,1) and runtime['sdk_quote_reads']==0
    assert runtime['script_arms'] in ([],[False],[False,True])
    assert len(runtime['records'])<=len(runtime['script_arms'])<=2
    observed=sum(r['quote_reads'] for r in runtime['records'])
    assert runtime['quote_reads']==observed<=1
    assert runtime['completed'] is False or runtime['stop_reason'] is None
    for flag in ('orders_available','fresh_performance_eligible','annual_eligible','local_clock_certified','historical_clock_certified'):
        assert runtime[flag] is False
    for count in ('http_requests','historical_reads','strategy_replays'):assert runtime[count]==0
    expected_failure=dict(version='clock_observer_042_v1',accepted=False,reason_code=17,quote_reads=0)
    evidence={};original=[]
    for enabled in (False,True):
        stem='enabled' if enabled else 'disabled';p=ROOT/('reports/clock-observer-044-'+stem+'-records.json')
        if p.exists():
            result=sealed(p);evidence[p.relative_to(ROOT).as_posix()]=sha(p)
            assert result['ledger_sha256']==sha(API['LEDGER']) and result['anchor']['enabled'] is enabled
            assert result['read_bytes']<=1048576
            original.extend(result['records'])
    assert runtime['records']==original
    deployed={}
    if runtime['deployment'] is not None:
        deployment=sealed(ROOT/'reports/clock-observer-044-deployment.json');d=runtime['deployment']
        assert deployment['ledger_sha256']==sha(API['LEDGER']) and deployment['actual_demo_usd_algo_off_verified']
        assert d['folder']==deployment['folder'] and re.fullmatch('ForexDemoLab042-[0-9a-f]{32}',d['folder'])
        assert d['artifact_binding']==deployment['artifact_binding'] and len(d['artifact_binding'])==1
        for n,h in d['artifact_binding'].items():
            assert n.endswith('/MQL5/Scripts/'+d['folder']+'/ForexDemoClockObserver042.ex5')
            assert sha(API['bound_path'](n))==h==deployment['compiled_artifact_sha256']
            assert h in build['compile_output_bindings'].values();deployed[n]=h
    comparison=None
    if runtime['completed']:
        assert runtime['native_connections_attempted']==1 and runtime['script_arms']==[False,True]
        assert len(original)==2 and original[0]==expected_failure and original[1]['accepted'] is True
        assert runtime['guard_checks']>=8 and len(runtime['anchors'])==len(runtime['collection_receipts_utc_ms'])==2
        r=original[1]
        base={'version','accepted','reason_code','quote_reads'}
        integer={'guard_checks','time_current_before_s','time_current_after_s','calculated_server_before_s','calculated_server_after_s',
            'gmt_before_s','gmt_after_s','local_before_s','local_after_s','tick_time_s','tick_time_msc','tick_flags','elapsed_us'}
        assert set(r)==base|integer|{'bid','ask'}
        assert r['version']=='clock_observer_042_v1' and r['reason_code']==0 and r['quote_reads']==1 and r['guard_checks']==5
        assert all(type(r[k]) is int for k in integer) and r['tick_time_s']==r['tick_time_msc']//1000
        assert 0<r['bid']<=r['ask'] and 0<=r['elapsed_us']<=15000000
        g0=r['gmt_before_s']*1000;g1=r['gmt_after_s']*1000+999
        def interval(prefix):return [r[prefix+'_before_s']*1000-g1,r[prefix+'_after_s']*1000+999-g0]
        comparison=dict(raw_tick_minus_gmt_interval_ms=[r['tick_time_msc']-g1,r['tick_time_msc']-g0],
            time_current_minus_gmt_interval_ms=interval('time_current'),calculated_server_minus_gmt_interval_ms=interval('calculated_server'),
            local_minus_gmt_interval_ms=interval('local'),seconds_equal_floor_milliseconds=True,elapsed_us=r['elapsed_us'],
            historical_clock_certified=False,offset_correction_authorized=False)
        assert runtime['comparison']==comparison
    else:assert runtime['comparison'] is None
    for n in ('reports/fresh-context-033-checks.json','reports/fresh-replication-035-checks.json'):
        assert sealed(ROOT/n)['diagnostic_passed'] is False
    write(ROOT/'reports/clock-observer-044-runtime-checks.json',dict(checker_passed=True,
        runtime_sha256=sha(ROOT/'reports/clock-observer-044-runtime.json'),ledger_sha256=sha(API['LEDGER']),
        completed=runtime['completed'],quote_reads_observed=observed,sdk_quote_reads=0,
        disabled_default_proven=bool(original and original[0]==expected_failure),comparison=comparison,
        original_record_bindings=evidence,deployment_bindings=deployed,orders_available=False,
        fresh_performance_eligible=False,annual_eligible=False,historical_clock_certified=False,
        prior_033_diagnostic_passed=False,prior_035_diagnostic_passed=False))
    print(json.dumps(dict(checker_passed=True,completed=runtime['completed'],quote_reads_observed=observed,comparison=comparison)))

if __name__=='__main__':check()
