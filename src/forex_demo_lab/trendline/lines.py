"""Bounded, stateless line inspection on explicit invented bar prefixes.

Profile validity precedes deduplication/ranking/lifecycle. No trading decision,
formation event or execution permission is produced here.
"""
from dataclasses import dataclass
from decimal import Decimal
from itertools import combinations
import hashlib

from ..elliott_full.contracts import Bar
from . import data, geometry as g, pivots

VERSION = "TRL_LINES_168_V1"
LOOKBACK_BARS = 600
PIVOT_CAP = 256
STRATEGIES = ("TRL_BRK3_E1","TRL_FXR_M","TRL_BRK2_E1","TRL_BNC_E1","TRL_BRK3_E1_D1")
PROFILES = STRATEGIES+("D1_BRK3",)
BREAK_PROFILES = tuple(p for p in STRATEGIES if p != "TRL_BNC_E1")


def validate_profile(profile,timeframe,role):
    if profile not in PROFILES or role not in ("full","action_break"):
        raise ValueError("declared line profile and penetration role required")
    if timeframe != ("D1" if profile == "D1_BRK3" else "H4"):
        raise ValueError("profile requires its frozen timeframe")
    if role == "action_break" and profile not in BREAK_PROFILES:
        raise ValueError("current-bar exception is restricted to action breaks")


def available_pivots(values,cursor,now_index):
    """Validate declared component metadata; not proof of candle discovery."""
    if not isinstance(values,(tuple,list)) or not isinstance(cursor,g.Cursor):
        raise ValueError("ordered typed pivot collection and cursor required")
    data.integer(now_index)
    result = []
    ids,indices = set(),set()
    for pivot in values:
        if not isinstance(pivot,pivots.Pivot):raise ValueError("typed pivot required")
        data.sha(pivot.id)
        for value in (pivot.bar_index,pivot.confirmation_index,pivot.confirmed_ordinal,
                      pivot.occurred_at,pivot.confirmed_at,pivot.segment):data.integer(value)
        if (not isinstance(pivot.price,Decimal) or pivot.timeframe != cursor.timeframe
                or type(pivot.radius) is not int or pivot.radius != 3
                or pivot.kind not in ("low","high") or g.exact(pivot.price) <= 0
                or pivot.confirmation_index != pivot.bar_index+3
                or pivot.confirmation_index > now_index or pivot.confirmed_at <= pivot.occurred_at
                or pivot.confirmed_ordinal == 0
                or pivot.confirmed_ordinal > cursor.ordinal
                or (pivot.confirmed_at,pivot.confirmed_ordinal) > (cursor.available_at,cursor.ordinal)
                or pivot.id in ids or pivot.bar_index in indices):
            raise ValueError("unique confirmed pivot metadata available at this cursor required")
        ids.add(pivot.id);indices.add(pivot.bar_index);result.append(pivot)
    return tuple(sorted(result,key=lambda p:(p.bar_index,p.id)))


@dataclass(frozen=True)
class PairSearch:
    pivots: tuple
    pairs: tuple
    rejected: tuple
    high_count: int
    low_count: int
    search_incomplete: bool


def enumerate_pairs(values,cursor,now_index,segment):
    data.integer(segment)
    values = available_pivots(values,cursor,now_index)
    # Appendix A's inclusive index-distance convention, before the cap.
    window = tuple(p for p in values if now_index-p.bar_index <= LOOKBACK_BARS)
    high = sum(p.kind == "high" for p in window)
    low = len(window)-high
    incomplete = max(high,low) > PIVOT_CAP
    active = tuple(p for p in window if p.segment == segment)
    if incomplete:return PairSearch(active,(),(),high,low,True)
    pairs,rejected = [],[]
    for kind in ("low","high"):
        for a,b in combinations((p for p in active if p.kind == kind),2):
            reason = None
            if b.bar_index-a.bar_index < 6:reason = "ANCHOR_TOO_CLOSE"
            elif (b.price <= a.price if kind == "low" else b.price >= a.price):reason = "WRONG_SLOPE"
            if reason:rejected.append((a.id,b.id,reason))
            else:pairs.append((a,b,g.Ray.from_pivots(a,b,cursor)))
    return PairSearch(active,tuple(pairs),tuple(rejected),high,low,False)


@dataclass(frozen=True)
class TouchScan:
    touches: tuple
    distances: tuple
    decisions: tuple
    reasons: tuple

    def record(self):
        return {"touch_ids":[p.id for p in self.touches],
                "touch_indices":[p.bar_index for p in self.touches],
                "summed_distance":g.rational_record(sum(self.distances,g.F(0))),
                "decisions":[{"pivot_id":i,"reason":reason,"distance":g.rational_record(distance),
                              "frozen_tolerance":g.rational_record(tol)} for i,reason,distance,tol in self.decisions],
                "reasons":list(self.reasons)}


