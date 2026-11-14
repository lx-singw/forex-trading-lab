"""Independent CSV, lineage, payload and hourly arithmetic; no source approval."""
import argparse
import csv
from datetime import datetime,timezone
from functools import lru_cache
import gzip
import hashlib
import json
import math
from pathlib import Path
import struct


def load(p): return json.loads(Path(p).read_text())


def sha(p):
    value=hashlib.sha256()
    with Path(p).open('rb') as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b''):value.update(chunk)
    return value.hexdigest()


@lru_cache(maxsize=4)
def eu_boundaries(year):
    import calendar
    dates=[]
    for month in (3,10):
        day=calendar.monthrange(year,month)[1]
        day-=(datetime(year,month,day).weekday()+1)%7
        dates.append(int(datetime(year,month,day,1,tzinfo=timezone.utc).timestamp())*1000)
    return dates


@lru_cache(maxsize=8192)
def independent_offset(year,source_hour_ms):
    spring,autumn=eu_boundaries(year)
    valid=[offset for offset in (4,5)
           if (spring<=source_hour_ms+offset*3_600_000<autumn)==(offset==4)]
    if len(valid)!=1:raise ValueError('Ambiguous or nonexistent independent candidate hour')
    return valid[0]*3_600_000


def check_month(folder):
    folder=Path(folder)
    meta=load(folder/'provenance.json')
    if sha(folder/'ticks.csv.gz')!=meta['data_sha256'] or sha(folder/'inventory.json')!=meta['inventory_sha256']:
        raise ValueError('Normalized output hash changed')
    inventory=load(folder/'inventory.json')
    expected={h['hour_start_ms']:h for h in inventory['hourly']}
    count=0; first=last=None; hour=None; bars={};payload=hashlib.sha256();gap_pairs=[]
    replay=meta['replay_lineage']
    with gzip.open(folder/'ticks.csv.gz','rt',newline='') as stream:
        reader=csv.DictReader(stream)
        if reader.fieldnames!=['sequence','source_sequence','source_label','candidate_time_msc','bid','ask','volume']:
            raise ValueError('Diagnostic schema differs')
        for row in reader:
            seq,source,ms=(int(row[k]) for k in ('sequence','source_sequence','candidate_time_msc'))
            bid,ask,volume=(float(row[k]) for k in ('bid','ask','volume'))
            original=count+(replay['rows'] if replay and count>=replay['second_start'] else 0)
            if (seq!=count or source!=original or last is not None and ms<last
                    or not all(math.isfinite(v) for v in (bid,ask,volume)) or not 0<bid<=ask or volume<0):
                raise ValueError('CSV order, lineage or quote differs')
            stamp=datetime.fromisoformat(row['source_label'])
            if stamp.tzinfo is not None or stamp.strftime('%Y%m')!=meta['source_month']:
                raise ValueError('Source label scope differs')
            # Independently check integer milliseconds against the declared calendar.
            # EU UTC changes are the last Sundays in March/October at01:00.
            source_ms=int(stamp.replace(tzinfo=timezone.utc).timestamp())*1000+stamp.microsecond//1000
            expected_ms=source_ms+independent_offset(stamp.year,source_ms//3_600_000*3_600_000)
            if ms!=expected_ms: raise ValueError('Independent candidate calendar differs')
            if last is not None and ms-last>3_600_000:gap_pairs.append((last,ms))
            first=ms if first is None else first
            last=ms
            h=ms//3_600_000*3_600_000
            if h not in bars:
                bars[h]=[0,ms,ms,bid,bid,bid,bid,ask,ask,ask,ask]
            bar=bars[h]
            bar[0]+=1;bar[2]=ms
            bar[4]=max(bar[4],bid);bar[5]=min(bar[5],bid);bar[6]=bid
            bar[8]=max(bar[8],ask);bar[9]=min(bar[9],ask);bar[10]=ask
            payload.update(struct.pack('>qqqddd',seq,source,ms,bid,ask,volume))
            count+=1
    if (count!=meta['candidate_rows'] or first!=meta['first_ms'] or last!=meta['last_ms']
            or count+meta['collapsed_replay_rows']!=meta['original_rows']
            or payload.hexdigest()!=meta['candidate_payload_sha256'] or set(bars)!=set(expected)):
        raise ValueError('Payload, count, endpoints or hour inventory differs')
    fields=['ticks','first_ms','last_ms','bid_open','bid_high','bid_low','bid_close',
            'ask_open','ask_high','ask_low','ask_close']
    for h,values in bars.items():
        if any(expected[h][key]!=value for key,value in zip(fields,values)):
            raise ValueError('Independent bid/ask hourly aggregate differs')
    if gap_pairs!=[(g['after_ms'],g['before_ms']) for g in inventory['gaps_over_one_hour']]:
        raise ValueError('Gap inventory differs')
    return {'source_month':meta['source_month'],'status':'independent_csv_calendar_payload_hourly_match',
            'ticks':count,'observed_hours':len(bars),'provenance_sha256':sha(folder/'provenance.json'),
            'market_data_eligibility_verified':False}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--year',type=int,required=True,choices=range(2020,2024))
    args=parser.parse_args()
    destination=Path(f'reports/normalization-015-independent-{args.year}.json')
    if destination.exists():raise FileExistsError('Independent review already exists')
    months=[]
    for m in range(1,13):
        row=check_month(Path(f'data/normalization-015/{args.year}{m:02}'))
        months.append(row)
        print(json.dumps(row),flush=True)
    with destination.open('x') as stream:
        json.dump({'year':args.year,'months':months,'performance_evaluation_ready':False},stream,indent=2,sort_keys=True)
        stream.write('\n')
