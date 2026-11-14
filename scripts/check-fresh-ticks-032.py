"""Independent binary/CSV reconstruction and all recorded poll witnesses."""
from collections import Counter,defaultdict
import csv
import json
import math
from pathlib import Path
import runpy
import struct

ROOT=Path(__file__).resolve().parents[1]
API=runpy.run_path(str(ROOT/'scripts/fresh-ticks-032.py'))
ledger=API['verify']()
folder=API['OUTPUT']
capture=API['sealed'](folder/'capture.json')
reservation=json.loads((folder/'reservation.json').read_text())
fields=('time','bid','ask','last','volume','time_msc','flags','volume_real')
integers={'time','volume','time_msc','flags'}
assert reservation['maximum_requests']==1 and reservation['orders_available'] is False
assert capture['version']==ledger['version']
assert (capture['start_raw_ms'],capture['end_raw_ms'])==(ledger['start_raw_ms'],ledger['end_raw_ms'])
assert capture['bounds']=='inclusive' and 0<=capture['requests']<=1
rows=[]
originals={p.name:API['sha'](p) for p in folder.iterdir() if p.is_file()}
if capture['complete_original_preserved']:
    binary=(folder/'response.bin').read_bytes()
    assert API['sha'](folder/'response.bin')==capture['binary_sha256']==capture['response_sha256']
    assert API['sha'](folder/'raw.csv')==capture['csv_sha256']
    assert len(binary)==capture['response_bytes']
    with (folder/'raw.csv').open(newline='') as f:
        reader=csv.DictReader(f)
        assert tuple(reader.fieldnames)==fields
        for row in reader:
            rows.append({k:int(row[k]) if k in integers else float(row[k]) for k in fields})
    assert len(rows)==capture['returned_rows']<=20000
    layout=capture['binary_layout']
    assert set(layout['fields'])==set(fields)
    size=layout['itemsize']
    assert 0<size<=128 and len(binary)==size*len(rows)
    codes={('i',1):'b',('u',1):'B',('i',2):'h',('u',2):'H',('i',4):'i',('u',4):'I',
           ('i',8):'q',('u',8):'Q',('f',4):'f',('f',8):'d'}
    occupied=set()
    for name,part in layout['fields'].items():
        fmt=part['format']
        assert fmt[0] in ('<','>','|') and int(fmt[2:])==part['size']
        assert fmt[1] in ('i','u') if name in integers else fmt[1]=='f'
        offset,length=part['offset'],part['size']
        region=set(range(offset,offset+length))
        assert 0<=offset and offset+length<=size and not occupied&region
        occupied|=region
        unpack=('<' if fmt[0]=='|' else fmt[0])+codes[(fmt[1],length)]
        for i,row in enumerate(rows):
            original=struct.unpack_from(unpack,binary,i*size+offset)[0]
            value=row[name]
            assert original==value or name not in integers and math.isnan(original) and math.isnan(value),(i,name)
    padding=set(range(size))-occupied
    assert padding==set(layout['padding_offsets'])
    assert all(binary[i+offset]==0 for i in range(0,len(binary),size) for offset in padding)
    counts,indices=Counter(),[]
    same=duplicates=0
    gaps=[]
    for i,row in enumerate(rows):
        failures=[]
        if not math.isfinite(row['bid']) or not math.isfinite(row['ask']) or row['bid']<=0 or row['ask']<row['bid']:
            failures.append('invalid_prices')
        if row['time_msc']<=0 or row['time']<0 or row['time_msc']//1000!=row['time']:
            failures.append('timestamp_mismatch')
        if row['time_msc']<ledger['start_raw_ms'] or row['time_msc']>ledger['end_raw_ms']:
            failures.append('outside_request')
        if row['volume']<0 or not 0<=row['flags']<=4294967295 or any(
                not math.isfinite(row[k]) or row[k]<0 for k in ('last','volume_real')):
            failures.append('invalid_auxiliary_fields')
        if i:
            prior=rows[i-1]
            difference=row['time_msc']-prior['time_msc']
            if difference<0:failures.append('decreasing_labels')
            else:gaps.append(difference)
            same+=difference==0
            duplicates+=all(row[k]==prior[k] for k in fields)
        counts.update(failures)
        if failures and len(indices)<20:indices.append(dict(row_index=i,errors=failures))
    expected=dict(rows=len(rows),first_raw_time_msc=rows[0]['time_msc'] if rows else None,
        last_raw_time_msc=rows[-1]['time_msc'] if rows else None,
        same_millisecond_transitions=same,exact_duplicate_transitions=duplicates,
        maximum_nonnegative_intertick_gap_ms=max(gaps,default=None),error_counts=dict(counts),first_error_indices=indices)
    assert capture['audit']==expected
    assert sum(p.stat().st_size for p in folder.iterdir() if p.is_file())<=4*1024*1024
else:
    assert not (folder/'raw.csv').exists() and not (folder/'response.bin').exists()
    assert capture['status']!='sample_preserved_and_rows_valid'
for key in ('source_clock_interpreted_as_utc','complete_market_history_verified','fresh_performance_eligible','annual_eligible','orders_available'):
    assert capture[key] is False
if capture['status']=='sample_preserved_and_rows_valid':
    assert capture['requests']==1 and rows and not capture['audit']['error_counts']
    assert capture['api_error_code']==1 and 0<=capture['elapsed_ns']<=60000000000
else:
    assert capture['stop_reason'] is not None
probe=API['sealed'](ROOT/'reports/fresh-data-031-probe.json')
assert API['sha'](ROOT/'reports/fresh-data-031-probe.json')==ledger['original_probe_sha256']
by_quote=defaultdict(list)
for i,row in enumerate(rows):
    by_quote[(row['time_msc'],row['bid'],row['ask'])].append(i)
witnesses=[]
for observation in probe['observations']:
    identity=(observation['raw_time_msc'],observation['bid'],observation['ask'])
    matches=by_quote[identity]
    witnesses.append(dict(poll_index=observation['poll_index'],raw_time_msc=identity[0],
        matching_original_row_indices=matches,status='missing' if not matches else 'ambiguous' if len(matches)>1 else 'matched'))
assert len(witnesses)==120
matched=sum(bool(w['matching_original_row_indices']) for w in witnesses)
ambiguous=sum(w['status']=='ambiguous' for w in witnesses)
serialized=json.dumps(capture).lower()
assert not any('"'+k+'"' in serialized for k in ('login','server','password','account_number','name','balance'))
diagnostic=capture['status']=='sample_preserved_and_rows_valid' and matched==120
API['write'](ROOT/'reports/fresh-ticks-032-checks.json',dict(kind='independent_original_sample_check_032',
    checker_passed=True,diagnostic_passed=diagnostic,ledger_sha256=API['sha'](API['LEDGER']),
    original_bindings=originals,rows_checked=len(rows),binary_fields_checked=len(rows)*8,
    witnesses_checked=120,witnesses_matched=matched,ambiguous_witnesses=ambiguous,
    distinct_poll_quote_identities=len({(r['raw_time_msc'],r['bid'],r['ask']) for r in probe['observations']}),
    distinct_original_rows_used_by_witnesses=len({i for w in witnesses for i in w['matching_original_row_indices']}),
    witnesses=witnesses,original_audit=capture.get('audit'),market_requests=capture['requests'],
    strategy_replays=0,fresh_performance_eligible=False,annual_eligible=False,orders_available=False))
print(json.dumps(dict(checker_passed=True,diagnostic_passed=diagnostic,rows=len(rows),witnesses_matched=matched,ambiguous=ambiguous)))
