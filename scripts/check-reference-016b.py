"""Recompute reference evidence from ZIPs using separate calendar arithmetic."""
import csv
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import hashlib
import io
import json
from pathlib import Path
import zipfile

DAYS=('2022-01-07','2022-07-08','2022-11-04','2023-01-06','2023-07-07','2023-11-03',
      '2023-03-26','2023-03-27','2023-07-14')
EPOCH=datetime(1970,1,1)
HOUR=3600000


def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''): h.update(block)
    return h.hexdigest()


def manual_utc(local):
    def sunday(month):
        last=datetime(local.year,month,31)
        return last-timedelta(days=(last.weekday()+1)%7)
    spring,autumn=sunday(3),sunday(10)
    if spring+timedelta(hours=2)<=local<spring+timedelta(hours=3):
        raise ValueError('Nonexistent CET label')
    if autumn+timedelta(hours=2)<=local<autumn+timedelta(hours=3):
        raise ValueError('Ambiguous CET label')
    summer=spring+timedelta(hours=3)<=local<autumn+timedelta(hours=2)
    delta=local-timedelta(hours=2 if summer else 1)-EPOCH
    return delta.days*86400000+delta.seconds*1000


def extract(day):
    path=Path('data/reference-016')/day/'original.zip'
    bars={}; count=0; previous=None
    with zipfile.ZipFile(path) as z:
        expected=datetime.strptime(day,'%Y-%m-%d').strftime('%d%m%y.txt')
        if z.namelist()!=[expected]: raise ValueError('Unexpected independent schema')
        with z.open(expected) as f:
            reader=csv.reader(io.TextIOWrapper(f,encoding='ascii'))
            if next(reader)!=['<TICKER>','<DTYYYYMMDD>','<TIME>','<OPEN>','<HIGH>','<LOW>','<CLOSE>']:
                raise ValueError('Header differs')
            for fields in reader:
                if len(fields)!=7: raise ValueError('Malformed row')
                if fields[0]!='EURUSD': continue
                next_date=(datetime.strptime(day,'%Y-%m-%d')+timedelta(days=1)).strftime('%Y%m%d')
                if fields[1]!=day.replace('-','') and (fields[1]!=next_date or fields[2]!='000000'):
                    raise ValueError('Date differs')
                local=datetime.strptime(fields[1],'%Y%m%d')
                time=fields[2]
                if time=='240000': local+=timedelta(days=1)
                else:
                    parsed=datetime.strptime(time,'%H%M%S')
                    if parsed.second: raise ValueError('Minute alignment differs')
                    local=local.replace(hour=parsed.hour,minute=parsed.minute)
                stamp=manual_utc(local)
                if previous is not None and stamp<=previous: raise ValueError('Order differs')
                previous=stamp
                o,h,l,c=map(Decimal,fields[3:])
                if not all(x.is_finite() and x>0 for x in (o,h,l,c)) or not l<=min(o,c)<=max(o,c)<=h:
                    raise ValueError('OHLC differs')
                hour=stamp//HOUR*HOUR
                if hour not in bars:
                    bars[hour]={'hour_start_ms':hour,'minutes':0,'first_ms':stamp,
                        'open':str(o),'high':str(h),'low':str(l)}
                bar=bars[hour];bar['minutes']+=1
                bar.update(last_ms=stamp,close=str(c),high=str(max(Decimal(bar['high']),h)),
                           low=str(min(Decimal(bar['low']),l)))
                count+=1
    return count,bars


def distances(reference,candidate):
    if reference is None or candidate is None:return None
    return {key:float(abs(Decimal(reference[key])-Decimal(str(candidate['bid_'+key])))*10000)
            for key in ('open','high','low','close')}


