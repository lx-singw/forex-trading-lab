"""Explicit, causal session observations for invented research inputs only.

This is a calendar/aggregation component, not a qualified data or execution
adapter. UTC edges are declarations, never inferred timezone/provider facts.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re

from .elliott_full.contracts import Bar, digest, integer

HOUR = 3_600_000
FRAMES = ("D1", "H4", "H1")
VERSION = "FXDL_ELLIOTT_SESSIONS146_V1"
START = int(datetime(2000, 1, 1, tzinfo=timezone.utc).timestamp()*1000)
END = int(datetime(2004, 1, 1, tzinfo=timezone.utc).timestamp()*1000)


def source_bindings():
    root = Path(__file__).resolve().parent
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (Path(__file__).resolve(), root/"elliott_full"/"contracts.py")}


def fields(value, keys):
    if type(value) is not dict or set(value) != set(keys):
        raise ValueError("exact session fields required")


def edges(values, start, end, period, partial):
    if type(values) is not list or not 2 <= len(values) <= 26:
        raise ValueError("bounded explicit edges required")
    for value in values:
        integer(value)
    if values[0] != start or values[-1] != end:
        raise ValueError("edges must cover entire declared session")
    lengths = [b-a for a, b in zip(values, values[1:])]
    if any(length != period for length in lengths[:-1]):
        raise ValueError("only terminal intraday bar may be shortened")
    if not 0 < lengths[-1] <= period or (lengths[-1] != period and not partial):
        raise ValueError("shortened terminal bar needs explicit policy")


@dataclass(frozen=True)
class Window:
    timeframe: str
    start: int
    end: int
    children: tuple
    session: str


@dataclass(frozen=True)
class Calendar:
    """Use from_record; serialized input and all indexes are immutable copies."""
    _json: str
    windows: tuple
    delay: int
    start: int
    end: int

    @classmethod
    def from_record(cls, value):
        fields(value, ("kind", "scope", "finalization_delay_ms", "segments"))
        if value["kind"] != "invented_session_calendar_146":
            raise ValueError("invented calendar only; market admission unavailable")
        fields(value["scope"], ("start", "end"))
        start, end = value["scope"]["start"], value["scope"]["end"]
        integer(start); integer(end)
        if not START <= start < end <= END or end-start > 800*25*HOUR:
            raise ValueError("bounded invented 2000-2003 scope required")
        delay = value["finalization_delay_ms"]
        integer(delay)
        if not 0 <= delay <= 60_000:
            raise ValueError("finalization delay policy")
        segments = value["segments"]
        if type(segments) is not list or not 1 <= len(segments) <= 1600:
            raise ValueError("bounded explicit calendar required")
        cursor, labels, windows = start, set(), []
        for row in segments:
            if type(row) is not dict or row.get("kind") not in ("session", "closure"):
                raise ValueError("session or declared closure required")
            keys = (("kind", "label", "start", "end", "h1", "h4", "partial")
                    if row["kind"] == "session" else ("kind", "start", "end", "reason"))
            fields(row, keys)
            a, b = row["start"], row["end"]
            integer(a); integer(b)
            if a != cursor or not a < b <= end:
                raise ValueError("calendar gap/overlap/order; no implicit closures")
            cursor = b
            if row["kind"] == "closure":
                if row["reason"] not in ("weekend", "holiday", "maintenance", "invented"):
                    raise ValueError("declared closure reason required")
                continue
            label = row["label"]
            if type(label) is not str or not re.fullmatch(r"session_[a-z0-9_]{1,48}", label) or label in labels:
                raise ValueError("unique anonymous session label required")
            labels.add(label)
            if type(row["partial"]) is not bool or b-a > 25*HOUR:
                raise ValueError("session duration/partial policy")
            if not row["partial"] and b-a not in (23*HOUR, 24*HOUR, 25*HOUR):
                raise ValueError("short session needs explicit partial policy")
            # A 23/25-hour declared day can have a shortened final H4 bucket.
            edges(row["h1"], a, b, HOUR, row["partial"])
            edges(row["h4"], a, b, 4*HOUR, True)
            if not set(row["h4"]) <= set(row["h1"]):
                raise ValueError("parent edges must coincide with child edges")
            children = tuple(row["h1"][:-1])
            windows.append(Window("D1", a, b, children, label))
            for x, y in zip(row["h4"], row["h4"][1:]):
                windows.append(Window("H4", x, y, tuple(t for t in children if x <= t < y), label))
            for x, y in zip(row["h1"], row["h1"][1:]):
                windows.append(Window("H1", x, y, (x,), label))
        if cursor != end or not labels or len(labels) > 800 or len(windows) > 27000:
            raise ValueError("complete bounded calendar required")
        encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
        return cls(encoded, tuple(windows), delay, start, end)

    def record(self):
        return json.loads(self._json)

    @property
    def sha256(self):
        return digest(self.record())

    def frame(self, timeframe):
        if timeframe not in FRAMES:
            raise ValueError("timeframe")
        return tuple(w for w in self.windows if w.timeframe == timeframe)

    def consecutive(self, timeframe, previous_start, next_start):
        """True only for adjacent *scheduled* bars, including declared closures."""
        integer(previous_start); integer(next_start)
        starts = [w.start for w in self.frame(timeframe)]
        try:
            i = starts.index(previous_start)
        except ValueError:
            return False
        return i+1 < len(starts) and starts[i+1] == next_start


class Observations:
    """Ordered receipt journal; complete observations cannot backdate publication.

    H1 OHLC observations do not prove underlying quote coverage, executable
    spreads or costs. No missing child is filled or synthesized.
    """
    def __init__(self, calendar):
        # Revalidate even a manually constructed Calendar before any observation.
        self.calendar = Calendar.from_record(calendar.record())
        if self.calendar != calendar:
            raise ValueError("calendar index does not match declaration")
        self.clock = calendar.start
        self._calendar_sha = calendar.sha256
        self._bindings = source_bindings()
        self._hours = {}
        self._journal = []
        self._scheduled = {w.start: w for w in calendar.frame("H1")}

    def advance(self, now):
        integer(now)
        if not self.clock <= now <= self.calendar.end+60_000:
            raise ValueError("monotonic bounded receipt clock required")
        self.clock = now

    def observe(self, bar):
        if not isinstance(bar, Bar) or bar.timeframe != "H1":
            raise ValueError("completed H1 observation required")
        if type(bar.lineage) is not str or not re.fullmatch(r"[0-9a-f]{64}", bar.lineage):
            raise ValueError("immutable SHA256 observation lineage required")
        window = self._scheduled.get(bar.start)
        if window is None or bar.end != window.end:
            raise ValueError("observation outside scheduled H1 window")
        if bar.start in self._hours:
            raise ValueError("duplicate observation; revisions require a new study")
        if not self.clock <= bar.available <= self.calendar.end+60_000:
            raise ValueError("receipt order/boundary")
        # Validate all conditions before mutating the journal or clock.
        self._hours[bar.start] = bar
        self._journal.append(bar.record())
        self.clock = bar.available

    def bars(self):
        result = []
        for w in self.calendar.windows:
            if any(t not in self._hours for t in w.children):
                continue
            children = [self._hours[t] for t in w.children]
            available = max(w.end+self.calendar.delay, *(b.available for b in children))
            if available > self.clock:
                continue
            lineage = digest({"calendar": self._calendar_sha, "session": w.session,
                              "timeframe": w.timeframe, "children": [b.record() for b in children]})
            result.append(Bar(w.timeframe, w.start, w.end, available,
                              children[0].open, max(b.high for b in children),
                              min(b.low for b in children), children[-1].close, lineage))
        return tuple(sorted(result, key=lambda b: (b.available, FRAMES.index(b.timeframe), b.start)))

    def status(self, timeframe):
        due = [w for w in self.calendar.frame(timeframe) if w.end+self.calendar.delay <= self.clock]
        published = {b.start: b for b in self.bars() if b.timeframe == timeframe}
        missing = [w.start for w in due if w.start not in published]
        latest = due[-1].start if due else None
        return {"state": ("no_completed_bar" if not due else
                          "missing_completed_bar" if missing else "ready"),
                "latest_due_start": latest, "missing_starts": missing,
                "complete_count": len(published), "as_of": self.clock,
                "historical_coverage_complete": not missing}

    def checkpoint(self):
        if self._bindings != source_bindings():
            raise ValueError("observation source changed during run")
        payload = {"schema": VERSION, "calendar_sha256": self.calendar.sha256,
                   "source_bindings": self._bindings,
                   "clock": self.clock, "observations": list(self._journal)}
        # Deep copy; caller mutation cannot alter the running journal.
        return json.loads(json.dumps({"payload": payload, "sha256": digest(payload)}))

    @classmethod
    def restore(cls, calendar, checkpoint):
        fields(checkpoint, ("payload", "sha256"))
        payload = checkpoint["payload"]
        fields(payload, ("schema", "calendar_sha256", "source_bindings", "clock", "observations"))
        if (payload["schema"] != VERSION or payload["calendar_sha256"] != calendar.sha256
                or payload["source_bindings"] != source_bindings()
                or digest(payload) != checkpoint["sha256"]):
            raise ValueError("checkpoint schema/calendar/content mismatch")
        if type(payload["observations"]) is not list or len(payload["observations"]) > 20000:
            raise ValueError("bounded observation journal required")
        stream = cls(calendar)
        for row in payload["observations"]:
            fields(row, ("timeframe", "start", "end", "available", "open", "high", "low", "close", "lineage"))
            stream.observe(Bar(**row))
        stream.advance(payload["clock"])
        return stream

    def report(self):
        return {"schema": VERSION, "kind": "invented_session_observations_146",
                "calendar_sha256": self.calendar.sha256, "as_of": self.clock,
                "bars": [b.record() for b in self.bars()],
                "coverage": {f: self.status(f) for f in FRAMES},
                "qualified_runner_available": False, "orders_available": False,
                "market_cells_run": 0, "returns_computed": False,
                "limitations": ["invented OHLC; underlying quote coverage not established",
                                "UTC edges declared; no provider/DST facts verified",
                                "not connected to strategy, frozen controls or native APIs"]}
