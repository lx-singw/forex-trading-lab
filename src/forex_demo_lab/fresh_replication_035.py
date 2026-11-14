"""Frozen source-hour diagnostic: one horizon, one four-hour tick range, one H1 range."""
import csv
from datetime import datetime, timezone
import hashlib
import io
import json
import math
from pathlib import Path

from .collection import SPEC_FIELDS
from .fresh_data_031 import guard, receipt, observation, ProbeRejected
from .fresh_ticks_032 import FIELDS, INTS, audit, response_hash

VERSION = 'four_source_hour_replication_035_v1'
START, END = 1791280800000, 1791295200000
HOURS = tuple(range(START, END, 3600000))
MAX_TICKS, MAX_BARS, MAX_BYTES = 100000, 10, 32*1024*1024
BAR_FIELDS = ('time','open','high','low','close','tick_volume','spread','real_volume')
BAR_INTS = {'time','tick_volume','spread','real_volume'}


def reservation():
    return dict(version=VERSION,start_raw_ms=START,end_raw_ms=END,
                bounds='inclusive_ticks_four_half_open_hours',maximum_requests=3,orders_available=False)


def reserve_output(output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    with (output/'reservation.json').open('x') as f:
        json.dump(reservation(),f,sort_keys=True); f.write('\n')
    return output


def numeric_layout(response, fields, integers):
    dtype = response.dtype
    if dtype.hasobject or tuple(dtype.names or ()) != fields or len(response.shape)!=1 or not 1<=dtype.itemsize<=128:
        raise ProbeRejected('unsupported_response_schema')
    parts, occupied = {}, set()
    for name in fields:
        part, offset = dtype.fields[name][:2]
        if part.kind not in (('i','u') if name in integers else ('f',)) or part.itemsize not in (
                (1,2,4,8) if name in integers else (4,8)):
            raise ProbeRejected('unsupported_response_schema')
        region=set(range(offset,offset+part.itemsize))
        if offset<0 or offset+part.itemsize>dtype.itemsize or occupied & region:
            raise ProbeRejected('unsupported_response_schema')
        occupied |= region
        parts[name]=dict(format=part.str,offset=offset,size=part.itemsize)
    return dict(itemsize=dtype.itemsize,fields=parts,padding_offsets=sorted(set(range(dtype.itemsize))-occupied))


def bar_audit(rows):
    errors=[]
    if len(rows)!=4: errors.append('expected_exactly_four_bars')
    if [r['time'] for r in rows]!=[h//1000 for h in HOURS]: errors.append('unexpected_bar_open_labels_or_order')
    for i,r in enumerate(rows):
        if not all(math.isfinite(r[k]) and r[k]>0 for k in ('open','high','low','close')) or not (
                r['low']<=min(r['open'],r['close'])<=max(r['open'],r['close'])<=r['high']):
            errors.append('invalid_bar_prices')
        if any(r[k]<0 for k in ('tick_volume','spread','real_volume')): errors.append('invalid_bar_auxiliary_fields')
    return dict(rows=len(rows),errors=errors)


def preserve(response, kind, output, meta):
    fields, integers, limit=(FIELDS, INTS, MAX_TICKS) if kind=='ticks' else (BAR_FIELDS, BAR_INTS, MAX_BARS)
    info=meta['reads'][-1]
    if response is None: raise ProbeRejected('api_returned_none')
    info.update(returned_rows=len(response),response_bytes=int(response.nbytes),
                response_sha256=response_hash(response),
                schema_fingerprint_sha256=hashlib.sha256(str(response.dtype.descr).encode()).hexdigest())
    if len(response)>limit: raise ProbeRejected('row_budget_exceeded')
    if response.nbytes>MAX_BYTES: raise ProbeRejected('response_byte_budget_exceeded')
    layout=numeric_layout(response,fields,integers)
    info['binary_layout']=layout
    rows=[{k:int(r[k]) if k in integers else float(r[k]) for k in fields} for r in response]
    text=io.StringIO(newline='')
    writer=csv.DictWriter(text,fieldnames=fields,lineterminator='\n')
    writer.writeheader(); writer.writerows(rows)
    serialized=text.getvalue().encode('utf-8')
    binary=response.tobytes()
    if len(binary)!=response.nbytes or len(binary)!=len(rows)*layout['itemsize']:
        raise ProbeRejected('binary_length_mismatch')
    if any(binary[i+o]!=0 for i in range(0,len(binary),layout['itemsize']) for o in layout['padding_offsets']):
        raise ProbeRejected('nonzero_response_padding_not_exported')
    used=sum(p.stat().st_size for p in output.iterdir() if p.is_file())
    if used+len(binary)+len(serialized)+65536>MAX_BYTES:
        raise ProbeRejected('serialized_evidence_budget_exceeded')
    with (output/(kind+'.bin')).open('xb') as f: f.write(binary)
    with (output/(kind+'.csv')).open('xb') as f: f.write(serialized)
    info.update(complete_original_preserved=True,binary_sha256=hashlib.sha256(binary).hexdigest(),
                csv_sha256=hashlib.sha256(serialized).hexdigest(),csv_bytes=len(serialized),
                audit=audit(rows,START,END) if kind=='ticks' else bar_audit(rows))
    return rows


def no_call(reason):
    return dict(version=VERSION,status='not_requested',stop_reason=reason,requests=0,reads=[],
        start_raw_ms=START,end_raw_ms=END,bounds='inclusive_ticks_four_half_open_hours',horizon=None,
        history_elapsed_ns=0,contract_snapshot=None,completion_receipt=None,
        source_clock_interpreted_as_utc=False,complete_market_history_verified=False,
        fresh_performance_eligible=False,annual_eligible=False,orders_available=False)


def capture(api, output, clock, start=START, end=END, *, prepared=False):
    if type(start) is not int or type(end) is not int or (start,end)!=(START,END):
        raise ValueError('Only the declared four source hours are permitted')
    output=Path(output)
    if prepared:
        if {p.name for p in output.iterdir()}!={'reservation.json'} or json.loads((output/'reservation.json').read_text())!=reservation():
            raise ValueError('Prepared reservation is not exclusively owned')
    else: reserve_output(output)
    meta=no_call(None)
    meta['package_version']=getattr(api,'__version__',None)
    try:
        receipt(clock()[0]); identity=guard(api)
        symbol=api.symbol_info('EURUSD')
        guard(api,identity); receipt(clock()[0])
        if symbol is None or symbol.visible is not True or symbol.currency_base!='EUR' or symbol.currency_profit!='USD':
            raise ProbeRejected('symbol_not_supported_or_visible')
        contract={k:getattr(symbol,k) for k in SPEC_FIELDS}
        if any(type(v) in (int,float) and not math.isfinite(v) for v in contract.values()):
            raise ProbeRejected('invalid_contract_snapshot')
        meta['contract_snapshot']=contract

        def read(kind, operation):
            guard(api,identity)
            before=clock(); receipt(before[0])
            if any(type(x) is not int or x<0 for x in before): raise ProbeRejected('invalid_receipt_clock')
            if meta['reads']:
                previous=meta['reads'][-1]['receipt_after']
                if before[0]<previous['utc_ms'] or before[1]<previous['monotonic_ns']:
                    raise ProbeRejected('receipt_clock_reversed_between_reads')
            info=dict(kind=kind,receipt_before=dict(utc_ms=before[0],monotonic_ns=before[1]),
                      receipt_after=None,elapsed_ns=None,complete_original_preserved=False)
            meta['reads'].append(info); meta['requests']+=1
            response=operation()
            after=clock()
            # Capture numeric SDK status before any subsequent guard API can reset it.
            try: info['api_error_code']=int(api.last_error()[0])
            except Exception: info['api_error_code']=None
            guard(api,identity); receipt(after[0])
            if any(type(x) is not int or x<0 for x in after) or after[0]<before[0] or after[1]<before[1]:
                raise ProbeRejected('receipt_clock_reversed_or_invalid')
            info.update(receipt_after=dict(utc_ms=after[0],monotonic_ns=after[1]),elapsed_ns=after[1]-before[1])
            if kind!='horizon': meta['history_elapsed_ns']+=info['elapsed_ns']
            return response,info,before,after

        quote,info,before,after=read('horizon',lambda:api.symbol_info_tick('EURUSD'))
        meta['horizon']=observation(0,quote,before,after)
        if info['api_error_code']!=1: raise ProbeRejected('horizon_api_error')
        if meta['horizon']['raw_time_msc']<=END: raise ProbeRejected('source_hour_not_completed')
        for kind,operation in (
            ('ticks',lambda:api.copy_ticks_range('EURUSD',datetime.fromtimestamp(START/1000,timezone.utc),
                     datetime.fromtimestamp(END/1000,timezone.utc),api.COPY_TICKS_ALL)),
            ('bars',lambda:api.copy_rates_range('EURUSD',api.TIMEFRAME_H1,
                     datetime.fromtimestamp(START//1000,timezone.utc),datetime.fromtimestamp(END//1000-1,timezone.utc)))):
            response,info,before,after=read(kind,operation)
            rows=preserve(response,kind,output,meta)
            guard(api,identity); receipt(clock()[0])
            if info['api_error_code']!=1: raise ProbeRejected('api_error_with_preserved_response')
            if info['elapsed_ns']>60000000000 or meta['history_elapsed_ns']>120000000000:
                raise ProbeRejected('soft_timeout_with_preserved_response')
            if not rows: raise ProbeRejected('empty_response')
            if info['audit'].get('error_counts') or info['audit'].get('errors'):
                raise ProbeRejected('original_row_validation_failed')
        guard(api,identity)
        completion=clock(); receipt(completion[0])
        if any(type(x) is not int or x<0 for x in completion) or completion[0]<after[0] or completion[1]<after[1]:
            raise ProbeRejected('completion_clock_reversed_or_invalid')
        meta['completion_receipt']=dict(utc_ms=completion[0],monotonic_ns=completion[1])
        meta['status']='four_source_hours_originals_preserved_and_rows_valid'
    except ProbeRejected as exc:
        meta['status'],meta['stop_reason']='stopped_replication',str(exc)
    except Exception:
        meta['status'],meta['stop_reason']='stopped_replication','api_or_runtime_failure_details_redacted'
    with (output/'capture.json').open('x') as f:
        json.dump(meta,f,indent=2,sort_keys=True,allow_nan=False); f.write('\n')
    return meta
