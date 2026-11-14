"""Bounded offline quote journal. Invented source only; no broker or order API."""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import sqlite3

SCHEMA = "quote_recorder_102_synthetic_v1"
SOURCE = "invented:quote-recorder-102"
MAX_BYTES = 16 * 1024 * 1024
UTC = timezone.utc
TABLES = {
    "metadata": "CREATE TABLE metadata (value TEXT NOT NULL)",
    "events": "CREATE TABLE events (sequence INTEGER PRIMARY KEY, payload TEXT NOT NULL, sha256 TEXT NOT NULL)",
    "head": "CREATE TABLE head (sequence INTEGER NOT NULL, sha256 TEXT NOT NULL)",
}
INVALID = {"invalid_quote_type", "invalid_quote_identity", "invalid_source_time", "invalid_prices"}


@dataclass(frozen=True)
class Quote:
    quote_id: int
    source_at: datetime
    bid: Decimal
    ask: Decimal


@dataclass(frozen=True)
class Policy:
    max_age_ms: int = 1000
    gap_ms: int = 2000
    max_events: int = 1000

    def __post_init__(self):
        for value, limit in ((self.max_age_ms, 60000), (self.gap_ms, 3600000), (self.max_events, 10000)):
            if type(value) is not int or not 1 <= value <= limit:
                raise ValueError("Invalid bounded recorder policy")


@dataclass(frozen=True)
class Result:
    sequence: int
    status: str
    flags: tuple[str, ...]


def _json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _digest(value):
    return hashlib.sha256(_json(value).encode("utf-8")).hexdigest()


def _time(value):
    if type(value) is not datetime or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("Explicit aware timestamp required")
    return value.astimezone(UTC).isoformat(timespec="microseconds")


def _price(value):
    if type(value) is not Decimal or not value.is_finite() or not 0 < value < Decimal("1000"):
        raise ValueError("Invalid invented EURUSD price")
    # Fixed-point output avoids exponent-dependent identity; bound input complexity.
    if len(value.as_tuple().digits) > 20 or not -12 <= value.as_tuple().exponent <= 12:
        raise ValueError("Invalid invented price precision")
    return format(value, "f").rstrip("0").rstrip(".") if "." in format(value, "f") else format(value, "f")


def _input(quote):
    if quote is None:
        return "missing", None, None
    if type(quote) is not Quote:
        return "invalid", None, "invalid_quote_type"
    if type(quote.quote_id) is not int or not 1 <= quote.quote_id <= 2**63 - 1:
        return "invalid", None, "invalid_quote_identity"
    try:
        source_at = _time(quote.source_at)
    except (ValueError, OverflowError):
        return "invalid", None, "invalid_source_time"
    try:
        bid, ask = _price(quote.bid), _price(quote.ask)
        if quote.ask < quote.bid:
            raise ValueError("Crossed quote")
    except (ValueError, ArithmeticError):
        return "invalid", None, "invalid_prices"
    return "quote", dict(quote_id=quote.quote_id, source_at=source_at, bid=bid, ask=ask), None


def _metadata(policy):
    if type(policy) is not Policy:
        raise ValueError("Invalid recorder policy type")
    Policy.__post_init__(policy)
    return dict(schema=SCHEMA, source=SOURCE, symbol="EURUSD", synthetic=True,
                source_clock="invented_explicit_offsets", receipt_clock="injected_for_offline_tests",
                market_data_qualified=False, orders_available=False,
                policy=dict(max_age_ms=policy.max_age_ms, gap_ms=policy.gap_ms, max_events=policy.max_events))


class _State:
    def __init__(self):
        self.received = None
        self.source = None
        self.seen = {}


