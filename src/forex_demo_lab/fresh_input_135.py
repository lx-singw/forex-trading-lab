"""Causal interval contract prototype. Invented inputs only; no financial engine."""
from copy import deepcopy
from pathlib import Path
import re
import struct

from .model import Config
from dataclasses import asdict
from .shadow_engine_113 import scenarios
from .paired_replay_133 import DENIED, canonical, digest, strict_json

SCHEMA = 'fresh_input135_v1'
MAX_BYTES, MAX_EVENTS = 8 * 1024 * 1024, 20_000
MAX_MONO = 90 * 86400 * 1_000_000
MIN_UTC, MAX_UTC = 946684800000000, 4102444800000000
HOUR = 3_600_000_000
BASES = ('unknown', 'declared_assumption', 'invented_measurement')


def expected_policy():
    return dict(schema=SCHEMA + '_policy', max_age_us=2_000_000,
                gap_notice_us=2_000_000, max_clock_valid_us=HOUR,
                max_terms_valid_us=24 * HOUR, max_calendar_valid_us=24 * HOUR,
                max_post_marker_delay_us=60_000_000, max_receipt_drift_ppm=1000,
                hypothetical_contract=asdict(Config()), hypothetical_cost_scenarios=scenarios())


def _keys(value, fields):
    if type(value) is not dict or set(value) != set(fields):
        raise ValueError('contract_fields')


def _int(value, low, high):
    if type(value) is not int or not low <= value <= high:
        raise ValueError('contract_integer')
    return value


def _interval(value, low, high):
    if type(value) is not list or len(value) != 2:
        raise ValueError('contract_interval')
    a, b = (_int(v, low, high) for v in value)
    if a > b:
        raise ValueError('contract_interval_order')
    return [a, b]


def _basis(value):
    if type(value) is not str or value not in BASES:
        raise ValueError('contract_basis')


def _quantity(basis, value, low, high):
    _basis(basis)
    if basis == 'unknown':
        if value is not None:
            raise ValueError('unknown_must_be_null')
        return None
    return _interval(value, low, high)


def _price(bits):
    if type(bits) is not str or not re.fullmatch('[0-9A-F]{16}', bits):
        raise ValueError('contract_native_bits')
    value = struct.unpack('>d', bytes.fromhex(bits))[0]
    if not 0 < value < float('inf'):
        raise ValueError('contract_price')
    return value


def _receipt(clock, at):
    if clock is None or clock['receipt_utc_us'] is None or not clock['observed_us'] <= at <= clock['observed_us'] + clock['valid_for_us']:
        return None
    delta = at - clock['observed_us']
    # Round outward: even a fractional microsecond expands the uncertainty.
    drift = (delta * clock['receipt_drift_ppm'] + 999_999) // 1_000_000
    return [clock['receipt_utc_us'][0] + delta - drift,
            clock['receipt_utc_us'][1] + delta + drift]


def _active(event, at):
    return event is not None and event['observed_us'] <= at <= event['observed_us'] + event['valid_for_us']


def _session(calendar, availability, at):
    if availability is None or not _active(calendar, at) or calendar['basis'] == 'unknown':
        return 'unknown'
    low, high = availability
    if any(start <= low and high < end for start, end in calendar['sessions_utc_us']):
        return 'open_under_declared_bounds'
    if any(low < end and high >= start for start, end in calendar['sessions_utc_us']):
        return 'ambiguous_boundary'
    return 'closed_under_declared_bounds'


def _runtime():
    root = Path(__file__).parent
    names = ('fresh_input_135.py', 'paired_replay_133.py', 'shadow_engine_113.py', 'model.py')
    return {n: digest((root / n).read_bytes()) for n in names}


