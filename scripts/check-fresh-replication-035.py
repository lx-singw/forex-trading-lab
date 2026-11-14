"""Independent original decoding and fixed four-hour replication reconstruction."""
from collections import Counter, defaultdict
import csv
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import runpy
import struct

ROOT=Path(__file__).resolve().parents[1]
TICKS=('time','bid','ask','last','volume','time_msc','flags','volume_real')
BARS=('time','open','high','low','close','tick_volume','spread','real_volume')
TICK_INTS={'time','volume','time_msc','flags'}
BAR_INTS={'time','tick_volume','spread','real_volume'}
START,END=1791280800000,1791295200000
HOURS=tuple(range(START,END,3600000))


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def decode(folder,kind,info):
    fields,integers,limit=(TICKS,TICK_INTS,100000) if kind=='ticks' else (BARS,BAR_INTS,10)
    binary=(folder/(kind+'.bin')).read_bytes()
    assert sha(folder/(kind+'.bin'))==info['binary_sha256']==info['response_sha256']
    assert sha(folder/(kind+'.csv'))==info['csv_sha256']
    assert len(binary)==info['response_bytes']
    assert (folder/(kind+'.csv')).stat().st_size==info['csv_bytes']
    with (folder/(kind+'.csv')).open(newline='') as f:
        reader=csv.DictReader(f);assert tuple(reader.fieldnames)==fields
        rows=[{k:int(r[k]) if k in integers else float(r[k]) for k in fields} for r in reader]
    assert len(rows)==info['returned_rows']<=limit
    layout=info['binary_layout'];assert set(layout['fields'])==set(fields)
    size=layout['itemsize'];assert 0<size<=128 and len(binary)==size*len(rows)
    codes={('i',1):'b',('u',1):'B',('i',2):'h',('u',2):'H',('i',4):'i',('u',4):'I',
           ('i',8):'q',('u',8):'Q',('f',4):'f',('f',8):'d'}
    occupied=set()
    for name,part in layout['fields'].items():
        fmt=part['format'];assert fmt[0] in ('<','>','|') and int(fmt[2:])==part['size']
        assert fmt[1] in ('i','u') if name in integers else fmt[1]=='f'
        offset,length=part['offset'],part['size'];region=set(range(offset,offset+length))
        assert 0<=offset and offset+length<=size and not occupied&region
        occupied |= region
        unpack=('<' if fmt[0]=='|' else fmt[0])+codes[(fmt[1],length)]
        for i,r in enumerate(rows):
            v=struct.unpack_from(unpack,binary,i*size+offset)[0];w=r[name]
            assert v==w or name not in integers and math.isnan(v) and math.isnan(w),(kind,i,name)
    padding=set(range(size))-occupied;assert padding==set(layout['padding_offsets'])
    assert all(binary[i+o]==0 for i in range(0,len(binary),size) for o in padding)
    return rows


def tick_audit(rows):
    counts,indices=Counter(),[];same=duplicates=0;gaps=[]
    for i,r in enumerate(rows):
        failures=[]
        if not math.isfinite(r['bid']) or not math.isfinite(r['ask']) or r['bid']<=0 or r['ask']<r['bid']:
            failures.append('invalid_prices')
        if r['time_msc']<=0 or r['time']<0 or r['time_msc']//1000!=r['time']:failures.append('timestamp_mismatch')
        if r['time_msc']<START or r['time_msc']>END:failures.append('outside_request')
        if r['volume']<0 or not 0<=r['flags']<=4294967295 or any(not math.isfinite(r[k]) or r[k]<0 for k in ('last','volume_real')):
            failures.append('invalid_auxiliary_fields')
        if i:
            p=rows[i-1];delta=r['time_msc']-p['time_msc']
            if delta<0:failures.append('decreasing_labels')
            else:gaps.append(delta)
            same+=delta==0;duplicates+=all(r[k]==p[k] for k in TICKS)
        counts.update(failures)
        if failures and len(indices)<20:indices.append(dict(row_index=i,errors=failures))
    return dict(rows=len(rows),first_raw_time_msc=rows[0]['time_msc'] if rows else None,
        last_raw_time_msc=rows[-1]['time_msc'] if rows else None,same_millisecond_transitions=same,
        exact_duplicate_transitions=duplicates,maximum_nonnegative_intertick_gap_ms=max(gaps,default=None),
        error_counts=dict(counts),first_error_indices=indices)


