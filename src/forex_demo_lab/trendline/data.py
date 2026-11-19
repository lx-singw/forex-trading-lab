"""Phase 2 invented Level B data boundary and calendar-aware bar observations.

Market manifests remain metadata-only. No network, credentials, native accounts
or submission APIs are used. Existing session146 algorithms stay unchanged.
"""
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re
from typing import TYPE_CHECKING

from .. import elliott_sessions_146 as sessions
from ..elliott_full.contracts import Bar

if TYPE_CHECKING:
    from .historical_calendar import Calendar

VERSION = "TRL_DATA_163_V1"
ROOT = Path(__file__).resolve().parents[3]
ROW_LIMIT = 20000
BYTE_LIMIT = 16 * 1024 * 1024
EVIDENCE = ("source_use", "clock_timezone_dst", "session_calendar", "coverage_lineage",
            "price_semantics", "entry_spread", "commission_swap_contract", "prior_exposure")
CANDIDATES = ("TRL_BRK3_E1", "TRL_FXR_M", "TRL_BRK2_E1", "TRL_BNC_E1",
              "TRL_BRK3_E1_D1", "T12_D", "CASH")


def fields(value, expected):
    if type(value) is not dict or set(value) != set(expected):
        raise ValueError("exact declared fields required")


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def sha(value, nullable=False):
    if nullable and value is None:
        return
    if type(value) is not str or not re.fullmatch(r"[0-9a-f]{64}", value):
        raise ValueError("SHA256 declaration required")


def integer(value):
    if type(value) is not int or value < 0:
        raise ValueError("nonnegative integer required")


def number(value):
    if type(value) is not str or not re.fullmatch(r"[0-9]{1,12}(?:\.[0-9]{1,12})?", value):
        raise ValueError("bounded nonnegative decimal string required")
    return Decimal(value)


def no_links(path):
    path = Path(path).absolute()
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError("symlink paths not accepted")
    return path


def read_json(path, limit=BYTE_LIMIT):
    path = no_links(path)
    with path.open("rb") as handle:
        raw = handle.read(limit + 1)
    if len(raw) > limit:
        raise ValueError("input byte limit")

    def unique(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("duplicate JSON key")
            result[key] = value
        return result

    def nonfinite(_):
        raise ValueError("nonfinite JSON")

    return json.loads(raw, object_pairs_hook=unique, parse_constant=nonfinite), hashlib.sha256(raw).hexdigest()


def write_new(path, value):
    path = no_links(path)
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(value, indent=2, allow_nan=False) + "\n")


def source_bindings():
    paths = [Path(__file__), Path(__file__).with_name("__main__.py"),
             ROOT / "docs/trendline/PROTOCOL.md",
             ROOT / "src/forex_demo_lab/elliott_sessions_146.py",
             ROOT / "src/forex_demo_lab/elliott_full/contracts.py"]
    return {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}


@dataclass(frozen=True)
class Declaration:
    """Immutable, labelled invented input descriptor, not market admission."""
    _json: str

    @classmethod
    def from_record(cls, value):
        fields(value, ("schema", "kind", "symbol", "data_level", "geometry_basis",
                       "spread_semantics", "partition", "input_sha256", "calendar"))
        if (value["schema"] != VERSION or value["kind"] != "invented_trendline_source"
                or value["symbol"] != "EURUSD" or value["data_level"] != "B"):
            raise ValueError("invented EURUSD Level B declaration required; market entry closed")
        combinations = {"bid_only": "constant_per_h1_assumption", "mid_candles_source": "not_available"}
        if (value["geometry_basis"] not in combinations
                or value["spread_semantics"] != combinations[value["geometry_basis"]]):
            raise ValueError("explicit geometry/spread semantics required; no blended midpoint")
        if value["partition"] not in ("development", "validation"):
            raise ValueError("partition declaration")
        sha(value["input_sha256"])
        sessions.Calendar.from_record(value["calendar"])
        return cls(canonical(value).decode())

    def record(self):
        return json.loads(self._json)

    @property
    def sha256(self):
        return digest(self.record())

    @property
    def calendar(self):
        return sessions.Calendar.from_record(self.record()["calendar"])


@dataclass(frozen=True)
class HistoricalDeclaration:
    """Internal descriptor for the reviewed historical count path."""

    _json: str
    calendar: "Calendar"

    def record(self):
        return json.loads(self._json)

    @property
    def sha256(self):
        return hashlib.sha256(self._json.encode()).hexdigest()


def research_declaration(source):
    """Share the typed historical descriptor inside the calculation kernels."""
    if type(source) is HistoricalDeclaration:
        return source
    return Declaration.from_record(source.record())


def unlock_record(declaration):
    """Explicit logged access to an invented validation fixture only.

    A self-authored receipt is not authentication, source qualification or a grant
    to access any protected market data. No real-market loader exists here.
    """
    declaration = Declaration.from_record(declaration.record())
    if declaration.record()["partition"] != "validation":
        raise ValueError("validation declaration required")
    return {"kind": "explicit_invented_validation_unlock", "schema": VERSION,
            "declaration_sha256": declaration.sha256,
            "input_sha256": declaration.record()["input_sha256"],
            "scope": declaration.calendar.record()["scope"],
            "purpose": "invented_software_verification_only",
            "market_data_authorized": False}


