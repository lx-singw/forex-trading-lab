"""Independent five-hour reconstruction from originals; no stage parser imports."""
import csv
import gzip
import hashlib
import io
import json
import re
import zipfile
from datetime import datetime,timedelta,timezone
from fractions import Fraction
from itertools import combinations
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
HOUR=3600000
EPOCH=datetime(1970,1,1,tzinfo=timezone.utc)
WINDOWS=(('march','2023-03-26T22:00:00Z','2023-03-27T01:00:00Z','202303','03'),
         ('july','2023-07-14T19:00:00Z','2023-07-14T21:00:00Z','202307','07'))
SOURCES=('exness','histdata_candidate','broker_conditional','forexite_reference')
FIELDS=['window','source','path','member','record','raw_label','event_ms','bid','ask','open','high','low','close']


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()


def ms(clock):
    delta=clock-EPOCH
    return delta.days*86400000+delta.seconds*1000+delta.microseconds//1000


def check_hist_members(archive,member):
    notes=member[:-4]+'.txt'
    assert archive.namelist()==[member,notes]
    entries=archive.infolist()
    assert all(not entry.flag_bits&1 for entry in entries)
    assert sum(entry.file_size for entry in entries)<=128*1024*1024
    note=archive.getinfo(notes)
    assert note.file_size<=65536
    with archive.open(note) as stream:
        content=stream.read(65537)
    assert len(content)==note.file_size and len(content)<=65536


