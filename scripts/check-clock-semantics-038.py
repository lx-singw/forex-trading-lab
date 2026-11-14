"""Independently decode originals and verify research/compile evidence and gates."""
from collections import Counter
import csv
from datetime import datetime
import json
import math
from pathlib import Path
import re
import runpy
import struct

ROOT=Path(__file__).resolve().parents[1]
API=runpy.run_path(str(ROOT/'scripts/clock-semantics-038.py'))
sha,write,sealed=API['sha'],API['write'],API['sealed']


def decode(folder,meta):
    blob=(ROOT/folder/'ticks.bin').read_bytes()
    assert sha(ROOT/folder/'ticks.bin')==meta['binary_sha256']==meta['response_sha256']
    assert sha(ROOT/folder/'ticks.csv')==meta['csv_sha256']
    assert len(blob)==meta['response_bytes']==60*meta['returned_rows']
    offsets=(0,8,16,24,32,40,48,52);sizes=(8,8,8,8,8,8,4,8)
    fields=('time','bid','ask','last','volume','time_msc','flags','volume_real')
    formats=('<i8','<f8','<f8','<f8','<u8','<i8','<u4','<f8')
    assert meta['binary_layout']==dict(itemsize=60,padding_offsets=[],fields={
        name:dict(format=fmt,offset=offset,size=size) for name,fmt,offset,size in zip(fields,formats,offsets,sizes)})
    with (ROOT/folder/'ticks.csv').open(newline='') as file:
        reader=csv.DictReader(file);assert tuple(reader.fieldnames)==fields;csv_rows=list(reader)
    assert len(csv_rows)==meta['returned_rows']
    seconds=[];milliseconds=[];histogram=Counter();mismatches=[];checked=0
    for i,raw in enumerate(csv_rows):
        values={}
        for name,offset,size,fmt in zip(fields,offsets,sizes,formats):
            part=blob[i*60+offset:i*60+offset+size]
            value=struct.unpack('<d',part)[0] if fmt=='<f8' else int.from_bytes(part,'little',signed=fmt=='<i8')
            csv_value=float(raw[name]) if fmt=='<f8' else int(raw[name])
            assert value==csv_value or fmt=='<f8' and math.isnan(value) and math.isnan(csv_value)
            values[name]=value;checked+=1
        second,ms=values['time'],values['time_msc'];assert second>0 and ms>0
        residual=ms-second*1000;histogram[str(residual)]+=1
        if second!=ms//1000:mismatches.append(dict(original_row_index=i,time_s=second,time_msc=ms,residual_ms=residual))
        seconds.append(second);milliseconds.append(ms)
    result=dict(rows=len(seconds),clock_fields_decoded=2*len(seconds),seconds_min=min(seconds),seconds_max=max(seconds),
        milliseconds_min=min(milliseconds),milliseconds_max=max(milliseconds),residual_histogram=dict(histogram),
        floor_relation_mismatches=mismatches,all_seconds_equal_floor_milliseconds=not mismatches,
        seconds_reversals=[i for i in range(1,len(seconds)) if seconds[i]<seconds[i-1]],
        milliseconds_reversals=[i for i in range(1,len(milliseconds)) if milliseconds[i]<milliseconds[i-1]])
    return result,checked


def intervals(rows):
    result=[]
    for i,row in enumerate(rows):
        b,a,raw=(row[k] for k in ('received_before_utc_ms','received_after_utc_ms','raw_time_msc'))
        assert type(b) is type(a) is type(raw) is int and 0<b<=a and raw>0
        result.append(dict(original_row_index=i,lower_ms=raw-a,upper_ms=raw-b))
    low=min(v['lower_ms'] for v in result);high=max(v['upper_ms'] for v in result)
    return dict(observations=len(rows),intervals=result,envelope_ms=[low,high],
        distance_from_hypothetical_three_hours_ms=[low-10800000,high-10800000],offset_correction_authorized=False)