def bars_audit(rows):
    errors=[]
    if len(rows)!=4:errors.append('expected_exactly_four_bars')
    if [r['time'] for r in rows]!=[h//1000 for h in HOURS]:errors.append('unexpected_bar_open_labels_or_order')
    for r in rows:
        prices=[r[k] for k in ('open','high','low','close')]
        if any(not math.isfinite(v) or v<=0 for v in prices) or r['low']>min(r['open'],r['close']) or max(r['open'],r['close'])>r['high']:
            errors.append('invalid_bar_prices')
        if min(r['tick_volume'],r['spread'],r['real_volume'])<0:errors.append('invalid_bar_auxiliary_fields')
    return dict(rows=len(rows),errors=errors)


def reconstruct(ticks,bars,sample):
    bidflags={i for i,t in enumerate(ticks) if t['flags']&2}
    askflags={i for i,t in enumerate(ticks) if t['flags']&4}
    bidchanges={i for i in range(1,len(ticks)) if ticks[i]['bid']!=ticks[i-1]['bid']}
    askchanges={i for i in range(1,len(ticks)) if ticks[i]['ask']!=ticks[i-1]['ask']}
    disagreements=[]
    for i in range(1,len(ticks)):
        fields=[]
        if (i in bidflags)!=(i in bidchanges):fields.append('bid')
        if (i in askflags)!=(i in askchanges):fields.append('ask')
        if fields:
            disagreements.append(dict(original_row_index=i,predecessor_original_row_index=i-1,
                raw_time_msc=ticks[i]['time_msc'],same_millisecond=ticks[i]['time_msc']==ticks[i-1]['time_msc'],
                mismatched_fields=fields,bid_flag=i in bidflags,ask_flag=i in askflags,
                bid_value_changed=i in bidchanges,ask_value_changed=i in askchanges,
                original_record=dict(ticks[i]),predecessor_record=dict(ticks[i-1])))
    hours=[]
    for start in HOURS:
        end=start+3600000;indices=[i for i,t in enumerate(ticks) if start<=t['time_msc']<end];selected=set(indices)
        definitions=[('all',selected),('bid_flag',bidflags&selected),('ask_flag',askflags&selected),
            ('both_flags',bidflags&askflags&selected),('neither_flag',selected-bidflags-askflags),
            ('bid_value_change_with_first',(bidchanges|{0})&selected),('ask_value_change_with_first',(askchanges|{0})&selected)]
        matches=[b for b in bars if b['time']==start//1000];recorded=matches[0] if len(matches)==1 else None
        comparisons=[]
        for name,selection in definitions:
            ordered=sorted(selection);prices=None
            if ordered:
                values=[ticks[i]['bid'] for i in ordered]
                prices=dict(open=values[0],high=max(values),low=min(values),close=values[-1])
            deltas=[]
            if prices is None or recorded is None:deltas=[dict(field='comparison_unavailable')]
            else:
                for key in ('open','high','low','close'):
                    if prices[key]!=recorded[key]:deltas.append(dict(field=key,reconstructed=prices[key],recorded=recorded[key],difference=prices[key]-recorded[key]))
            comparisons.append(dict(definition=name,original_row_indices=ordered,events=len(ordered),
                bid_ohlc=prices,bar_price_differences=deltas,recorded_tick_volume=recorded['tick_volume'] if recorded is not None else None,
                volume_difference=len(ordered)-recorded['tick_volume'] if recorded is not None else None))
        ds=[d for d in disagreements if d['original_row_index'] in selected]
        hours.append(dict(start_raw_ms=start,end_raw_ms=end,hour_event_rows=len(indices),
            first_original_row_index=indices[0] if indices else None,last_original_row_index=indices[-1] if indices else None,
            exact_open_boundary_row_indices=[i for i,t in enumerate(ticks) if t['time_msc']==start],
            exact_close_boundary_row_indices=[i for i,t in enumerate(ticks) if t['time_msc']==end],
            first_row_without_predecessor_indices=[0] if 0 in selected else [],
            flag_histogram=dict(sorted(Counter(ticks[i]['flags'] for i in indices).items())),
            known_mask_histogram=dict(sorted(Counter(ticks[i]['flags']&126 for i in indices).items())),
            remaining_mask_histogram=dict(sorted(Counter(ticks[i]['flags']&4294967169 for i in indices).items())),
            category_counts=dict(bid_flags=len(bidflags&selected),ask_flags=len(askflags&selected),
                both_flags=len(bidflags&askflags&selected),neither_flag=len(selected-bidflags-askflags)),
            bid_value_change_transitions=len(bidchanges&selected),ask_value_change_transitions=len(askchanges&selected),
            flag_value_disagreement_row_indices=[d['original_row_index'] for d in ds],
            bid_disagreement_rows=sum('bid' in d['mismatched_fields'] for d in ds),ask_disagreement_rows=sum('ask' in d['mismatched_fields'] for d in ds),
            fixed_definition_comparisons=comparisons,recorded_matching_bars=matches,
            relative_bid_price_count_hypothesis_passed=recorded is not None and bool(indices) and
                not comparisons[0]['bar_price_differences'] and comparisons[1]['volume_difference']==0))
    lookup={}
    for i,t in enumerate(ticks):lookup.setdefault(tuple(t[k] for k in TICKS),[]).append(i)
    witnesses=[]
    for i,t in enumerate(sample):
        matches=lookup.get(tuple(t[k] for k in TICKS),[])
        witnesses.append(dict(prior_original_row_index=i,matching_original_row_indices=matches,
                             status='matched' if len(matches)==1 else 'ambiguous' if matches else 'missing'))
    return dict(source_rows=len(ticks),hours=hours,flag_value_disagreements=disagreements,
        disagreement_rows=len(disagreements),same_millisecond_disagreement_rows=sum(d['same_millisecond'] for d in disagreements),
        witnesses=witnesses,witnesses_checked=len(sample),witnesses_matched=sum(w['status']=='matched' for w in witnesses),
        ambiguous_witnesses=sum(w['status']=='ambiguous' for w in witnesses),missing_witnesses=sum(w['status']=='missing' for w in witnesses),
        upper_boundary_row_indices=[i for i,t in enumerate(ticks) if t['time_msc']==END],
        outside_inclusive_request_row_indices=[i for i,t in enumerate(ticks) if not START<=t['time_msc']<=END],
        all_four_relative_hypotheses_passed=all(h['relative_bid_price_count_hypothesis_passed'] for h in hours),
        unknown_bits_interpreted=False,prior_033_diagnostic_passed=False,source_clock_interpreted_as_utc=False,
        strategy_replays=0,fresh_performance_eligible=False,annual_eligible=False,orders_available=False)


def main():
    api=runpy.run_path(str(ROOT/'scripts/fresh-replication-035.py'));ledger=api['verify']();folder=api['OUTPUT']
    capture=api['sealed'](folder/'capture.json');analysis=api['sealed'](ROOT/'reports/fresh-replication-035-analysis.json')
    reservation=json.loads((folder/'reservation.json').read_text())
    assert reservation==dict(version=ledger['version'],start_raw_ms=START,end_raw_ms=END,
        bounds='inclusive_ticks_four_half_open_hours',maximum_requests=3,orders_available=False)
    assert capture['version']==ledger['version'] and (capture['start_raw_ms'],capture['end_raw_ms'])==(START,END)
    assert capture['bounds']==reservation['bounds'] and 0<=capture['requests']==len(capture['reads'])<=3
    assert [r['kind'] for r in capture['reads']]==['horizon','ticks','bars'][:capture['requests']]
    originals={p.name:sha(p) for p in folder.iterdir() if p.is_file()}
    decoded={'ticks':[],'bars':[]};elapsed=0
    for r in capture['reads']:
        if r['receipt_after'] is not None:
            before,after=r['receipt_before'],r['receipt_after']
            for value in (before,after):
                assert all(type(v) is int and v>=0 for v in value.values())
                assert datetime.fromtimestamp(value['utc_ms']/1000,timezone.utc).date().isoformat()==ledger['date']
            assert after['utc_ms']>=before['utc_ms'] and r['elapsed_ns']==after['monotonic_ns']-before['monotonic_ns']>=0
            if r['kind']!='horizon':elapsed+=r['elapsed_ns']
        if r['kind']=='horizon':continue
        kind=r['kind']
        if r['complete_original_preserved']:
            rows=decode(folder,kind,r);decoded[kind]=rows
            assert r['audit']==(tick_audit(rows) if kind=='ticks' else bars_audit(rows))
        else:assert not (folder/(kind+'.bin')).exists() and not (folder/(kind+'.csv')).exists()
    assert elapsed==capture['history_elapsed_ns']
    for kind in set(('ticks','bars'))-{r['kind'] for r in capture['reads']}:
        assert not (folder/(kind+'.bin')).exists() and not (folder/(kind+'.csv')).exists()
    assert sum(p.stat().st_size for p in folder.iterdir() if p.is_file())<=ledger['maximum_evidence_bytes']
    for key in ('orders_available','annual_eligible','fresh_performance_eligible','complete_market_history_verified','source_clock_interpreted_as_utc'):
        assert capture[key] is False
    if capture['status']=='four_source_hours_originals_preserved_and_rows_valid':
        assert capture['requests']==3 and capture['stop_reason'] is None and capture['horizon']['raw_time_msc']>END
        assert abs(capture['horizon']['raw_time_msc']-capture['horizon']['received_after_utc_ms'])<=86400000
        assert all(math.isfinite(capture['horizon'][k]) for k in ('bid','ask')) and 0<capture['horizon']['bid']<=capture['horizon']['ask']
        for position in ('before','after'):
            r=capture['reads'][0]['receipt_'+position]
            assert capture['horizon']['received_'+position+'_utc_ms']==r['utc_ms']
            assert capture['horizon']['received_'+position+'_monotonic_ns']==r['monotonic_ns']
        for previous,current in zip(capture['reads'],capture['reads'][1:]):
            assert current['receipt_before']['utc_ms']>=previous['receipt_after']['utc_ms']
            assert current['receipt_before']['monotonic_ns']>=previous['receipt_after']['monotonic_ns']
        assert elapsed<=120000000000 and all(r['api_error_code']==1 for r in capture['reads'])
        assert all(r['elapsed_ns']<=60000000000 for r in capture['reads'][1:])
        completion=capture['completion_receipt'];last=capture['reads'][-1]['receipt_after']
        assert datetime.fromtimestamp(completion['utc_ms']/1000,timezone.utc).date().isoformat()==ledger['date']
        assert completion['utc_ms']>=last['utc_ms'] and completion['monotonic_ns']>=last['monotonic_ns']
        assert not tick_audit(decoded['ticks'])['error_counts'] and not bars_audit(decoded['bars'])['errors']
    else:assert capture['stop_reason'] is not None
    old=runpy.run_path(str(ROOT/'scripts/check-fresh-context-033.py'))
    old_capture=api['sealed'](ROOT/'data/fresh-context-033/capture.json')
    witnesses=old['decode'](ROOT/'data/fresh-context-033','ticks',old_capture['reads'][1]);assert len(witnesses)==13769
    invalid=any(r.get('complete_original_preserved') and (r.get('audit',{}).get('error_counts') or r.get('audit',{}).get('errors')) for r in capture['reads'])
    if invalid:
        expected=dict(analysis_available=False,analysis_stop_reason='invalid_originals_not_interpreted',source_rows=len(decoded['ticks']),
            witnesses_matched=None,disagreement_rows=None,all_four_relative_hypotheses_passed=False,
            prior_033_diagnostic_passed=False,strategy_replays=0,fresh_performance_eligible=False,annual_eligible=False,orders_available=False)
    else:
        expected=reconstruct(decoded['ticks'],decoded['bars'],witnesses)
        expected.update(analysis_available=True,analysis_stop_reason=None)
    for key,value in expected.items():assert analysis[key]==json.loads(json.dumps(value)),key
    assert analysis['ledger_sha256']==sha(api['LEDGER']) and analysis['capture_sha256']==sha(folder/'capture.json')
    assert analysis['market_requests']==capture['requests']
    assert analysis['collector_rows_valid']==(capture['status']=='four_source_hours_originals_preserved_and_rows_valid')
    diagnostic=analysis['collector_rows_valid'] and expected['all_four_relative_hypotheses_passed'] and expected['witnesses_matched']==13769
    assert analysis['diagnostic_passed']==diagnostic
    qualification=api['sealed'](ROOT/'reports/fresh-replication-035-qualification.json')
    assert sha(ROOT/'reports/fresh-replication-035-qualification.json')==ledger['qualification_review_sha256']
    assert qualification['performance_testing_permitted'] is False and qualification['relative_feed_collection_permitted'] is True
    assert api['sealed'](ROOT/'reports/fresh-context-033-checks.json')['diagnostic_passed'] is False
    assert not any('"'+k+'"' in json.dumps(capture).lower() for k in ('login','server','password','account_number','balance'))
    api['write'](ROOT/'reports/fresh-replication-035-checks.json',dict(kind='independent_four_hour_replication_check_035',
        checker_passed=True,diagnostic_passed=diagnostic,ledger_sha256=sha(api['LEDGER']),analysis_sha256=sha(ROOT/'reports/fresh-replication-035-analysis.json'),
        original_bindings=originals,rows_checked=len(decoded['ticks']),bars_checked=len(decoded['bars']),
        binary_fields_checked=8*(len(decoded['ticks'])+len(decoded['bars'])+len(witnesses)),reconstructed_fields=list(expected),
        witnesses_matched=expected['witnesses_matched'],ambiguous_witnesses=expected.get('ambiguous_witnesses'),missing_witnesses=expected.get('missing_witnesses'),
        disagreement_rows=expected['disagreement_rows'],tick_audit=tick_audit(decoded['ticks']),bar_audit=bars_audit(decoded['bars']),
        hours=[{k:v for k,v in h.items() if k!='fixed_definition_comparisons'} for h in expected.get('hours',[])],
        market_requests=capture['requests'],history_elapsed_ns=elapsed,prior_033_diagnostic_passed=False,
        strategy_replays=0,fresh_performance_eligible=False,annual_eligible=False,orders_available=False))
    print(json.dumps(dict(checker_passed=True,diagnostic_passed=diagnostic,rows=len(decoded['ticks']),bars=len(decoded['bars']),
        witnesses_matched=expected['witnesses_matched'],hour_hypotheses=[h['relative_bid_price_count_hypothesis_passed'] for h in expected.get('hours',[])])))


if __name__=='__main__':main()