def _decision(state, kind, quote, invalid, received, policy):
    flags = []
    now = datetime.fromisoformat(received)
    if state.received is not None and now < state.received:
        status, flags = "rejected", ["receipt_clock_backwards"]
    else:
        if state.received is not None and now - state.received > timedelta(milliseconds=policy.gap_ms):
            flags.append("receipt_gap")
        if kind == "missing":
            status = "missing"
            flags.append("missing_quote")
        elif kind == "invalid":
            status = "invalid"
            flags.append(invalid)
        else:
            source = datetime.fromisoformat(quote["source_at"])
            age = now - source
            if age < timedelta(0):
                flags.append("future_source_time")
            if age > timedelta(milliseconds=policy.max_age_ms):
                flags.append("stale_quote")
            previous = state.seen.get(quote["quote_id"])
            if previous is not None:
                if previous == quote:
                    flags.append("duplicate_quote")
                    status = "duplicate"
                else:
                    flags.append("conflicting_duplicate")
                    status = "rejected"
            else:
                if state.source is not None and source < state.source:
                    flags.append("source_clock_backwards")
                if state.source is not None and source - state.source > timedelta(milliseconds=policy.gap_ms):
                    flags.append("source_gap")
                status = "rejected" if any(f in flags for f in (
                    "future_source_time", "stale_quote", "source_clock_backwards")) else "accepted"
                if status == "accepted":
                    state.seen[quote["quote_id"]] = quote
                    state.source = source
    if state.received is None or now > state.received:
        state.received = now
    return status, flags