class Replay:
    """Pull/ack with derived state rebuilt from committed inputs on restore.

    Interval bases are labels on invented evidence, not authentication. This
    class neither accepts market captures nor authorizes a strategy or order.
    """
    def __init__(self, raw, raw_policy):
        policy = strict_json(raw_policy, 65_536)
        if canonical(policy) != canonical(expected_policy()):
            raise ValueError('frozen_contract_policy')
        fixture = strict_json(raw, MAX_BYTES)
        _keys(fixture, ('schema', 'kind', 'run', 'symbol', 'events'))
        if fixture['schema'] != SCHEMA or fixture['kind'] != 'invented_fixture' or fixture['symbol'] != 'EURUSD':
            raise ValueError('invented_contract_required')
        _int(fixture['run'], 1, 64)
        if type(fixture['events']) is not list or not 1 <= len(fixture['events']) <= MAX_EVENTS:
            raise ValueError('contract_event_count')
        self._events = [canonical(e) for e in fixture['events']]
        self._input_hash, self._policy_hash = digest(raw), digest(raw_policy)
        self._policy, self._runtime = policy, _runtime()
        header = {k: fixture[k] for k in ('schema', 'kind', 'run', 'symbol')}
        self._chain = digest(canonical(dict(header=header, policy=policy, runtime=self._runtime)))
        self._index, self._verdicts = 0, []
        self._state = dict(last_us=0, clock=None, clock_generation=0, terms=None,
                           calendar=None, last_quote=None, source_highwater=None, pending_review=[])

    def peek(self):
        return None if self._index == len(self._events) else strict_json(self._events[self._index], MAX_BYTES)

    def _evaluate(self, event):
        _keys(event, {'clock': ('type', 'sequence', 'observed_us', 'receipt_basis', 'receipt_utc_us',
                               'receipt_drift_ppm', 'source_basis', 'source_to_utc_us',
                               'source_label_range_msc', 'valid_for_us'),
                      'terms': ('type', 'sequence', 'observed_us', 'contract_basis', 'contract_profile',
                                'cost_basis', 'cost_profile', 'valid_for_us'),
                      'calendar': ('type', 'sequence', 'observed_us', 'basis', 'sessions_utc_us', 'valid_for_us'),
                      'quote': ('type', 'sequence', 'observed_us', 'acquired_us', 'source_msc',
                                'bid_bits', 'ask_bits', 'raw_flags', 'delay_basis', 'post_marker_delay_us')
                      }.get(event.get('type') if type(event) is dict and type(event.get('type')) is str else None, ()))
        kind = event.get('type')
        if kind not in ('clock', 'terms', 'calendar', 'quote'):
            raise ValueError('contract_event_type')
        if _int(event['sequence'], 1, MAX_EVENTS) != self._index + 1:
            raise ValueError('contract_sequence')
        now = _int(event['observed_us'], 0, MAX_MONO)
        if now < self._state['last_us']:
            raise ValueError('monotonic_reset_requires_new_run')
        state = deepcopy(self._state); state['last_us'] = now
        verdict = dict(type=kind, sequence=event['sequence'], observed_us=now,
                       evidence_scope='invented_contract_software_check', **DENIED)
        if kind == 'clock':
            _quantity(event['receipt_basis'], event['receipt_utc_us'], MIN_UTC, MAX_UTC)
            _quantity(event['source_basis'], event['source_to_utc_us'], -24 * HOUR, 24 * HOUR)
            _int(event['receipt_drift_ppm'], 0, self._policy['max_receipt_drift_ppm'])
            _int(event['valid_for_us'], 0, self._policy['max_clock_valid_us'])
            if event['source_basis'] == 'unknown':
                if event['source_label_range_msc'] is not None:
                    raise ValueError('unknown_source_scope')
            else:
                _interval(event['source_label_range_msc'], MIN_UTC // 1000, MAX_UTC // 1000)
            old = state['clock']; predicted = _receipt(old, now)
            fresh = event['receipt_utc_us']
            continuity = 'initial' if old is None else 'unverifiable'
            if old and predicted is not None and fresh is not None:
                continuity = 'bounds_overlap' if max(predicted[0], fresh[0]) <= min(predicted[1], fresh[1]) else 'disjoint_bounds'
                if old['source_to_utc_us'] is None or event['source_to_utc_us'] is None:
                    if continuity != 'disjoint_bounds': continuity = 'unverifiable'
                elif max(old['source_to_utc_us'][0], event['source_to_utc_us'][0]) > min(old['source_to_utc_us'][1], event['source_to_utc_us'][1]):
                    continuity = 'disjoint_bounds'
            if old and continuity != 'bounds_overlap':
                state['pending_review'].append('clock_mapping_' + continuity)
            state['clock'] = deepcopy(event); state['clock_generation'] += 1
            verdict.update(clock_generation=state['clock_generation'], continuity=continuity,
                           receipt_basis=event['receipt_basis'], source_basis=event['source_basis'])
        elif kind == 'terms':
            _int(event['valid_for_us'], 0, self._policy['max_terms_valid_us'])
            for field, profile in (('contract', 'baseline_113'), ('cost', 'base_and_adverse_113')):
                _basis(event[field + '_basis'])
                expected = None if event[field + '_basis'] == 'unknown' else profile
                if event[field + '_profile'] != expected:
                    raise ValueError('contract_terms_profile')
            state['terms'] = deepcopy(event)
            verdict.update(contract_basis=event['contract_basis'], cost_basis=event['cost_basis'])
        elif kind == 'calendar':
            _basis(event['basis']); _int(event['valid_for_us'], 0, self._policy['max_calendar_valid_us'])
            sessions = event['sessions_utc_us']
            if event['basis'] == 'unknown':
                if sessions is not None: raise ValueError('unknown_calendar_scope')
            else:
                if type(sessions) is not list or len(sessions) > 32:
                    raise ValueError('contract_sessions')
                previous_end = None
                for session in sessions:
                    start, end = _interval(session, MIN_UTC, MAX_UTC)
                    if start == end or previous_end is not None and start < previous_end:
                        raise ValueError('contract_session_order')
                    previous_end = end
            state['calendar'] = deepcopy(event); verdict['calendar_basis'] = event['basis']
        else:
            _int(event['acquired_us'], 0, now)
            _int(event['source_msc'], MIN_UTC // 1000, MAX_UTC // 1000)
            _int(event['raw_flags'], 0, 2**32 - 1)
            if _price(event['ask_bits']) < _price(event['bid_bits']):
                raise ValueError('contract_crossed_quote')
            delay = _quantity(event['delay_basis'], event['post_marker_delay_us'], 0, self._policy['max_post_marker_delay_us'])
            reasons, review = [], list(state['pending_review'])
            state['pending_review'] = []
            clock, terms = state['clock'], state['terms']
            horizon = now if delay is None else now + delay[1]
            lower = None if delay is None else _receipt(clock, now + delay[0])
            upper = None if delay is None else _receipt(clock, horizon)
            availability = None if lower is None or upper is None else [lower[0], upper[1]]
            source = None
            if delay is None: reasons.append('post_marker_delay_unknown')
            if not _active(clock, horizon): reasons.append('clock_missing_or_expired')
            elif clock['receipt_utc_us'] is None: reasons.append('receipt_utc_unknown')
            if clock is None or clock['source_to_utc_us'] is None:
                reasons.append('source_mapping_unknown')
            elif not clock['source_label_range_msc'][0] <= event['source_msc'] <= clock['source_label_range_msc'][1]:
                reasons.append('source_mapping_out_of_scope')
            elif _active(clock, horizon):
                source = [event['source_msc'] * 1000 + n for n in clock['source_to_utc_us']]
            if source is not None and not MIN_UTC <= source[0] <= source[1] <= MAX_UTC:
                source = None; reasons.append('source_utc_out_of_range')
            if availability is not None and not MIN_UTC <= availability[0] <= availability[1] <= MAX_UTC:
                availability = None; reasons.append('availability_utc_out_of_range')
            age = None if availability is None or source is None else [availability[0] - source[1], availability[1] - source[0]]
            if age is None: age_state = 'unknown'
            elif age[1] < 0: age_state = 'definitely_future'
            elif age[0] < 0: age_state = 'possibly_future'
            elif age[0] > self._policy['max_age_us']: age_state = 'definitely_stale'
            elif age[1] > self._policy['max_age_us']: age_state = 'possibly_stale'
            else: age_state = 'within_declared_bounds'
            if age_state != 'within_declared_bounds': reasons.append('age_' + age_state)
            hour = None
            if availability is not None:
                if availability[0] // HOUR == availability[1] // HOUR: hour = availability[0] // HOUR
                else: reasons.append('receipt_hour_ambiguous'); review.append('receipt_hour_ambiguous')
            if not _active(terms, horizon): reasons.append('terms_missing_or_expired')
            elif terms['contract_profile'] is None or terms['cost_profile'] is None: reasons.append('contract_or_cost_unknown')
            session = _session(state['calendar'], availability, horizon)
            if session != 'open_under_declared_bounds': reasons.append('session_' + session)
            prior = state['last_quote']; gap = None if prior is None else now - prior['observed_us']
            same = prior is not None and all(event[k] == prior[k] for k in ('source_msc', 'bid_bits', 'ask_bits', 'raw_flags'))
            reversal = prior is not None and event['source_msc'] < prior['source_msc']
            below = state['source_highwater'] is not None and event['source_msc'] < state['source_highwater']
            changed = prior is not None and event['source_msc'] == prior['source_msc'] and not same
            for fault, reason in ((gap is not None and gap > self._policy['gap_notice_us'], 'sampling_gap'),
                                  (reversal, 'source_reversal'), (below, 'source_below_highwater'),
                                  (changed, 'same_source_changed_payload')):
                if fault: reasons.append(reason); review.append(reason)
            if review: reasons += review
            state['last_quote'] = deepcopy(event)
            state['source_highwater'] = event['source_msc'] if state['source_highwater'] is None else max(state['source_highwater'], event['source_msc'])
            verdict.update(original_quote=deepcopy(event), availability_utc_us=availability,
                           source_utc_us=source, estimated_age_bounds_us=age, age_state=age_state,
                           receipt_h1_index=hour, clock_generation=state['clock_generation'],
                           receipt_basis=None if clock is None else clock['receipt_basis'],
                           source_basis=None if clock is None else clock['source_basis'], delay_basis=event['delay_basis'],
                           calendar_state=session, quote_marker_gap_us=gap, repeated_snapshot=same,
                           source_reversal=reversal, source_below_highwater=below, same_source_changed_payload=changed,
                           reasons=sorted(set(reasons)), hypothetical_input_usable=not reasons,
                           risk_observation_retained=True, requires_history_review=bool(review),
                           history_review_reasons=sorted(set(review)), full_strategy_entry_permission=False)
        return state, verdict

    def ack(self, event):
        if type(event) is not dict:
            raise ValueError('contract_ack')
        try: encoded = canonical(event)
        except (ValueError, TypeError, OverflowError, RecursionError):
            raise ValueError('contract_ack') from None
        if self._index and encoded == self._events[self._index - 1]:
            return deepcopy(self._verdicts[-1])
        if self._index == len(self._events) or encoded != self._events[self._index]:
            raise ValueError('contract_ack_order')
        state, verdict = self._evaluate(event)
        chain = digest(self._chain.encode('ascii') + b'\n' + encoded)
        verdict['causal_prefix_sha256'] = chain
        self._state, self._chain = state, chain
        self._verdicts.append(verdict); self._index += 1
        return deepcopy(verdict)

    def checkpoint(self):
        state = dict(schema=SCHEMA + '_cursor', input_sha256=self._input_hash,
                     policy_sha256=self._policy_hash, runtime=self._runtime,
                     committed_events=self._index, causal_prefix_sha256=self._chain)
        return canonical(dict(state=state, checksum=digest(canonical(state))))

    @classmethod
    def restore(cls, raw, raw_policy, checkpoint):
        saved = strict_json(checkpoint, 16_384)
        _keys(saved, ('state', 'checksum')); _keys(saved['state'], ('schema', 'input_sha256', 'policy_sha256', 'runtime', 'committed_events', 'causal_prefix_sha256'))
        result = cls(raw, raw_policy)
        count = _int(saved['state']['committed_events'], 0, len(result._events))
        for _ in range(count): result.ack(result.peek())
        if canonical(saved) != result.checkpoint():
            raise ValueError('contract_checkpoint_binding_or_integrity')
        return result

    def report(self):
        if self._index != len(self._events):
            raise ValueError('contract_not_exhausted')
        quotes = [v for v in self._verdicts if v['type'] == 'quote']
        return dict(schema=SCHEMA + '_report', kind='invented_software_check',
                    input_sha256=self._input_hash, policy_sha256=self._policy_hash, runtime=deepcopy(self._runtime),
                    committed_events=self._index, causal_prefix_sha256=self._chain,
                    quote_observations=len(quotes), usable_under_invented_bounds=sum(v['hypothetical_input_usable'] for v in quotes),
                    risk_observations_retained=sum(v['risk_observation_retained'] for v in quotes),
                    history_reviews=sum(v['requires_history_review'] for v in quotes),
                    verdicts=deepcopy(self._verdicts), financial_engine_events=0,
                    strategy_evaluated=False, profitability_established=False,
                    measurements_are_synthetic=True, native_capture_conversion_available=False, **DENIED)

    def run(self):
        while (event := self.peek()) is not None: self.ack(event)
        return self.report()


def invented_cases():
    """Fixed demonstration matrix, not market data or strategy outcomes."""
    utc = 1704067800000000  # invented2024-01-01 00:10UTC anchor
    offset = -10_800_000_000
    base = [dict(type='clock', sequence=1, observed_us=0, receipt_basis='declared_assumption',
                 receipt_utc_us=[utc, utc], receipt_drift_ppm=0, source_basis='declared_assumption',
                 source_to_utc_us=[offset, offset], source_label_range_msc=[utc // 1000 - offset // 1000 - 10_000, utc // 1000 - offset // 1000 + 3_600_000], valid_for_us=HOUR),
            dict(type='terms', sequence=2, observed_us=0, contract_basis='declared_assumption', contract_profile='baseline_113',
                 cost_basis='declared_assumption', cost_profile='base_and_adverse_113', valid_for_us=HOUR),
            dict(type='calendar', sequence=3, observed_us=0, basis='declared_assumption',
                 sessions_utc_us=[[utc - HOUR, utc + HOUR]], valid_for_us=HOUR)]
    def quote(sequence=4, at=1_000_000, age=100_000):
        return dict(type='quote', sequence=sequence, observed_us=at, acquired_us=at - 10,
                    source_msc=(utc + at - age - offset) // 1000,
                    bid_bits=struct.pack('>d', 1.1).hex().upper(), ask_bits=struct.pack('>d', 1.1001).hex().upper(),
                    raw_flags=1026, delay_basis='declared_assumption', post_marker_delay_us=[0, 1000])
    cases = {}
    def add(name, events):
        cases[name] = dict(schema=SCHEMA, kind='invented_fixture', run=len(cases) + 1, symbol='EURUSD', events=events)
    add('bounded_assumptions', deepcopy(base) + [quote()])
    rows = deepcopy(base); rows[0].update(receipt_basis='unknown', receipt_utc_us=None)
    add('unknown_receipt_clock', rows + [quote()])
    rows = deepcopy(base); rows[0]['valid_for_us'] = 999_999
    add('expired_calibration', rows + [quote()])
    rows = deepcopy(base); rows[0]['receipt_utc_us'] = [utc - 200_000, utc + 200_000]
    add('uncertain_age_limit', rows + [quote(age=1_900_000)])
    add('definitely_stale', deepcopy(base) + [quote(age=3_000_000)])
    add('future_source', deepcopy(base) + [quote(age=-100_000)])
    event = quote(); event.update(delay_basis='unknown', post_marker_delay_us=None)
    add('unknown_post_marker_delay', deepcopy(base) + [event])
    rows = deepcopy(base); rows[1].update(cost_basis='unknown', cost_profile=None)
    add('unknown_costs', rows + [quote()])
    rows = deepcopy(base); rows[1]['valid_for_us'] = 999_999
    add('expired_terms', rows + [quote()])
    add('polling_gap', deepcopy(base) + [quote(), quote(5, 6_000_000), quote(6, 7_000_000)])
    rows = deepcopy(base); rows[2]['sessions_utc_us'] = [[utc - HOUR, utc + 1_000_500]]
    add('uncertain_session_close', rows + [quote()])
    rows = deepcopy(base); rows[2]['sessions_utc_us'] = []
    add('declared_closed_session', rows + [quote()])
    first = quote(); second = quote(5, 2_000_000); second['source_msc'] = first['source_msc'] - 1
    add('source_reversal', deepcopy(base) + [first, second])
    first = quote(); second = quote(5, 2_000_000); second['source_msc'] = first['source_msc']; second['raw_flags'] = 1027
    add('same_source_changed_payload', deepcopy(base) + [first, second])
    rows = deepcopy(base); update = deepcopy(rows[0]); update.update(sequence=5, observed_us=2_000_000, receipt_utc_us=[utc + 7_000_000] * 2)
    add('clock_discontinuity', rows + [quote(), update, quote(6, 3_000_000)])
    return cases


def markdown(reports):
    lines = ['# Fresh input135 invented contract checks', '',
             'Synthetic clock/context/quote events only. No native data, strategy returns or orders.', '',
             '| Case | Quotes | Usable under invented bounds | Risk observations retained | History reviews |',
             '| --- | ---: | ---: | ---: | ---: |']
    for name, report in sorted(reports.items()):
        lines.append(f"| {name} | {report['quote_observations']} | {report['usable_under_invented_bounds']} | {report['risk_observations_retained']} | {report['history_reviews']} |")
    lines += ['', 'Usability depends on declared interval, timing, cost and session assumptions.',
              'A usable quote does not authorize a strategy entry or establish market profitability.',
              'Unknown or expired inputs remain unknown; original quotes and anomalies stay visible.', '']
    return '\n'.join(lines)
