"""Build a historical development grid from a reviewed, explicit UTC schedule."""

from dataclasses import dataclass
from functools import cached_property

from ..elliott_sessions_146 import FRAMES, HOUR, Window, edges
from ..elliott_full.contracts import Bar
from . import data

KIND = "trendline_historical_session_calendar_217"
BYTE_LIMIT = 1024 * 1024


def _session_edges(values, start, end, period, partial, leading_partial):
    if leading_partial and type(values) is list and 3 <= len(values) <= 26:
        first, next_edge = values[:2]
        data.integer(first)
        data.integer(next_edge)
        if first == start and 0 < next_edge - start < period:
            edges(values[1:], next_edge, end, period, partial)
            return
    edges(values, start, end, period, partial)


@dataclass(frozen=True)
class Calendar:
    sha256: str
    start: int
    development_start: int
    end: int
    delay: int
    windows: tuple[Window, ...]

    @classmethod
    def from_record(cls, record, *, sha256, start, development_start, end, delay):
        data.fields(record, ("kind", "segments"))
        segments = record["segments"]
        if record["kind"] != KIND or type(segments) is not list or not 1 <= len(segments) <= 1600:
            raise ValueError("bounded historical session calendar required")
        cursor = start
        windows = []
        h1_count = 0
        for segment in segments:
            if type(segment) is not dict or segment.get("kind") not in ("session", "closure"):
                raise ValueError("historical session or explicit closure required")
            closed = segment["kind"] == "closure"
            fields = ("kind", "start", "end", "reason") if closed else ("kind", "start", "end", "h1", "h4", "partial")
            if not closed and "leading_partial" in segment:
                fields += ("leading_partial",)
            data.fields(segment, fields)
            left, right = segment["start"], segment["end"]
            data.integer(left)
            data.integer(right)
            if left != cursor or not left < right <= end:
                raise ValueError("calendar segments must cover reviewed scope without gaps or overlaps")
            cursor = right
            if closed:
                if segment["reason"] not in ("weekend", "holiday", "maintenance"):
                    raise ValueError("declared historical closure reason required")
                continue
            partial = segment["partial"]
            leading = segment.get("leading_partial", False)
            duration = right - left
            if type(partial) is not bool or duration > 25 * HOUR:
                raise ValueError("invalid session duration or partial policy")
            if type(leading) is not bool or (leading and not partial):
                raise ValueError("leading partial windows require explicit partial session policy")
            if not partial and duration not in (23 * HOUR, 24 * HOUR, 25 * HOUR):
                raise ValueError("short session needs explicit partial policy")
            if left < development_start < right:
                raise ValueError("session crosses the warmup and development boundary")
            hours, groups = segment["h1"], segment["h4"]
            _session_edges(hours, left, right, HOUR, partial, leading)
            _session_edges(groups, left, right, 4 * HOUR, True, leading)
            if not set(groups) <= set(hours):
                raise ValueError("parent edges must coincide with child edges")
            h1_count += len(hours) - 1
            if h1_count > data.ROW_LIMIT:
                raise ValueError("historical calendar exceeds the bounded H1 input")

            session = f"session_{left}"
            children = tuple(hours[:-1])
            windows.append(Window("D1", left, right, children, session))
            for a, b in zip(groups, groups[1:]):
                windows.append(Window("H4", a, b, tuple(t for t in children if a <= t < b), session))
            for a, b in zip(hours, hours[1:]):
                windows.append(Window("H1", a, b, (a,), session))
        if cursor != end or not windows:
            raise ValueError("historical calendar must cover the entire reviewed scope")
        return cls(sha256, start, development_start, end, delay, tuple(windows))

    @cached_property
    def _frames(self):
        return tuple(tuple(window for window in self.windows if window.timeframe == frame) for frame in FRAMES)

    def frame(self, timeframe):
        if timeframe not in FRAMES:
            raise ValueError("timeframe")
        return self._frames[FRAMES.index(timeframe)]

    def _available_at(self, window, receipts):
        if any(child not in receipts for child in window.children):
            return None
        return max(window.end + self.delay, *(receipts[child] for child in window.children))

    def publications(self, hours, cutoff):
        """Aggregate only windows fully observable through the receipt cutoff."""
        visible = {hour.start: hour for hour in hours if hour.available_at <= cutoff}
        receipts = {start: hour.available_at for start, hour in visible.items()}
        bars = []
        for window in self.windows:
            if window.timeframe == "H1":
                continue
            available = self._available_at(window, receipts)
            if available is None or available > cutoff:
                continue
            children = [visible[start] for start in window.children]
            lineage = data.digest({"calendar": self.sha256, "timeframe": window.timeframe,
                                   "children": [hour.record() for hour in children]})
            bars.append(Bar(window.timeframe, window.start, window.end, available, children[0].open,
                            max(hour.high for hour in children), min(hour.low for hour in children),
                            children[-1].close, lineage))
        return tuple(sorted(bars, key=lambda bar: (bar.available, FRAMES.index(bar.timeframe), bar.start)))

    def coverage(self, hours, *, start, cutoff):
        receipts = {hour.start: hour.available_at for hour in hours}
        report = {}
        for frame in FRAMES:
            windows = [window for window in self.frame(frame) if start <= window.start < cutoff]
            due = [window for window in windows if window.end + self.delay <= cutoff]
            missing = []
            for window in due:
                available = self._available_at(window, receipts)
                if available is None or available > cutoff:
                    missing.append(window.start)
            report[frame] = {
                "scheduled": len(windows),
                "complete_by_cutoff": len(due) - len(missing),
                "missing_due_starts": missing,
                "pending_at_cutoff": len(windows) - len(due),
            }
        return report