def check():
    ledger=API['verify']();audit=sealed(API['OUTPUT']);research=sealed(API['RESEARCH']);compile=sealed(API['COMPILE'])
    tests=sealed(ROOT/'reports/clock-semantics-038-tests.json')
    assert tests['passed'] and tests['tests_run']==tests['tests_passed']==546 and tests['new_tests']==24
    assert tests['shared_guard_checks']==73
    assert audit['ledger_sha256']==compile['ledger_sha256']==sha(API['LEDGER'])
    assert audit['research_sha256']==sha(API['RESEARCH'])
    declaration=json.loads(API['DECLARATION'].read_text());targets=declaration['targets']
    assert declaration['budgets']==dict(search=0,open=8,find=6) and len(set(targets))==len(targets)==8
    actions=research['actions'];counts=Counter();opened=set();retrieved=set();found=set()
    assert set(research)=={'version','actions','findings','market_requests','orders_available'}
    for i,action in enumerate(actions):
        assert action['index']==i and action['kind'] in ('open','find') and action['url'] in targets
        stamp=datetime.fromisoformat(action['retrieved_utc']);assert stamp.utcoffset().total_seconds()==0
        counts[action['kind']]+=1
        if action['kind']=='open':
            assert set(action)=={'index','kind','url','status','retrieved_utc'}
            assert action['url'] not in opened and action['status'] in ('retrieved','unavailable')
            opened.add(action['url'])
            if action['status']=='retrieved':retrieved.add(action['url'])
        else:
            assert set(action)=={'index','kind','url','pattern','matched','retrieved_utc'}
            pair=action['url'],action['pattern'];assert action['url'] in retrieved and pair not in found
            assert action['pattern'] in declaration['find_patterns'] and type(action['matched']) is bool
            found.add(pair)
    assert counts['open']<=8 and counts['find']<=6 and counts['search']==0
    ids=set()
    for finding in research['findings']:
        assert set(finding)=={'id','url','summary','limitation'} and finding['id'] not in ids and finding['url'] in retrieved
        assert all(isinstance(finding[k],str) and finding[k] for k in ('id','summary','limitation'))
        ids.add(finding['id'])
    reconstructed=dict(search=0,open=counts['open'],find=counts['find'],findings=len(ids))
    assert reconstructed==audit['action_counts']
    fields=0;rows=0;clock_fields=0
    for observed in audit['native_fields']:
        stage=observed['stage'];folder=observed['original_folder']
        assert (stage,folder) in ((33,'data/fresh-context-033'),(35,'data/fresh-replication-035'))
        original=sealed(ROOT/folder/'capture.json');derived,count=decode(folder,original['reads'][1])
        for key,value in derived.items():assert observed[key]==value,key
        assert observed['binary_sha256']==sha(ROOT/folder/'ticks.bin')
        fields+=count;rows+=derived['rows'];clock_fields+=derived['clock_fields_decoded']
    assert [v['stage'] for v in audit['native_fields']]==[33,35]
    assert fields==audit['native_csv_fields_verified'] and rows==audit['saved_tick_rows'] and clock_fields==audit['clock_fields_decoded']
    old=sealed(ROOT/'reports/fresh-data-031-probe.json');current=sealed(ROOT/'reports/clock-reference-037-capture.json')
    for stage,observations,observed in ((31,old['observations'],audit['receipt_comparisons'][0]),(37,[current['quote']],audit['receipt_comparisons'][1])):
        assert observed['stage']==stage
        for key,value in intervals(observations).items():assert observed[key]==value,key
    assert audit['prior_public_reference_comparison']==current['comparison']
    assert compile['source_sha256']==sha(ROOT/API['MQL']) and compile['header_sha256']==sha(ROOT/API['HEADER'])
    reserve=ROOT/'reports/clock-semantics-038-compile-reservation.json'
    assert compile['reservation_sha256']==sha(reserve) and sealed(reserve)['ledger_sha256']==sha(API['LEDGER'])
    assert 0<=compile['compilation_attempts']<=1 and compile['compiler_available']==ledger['compiler_available']
    outputs=compile['output_bindings']
    for name,h in outputs.items():
        assert '/ForexDemoLab/builds/clock038-' in name and sha(API['bound_path'](name))==h,name
    if compile['compiled']:
        assert compile['outcome']=='compiled' and compile['errors']==compile['warnings']==0 and compile['process_completed'] is True
        by_file={Path(n).name:n for n in outputs}
        assert set(by_file)=={'ForexDemoClockObserver038.mq5','ClockGuard038.mqh','compile.log','ForexDemoClockObserver038.ex5'}
        assert outputs[by_file['ForexDemoClockObserver038.mq5']]==sha(ROOT/API['MQL'])
        assert outputs[by_file['ClockGuard038.mqh']]==sha(ROOT/API['HEADER'])
        log=API['bound_path'](by_file['compile.log']).read_text(encoding='utf-16')
        matches=re.findall(r'(\d+) errors, (\d+) warnings',log);assert matches and matches[-1]==('0','0')
        assert API['bound_path'](by_file['ForexDemoClockObserver038.ex5']).stat().st_size>0
    else:assert compile['outcome'] in ('compile_failed','compiler_timeout','compiler_unavailable','compiler_driver_failure_details_redacted')
    assert compile['observer_attached'] is compile['observer_runtime_executed'] is False
    for report in (audit,research,compile):assert report['market_requests']==0 and report['orders_available'] is False
    assert audit['native_connections']==compile['native_connections']==audit['historical_downloads']==audit['strategy_replays']==0
    for key in ('raw_labels_normalized','unknown_bits_interpreted','source_clock_sessions_qualified',
                'upstream_completeness_qualified','historical_executable_costs_qualified','fresh_performance_eligible','annual_eligible','observer_runtime_executed'):
        assert audit[key] is False
    for name in ('reports/fresh-context-033-checks.json','reports/fresh-replication-035-checks.json'):
        assert sealed(ROOT/name)['diagnostic_passed'] is False
    write(ROOT/'reports/clock-semantics-038-checks.json',dict(checker_passed=True,ledger_sha256=sha(API['LEDGER']),
        audit_sha256=sha(API['OUTPUT']),research_sha256=sha(API['RESEARCH']),compile_sha256=sha(API['COMPILE']),
        input_bindings_verified=len(ledger['bindings']),software_tests_passed=546,new_tests=24,shared_guard_checks=73,
        native_csv_fields_verified=fields,saved_tick_rows=rows,clock_fields_decoded=clock_fields,
        native_clock_results=audit['native_fields'],receipt_comparisons=audit['receipt_comparisons'],action_counts=reconstructed,
        observer_compiled=compile['compiled'],compile_output_bindings=outputs,observer_attached=False,observer_runtime_executed=False,
        market_requests=0,native_connections=0,historical_downloads=0,strategy_replays=0,orders_available=False,
        raw_labels_normalized=False,source_clock_sessions_qualified=False,upstream_completeness_qualified=False,
        historical_executable_costs_qualified=False,prior_033_diagnostic_passed=False,prior_035_diagnostic_passed=False,
        fresh_performance_eligible=False,annual_eligible=False))
    print(json.dumps(dict(checker_passed=True,saved_tick_rows=rows,fields_verified=fields,clock_fields_decoded=clock_fields,
                         observer_compiled=compile['compiled'],action_counts=reconstructed,market_requests=0)))


if __name__=='__main__':check()
