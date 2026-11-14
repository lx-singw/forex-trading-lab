"""Fixed seven event definitions over four raw-label hours, no clock conversion."""
from collections import Counter,defaultdict
import csv
import hashlib
import math
from pathlib import Path
import struct
from .fresh_replication_035 import START,END,HOURS,FIELDS
from .fresh_flags_034 import KNOWN_MASK,DEFINITIONS,validate,bid_bar


def original(folder,kind,meta,*,sample=False):
    """Verify the frozen 60-byte native schemas, seals supplied by the caller."""
    folder=Path(folder)
    fields,integers,fmt=(FIELDS,{'time','volume','time_msc','flags'},'<qdddQqId') if kind=='ticks' else (('time','open','high','low','close','tick_volume','spread','real_volume'),{'time','tick_volume','spread','real_volume'},'<qddddQiQ')
    binary_path=folder/('response.bin' if sample else kind+'.bin')
    csv_path=folder/('raw.csv' if sample else kind+'.csv')
    binary=binary_path.read_bytes()
    if hashlib.sha256(binary).hexdigest()!=meta['binary_sha256'] or meta['response_sha256']!=meta['binary_sha256']:
        raise ValueError('Original binary hash mismatch')
    if hashlib.sha256(csv_path.read_bytes()).hexdigest()!=meta['csv_sha256'] or csv_path.stat().st_size!=meta['csv_bytes']:
        raise ValueError('Original CSV hash/size mismatch')
    offsets=(0,8,16,24,32,40,48,52)
    formats=('<i8','<f8','<f8','<f8','<u8','<i8','<u4','<f8') if kind=='ticks' else (
             '<i8','<f8','<f8','<f8','<f8','<u8','<i4','<u8')
    expected=dict(itemsize=60,fields={k:dict(format=f,offset=o,size=int(f[2:])) for k,f,o in zip(fields,formats,offsets)},padding_offsets=[])
    if meta['binary_layout']!=expected:raise ValueError('Original layout differs from frozen schema')
    with csv_path.open(newline='') as f:
        reader=csv.DictReader(f)
        if tuple(reader.fieldnames)!=fields:raise ValueError('Unexpected CSV fields')
        rows=[{k:int(r[k]) if k in integers else float(r[k]) for k in fields} for r in reader]
    if len(rows)!=meta['returned_rows'] or len(binary)!=meta['response_bytes'] or len(binary)!=len(rows)*60:
        raise ValueError('Original row/byte count mismatch')
    for i,r in enumerate(rows):
        native=struct.unpack_from(fmt,binary,i*60)
        if any(v!=r[k] and not (k not in integers and math.isnan(v) and math.isnan(r[k])) for k,v in zip(fields,native)):
            raise ValueError('Original binary/CSV field mismatch')
    return rows


