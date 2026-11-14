"""Explicit sequence-bound candidate clock conversion, not certified UTC."""
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import math


@dataclass(frozen=True)
class Boundary:
    month: str
    before_last: datetime
    after_first: datetime
    before_hours: int
    after_hours: int

    def __post_init__(self):
        if (len(self.month) != 6 or not self.month.isdigit()
                or self.before_last.tzinfo is not None or self.after_first.tzinfo is not None
                or any(t.strftime('%Y%m') != self.month for t in (self.before_last, self.after_first))
                or (self.before_hours, self.after_hours) not in ((5, 4), (4, 5))):
            raise ValueError('Invalid explicit clock boundary')


class SequenceClock:
    def __init__(self, boundary):
        self.boundary = boundary
        self.sequence = 0
        self.previous_source = self.previous_candidate = None
        self.changed = False
        self.transition_sequence = None

    def map(self, tick):
        stamp = tick['source_label']
        if (tick['sequence'] != self.sequence or stamp.tzinfo is not None
                or stamp.strftime('%Y%m') != self.boundary.month
                or not all(math.isfinite(tick[k]) for k in ('bid', 'ask'))
                or not 0 < tick['bid'] <= tick['ask']):
            raise ValueError('Invalid source sequence/month/quote')
        change = (not self.changed and self.previous_source == self.boundary.before_last
                  and stamp == self.boundary.after_first)
        if (self.previous_source is not None and stamp < self.previous_source and not change):
            raise ValueError('Unlisted backward source timestamp')
        after = self.changed or change
        hours = self.boundary.after_hours if after else self.boundary.before_hours
        candidate = (stamp + timedelta(hours=hours)).replace(tzinfo=timezone.utc)
        if self.previous_candidate is not None and candidate < self.previous_candidate:
            raise ValueError('Nonmonotonic candidate clock')
        # Commit state only after all validation, so rejected input cannot advance it.
        if change:
            self.changed = True
            self.transition_sequence = self.sequence
        self.previous_source, self.previous_candidate = stamp, candidate
        self.sequence += 1
        return {**tick, 'candidate_time': candidate, 'candidate_offset_hours': hours}

    def finish(self):
        if not self.changed:
            raise ValueError('Declared adjacent boundary was not observed')

    def checkpoint(self):
        return {'sequence': self.sequence, 'changed': self.changed,
                'transition_sequence': self.transition_sequence,
                'previous_source': self.previous_source.isoformat() if self.previous_source else None,
                'previous_candidate': self.previous_candidate.isoformat() if self.previous_candidate else None}

    @classmethod
    def restore(cls, boundary, state):
        obj = cls(boundary)
        seq, changed, transition = state['sequence'], state['changed'], state['transition_sequence']
        source = datetime.fromisoformat(state['previous_source']) if state['previous_source'] else None
        candidate = datetime.fromisoformat(state['previous_candidate']) if state['previous_candidate'] else None
        if (type(seq) is not int or seq < 0 or type(changed) is not bool
                or (source is None) != (candidate is None)
                or (seq == 0) != (source is None and candidate is None)
                or (changed and (type(transition) is not int or not 0 < transition < seq))
                or (not changed and transition is not None)):
            raise ValueError('Invalid clock checkpoint')
        if source is not None:
            offset = boundary.after_hours if changed else boundary.before_hours
            if (source.tzinfo is not None or source.strftime('%Y%m') != boundary.month
                    or candidate.utcoffset() != timedelta(0)
                    or candidate != (source + timedelta(hours=offset)).replace(tzinfo=timezone.utc)):
                raise ValueError('Checkpoint does not match boundary mapping')
        obj.sequence, obj.changed, obj.transition_sequence = seq, changed, transition
        obj.previous_source, obj.previous_candidate = source, candidate
        return obj


def activity_passes(event, controls):
    if len(controls) != 2 or event is None or any(c is None for c in controls):
        return False
    return all(c['ticks'] > 0 and c['range_pips'] > 0
               and event['range_pips'] >= 3 * c['range_pips']
               and event['ticks'] >= 2 * c['ticks'] for c in controls)