@dataclass(frozen=True)
class Hour:
    start: int
    end: int
    available_at: int
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    spread_pips: Decimal | None

    @classmethod
    def from_record(cls, value, basis):
        fields(value, ("start", "end", "available_at", "open", "high", "low", "close", "spread_pips"))
        for key in ("start", "end", "available_at"):
            integer(value[key])
        prices = {key: number(value[key]) for key in ("open", "high", "low", "close")}
        if not 0 < prices["low"] <= min(prices["open"], prices["close"]) <= max(prices["open"], prices["close"]) <= prices["high"]:
            raise ValueError("positive OHLC geometry required")
        if not value["start"] < value["end"] <= value["available_at"]:
            raise ValueError("completed observation chronology required")
        if basis == "bid_only":
            spread = number(value["spread_pips"])
        elif basis == "mid_candles_source" and value["spread_pips"] is None:
            spread = None
        else:
            raise ValueError("basis/spread mismatch")
        return cls(**{key:value[key] for key in ("start", "end", "available_at")},
                   **prices, spread_pips=spread)

    def record(self):
        return {key: str(value) if isinstance(value, Decimal) else value
                for key, value in self.__dict__.items()}


def load_dataset(descriptor_path, hours_path, unlock_path=None):
    """Inspect declaration/unlock before even opening the named hourly file."""
    value, _ = read_json(descriptor_path, 1024 * 1024)
    source = Declaration.from_record(value)
    if value["partition"] == "validation":
        if unlock_path is None:
            raise ValueError("explicit logged invented validation unlock required before price read")
        record, _ = read_json(unlock_path, 4096)
        if canonical(record) != canonical(unlock_record(source)):
            raise ValueError("unlock does not match invented declaration/input/scope")
    elif unlock_path is not None:
        raise ValueError("unexpected validation unlock on development input")
    rows, raw_sha = read_json(hours_path)
    if raw_sha != value["input_sha256"]:
        raise ValueError("hourly file bytes do not match declared SHA256")
    if type(rows) is not list or not 1 <= len(rows) <= ROW_LIMIT:
        raise ValueError("bounded nonempty hourly observations required")
    hours = tuple(Hour.from_record(row, value["geometry_basis"]) for row in rows)
    # Check the complete supplied prefix before returning anything usable.
    check = BarStream(source)
    for hour in hours:
        check.observe(hour)
    return source, hours


class BarStream:
    """Level B wrapper over unchanged146 calendar/aggregation interfaces."""
    def __init__(self, declaration):
        self.source = Declaration.from_record(declaration.record())
        self._observer = sessions.Observations(self.source.calendar)
        self._bindings = source_bindings()
        source = self.source.record()
        self._basis = source["geometry_basis"]
        # Whole-file SHA binds the report, not causal identities: appending a valid
        # future suffix must not rename earlier bar/pivot inputs.
        self._geometry_identity = digest({key:value for key,value in source.items()
                                          if key != "input_sha256"})
        self._declaration_sha = self.source.sha256
        self._rows = []

    @property
    def clock(self):
        return self._observer.clock

    def observe(self, hour):
        if not isinstance(hour, Hour):
            raise ValueError("typed hourly observation required")
        if len(self._rows) >= ROW_LIMIT:
            raise ValueError("hourly observation bound")
        hour = Hour.from_record(hour.record(), self._basis)
        lineage = digest({"geometry_declaration": self._geometry_identity, "hour": hour.record()})
        bar = Bar("H1", hour.start, hour.end, hour.available_at,
                  hour.open, hour.high, hour.low, hour.close, lineage)
        self._observer.observe(bar)
        self._rows.append(hour)

    def advance(self, now):
        self._observer.advance(now)

    def bars(self):
        return self._observer.bars()

    def report(self):
        if self._bindings != source_bindings() or self.source.sha256 != self._declaration_sha:
            raise ValueError("implementation/protocol bindings changed during replay")
        source = self.source.record()
        bars = []
        for bar in self.bars():
            row = bar.record()
            row["available_at"] = row.pop("available")
            bars.append(row)
        return {"schema": VERSION, "kind": "invented_trendline_bar_report",
                "data_level": "B", "geometry_basis": source["geometry_basis"],
                "spread_semantics": source["spread_semantics"], "partition": source["partition"],
                "declaration_sha256": self.source.sha256, "input_sha256": source["input_sha256"],
                "source_bindings": dict(self._bindings), "as_of": self.clock, "bars": bars,
                "coverage": {frame:self._observer.status(frame) for frame in sessions.FRAMES},
                "observed_hours": len(self._rows),
                "execution_side_data": ("invented_bid_and_constant_spread" if source["geometry_basis"] == "bid_only"
                                        else "unavailable_mid_only"),
                "qualified_market_source": False, "market_cells_run": 0,
                "broker_performance_available": False, "demo_eligible": False,
                "orders_available": False, "returns_computed": False,
                "limitations": ["invented OHLC, not qualified market data",
                                "explicit calendar edges do not authenticate provider DST/sessions",
                                "Level B cannot establish quote age or intrabar order",
                                "no strategy, execution ledger or native integration"]}


