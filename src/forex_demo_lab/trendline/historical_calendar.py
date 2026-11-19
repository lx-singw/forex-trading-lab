"""Build a historical development grid from a reviewed, explicit UTC schedule."""

from dataclasses import dataclass

from ..elliott_sessions_146 import FRAMES, HOUR, Window, edges
from . import data

KIND = "trendline_historical_session_calendar_217"
BYTE_LIMIT = 1024 * 1024


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
            data.fields(segment, ("kind", "start", "end", "reason") if closed else
                        ("kind", "start", "end", "h1", "h4", "partial"))
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
            duration = right - left
            if type(partial) is not bool or duration > 25 * HOUR:
                raise ValueError("invalid session duration or partial policy")
            if not partial and duration not in (23 * HOUR, 24 * HOUR, 25 * HOUR):
                raise ValueError("short session needs explicit partial policy")
            if left < development_start < right:
                raise ValueError("session crosses the warmup and development boundary")
            hours, groups = segment["h1"], segment["h4"]
            edges(hours, left, right, HOUR, partial)
            edges(groups, left, right, 4 * HOUR, True)
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

    def frame(self, timeframe):
        if timeframe not in FRAMES:
            raise ValueError("timeframe")
        return tuple(window for window in self.windows if window.timeframe == timeframe)

    def coverage(self, hours, *, start, cutoff):
        receipts = {hour.start: hour.available_at for hour in hours}
        report = {}
        for frame in FRAMES:
            windows = [window for window in self.frame(frame) if start <= window.start < cutoff]
            due = [window for window in windows if window.end + self.delay <= cutoff]
            missing = [
                window.start for window in due
                if any(child not in receipts or receipts[child] > cutoff for child in window.children)
            ]
            report[frame] = {
                "scheduled": len(windows),
                "complete_by_cutoff": len(due) - len(missing),
                "missing_due_starts": missing,
                "pending_at_cutoff": len(windows) - len(due),
            }
        return report
