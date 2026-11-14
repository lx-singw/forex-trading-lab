"""Bounded receipt-clock observations; no history or execution capability."""
from datetime import datetime, timezone
import math

from .collection import SPEC_FIELDS

VERSION = 'receipt_clock_probe_031_v1'
DATE = '2026-10-06'
MAX_READS = 120
INTERVAL_SECONDS = .5
MAX_ELAPSED_NS = 60_000_000_000


class ProbeRejected(ValueError):
    pass


def guard(api, identity=None):
    terminal, account = api.terminal_info(), api.account_info()
    if terminal is None or account is None or terminal.connected is not True:
        raise ProbeRejected('disconnected')
    if type(account.trade_mode) is not int or account.trade_mode != api.ACCOUNT_TRADE_MODE_DEMO:
        raise ProbeRejected('actual_account_not_demo')
    if account.currency != 'USD':
        raise ProbeRejected('account_currency_not_usd')
    if terminal.trade_allowed is not False:
        raise ProbeRejected('algo_trading_enabled')
    # This identity is private and ephemeral; it never enters returned records.
    current = (account.login, account.server)
    if type(current[0]) is not int or not isinstance(current[1], str) or identity is not None and current != identity:
        raise ProbeRejected('account_changed_or_invalid')
    return current


def receipt(utc_ms):
    if type(utc_ms) is not int or utc_ms < 0:
        raise ProbeRejected('invalid_receipt_clock')
    try:
        date = datetime.fromtimestamp(utc_ms/1000, timezone.utc).date().isoformat()
    except (ValueError, OverflowError, OSError) as exc:
        raise ProbeRejected('invalid_receipt_clock') from exc
    if date != DATE:
        raise ProbeRejected('receipt_outside_declared_date')


def observation(index, quote, before, after, previous=None):
    for utc, mono in (before, after):
        receipt(utc)
        if type(mono) is not int or mono < 0:
            raise ProbeRejected('invalid_monotonic_clock')
    if after[0] < before[0] or after[1] < before[1] or previous is not None and (
            before[0] < previous['received_after_utc_ms'] or before[1] < previous['received_after_monotonic_ns']):
        raise ProbeRejected('receipt_clock_reversed')
    if quote is None:
        raise ProbeRejected('quote_unavailable')
    stamp, bid, ask = quote.time_msc, quote.bid, quote.ask
    if type(stamp) is not int or stamp <= 0 or type(bid) not in (int, float) or type(ask) not in (int, float) or not (
            math.isfinite(bid) and math.isfinite(ask) and 0 < bid <= ask):
        raise ProbeRejected('invalid_quote')
    if abs(stamp-after[0]) > 86400000:
        raise ProbeRejected('raw_label_outside_current_probe_bound')
    if previous is not None and stamp < previous['raw_time_msc']:
        raise ProbeRejected('source_clock_reversed')
    repeat = previous is not None and (stamp, bid, ask) == (
        previous['raw_time_msc'], previous['bid'], previous['ask'])
    return dict(poll_index=index, raw_time_msc=stamp, bid=bid, ask=ask,
        received_before_utc_ms=before[0], received_after_utc_ms=after[0],
        received_before_monotonic_ns=before[1], received_after_monotonic_ns=after[1],
        repeated_snapshot=repeat)


def clock_summary(rows):
    return dict(observations=len(rows), repeated_snapshots=sum(r['repeated_snapshot'] for r in rows),
        raw_minus_receipt_lower_ms=min((r['raw_time_msc']-r['received_after_utc_ms'] for r in rows), default=None),
        raw_minus_receipt_upper_ms=max((r['raw_time_msc']-r['received_before_utc_ms'] for r in rows), default=None),
        max_read_latency_ms=max((r['received_after_utc_ms']-r['received_before_utc_ms'] for r in rows), default=None))


def probe(api, clock, sleep, reads=MAX_READS):
    """Clock returns (UTC milliseconds, monotonic nanoseconds). Always fails closed."""
    if type(reads) is not int or not 1 <= reads <= MAX_READS:
        raise ValueError('Read budget outside declared bound')
    rows, contract, reason, calls, started = [], None, None, 0, None
    try:
        initial = clock()
        receipt(initial[0])
        if type(initial[1]) is not int or initial[1] < 0:
            raise ProbeRejected('invalid_monotonic_clock')
        started = initial
        identity = guard(api)
        symbol = api.symbol_info('EURUSD')
        guard(api, identity)
        if symbol is None or symbol.visible is not True or symbol.currency_base != 'EUR' or symbol.currency_profit != 'USD':
            raise ProbeRejected('symbol_not_supported_or_visible')
        contract = {k: getattr(symbol, k) for k in SPEC_FIELDS}
        if any(type(v) in (int, float) and not math.isfinite(v) for v in contract.values()):
            contract = None
            raise ProbeRejected('invalid_contract_snapshot')
        for index in range(reads):
            guard(api, identity)
            before = clock()
            receipt(before[0])
            if before[1]-initial[1] >= MAX_ELAPSED_NS:
                raise ProbeRejected('elapsed_budget_exhausted')
            calls += 1
            quote = api.symbol_info_tick('EURUSD')
            after = clock()
            guard(api, identity)
            if after[1]-initial[1] > MAX_ELAPSED_NS:
                raise ProbeRejected('elapsed_budget_exhausted')
            row = observation(index, quote, before, after, rows[-1] if rows else None)
            rows.append(row)
            if index+1 < reads:
                sleep(INTERVAL_SECONDS)
        guard(api, identity)
    except ProbeRejected as exc:
        reason = str(exc)
    except Exception:
        # API exception text can contain identity or connection details.
        reason = 'api_or_clock_failure_details_redacted'
    return dict(version=VERSION, status='completed_receipt_probe' if reason is None else 'stopped_guarded_probe',
        stop_reason=reason, actual_quote_reads=calls, requested_reads=reads,
        probe_started_utc_ms=started[0] if started else None,
        probe_started_monotonic_ns=started[1] if started else None,
        observations=rows, clock_summary=clock_summary(rows), contract_snapshot=contract,
        account_type='demo' if contract is not None else None,
        continuous_tick_capture=False, raw_labels_interpreted_as_utc=False,
        local_clock_independently_certified=False, historical_timezone_verified=False,
        fresh_performance_eligible=False, annual_eligible=False, orders_available=False)