def analyze(rows,bars,witness_rows):
    validate(rows);validate(witness_rows)
    changes={};disagreements=[]
    for i,r in enumerate(rows):
        if not i:continue
        bc=r['bid']!=rows[i-1]['bid'];ac=r['ask']!=rows[i-1]['ask']
        changes[i]=(bc,ac)
        bf,af=bool(r['flags']&2),bool(r['flags']&4)
        fields=[k for k,f,c in (('bid',bf,bc),('ask',af,ac)) if f!=c]
        if fields:
            disagreements.append(dict(original_row_index=i,predecessor_original_row_index=i-1,
                raw_time_msc=r['time_msc'],same_millisecond=r['time_msc']==rows[i-1]['time_msc'],
                mismatched_fields=fields,bid_flag=bf,ask_flag=af,bid_value_changed=bc,ask_value_changed=ac,
                original_record=dict(r),predecessor_record=dict(rows[i-1])))
    results=[]
    for start in HOURS:
        end=start+3600000;indices=[i for i,r in enumerate(rows) if start<=r['time_msc']<end]
        hour=[rows[i] for i in indices]
        definitions={name:[] for name in DEFINITIONS}
        for i in indices:
            r=rows[i];bf,af=bool(r['flags']&2),bool(r['flags']&4)
            bc,ac=changes.get(i,(None,None))
            selections=dict(all=True,bid_flag=bf,ask_flag=af,both_flags=bf and af,neither_flag=not bf and not af,
                            bid_value_change_with_first=i==0 or bc,ask_value_change_with_first=i==0 or ac)
            for name,selected in selections.items():
                if selected:definitions[name].append(i)
        matching=[r for r in bars if r['time']==start//1000]
        recorded=matching[0] if len(matching)==1 else None
        comparisons=[]
        for name,selected in definitions.items():
            prices=bid_bar([rows[i] for i in selected]);differences=[]
            if prices is not None and recorded is not None:
                differences=[dict(field=k,reconstructed=v,recorded=recorded[k],difference=v-recorded[k])
                             for k,v in prices.items() if v!=recorded[k]]
            else:differences=[dict(field='comparison_unavailable')]
            comparisons.append(dict(definition=name,original_row_indices=selected,events=len(selected),
                bid_ohlc=prices,bar_price_differences=differences,
                recorded_tick_volume=recorded['tick_volume'] if recorded else None,
                volume_difference=len(selected)-recorded['tick_volume'] if recorded else None))
        selected_differences=[d for d in disagreements if start<=d['raw_time_msc']<end]
        full=comparisons[0];bid=comparisons[1]
        results.append(dict(start_raw_ms=start,end_raw_ms=end,hour_event_rows=len(indices),
            first_original_row_index=indices[0] if indices else None,last_original_row_index=indices[-1] if indices else None,
            exact_open_boundary_row_indices=[i for i,r in enumerate(rows) if r['time_msc']==start],
            exact_close_boundary_row_indices=[i for i,r in enumerate(rows) if r['time_msc']==end],
            first_row_without_predecessor_indices=[0] if 0 in indices else [],
            flag_histogram=dict(sorted(Counter(r['flags'] for r in hour).items())),
            known_mask_histogram=dict(sorted(Counter(r['flags']&KNOWN_MASK for r in hour).items())),
            remaining_mask_histogram=dict(sorted(Counter(r['flags']&(~KNOWN_MASK & 4294967295) for r in hour).items())),
            category_counts=dict(bid_flags=len(definitions['bid_flag']),ask_flags=len(definitions['ask_flag']),
                both_flags=len(definitions['both_flags']),neither_flag=len(definitions['neither_flag'])),
            bid_value_change_transitions=sum(changes.get(i,(False,False))[0] for i in indices),
            ask_value_change_transitions=sum(changes.get(i,(False,False))[1] for i in indices),
            flag_value_disagreement_row_indices=[d['original_row_index'] for d in selected_differences],
            bid_disagreement_rows=sum('bid' in d['mismatched_fields'] for d in selected_differences),
            ask_disagreement_rows=sum('ask' in d['mismatched_fields'] for d in selected_differences),
            fixed_definition_comparisons=comparisons,recorded_matching_bars=matching,
            relative_bid_price_count_hypothesis_passed=recorded is not None and bool(indices) and
                not full['bar_price_differences'] and bid['volume_difference']==0))
    lookup=defaultdict(list)
    for i,r in enumerate(rows):lookup[tuple(r[k] for k in FIELDS)].append(i)
    witnesses=[]
    for i,r in enumerate(witness_rows):
        matches=lookup[tuple(r[k] for k in FIELDS)]
        witnesses.append(dict(prior_original_row_index=i,matching_original_row_indices=matches,
            status='missing' if not matches else 'ambiguous' if len(matches)>1 else 'matched'))
    return dict(source_rows=len(rows),hours=results,flag_value_disagreements=disagreements,
        disagreement_rows=len(disagreements),same_millisecond_disagreement_rows=sum(d['same_millisecond'] for d in disagreements),
        witnesses=witnesses,witnesses_checked=len(witness_rows),witnesses_matched=sum(w['status']=='matched' for w in witnesses),
        ambiguous_witnesses=sum(w['status']=='ambiguous' for w in witnesses),missing_witnesses=sum(w['status']=='missing' for w in witnesses),
        upper_boundary_row_indices=[i for i,r in enumerate(rows) if r['time_msc']==END],
        outside_inclusive_request_row_indices=[i for i,r in enumerate(rows) if not START<=r['time_msc']<=END],
        all_four_relative_hypotheses_passed=all(h['relative_bid_price_count_hypothesis_passed'] for h in results),
        unknown_bits_interpreted=False,prior_033_diagnostic_passed=False,source_clock_interpreted_as_utc=False,
        strategy_replays=0,fresh_performance_eligible=False,annual_eligible=False,orders_available=False)