class Recorder:
    """Local synthetic journal. Committed events are the only restart state."""

    def __init__(self, connection, path):
        self._db, self.path = connection, Path(path)

    @classmethod
    def create(cls, path, policy=Policy()):
        metadata = _metadata(policy)
        path = Path(path)
        # Never replace an existing journal, even an empty or damaged file.
        with path.open("xb"):
            pass
        recorder = cls._connect(path)
        try:
            recorder._db.execute("BEGIN IMMEDIATE")
            for sql in TABLES.values():
                recorder._db.execute(sql)
            recorder._db.execute("INSERT INTO metadata VALUES (?)", (_json(metadata),))
            recorder._db.execute("INSERT INTO head VALUES (?, ?)", (0, _digest(metadata)))
            recorder._db.execute("COMMIT")
            recorder._history()
            return recorder
        except BaseException:
            recorder.close()
            raise

    @classmethod
    def _connect(cls, path):
        path = Path(path)
        if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_BYTES:
            raise ValueError("Invalid bounded journal file")
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
        recorder = cls._connect(path)
        try:
            recorder._history()
            return recorder
        except BaseException:
            recorder.close()
            raise

    def _history(self):
        if self.path.stat().st_size > MAX_BYTES:
            raise ValueError("Journal file limit exceeded")
        objects = self._db.execute("SELECT type, name, sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%'").fetchall()
        if sorted(objects) != sorted(("table", name, sql) for name, sql in TABLES.items()):
            raise ValueError("Unexpected journal schema")
        if self._db.execute("PRAGMA quick_check").fetchall() != [("ok",)]:
            raise ValueError("Damaged journal")
        if self._db.execute("PRAGMA journal_mode").fetchone() != ("delete",):
            raise ValueError("Unexpected journal mode")
        metadata_rows = self._db.execute("SELECT value FROM metadata").fetchall()
        if len(metadata_rows) != 1:
            raise ValueError("Invalid journal metadata")
        try:
            metadata = json.loads(metadata_rows[0][0])
            policy = Policy(**metadata["policy"])
            if metadata != _metadata(policy) or metadata_rows[0][0] != _json(metadata):
                raise ValueError("Changed source metadata")
        except (ValueError, TypeError, KeyError) as exc:
            raise ValueError("Invalid journal metadata") from exc
        rows = self._db.execute("SELECT sequence, payload, sha256 FROM events ORDER BY sequence LIMIT ?",
                                (policy.max_events + 1,)).fetchall()
        if len(rows) > policy.max_events:
            raise ValueError("Journal event limit exceeded")
        state, chain, events = _State(), _digest(metadata), []
        for index, (sequence, payload, digest) in enumerate(rows, 1):
            try:
                body = json.loads(payload)
                kind, quote, invalid = body["input_kind"], body["quote"], body["invalid_reason"]
                received = _time(datetime.fromisoformat(body["received_at"]))
                if kind == "quote":
                    if set(quote) != {"quote_id", "source_at", "bid", "ask"}:
                        raise ValueError("Invalid quote schema")
                    parsed = Quote(quote["quote_id"], datetime.fromisoformat(quote["source_at"]),
                                   Decimal(quote["bid"]), Decimal(quote["ask"]))
                    if _input(parsed) != (kind, quote, invalid):
                        raise ValueError("Invalid quote encoding")
                elif kind not in ("invalid", "missing") or quote is not None or (
                    invalid not in INVALID if kind == "invalid" else invalid is not None):
                    raise ValueError("Invalid input encoding")
                status, flags = _decision(state, kind, quote, invalid, received, policy)
                expected = dict(sequence=index, input_kind=kind, quote=quote, invalid_reason=invalid,
                                received_at=received, status=status, flags=flags, previous_sha256=chain)
                if sequence != index or body != expected or payload != _json(expected) or digest != _digest(expected):
                    raise ValueError("Journal history mismatch")
            except (ValueError, TypeError, KeyError, ArithmeticError, OverflowError) as exc:
                raise ValueError("Journal history mismatch") from exc
            events.append(body)
            chain = digest
        if self._db.execute("SELECT sequence, sha256 FROM head").fetchall() != [(len(events), chain)]:
            raise ValueError("Journal head mismatch")
        return policy, state, chain, events

    def _insert(self, body):
        self._db.execute("INSERT INTO events VALUES (?, ?, ?)",
                         (body["sequence"], _json(body), _digest(body)))
        self._db.execute("UPDATE head SET sequence=?, sha256=?", (body["sequence"], _digest(body)))

    def record(self, quote, received_at):
        received = _time(received_at)
        kind, canonical, invalid = _input(quote)
        try:
            self._db.execute("BEGIN IMMEDIATE")
            policy, state, chain, events = self._history()
            if len(events) == policy.max_events:
                raise ValueError("Journal event limit reached")
            status, flags = _decision(state, kind, canonical, invalid, received, policy)
            body = dict(sequence=len(events) + 1, input_kind=kind, quote=canonical, invalid_reason=invalid,
                        received_at=received, status=status, flags=flags, previous_sha256=chain)
            self._insert(body)
            self._db.execute("COMMIT")
            return Result(body["sequence"], status, tuple(flags))
        except BaseException:
            if self._db.in_transaction:
                self._db.execute("ROLLBACK")
            raise

    def events(self):
        return tuple(self._history()[3])

    def summary(self):
        policy, state, chain, events = self._history()
        statuses = {name: sum(e["status"] == name for e in events)
                    for name in ("accepted", "duplicate", "missing", "invalid", "rejected")}
        flags = sorted({f for e in events for f in e["flags"]})
        return dict(schema=SCHEMA, source=SOURCE, symbol="EURUSD", synthetic=True, events=len(events),
                    statuses=statuses, flags=flags, chain_sha256=chain,
                    market_data_qualified=False, orders_available=False)

    def close(self):
        self._db.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


def invented_events():
    """Invented2030 quotes; no observed market prices or historical eligibility."""
    start = datetime(2030, 1, 7, tzinfo=UTC)
    def at(ms):
        return start + timedelta(milliseconds=ms)
    def q(identity, ms, bid="1.1000", ask="1.1002"):
        return Quote(identity, at(ms), Decimal(bid), Decimal(ask))
    return [
        (q(1, 0), at(100)),
        (q(1, 0), at(200)),
        (q(1, 0, "1.1001"), at(300)),
        (q(2, 500), at(600)),
        (q(3, 400), at(700)),
        (q(4, 0), at(2000)),
        (None, at(2100)),
        (q(5, 2200), at(2200)),
        (q(6, 5000), at(5100)),
        (q(7, 10000), at(5200)),
        (Quote(8, at(5000).replace(tzinfo=None), Decimal("1.1"), Decimal("1.2")), at(5300)),
        (q(8, 5000, "1.1001"), at(5400)),
        (q(9, 5400), at(5350)),
        (q(9, 5400), at(5600)),
    ]
