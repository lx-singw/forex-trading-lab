"""Diagnostic monthly normalization with exact source lineage; no approval."""
import csv
from datetime import datetime, timezone
import gzip
import hashlib
import io
import json
from pathlib import Path
import struct

from .cli import write_json
from .corrected_clock import corrected_events
from .tick_audit import sha256

FIELDS = ['sequence','source_sequence','source_label','candidate_time_msc','bid','ask','volume']
MONTHS = tuple(f'{y}{m:02}' for y in range(2020,2024) for m in range(1,13))
HOUR = 3_600_000
EPOCH = datetime(1970,1,1,tzinfo=timezone.utc)


def milliseconds(instant):
    if instant.tzinfo is None or instant.microsecond % 1000:
        raise ValueError('Candidate timestamp must have exact integer milliseconds')
    delta=instant-EPOCH
    return delta.days*86_400_000+delta.seconds*1000+delta.microseconds//1000


def payload_bytes(sequence,source_sequence,ms,bid,ask,volume):
    return struct.pack('>qqqddd',sequence,source_sequence,ms,bid,ask,volume)


def normalize(ticks,month,destination,binding,expected_original_rows,replay=None):
    """Finish a complete source stream before publishing any ready provenance."""
    destination=Path(destination)
    if month not in MONTHS:
        raise ValueError('Source month outside declared scope')
    destination.mkdir(parents=True,exist_ok=False)
    partial=destination/'ticks.csv.gz.partial'
    count=same_ms=identical=above_spread=0
    first=last=previous_quote=None
    digest=hashlib.sha256()
    hours,gaps,year_counts=[],[],{}
    current=None
    with partial.open('xb') as binary, gzip.GzipFile(filename='',mode='wb',fileobj=binary,mtime=0,compresslevel=1) as zipped:
        with io.TextIOWrapper(zipped,encoding='utf-8',newline='') as output:
            writer=csv.writer(output)
            writer.writerow(FIELDS)
            for tick in corrected_events(ticks,month,replay):
                ms=milliseconds(tick['candidate_time'])
                bid,ask,volume=tick['bid'],tick['ask'],tick['volume']
                if last is not None:
                    same_ms+=ms==last
                    identical+=(ms,bid,ask,volume)==previous_quote
                    if ms-last>HOUR:
                        gaps.append({'after_ms':last,'before_ms':ms,'seconds':(ms-last)/1000,
                                     'classification':'unclassified_never_filled'})
                first=ms if first is None else first
                last=ms
                previous_quote=(ms,bid,ask,volume)
                hour=ms//HOUR*HOUR
                spread=(ask-bid)/.0001
                above_spread+=spread>1.5
                if current is None or current['hour_start_ms']!=hour:
                    current={'hour_start_ms':hour,'ticks':0,'first_ms':ms,'last_ms':ms,
                        'bid_open':bid,'bid_high':bid,'bid_low':bid,'bid_close':bid,
                        'ask_open':ask,'ask_high':ask,'ask_low':ask,'ask_close':ask,
                        'entry_spread_pips':spread,'minimum_spread_pips':spread,'maximum_spread_pips':spread}
                    hours.append(current)
                    year=str(tick['candidate_time'].year)
                year_counts[year]=year_counts.get(year,0)+1
                current['ticks']+=1
                current['last_ms']=ms
                current['bid_high']=max(current['bid_high'],bid)
                current['bid_low']=min(current['bid_low'],bid)
                current['bid_close']=bid
                current['ask_high']=max(current['ask_high'],ask)
                current['ask_low']=min(current['ask_low'],ask)
                current['ask_close']=ask
                current['minimum_spread_pips']=min(current['minimum_spread_pips'],spread)
                current['maximum_spread_pips']=max(current['maximum_spread_pips'],spread)
                source_label=tick['source_label'].isoformat(timespec='milliseconds')
                writer.writerow([count,tick['source_sequence'],source_label,ms,bid,ask,volume])
                digest.update(payload_bytes(count,tick['source_sequence'],ms,bid,ask,volume))
                count+=1
    removed=replay.rows if replay else 0
    if not count or count+removed!=expected_original_rows:
        raise ValueError('Original/derived/replay row counts do not reconcile')
    data=destination/'ticks.csv.gz'
    partial.rename(data)
    inventory={'month':month,'hourly':hours,'gaps_over_one_hour':gaps,
        'same_millisecond_transitions':same_ms,'identical_transition_events_retained':identical,
        'quotes_above_1_5_pip_spread':above_spread,'candidate_year_tick_counts':year_counts,
        'performance_evaluation_ready':False}
    write_json(destination/'inventory.json',inventory)
    result={'kind':'diagnostic_candidate_ticks_015','symbol':'EURUSD','source_month':month,
        'source_binding':binding,'source_member':f'DAT_ASCII_EURUSD_T_{month}.csv',
        'original_rows':expected_original_rows,'candidate_rows':count,'collapsed_replay_rows':removed,
        'first_ms':first,'last_ms':last,'data_sha256':sha256(data),
        'inventory_sha256':sha256(destination/'inventory.json'),'candidate_payload_sha256':digest.hexdigest(),
        'replay_lineage':{**vars(replay),'correspondence':'second_start+i -> first_start+i; all other source rows retained'} if replay else None,
        'candidate_clock':'source wall +7h with frozen Europe/Athens calendar; unapproved hypothesis',
        'original_archives_unchanged':True,'absolute_utc_verified':False,
        'performance_evaluation_ready':False,'demo_execution_ready':False}
    write_json(destination/'provenance.json',result)
    write_json(destination/'seal.json',{'provenance_sha256':sha256(destination/'provenance.json')})
    return result


