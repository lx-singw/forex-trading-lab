"""Broker-free snapshot adapter model. Every input and journal is invented."""

from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from decimal import Decimal
import hashlib
import json
import math
from pathlib import Path
import sqlite3

CONTRACT103 = "12f23053486464a73bca41b8784e8a94a6820948f2b30b4acd46dea2e0486662"
SCHEMA = "snapshot_collector_104_invented_v1"
MAX_BYTES = 16 * 1024 * 1024
TABLES = {
    "metadata": "CREATE TABLE metadata (value TEXT NOT NULL)",
    "events": "CREATE TABLE events (sequence INTEGER PRIMARY KEY, payload TEXT NOT NULL, sha256 TEXT NOT NULL)",
    "head": "CREATE TABLE head (sequence INTEGER NOT NULL, sha256 TEXT NOT NULL)",
}
GUARDS = {"demo_ok", "guard_unavailable", "account_mode_rejected", "disconnected",
          "algo_enabled", "instrument_rejected", "identity_invalid", "account_changed"}


@dataclass(frozen=True)
class Policy:
    max_reads: int = 120
    max_events: int = 1024
    max_session_ms: int = 60000
    gap_ms: int = 2000
    jump_tolerance_ms: int = 500

    def __post_init__(self):
        for value, low, high in ((self.max_reads, 1, 1000), (self.max_events, 4, 10000),
                                 (self.max_session_ms, 1, 60000), (self.gap_ms, 1, 3600000),
                                 (self.jump_tolerance_ms, 1, 1000)):
            if type(value) is not int or not low <= value <= high:
                raise ValueError("invalid_bounded_policy")


@dataclass(frozen=True)
class Clock:
    utc: datetime
    monotonic_ns: int


@dataclass(frozen=True)
class Guard:
    trade_mode: int = 0  # Invented DEMO enum; never an actual SDK account certificate.
    connected: bool = True
    algo_trading: bool = False
    currency: str = "USD"
    symbol: str = "EURUSD"
    visible: bool = True
    base: str = "EUR"
    quote: str = "USD"
    identity: bytes = field(default=b"invented-role-A", repr=False)


@dataclass(frozen=True)
class Tick:
    time_s: int
    time_msc: int
    bid: float
    ask: float
    last: float = 0.0
    volume: int = 0
    flags: int = 2
    volume_real: float = 0.0


@dataclass(frozen=True)
class Frame:
    before: object
    tick: object
    after: object
    kind: str = "poll_snapshot"
    error: object = field(default=None, repr=False)


class ReplaySource:
    """Stored invented frames only. No callback, adapter, SDK or attachment."""

    def __init__(self, frames):
        if type(frames) not in (list, tuple) or len(frames) > 1000 or any(
                type(f) is not Frame or f.kind not in ("poll_snapshot", "late_history_model") for f in frames):
            raise ValueError("invented_frames_required")
        self._frames = iter(tuple(frames))
        self.calls = []

    def frame(self):
        return next(self._frames)

    def guard(self, frame, stage):
        self.calls.append(stage)
        return frame.before if stage == "before" else frame.after

    def read(self, frame):
        self.calls.append("read")
        if frame.error is not None:
            raise ValueError("invented_read_failure")
        return frame.tick


class ReplayClock:
    def __init__(self, readings):
        if type(readings) not in (list, tuple) or len(readings) > 10000:
            raise ValueError("invented_clock_readings_required")
        self._readings = iter(tuple(readings))
        self.calls = 0

    def read(self):
        self.calls += 1
        try:
            return next(self._readings)
        except StopIteration:
            return None


def connect_broker():
    raise ValueError("broker_entry_disabled")


def _json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _hash(value):
    return hashlib.sha256(_json(value).encode()).hexdigest()


