"""Raw-label quote recovery diagnostics; never approves simulator input."""
import csv
from datetime import datetime, timedelta, timezone
import math

from .reconstruction import HOUR, PRICES, bound, checked_capture


def chunks(start, end):
    lower, upper = bound(start), bound(end)
    if upper <= lower:
        raise ValueError('Recovery interval must increase')
    result = []
    while lower < upper:
        stop = min(lower + 48 * HOUR, upper)
        result.append((label(lower), label(stop)))
        lower = stop
    return result


def label(ms):
    return datetime.fromtimestamp(ms / 1000, timezone.utc).isoformat()


def references(path):
    result = {}
    with path.open(encoding='utf-8-sig', newline='') as stream:
        for row in csv.DictReader(stream):
            hour = bound(row['time'])
            prices = {k: float(row[k]) for k in PRICES}
            o, h, l, c = (prices[k] for k in PRICES)
            if (hour in result or not all(math.isfinite(v) and v > 0 for v in prices.values())
                    or not l <= min(o, c) <= max(o, c) <= h):
                raise ValueError('Invalid or duplicate reference candle')
            result[hour] = prices
    return result


def audit_chunk(folder, expected_start, expected_end, reference):
    metadata, ticks, start, end = checked_capture(folder)
    if ((start, end) != (bound(expected_start), bound(expected_end))
            or metadata.get('account_type') != 'demo'):
        raise ValueError('Capture differs from declared window or demo mode')
    bars, gaps, previous = {}, [], None
    same_ms = 0
    for tick in ticks:
        ms, bid, ask = tick['time_msc'], tick['bid'], tick['ask']
        if previous is not None:
            same_ms += ms == previous
            if ms - previous > HOUR:
                gaps.append({'after_source_label': label(previous), 'before_source_label': label(ms),
                             'seconds': (ms - previous) / 1000, 'classification': 'unclassified'})
        previous = ms
        hour = ms // HOUR * HOUR
        bar = bars.get(hour)
        if bar is None:
            bar = bars[hour] = {'ticks': 0, 'first_ms': ms, 'last_ms': ms,
                **{f'{side}_{k}': price for side, price in (('bid', bid), ('ask', ask)) for k in PRICES}}
        bar['ticks'] += 1
        bar['last_ms'] = ms
        for side, price in (('bid', bid), ('ask', ask)):
            bar[f'{side}_high'] = max(bar[f'{side}_high'], price)
            bar[f'{side}_low'] = min(bar[f'{side}_low'], price)
            bar[f'{side}_close'] = price
    hours = []
    for hour in range(start, end, HOUR):
        bar, old = bars.get(hour), reference.get(hour)
        item = {'source_hour_label': label(hour), 'ticks': bar['ticks'] if bar else 0}
        if bar:
            item.update(bar)
            if old is not None:
                differences = {k: (bar[f'bid_{k}'] - old[k]) / .0001 for k in PRICES}
                item.update(bid_difference_pips=differences,
                            status='match' if all(abs(v) < .05 for v in differences.values()) else 'mismatch')
            else:
                item['status'] = 'ticks_without_reference'
        else:
            item['status'] = 'reference_without_ticks' if old is not None else 'empty_unclassified'
        hours.append(item)
    return {'ticks': len(ticks), 'hours': hours, 'gaps_over_one_hour': gaps,
            'same_millisecond_events': same_ms, 'first_ms': ticks[0]['time_msc'] if ticks else None,
            'last_ms': ticks[-1]['time_msc'] if ticks else None,
            'data_sha256': metadata['data_sha256'], 'account_type': metadata['account_type'],
            'terminal_algo_trading': metadata['terminal_algo_trading'],
            'source_label_start': expected_start, 'source_label_end_exclusive': expected_end,
            'performance_evaluation_ready': False}


def sample_passed(report, expected_hours=12):
    return (len(report['hours']) == expected_hours
            and all(h['ticks'] > 0 and h['status'] == 'match' for h in report['hours']))


def combine(reports):
    """Reject holes/overlaps even on resume; preserve gaps through empty chunks."""
    if not reports:
        raise ValueError('No recovery reports')
    cursor, previous = bound(reports[0]['source_label_start']), None
    hours, gaps, seams, same_ms = [], [], [], 0
    for i, report in enumerate(reports):
        start, end = bound(report['source_label_start']), bound(report['source_label_end_exclusive'])
        if start != cursor or not start < end <= start + 48 * HOUR:
            raise ValueError('Recovery chunks overlap or leave a hole')
        if [bound(h['source_hour_label']) for h in report['hours']] != list(range(start, end, HOUR)):
            raise ValueError('Chunk hour inventory is incomplete or duplicated')
        first, last = report['first_ms'], report['last_ms']
        if (first is None) != (last is None) or (first is not None and not start <= first <= last < end):
            raise ValueError('Chunk event bounds are invalid')
        if first is not None:
            if previous is not None:
                if first < previous:
                    raise ValueError('Backward tick across chunks')
                same_ms += first == previous
                seam = {'before_chunk': i, 'after_source_label': label(previous),
                        'before_source_label': label(first), 'seconds': (first - previous) / 1000,
                        'classification': 'unclassified'}
                seams.append(seam)
                if first - previous > HOUR:
                    gaps.append(seam)
            previous = last
        hours.extend(report['hours'])
        gaps.extend(report['gaps_over_one_hour'])
        same_ms += report['same_millisecond_events']
        cursor = end
    if sum(h['ticks'] for h in hours) != sum(r['ticks'] for r in reports):
        raise ValueError('Combined tick count disagrees with hours')
    counts = {status: sum(h['status'] == status for h in hours) for status in
              ('match', 'mismatch', 'ticks_without_reference', 'reference_without_ticks', 'empty_unclassified')}
    return {'source_label_start': reports[0]['source_label_start'], 'source_label_end_exclusive': label(cursor),
            'chunks': len(reports), 'ticks': sum(r['ticks'] for r in reports), 'hours': hours,
            'hour_counts': counts, 'gaps_over_one_hour': gaps, 'chunk_seams': seams,
            'same_millisecond_events': same_ms, 'absolute_utc_verified': False,
            'complete_market_history_verified': False, 'performance_evaluation_ready': False}
