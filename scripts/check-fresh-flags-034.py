"""Separate reconstruction of every fixed flag audit field from sealed originals."""
from collections import Counter
import csv
import json
from pathlib import Path
import runpy
import struct

ROOT=Path(__file__).resolve().parents[1]
FIELDS=('time','bid','ask','last','volume','time_msc','flags','volume_real')
START,END=1791291600000,1791295200000


def reconstruct(ticks,bars,sample):
    hour=[i for i,t in enumerate(ticks) if 1791291600000<=t['time_msc']<1791295200000]
    flaghist=Counter(ticks[i]['flags'] for i in hour)
    known=Counter(ticks[i]['flags']&126 for i in hour)
    remaining=Counter(ticks[i]['flags']&4294967169 for i in hour)
    bflags={i for i,t in enumerate(ticks) if t['flags']&2}
    aflags={i for i,t in enumerate(ticks) if t['flags']&4}
    bchange={i for i in range(1,len(ticks)) if ticks[i]['bid']!=ticks[i-1]['bid']}
    achange={i for i in range(1,len(ticks)) if ticks[i]['ask']!=ticks[i-1]['ask']}
    hourset=set(hour)
    differences=[]
    for i in range(1,len(ticks)):
        mismatch=[]
        if (i in bflags)!=(i in bchange):mismatch.append('bid')
        if (i in aflags)!=(i in achange):mismatch.append('ask')
        if mismatch:
            differences.append(dict(original_row_index=i,predecessor_original_row_index=i-1,
                within_half_open_hour=i in hourset,same_millisecond=ticks[i]['time_msc']==ticks[i-1]['time_msc'],
                mismatched_fields=mismatch,bid_flag=i in bflags,ask_flag=i in aflags,
                bid_value_changed=i in bchange,ask_value_changed=i in achange,
                original_record=dict(ticks[i]),predecessor_record=dict(ticks[i-1])))
    lookup={}
    for i,t in enumerate(ticks):lookup.setdefault(tuple(t[k] for k in FIELDS),[]).append(i)
    witnesses=[]
    for i,t in enumerate(sample):
        matches=lookup.get(tuple(t[k] for k in FIELDS),[])
        witnesses.append(dict(prior_original_row_index=i,matching_original_row_indices=matches,
                             status='matched' if len(matches)==1 else 'ambiguous' if matches else 'missing'))
    definitions=[('all',hourset),('bid_flag',bflags&hourset),('ask_flag',aflags&hourset),
        ('both_flags',bflags&aflags&hourset),('neither_flag',hourset-bflags-aflags),
        ('bid_value_change_with_first',(bchange|{0})&hourset),('ask_value_change_with_first',(achange|{0})&hourset)]
    comparisons=[]
    for name,selection in definitions:
        indices=sorted(selection)
        prices=None
        if indices:
            values=[ticks[i]['bid'] for i in indices]
            prices=dict(open=values[0],high=max(values),low=min(values),close=values[-1])
        deltas=[]
        if prices is None or len(bars)!=1:deltas=[dict(field='comparison_unavailable')]
        else:
            for key in ('open','high','low','close'):
                if prices[key]!=bars[0][key]:deltas.append(dict(field=key,reconstructed=prices[key],recorded=bars[0][key],difference=prices[key]-bars[0][key]))
        comparisons.append(dict(definition=name,original_row_indices=indices,events=len(indices),bid_ohlc=prices,
            bar_price_differences=deltas,recorded_tick_volume=bars[0]['tick_volume'] if len(bars)==1 else None,
            volume_difference=len(indices)-bars[0]['tick_volume'] if len(bars)==1 else None))
    return dict(version='offline_quote_flags_034_v1',source_rows=len(ticks),half_open_hour_rows=len(hour),
        upper_boundary_row_indices=[i for i,t in enumerate(ticks) if t['time_msc']==END],
        outside_inclusive_request_row_indices=[i for i,t in enumerate(ticks) if not START<=t['time_msc']<=END],
        flag_histogram=dict(sorted(flaghist.items())),known_mask_histogram=dict(sorted(known.items())),remaining_mask_histogram=dict(sorted(remaining.items())),
        category_counts=dict(bid_flags=len(bflags&hourset),ask_flags=len(aflags&hourset),
                             both_flags=len(bflags&aflags&hourset),neither_flag=len(hourset-bflags-aflags)) if hour else {},
        bid_value_change_transitions=len(bchange&hourset),ask_value_change_transitions=len(achange&hourset),
        first_row_without_predecessor_indices=[0] if 0 in hourset else [],
        flag_value_disagreements=differences,disagreement_rows=len(differences),
        bid_disagreement_rows=sum('bid' in d['mismatched_fields'] for d in differences),
        ask_disagreement_rows=sum('ask' in d['mismatched_fields'] for d in differences),
        same_millisecond_disagreement_rows=sum(d['same_millisecond'] for d in differences),
        witnesses=witnesses,witnesses_matched=sum(w['status']=='matched' for w in witnesses),
        ambiguous_witnesses=sum(w['status']=='ambiguous' for w in witnesses),missing_witnesses=sum(w['status']=='missing' for w in witnesses),
        fixed_definition_comparisons=comparisons,recorded_bars=bars,unknown_bits_interpreted=False,
        source_clock_interpreted_as_utc=False,prior_033_diagnostic_passed=False,market_requests=0,strategy_replays=0,
        fresh_performance_eligible=False,annual_eligible=False,orders_available=False)


