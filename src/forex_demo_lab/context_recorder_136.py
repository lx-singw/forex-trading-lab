"""Inspect the separate136 native wire offline. No UTC/cost/market admission."""
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import re

from .metadata_probe_127 import INTEGER_KEYS, DOUBLE_KEYS, STRING_KEYS, integer, native
from .cost_probe_128 import currency, signed32
from .paired_replay_133 import DENIED

DATES = tuple(f'2026.10.{day}' for day in range(26, 31))
MAX_BYTES, MAX_US, MAX_POLLS, MAX_QUERIES = 33_554_432, 14_400_000_000, 14_400, 43_604
MAX_FRAMES, DETAIL_LIMIT, ZERO = 87_762, 128, '0' * 64
PROPERTIES = tuple([('I', k) for k in INTEGER_KEYS] + [('D', k) for k in DOUBLE_KEYS] + [('V', k) for k in STRING_KEYS])
CYCLE = (('C', 'before'), ('T', 'quote'), ('C', 'after'))
CLOCK_FIELDS = ('time_current', 'time_trade_server', 'time_gmt', 'time_local', 'gmt_offset', 'daylight_savings')


def inspect_bytes(data):
    if type(data) is not bytes or not 0 < len(data) <= MAX_BYTES:
        raise ValueError('context136_size')
    try: chunks = data.decode('ascii').split('\r\n')
    except UnicodeDecodeError: raise ValueError('context136_encoding') from None
    tail = chunks.pop()
    if len(chunks) > MAX_FRAMES or any(len(line) > 2048 for line in chunks + [tail]):
        raise ValueError('context136_frame_bounds')
    if any('\r' in line or '\n' in line or any((ord(c) < 32 and c != '\t') or ord(c) == 127 for c in line)
           for line in chunks + ([tail.removesuffix('\r')] if tail else [])):
        raise ValueError('context136_framing')
    chain = ZERO; kind = origin = last = terminal = pending = active = None
    stop_code = None; attempted = polls = part = 0; last_poll_start = None
    rows, contexts, pairs, poll_rows = [], [], [], []
    remaining = 0; current_rule = None; total_tiers = 0

    def clock(seconds, micros):
        nonlocal last
        if (seconds < last[0] or micros < last[1] or micros - origin[1] > MAX_US
                or abs(seconds - origin[0] - (micros - origin[1]) // 1_000_000) > 2):
            raise ValueError('context136_clock')
        try: date = datetime.fromtimestamp(seconds, timezone.utc).strftime('%Y.%m.%d')
        except (OverflowError, ValueError, OSError): raise ValueError('context136_clock_range') from None
        if date not in DATES: raise ValueError('context136_date')
        last = (seconds, micros)

    def due():
        return polls < MAX_POLLS and polls % 3600 == 0 and len(contexts) == polls // 3600

    def expected():
        if active is not None:
            phase = active['_phase']
            if phase == 0: return ('C', 'context_before')
            if phase == 1: return PROPERTIES[active['_property']]
            if phase == 2: return ('W', f"{active['_day']}:{active['_index']}")
            if phase in (3, 4, 5, 6): return (('K', 'commissions'), ('M', 'buy'), ('M', 'sell'), ('C', 'context_after'))[phase - 3]
            return None
        return None if due() or polls == MAX_POLLS else CYCLE[part]

    def finish_rule():
        nonlocal current_rule, remaining
        active['commission_rules'].append(current_rule)
        current_rule = None; remaining -= 1
        if remaining == 0: active['commission_state'] = 'reported_rules'

    for line_no, line in enumerate(chunks):
        try: payload, checksum = line.rsplit('\t', 1)
        except ValueError: raise ValueError('context136_checksum') from None
        if (not re.fullmatch('[0-9A-F]{64}', checksum)
                or hashlib.sha256((chain + '\t' + payload + '\n').encode('ascii')).hexdigest().upper() != checksum):
            raise ValueError('context136_checksum')
        chain = checksum; f = payload.split('\t'); tag = f[0]
        if line_no == 0:
            if (len(f) != 6 or f[:2] != ['H', 'FXDL_CONTEXT136_V1']
                    or f[2] not in ('market_declared', 'invented_fixture') or f[3] not in DATES):
                raise ValueError('context136_header')
            origin = (integer(f[4]), integer(f[5], 2**64 - 1)); last = origin; kind = f[2]
            if min(origin) <= 0: raise ValueError('context136_origin')
            clock(*origin)
            if datetime.fromtimestamp(origin[0], timezone.utc).strftime('%Y.%m.%d') != f[3]:
                raise ValueError('context136_header_date')
            continue
        if terminal is not None: raise ValueError('context136_after_terminal')
        if tag == 'B':
            if (len(f) != 3 or active is not None or pending is not None or part != 0 or not due()
                    or len(contexts) >= 4 or integer(f[1], 4) != len(contexts) + 1 or integer(f[2], MAX_POLLS) != polls):
                raise ValueError('context136_context_begin')
            active = dict(index=len(contexts) + 1, polls_before=polls, complete=False, rows=[],
                          commission_state='not_observed', commission_rules=[], weekly_template_truncated=False,
                          _phase=0, _property=0, _day=0, _index=0)
            contexts.append(active); total_tiers = 0
            continue
        if tag == 'Z':
            if (len(f) != 3 or active is None or active['_phase'] != 7 or pending is not None
                    or remaining or current_rule is not None or integer(f[1], 4) != active['index']
                    or integer(f[2], MAX_QUERIES) != attempted):
                raise ValueError('context136_context_end')
            active['complete'] = True; active = None; continue
        if tag == 'A':
            if (len(f) != 4 or pending is not None or remaining or current_rule is not None
                    or attempted >= MAX_QUERIES or expected() != (f[2], f[3])
                    or integer(f[1], MAX_QUERIES) != attempted + 1):
                raise ValueError('context136_attempt')
            attempted += 1; pending = (attempted, f[2], f[3]); continue
        if tag in ('R', 'L'):
            if len(f) != (10 if tag == 'R' else 12): raise ValueError('context136_rule_payload_fields')
            if active is None or pending is not None or remaining <= 0 or active['_phase'] != 4:
                raise ValueError('context136_rule_order')
            commission_sequence = next(r['sequence'] for r in active['rows'] if r['type'] == 'K')
            if integer(f[1], MAX_QUERIES) != commission_sequence: raise ValueError('context136_rule_sequence')
            if tag == 'R':
                if len(f) != 10 or current_rule is not None or integer(f[2], 7) != len(active['commission_rules']):
                    raise ValueError('context136_rule_fields')
                tiers = integer(f[9], 16); total_tiers += tiers
                if total_tiers > 128: raise ValueError('context136_tier_limit')
                current_rule = dict(index=int(f[2]), currency=currency(f[3]),
                                    **dict(zip(('mode_range', 'mode_charge', 'mode_entry', 'mode_direction', 'mode_profit'),
                                               [signed32(v) for v in f[4:9]])), tier_count=tiers, tiers=[])
                if tiers == 0: finish_rule()
            else:
                if (len(f) != 12 or current_rule is None or integer(f[2], 7) != current_rule['index']
                        or integer(f[3], 15) != len(current_rule['tiers'])):
                    raise ValueError('context136_tier_fields')
                tier = dict(index=int(f[3]), mode=signed32(f[4]), volume_type=signed32(f[5]),
                            **dict(zip(('value', 'min_value', 'max_value', 'range_from', 'range_to'), [native(v) for v in f[6:11]])),
                            native_bits=f[6:11], currency=currency(f[11]))
                current_rule['tiers'].append(tier)
                if len(current_rule['tiers']) == current_rule['tier_count']: finish_rule()
            continue
        if tag in ('C', 'I', 'D', 'V', 'W', 'K', 'M', 'T'):
            lengths = {'C': 17, 'I': 12, 'D': 12, 'V': 12, 'W': 13, 'K': 12, 'M': 13, 'T': 19}
            if len(f) != lengths[tag]: raise ValueError('context136_outcome_fields')
            if pending is None or (integer(f[1], MAX_QUERIES), tag, f[2]) != pending:
                raise ValueError('context136_unmatched_outcome')
            bs, ats, gs, bu, au, gu = [integer(v, 2**64 - 1) for v in f[3:9]]
            if not bs <= ats <= gs or not bu <= au <= gu: raise ValueError('context136_receipt_order')
            for moment in ((bs, bu), (ats, au), (gs, gu)): clock(*moment)
            ok, error = bool(integer(f[9], 1)), integer(f[10], 2**31 - 1)
            if ok and error: raise ValueError('context136_query_error')
            row = dict(sequence=attempted, type=tag, key=f[2], receipt_nominal_gmt_seconds=[bs, ats, gs],
                       receipt_monotonic_us=[bu, au, gu], query_succeeded=ok, error_code=error,
                       context_index=active['index'] if active is not None else len(contexts))
            values = f[11:]
            if tag == 'C':
                if not ok: raise ValueError('context136_clock_failed')
                row['raw_clocks'] = dict(zip(CLOCK_FIELDS, [integer(v, signed=True) for v in values]))
                if active is None and f[2] == 'before':
                    if last_poll_start is not None and bu - last_poll_start < 1_000_000:
                        raise ValueError('context136_poll_spacing')
                    last_poll_start = bu
            elif tag in ('I', 'D', 'V'):
                if tag == 'I': value = integer(values[0], signed=True)
                elif tag == 'D': value = native(values[0]); row['native_bits'] = values[0]
                else:
                    if not re.fullmatch('[A-Z]{3}' if ok else 'NA', values[0]): raise ValueError('context136_currency')
                    value = values[0]
                if not ok and values[0] != ('0000000000000000' if tag == 'D' else 'NA' if tag == 'V' else '0'):
                    raise ValueError('context136_failed_property_payload')
                row['value'] = value if ok else None
            elif tag == 'W':
                a, b = [integer(v, signed=True) for v in values]
                if not ok and (a != 0 or b != 0): raise ValueError('context136_failed_session_payload')
                row.update(raw_from_seconds=a if ok else None, raw_to_seconds=b if ok else None)
                if ok and active['_index'] == 8: active['weekly_template_truncated'] = True
            elif tag == 'K':
                count = signed32(values[0])
                if count < -1 or ok and count > 8: raise ValueError('context136_commission_count')
                row['native_return_count'] = count
                active['commission_state'] = 'reported_empty' if ok and count == 0 else 'incomplete' if ok else 'query_failed'
                if ok: remaining = count
            elif tag == 'M':
                a, b = [Decimal(native(v)) for v in values]
                if min(a, b) < 0 or not ok and values != ['0000000000000000'] * 2:
                    raise ValueError('context136_margin_payload')
                row.update(initial_rate=str(a) if ok else None, maintenance_rate=str(b) if ok else None, native_bits=values)
            else:
                if not ok: raise ValueError('context136_quote_failed')
                seconds, millis = integer(values[0], 32535215999), integer(values[1], 32535215999999)
                bid, ask, price, real = [Decimal(native(values[k])) for k in (2, 3, 4, 7)]
                if seconds <= 0 or millis // 1000 != seconds or bid <= 0 or ask < bid or min(price, real) < 0:
                    raise ValueError('context136_quote')
                row.update(source_seconds=seconds, source_millis=millis, bid_decimal=str(bid), ask_decimal=str(ask),
                           volume=integer(values[5], 2**64 - 1), raw_flags=integer(values[6], 2**32 - 1), source_age=None,
                           native_bits={k: values[i] for k, i in (('bid', 2), ('ask', 3), ('last', 4), ('volume_real', 7))})
            rows.append(row); pending = None
            if active is not None:
                active['rows'].append(row); phase = active['_phase']
                if phase == 0: active['_phase'] = 1
                elif phase == 1:
                    active['_property'] += 1
                    if active['_property'] == len(PROPERTIES): active['_phase'] = 2
                elif phase == 2:
                    if ok and active['_index'] < 8: active['_index'] += 1
                    else:
                        active['_day'] += 1; active['_index'] = 0
                        if active['_day'] == 7: active['_phase'] = 3
                else: active['_phase'] += 1
            else:
                poll_rows.append(row); part += 1
                if part == 3:
                    polls += 1; part = 0
                    pairs.append(dict(poll=polls, context_index=len(contexts), before_sequence=poll_rows[0]['sequence'],
                                      quote_sequence=poll_rows[1]['sequence'], after_sequence=poll_rows[2]['sequence'],
                                      after_guard_offset_us=gu - origin[1]))
                    poll_rows = []
            continue
        if tag == 'E':
            if (len(f) != 5 or pending is not None or active is not None or remaining or current_rule is not None
                    or polls != MAX_POLLS or part != 0 or integer(f[1], MAX_QUERIES) != attempted
                    or integer(f[2], MAX_POLLS) != polls):
                raise ValueError('context136_premature_end')
            clock(integer(f[3]), integer(f[4], 2**64 - 1)); terminal = 'complete'; continue
        if tag == 'S':
            if (len(f) != 4 or not 2 <= integer(f[1], 22) <= 22 or integer(f[2], MAX_QUERIES) != attempted
                    or integer(f[3], MAX_POLLS) != polls):
                raise ValueError('context136_stop')
            terminal = 'stopped'; stop_code = int(f[1]); continue
        raise ValueError('context136_record')
    if kind is None: raise ValueError('context136_header')
    if tail and terminal is not None: raise ValueError('context136_tail_after_terminal')
    for context in contexts:
        for key in list(context):
            if key.startswith('_'): del context[key]
    if active is not None:
        active['remaining_commission_rules'] = remaining
        active['partial_commission_rule'] = current_rule
    return dict(schema='context_recorder136_inspection_v1', declared_kind=kind,
                capture_status=terminal or 'incomplete', stop_code=stop_code,
                origin_nominal_gmt_seconds=origin[0], origin_monotonic_us=origin[1],
                queries_attempted=attempted, queries_recorded=len(rows), completed_polls=polls,
                pending_attempt=pending is not None, pending_rule_payload=remaining > 0 or current_rule is not None,
                truncated_tail=bool(tail), incomplete_context=active is not None,
                quarantined_poll_rows=len(poll_rows), contexts=contexts, rows=rows, paired_polls=pairs,
                chain_head=chain, export_sha256=hashlib.sha256(data).hexdigest(), **DENIED)


def quality_report(data):
    parsed = inspect_bytes(data); quotes = [r for r in parsed['rows'] if r['type'] == 'T']
    events = []; repeats = reversals = changed = gaps = total = 0
    repeat_start = None; longest = 0
    def snapshot(q): return [q[k] for k in ('source_millis', 'native_bits', 'volume', 'raw_flags')]
    for a, b in zip(quotes, quotes[1:]):
        same = snapshot(a) == snapshot(b); reverse = b['source_millis'] < a['source_millis']
        modified = b['source_millis'] == a['source_millis'] and not same
        gap = b['receipt_monotonic_us'][0] - a['receipt_monotonic_us'][0]
        repeats += same; reversals += reverse; changed += modified; gaps += gap > 2_000_000
        if same:
            if repeat_start is None: repeat_start = a['receipt_monotonic_us'][0]
            longest = max(longest, b['receipt_monotonic_us'][0] - repeat_start)
        else: repeat_start = None
        if same or reverse or modified or gap > 2_000_000:
            total += 1
            if len(events) < DETAIL_LIMIT:
                events.append(dict(quote_sequence=b['sequence'], prior_quote_sequence=a['sequence'],
                                   receipt_gap_us=gap, repeated=same, source_reversal=reverse, same_time_changed=modified))
    contexts = []
    for context in parsed['contexts']:
        contexts.append({**context, 'sequential_observations_not_atomic_contract': True,
                         'applicable_USD_commission': None, 'applicable_USD_margin': None,
                         'holiday_calendar_established': False})
    return dict(schema='context_recorder136_quality_v1', declared_kind=parsed['declared_kind'],
                export_sha256=parsed['export_sha256'], input_bytes=len(data),
                capture_status=parsed['capture_status'], stop_code=parsed['stop_code'],
                queries_attempted=parsed['queries_attempted'], queries_recorded=parsed['queries_recorded'],
                completed_polls=parsed['completed_polls'], quote_observations=len(quotes), contexts=contexts,
                pending_attempt=parsed['pending_attempt'], pending_rule_payload=parsed['pending_rule_payload'],
                truncated_tail=parsed['truncated_tail'], incomplete_context=parsed['incomplete_context'],
                quarantined_poll_rows=parsed['quarantined_poll_rows'],
                origin_nominal_gmt_seconds=parsed['origin_nominal_gmt_seconds'], origin_monotonic_us=parsed['origin_monotonic_us'],
                last_paired_after_guard_offset_us=parsed['paired_polls'][-1]['after_guard_offset_us'] if parsed['paired_polls'] else None,
                adjacent_repeats=repeats, source_reversals=reversals, same_time_changed=changed,
                quote_receipt_gaps_over2s=gaps, longest_observed_repeat_span_us=longest if len(quotes) > 1 else None,
                repeat_span_is_age=False, event_count=total, events=events, event_detail_limit=DETAIL_LIMIT,
                event_details_truncated=total > len(events), source_offset_bounds=None,
                receipt_UTC_uncertainty_bounds=None, delivery_delay_bounds=None, complete_costs_established=False,
                native_to135_conversion_available=False, strategy_evaluated=False, financial_engine_events=0,
                profitability_established=False, **DENIED)


def markdown(report):
    lines = ['# Context recorder136 diagnostic quality', '', f"Declared kind: **{report['declared_kind']}**.", '',
             f"Status: {report['capture_status']}; stop code: {report['stop_code']}; paired polls: {report['completed_polls']}.",
             f"Quotes: {report['quote_observations']}; repeats: {report['adjacent_repeats']}; gaps over2s: {report['quote_receipt_gaps_over2s']}.", '',
             '| Context | Prior completed polls | Complete | Commission response |', '| --- | ---: | --- | --- |']
    lines += [f"| {c['index']} | {c['polls_before']} | {c['complete']} | {c['commission_state']} |" for c in report['contexts']]
    lines += ['', 'Context rows are sequential observations, not an atomic contract or future fee promise.',
              'Empty rules, failed queries and absent payloads remain distinct. Dollar fees/margin,',
              'source offset, receipt UTC uncertainty, delivery delay and quote age remain unknown.',
              'No native135 conversion, strategy return, market/paper admission or order capability.', '']
    return '\n'.join(lines)
