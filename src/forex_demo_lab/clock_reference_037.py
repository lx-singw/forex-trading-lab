"""Bounded coarse clock observations, with no history or order capability."""
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import http.client
import ssl

from .fresh_data_031 import DATE, ProbeRejected, guard, observation, receipt

VERSION = 'coarse_clock_reference_037_v1'
TARGETS = ('https://www.time.gov/', 'https://www.microsoft.com/', 'https://www.mql5.com/')
HEADERS = ('Date', 'Age', 'Cache-Control')
MAX_NS = 30_000_000_000


def bounds(before, after, previous=None):
    for utc, mono in (before, after):
        receipt(utc)
        if type(mono) is not int or mono < 0:
            raise ProbeRejected('invalid_monotonic_clock')
    if after[0] < before[0] or after[1] < before[1] or previous is not None and (
            before[0] < previous[0] or before[1] < previous[1]):
        raise ProbeRejected('receipt_clock_reversed')
    if abs((after[0]-before[0])*1_000_000-(after[1]-before[1])) > 5_000_000_000:
        raise ProbeRejected('receipt_clock_discontinuity')


def https_head(index, timeout=10, connection=http.client.HTTPSConnection):
    """Single verified TLS connection, no redirect/retry, whitelisted headers only.

    The parent process enforces the whole-operation deadline, including DNS.
    """
    if type(index) is not int or not 0 <= index < len(TARGETS) or not 0 < timeout <= 10:
        raise ValueError('request_outside_declaration')
    host = TARGETS[index].split('/')[2]
    conn = connection(host, timeout=timeout, context=ssl.create_default_context())
    try:
        conn.request('HEAD', '/')
        response = conn.getresponse()
        headers, invalid = {}, False
        for name in HEADERS:
            values = [v for k, v in response.getheaders() if k.lower() == name.lower()]
            if len(values) > 1 or any(not isinstance(v, str) or len(v) > 2048 or
                                     any(ord(c) < 32 or ord(c) > 126 for c in v) for v in values):
                invalid = True
                headers[name] = None
            else:
                headers[name] = values[0] if values else None
        return dict(status=response.status, headers=headers,
                    transport_outcome='malformed_headers' if invalid else 'response')
    finally:
        conn.close()


def reference(row):
    """Reconstruct coarse offset bounds without treating raw labels as UTC."""
    result = dict(usable=False, reason=None, date_utc_ms=None, offset_interval_ms=None,
                  uncertainty_ms=None)
    before, after = tuple(row['before']), tuple(row['after'])
    try:
        bounds(before, after)
        if after[1]-before[1] > 10_000_000_000:
            raise ProbeRejected('request_deadline_exceeded')
        if row['transport_outcome'] != 'response':
            raise ProbeRejected(row['transport_outcome'])
        if type(row['status']) is not int or not 200 <= row['status'] < 300:
            raise ProbeRejected('redirect' if type(row['status']) is int and 300 <= row['status'] < 400 else 'http_failure')
        headers = row['headers']
        if set(headers) != set(HEADERS):
            raise ProbeRejected('malformed_headers')
        age = headers['Age']
        if age is not None and (not age.isascii() or not age.isdigit() or int(age) != 0):
            raise ProbeRejected('cached_or_invalid_age')
        value = headers['Date']
        if not isinstance(value, str) or len(value) > 2048:
            raise ProbeRejected('missing_or_invalid_date')
        try:
            date = parsedate_to_datetime(value)
            if date.tzinfo is None or date.utcoffset().total_seconds() != 0:
                raise ValueError()
            # Require canonical IMF-fixdate; reject ambiguous, duplicate or malformed values.
            if date.strftime('%a, %d %b %Y %H:%M:%S GMT') != value:
                raise ValueError()
            stamp = int(date.timestamp())*1000
        except (ValueError, TypeError, OverflowError):
            raise ProbeRejected('missing_or_invalid_date')
        result['date_utc_ms'] = stamp
        if not before[0]-5000 <= stamp <= after[0]+5000:
            raise ProbeRejected('date_outside_fresh_receipt_bounds')
        result.update(usable=True, offset_interval_ms=[stamp-after[0], stamp+1000-before[0]],
                      uncertainty_ms=after[0]-before[0]+1000)
    except ProbeRejected as exc:
        result['reason'] = str(exc)
    return result


