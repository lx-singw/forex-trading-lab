"""Synthetic, observation-only inputs and strict compiled-MQL result checks."""
import csv
from datetime import datetime, timedelta, timezone
import hashlib
import io
import math

from .model import Bar, Config, signal

START = datetime(2024, 1, 2, tzinfo=timezone.utc)
CLOSED = int((START + timedelta(hours=50)).timestamp())
FIELDS = ['case_id', 'kind', 'init', 'observations', 'side', 'stop', 'removed',
          'account_reads', 'last_closed', 'copy_contract']
MARKER = b'datetime last_closed = 0;'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def observer_body(data):
    if data.count(MARKER) != 1:
        raise ValueError('Observer body marker must be unique')
    return data[data.index(MARKER):]


def fixtures():
    cases = []

    def add(name, *, kind='observation', pattern='buy', expect=None, **settings):
        closes = [1.0] * 51
        if pattern == 'buy': closes[-1] = 1.004
        elif pattern == 'sell': closes[-1] = .996
        elif pattern == 'zero_atr': closes[0], closes[30] = .971, .98
        elif pattern not in ('flat', 'gap'): raise ValueError('Undeclared pattern')
        if pattern == 'gap': closes[-1] = 1.008
        bars = []
        for i, close in enumerate(closes):
            width = 0 if pattern == 'zero_atr' and i >= 36 else .0002
            bars.append(Bar(START + timedelta(hours=i), close, close + width,
                            close - width, close, 1.0))
        side, distance = signal(bars, Config())
        controls = dict(connected=True, mode='DEMO', query_error=0, stale_error=0,
                        switch_read=0, switch_mode='DEMO', switch_error=0,
                        symbol='EURUSD', period='H1', copy_count=51, bid=1.1,
                        ask=1.1001, tick_ok=True, positions=0, orders=0,
                        init_closed=CLOSED-3600, current_open=CLOSED+3600, repeats=1)
        controls.update(settings)
        expected = dict(init=0, observations=int(side != 0 and distance > 0),
                        side='BUY' if side > 0 else 'SELL' if side < 0 else '',
                        stop=distance if side != 0 and distance > 0 else 0,
                        removed=0, account_reads=3 if side and distance > 0 else 2,
                        last_closed=CLOSED, copy_contract=1)
        if not expected['observations']: expected['side'] = ''
        expected.update(expect or {})
        cases.append(dict(case_id=name, kind=kind, controls=controls,
                          bars=[bar.to_dict() for bar in bars], expected=expected))

    for name, mode, connected, error, stale, passed, reads in (
        ('guard_demo', 'DEMO', True, 0, 0, 1, 1),
        ('guard_real', 'REAL', True, 0, 0, 0, 1),
        ('guard_contest', 'CONTEST', True, 0, 0, 0, 1),
        ('guard_unknown', 'UNKNOWN', True, 0, 0, 0, 1),
        ('guard_disconnected', 'DEMO', False, 0, 0, 0, 0),
        ('guard_query_error', 'DEMO', True, 4014, 0, 0, 1),
        ('guard_stale_error_reset', 'DEMO', True, 0, 4014, 1, 1),
    ):
        add(name, kind='guard', mode=mode, connected=connected, query_error=error,
            stale_error=stale, expect=dict(init=-99, observations=passed, side='',
                                         stop=0, account_reads=reads, last_closed=0))

    add('buy_then_duplicate', repeats=2, expect=dict(account_reads=4))
    add('sell_then_duplicate', pattern='sell', repeats=2, expect=dict(account_reads=4))
    add('flat', pattern='flat', repeats=2, expect=dict(account_reads=3))
    add('atr_true_range_gap', pattern='gap')
    silent = dict(observations=0, side='', stop=0, account_reads=2)
    add('zero_atr_cross', pattern='zero_atr', expect=silent)
    add('warmup_50', copy_count=50, expect={**silent, 'last_closed': CLOSED-3600})
    add('copy_failure', copy_count=-1, expect={**silent, 'last_closed': CLOSED-3600})
    add('restart_no_replay', init_closed=CLOSED, expect=silent)
    add('unknown_previous', init_closed=0, expect=silent)
    add('closed_hour_gap', init_closed=CLOSED-7200, expect=silent)
    add('current_hour_gap', current_open=CLOSED+7200, expect=silent)
    add('quote_unavailable', tick_ok=False, expect=silent)
    add('nonpositive_bid', bid=0, expect=silent)
    add('nonpositive_ask', ask=0, expect=silent)
    add('crossed_quote', ask=1.0999, expect=silent)
    add('spread_below_limit', ask=1.100149)
    add('spread_above_limit', ask=1.100151, expect=silent)
    add('existing_position', positions=1, expect=silent)
    add('pending_order', orders=1, expect=silent)
    for mode in ('REAL', 'CONTEST', 'UNKNOWN'):
        add('init_' + mode.lower(), mode=mode,
            expect={**silent, 'init': 1, 'account_reads': 1, 'last_closed': 0})
    add('init_disconnected', connected=False,
        expect={**silent, 'init': 1, 'account_reads': 0, 'last_closed': 0})
    add('init_account_error', query_error=4014,
        expect={**silent, 'init': 1, 'account_reads': 1, 'last_closed': 0})
    for name, controls in (('wrong_symbol', dict(symbol='EURUSDx')),
                           ('wrong_period', dict(period='M15'))):
        add(name, **controls,
            expect={**silent, 'init': 2, 'account_reads': 1, 'last_closed': 0})
    for mode in ('REAL', 'CONTEST'):
        add('tick_switch_' + mode.lower(), switch_read=2, switch_mode=mode,
            expect={**silent, 'removed': 1, 'last_closed': CLOSED-3600})
        add('final_switch_' + mode.lower(), switch_read=3, switch_mode=mode,
            expect={**silent, 'account_reads': 3})
    add('final_account_error', switch_read=3, switch_error=4014,
        expect={**silent, 'account_reads': 3})
    validate_fixtures(cases)
    return cases