def scan_touches(ray,a,b,values,tolerances):
    """Chronological greedy acceptance; callers validate metadata/provenance."""
    if (not isinstance(ray,g.Ray) or not isinstance(tolerances,dict)
            or not isinstance(values,(list,tuple))):
        raise ValueError("typed ray and explicit frozen tolerance map required")
    if (not all(isinstance(v,pivots.Pivot) for v in (a,b,*values))
            or a.kind != b.kind or a.segment != b.segment
            or ray.kind != ("support" if a.kind == "low" else "resistance")
            or a not in values or b not in values):
        raise ValueError("same-kind confirmed touch anchors required")
    if (ray.a_index,ray.a_price,ray.b_index,ray.b_price) != (a.bar_index,a.price,b.bar_index,b.price):
        raise ValueError("touch anchors must match ray geometry")
    accepted,distances,decisions = [],[],[]
    for pivot in sorted(values,key=lambda p:(p.bar_index,p.id)):
        if pivot.bar_index < a.bar_index or pivot.kind != a.kind or pivot.segment != a.segment:continue
        if pivot.timeframe != ray.timeframe:raise ValueError("mixed touch frames")
        if pivot.id not in tolerances:raise ValueError("missing frozen tolerance binding")
        tol = tolerances[pivot.id]
        tol = None if tol is None else g.exact(tol)
        if tol is not None and tol < 0:raise ValueError("nonnegative touch tolerance required")
        distance = ray.correct_side_distance(pivot.bar_index,pivot.price)
        if tol is None or tol == 0:reason = "TOUCH_ATR_UNAVAILABLE"
        elif distance < 0:reason = "PENETRATING_PIVOT"
        elif distance > tol:reason = "OUTSIDE_TOLERANCE"
        elif accepted and pivot.bar_index-accepted[-1].bar_index < 6:reason = "TOUCH_TOO_CLOSE"
        else:
            reason = "ACCEPTED";accepted.append(pivot);distances.append(distance)
        decisions.append((pivot.id,reason,distance,tol))
    statuses = {i:reason for i,reason,_,_ in decisions}
    reasons = []
    if statuses.get(a.id) != "ACCEPTED":reasons.append("ANCHOR_ATR_UNAVAILABLE")
    if statuses.get(b.id) != "ACCEPTED":
        reasons.append("ANCHOR_SPACING_CONFLICT" if statuses.get(b.id) == "TOUCH_TOO_CLOSE" else "ANCHOR_TOUCH_UNAVAILABLE")
    return TouchScan(tuple(accepted),tuple(distances),tuple(decisions),tuple(reasons))


def penetration(ray,indexed_bars,now_index,*,include_current=True):
    """First strict penetration after A; missing bars fail coverage separately."""
    if not isinstance(ray,g.Ray) or type(include_current) is not bool:
        raise ValueError("typed ray and explicit current-bar policy required")
    data.integer(now_index)
    for index,bar in sorted(indexed_bars,key=lambda item:item[0]):
        data.integer(index)
        if not isinstance(bar,Bar) or bar.timeframe != ray.timeframe:raise ValueError("typed matching poke bar required")
        if ray.a_index < index <= now_index and (include_current or index < now_index):
            extreme = bar.low if ray.kind == "support" else bar.high
            distance = ray.correct_side_distance(index,extreme)
            if distance < 0:return (index,-distance)
    return None


def profile_tests(touches,now_index,timeframe,profile,atr,angle_range=None,*,slope):
    validate_profile(profile,timeframe,"full")
    data.integer(now_index)
    if (not isinstance(touches,(tuple,list)) or any(not isinstance(p,pivots.Pivot) for p in touches)
            or any(p.timeframe != timeframe or p.confirmation_index > now_index for p in touches)
            or len({p.id for p in touches}) != len(touches)
            or any(b.bar_index-a.bar_index < 6 or a.kind != b.kind or a.segment != b.segment
                   for a,b in zip(touches,touches[1:]))):
        raise ValueError("prior confirmed, chronologically spaced matching-frame touches required")
    count = len(touches)
    minimum = 2 if profile in ("TRL_BRK2_E1","TRL_BNC_E1") else 3
    issues = []
    if count < minimum or (profile == "TRL_BRK2_E1" and count != 2):issues.append("TOUCH_COUNT")
    age = None if not touches else now_index-touches[0].bar_index
    span = None if not touches else touches[-1].bar_index-touches[0].bar_index
    if profile == "TRL_FXR_M":
        if span is None or span < 90:issues.append("FORMATION_TOO_SHORT")
    elif age is None or age < (15 if timeframe == "D1" else 30):issues.append("LINE_TOO_YOUNG")
    slopes = g.slope_tests(slope,atr,angle_range,require_angle=profile == "TRL_FXR_M")
    issues.extend(slopes["reasons"])
    return {"passes":not issues,"reasons":issues,"age_bars":age,"formation_span_bars":span,
            "touch_count":count,"slope_tests":slopes}