def check():
    ledger_path=Path('reports/reference-016b-ledger.json')
    ledger=json.loads(ledger_path.read_text())
    seal=json.loads(Path('reports/reference-016b-seal.json').read_text())
    if sha(ledger_path)!=seal['ledger_sha256']: raise ValueError('Ledger seal differs')
    for name,digest in ledger['file_bindings'].items():
        if sha(Path(name))!=digest: raise ValueError('Bound input changed')
    review_path=Path('reports/reference-016b-review.json')
    review=json.loads(review_path.read_text())
    if len(review['source_days'])!=9 or len(review['screens'])!=6 or len(review['gap_probes'])!=3:
        raise ValueError('Review scope differs')
    if set(review['utc_day_comparisons'])!=set(DAYS):raise ValueError('Comparison days differ')
    if review['ledger_sha256']!=sha(ledger_path): raise ValueError('Review ledger differs')
    if any(review[key] for key in ('session_calendar_certified','absolute_utc_certified',
                                  'performance_evaluation_ready','demo_execution_ready')):
        raise ValueError('Reference promoted beyond diagnostic scope')
    references={};candidate={};total=0
    for day,record in zip(sorted(DAYS),review['source_days']):
        if record['source_day']!=day: raise ValueError('Source day differs')
        count,bars=extract(day);total+=count
        if record['archive_sha256']!=sha(Path('data/reference-016')/day/'original.zip'):
            raise ValueError('Archive binding differs')
        if count!=record['eurusd_rows'] or list(bars.values())!=record['hourly']:
            raise ValueError('Independent reference aggregates differ')
        for stamp,bar in bars.items():
            if stamp in references:
                old=references[stamp]
                if bar['first_ms']<=old['last_ms']:raise ValueError('Files overlap')
                old.update(minutes=old['minutes']+bar['minutes'],last_ms=bar['last_ms'],close=bar['close'],
                    high=str(max(Decimal(old['high']),Decimal(bar['high']))),
                    low=str(min(Decimal(old['low']),Decimal(bar['low']))))
            else: references[stamp]=dict(bar)
        month=day[:7].replace('-','')
        for bar in json.loads(Path(f'data/normalization-015/{month}/inventory.json').read_text())['hourly']:
            candidate[bar['hour_start_ms']]=bar
    if total!=review['reference_eurusd_rows'] or list(references.values())!=review['reference_hourly']:
        raise ValueError('Combined reference differs')
    comparisons={}
    for day in DAYS:
        start=(datetime.strptime(day,'%Y-%m-%d')-EPOCH).days*86400000
        expected=[]
        for hour in range(24):
            stamp=start+hour*HOUR
            expected.append({'hour_start_ms':stamp,'reference':references.get(stamp),
                'candidate':candidate.get(stamp),
                'absolute_ohlc_distance_pips':distances(references.get(stamp),candidate.get(stamp))})
        if expected!=review['utc_day_comparisons'][day]:raise ValueError('Hourly comparison differs')
        comparisons[day]=expected
    for saved in review['gap_probes']:
        instant=datetime.fromisoformat(saved['utc_label'])
        if {k:v for k,v in saved.items() if k!='utc_label'}!=comparisons[instant.strftime('%Y-%m-%d')][instant.hour]:
            raise ValueError('Gap probe differs')
    passes=[]
    for day,saved in zip(DAYS[:6],review['screens']):
        start=(datetime.strptime(day,'%Y-%m-%d')-EPOCH).days*86400000
        values={name:[] for name in ('aligned','minus_one_hour','plus_one_hour')}
        for hour in range(6,18):
            for name,shift in zip(values,(0,-1,1)):
                delta=distances(references.get(start+hour*HOUR),candidate.get(start+(hour+shift)*HOUR))
                values[name].append(None if delta is None else delta['close'])
        complete=all(None not in v for v in values.values())
        medians={}
        for key,array in values.items():
            ordered=sorted(x for x in array if x is not None)
            medians[key]=(ordered[5]+ordered[6])/2 if len(ordered)==12 else None
        within=sum(v is not None and v<=2 for v in values['aligned'])
        passed=bool(complete and within>=10 and medians['aligned']<=2
                    and medians['aligned']<medians['minus_one_hour']
                    and medians['aligned']<medians['plus_one_hour'])
        expected={'day':day,'utc_hours':list(range(6,18)),'close_distances_pips':values,
            'median_close_distance_pips':medians,'all_36_pairs_present':complete,
            'aligned_pairs_within_2_pips':within,'fixed_screen_pass':passed}
        if expected!=saved:raise ValueError('Fixed screen differs')
        passes.append(passed)
    if all(passes)!=review['all_six_screens_pass']:raise ValueError('Overall screen differs')
    result={'kind':'independent_reference_check_016b','review_sha256':sha(review_path),
        'ledger_sha256':sha(ledger_path),'nine_archives_checked':9,'eurusd_rows_checked':total,
        'utc_day_hours_checked':216,'screens_checked':6,'gap_probes_checked':3,
        'calendar_method':'manual last Sunday CET/CEST; no normalizer or reference imports',
        'all_saved_arithmetic_matches':True,'absolute_utc_certified':False,
        'performance_evaluation_ready':False,'demo_execution_ready':False}
    path=Path('reports/reference-016b-independent.json')
    with path.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps(result),flush=True)


if __name__=='__main__':check()