def validate_fixtures(cases):
    names = set()
    for case in cases:
        if case['case_id'] in names: raise ValueError('Duplicate fixture')
        names.add(case['case_id'])
        bars = [Bar.from_dict(row) for row in case['bars']]
        if len(bars) != 51 or any(b.time != START + timedelta(hours=i) for i, b in enumerate(bars)):
            raise ValueError('Fixture bounds or closed candle inventory differs')
        if case['kind'] not in ('guard', 'observation'):
            raise ValueError('Unknown fixture kind')
    if not cases: raise ValueError('Empty fixture inventory')


def mql_inputs(cases):
    validate_fixtures(cases)
    # Only inputs, never expected outcomes, are compiled into the harness.
    lines = [f'#define CASES018 {len(cases)}', 'void Load018(int index)', '{', ' switch(index)', ' {']
    controls = dict(connected='gConnected', mode='gMode', query_error='gQueryError',
                    stale_error='gError', switch_read='gSwitchRead', switch_mode='gSwitchMode',
                    switch_error='gSwitchError', symbol='gSymbol', period='gPeriod',
                    copy_count='gCopyCount', bid='gBid', ask='gAsk', tick_ok='gTickOK',
                    positions='gPositions', orders='gOrders', init_closed='gInitClosed',
                    current_open='gCurrentOpen', repeats='gRepeats')
    for index, case in enumerate(cases):
        lines.extend([f' case {index}:', f' gName="{case["case_id"]}";',
                      f' gGuard={str(case["kind"] == "guard").lower()};'])
        for key, variable in controls.items():
            value = case['controls'][key]
            if key in ('mode', 'switch_mode'):
                value = '-999' if value == 'UNKNOWN' else 'ACCOUNT_TRADE_MODE_' + value
            elif key == 'period': value = 'PERIOD_' + value
            elif isinstance(value, bool): value = str(value).lower()
            elif isinstance(value, str): value = '"' + value + '"'
            else: value = repr(value)
            lines.append(f' {variable}={value};')
        for i, bar in enumerate(case['bars']):
            lines.append(f' gBars[{i}].time={int(Bar.from_dict(bar).time.timestamp())};'
                         f' gBars[{i}].open={bar["open"]!r}; gBars[{i}].high={bar["high"]!r};'
                         f' gBars[{i}].low={bar["low"]!r}; gBars[{i}].close={bar["close"]!r};')
        lines.append(' break;')
    lines.extend([' }', '}'])
    return ('\n'.join(lines) + '\n').encode()


def check_runtime(text, cases):
    validate_fixtures(cases)
    reader = csv.DictReader(io.StringIO(text.lstrip('\ufeff')))
    if reader.fieldnames != FIELDS: raise ValueError('Runtime schema differs')
    rows = list(reader)
    if [r['case_id'] for r in rows] != [c['case_id'] for c in cases]:
        raise ValueError('Runtime case inventory/order differs')
    comparisons = 0
    for row, case in zip(rows, cases):
        if row['kind'] != case['kind'] or None in row: raise ValueError('Malformed runtime row')
        for key, expected in case['expected'].items():
            value = row[key]
            if key == 'stop':
                actual = float(value)
                valid = math.isfinite(actual) and abs(actual - expected) <= 1e-12
            elif key == 'side': valid = value == expected
            else: valid = int(value) == expected
            if not valid: raise ValueError(f'{case["case_id"]}: {key} differs')
            comparisons += 1
    return dict(kind='synthetic_observer_runtime_review_018', passed=True,
                cases=len(cases), guard_cases=sum(c['kind'] == 'guard' for c in cases),
                comparisons=comparisons, runtime_output_sha256=digest(text.encode()),
                actual_broker_account_switch_verified=False,
                performance_evaluation_ready=False, demo_execution_ready=False)