def source_events(window,source):
    name,first,last,month,exness_month=window
    begin=datetime.fromisoformat(first.replace('Z','+00:00'))
    end=datetime.fromisoformat(last.replace('Z','+00:00'))
    start_ms,end_ms=ms(begin),ms(end)
    selected=[]
    if source=='exness':
        path=f'data/exness-024/Exness_EURUSD_2023_{exness_month}.zip'
        with zipfile.ZipFile(ROOT/path) as archive:
            assert len(archive.infolist())==1 and archive.infolist()[0].file_size<=256*1024*1024
            entry=archive.infolist()[0]
            assert not entry.flag_bits&1
            with archive.open(entry) as stream:
                rows=csv.reader(io.TextIOWrapper(stream,encoding='utf-8',newline=''))
                assert next(rows)==['Exness','Symbol','Timestamp','Bid','Ask']
                for record,row in enumerate(rows,2):
                    assert len(row)==5 and row[:2]==['exness','EURUSD']
                    if not first.replace('T',' ').replace('Z','.000Z')<=row[2]<last.replace('T',' ').replace('Z','.000Z'):
                        continue
                    stamp=row[2]
                    assert re.fullmatch(r'[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{3}Z',stamp)
                    clock=datetime(int(stamp[:4]),int(stamp[5:7]),int(stamp[8:10]),int(stamp[11:13]),
                                   int(stamp[14:16]),int(stamp[17:19]),int(stamp[20:23])*1000,tzinfo=timezone.utc)
                    selected.append(dict(path=path,member=entry.filename,record=record,raw_label=stamp,
                                         event_ms=ms(clock),bid=row[3],ask=row[4]))
    elif source=='histdata_candidate':
        path=f'data/history-009-raw/{month}/original.zip'
        lower=(begin-timedelta(hours=4)).strftime('%Y%m%d %H%M%S')+'000'
        upper=(end-timedelta(hours=4)).strftime('%Y%m%d %H%M%S')+'000'
        with zipfile.ZipFile(ROOT/path) as archive:
            member=f'DAT_ASCII_EURUSD_T_{month}.csv'
            check_hist_members(archive,member)
            with archive.open(member) as stream:
                count=0
                for record,row in enumerate(csv.reader(io.TextIOWrapper(stream,encoding='ascii')),1):
                    count=record
                    assert len(row)==4
                    label=row[0]
                    if not lower<=label<upper:continue
                    assert re.fullmatch(r'[0-9]{8} [0-9]{9}',label)
                    wall=datetime(int(label[:4]),int(label[4:6]),int(label[6:8]),int(label[9:11]),
                                  int(label[11:13]),int(label[13:15]),int(label[15:])*1000,tzinfo=timezone.utc)
                    clock=wall+timedelta(hours=4)
                    selected.append(dict(path=path,member=member,record=record,
                                         raw_label=wall.replace(tzinfo=None).isoformat(timespec='milliseconds'),
                                         event_ms=ms(clock),bid=row[1],ask=row[2]))
        provenance=json.loads((ROOT/f'data/normalization-015/{month}/provenance.json').read_text())
        assert count==provenance['original_rows']
    elif source=='broker_conditional':
        folder='data/correction-013-gaps/2023-03-27' if name=='march' else 'data/recovery-010/chunk-081'
        path=folder+'/ticks.csv.gz'
        with gzip.open(ROOT/path,'rt',newline='') as f:
            rows=csv.reader(f)
            assert next(rows)==['sequence','time_msc','bid','ask','flags']
            count=0
            for record,row in enumerate(rows,2):
                count+=1
                assert len(row)==5 and int(row[0])==record-2
                stamp=int(row[1])-10800000
                if start_ms<=stamp<end_ms:
                    selected.append(dict(path=path,member=None,record=record,raw_label=row[1],
                                         event_ms=stamp,bid=row[2],ask=row[3]))
        metadata=json.loads((ROOT/f'{folder}/capture.json').read_text())
        assert count==metadata['ticks']
    else:
        days=('2023-03-26','2023-03-27') if name=='march' else ('2023-07-14',)
        for day in days:
            path=f'data/reference-016/{day}/original.zip'
            member=datetime.strptime(day,'%Y-%m-%d').strftime('%d%m%y.txt')
            with zipfile.ZipFile(ROOT/path) as archive:
                assert archive.namelist()==[member] and archive.infolist()[0].file_size<=16*1024*1024
                with archive.open(member) as stream:
                    rows=csv.reader(io.TextIOWrapper(stream,encoding='ascii',newline=''))
                    assert next(rows)==['<TICKER>','<DTYYYYMMDD>','<TIME>','<OPEN>','<HIGH>','<LOW>','<CLOSE>']
                    for record,row in enumerate(rows,2):
                        assert len(row)==7
                        if row[0]!='EURUSD':continue
                        local=datetime.strptime(row[1],'%Y%m%d')
                        assert row[1]==day.replace('-','') or (local==datetime.strptime(day,'%Y-%m-%d')+timedelta(days=1) and row[2]=='000000')
                        if row[2]=='240000':
                            local+=timedelta(days=1)
                        else:
                            assert re.fullmatch(r'[0-9]{6}',row[2]) and row[2][4:]=='00'
                            local=local.replace(hour=int(row[2][:2]),minute=int(row[2][2:4]),second=int(row[2][4:]))
                        clock=(local-timedelta(hours=2)).replace(tzinfo=timezone.utc)
                        stamp=ms(clock)
                        if start_ms<=stamp<end_ms:
                            selected.append(dict(path=path,member=member,record=record,raw_label=row[1]+' '+row[2],
                                                 event_ms=stamp,**dict(zip(('open','high','low','close'),row[3:]))))
    for event in selected:
        fields=('open','high','low','close') if source=='forexite_reference' else ('bid','ask')
        numbers=[Fraction(event[key]) for key in fields]
        assert all(n>0 for n in numbers)
        if source=='forexite_reference':
            o,h,l,c=numbers
            assert l<=min(o,c)<=max(o,c)<=h
        else:
            assert numbers[1]>=numbers[0]
        assert start_ms<=event['event_ms']<end_ms
    return selected


def capture_bounds(window,source):
    if source!='broker_conditional':
        return (ms(datetime.fromisoformat(window[1].replace('Z','+00:00'))),
                ms(datetime.fromisoformat(window[2].replace('Z','+00:00'))))
    folder='data/correction-013-gaps/2023-03-27' if window[0]=='march' else 'data/recovery-010/chunk-081'
    metadata=json.loads((ROOT/f'{folder}/capture.json').read_text())
    assert metadata['account_type']=='demo' and metadata['terminal_algo_trading'] is False
    return tuple(ms(datetime.fromisoformat(metadata[key]))-10800000
                 for key in ('source_label_start','source_label_end_exclusive'))