def _clock(value):
    if type(value) is not Clock or type(value.utc) is not datetime or type(value.monotonic_ns) is not int:
        return None
    try:
        if value.utc.tzinfo is None or value.utc.utcoffset() is None or not 0 <= value.monotonic_ns < 2**63:
            return None
        return dict(utc=value.utc.astimezone(timezone.utc).isoformat(timespec="microseconds"),
                    monotonic_ns=value.monotonic_ns)
    except (ValueError, OverflowError):
        return None


def _clock_check(value):
    if value is not None and _clock(Clock(datetime.fromisoformat(value["utc"]), value["monotonic_ns"])) != value:
        raise ValueError("invalid_clock_encoding")


def _native(value, positive=False):
    if type(value) is not float or not math.isfinite(value) or not (0 < value < 1000 if positive else 0 <= value < 1e12):
        raise ValueError("invalid_native_price")
    return dict(hex=value.hex(), decimal_text=str(Decimal(str(value))))


def _tick(value):
    if type(value) is not Tick:
        return None
    try:
        for number, high in ((value.time_s, 2**63 - 1), (value.time_msc, 2**63 - 1),
                             (value.volume, 2**63 - 1), (value.flags, 2**32 - 1)):
            if type(number) is not int or not 0 <= number <= high:
                return None
        if value.time_msc <= 0 or value.time_s != value.time_msc // 1000 or value.bid > value.ask:
            return None
        return dict(time_s=value.time_s, time_msc=value.time_msc,
                    bid=_native(value.bid, True), ask=_native(value.ask, True),
                    last=_native(value.last), volume=value.volume, flags=value.flags,
                    volume_real=_native(value.volume_real))
    except (ValueError, TypeError, ArithmeticError):
        return None


def _tick_check(value):
    parsed = Tick(value["time_s"], value["time_msc"], float.fromhex(value["bid"]["hex"]),
                  float.fromhex(value["ask"]["hex"]), float.fromhex(value["last"]["hex"]),
                  value["volume"], value["flags"], float.fromhex(value["volume_real"]["hex"]))
    if _tick(parsed) != value:
        raise ValueError("invalid_snapshot_encoding")


def _guard(value, identity):
    if type(value) is not Guard:
        return "guard_unavailable", identity
    if type(value.trade_mode) is not int or value.trade_mode != 0:
        return "account_mode_rejected", identity
    if value.connected is not True:
        return "disconnected", identity
    if value.algo_trading is not False:
        return "algo_enabled", identity
    if (value.currency, value.symbol, value.visible, value.base, value.quote) != ("USD", "EURUSD", True, "EUR", "USD") or value.visible is not True:
        return "instrument_rejected", identity
    if type(value.identity) is not bytes or not 1 <= len(value.identity) <= 64:
        return "identity_invalid", identity
    if identity is not None and value.identity != identity:
        return "account_changed", identity
    return "demo_ok", value.identity


def _metadata(policy):
    if type(policy) is not Policy:
        raise ValueError("invalid_policy_type")
    Policy.__post_init__(policy)
    return dict(schema=SCHEMA, source="invented:snapshot-collector-104", synthetic=True,
                symbol="EURUSD", sampling="poll_snapshot_model", contract103_sha256=CONTRACT103,
                price_encoding="native_float_hex_and_Decimal_str_float",
                source_clock="raw_unverified", receipt_clock="injected_for_offline_tests",
                source_utc_certified=False, provider_tick_identity=False, market_data_qualified=False,
                broker_entry_available=False, orders_available=False,
                policy={k: getattr(policy, k) for k in ("max_reads", "max_events", "max_session_ms", "gap_ms", "jump_tolerance_ms")})


def _state():
    return dict(session=0, start=None, within=None, wall=None, reads=0, pending=None, stop=None,
                last_tick=None, last_tick_session=None, change_mono=None, source_high=None, observed=[])