def completed(destination,binding):
    destination=Path(destination)
    if (destination/'ticks.csv.gz.partial').exists() or not (destination/'provenance.json').is_file():
        raise ValueError('Partial or failed month cannot be resumed or overwritten')
    result=json.loads((destination/'provenance.json').read_text())
    seal=json.loads((destination/'seal.json').read_text())
    if (sha256(destination/'provenance.json')!=seal['provenance_sha256']
            or result.get('kind')!='diagnostic_candidate_ticks_015' or result.get('source_binding')!=binding
            or sha256(destination/'ticks.csv.gz')!=result['data_sha256']
            or sha256(destination/'inventory.json')!=result['inventory_sha256']
            or result.get('performance_evaluation_ready') is not False):
        raise ValueError('Completed diagnostic month changed')
    return result


def coverage(rows):
    """Full frozen scope; no session closures are inferred from the calendar."""
    if len(rows)!=48 or {r['source_month'] for r in rows}!=set(MONTHS):
        raise ValueError('Exactly all 48 unique source months required')
    rows=sorted(rows,key=lambda r:r['source_month'])
    seams=[]
    for a,b in zip(rows,rows[1:]):
        if b['first_ms']<a['last_ms']:
            raise ValueError('Candidate month seam reverses chronology')
        seams.append({'after_source_month':a['source_month'],'before_source_month':b['source_month'],
                      'after_ms':a['last_ms'],'before_ms':b['first_ms'],
                      'seconds':(b['first_ms']-a['last_ms'])/1000,'classification':'unclassified_never_filled'})
    return {'months':48,'original_rows':sum(r['original_rows'] for r in rows),
        'candidate_rows':sum(r['candidate_rows'] for r in rows),
        'collapsed_replay_rows':sum(r['collapsed_replay_rows'] for r in rows),
        'month_seams':seams,'performance_evaluation_ready':False,'absolute_utc_verified':False}


def empty_hours(observed):
    lower=milliseconds(datetime(2020,1,1,tzinfo=timezone.utc))
    upper=milliseconds(datetime(2024,1,1,tzinfo=timezone.utc))
    observed=set(observed)
    missing=[h for h in range(lower,upper,HOUR) if h not in observed]
    weekday=[h for h in missing if datetime.fromtimestamp(h/1000,timezone.utc).weekday()<5]
    return {'bounds_ms':[lower,upper],'observed_hours_inside_bounds':sum(lower<=h<upper for h in observed),
        'observed_hours_outside_bounds':sorted(h for h in observed if not lower<=h<upper),
        'quote_free_hours':missing,'weekday_quote_free_hours':weekday,
        'classification':'watchlist_only_no_authoritative_session_calendar',
        'missing_hours_filled':False,'session_closures_certified':False}
