"""Exact line arithmetic and causal indicators for invented trendline research.

Geometry is not an eligible trading line. Touches, pokes, enumeration, ranking
and lifecycle acceptance remain the next Phase4 increments.
"""
from bisect import bisect_right
from collections import deque
from copy import copy
from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction as F
import hashlib
import re

from ..elliott_full.contracts import Bar
from . import data, pivots

VERSION = "TRL_GEOMETRY_167_V1"
ATR_PERIOD = 14
ANGLE_WINDOW = 390
CHART_ASPECT = F(1,2)
MAX_ATR_SLOPE = F(1,2)
TOUCH_TOLERANCE = F(1,4)


def exact(value):
    if isinstance(value,bool) or not isinstance(value,(str,int,Decimal,F)):
        raise ValueError("exact decimal/integer/rational required; floats refused")
    if isinstance(value,str) and not re.fullmatch(r"-?[0-9]{1,20}(?:\.[0-9]{1,20})?",value):
        raise ValueError("bounded decimal spelling required")
    if isinstance(value,Decimal) and not value.is_finite():
        raise ValueError("finite exact price required")
    return F(value)


def rational_record(value):
    if value is None:
        return None
    value = exact(value)
    return {"numerator":value.numerator,"denominator":value.denominator}


def true_range(high,low,previous_close):
    high,low,previous_close = map(exact,(high,low,previous_close))
    if not 0 < low <= high or previous_close <= 0:
        raise ValueError("positive high/low/prior close required")
    return max(high-low,abs(high-previous_close),abs(low-previous_close))


def atr_sma14(ranges):
    if not isinstance(ranges,(list,tuple,deque)):
        raise ValueError("ordered true-range sequence required")
    values = [exact(value) for value in ranges]
    if any(value < 0 for value in values):
        raise ValueError("nonnegative true ranges required")
    return None if len(values) < ATR_PERIOD else sum(values[-ATR_PERIOD:],F(0))/ATR_PERIOD


@dataclass(frozen=True)
class Cursor:
    timeframe: str
    available_at: int
    ordinal: int

    def __post_init__(self):
        if self.timeframe not in ("H4","D1"):
            raise ValueError("pivot-frame cursor required")
        data.integer(self.available_at)
        data.integer(self.ordinal)


@dataclass(frozen=True)
class Ray:
    """Pure coordinate geometry; no claim about touches, coverage or validity."""
    kind: str
    a_index: int
    a_price: F
    b_index: int
    b_price: F
    timeframe: str = "H4"

    def __post_init__(self):
        data.integer(self.a_index);data.integer(self.b_index)
        if self.timeframe not in ("H4","D1") or self.kind not in ("support","resistance"):
            raise ValueError("declared support/resistance timeframe required")
        a,b = exact(self.a_price),exact(self.b_price)
        if min(a,b) <= 0 or self.b_index-self.a_index < 6:
            raise ValueError("positive anchors and six-bar minimum spacing required")
        if (self.kind == "support" and b <= a) or (self.kind == "resistance" and b >= a):
            raise ValueError("strict rising support or falling resistance required")
        object.__setattr__(self,"a_price",a);object.__setattr__(self,"b_price",b)

    @classmethod
    def from_pivots(cls,a,b,cursor):
        if not isinstance(cursor,Cursor) or not all(isinstance(p,pivots.Pivot) for p in (a,b)):
            raise ValueError("confirmed typed pivots and frame cursor required")
        for pivot in (a,b):
            data.sha(pivot.id)
            for value in (pivot.bar_index,pivot.confirmation_index,pivot.confirmed_ordinal,
                          pivot.occurred_at,pivot.confirmed_at,pivot.segment):
                data.integer(value)
            if (pivot.radius != 3 or type(pivot.radius) is not int
                    or pivot.confirmation_index != pivot.bar_index+3
                    or pivot.confirmed_at <= pivot.occurred_at
                    or pivot.kind not in ("high","low")
                    or pivot.timeframe != cursor.timeframe
                    or (pivot.confirmed_at,pivot.confirmed_ordinal) > (cursor.available_at,cursor.ordinal)):
                raise ValueError("pivot confirmation unavailable at declared frame cursor")
        if a.kind != b.kind or a.segment != b.segment:
            raise ValueError("same-kind pivots from one contiguous segment required")
        return cls("support" if a.kind == "low" else "resistance",
                   a.bar_index,a.price,b.bar_index,b.price,cursor.timeframe)

    @property
    def slope(self):
        return (self.b_price-self.a_price)/(self.b_index-self.a_index)

    def value(self,index):
        data.integer(index)
        return self.a_price+self.slope*(index-self.a_index)

    def project(self,index,bars_ahead):
        data.integer(index);data.integer(bars_ahead)
        return self.value(index+bars_ahead)

    def correct_side_distance(self,index,price):
        """Negative distance is penetration; never round or forgive it."""
        price = exact(price)
        return price-self.value(index) if self.kind == "support" else self.value(index)-price

    def record(self):
        return {"kind":self.kind,"timeframe":self.timeframe,"a_index":self.a_index,
                "a_price":rational_record(self.a_price),"b_index":self.b_index,
                "b_price":rational_record(self.b_price),"slope":rational_record(self.slope),
                "geometry_only":True}