def _relation(previous, current, policy):
    if current is None:
        return "invalid_receipt_clock"
    if previous is None:
        return None
    wall = datetime.fromisoformat(current["utc"]) - datetime.fromisoformat(previous["utc"])
    mono = current["monotonic_ns"] - previous["monotonic_ns"]
    if wall < timedelta(0) or mono < 0:
        return "receipt_clock_reversed"
    wall_ns = (wall.days * 86400 + wall.seconds) * 10**9 + wall.microseconds * 1000
    return "receipt_clock_jump" if abs(wall_ns - mono) > policy.jump_tolerance_ms * 10**6 else None


def _before_issue(state, clock, policy):
    issue = _relation(state["within"], clock, policy)
    if issue is None and clock["monotonic_ns"] - state["start"]["monotonic_ns"] >= policy.max_session_ms * 10**6:
        issue = "session_deadline_exhausted"
    return issue


def _outcome_issue(state, data, policy):
    if data["guard_before"] != "demo_ok":
        return data["guard_before"]
    issue = _before_issue(state, data["received_before"], policy)
    if issue:
        return issue
    if data["guard_after"] != "demo_ok":
        return data["guard_after"]
    issue = _relation(data["received_before"], data["received_after"], policy)
    issue = issue or _relation(data["received_after"], data["guard_completed"], policy)
    if issue:
        return issue
    if data["guard_completed"]["monotonic_ns"] - state["start"]["monotonic_ns"] > policy.max_session_ms * 10**6:
        return "session_deadline_exhausted"
    return "read_failure" if data["read_error"] else None


