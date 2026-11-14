"""Bounded minute-reference diagnostics; never simulator inputs or approval."""
import csv
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from statistics import median
from zoneinfo import ZoneInfo

HEADER = ['<TICKER>', '<DTYYYYMMDD>', '<TIME>', '<OPEN>', '<HIGH>', '<LOW>', '<CLOSE>']
ANCHORS = ('2022-01-07', '2022-07-08', '2022-11-04',
           '2023-01-06', '2023-07-07', '2023-11-03')
DAYS = ANCHORS + ('2023-03-26', '2023-03-27', '2023-07-14')
HOUR = 3_600_000
EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)


def ms(instant):
    delta = instant - EPOCH
    return delta.days * 86_400_000 + delta.seconds * 1000


def utc_label(local):
    """Reject a wall label that cannot identify exactly one actual instant."""
    zone = ZoneInfo('Europe/Berlin')
    first, second = (local.replace(tzinfo=zone, fold=i) for i in (0, 1))
    if first.utcoffset() != second.utcoffset():
        raise ValueError('Ambiguous or nonexistent CET/CEST label')
    instant = first.astimezone(timezone.utc)
    if instant.astimezone(zone).replace(tzinfo=None) != local:
        raise ValueError('Nonexistent local label')
    return instant


def parse(lines, day):
    """Keep source row and literal label, without inferring bar start/end."""
    if day not in DAYS:
        raise ValueError('Undeclared reference date')
    reader = csv.reader(lines)
    if next(reader, None) != HEADER:
        raise ValueError('Unexpected reference schema')
    expected = day.replace('-', '')
    previous = None
    rows = []
    for number, fields in enumerate(reader, 2):
        if len(fields) != 7:
            raise ValueError('Malformed reference row')
        if fields[0] != 'EURUSD':
            continue
        if fields[1] != expected or len(fields[2]) != 6 or not fields[2].isdigit():
            raise ValueError('Unexpected source date/time')
        if fields[2] == '240000':
            local = datetime.strptime(expected, '%Y%m%d') + timedelta(days=1)
        else:
            local = datetime.strptime(fields[1] + fields[2], '%Y%m%d%H%M%S')
        if local.second:
            raise ValueError('Reference label is not minute aligned')
        instant = utc_label(local)
        stamp = ms(instant)
        if previous is not None and stamp <= previous:
            raise ValueError('Duplicate or reversed EURUSD reference label')
        previous = stamp
        try:
            o, h, l, c = (Decimal(x) for x in fields[3:])
        except InvalidOperation as e:
            raise ValueError('Invalid reference price') from e
        if not all(x.is_finite() and x > 0 for x in (o, h, l, c)):
            raise ValueError('Nonfinite/nonpositive reference OHLC')
        if not l <= min(o, c) <= max(o, c) <= h:
            raise ValueError('Inconsistent reference OHLC')
        rows.append({'source_day': day, 'source_row': number,
                     'source_date': fields[1], 'source_time': fields[2],
                     'reference_time_msc': stamp,
                     **dict(zip(('open', 'high', 'low', 'close'), fields[3:]))})
    return rows


def hourly(rows):
    result = {}
    previous = None
    for row in rows:
        stamp = row['reference_time_msc']
        if previous is not None and stamp <= previous:
            raise ValueError('Reference files overlap or reverse')
        previous = stamp
        hour = stamp // HOUR * HOUR
        o, h, l, c = (Decimal(row[k]) for k in ('open', 'high', 'low', 'close'))
        if hour not in result:
            result[hour] = {'hour_start_ms': hour, 'minutes': 0, 'first_ms': stamp,
                            'open': str(o), 'high': str(h), 'low': str(l)}
        bar = result[hour]
        bar.update(minutes=bar['minutes'] + 1, last_ms=stamp, close=str(c),
                   high=str(max(Decimal(bar['high']), h)),
                   low=str(min(Decimal(bar['low']), l)))
    return result


def difference(reference, candidate):
    if reference is None or candidate is None:
        return None
    return {k: float(abs(Decimal(reference[k]) - Decimal(str(candidate['bid_' + k])))
                     / Decimal('0.0001')) for k in ('open', 'high', 'low', 'close')}


def screen(day, reference, candidate):
    start = ms(datetime.fromisoformat(day).replace(tzinfo=timezone.utc))
    distances = {'aligned': [], 'minus_one_hour': [], 'plus_one_hour': []}
    for hour in range(6, 18):
        stamp = start + hour * HOUR
        for name, offset in (('aligned', 0), ('minus_one_hour', -HOUR), ('plus_one_hour', HOUR)):
            delta = difference(reference.get(stamp), candidate.get(stamp + offset))
            distances[name].append(None if delta is None else delta['close'])
    complete = all(all(v is not None for v in values) for values in distances.values())
    medians = {k: median(v) if all(x is not None for x in v) else None
               for k, v in distances.items()}
    within = sum(x is not None and x <= 2 for x in distances['aligned'])
    passed = bool(complete and within >= 10 and medians['aligned'] <= 2
                  and medians['aligned'] < medians['minus_one_hour']
                  and medians['aligned'] < medians['plus_one_hour'])
    return {'day': day, 'utc_hours': list(range(6, 18)), 'close_distances_pips': distances,
            'median_close_distance_pips': medians, 'all_36_pairs_present': complete,
            'aligned_pairs_within_2_pips': within, 'fixed_screen_pass': passed}


def compare_day(day, reference, candidate):
    start = ms(datetime.fromisoformat(day).replace(tzinfo=timezone.utc))
    return [{'hour_start_ms': stamp,
             'reference': reference.get(stamp), 'candidate': candidate.get(stamp),
             'absolute_ohlc_distance_pips': difference(reference.get(stamp), candidate.get(stamp))}
            for stamp in (start + h * HOUR for h in range(24))]
