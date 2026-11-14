"""One guarded full-source quote sample, preserving binary and CSV originals."""
from collections import Counter
import csv
from datetime import datetime, timezone
import hashlib
import io
import json
import math
from pathlib import Path

from .collection import SPEC_FIELDS
from .fresh_data_031 import guard, receipt, ProbeRejected

VERSION = 'full_tick_sample_032_v1'
START, END = 1791293942000, 1791294003000
MAX_ROWS, MAX_BYTES = 20000, 4*1024*1024
FIELDS = ('time','bid','ask','last','volume','time_msc','flags','volume_real')
INTS = {'time','volume','time_msc','flags'}


def layout(response):
    dtype = response.dtype
    if dtype.hasobject or tuple(dtype.names or ()) != FIELDS or len(response.shape) != 1 or not 1 <= dtype.itemsize <= 128:
        raise ProbeRejected('unsupported_response_schema')
    fields, occupied = {}, set()
    for name in FIELDS:
        part, offset = dtype.fields[name][:2]
        if (part.kind not in ('i','u') if name in INTS else part.kind != 'f'):
            raise ProbeRejected('unsupported_response_schema')
        if part.itemsize not in (1,2,4,8) or name not in INTS and part.itemsize not in (4,8):
            raise ProbeRejected('unsupported_response_schema')
        region = set(range(offset,offset+part.itemsize))
        if occupied & region or offset < 0 or offset+part.itemsize > dtype.itemsize:
            raise ProbeRejected('unsupported_response_schema')
        occupied |= region
        fields[name] = dict(format=part.str,offset=offset,size=part.itemsize)
    return dict(itemsize=dtype.itemsize,fields=fields,
                padding_offsets=sorted(set(range(dtype.itemsize))-occupied))


def response_hash(response):
    try:
        if response.dtype.hasobject:
            return None
        try:
            view = memoryview(response).cast('B')
        except TypeError:
            if response.nbytes > MAX_BYTES:
                return None
            view = memoryview(response.tobytes())
        digest = hashlib.sha256()
        for i in range(0,len(view),65536):
            digest.update(view[i:i+65536])
        return digest.hexdigest()
    except Exception:
        return None


def audit(rows, start=START, end=END):
    errors, indices, ties, duplicates, gaps = Counter(), [], 0, 0, []
    previous = None
    for index,row in enumerate(rows):
        problems = []
        if not all(math.isfinite(row[k]) for k in ('bid','ask')) or not 0 < row['bid'] <= row['ask']:
            problems.append('invalid_prices')
        if row['time_msc'] <= 0 or row['time'] < 0 or row['time'] != row['time_msc']//1000:
            problems.append('timestamp_mismatch')
        if not start <= row['time_msc'] <= end:
            problems.append('outside_request')
        if row['volume'] < 0 or not 0 <= row['flags'] <= 2**32-1 or not all(
                math.isfinite(row[k]) and row[k] >= 0 for k in ('last','volume_real')):
            problems.append('invalid_auxiliary_fields')
        if previous is not None:
            delta = row['time_msc']-previous['time_msc']
            if delta < 0:
                problems.append('decreasing_labels')
            else:
                gaps.append(delta)
            ties += delta == 0
            duplicates += all(row[k] == previous[k] for k in FIELDS)
        errors.update(problems)
        if problems and len(indices) < 20:
            indices.append(dict(row_index=index,errors=problems))
        previous = row
    return dict(rows=len(rows),first_raw_time_msc=rows[0]['time_msc'] if rows else None,
        last_raw_time_msc=rows[-1]['time_msc'] if rows else None,
        same_millisecond_transitions=ties,exact_duplicate_transitions=duplicates,
        maximum_nonnegative_intertick_gap_ms=max(gaps,default=None),
        error_counts=dict(errors),first_error_indices=indices)


def reserve_output(output,start=START,end=END):
    if type(start) is not int or type(end) is not int or (start,end)!=(START,END) or not 0 < end-start <= 120000:
        raise ValueError('Only the frozen source-label interval is permitted')
    output = Path(output)
    output.mkdir(parents=True,exist_ok=False)
    reservation = dict(version=VERSION,start_raw_ms=start,end_raw_ms=end,
                       bounds='inclusive',maximum_requests=1,orders_available=False)
    with (output/'reservation.json').open('x') as f:
        json.dump(reservation,f,sort_keys=True); f.write('\n')
    return output


