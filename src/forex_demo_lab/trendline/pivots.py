"""Radius3 causal pivots over explicitly invented H4/D1 publications.

Adapted from the existing confirmed/incremental extrema algorithm without
editing frozen Elliott code. Missing scheduled bars start a fresh neighbourhood;
late/reordered backfill cannot rewrite earlier confirmation history.
"""
from collections import deque
from dataclasses import dataclass
from decimal import Decimal
import hashlib

from ..elliott_full.contracts import Bar
from . import data

VERSION = "TRL_PIVOTS_166_V1"
RADIUS = 3
MAX_BARS = 20000


def bindings():
    result = data.source_bindings()
    for relative in ("src/forex_demo_lab/trendline/pivots.py",
                     "src/forex_demo_lab/elliott_full/patterns.py",
                     "scripts/trendline-pivots-166.py"):
        result[relative] = hashlib.sha256((data.ROOT/relative).read_bytes()).hexdigest()
    return result


@dataclass(frozen=True)
class Pivot:
    id: str
    kind: str
    bar_index: int
    confirmation_index: int
    occurred_at: int
    confirmed_at: int
    confirmed_ordinal: int
    price: Decimal
    timeframe: str
    radius: int
    segment: int

    def record(self):
        return {key:str(value) if isinstance(value,Decimal) else value for key,value in self.__dict__.items()}


class PivotStream:
    def __init__(self,source,timeframe="H4",radius=RADIUS):
        if timeframe not in ("H4","D1"):
            raise ValueError("H4 or D1 pivot timeframe required")
        if type(radius) is not int or radius != RADIUS:
            raise ValueError("TRL_V1 pivot radius is frozen at3")
        self.source = data.Declaration.from_record(source.record())
        self._source_json = self.source._json
        self._source_sha = self.source.sha256
        self._timeframe = timeframe
        self._bindings = bindings()
        calendar = self.source.calendar
        self._schedule = {w.start:(i,w) for i,w in enumerate(calendar.frame(timeframe))}
        self._scope_end = calendar.end
        self._clock = calendar.start
        self._window = deque(maxlen=2*RADIUS+1)
        self._journal = []
        self._chain = []
        self._gaps = []
        self._segment = 0
        self._count = 0
        self._last = None
        self._last_index = None

    def _check(self):
        if self.source._json != self._source_json or self._bindings != bindings():
            raise ValueError("pivot source/protocol bindings changed")

    @property
    def clock(self):
        return self._clock

    @property
    def timeframe(self):
        return self._timeframe

    @property
    def journal(self):
        return tuple(self._journal)

    @property
    def alternating(self):
        """Current contiguous segment only; raw journal is never superseded."""
        return tuple(self._chain)

    def advance(self,now):
        self._check()
        data.integer(now)
        if not self._clock <= now <= self._scope_end+60000:
            raise ValueError("monotonic bounded pivot publication clock required")
        self._clock = now

    def observe(self,bar):
        self._check()
        if not isinstance(bar,Bar):
            raise ValueError("typed completed invented bar required")
        # Revalidate even manually constructed Bar instances before mutation.
        bar = Bar(**bar.record())
        data.sha(bar.lineage)
        scheduled = self._schedule.get(bar.start)
        if bar.timeframe != self.timeframe or scheduled is None or scheduled[1].end != bar.end:
            raise ValueError("bar outside declared pivot schedule/frame")
        index = scheduled[0]
        if self._last is not None and index == self._last_index:
            if bar == self._last:
                return ()  # Identical latest publication is idempotent.
            raise ValueError("conflicting duplicate pivot input")
        if self._last_index is not None and index < self._last_index:
            raise ValueError("late/reordered backfill unsupported; no retrospective pivots")
        if not self._clock <= bar.available <= self._scope_end+60000:
            raise ValueError("pivot publication receipt order/boundary")
        if self._count >= MAX_BARS:
            raise ValueError("bounded pivot observation limit")

        expected_index = 0 if self._last_index is None else self._last_index+1
        gap = index > expected_index
        window = [] if gap else list(self._window)
        window.append((index,bar))
        window = window[-(2*RADIUS+1):]
        segment = self._segment+1 if gap else self._segment
        confirmed = None
        if len(window) == 2*RADIUS+1:
            center_index,center = window[RADIUS]
            neighbors = [candidate for i,(_,candidate) in enumerate(window) if i != RADIUS]
            high = all(center.high > other.high for other in neighbors)
            low = all(center.low < other.low for other in neighbors)
            if high != low:  # Dual extremes and ties remain unresolved/excluded.
                kind = "high" if high else "low"
                confirmed = Pivot(data.digest([center.lineage,kind,RADIUS]),kind,center_index,index,
                                  center.end,bar.available,self._count+1,center.high if high else center.low,
                                  self.timeframe,RADIUS,segment)

        # All validation/derivation above is complete before publishing new state.
        if gap:
            self._gaps.append((expected_index,index-1,bar.available))
            self._chain = []
        self._segment = segment
        self._window = deque(window,maxlen=2*RADIUS+1)
        self._clock = bar.available
        self._last,self._last_index = bar,index
        self._count += 1
        if confirmed is not None:
            self._journal.append(confirmed)
            if self._chain and self._chain[-1].kind == confirmed.kind:
                previous = self._chain[-1]
                if (confirmed.price > previous.price if confirmed.kind == "high" else confirmed.price < previous.price):
                    self._chain[-1] = confirmed
            else:
                self._chain.append(confirmed)
        return () if confirmed is None else (confirmed,)

    def report(self):
        self._check()
        return {"schema":VERSION,"kind":"invented_trendline_pivot_report","data_level":"B",
                "geometry_basis":self.source.record()["geometry_basis"],"timeframe":self.timeframe,
                "radius":RADIUS,"declaration_sha256":self._source_sha,
                "input_sha256":self.source.record()["input_sha256"],"source_bindings":dict(self._bindings),
                "as_of":self._clock,"publication_ordinal":self._count,"observed_bars":self._count,
                "latest_scheduled_index":self._last_index,
                "contiguous_window_bars":len(self._window),
                "window_state":("NO_BARS" if not self._count else
                                "COMPLETE" if len(self._window) == 2*RADIUS+1 else "INSUFFICIENT_CONTIGUOUS_BARS"),
                "pivots":[p.record() for p in self._journal],
                "alternating_view":[p.record() for p in self._chain],
                "alternating_view_scope":"current_contiguous_segment_only",
                "gaps":[{"missing_first_index":a,"missing_last_index":b,"observed_at":at}
                        for a,b,at in self._gaps],
                "qualified_market_source":False,"market_cells_run":0,"returns_computed":False,
                "demo_eligible":False,"orders_available":False,
                "limitations":["invented geometry inputs; no market-source qualification",
                                "late/reordered backfill rejected; missing schedule resets confirmation window",
                                "raw pivot journal is immutable; alternating view is diagnostic only",
                                "line enumeration, setup decisions and account execution are not implemented here"]}