def slope_tests(slope,atr,price_range=None,*,require_angle=False):
    if type(require_angle) is not bool:
        raise ValueError("explicit angle-profile flag required")
    slope = abs(exact(slope))
    issues = []
    atr_slope = None
    if atr is None:
        issues.append("ATR_UNAVAILABLE")
    else:
        atr = exact(atr)
        if atr < 0:raise ValueError("nonnegative ATR required")
        if atr == 0:issues.append("ZERO_ATR")
        else:
            atr_slope = slope/atr
            if atr_slope > MAX_ATR_SLOPE:issues.append("SLOPE_TOO_STEEP")
    angle_ratio = None
    if require_angle:
        if price_range is None:issues.append("ANGLE_HISTORY_UNAVAILABLE")
        else:
            price_range = exact(price_range)
            if price_range < 0:raise ValueError("nonnegative price range required")
            if price_range == 0:issues.append("ZERO_ANGLE_RANGE")
            else:
                angle_ratio = slope*ANGLE_WINDOW*CHART_ASPECT/price_range
                # atan is monotone and tan(45 degrees)=1: exact boundary decision.
                if angle_ratio > 1:issues.append("ANGLE_TOO_STEEP")
    return {"passes":not issues,"reasons":issues,"atr_slope":rational_record(atr_slope),
            "normalized_angle_ratio":rational_record(angle_ratio),"angle_required":require_angle,
            "angle_rule":"atan(normalized_ratio)<=45deg iff normalized_ratio<=1"}


@dataclass(frozen=True)
class Metrics:
    timeframe: str
    bar_index: int
    available_at: int
    publication_ordinal: int
    segment: int
    true_range: F | None
    atr_sma14: F | None
    true_range_count: int
    angle_range: F | None
    angle_bar_count: int

    def record(self):
        return {key:rational_record(value) if key in ("true_range","atr_sma14","angle_range") else value
                for key,value in self.__dict__.items()}


@data.cached_bindings
def bindings():
    result = pivots.bindings()
    for relative in ("src/forex_demo_lab/trendline/geometry.py","scripts/trendline-geometry-167.py"):
        result[relative] = hashlib.sha256((data.ROOT/relative).read_bytes()).hexdigest()
    return result