def _apply(state, kind, data, policy, sequence):
    flags = []
    if kind == "session":
        if set(data) != {"clock"} or data["clock"] is None or state["pending"] is not None or state["stop"]:
            raise ValueError("journal_acquisition_blocked")
        _clock_check(data["clock"])
        if state["wall"] is not None and data["clock"]["utc"] < state["wall"]:
            raise ValueError("restart_wall_clock_reversed")
        if state["session"]:
            flags = ["session_boundary", "restart_gap"]
        state["session"] += 1
        state["start"] = state["within"] = data["clock"]
        state["wall"] = data["clock"]["utc"]
        state["change_mono"] = None
        return dict(status="session_started", flags=flags, session=state["session"])
    if state["session"] == 0 or state["stop"]:
        raise ValueError("journal_acquisition_blocked")
    if kind == "attempt":
        if data != {"session": state["session"]} or state["pending"] is not None or state["reads"] >= policy.max_reads:
            raise ValueError("attempt_not_admitted")
        state["pending"] = sequence
        state["reads"] += 1
        return dict(status="attempt_reserved", flags=[], session=state["session"])
    if kind == "decision":
        if set(data) != {"session", "clock"} or data["session"] != state["session"] or state["pending"] is not None:
            raise ValueError("decision_not_admitted")
        _clock_check(data["clock"])
        issue = _before_issue(state, data["clock"], policy)
        if issue is None and data["clock"]["utc"] <= state["wall"]:
            issue = "decision_not_after_record"
        if issue:
            state["stop"] = issue
            return dict(status="stopped", reason=issue, flags=[issue], visible=[])
        state["within"] = data["clock"]
        state["wall"] = data["clock"]["utc"]
        return dict(status="model_decision", flags=[], visible=[s for s, utc in state["observed"] if utc < data["clock"]["utc"]])
    if kind != "outcome" or set(data) != {"attempt", "session", "attempt_kind", "read_called", "read_error", "guard_before", "guard_after",
                                          "received_before", "received_after", "guard_completed", "input_kind", "tick"}:
        raise ValueError("invalid_event_shape")
    if data["attempt"] != state["pending"] or type(data["attempt"]) is not int or data["session"] != state["session"]:
        raise ValueError("outcome_without_attempt")
    if data["attempt_kind"] not in ("poll_snapshot", "late_history_model") or type(data["read_called"]) is not bool or type(data["read_error"]) is not bool:
        raise ValueError("invalid_attempt_encoding")
    if data["guard_before"] not in GUARDS or data["guard_after"] not in GUARDS | {"not_called"}:
        raise ValueError("invalid_guard_encoding")
    for k in ("received_before", "received_after", "guard_completed"):
        _clock_check(data[k])
    pre_issue = data["guard_before"] != "demo_ok" or _before_issue(state, data["received_before"], policy) is not None
    if data["read_called"] == pre_issue or (not data["read_called"] and (data["received_after"] is not None or data["guard_completed"] is not None or data["guard_after"] != "not_called" or data["read_error"])):
        raise ValueError("inconsistent_read_boundary")
    if data["read_called"] and data["guard_after"] == "not_called":
        raise ValueError("missing_after_guard")
    issue = _outcome_issue(state, data, policy)
    if issue:
        if data["input_kind"] != "discarded" or data["tick"] is not None:
            raise ValueError("unsafe_quote_retained")
        state["stop"] = issue
        result = dict(status="stopped", reason=issue, flags=[issue])
    else:
        if data["input_kind"] not in ("quote", "missing", "invalid"):
            raise ValueError("invalid_input_kind")
        prior_clock = state["within"]
        if datetime.fromisoformat(data["received_before"]["utc"]) - datetime.fromisoformat(prior_clock["utc"]) > timedelta(milliseconds=policy.gap_ms):
            flags.append("receipt_gap")
        if data["input_kind"] != "quote":
            if data["tick"] is not None:
                raise ValueError("unsafe_input_retained")
            flags.append("missing_quote" if data["input_kind"] == "missing" else "invalid_snapshot")
            result = dict(status=data["input_kind"], flags=flags)
        else:
            _tick_check(data["tick"])
            tick = data["tick"]
            flags.append("source_age_unverified")
            if tick["flags"] & ~126:
                flags.append("unknown_flags_preserved")
            if data["attempt_kind"] == "late_history_model":
                flags.append("late_history_availability")
            high = state["source_high"]
            if high is not None and tick["time_msc"] < high:
                flags.append("raw_source_clock_backwards")
            if high is not None and tick["time_msc"] - high > policy.gap_ms:
                flags.append("raw_source_gap")
            repeat = tick == state["last_tick"]
            if repeat:
                flags.append("repeated_snapshot")
            elif state["last_tick"] is not None and tick["time_msc"] == state["last_tick"]["time_msc"]:
                flags.append("same_time_changed_snapshot")
            mono = data["received_after"]["monotonic_ns"]
            same_session = state["last_tick_session"] == state["session"]
            repeated_ms = (mono - state["change_mono"]) / 10**6 if repeat and same_session and state["change_mono"] is not None else None
            if not repeat or not same_session:
                state["change_mono"] = mono
            state["last_tick"], state["last_tick_session"] = tick, state["session"]
            state["source_high"] = max(high or 0, tick["time_msc"])
            state["observed"].append((sequence, data["guard_completed"]["utc"]))
            result = dict(status="observed_model", flags=flags, source_age_ms=None, repeated_snapshot_ms=repeated_ms)
        state["within"] = data["guard_completed"]
        state["wall"] = data["guard_completed"]["utc"]
    state["pending"] = None
    return result


