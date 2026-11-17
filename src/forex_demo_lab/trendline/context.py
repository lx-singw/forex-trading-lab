"""Completed daily context for the optional H4 trendline variant."""
from bisect import bisect_right
from decimal import Decimal
import hashlib

from ..elliott_full.contracts import Bar
from . import data, engine, geometry, selection

VERSION = "TRL_CONTEXT_172_V1"
PROFILE = "TRL_BRK3_E1_D1"
DAILY_PROFILE = "D1_BRK3"
MAX_DISTANCE_ATR = 3

OUTCOMES = {
    ("LONG", "BULLISH"): "ALLOW",
    ("LONG", "BEARISH"): "CONTEXT_CONFLICT",
    ("LONG", "NEUTRAL"): "CONTEXT_NEUTRAL",
    ("LONG", "UNAVAILABLE"): "CONTEXT_UNAVAILABLE",
    ("SHORT", "BULLISH"): "CONTEXT_CONFLICT",
    ("SHORT", "BEARISH"): "ALLOW",
    ("SHORT", "NEUTRAL"): "CONTEXT_NEUTRAL",
    ("SHORT", "UNAVAILABLE"): "CONTEXT_UNAVAILABLE",
}


def outcome(trade_direction, bias):
    """Apply the D1 table to the proposed trade direction."""
    if type(trade_direction) is not str or type(bias) is not str:
        raise ValueError("declared trade direction and D1 bias required")
    try:
        return OUTCOMES[trade_direction, bias]
    except KeyError:
        raise ValueError("declared trade direction and D1 bias required") from None


def _nearest(levels, close, limit, *, below):
    distances = [(close - value if below else value - close, line_id)
                 for line_id, value in levels]
    qualifying = [(distance, line_id) for distance, line_id in distances
                  if 0 < distance <= limit]
    if not qualifying:
        return None
    distance = min(value for value, _ in qualifying)
    return {
        "line_ids": sorted(line_id for value, line_id in qualifying if value == distance),
        "value": geometry.rational_record(close - distance if below else close + distance),
        "distance": geometry.rational_record(distance),
    }


class DailyContext:
    """Advance with D1 publications, then read at the H4 receipt clock."""

    def __init__(self, source):
        self._engine = engine.Engine(source, DAILY_PROFILE, "D1")
        calendar = self._engine.source.calendar
        self._end = calendar.end + 60000
        self._due = tuple(window.end + calendar.delay for window in calendar.frame("D1"))
        self._delay = calendar.delay
        self._frame = None

    def observe(self, bar):
        self._frame = self._engine.observe(bar)

    def snapshot(self, as_of):
        data.integer(as_of)
        if not self._engine.clock <= as_of <= self._end:
            raise ValueError("D1 context query outside the available publication frontier")
        due_count = bisect_right(self._due, as_of)
        due_end = self._due[due_count - 1] - self._delay if due_count else None
        frame = self._frame
        bar = frame["bar"] if frame is not None else None
        metrics = self._engine.metrics
        atr = metrics.atr_sma14 if metrics is not None else None
        result = {
            "as_of": as_of,
            "d1_bar": None if bar is None else dict(bar),
            "d1_frame_id": None if frame is None else frame["id"],
            "latest_due_end": due_end,
            "atr_sma14": geometry.rational_record(atr),
            "S_below": None,
            "R_above": None,
            "bias": "UNAVAILABLE",
        }
        if due_end is None:
            result["reason"] = "NO_COMPLETED_D1_DUE"
        elif bar is None or bar["end"] != due_end:
            result["reason"] = "MISSING_COMPLETED_D1"
        elif frame["search_incomplete"]:
            result["reason"] = "D1_SEARCH_INCOMPLETE"
        elif atr is None or atr == 0:
            result["reason"] = "D1_ATR_UNAVAILABLE" if atr is None else "D1_ZERO_ATR"
        else:
            self._set_bias(result, frame, geometry.exact(Decimal(bar["close"])), atr)
        return result

    @staticmethod
    def _set_bias(result, frame, close, atr):
        eligible = set(frame["eligible_line_ids"])
        levels = {"support": [], "resistance": []}
        for record in frame["selection"]["ranked"]:
            line = selection.ValidatedLine.from_record(record)
            line_id = engine.instance_id(line)
            if line_id in eligible:
                levels[line.ray.kind].append((line_id, line.ray.value(frame["bar_index"])))
        support = _nearest(levels["support"], close, MAX_DISTANCE_ATR * atr, below=True)
        resistance = _nearest(levels["resistance"], close, MAX_DISTANCE_ATR * atr, below=False)
        result["S_below"], result["R_above"] = support, resistance
        result["bias"] = {
            (True, False): "BULLISH",
            (False, True): "BEARISH",
            (True, True): "NEUTRAL",
            (False, False): "UNAVAILABLE",
        }[support is not None, resistance is not None]
        result["reason"] = None if support or resistance else "NO_NEARBY_D1_LINE"


def bindings():
    result = engine.bindings()
    for path in ("src/forex_demo_lab/trendline/context.py", "scripts/trendline-context-172.py"):
        result[path] = hashlib.sha256((data.ROOT / path).read_bytes()).hexdigest()
    return result


def replay(source, publications, *, profile="TRL_BRK3_E1", as_of):
    """Join the same source's completed D1/H4 publications in bar-stream order."""
    data.integer(as_of)
    if not isinstance(publications, (tuple, list)) or len(publications) > data.ROW_LIMIT:
        raise ValueError("bounded completed D1/H4 prefix required")
    h4 = engine.Engine(source, profile, "H4")
    daily = DailyContext(source) if profile == PROFILE else None
    bound = bindings() if daily is not None else None
    decisions = []
    last_order = None
    for bar in publications:
        if not isinstance(bar, Bar) or bar.timeframe not in ("D1", "H4") or bar.available > as_of:
            raise ValueError("completed D1/H4 publications at or before as-of required")
        order = (bar.available, bar.timeframe != "D1", bar.start)
        if last_order is not None and order <= last_order:
            raise ValueError("unique D1/H4 publications in receipt order required")
        last_order = order
        if bar.timeframe == "D1":
            if daily is not None:
                daily.observe(bar)
            continue
        frame = h4.observe(bar)
        if daily is not None:
            snapshot = daily.snapshot(bar.available)
            decisions.append({
                "h4_frame_id": frame["id"],
                "snapshot": snapshot,
                "outcomes": {side: outcome(side, snapshot["bias"]) for side in ("LONG", "SHORT")},
            })
    h4.advance(as_of)
    report = h4.report()
    if daily is not None:
        if bound != bindings():
            raise ValueError("context source/protocol bindings changed during replay")
        report["context"] = {"schema": VERSION, "source_bindings": bound, "decisions": decisions}
    return report