def main():
    api=runpy.run_path(str(ROOT/'scripts/fresh-flags-034.py'));ledger=api['verify']()
    result=api['sealed'](api['OUTPUT']);reservation=api['sealed'](api['RESERVATION'])
    assert reservation==dict(version=ledger['version'],ledger_sha256=api['sha'](api['LEDGER']),maximum_market_requests=0,orders_available=False)
    assert result['ledger_sha256']==api['sha'](api['LEDGER'])
    reader=runpy.run_path(str(ROOT/'scripts/check-fresh-context-033.py'))
    capture=api['sealed'](ROOT/'data/fresh-context-033/capture.json')
    ticks=reader['decode'](ROOT/'data/fresh-context-033','ticks',capture['reads'][1])
    bars=reader['decode'](ROOT/'data/fresh-context-033','bars',capture['reads'][2])
    sample_capture=api['sealed'](ROOT/'data/fresh-ticks-032/capture.json')
    sample_folder=ROOT/'data/fresh-ticks-032'
    with (sample_folder/'raw.csv').open(newline='') as f:
        rows=csv.DictReader(f);assert tuple(rows.fieldnames)==FIELDS
        sample=[{k:int(r[k]) if k in ('time','volume','time_msc','flags') else float(r[k]) for k in FIELDS} for r in rows]
    binary=(sample_folder/'response.bin').read_bytes()
    assert api['sha'](sample_folder/'response.bin')==sample_capture['binary_sha256']==sample_capture['response_sha256']
    assert api['sha'](sample_folder/'raw.csv')==sample_capture['csv_sha256']
    assert len(binary)==sample_capture['response_bytes']==60*len(sample) and len(sample)==sample_capture['returned_rows']==196
    assert (sample_folder/'raw.csv').stat().st_size==sample_capture['csv_bytes']
    for i,r in enumerate(sample):assert tuple(r[k] for k in FIELDS)==struct.unpack_from('<qdddQqId',binary,i*60)
    assert not reader['tick_audit'](ticks)['error_counts'] and not reader['bars_audit'](bars)['errors']
    expected=reconstruct(ticks,bars,sample)
    for key,value in expected.items():assert result[key]==json.loads(json.dumps(value)),key
    assert result['fields_compared']==8*(len(ticks)+len(bars)+len(sample))==111728
    assert result['kind']=='offline_fixed_flag_audit_034'
    inputs={n:h for n,h in ledger['bindings'].items() if n.startswith('data/')}
    assert result['input_original_bindings']==inputs
    old=api['sealed'](ROOT/'reports/fresh-context-033-checks.json');assert old['diagnostic_passed'] is False
    api['write'](ROOT/'reports/fresh-flags-034-checks.json',dict(kind='independent_offline_flag_check_034',checker_passed=True,
        audit_sha256=api['sha'](api['OUTPUT']),ledger_sha256=api['sha'](api['LEDGER']),input_original_bindings=inputs,
        reconstructed_fields=list(expected),binary_fields_checked=111728,source_rows=len(ticks),witnesses_matched=result['witnesses_matched'],
        disagreement_rows=result['disagreement_rows'],bid_disagreement_rows=result['bid_disagreement_rows'],ask_disagreement_rows=result['ask_disagreement_rows'],
        prior_033_diagnostic_passed=False,market_requests=0,strategy_replays=0,fresh_performance_eligible=False,annual_eligible=False,orders_available=False))
    print(json.dumps(dict(checker_passed=True,fields_checked=111728,disagreement_rows=result['disagreement_rows'],market_requests=0)))


if __name__=='__main__':main()
