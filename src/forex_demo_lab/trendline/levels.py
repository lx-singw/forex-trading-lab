"""Causal support and resistance clusters for invented FXR replay."""
from collections import defaultdict
from statistics import median

from . import geometry, pivots

LOOKBACK_H4 = 500


def cluster(observations, tolerance):
    """Cluster typed pivots with resolved physical H4 occurrence indices."""
    physical = defaultdict(list)
    for pivot, index in observations:
        physical[pivot.kind, geometry.exact(pivot.price), index].append(pivot)

    clusters = []
    for key, evidence in sorted(physical.items()):
        kind, price, index = key
        if not clusters or clusters[-1][0] != kind or price - clusters[-1][1] > tolerance:
            clusters.append((kind, price, []))
        clusters[-1][2].append((price, index, evidence))
    return [{
        "kind": kind,
        "price": geometry.rational_record(median(point[0] for point in members)),
        "eligible": len(members) >= 2,
        "members": [_member(price, index, evidence) for price, index, evidence in members],
    } for kind, _, members in clusters]


def _member(price, index, evidence):
    sources = sorted({(p.timeframe, p.id, p.confirmed_at) for p in evidence})
    return {
        "h4_index": index,
        "price": geometry.rational_record(price),
        "sources": [{"timeframe": frame, "pivot_id": pivot_id, "confirmed_at": confirmed_at}
                    for frame, pivot_id, confirmed_at in sources],
    }


class LevelFinder:
    """Use completed D1 publications and the already staged H4 frontier."""

    def __init__(self, source):
        calendar = source.calendar
        self._delay = calendar.delay
        self._d1 = calendar.frame("D1")
        self._h4 = calendar.frame("H4")
        self._children = defaultdict(list)
        for index, window in enumerate(self._h4):
            self._children[window.session].append(index)
        self._daily = pivots.PivotStream(source, "D1")

    def observe_daily(self, bar):
        if bar.available < bar.end + self._delay:
            raise ValueError("declared finalized daily level publication required")
        self._daily.observe(bar)

    def capture(self, inspector, atr):
        index = inspector.metrics.bar_index
        as_of = inspector.clock
        first = max(0, index - LOOKBACK_H4 + 1)
        observed = dict(inspector.indexed)
        points = [(p, p.bar_index) for p in inspector.pivot_journal
                  if first <= p.bar_index <= index and p.confirmed_at <= as_of]
        unresolved = []
        for pivot in self._daily.journal:
            day = self._d1[pivot.bar_index]
            if pivot.confirmed_at > as_of or day.end <= self._h4[first].start:
                continue
            child, reason = self._daily_occurrence(pivot, observed, day)
            if reason:
                unresolved.append({"pivot_id": pivot.id, "reason": reason})
            elif first <= child <= index:
                points.append((pivot, child))
        tolerance = atr * geometry.TOUCH_TOLERANCE
        return {
            "as_of": as_of,
            "first_h4_index": first,
            "last_h4_index": index,
            "tolerance": geometry.rational_record(tolerance),
            "clusters": cluster(points, tolerance),
            "unresolved_daily": unresolved,
        }

    def _daily_occurrence(self, pivot, observed, day):
        children = self._children[day.session]
        if not all(index in observed for index in children):
            return None, "D1_H4_COVERAGE_INCOMPLETE"
        extreme = "high" if pivot.kind == "high" else "low"
        prices = {index: getattr(observed[index], extreme) for index in children}
        select = max if pivot.kind == "high" else min
        if select(prices.values()) != pivot.price:
            return None, "D1_H4_PRICE_MISMATCH"
        matches = [index for index, price in prices.items() if price == pivot.price]
        if len(matches) != 1:
            return None, "D1_H4_OCCURRENCE_AMBIGUOUS"
        return matches[0], None
