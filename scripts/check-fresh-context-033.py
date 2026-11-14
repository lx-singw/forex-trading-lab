"""Independent stdlib decoding, complete-record witnesses and source-hour H1 comparison."""
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
START,END=1791291600000,1791295200000


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
    if len(rows)!=1:errors.append('expected_exactly_one_bar')
    for r in rows:
        if r['time']!=1791291600:errors.append('unexpected_bar_open_label')
        prices=[r[k] for k in ('open','high','low','close')]
        if any(not math.isfinite(v) or v<=0 for v in prices) or r['low']>min(r['open'],r['close']) or max(r['open'],r['close'])>r['high']:
            errors.append('invalid_bar_prices')
        if min(r['tick_volume'],r['spread'],r['real_volume'])<0:errors.append('invalid_bar_auxiliary_fields')
    return dict(rows=len(rows),errors=errors)


def compare(ticks,bars,witness_rows):
    lookup=defaultdict(list)
    for i,r in enumerate(ticks):lookup[tuple(r[k] for k in TICKS)].append(i)
    witnesses=[]
    for i,r in enumerate(witness_rows):
        matches=lookup[tuple(r[k] for k in TICKS)]
        witnesses.append(dict(prior_original_row_index=i,matching_original_row_indices=matches,
            status='missing' if not matches else 'ambiguous' if len(matches)>1 else 'matched'))
    hour=[r for r in ticks if START<=r['time_msc']<END]
    boundary=[i for i,r in enumerate(ticks) if r['time_msc']==END]
    stats=None;differences=[]
    if hour:
        stats=dict(open=hour[0]['bid'],high=max(r['bid'] for r in hour),low=min(r['bid'] for r in hour),
                   close=hour[-1]['bid'],tick_volume=len(hour))
    if stats is not None and len(bars)==1:
        for k,v in stats.items():
            if v!=bars[0][k]:differences.append(dict(field=k,reconstructed=v,recorded=bars[0][k],difference=v-bars[0][k]))
    else:differences.append(dict(field='comparison_availability',reconstructed=stats is not None,recorded=len(bars)==1))
    return dict(witnesses=witnesses,witnesses_checked=len(witness_rows),
        witnesses_matched=sum(w['status']=='matched' for w in witnesses),
        ambiguous_witnesses=sum(w['status']=='ambiguous' for w in witnesses),
        missing_witnesses=sum(w['status']=='missing' for w in witnesses),
        half_open_hour_rows=len(hour),upper_boundary_row_indices=boundary,upper_boundary_rows=len(boundary),
        reconstructed_bid_bar=stats,recorded_bars=bars,bar_differences=differences,
        bar_agreement=not differences)


