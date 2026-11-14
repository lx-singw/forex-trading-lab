"""Pure offline fixed flag definitions; no market API or strategy evaluation."""
from collections import Counter,defaultdict
import csv
import hashlib
import math
from pathlib import Path
import struct

VERSION='offline_quote_flags_034_v1'
START,END=1791291600000,1791295200000
FIELDS=('time','bid','ask','last','volume','time_msc','flags','volume_real')
BAR_FIELDS=('time','open','high','low','close','tick_volume','spread','real_volume')
INTS={'time','volume','time_msc','flags'}
BAR_INTS={'time','tick_volume','spread','real_volume'}
FLAGS=dict(BID=2,ASK=4,LAST=8,VOLUME=16,BUY=32,SELL=64)
KNOWN_MASK=126
DEFINITIONS=('all','bid_flag','ask_flag','both_flags','neither_flag',
             'bid_value_change_with_first','ask_value_change_with_first')


def original(folder,kind,meta,*,sample=False):
    """Verify the frozen 60-byte native schemas, seals supplied by the caller."""
    folder=Path(folder)
    fields,integers,fmt=(FIELDS,INTS,'<qdddQqId') if kind=='ticks' else (BAR_FIELDS,BAR_INTS,'<qddddQiQ')
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
        if tuple(r[k] for k in fields)!=struct.unpack_from(fmt,binary,i*60):
            raise ValueError('Original binary/CSV field mismatch')
    return rows


def validate(rows):
    previous=None
    for r in rows:
        if set(r)!=set(FIELDS) or any(type(r[k]) is not int for k in INTS):raise ValueError('Invalid tick schema')
        if not all(type(r[k]) in (int,float) and math.isfinite(r[k]) for k in set(FIELDS)-INTS):
            raise ValueError('Invalid numeric values')
        if not 0<r['bid']<=r['ask'] or min(r['last'],r['volume_real'],r['volume'])<0 or not 0<=r['flags']<=4294967295:
            raise ValueError('Invalid quote fields')
        if r['time_msc']<=0 or r['time']!=r['time_msc']//1000 or previous is not None and r['time_msc']<previous:
            raise ValueError('Invalid source chronology')
        previous=r['time_msc']


def bid_bar(rows):
    if not rows:return None
    return dict(open=rows[0]['bid'],high=max(r['bid'] for r in rows),low=min(r['bid'] for r in rows),close=rows[-1]['bid'])


def analyze(rows,bars,witness_rows,start=START,end=END):
    if (start,end)!=(START,END):raise ValueError('Only the declared source hour is permitted')
    validate(rows);validate(witness_rows)
    hour_indices=[i for i,r in enumerate(rows) if start<=r['time_msc']<end]
    histogram=Counter();known=Counter();remaining=Counter();categories=Counter()
    definitions={name:[] for name in DEFINITIONS}
    differences=[];bid_changes=ask_changes=0
    unknown_first=[]
    for i,r in enumerate(rows):
        bf,af=bool(r['flags']&2),bool(r['flags']&4)
        bc=ac=None
        if i:
            bc=r['bid']!=rows[i-1]['bid'];ac=r['ask']!=rows[i-1]['ask']
            problems=[name for name,flag,change in (('bid',bf,bc),('ask',af,ac)) if flag!=change]
            if problems:
                differences.append(dict(original_row_index=i,predecessor_original_row_index=i-1,
                    within_half_open_hour=start<=r['time_msc']<end,same_millisecond=r['time_msc']==rows[i-1]['time_msc'],
                    mismatched_fields=problems,bid_flag=bf,ask_flag=af,bid_value_changed=bc,ask_value_changed=ac,
                    original_record={k:r[k] for k in FIELDS},predecessor_record={k:rows[i-1][k] for k in FIELDS}))
        if not start<=r['time_msc']<end:continue
        histogram[r['flags']]+=1;known[r['flags']&KNOWN_MASK]+=1;remaining[r['flags']&(~KNOWN_MASK & 4294967295)]+=1
        categories['bid_flags']+=bf;categories['ask_flags']+=af;categories['both_flags']+=bf and af
        categories['neither_flag']+=not bf and not af
        if i:
            bid_changes+=bc;ask_changes+=ac
        else:unknown_first.append(i)
        selections=dict(all=True,bid_flag=bf,ask_flag=af,both_flags=bf and af,neither_flag=not bf and not af,
                        bid_value_change_with_first=i==0 or bc,ask_value_change_with_first=i==0 or ac)
        for name,selected in selections.items():
            if selected:definitions[name].append(i)
    lookup=defaultdict(list)
    for i,r in enumerate(rows):lookup[tuple(r[k] for k in FIELDS)].append(i)
    witnesses=[]
    for i,r in enumerate(witness_rows):
        indices=lookup[tuple(r[k] for k in FIELDS)]
        witnesses.append(dict(prior_original_row_index=i,matching_original_row_indices=indices,
            status='missing' if not indices else 'ambiguous' if len(indices)>1 else 'matched'))
    comparisons=[]
    for name,indices in definitions.items():
        prices=bid_bar([rows[i] for i in indices]);price_differences=[]
        if len(bars)==1 and prices is not None:
            price_differences=[dict(field=k,reconstructed=v,recorded=bars[0][k],difference=v-bars[0][k])
                               for k,v in prices.items() if v!=bars[0][k]]
        else:price_differences=[dict(field='comparison_unavailable')]
        comparisons.append(dict(definition=name,original_row_indices=indices,events=len(indices),
            bid_ohlc=prices,bar_price_differences=price_differences,
            recorded_tick_volume=bars[0]['tick_volume'] if len(bars)==1 else None,
            volume_difference=len(indices)-bars[0]['tick_volume'] if len(bars)==1 else None))
    return dict(version=VERSION,source_rows=len(rows),half_open_hour_rows=len(hour_indices),
        upper_boundary_row_indices=[i for i,r in enumerate(rows) if r['time_msc']==end],
        outside_inclusive_request_row_indices=[i for i,r in enumerate(rows) if not start<=r['time_msc']<=end],
        flag_histogram=dict(sorted(histogram.items())),known_mask_histogram=dict(sorted(known.items())),
        remaining_mask_histogram=dict(sorted(remaining.items())),category_counts=dict(categories),
        bid_value_change_transitions=bid_changes,ask_value_change_transitions=ask_changes,
        first_row_without_predecessor_indices=unknown_first,
        flag_value_disagreements=differences,disagreement_rows=len(differences),
        bid_disagreement_rows=sum('bid' in d['mismatched_fields'] for d in differences),
        ask_disagreement_rows=sum('ask' in d['mismatched_fields'] for d in differences),
        same_millisecond_disagreement_rows=sum(d['same_millisecond'] for d in differences),
        witnesses=witnesses,witnesses_matched=sum(w['status']=='matched' for w in witnesses),
        ambiguous_witnesses=sum(w['status']=='ambiguous' for w in witnesses),missing_witnesses=sum(w['status']=='missing' for w in witnesses),
        fixed_definition_comparisons=comparisons,recorded_bars=bars,unknown_bits_interpreted=False,
        source_clock_interpreted_as_utc=False,prior_033_diagnostic_passed=False,
        market_requests=0,strategy_replays=0,fresh_performance_eligible=False,annual_eligible=False,orders_available=False)
