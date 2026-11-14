"""Saved raw-field arithmetic and fixed primary-source action validation."""
from collections import Counter
from datetime import datetime
import struct

VERSION='native_clock_semantics_038_v1'
TARGETS=tuple('https://www.mql5.com/en/docs/'+p for p in (
    'dateandtime/timecurrent','dateandtime/timetradeserver','dateandtime/timegmt','dateandtime/timelocal',
    'constants/structures/mqltick','account/accountinfointeger','check/terminalinfointeger','runtime/running'))
PATTERNS=('last quote','calculation','local time','milliseconds','ACCOUNT_TRADE_MODE','TERMINAL_TRADE_ALLOWED')


def native_clocks(blob):
    if not isinstance(blob,bytes) or not blob or len(blob)%60:
        raise ValueError('invalid_native_tick_bytes')
    residual=Counter();mismatches=[];seconds=[];milliseconds=[]
    for i in range(len(blob)//60):
        second=struct.unpack_from('<q',blob,i*60)[0]
        millisecond=struct.unpack_from('<q',blob,i*60+40)[0]
        if second<=0 or millisecond<=0:raise ValueError('invalid_native_clock')
        delta=millisecond-second*1000;residual[delta]+=1
        if millisecond//1000!=second:
            mismatches.append(dict(original_row_index=i,time_s=second,time_msc=millisecond,residual_ms=delta))
        seconds.append(second);milliseconds.append(millisecond)
    return dict(rows=len(seconds),clock_fields_decoded=2*len(seconds),
        seconds_min=min(seconds),seconds_max=max(seconds),milliseconds_min=min(milliseconds),milliseconds_max=max(milliseconds),
        residual_histogram={str(k):v for k,v in sorted(residual.items())},
        floor_relation_mismatches=mismatches,all_seconds_equal_floor_milliseconds=not mismatches,
        seconds_reversals=[i for i in range(1,len(seconds)) if seconds[i]<seconds[i-1]],
        milliseconds_reversals=[i for i in range(1,len(milliseconds)) if milliseconds[i]<milliseconds[i-1]])


def receipt_intervals(rows):
    if not rows:raise ValueError('no_saved_receipts')
    intervals=[]
    for i,row in enumerate(rows):
        q,b,a=(row[k] for k in ('raw_time_msc','received_before_utc_ms','received_after_utc_ms'))
        if any(type(v) is not int or v<=0 for v in (q,b,a)) or a<b:raise ValueError('invalid_saved_receipt')
        intervals.append(dict(original_row_index=i,lower_ms=q-a,upper_ms=q-b))
    lower=min(r['lower_ms'] for r in intervals);upper=max(r['upper_ms'] for r in intervals)
    return dict(observations=len(rows),intervals=intervals,envelope_ms=[lower,upper],
        distance_from_hypothetical_three_hours_ms=[lower-10_800_000,upper-10_800_000],
        offset_correction_authorized=False)


def research_valid(research,declared):
    if research['version']!=VERSION or declared['version']!=VERSION or tuple(declared['targets'])!=TARGETS:
        raise ValueError('research_declaration_changed')
    if tuple(declared['find_patterns'])!=PATTERNS or declared['budgets']!={'search':0,'open':8,'find':6}:
        raise ValueError('research_budget_changed')
    if set(research)!={'version','actions','findings','market_requests','orders_available'}:
        raise ValueError('research_schema_changed')
    counts=Counter();opened=set();retrieved=set();found=set()
    for i,action in enumerate(research['actions']):
        if action['index']!=i or action['kind'] not in ('open','find') or action['url'] not in TARGETS:
            raise ValueError('undeclared_action')
        date=datetime.fromisoformat(action['retrieved_utc'])
        if date.utcoffset() is None or date.utcoffset().total_seconds()!=0:raise ValueError('action_receipt_not_utc')
        counts[action['kind']]+=1
        if counts[action['kind']]>declared['budgets'][action['kind']]:raise ValueError('action_budget_exhausted')
        if action['kind']=='open':
            if set(action)!={'index','kind','url','retrieved_utc','status'}:raise ValueError('action_schema_changed')
            if action['url'] in opened or action['status'] not in ('retrieved','unavailable'):raise ValueError('retry_or_bad_status')
            opened.add(action['url'])
            if action['status']=='retrieved':retrieved.add(action['url'])
        else:
            if set(action)!={'index','kind','url','retrieved_utc','pattern','matched'} or type(action['matched']) is not bool:
                raise ValueError('action_schema_changed')
            pair=(action['url'],action['pattern'])
            if action['url'] not in retrieved or action['pattern'] not in PATTERNS or pair in found:
                raise ValueError('undeclared_find_or_retry')
            found.add(pair)
    ids=set()
    for finding in research['findings']:
        if set(finding)!={'id','url','summary','limitation'} or finding['id'] in ids or finding['url'] not in retrieved:
            raise ValueError('invalid_attribution')
        if not all(isinstance(finding[k],str) and finding[k] for k in ('id','summary','limitation')):
            raise ValueError('empty_finding')
        ids.add(finding['id'])
    if research['market_requests']!=0 or research['orders_available'] is not False:raise ValueError('scope_changed')
    return dict(search=0,open=counts['open'],find=counts['find'],findings=len(ids))