def capture(api, output, clock, start=START, end=END, *, prepared=False):
    if (start,end)!=(START,END):
        raise ValueError('Only the frozen source-label interval is permitted')
    output = Path(output)
    if prepared:
        expected=dict(version=VERSION,start_raw_ms=start,end_raw_ms=end,bounds='inclusive',maximum_requests=1,orders_available=False)
        if set(p.name for p in output.iterdir()) != {'reservation.json'} or json.loads((output/'reservation.json').read_text()) != expected:
            raise ValueError('Prepared reservation is not exclusively owned')
    else:
        reserve_output(output,start,end)
    meta = dict(version=VERSION,status='not_requested',stop_reason=None,requests=0,
        start_raw_ms=start,end_raw_ms=end,bounds='inclusive',contract_snapshot=None,
        receipt_before=None,receipt_after=None,elapsed_ns=None,returned_rows=None,
        response_bytes=None,response_sha256=None,binary_layout=None,audit=None,
        complete_original_preserved=False,source_clock_interpreted_as_utc=False,
        complete_market_history_verified=False,fresh_performance_eligible=False,
        annual_eligible=False,orders_available=False)
    meta['package_version'] = getattr(api,'__version__',None)
    try:
        receipt(clock()[0])
        identity = guard(api)
        symbol = api.symbol_info('EURUSD')
        guard(api,identity)
        if symbol is None or symbol.visible is not True or symbol.currency_base!='EUR' or symbol.currency_profit!='USD':
            raise ProbeRejected('symbol_not_supported_or_visible')
        contract = {k:getattr(symbol,k) for k in SPEC_FIELDS}
        if any(type(v) in (int,float) and not math.isfinite(v) for v in contract.values()):
            raise ProbeRejected('invalid_contract_snapshot')
        meta['contract_snapshot'] = contract
        guard(api,identity)
        before = clock()
        receipt(before[0])
        meta['receipt_before'] = dict(utc_ms=before[0],monotonic_ns=before[1])
        meta['requests'] = 1
        response = api.copy_ticks_range('EURUSD',datetime.fromtimestamp(start/1000,timezone.utc),
                                       datetime.fromtimestamp(end/1000,timezone.utc),api.COPY_TICKS_ALL)
        after = clock()
        meta['receipt_after'] = dict(utc_ms=after[0],monotonic_ns=after[1])
        meta['elapsed_ns'] = after[1]-before[1]
        try:
            meta['api_error_code'] = int(api.last_error()[0])  # No free-text details.
        except Exception:
            meta['api_error_code'] = None
        guard(api,identity)
        receipt(after[0])
        if after[0] < before[0] or meta['elapsed_ns'] < 0:
            raise ProbeRejected('receipt_clock_reversed')
        if response is None:
            raise ProbeRejected('api_returned_none')
        meta['returned_rows'],meta['response_bytes'] = len(response),int(response.nbytes)
        meta['response_sha256'] = response_hash(response)
        meta['schema_fingerprint_sha256'] = hashlib.sha256(str(response.dtype.descr).encode()).hexdigest()
        if len(response)>MAX_ROWS:
            raise ProbeRejected('row_budget_exceeded')
        if response.nbytes>MAX_BYTES:
            raise ProbeRejected('response_byte_budget_exceeded')
        meta['binary_layout'] = layout(response)
        rows = [{k:int(r[k]) if k in INTS else float(r[k]) for k in FIELDS} for r in response]
        text = io.StringIO(newline='')
        writer = csv.DictWriter(text,fieldnames=FIELDS,lineterminator='\n')
        writer.writeheader(); writer.writerows(rows)
        csv_bytes = text.getvalue().encode('utf-8')
        binary = response.tobytes()
        size = meta['binary_layout']['itemsize']
        if any(binary[i+o] != 0 for i in range(0,len(binary),size)
               for o in meta['binary_layout']['padding_offsets']):
            raise ProbeRejected('nonzero_response_padding_not_exported')
        if len(binary)!=response.nbytes or len(csv_bytes)+len(binary)+65536>MAX_BYTES:
            raise ProbeRejected('serialized_evidence_budget_exceeded')
        with (output/'response.bin').open('xb') as f:f.write(binary)
        with (output/'raw.csv').open('xb') as f:f.write(csv_bytes)
        meta.update(complete_original_preserved=True,
            csv_sha256=hashlib.sha256(csv_bytes).hexdigest(),csv_bytes=len(csv_bytes),
            binary_sha256=hashlib.sha256(binary).hexdigest(),audit=audit(rows,start,end))
        guard(api,identity)
        if meta['api_error_code']!=1:
            raise ProbeRejected('api_error_with_preserved_response')
        if meta['elapsed_ns']>60_000_000_000:
            raise ProbeRejected('soft_timeout_with_preserved_response')
        if not rows:
            raise ProbeRejected('empty_response')
        if meta['audit']['error_counts']:
            raise ProbeRejected('original_row_validation_failed')
        meta['status'] = 'sample_preserved_and_rows_valid'
    except ProbeRejected as exc:
        meta['status'],meta['stop_reason'] = 'stopped_sample',str(exc)
    except Exception:
        meta['status'],meta['stop_reason'] = 'stopped_sample','api_or_runtime_failure_details_redacted'
    with (output/'capture.json').open('x') as f:
        json.dump(meta,f,indent=2,sort_keys=True,allow_nan=False); f.write('\n')
    return meta
