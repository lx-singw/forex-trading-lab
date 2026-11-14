"""Inspect bounded read-only timing exports; raw clock arithmetic is not age."""
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
from pathlib import Path
import re

from .metadata_probe_127 import integer, native

DATES = ('2026.10.19', '2026.10.20', '2026.10.21', '2026.10.22', '2026.10.23')
MAX_BYTES, MAX_QUERIES, MAX_US, MIN_SPACING_US = 8388608, 10800, 3600000000, 1000000
ZERO = '0' * 64
CYCLE = (('C', 'before'), ('T', 'quote'), ('C', 'after'))
CLOCK_FIELDS = ('time_current', 'time_trade_server', 'time_gmt', 'time_local', 'gmt_offset', 'daylight_savings')


def inspect_bytes(data):
    if type(data) is not bytes or not 0 < len(data) <= MAX_BYTES:
        raise ValueError('paired_size')
    try:
        text = data.decode('ascii')
    except UnicodeDecodeError:
        raise ValueError('paired_encoding') from None
    chunks = text.split('\r\n'); tail = chunks.pop()
    if len(chunks) > 21602 or any(len(l) > 2048 for l in chunks + [tail]):
        raise ValueError('paired_frame_bounds')
    if any('\r' in l or '\n' in l or any((ord(c) < 32 and c != '\t') or ord(c) == 127 for c in l)
           for l in chunks + ([tail.removesuffix('\r')] if tail else [])):
        raise ValueError('paired_framing')
    chain = ZERO; pending = None; terminal = None; kind = None; count = 0
    origin = last = None; last_poll_start = None; rows = []; stop_code = None

    def clock(seconds, micros):
        nonlocal last
        if (seconds < last[0] or micros < last[1] or micros - origin[1] > MAX_US
                or abs((seconds-origin[0]) - (micros-origin[1])//1000000) > 2):
            raise ValueError('paired_clock')
        try:
            date = datetime.fromtimestamp(seconds, timezone.utc).strftime('%Y.%m.%d')
        except (ValueError, OverflowError, OSError):
            raise ValueError('paired_clock_range') from None
        if date not in DATES:
            raise ValueError('paired_date')
        last = (seconds, micros)

    for line_no, line in enumerate(chunks):
        try:
            payload, digest = line.rsplit('\t', 1)
        except ValueError:
            raise ValueError('paired_checksum') from None
        if (not re.fullmatch('[0-9A-F]{64}', digest)
                or hashlib.sha256((chain+'\t'+payload+'\n').encode('ascii')).hexdigest().upper() != digest):
            raise ValueError('paired_checksum')
        chain = digest; f = payload.split('\t'); tag = f[0]
        if line_no == 0:
            if (len(f) != 6 or f[:2] != ['H', 'FXDL_PAIRED132_V1']
                    or f[2] not in ('market_declared', 'invented_fixture') or f[3] not in DATES):
                raise ValueError('paired_header')
            origin = (integer(f[4]), integer(f[5], 2**64-1)); last = origin; kind = f[2]
            if min(origin) <= 0:
                raise ValueError('paired_origin')
            clock(*origin)
            if datetime.fromtimestamp(origin[0], timezone.utc).strftime('%Y.%m.%d') != f[3]:
                raise ValueError('paired_header_date')
            continue
        if terminal is not None:
            raise ValueError('paired_after_terminal')
        if tag == 'A':
            if (len(f) != 4 or pending is not None or count >= MAX_QUERIES
                    or CYCLE[count % 3] != (f[2], f[3]) or integer(f[1], MAX_QUERIES) != count+1):
                raise ValueError('paired_attempt')
            count += 1; pending = (count, f[2], f[3]); continue
        if tag in ('C', 'T'):
            if len(f) != (17 if tag == 'C' else 19):
                raise ValueError('paired_outcome_fields')
            if pending is None or (integer(f[1], MAX_QUERIES), tag, f[2]) != pending:
                raise ValueError('paired_unmatched_outcome')
            bs, ats, gs, bu, au, gu = [integer(v, 2**64-1) for v in f[3:9]]
            if not bs <= ats <= gs or not bu <= au <= gu:
                raise ValueError('paired_receipt_order')
            for pair in ((bs, bu), (ats, au), (gs, gu)):
                clock(*pair)
            if f[9:11] != ['1', '0']:
                raise ValueError('paired_query_failed')
            row = {'sequence': count, 'type': tag, 'key': f[2],
                   'receipt_nominal_gmt_seconds': [bs, ats, gs], 'receipt_monotonic_us': [bu, au, gu]}
            values = f[11:]
            if tag == 'C':
                row['raw_clocks'] = dict(zip(CLOCK_FIELDS, [integer(v, signed=True) for v in values]))
                if f[2] == 'before':
                    if last_poll_start is not None and bu-last_poll_start < MIN_SPACING_US:
                        raise ValueError('paired_poll_spacing')
                    last_poll_start = bu
            else:
                seconds, millis = integer(values[0], 32535215999), integer(values[1], 32535215999999)
                bid, ask, price, real_volume = [Decimal(native(values[k])) for k in (2, 3, 4, 7)]
                if seconds <= 0 or millis//1000 != seconds or bid <= 0 or ask < bid or min(price, real_volume) < 0:
                    raise ValueError('paired_quote')
                row.update(source_seconds=seconds, source_millis=millis, bid_decimal=str(bid), ask_decimal=str(ask),
                           volume=integer(values[5], 2**64-1), raw_flags=integer(values[6], 2**32-1), source_age=None)
                row['native_bits'] = {k: values[j] for k, j in (('bid', 2), ('ask', 3), ('last', 4), ('volume_real', 7))}
            rows.append(row); pending = None; continue
        if tag == 'E':
            if len(f) != 4 or pending is not None or count != MAX_QUERIES or integer(f[1], MAX_QUERIES) != count:
                raise ValueError('paired_premature_end')
            clock(integer(f[2]), integer(f[3], 2**64-1)); terminal = 'complete'; continue
        if tag == 'S':
            if len(f) != 3 or not 2 <= integer(f[1], 20) <= 20 or integer(f[2], MAX_QUERIES) != count:
                raise ValueError('paired_stop')
            stop_code = int(f[1]); terminal = 'stopped'; continue
        raise ValueError('paired_record')
    if kind is None:
        raise ValueError('paired_header')
    if tail and terminal:
        raise ValueError('paired_tail_after_terminal')

    polls = []
    for index in range(0, len(rows)-2, 3):
        before, quote, after = rows[index:index+3]
        b, a = before['raw_clocks'], after['raw_clocks']; ms = quote['source_millis']
        polls.append({'poll': index//3+1, 'quote_sequence': quote['sequence'],
                      'raw_source_minus_time_current_ms': [ms-b['time_current']*1000, ms-a['time_current']*1000],
                      'raw_source_minus_time_trade_server_ms': [ms-b['time_trade_server']*1000, ms-a['time_trade_server']*1000],
                      'raw_server_minus_gmt_seconds': [b['time_trade_server']-b['time_gmt'], a['time_trade_server']-a['time_gmt']],
                      'raw_local_minus_gmt_seconds': [b['time_local']-b['time_gmt'], a['time_local']-a['time_gmt']],
                      'arithmetic_is_quote_age': False})
    quotes = [r for r in rows if r['type'] == 'T']
    def snapshot(r):
        return (r['source_seconds'], r['source_millis'], r['native_bits'], r['volume'], r['raw_flags'])
    advances = reversals = repeats = same_time_changed = 0
    repeat_start = None; longest_repeat_us = 0
    for prior, current in zip(quotes, quotes[1:]):
        delta = current['source_millis']-prior['source_millis']
        advances += delta > 0; reversals += delta < 0
        same = snapshot(prior) == snapshot(current)
        repeats += same; same_time_changed += delta == 0 and not same
        if same:
            if repeat_start is None:
                repeat_start = prior['receipt_monotonic_us'][0]
            longest_repeat_us = max(longest_repeat_us, current['receipt_monotonic_us'][0]-repeat_start)
        else:
            repeat_start = None
    clocks = [r for r in rows if r['type'] == 'C']
    clock_changes = {key: {'advances': sum(b['raw_clocks'][key] > a['raw_clocks'][key] for a, b in zip(clocks, clocks[1:])),
                           'reversals': sum(b['raw_clocks'][key] < a['raw_clocks'][key] for a, b in zip(clocks, clocks[1:]))}
                     for key in CLOCK_FIELDS}
    return {'schema': 'paired_recorder132_inspection_v1', 'declared_kind': kind, 'capture_status': terminal or 'incomplete',
            'stop_code': stop_code, 'queries_attempted': count, 'queries_recorded': len(rows), 'quotes_recorded': len(quotes),
            'completed_polls': len(polls), 'pending_attempt': pending is not None, 'truncated_tail': bool(tail),
            'origin_nominal_gmt_seconds': origin[0], 'origin_monotonic_us': origin[1],
            'rows': rows, 'paired_raw_arithmetic': polls, 'raw_clock_changes': clock_changes,
            'source_label_advances': advances, 'source_label_reversals': reversals, 'adjacent_identical_snapshots': repeats,
            'same_time_changed_snapshots': same_time_changed,
            'longest_observed_repeat_span_us': longest_repeat_us if len(quotes) >= 2 else None,
            'repeat_span_is_quote_age': False, 'chain_head': chain, 'export_sha256': hashlib.sha256(data).hexdigest(),
            'source_utc_certified': False, 'receipt_utc_certified': False, 'source_age': None,
            'tick_delivery_complete': False, 'executable_freshness_certified': False, 'historical_timezone_rule_established': False,
            'market_data_qualified': False, 'paper_evaluation_available': False, 'orders_available': False,
            'real_money_execution_available': False, 'producer_authenticated': False}


def inspect_file(path):
    p = Path(path)
    if p.is_symlink() or not p.is_file() or p.stat().st_size > MAX_BYTES:
        raise ValueError('paired_file')
    with p.open('rb') as stream:
        data = stream.read(MAX_BYTES+1)
    return inspect_bytes(data)


def quality_report(data):
    """Reuse131 numerical reporting, keeping132 wire provenance and dates."""
    from .forward_quality_131 import _quality
    inspected = inspect_bytes(data)
    report = _quality('timing130', inspected)
    report['schema'] = 'paired_recorder132_quality_v1'
    report['format'] = 'paired132'
    report['wire_schema'] = inspected['schema']
    report['export_sha256'] = inspected['export_sha256']
    report['input_bytes'] = len(data)
    report['bounds'] = {'max_bytes': MAX_BYTES, 'max_queries': MAX_QUERIES, 'max_elapsed_us': MAX_US,
                        'minimum_poll_spacing_us': MIN_SPACING_US, 'nominal_dates': list(DATES)}
    return report


def quality_markdown(report):
    from .forward_quality_131 import render_markdown
    bundle = {'sources': [{'id': 'paired132',
                          'files': [{'path': 'Paired132.txt', 'sha256': report['export_sha256'],
                                     'bytes': report['input_bytes']}],
                          'quality': report}]}
    heading = ('# Paired forward recorder132 quality\n\n'
               f"Declared input kind: **{report['declared_kind']}**. Producer identity is unverified; no trading admission.")
    return render_markdown(bundle).replace('# Forward recorder quality report131', heading, 1)