def build_bar(events,start,size,available,reference):
    selected=[event for event in events if start<=event['event_ms']<start+size]
    assert available or not selected
    bar=dict(start_ms=start,available=available,records=len(selected) if available else None,
             first_ms=None,last_ms=None,first_original=None,last_original=None,
             **{f'{side}_{key}':None for side in ('bid','ask','reference') for key in ('open','high','low','close')},
             status='unavailable' if not available else 'present' if selected else 'empty')
    if selected:
        a,b=selected[0],selected[-1]
        bar.update(first_ms=a['event_ms'],last_ms=b['event_ms'],
                   first_original={k:a[k] for k in ('path','member','record','raw_label')},
                   last_original={k:b[k] for k in ('path','member','record','raw_label')})
        for side in (('reference',) if reference else ('bid','ask')):
            if reference:
                o=Fraction(a['open']);c=Fraction(b['close'])
                h=max(Fraction(e['high']) for e in selected)
                l=min(Fraction(e['low']) for e in selected)
            else:
                values=[Fraction(e[side]) for e in selected]
                o,c,h,l=values[0],values[-1],max(values),min(values)
            bar.update({f'{side}_{key}':value for key,value in zip(('open','high','low','close'),(o,h,l,c))})
    return bar


def verify_bar(expected,saved):
    assert expected.keys()==saved.keys()
    for key,value in expected.items():
        if isinstance(value,Fraction):
            assert Fraction(saved[key])==value,key
        else:
            assert saved[key]==value,key


def event_digest(events,reference):
    digest=hashlib.sha256()
    previous=None
    last_record=None
    ties=0
    for event in events:
        stamp=event['event_ms']
        assert previous is None or stamp>=previous
        identity=(event['path'],event['member'])
        assert last_record is None or last_record[0]!=identity or event['record']>last_record[1]
        if previous==stamp:
            assert not reference
            ties+=1
        fields=('open','high','low','close') if reference else ('bid','ask')
        values=[Fraction(event[key]) for key in fields]
        payload=[event['path'],event['member'],event['record'],event['raw_label'],stamp,
                 [str(n.numerator)+'/'+str(n.denominator) for n in values]]
        digest.update((json.dumps(payload,separators=(',',':'),ensure_ascii=True)+'\n').encode('ascii'))
        previous=stamp;last_record=(identity,event['record'])
    return digest.hexdigest(),ties