class Journal:
    """Separate invented104 schema; committed attempts/outcomes are restart state."""

    def __init__(self, db, path):
        self._db, self.path = db, Path(path)

    @classmethod
    def create(cls, path, policy=Policy()):
        metadata = _metadata(policy)
        path = Path(path)
        with path.open("xb"):
            pass
        j = cls._connect(path)
        try:
            j._db.execute("BEGIN IMMEDIATE")
            for sql in TABLES.values():
                j._db.execute(sql)
            j._db.execute("INSERT INTO metadata VALUES (?)", (_json(metadata),))
            j._db.execute("INSERT INTO head VALUES (?,?)", (0, _hash(metadata)))
            j._db.execute("COMMIT")
            j._history()
            return j
        except BaseException:
            j.close()
            raise

    @classmethod
    def _connect(cls, path):
        path = Path(path)
        if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_BYTES:
            raise ValueError("invalid_bounded_journal")
        db = sqlite3.connect(path.resolve().as_uri() + "?mode=rw", uri=True, timeout=0, isolation_level=None)
        try:
            db.execute("PRAGMA trusted_schema=OFF")
            db.execute("PRAGMA synchronous=FULL")
        except BaseException:
            db.close()
            raise
        return cls(db, path)

    @classmethod
    def resume(cls, path):
        j = cls._connect(path)
        try:
            j._history()
            return j
        except BaseException:
            j.close()
            raise

    def _history(self):
        if self.path.stat().st_size > MAX_BYTES:
            raise ValueError("journal_file_limit")
        objects = self._db.execute("SELECT type,name,sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%'").fetchall()
        if sorted(objects) != sorted(("table", name, sql) for name, sql in TABLES.items()):
            raise ValueError("unexpected_schema")
        if self._db.execute("PRAGMA quick_check").fetchall() != [("ok",)] or self._db.execute("PRAGMA journal_mode").fetchone() != ("delete",):
            raise ValueError("journal_integrity_failure")
        rows = self._db.execute("SELECT value FROM metadata").fetchall()
        if len(rows) != 1:
            raise ValueError("invalid_metadata")
        try:
            metadata = json.loads(rows[0][0])
            policy = Policy(**metadata["policy"])
            if metadata != _metadata(policy) or rows[0][0] != _json(metadata):
                raise ValueError("changed_metadata")
            state, chain, events = _state(), _hash(metadata), []
            rows = self._db.execute("SELECT sequence,payload,sha256 FROM events ORDER BY sequence LIMIT ?", (policy.max_events + 1,)).fetchall()
            if len(rows) > policy.max_events:
                raise ValueError("journal_event_limit")
            for index, (sequence, text, checksum) in enumerate(rows, 1):
                body = json.loads(text)
                derived = _apply(state, body["kind"], body["data"], policy, index)
                expected = dict(sequence=index, kind=body["kind"], data=body["data"], derived=derived, previous_sha256=chain)
                if sequence != index or body != expected or text != _json(expected) or checksum != _hash(expected):
                    raise ValueError("history_mismatch")
                events.append(body)
                chain = checksum
        except (ValueError, TypeError, KeyError, ArithmeticError, OverflowError) as exc:
            raise ValueError("invalid_journal_history") from exc
        if self._db.execute("SELECT sequence,sha256 FROM head").fetchall() != [(len(events), chain)]:
            raise ValueError("head_mismatch")
        return policy, state, chain, events

    def _insert(self, body):
        self._db.execute("INSERT INTO events VALUES (?,?,?)", (body["sequence"], _json(body), _hash(body)))
        self._db.execute("UPDATE head SET sequence=?,sha256=?", (body["sequence"], _hash(body)))

    def _append(self, kind, data, tick=None):
        try:
            self._db.execute("BEGIN IMMEDIATE")
            policy, state, chain, events = self._history()
            reserve = 2 if kind == "attempt" else 1
            if len(events) + reserve > policy.max_events:
                raise ValueError("journal_event_budget")
            if kind == "outcome":
                data = dict(data)
                if _outcome_issue(state, data, policy):
                    data.update(input_kind="discarded", tick=None)
                else:
                    encoded = _tick(tick)
                    data.update(input_kind="missing" if tick is None else "quote" if encoded is not None else "invalid", tick=encoded)
            derived = _apply(state, kind, data, policy, len(events) + 1)
            body = dict(sequence=len(events) + 1, kind=kind, data=data, derived=derived, previous_sha256=chain)
            self._insert(body)
            self._db.execute("COMMIT")
            return body
        except BaseException:
            if self._db.in_transaction:
                self._db.execute("ROLLBACK")
            raise

    def start_session(self, clock):
        return self._append("session", dict(clock=_clock(clock)))["derived"]["session"]

    def begin_attempt(self, session):
        return self._append("attempt", dict(session=session))["sequence"]

    def before_issue(self, clock):
        policy, state, _, _ = self._history()
        return _before_issue(state, _clock(clock), policy)

    def finish(self, data, tick):
        return self._append("outcome", data, tick)

    def decision(self, session, clock):
        return self._append("decision", dict(session=session, clock=_clock(clock)))

    def visible(self, decision_sequence):
        if type(decision_sequence) is not int:
            raise ValueError("recorded_model_decision_required")
        events = self.events()
        if not 1 <= decision_sequence <= len(events) or events[decision_sequence - 1]["derived"]["status"] != "model_decision":
            raise ValueError("recorded_model_decision_required")
        return tuple(events[decision_sequence - 1]["derived"]["visible"])

    def events(self):
        return tuple(self._history()[3])

    def summary(self):
        _, state, chain, events = self._history()
        return dict(schema=SCHEMA, source="invented:snapshot-collector-104", synthetic=True,
                    events=len(events), attempts=state["reads"], sessions=state["session"],
                    statuses={s: sum(e["derived"]["status"] == s for e in events) for s in
                              ("observed_model", "missing", "invalid", "stopped", "model_decision")},
                    flags=sorted({f for e in events for f in e["derived"]["flags"]}),
                    pending_attempt=state["pending"], stop_reason=state["stop"], chain_sha256=chain,
                    broker_entry_available=False, market_data_qualified=False, orders_available=False)

    def close(self):
        self._db.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


