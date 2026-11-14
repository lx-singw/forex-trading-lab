"""Strict sanitized native clock records and bounded runtime state; no orders."""
from datetime import datetime,timezone
import json
import math
from .fresh_data_031 import guard,ProbeRejected

DATE='2026-10-06';VERSION='clock_observer_042_v1';PREFIX='FXDL_CLOCK042 '
BASE={'version','accepted','reason_code','quote_reads'}
INTEGER_FIELDS={'guard_checks','time_current_before_s','time_current_after_s','calculated_server_before_s',
    'calculated_server_after_s','gmt_before_s','gmt_after_s','local_before_s','local_after_s',
    'tick_time_s','tick_time_msc','tick_flags','elapsed_us'}
SUCCESS=BASE|INTEGER_FIELDS|{'bid','ask'}

def date_guard():
    if datetime.now(timezone.utc).date().isoformat()!=DATE:raise ValueError('declared_date_expired')

def runtime_guard(api,identity=None):
    current=guard(api,identity)
    if current[0]<=0 or not current[1]:raise ProbeRejected('account_changed_or_invalid')
    info=api.symbol_info('EURUSD')
    if info is None or info.visible is not True or info.currency_base!='EUR' or info.currency_profit!='USD':
        raise ProbeRejected('symbol_not_supported_or_visible')
    guard(api,current)
    return current

def unique_pairs(pairs):
    out={}
    for key,value in pairs:
        if key in out:raise ValueError('duplicate_native_key')
        out[key]=value
    return out

def parse_record(text):
    if not isinstance(text,str) or len(text)>8192 or not text.startswith(PREFIX):raise ValueError('invalid_native_prefix')
    try:r=json.loads(text[len(PREFIX):],object_pairs_hook=unique_pairs)
    except Exception:raise ValueError('invalid_native_json') from None
    if not isinstance(r,dict) or set(r)!=(SUCCESS if r.get('accepted') is True else BASE):raise ValueError('native_schema_changed')
    if r['version']!=VERSION or type(r['accepted']) is not bool:raise ValueError('native_version_or_boolean_changed')
    if type(r['reason_code']) is not int or type(r['quote_reads']) is not int or r['quote_reads'] not in (0,1):raise ValueError('native_counter_invalid')
    if not r['accepted']:
        if not 1<=r['reason_code']<=19 or r['reason_code']==17 and r['quote_reads']!=0:raise ValueError('native_rejection_invalid')
        return r
    if r['reason_code']!=0 or r['quote_reads']!=1 or r['guard_checks']!=5:raise ValueError('native_success_unsupported')
    if any(type(r[k]) is not int for k in INTEGER_FIELDS):raise ValueError('native_integer_invalid')
    for prefix in ('time_current','calculated_server','gmt','local'):
        b,a=r[prefix+'_before_s'],r[prefix+'_after_s']
        if not 0<b<=a<=32535215999:raise ValueError('native_clock_invalid')
    if not 0<r['tick_time_s']<=32535215999 or not 0<r['tick_time_msc']<=32535215999999 or r['tick_time_msc']//1000!=r['tick_time_s']:
        raise ValueError('native_tick_clock_invalid')
    if not 0<=r['tick_flags']<=4294967295 or not 0<=r['elapsed_us']<=15000000:raise ValueError('native_flags_or_timeout_invalid')
    if any(type(r[k]) not in (int,float) or not math.isfinite(r[k]) for k in ('bid','ask')) or not 0<r['bid']<=r['ask']:
        raise ValueError('native_prices_invalid')
    for k in ('gmt_before_s','gmt_after_s'):
        if datetime.fromtimestamp(r[k],timezone.utc).date().isoformat()!=DATE:raise ValueError('native_date_expired')
    age=r['time_current_after_s']*1000-r['tick_time_msc']
    if not -2000<=age<=60000 or abs(r['tick_time_msc']-r['gmt_after_s']*1000)>86400000:raise ValueError('native_quote_age_invalid')
    if abs(r['gmt_after_s']-r['gmt_before_s']-r['elapsed_us']//1000000)>2:raise ValueError('native_wall_clock_discontinuity')
    return r

def records_from_log(raw):
    if not isinstance(raw,bytes) or len(raw)>1048576 or len(raw)%2:raise ValueError('native_log_chunk_invalid')
    text=raw.decode('utf-16-le',errors='strict');records=[]
    for line in text.splitlines():
        if PREFIX in line:
            if line.count(PREFIX)!=1:raise ValueError('ambiguous_native_prefix')
            records.append(parse_record(line[line.index(PREFIX):]))
    return records

class RuntimeSequence:
    def __init__(self):self.arms=[];self.records=[];self.pending=None
    def arm(self,enabled):
        if type(enabled) is not bool or self.pending is not None or len(self.arms)>=2:raise ValueError('runtime_budget_or_order_invalid')
        if enabled:
            if self.records!=[dict(version=VERSION,accepted=False,reason_code=17,quote_reads=0)]:raise ValueError('disabled_proof_required')
        elif self.arms:raise ValueError('disabled_arm_repeated')
        self.pending=enabled;self.arms.append(enabled)
    def collect(self,records):
        if self.pending is None or len(records)!=1:raise ValueError('exactly_one_native_record_required')
        r=parse_record(PREFIX+json.dumps(records[0]));enabled=self.pending
        if not enabled and r!=dict(version=VERSION,accepted=False,reason_code=17,quote_reads=0):raise ValueError('disabled_run_read_or_reason_invalid')
        self.records.append(r);self.pending=None
        if enabled and not r['accepted']:raise ValueError('native_observer_guard_rejected')
        return r

def comparison(record):
    r=parse_record(PREFIX+json.dumps(record))
    if not r['accepted']:return None
    g0=r['gmt_before_s']*1000;g1=r['gmt_after_s']*1000+999
    def interval(prefix):return [r[prefix+'_before_s']*1000-g1,r[prefix+'_after_s']*1000+999-g0]
    return dict(raw_tick_minus_gmt_interval_ms=[r['tick_time_msc']-g1,r['tick_time_msc']-g0],
        time_current_minus_gmt_interval_ms=interval('time_current'),
        calculated_server_minus_gmt_interval_ms=interval('calculated_server'),
        local_minus_gmt_interval_ms=interval('local'),
        seconds_equal_floor_milliseconds=True,elapsed_us=r['elapsed_us'],
        historical_clock_certified=False,offset_correction_authorized=False)