def main():
    supplemental_path=ROOT/'reports/exness-comparison-025b-ledger.json'
    assert sha(supplemental_path)==supplemental_path.with_suffix('.sha256').read_text().strip()
    supplemental=json.loads(supplemental_path.read_text())
    for name,digest in supplemental['bindings'].items():assert sha(ROOT/name)==digest,name
    ledger_path=ROOT/'reports/exness-comparison-025-ledger.json'
    assert sha(ledger_path)==ledger_path.with_suffix('.sha256').read_text().strip()
    ledger=json.loads(ledger_path.read_text())
    for name,digest in ledger['bindings'].items():assert sha(ROOT/name)==digest,name
    report_path=ROOT/'reports/exness-comparison-025-review.json'
    assert sha(report_path)==report_path.with_suffix('.sha256').read_text().strip()
    report=json.loads(report_path.read_text())
    assert report['ledger_sha256']==sha(ledger_path)
    assert len(report['windows'])==2
    for key in ('annual_eligible','absolute_utc_certified','historical_sessions_certified','upstream_independence_verified',
                'performance_evaluation_ready','market_profitability_established','orders_available'):
        assert report[key] is False
    lineage_path=ROOT/report['lineage_path']
    assert sha(lineage_path)==report['lineage_sha256']
    reviews=[]
    canonical={}
    bars_checked=distance_count=lineage_count=0
    tail=0
    with lineage_path.open(newline='') as stream:
        saved_rows=csv.DictReader(stream)
        assert saved_rows.fieldnames==FIELDS
        for window,saved_window in zip(WINDOWS,report['windows']):
            assert saved_window['name']==window[0]
            begin=ms(datetime.fromisoformat(window[1].replace('Z','+00:00')))
            end=ms(datetime.fromisoformat(window[2].replace('Z','+00:00')))
            source_bars={}
            for source in SOURCES:
                events=source_events(window,source)
                reference=source=='forexite_reference'
                saved=saved_window['sources'][source]
                assert saved['selected_records']==len(events)
                expected_hash,ties=event_digest(events,reference)
                assert saved['event_sha256']==expected_hash and saved['tied_transitions']==ties
                captured=capture_bounds(window,source)
                expected_hours=[]
                assert len(saved['hours'])==(end-begin)//HOUR
                for hour,saved_bar in zip(range(begin,end,HOUR),saved['hours']):
                    expected=build_bar(events,hour,HOUR,captured[0]<=hour and hour+HOUR<=captured[1],reference)
                    verify_bar(expected,saved_bar)
                    expected_hours.append(expected);bars_checked+=1
                source_bars[source]=expected_hours
                if source=='exness':
                    assert len(saved['minutes'])==(end-begin)//60000
                    for minute,saved_bar in zip(range(begin,end,60000),saved['minutes']):
                        verify_bar(build_bar(events,minute,60000,True,False),saved_bar)
                        bars_checked+=1
                    if window[0]=='july':
                        cutoff=ms(datetime(2023,7,14,19,25,16,885000,tzinfo=timezone.utc))
                        tail=sum(cutoff<event['event_ms']<cutoff//HOUR*HOUR+HOUR for event in events)
                        assert saved['tail_records']==tail
                    else:assert saved['tail_records'] is None
                else:assert not saved['minutes'] and saved['tail_records'] is None
                for event in events:
                    row=next(saved_rows,None)
                    assert row is not None and row['window']==window[0] and row['source']==source
                    for key in FIELDS[2:]:
                        if key in ('bid','ask','open','high','low','close'):
                            if key in event:assert Fraction(row[key])==Fraction(event[key])
                            else:assert row[key]==''
                        elif key in ('record','event_ms'):assert int(row[key])==event[key]
                        else:assert row[key]==('' if event.get(key) is None else str(event[key]))
                    lineage_count+=1
                reviews.append(dict(window=window[0],source=source,selected_records=len(events),
                                    original_event_sha256=expected_hash,matched=True))
            expected_distances=[]
            for left,right in combinations(SOURCES,2):
                for a,b in zip(source_bars[left],source_bars[right]):
                    distances=None
                    if a['records'] and b['records']:
                        first='reference' if left=='forexite_reference' else 'bid'
                        second='reference' if right=='forexite_reference' else 'bid'
                        distances={key:abs(a[f'{first}_{key}']-b[f'{second}_{key}'])*10000
                                   for key in ('open','high','low','close')}
                    expected_distances.append(dict(left=left,right=right,hour_start_ms=a['start_ms'],absolute_ohlc_distance_pips=distances))
            assert len(expected_distances)==len(saved_window['distances'])
            for expected,saved in zip(expected_distances,saved_window['distances']):
                for key in ('left','right','hour_start_ms'):assert expected[key]==saved[key]
                values=expected['absolute_ohlc_distance_pips']
                if values is None:assert saved['absolute_ohlc_distance_pips'] is None
                else:
                    for key,value in values.items():assert Fraction(saved['absolute_ohlc_distance_pips'][key])==value
                distance_count+=1
            canonical[window[0]]=source_bars['exness']
        assert next(saved_rows,None) is None
    march=canonical['march'][1]['records'];july=canonical['july'][1]['records']
    expected=dict(march_utc23=dict(answer=march>0,count=march),july_tail=dict(answer=tail>0,count=tail),
                  july_utc20=dict(answer=july>0,count=july))
    assert report['questions']==expected
    output=dict(kind='independent_original_coverage_comparison_025b',passed=True,sources=reviews,
                lineage_records_checked=lineage_count,aggregate_bins_checked=bars_checked,
                pairwise_hour_distances_checked=distance_count,questions=expected,
                supplemental_ledger_sha256=sha(supplemental_path),ledger_sha256=sha(ledger_path),review_sha256=sha(report_path),lineage_sha256=sha(lineage_path),
                calendar_method='Fixed previously declared selected-period mappings, manual timestamps, no primary imports',
                annual_eligible=False,performance_evaluation_ready=False,orders_available=False)
    path=ROOT/'reports/exness-comparison-025b-checks.json'
    with path.open('x') as f:json.dump(output,f,indent=2,sort_keys=True);f.write('\n')
    with path.with_suffix('.sha256').open('x') as f:f.write(sha(path)+'\n')
    print(json.dumps(dict(passed=True,lineage_records_checked=lineage_count,aggregate_bins_checked=bars_checked,
                          pairwise_hour_distances_checked=distance_count,questions=expected)),flush=True)


if __name__=='__main__':main()