def bindings():
    result = g.bindings()
    for relative in ("src/forex_demo_lab/trendline/lines.py","scripts/trendline-lines-168.py"):
        result[relative] = hashlib.sha256((data.ROOT/relative).read_bytes()).hexdigest()
    return result


def inspect(source,bars,*,timeframe="H4",profile="TRL_BRK3_E1",role="full",as_of=None):
    """Rebuild a single snapshot from an explicit prefix, never a future suffix.

    This stateless implementation intentionally does not persist lifecycle state,
    deduplicate, rank, declare formation time or emit an entry signal.
    """
    validate_profile(profile,timeframe,role)
    if not isinstance(bars,(list,tuple)) or len(bars) > pivots.MAX_BARS:
        raise ValueError("bounded explicit bar prefix required")
    source = data.Declaration.from_record(source.record())
    bound = bindings()
    observer = g.GeometryStream(source,timeframe)
    windows = {w.start:i for i,w in enumerate(source.calendar.frame(timeframe))}
    indexed = []
    if as_of is not None:data.integer(as_of)
    for bar in bars:
        if not isinstance(bar,Bar):raise ValueError("typed prefix bar required")
        if as_of is not None and bar.available > as_of:raise ValueError("prefix contains future publication")
        observer.observe(bar)
        if not indexed or bar != indexed[-1][1]:indexed.append((windows[bar.start],bar))
    if as_of is not None:observer.advance(as_of)
    report = observer.report()
    latest = observer.snapshots[-1] if observer.snapshots else None
    now_index = None if latest is None else latest.bar_index
    counts = {"high":0,"low":0}
    candidates,rejected = [],[]
    observed_indices = {i for i,_ in indexed}
    incomplete = False
    coverage = observer.coverage_state()
    if latest is not None:
        cursor = g.Cursor(timeframe,report["as_of"],latest.publication_ordinal)
        search = enumerate_pairs(observer.journal,cursor,now_index,latest.segment)
        counts = {"high":search.high_count,"low":search.low_count}
        incomplete = search.search_incomplete
        rejected = [{"a_id":a,"b_id":b,"reasons":[reason]} for a,b,reason in search.rejected]
        tolerances = {} if incomplete else {p.id:observer.touch_tolerance(p.id) for p in search.pivots}
        recent_bars = tuple((i,b) for i,b in indexed if now_index-i <= LOOKBACK_BARS)
        for a,b,ray in search.pairs:
            touches = scan_touches(ray,a,b,search.pivots,tolerances)
            poked = penetration(ray,recent_bars,now_index,include_current=role == "full")
            tests = profile_tests(touches.touches,now_index,timeframe,profile,latest.atr_sma14,
                                  latest.angle_range,slope=ray.slope)
            reasons = list(touches.reasons)
            if poked is not None:reasons.append("POKED")
            reasons.extend(tests["reasons"])
            if coverage != "CURRENT":reasons.append("MISSING_COMPLETED_BAR")
            if not all(i in observed_indices for i in range(a.bar_index,now_index+1)):
                reasons.append("LINE_COVERAGE_INCOMPLETE")
            identity = data.digest(["EURUSD",timeframe,ray.kind,a.id,b.id])
            candidates.append({"id":identity,"a_id":a.id,"b_id":b.id,"ray":ray.record(),
                               "touches":touches.record(),"profile_tests":tests,
                               "first_penetration":None if poked is None else {"bar_index":poked[0],"distance":g.rational_record(poked[1])},
                               "profile_valid":not reasons,"reasons":reasons})
    if bindings() != bound:raise ValueError("line source/protocol bindings changed during inspection")
    return {"schema":VERSION,"kind":"invented_trendline_line_inspection","data_level":"B",
            "geometry_basis":source.record()["geometry_basis"],"timeframe":timeframe,"profile":profile,
            "penetration_role":role,"as_of":report["as_of"],"bar_index":now_index,
            "declaration_sha256":source.sha256,"input_sha256":source.record()["input_sha256"],
            "source_bindings":bound,"coverage_state":coverage,"lookback_index_distance":LOOKBACK_BARS,
            "window_pivot_counts":counts,"search_incomplete":incomplete,"pair_rejections":rejected,
            "snapshot_reasons":(["SEARCH_INCOMPLETE"] if incomplete else [])+
                               (["MISSING_COMPLETED_BAR"] if coverage != "CURRENT" else []),
            "candidates":candidates,"profile_valid_ids":[c["id"] for c in candidates if c["profile_valid"]],
            "entry_ready":False,"market_cells_run":0,"returns_computed":False,
            "qualified_market_source":False,"demo_eligible":False,"orders_available":False,
            "limitations":["stateless profile validity only; deduplication/ranking/lifecycle pending",
                            "action-break inspection excludes current bar but does not establish a trigger",
                            "no formation-time, consumption, safety selection or execution decision",
                            "actual source/run qualification remains open"]}
