"""Fixed-window coverage evidence. No executable data or performance approval."""
import hashlib
import json
from decimal import Decimal, localcontext
from fractions import Fraction
from itertools import combinations

HOUR = 3600000
MINUTE = 60000


def price(value):
    number = Decimal(value)
    if not number.is_finite() or number <= 0:
        raise ValueError('Invalid price')
    return number


def canonical_event(event):
    values = ([event['bid'], event['ask']] if event['kind'] == 'ticks'
              else [event[key] for key in ('open', 'high', 'low', 'close')])
    fractions = [Fraction(price(value)) for value in values]
    payload = [event['path'], event['member'], event['record'], event['raw_label'],
               event['event_ms'], [f'{v.numerator}/{v.denominator}' for v in fractions]]
    return (json.dumps(payload, separators=(',', ':'), ensure_ascii=True) + '\n').encode('ascii')


def update_bar(bar, event):
    stamp = event['event_ms']
    if event['kind'] == 'ticks':
        bid, ask = price(event['bid']), price(event['ask'])
        if ask < bid:
            raise ValueError('Crossed quote')
        values = {'bid': (bid, bid, bid, bid), 'ask': (ask, ask, ask, ask)}
    else:
        o, h, l, c = (price(event[key]) for key in ('open', 'high', 'low', 'close'))
        if not l <= min(o, c) <= max(o, c) <= h:
            raise ValueError('Invalid reference OHLC')
        values = {'reference': (o, h, l, c)}
    location = {key: event[key] for key in ('path', 'member', 'record', 'raw_label')}
    if bar['records'] == 0:
        bar.update(first_ms=stamp, first_original=location)
        for side, (o, h, l, c) in values.items():
            bar.update({f'{side}_{key}': str(value) for key, value in zip(('open','high','low','close'), (o,h,l,c))})
    bar['records'] += 1
    bar.update(last_ms=stamp, last_original=location)
    for side, (o, h, l, c) in values.items():
        bar[f'{side}_high'] = str(max(Decimal(bar[f'{side}_high']), h))
        bar[f'{side}_low'] = str(min(Decimal(bar[f'{side}_low']), l))
        bar[f'{side}_close'] = str(c)


def empty_bar(start, available, kind):
    return dict(start_ms=start, available=available,
                records=0 if available else None, first_ms=None, last_ms=None,
                first_original=None, last_original=None,
                **{f'{side}_{key}': None for side in ('bid','ask','reference')
                   for key in ('open','high','low','close')})


def aggregate(events, start, end, *, kind='ticks', captured=None, minute_bins=False,
              tail_cutoff=None, save_event=None):
    if type(start) is not int or type(end) is not int or start % HOUR or end % HOUR or end <= start:
        raise ValueError('Invalid whole-hour interval')
    if kind not in ('ticks', 'reference'):
        raise ValueError('Invalid source kind')
    if captured is None:
        captured = (start, end)
    hours = {hour: empty_bar(hour, captured[0] <= hour and hour + HOUR <= captured[1], kind)
             for hour in range(start, end, HOUR)}
    minutes = {minute: empty_bar(minute, captured[0] <= minute and minute + MINUTE <= captured[1], kind)
               for minute in range(start, end, MINUTE)} if minute_bins else {}
    digest = hashlib.sha256()
    previous = None
    previous_record = None
    count = tail = ties = 0
    for event in events:
        stamp = event['event_ms']
        if type(stamp) is not int or type(event['record']) is not int or event['record'] < 1 or event['kind'] != kind:
            raise ValueError('Invalid event contract')
        if not start <= stamp < end:
            continue
        identity = (event['path'], event['member'])
        if previous is not None and stamp < previous:
            raise ValueError('Reversed selected event')
        if previous_record is not None and previous_record[0] == identity and event['record'] <= previous_record[1]:
            raise ValueError('Repeated or reversed original record')
        if previous == stamp:
            if kind == 'reference':
                raise ValueError('Repeated reference label')
            ties += 1
        if not hours[stamp // HOUR * HOUR]['available']:
            raise ValueError('Quote outside captured availability')
        update_bar(hours[stamp // HOUR * HOUR], event)
        if minute_bins:
            update_bar(minutes[stamp // MINUTE * MINUTE], event)
        digest.update(canonical_event(event))
        count += 1
        if tail_cutoff is not None and tail_cutoff < stamp < tail_cutoff // HOUR * HOUR + HOUR:
            tail += 1
        if save_event:
            save_event(event)
        previous = stamp
        previous_record = (identity, event['record'])
    for bar in (*hours.values(), *minutes.values()):
        bar['status'] = 'unavailable' if not bar['available'] else 'present' if bar['records'] else 'empty'
    return dict(kind=kind, selected_records=count, tied_transitions=ties,
                event_sha256=digest.hexdigest(), hours=list(hours.values()),
                minutes=list(minutes.values()), tail_records=tail if tail_cutoff is not None else None)


def distances(sources):
    results = []
    for left, right in combinations(sources, 2):
        a, b = sources[left], sources[right]
        if len(a['hours']) != len(b['hours']):
            raise ValueError('Hour grids differ')
        for first, second in zip(a['hours'], b['hours']):
            if first['start_ms'] != second['start_ms']:
                raise ValueError('Hour labels differ')
            side_a = 'bid' if a['kind'] == 'ticks' else 'reference'
            side_b = 'bid' if b['kind'] == 'ticks' else 'reference'
            delta = None
            if first['records'] and second['records']:
                with localcontext() as context:
                    context.prec = 80
                    delta = {key: str(abs(Decimal(first[f'{side_a}_{key}']) - Decimal(second[f'{side_b}_{key}'])) / Decimal('.0001'))
                             for key in ('open','high','low','close')}
            results.append(dict(left=left, right=right, hour_start_ms=first['start_ms'],
                                absolute_ohlc_distance_pips=delta))
    return results


def questions(march, july, march_hour, july_empty_hour):
    def selected(summary, hour):
        return next(bar for bar in summary['hours'] if bar['start_ms'] == hour)
    spring = selected(march, march_hour)
    summer = selected(july, july_empty_hour)
    return dict(march_utc23=dict(answer=spring['records'] > 0 if spring['available'] else None, count=spring['records']),
                july_tail=dict(answer=july['tail_records'] > 0 if july['tail_records'] is not None else None,
                               count=july['tail_records']),
                july_utc20=dict(answer=summer['records'] > 0 if summer['available'] else None, count=summer['records']))