class Collector:
    """Only fixed replay objects can enter this model; no actual broker adapter."""

    def __init__(self, journal, source, clock):
        if type(journal) is not Journal or type(source) is not ReplaySource or type(clock) is not ReplayClock:
            raise ValueError("broker_free_replay_objects_required")
        self.journal, self.source, self.clock = journal, source, clock
        self._identity, self.stopped = None, False
        self.session = journal.start_session(clock.read())

    def poll(self):
        if self.stopped:
            raise ValueError("collector_stopped")
        try:
            attempt = self.journal.begin_attempt(self.session)
            data = dict(attempt=attempt, session=self.session, attempt_kind="poll_snapshot", read_called=False,
                        read_error=False, guard_before="guard_unavailable", guard_after="not_called",
                        received_before=None, received_after=None, guard_completed=None)
            tick = None
            try:
                frame = self.source.frame()
            except StopIteration:
                frame = None
            if frame is not None:
                data["attempt_kind"] = frame.kind
                code, identity = _guard(self.source.guard(frame, "before"), self._identity)
                data["guard_before"] = code
                if code == "demo_ok":
                    self._identity = identity
                    before = self.clock.read()
                    data["received_before"] = _clock(before)
                    if self.journal.before_issue(before) is None:
                        data["read_called"] = True
                        try:
                            tick = self.source.read(frame)
                        except Exception:
                            data["read_error"] = True
                        data["received_after"] = _clock(self.clock.read())
                        data["guard_after"], _ = _guard(self.source.guard(frame, "after"), self._identity)
                        data["guard_completed"] = _clock(self.clock.read())
            body = self.journal.finish(data, tick)
            self.stopped = body["derived"]["status"] == "stopped"
            return body
        except BaseException as exc:
            self.stopped = True
            if isinstance(exc, Exception):
                raise ValueError("journal_or_model_failure_details_redacted") from None
            raise

    def decision(self):
        if self.stopped:
            raise ValueError("collector_stopped")
        try:
            body = self.journal.decision(self.session, self.clock.read())
            self.stopped = body["derived"]["status"] == "stopped"
            return body
        except BaseException as exc:
            self.stopped = True
            if isinstance(exc, Exception):
                raise ValueError("journal_or_model_failure_details_redacted") from None
            raise