def compare(rows, quote):
    assessments = [reference(r) for r in rows if r['after'] is not None]
    usable = [r for r in assessments if r['usable']]
    if len(usable) < 2 or quote is None:
        return dict(outcome='insufficient_evidence', raw_minus_receipt_ms=None,
                    raw_minus_reference_ms=None, reference_offset_envelope_ms=None)
    lo = min(r['offset_interval_ms'][0] for r in usable)
    hi = max(r['offset_interval_ms'][1] for r in usable)
    qlo = quote['raw_time_msc']-quote['received_after_utc_ms']
    qhi = quote['raw_time_msc']-quote['received_before_utc_ms']
    difference = [qlo-hi, qhi-lo]
    return dict(outcome='agreement' if difference[0] <= 5000 and difference[1] >= -5000 else 'disagreement',
                raw_minus_receipt_ms=[qlo, qhi], raw_minus_reference_ms=difference,
                reference_offset_envelope_ms=[lo, hi])


def collect(clock, service_status, transport, connect):
    """Dependencies are injected; connection is deferred until two usable hosts."""
    out = dict(version=VERSION, declared_date=DATE, requests=[], windows_time_service=None,
               native_connections_attempted=0, actual_quote_reads=0, quote=None, quote_last_error_code=None,
               quote_guards_passed=False, stop_reason=None, started=None, completed=None,
               fresh_performance_eligible=False, annual_eligible=False, orders_available=False,
               historical_reads=0, strategy_replays=0, raw_labels_normalized=False,
               local_clock_certified=False)
    api = None
    try:
        start = clock(); bounds(start, start); out['started'] = start
        status = service_status()
        if set(status) != {'available', 'running', 'outcome'} or type(status['available']) is not bool or \
                status['running'] is not None and type(status['running']) is not bool or status['outcome'] not in ('observed', 'unavailable', 'query_failed'):
            raise ProbeRejected('invalid_service_status')
        out['windows_time_service'] = status
        previous = clock(); bounds(start, previous)
        request_start = None
        for index, target in enumerate(TARGETS):
            before = clock(); bounds(previous, before)
            if request_start is None:
                request_start = before
            remaining = MAX_NS-(before[1]-request_start[1])
            if remaining <= 0:
                raise ProbeRejected('total_request_budget_exhausted')
            row = dict(index=index, target=target, before=before, after=None,
                       status=None, headers={k:None for k in HEADERS}, transport_outcome='transport_failure')
            out['requests'].append(row)  # Record attempted request even on exception/timeout.
            try:
                response = transport(index, min(10, remaining/1e9))
                if set(response) != {'status', 'headers', 'transport_outcome'} or \
                        response['transport_outcome'] not in ('response', 'timeout', 'transport_failure', 'malformed_headers') or \
                        set(response['headers']) != set(HEADERS) or \
                        any(v is not None and (not isinstance(v, str) or len(v)>2048 or any(ord(c)<32 or ord(c)>126 for c in v)) for v in response['headers'].values()) or \
                        response['status'] is not None and type(response['status']) is not int:
                    raise ValueError()
                row.update(response)
            except Exception:
                row['transport_outcome'] = 'transport_failure'
            after = clock(); row['after'] = after
            row['assessment'] = reference(row)
            bounds(before, after)
            if after[1]-request_start[1] > MAX_NS:
                raise ProbeRejected('total_request_budget_exhausted')
            if after[1]-before[1] > 10_000_000_000:
                raise ProbeRejected('request_deadline_exceeded')
            previous = after
        if sum(r['assessment']['usable'] for r in out['requests']) < 2:
            raise ProbeRejected('fewer_than_two_usable_hosts')
        before_connect = clock(); bounds(previous, before_connect)
        out['native_connections_attempted'] = 1
        api = connect()
        if api is None:
            raise ProbeRejected('existing_terminal_connection_unavailable')
        identity = guard(api)
        before = clock(); bounds(before_connect, before)
        guard(api, identity)
        out['actual_quote_reads'] = 1
        tick = api.symbol_info_tick('EURUSD')
        after = clock()
        error = api.last_error()
        if isinstance(error, tuple) and error and type(error[0]) is int:
            out['quote_last_error_code'] = error[0]
        guard(api, identity)
        bounds(before, after)
        candidate = observation(0, tick, before, after)
        guard(api, identity)
        completed = clock(); out['completed'] = completed; bounds(after, completed)
        guard(api, identity)
        out['quote'] = candidate
        out['quote_guards_passed'] = True
    except ProbeRejected as exc:
        out['stop_reason'] = str(exc)
    except Exception:
        out['stop_reason'] = 'runtime_failure_details_redacted'
    finally:
        if api is not None:
            try:
                api.shutdown()
            except Exception:
                out['quote'] = None; out['quote_guards_passed'] = False
                out['stop_reason'] = 'ipc_shutdown_failure_details_redacted'
        if out['completed'] is None:
            try:
                final = clock(); out['completed'] = final
                bounds(out['started'] or final, final)
            except Exception:
                out['quote'] = None; out['quote_guards_passed'] = False
                out['stop_reason'] = 'completion_clock_invalid'
    out['comparison'] = compare(out['requests'], out['quote'])
    return out
