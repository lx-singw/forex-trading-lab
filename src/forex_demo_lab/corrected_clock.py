"""Explicit replay lineage and candidate calendar; no market-data approval."""
from dataclasses import dataclass
from datetime import timedelta, timezone
from functools import lru_cache
import math
from zoneinfo import ZoneInfo

EUROPE = ZoneInfo('Europe/Athens')


@dataclass(frozen=True)
class Replay:
    first_start: int
    second_start: int
    rows: int

    def __post_init__(self):
        if (any(type(v) is not int for v in (self.first_start, self.second_start, self.rows))
                or self.first_start < 0 or self.rows < 1
                or self.first_start + self.rows != self.second_start):
            raise ValueError('Replay must identify exact adjacent ranges')


@lru_cache(maxsize=8192)
def _hour_offset(source_hour):
    wall = source_hour + timedelta(hours=7)
    candidates = set()
    for fold in (0, 1):
        instant = wall.replace(tzinfo=EUROPE, fold=fold).astimezone(timezone.utc)
        if instant.astimezone(EUROPE).replace(tzinfo=None) == wall:
            candidates.add(instant)
    if len(candidates) != 1:
        raise ValueError('Ambiguous or nonexistent candidate wall time')
    return candidates.pop() - source_hour.replace(tzinfo=timezone.utc)


def candidate_utc(source):
    if source.tzinfo is not None or not 2020 <= source.year <= 2023:
        raise ValueError('Candidate clock outside declared raw-label years')
    hour = source.replace(minute=0, second=0, microsecond=0)
    return source.replace(tzinfo=timezone.utc) + _hour_offset(hour)


def corrected_events(ticks, month, replay=None):
    saved = []
    source_count = output_count = removed = 0
    previous_source = previous_utc = None
    for tick in ticks:
        source = tick['source_label']
        if (tick['sequence'] != source_count or source.tzinfo is not None or source.strftime('%Y%m') != month
                or not all(math.isfinite(tick[k]) for k in ('bid', 'ask', 'volume'))
                or not 0 < tick['bid'] <= tick['ask'] or tick['volume'] < 0):
            raise ValueError('Invalid correction input sequence/month/quote')
        i = source_count
        source_count += 1
        payload = (source, tick['bid'], tick['ask'], tick['volume'])
        if replay is not None:
            if replay.first_start <= i < replay.second_start:
                saved.append(payload)
            if replay.second_start <= i < replay.second_start + replay.rows:
                n = i - replay.second_start
                if len(saved) != replay.rows or payload != saved[n]:
                    raise ValueError('Replay content differs from declared first copy')
                removed += 1
                continue
        if previous_source is not None and source < previous_source:
            raise ValueError('Unlisted source reversal')
        instant = candidate_utc(source)
        if previous_utc is not None and instant < previous_utc:
            raise ValueError('Nonmonotonic corrected candidate')
        previous_source, previous_utc = source, instant
        yield {**tick, 'source_sequence': i, 'sequence': output_count, 'candidate_time': instant}
        output_count += 1
    if replay is not None and (len(saved) != replay.rows or removed != replay.rows):
        raise ValueError('Incomplete declared replay')