def draft_plan():
    return {"schema": VERSION, "kind": "trendline_market_source_plan", "symbol": "EURUSD",
            "data_level": "B", "source_alias": "unassigned", "geometry_basis": None,
            "input_sha256": None, "calendar_sha256": None, "spread_semantics": None,
            "scope": {key:None for key in ("warmup", "development", "validation")},
            "evidence_sha256": {key:None for key in EVIDENCE}}


def assess_plan(value):
    """Validate metadata only; even complete self-claims cannot admit prices."""
    fields(value, draft_plan().keys())
    if (value["schema"] != VERSION or value["kind"] != "trendline_market_source_plan"
            or value["symbol"] != "EURUSD" or value["data_level"] not in ("B", "Q")):
        raise ValueError("market metadata declaration required")
    if value["source_alias"] not in ("unassigned", "twelve_data", "oanda_export", "local_export"):
        raise ValueError("anonymous source category required")
    basis = value["geometry_basis"]
    if basis not in (None, "bid_only", "mid_candles_source", "mid_sync"):
        raise ValueError("geometry declaration")
    if ((value["data_level"] == "B" and basis == "mid_sync")
            or (value["data_level"] == "Q" and basis not in (None, "mid_sync"))):
        raise ValueError("data level/geometry mismatch")
    if value["spread_semantics"] not in (None, "constant_per_h1_assumption", "recorded_bid_ask", "not_available"):
        raise ValueError("spread declaration")
    expected_spread = {"bid_only":"constant_per_h1_assumption",
                       "mid_candles_source":"not_available", "mid_sync":"recorded_bid_ask"}
    if basis is not None and value["spread_semantics"] not in (None, expected_spread[basis]):
        raise ValueError("geometry/spread declaration mismatch")
    for key in ("input_sha256", "calendar_sha256"):
        sha(value[key], nullable=True)
    fields(value["evidence_sha256"], EVIDENCE)
    for evidence in value["evidence_sha256"].values():
        sha(evidence, nullable=True)
    fields(value["scope"], ("warmup", "development", "validation"))
    intervals = {}
    reasons = ["independent_source_calendar_cost_exposure_review_required",
               "qualified_market_reader_not_implemented"]
    if value["source_alias"] == "unassigned":
        reasons.append("source_unassigned")
    for key, interval in value["scope"].items():
        if interval is None:
            reasons.append(key + "_unassigned")
            continue
        fields(interval, ("start", "end"))
        dates = []
        for text in (interval["start"], interval["end"]):
            if type(text) is not str or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):
                raise ValueError("ISO date required")
            day = date.fromisoformat(text)
            if not 1900 <= day.year <= 2100:
                raise ValueError("bounded metadata date required")
            dates.append(day)
        a, b = dates
        if not a < b:
            raise ValueError("half-open source interval required")
        intervals[key] = (a, b)
        for name, left, right in (("consumed", "2025-01-01", "2026-01-01"),
                                  ("quarantined", "2026-10-01", "2026-11-01"),
                                  ("reserved", "2026-11-01", "2027-01-01")):
            if a < date.fromisoformat(right) and date.fromisoformat(left) < b:
                reasons.append(key + "_overlaps_" + name)
        if key == "validation" and a < date(2025,1,1) and date(2024,1,1) < b:
            reasons.append("validation_overlaps_seen_2024")
    dev, validation, warmup = (intervals.get(key) for key in ("development", "validation", "warmup"))
    if dev and validation and dev[1] > validation[0]:
        reasons.append("development_validation_not_chronological")
    if warmup and dev and warmup[1] > dev[0]:
        reasons.append("warmup_overlaps_development")
    for key in ("geometry_basis", "spread_semantics", "input_sha256", "calendar_sha256"):
        if value[key] is None:
            reasons.append(key + "_unassigned")
    reasons.extend(key + "_evidence_missing" for key in EVIDENCE if value["evidence_sha256"][key] is None)
    return {"schema": VERSION, "kind": "metadata_assessment_not_admission", "status": "UNAVAILABLE",
            "data_level": value["data_level"], "geometry_basis": basis, "reasons": reasons,
            "cells": [{"candidate":candidate, "profile":cost, "partition":partition,
                       "status":"UNAVAILABLE", "returns":None}
                      for candidate in CANDIDATES for cost in ("base", "adverse")
                      for partition in ("development", "validation")],
            "orders_available": False, "demo_eligible": False,
            "limitations": ["metadata lint only; hashes are unverified declarations",
                            "minimum warmup, sample lengths, costs and prior trials still require study preflight",
                            "no price file opened or market-data admission implemented"]}