def main():
    api=runpy.run_path(str(ROOT/'scripts/fresh-context-033.py'));ledger=api['verify']();folder=api['OUTPUT']
    capture=api['sealed'](folder/'capture.json');reservation=json.loads((folder/'reservation.json').read_text())
    assert reservation==dict(version=ledger['version'],start_raw_ms=START,end_raw_ms=END,
        bounds='inclusive_ticks_half_open_hour',maximum_requests=3,orders_available=False)
    assert capture['version']==ledger['version'] and (capture['start_raw_ms'],capture['end_raw_ms'])==(START,END)
    assert capture['bounds']==reservation['bounds'] and 0<=capture['requests']==len(capture['reads'])<=3
    assert [r['kind'] for r in capture['reads']]==['horizon','ticks','bars'][:capture['requests']]
    originals={p.name:sha(p) for p in folder.iterdir() if p.is_file()}
    decoded={'ticks':[],'bars':[]};elapsed=0
    for read in capture['reads']:
        if read['receipt_after'] is not None:
            before,after=read['receipt_before'],read['receipt_after']
            for r in (before,after):
                assert all(type(v) is int and v>=0 for v in r.values())
                assert datetime.fromtimestamp(r['utc_ms']/1000,timezone.utc).date().isoformat()==ledger['date']
            assert after['utc_ms']>=before['utc_ms']
            assert read['elapsed_ns']==after['monotonic_ns']-before['monotonic_ns']>=0
            if read['kind']!='horizon':elapsed+=read['elapsed_ns']
        if read['kind']=='horizon':continue
        kind=read['kind']
        if read['complete_original_preserved']:
            rows=decode(folder,kind,read);decoded[kind]=rows
            assert read['audit']==(tick_audit(rows) if kind=='ticks' else bars_audit(rows))
        else:assert not (folder/(kind+'.bin')).exists() and not (folder/(kind+'.csv')).exists()
    assert elapsed==capture['history_elapsed_ns']
    for kind in set(('ticks','bars'))-{r['kind'] for r in capture['reads']}:
        assert not (folder/(kind+'.bin')).exists() and not (folder/(kind+'.csv')).exists()
    assert sum(p.stat().st_size for p in folder.iterdir() if p.is_file())<=ledger['maximum_evidence_bytes']
    for key in ('orders_available','annual_eligible','fresh_performance_eligible','complete_market_history_verified','source_clock_interpreted_as_utc'):
        assert capture[key] is False
    if capture['status']=='source_hour_originals_preserved_and_rows_valid':
        assert capture['requests']==3 and capture['stop_reason'] is None
        assert capture['horizon']['raw_time_msc']>END
        assert abs(capture['horizon']['raw_time_msc']-capture['horizon']['received_after_utc_ms'])<=86400000
        assert all(math.isfinite(capture['horizon'][k]) for k in ('bid','ask')) and 0<capture['horizon']['bid']<=capture['horizon']['ask']
        for position in ('before','after'):
            r=capture['reads'][0]['receipt_'+position]
            assert capture['horizon']['received_'+position+'_utc_ms']==r['utc_ms']
            assert capture['horizon']['received_'+position+'_monotonic_ns']==r['monotonic_ns']
        for prior,current in zip(capture['reads'],capture['reads'][1:]):
            assert current['receipt_before']['utc_ms']>=prior['receipt_after']['utc_ms']
            assert current['receipt_before']['monotonic_ns']>=prior['receipt_after']['monotonic_ns']
        assert elapsed<=120000000000 and all(r['api_error_code']==1 for r in capture['reads'])
        assert all(r['elapsed_ns']<=60000000000 for r in capture['reads'][1:])
        completion=capture['completion_receipt'];last=capture['reads'][-1]['receipt_after']
        assert datetime.fromtimestamp(completion['utc_ms']/1000,timezone.utc).date().isoformat()==ledger['date']
        assert completion['utc_ms']>=last['utc_ms'] and completion['monotonic_ns']>=last['monotonic_ns']
        assert not tick_audit(decoded['ticks'])['error_counts'] and not bars_audit(decoded['bars'])['errors']
    else:assert capture['stop_reason'] is not None
    old_folder=ROOT/'data/fresh-ticks-032';old=api['sealed'](old_folder/'capture.json')
    # Decode all eight original fields from both representations of the frozen 032 input.
    # Adapt its names only; the old originals are never edited.
    with (old_folder/'raw.csv').open(newline='') as f:
        reader=csv.DictReader(f);assert tuple(reader.fieldnames)==TICKS
        witness_rows=[{k:int(r[k]) if k in TICK_INTS else float(r[k]) for k in TICKS} for r in reader]
    old_binary=(old_folder/'response.bin').read_bytes()
    assert sha(old_folder/'response.bin')==old['response_sha256'] and sha(old_folder/'raw.csv')==old['csv_sha256']
    assert len(witness_rows)==196 and len(old_binary)==196*60
    for i,r in enumerate(witness_rows):assert tuple(r[k] for k in TICKS)==struct.unpack_from('<qdddQqId',old_binary,i*60)
    comparison=compare(decoded['ticks'],decoded['bars'],witness_rows)
    assert not any('"'+k+'"' in json.dumps(capture).lower() for k in ('login','server','password','account_number','balance'))
    diagnostic=(capture['status']=='source_hour_originals_preserved_and_rows_valid' and
                comparison['witnesses_matched']==196 and comparison['bar_agreement'])
    report=dict(kind='independent_source_hour_check_033',checker_passed=True,diagnostic_passed=diagnostic,
        ledger_sha256=sha(api['LEDGER']),original_bindings=originals,rows_checked=len(decoded['ticks']),
        bars_checked=len(decoded['bars']),binary_fields_checked=8*(len(decoded['ticks'])+len(decoded['bars'])),
        tick_audit=tick_audit(decoded['ticks']),bar_audit=bars_audit(decoded['bars']),**comparison,
        history_elapsed_ns=elapsed,market_requests=capture['requests'],strategy_replays=0,
        fresh_performance_eligible=False,annual_eligible=False,orders_available=False)
    api['write'](ROOT/'reports/fresh-context-033-checks.json',report)
    print(json.dumps({k:report[k] for k in ('checker_passed','diagnostic_passed','rows_checked','bars_checked',
                                          'witnesses_matched','ambiguous_witnesses','bar_differences')}))


if __name__=='__main__':main()