class GeometryStream:
    """Causal ATR/angle frontier and frozen per-pivot confirmation metrics."""
    def __init__(self,source,timeframe="H4"):
        self._pivots = pivots.PivotStream(source,timeframe)
        self._bindings = bindings()
        calendar = self._pivots.source.calendar
        windows = calendar.frame(timeframe)
        self._schedule = {w.start:(i,w) for i,w in enumerate(windows)}
        self._delay = calendar.delay
        self._due_times = tuple(window.end + self._delay for window in windows)
        self._bars = deque(maxlen=ANGLE_WINDOW)
        self._ranges = deque(maxlen=ATR_PERIOD)
        self._seen_lineage = set()
        self._snapshots = []
        self._confirmation = {}
        self._pivot_by_id = {}
        self._last = None
        self._last_index = None

    def _check(self):
        if self._bindings != bindings():
            raise ValueError("geometry source/protocol bindings changed")

    def fork(self):
        """Stage an independent mutable frontier; published records are immutable."""
        self._check()
        result = copy(self)
        result._pivots = self._pivots.fork()
        result._bindings = dict(self._bindings)
        result._bars = deque(self._bars,maxlen=self._bars.maxlen)
        result._ranges = deque(self._ranges,maxlen=self._ranges.maxlen)
        result._seen_lineage = set(self._seen_lineage)
        result._snapshots = list(self._snapshots)
        result._confirmation = dict(self._confirmation)
        result._pivot_by_id = dict(self._pivot_by_id)
        return result

    @property
    def timeframe(self):
        return self._pivots.timeframe

    @property
    def snapshots(self):
        return tuple(self._snapshots)

    @property
    def latest(self):
        return self._snapshots[-1] if self._snapshots else None

    @property
    def clock(self):
        return self._pivots.clock

    @property
    def journal(self):
        return self._pivots.journal

    def advance(self,now):
        self._check()
        self._pivots.advance(now)

    def observe(self,bar):
        self._check()
        if not isinstance(bar,Bar):raise ValueError("typed completed geometry bar required")
        bar = Bar(**bar.record())
        scheduled = self._schedule.get(bar.start)
        if (bar.timeframe != self.timeframe or scheduled is None or scheduled[1].end != bar.end
                or bar.available < bar.end+self._delay):
            raise ValueError("declared finalized geometry publication required")
        if bar == self._last:
            return self._pivots.observe(bar)
        if bar.lineage in self._seen_lineage:
            raise ValueError("conflicting reused geometry lineage")
        index = scheduled[0]
        gap = self._last_index is None or index != self._last_index+1
        bars = deque(() if gap else self._bars,maxlen=ANGLE_WINDOW)
        ranges = deque(() if gap else self._ranges,maxlen=ATR_PERIOD)
        tr = None if gap else true_range(bar.high,bar.low,self._last.close)
        if tr is not None:ranges.append(tr)
        bars.append(bar)
        atr = atr_sma14(ranges)
        price_range = (exact(max(b.high for b in bars))-exact(min(b.low for b in bars))
                       if len(bars) == ANGLE_WINDOW else None)
        # Fork stages pivot mutation as well as metrics, making rejection atomic.
        observer = self._pivots.fork()
        new_pivots = observer.observe(bar)
        point = Metrics(self.timeframe,index,bar.available,observer.publication_ordinal,observer.segment,
                        tr,atr,len(ranges),price_range,len(bars))
        for pivot in new_pivots:
            if pivot.id in self._pivot_by_id:raise ValueError("conflicting pivot identity")
        self._pivots = observer
        self._bars,self._ranges = bars,ranges
        self._last,self._last_index = bar,index
        self._seen_lineage.add(bar.lineage)
        self._snapshots.append(point)
        for pivot in new_pivots:
            self._confirmation[pivot.id] = point
            self._pivot_by_id[pivot.id] = pivot
        return new_pivots

    def confirmation_metrics(self,pivot_id):
        if pivot_id not in self._confirmation:raise ValueError("confirmed pivot not present")
        return self._confirmation[pivot_id]

    def touch_tolerance(self,pivot_id):
        atr = self.confirmation_metrics(pivot_id).atr_sma14
        return None if atr is None or atr == 0 else atr*TOUCH_TOLERANCE

    def ray(self,a_id,b_id):
        if a_id not in self._pivot_by_id or b_id not in self._pivot_by_id:
            raise ValueError("anchors must be confirmed in this geometry stream")
        cursor = Cursor(self.timeframe,self._pivots.clock,len(self._snapshots))
        return Ray.from_pivots(self._pivot_by_id[a_id],self._pivot_by_id[b_id],cursor)

    def coverage_state(self):
        due = bisect_right(self._due_times, self.clock) - 1
        if due < 0:return "NO_COMPLETED_BAR_DUE"
        return "MISSING_COMPLETED_BAR" if self._last_index is None or due > self._last_index else "CURRENT"

    def test_ray(self,ray,*,require_angle=False):
        self._check()
        if not isinstance(ray,Ray) or ray.timeframe != self.timeframe:
            raise ValueError("matching typed ray required")
        point = self._snapshots[-1] if self._snapshots else None
        result = slope_tests(ray.slope,None if point is None else point.atr_sma14,
                             None if point is None else point.angle_range,require_angle=require_angle)
        if self.coverage_state() != "CURRENT":
            result["reasons"].append("MISSING_COMPLETED_BAR")
            result["passes"] = False
        return result

    def report(self):
        self._check()
        piv = self._pivots.report()
        return {"schema":VERSION,"kind":"invented_trendline_geometry_report","data_level":"B",
                "geometry_basis":self._pivots.source.record()["geometry_basis"],"timeframe":self.timeframe,
                "as_of":self._pivots.clock,"source_bindings":dict(self._bindings),
                "coverage_state":self.coverage_state(),
                "latest":None if not self._snapshots else self._snapshots[-1].record(),
                "snapshots":[s.record() for s in self._snapshots],"pivots":piv["pivots"],
                "confirmations":[{"pivot_id":p.id,"metrics":self._confirmation[p.id].record(),
                                  "touch_tolerance":rational_record(self.touch_tolerance(p.id))} for p in self.journal],
                "gaps":piv["gaps"],"declaration_sha256":piv["declaration_sha256"],
                "input_sha256":piv["input_sha256"],"market_cells_run":0,"returns_computed":False,
                "qualified_market_source":False,"demo_eligible":False,"orders_available":False,
                "limitations":["geometry/ATR only; no eligible-line or trading decision claimed",
                                "fourteen true ranges require fifteen contiguous bars including prior close",
                                "normalized-angle rule is an approximation with fixed390-bar range/aspect",
                                "actual data/source/run qualification remains open"]}
