"""Pure fixed daily features on invented sessions; no market or execution API."""
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
from statistics import fmean, pstdev

ROOT = Path(__file__).resolve().parents[2]
DAY = 86_400_000
MIN_TIME, MAX_TIME = 946_684_800_000, 1_072_915_200_000  # Invented 2000..2003 only.
MAX_SESSIONS, MAX_BYTES = 800, 8 * 1024 * 1024
VERSION = "FXDL_DAILY118_V1"
CANDIDATES = ("T12_D", "MR20_D", "MIX50_D", "CASH")
DECLARATION_SHA256 = "fc9629f0922700e9ea8118cbf23460f550870a5ecf17ff14e6246833766faf6f"
DEPENDENCIES = (
    "src/forex_demo_lab/daily_features_118.py",
    "src/forex_demo_lab/daily_fixture_118.py",
    "scripts/daily-features-118.py", "tests/test_daily_features_118.py",
    "config/research-candidates-117.json", "docs/DAILY-STRATEGY-118-PROTOCOL.md",
    "docs/DAILY-STRATEGY-118-PLAN.md",
)
FIXTURE_FIELDS = {"format", "kind", "clock", "symbol", "case", "calendar",
                  "bars", "target_session_id", "decision_msc"}
CALENDAR_FIELDS = {"kind", "calendar_id", "available_msc", "sessions"}
SESSION_FIELDS = {"session_id", "start_msc", "end_msc", "status"}
BAR_FIELDS = {"session_id", "start_msc", "end_msc", "observation_msc", "available_msc",
              "open", "high", "low", "close", "lineage_sha256"}


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def _digest(value):
    return hashlib.sha256(_canonical(value)).hexdigest()


def _pairs(items):
    result = {}
    for key, value in items:
        if key in result:
            raise ValueError("duplicate_json_field")
        result[key] = value
    return result


def _json(raw):
    def nonfinite(_):
        raise ValueError("nonfinite_json")
    try:
        return json.loads(raw, object_pairs_hook=_pairs, parse_constant=nonfinite)
    except (UnicodeError, json.JSONDecodeError, RecursionError) as exc:
        raise ValueError("invalid_json") from exc


def _fields(value, fields, reason):
    if type(value) is not dict or set(value) != fields:
        raise ValueError(reason)


def _integer(value, low, high, reason):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(reason)
    return value


def _number(value, reason, positive=False):
    if type(value) not in (int, float):
        raise ValueError(reason)
    try:
        number = float(value)
    except OverflowError as exc:
        raise ValueError(reason) from exc
    if not math.isfinite(number) or (positive and number <= 0):
        raise ValueError(reason)
    return number


def _name(value, reason):
    if type(value) is not str or not re.fullmatch(r"[a-z][a-z0-9_]{0,63}", value):
        raise ValueError(reason)


def rule_definitions():
    return {"candidates": list(CANDIDATES), "warmup_sessions": 253,
            "trend_lookback_sessions": 252, "reentry_window": 20,
            "reentry_deviation": "population", "reentry_threshold": 2,
            "mix_weights": [0.5, 0.5], "atr_sessions": 14, "stop_atr": 2,
            "cash_interest": 0, "abstention_risk": 0,
            "declaration_sha256": DECLARATION_SHA256,
            "implementation_scope": "features_only_invented_no_sizing_or_fills"}


def schema_definitions():
    return {"version": VERSION, "fixture_fields": sorted(FIXTURE_FIELDS),
            "calendar_fields": sorted(CALENDAR_FIELDS), "session_fields": sorted(SESSION_FIELDS),
            "bar_fields": sorted(BAR_FIELDS), "clock": "invented_utc_milliseconds",
            "calendar_kind": "invented_calendar", "day_milliseconds": DAY,
            "max_sessions": MAX_SESSIONS, "min_time": MIN_TIME, "max_time": MAX_TIME,
            "market_admission": False}


def bar_lineage(case, calendar_id, session, bar):
    """Content consistency only; no origin authentication or market qualification."""
    return _digest({"format": VERSION, "kind": "invented_daily_fixture",
                    "clock": "invented_utc_milliseconds", "symbol": "EURUSD",
                    "case": case, "calendar_id": calendar_id, "session": session,
                    "bar": {k: v for k, v in bar.items() if k != "lineage_sha256"}})


@dataclass(frozen=True)
class Session:
    session_id: int
    start_msc: int
    end_msc: int
    status: str

    def __post_init__(self):
        _integer(self.session_id, 0, MAX_SESSIONS - 1, "session_id")
        _integer(self.start_msc, MIN_TIME, MAX_TIME - DAY, "session_time")
        _integer(self.end_msc, MIN_TIME + DAY, MAX_TIME, "session_time")
        if self.start_msc % DAY or self.end_msc - self.start_msc != DAY:
            raise ValueError("invented_day_boundary")
        if type(self.status) is not str or self.status not in ("trading", "closure"):
            raise ValueError("session_status")


@dataclass(frozen=True)
class DailyBar:
    session_id: int
    start_msc: int
    end_msc: int
    observation_msc: int
    available_msc: int
    open: float
    high: float
    low: float
    close: float
    lineage_sha256: str

    def __post_init__(self):
        Session(self.session_id, self.start_msc, self.end_msc, "trading")
        _integer(self.observation_msc, self.start_msc, self.end_msc - 1, "observation_time")
        _integer(self.available_msc, self.end_msc, MAX_TIME, "bar_not_completed")
        for field in ("open", "high", "low", "close"):
            _number(getattr(self, field), "bar_price", positive=True)
        if not self.low <= min(self.open, self.close) <= max(self.open, self.close) <= self.high:
            raise ValueError("bar_ohlc")
        if type(self.lineage_sha256) is not str or not re.fullmatch(r"[0-9a-f]{64}", self.lineage_sha256):
            raise ValueError("bar_lineage")


@dataclass(frozen=True)
class Snapshot:
    case: str
    target_session_id: int
    decision_msc: int
    available_msc: int
    history: tuple[DailyBar, ...]
    calendar_prefix_sha256: str


@dataclass(frozen=True)
class DailyDecision:
    candidate: str
    side: int
    score: float
    stop_distance: float
    risk_multiplier: float
    reason: str
    component_sides: tuple[tuple[str, int], ...]
    trend_return: float | None
    previous_z: float | None
    current_z: float | None
    reentry_reason: str
    decision_msc: int
    available_msc: int
    target_session_id: int
    used_bar_hashes: tuple[str, ...]
    calendar_prefix_sha256: str
    rules_sha256: str


def snapshot(value):
    """Validate a full invented bundle; select only observations available at target."""
    _fields(value, FIXTURE_FIELDS, "fixture_fields")
    if (value["format"] != VERSION or value["kind"] != "invented_daily_fixture"
            or value["clock"] != "invented_utc_milliseconds" or value["symbol"] != "EURUSD"):
        raise ValueError("invented_fixture_required")
    _name(value["case"], "fixture_case")
    cal = value["calendar"]
    _fields(cal, CALENDAR_FIELDS, "calendar_fields")
    if cal["kind"] != "invented_calendar":
        raise ValueError("invented_calendar_required")
    _name(cal["calendar_id"], "calendar_id")
    _integer(cal["available_msc"], MIN_TIME, MAX_TIME, "calendar_availability")
    rows = cal["sessions"]
    if type(rows) is not list or not 1 <= len(rows) <= MAX_SESSIONS:
        raise ValueError("calendar_count")
    sessions = []
    for i, row in enumerate(rows):
        _fields(row, SESSION_FIELDS, "session_fields")
        session = Session(**row)
        if session.session_id != i or (sessions and session.start_msc != sessions[-1].end_msc):
            raise ValueError("calendar_sequence")
        sessions.append(session)
    if cal["available_msc"] > sessions[0].start_msc:
        raise ValueError("calendar_not_predeclared")
    target = _integer(value["target_session_id"], 0, len(sessions) - 1, "target_session_id")
    asof = _integer(value["decision_msc"], MIN_TIME, MAX_TIME, "decision_time")
    if sessions[target].status != "trading":
        raise ValueError("target_is_closure")
    rows = value["bars"]
    if type(rows) is not list or not 1 <= len(rows) <= MAX_SESSIONS:
        raise ValueError("bar_count")
    bars = {}
    last_id = -1
    for row in rows:
        _fields(row, BAR_FIELDS, "bar_fields")
        bar = DailyBar(**row)
        if bar.session_id <= last_id:
            raise ValueError("bar_sequence")
        if bar.session_id >= len(sessions):
            raise ValueError("bar_session_unknown")
        session = sessions[bar.session_id]
        if session.status != "trading":
            raise ValueError("bar_on_closure")
        if (bar.start_msc, bar.end_msc) != (session.start_msc, session.end_msc):
            raise ValueError("bar_session_mismatch")
        if bar.lineage_sha256 != bar_lineage(value["case"], cal["calendar_id"], asdict(session), row):
            raise ValueError("bar_lineage_mismatch")
        bars[bar.session_id], last_id = bar, bar.session_id
    history = []
    for session in sessions[:target + 1]:
        if session.status == "closure":
            continue
        if session.session_id not in bars:
            raise ValueError("missing_required_session")
        bar = bars[session.session_id]
        if bar.available_msc > asof:
            raise ValueError("session_unavailable")
        history.append(bar)
    prefix = {"kind": cal["kind"], "calendar_id": cal["calendar_id"],
              "available_msc": cal["available_msc"], "sessions": [asdict(s) for s in sessions[:target + 1]]}
    return Snapshot(value["case"], target, asof, max(b.available_msc for b in history),
                    tuple(history[-253:]), _digest(prefix))


def reentry_side(previous_z, current_z):
    previous_z = _number(previous_z, "feature_arithmetic")
    current_z = _number(current_z, "feature_arithmetic")
    return 1 if previous_z < -2 <= current_z else -1 if previous_z > 2 >= current_z else 0


def mix_sides(trend, reentry):
    for side in (trend, reentry):
        if type(side) is not int or side not in (-1, 0, 1):
            raise ValueError("component_side")
    score = 0.5 * trend + 0.5 * reentry
    return (1 if score > 0 else -1 if score < 0 else 0), score, abs(score)


def decisions(value):
    observed = snapshot(value)
    history = observed.history
    trend, reentry, distance = 0, 0, 0.0
    momentum = old_z = new_z = None
    reentry_reason = "warmup"
    if len(history) == 253:
        try:
            closes = [float(b.close) for b in history]
            momentum = _number(closes[-1] / closes[0] - 1, "feature_arithmetic")
            trend = 1 if momentum > 0 else -1 if momentum < 0 else 0
            previous, current = closes[-21:-1], closes[-20:]
            old_sd, new_sd = pstdev(previous), pstdev(current)
            reentry_reason = "zero_price_deviation"
            if old_sd and new_sd:
                old_z = _number((previous[-1] - fmean(previous)) / old_sd, "feature_arithmetic")
                new_z = _number((current[-1] - fmean(current)) / new_sd, "feature_arithmetic")
                reentry = reentry_side(old_z, new_z)
                reentry_reason = "price_reentry" if reentry else "no_reentry"
            ranges = [max(float(history[i].high) - float(history[i].low),
                          abs(float(history[i].high) - closes[i - 1]),
                          abs(float(history[i].low) - closes[i - 1])) for i in range(239, 253)]
            distance = _number(fmean(ranges) * 2, "feature_arithmetic")
        except (OverflowError, ZeroDivisionError) as exc:
            raise ValueError("feature_arithmetic") from exc
    mix_side, score, multiplier = mix_sides(trend, reentry)
    sides = {"T12_D": (trend, float(trend), float(abs(trend))),
             "MR20_D": (reentry, float(reentry), float(abs(reentry))),
             "MIX50_D": (mix_side, score, multiplier), "CASH": (0, 0.0, 0.0)}
    result = {}
    for candidate, (side, score, multiplier) in sides.items():
        reason = "active_signal" if side else "no_signal"
        if candidate == "CASH":
            reason, stop = "cash", 0.0
        elif len(history) < 253:
            reason, stop = "warmup", 0.0
        elif distance == 0:
            side, multiplier, reason, stop = 0, 0.0, "zero_true_range", 0.0
        else:
            stop = distance
            if candidate == "MR20_D" and not side:
                reason = reentry_reason
            if candidate == "MIX50_D" and trend and reentry and not side:
                reason = "opposing_components"
        result[candidate] = DailyDecision(
            candidate, side, score, stop, multiplier, reason,
            (("T12_D", trend), ("MR20_D", reentry)), momentum, old_z, new_z,
            reentry_reason, observed.decision_msc, observed.available_msc,
            observed.target_session_id, tuple(b.lineage_sha256 for b in history),
            observed.calendar_prefix_sha256, _digest(rule_definitions()))
    return result


def _read(path):
    path = Path(path)
    if path.is_symlink() or not path.is_file():
        raise ValueError("invalid_input_file")
    with path.open("rb") as handle:
        raw = handle.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError("input_size")
    return raw


def write_new(path, value):
    data = json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n"
    with Path(path).open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(data)


def source_bindings():
    return {n: hashlib.sha256(_read(ROOT / n)).hexdigest() for n in DEPENDENCIES}


def freeze_fixture(path, manifest_path):
    raw = _read(path)
    value = _json(raw)
    observed = snapshot(value)  # Validate structure/timing, not calculate features.
    sources = source_bindings()
    if sources["config/research-candidates-117.json"] != DECLARATION_SHA256:
        raise ValueError("fixed_declaration_changed")
    manifest = {"format": "FXDL_DAILY118_FREEZE_V1", "kind": "invented_feature_freeze",
                "frozen_at_utc": datetime.now(timezone.utc).isoformat(),
                "fixture_sha256": hashlib.sha256(raw).hexdigest(), "case": observed.case,
                "target_session_id": observed.target_session_id, "decision_msc": observed.decision_msc,
                "rules": rule_definitions(), "rules_sha256": _digest(rule_definitions()),
                "schema": schema_definitions(), "schema_sha256": _digest(schema_definitions()),
                "sources": sources, "market_admission": False, "returns_computed": False}
    write_new(manifest_path, manifest)
    return manifest


def evaluate_fixture(path, manifest_path, output_path):
    raw, manifest = _read(path), _json(_read(manifest_path))
    fields = {"format", "kind", "frozen_at_utc", "fixture_sha256", "case", "target_session_id",
              "decision_msc", "rules", "rules_sha256", "schema", "schema_sha256", "sources",
              "market_admission", "returns_computed"}
    _fields(manifest, fields, "manifest_fields")
    _integer(manifest["target_session_id"], 0, MAX_SESSIONS - 1, "manifest_target")
    _integer(manifest["decision_msc"], MIN_TIME, MAX_TIME, "manifest_target")
    try:
        if type(manifest["frozen_at_utc"]) is not str:
            raise ValueError("manifest_freeze_time")
        frozen = datetime.fromisoformat(manifest["frozen_at_utc"])
        if frozen.utcoffset() is None or frozen.utcoffset().total_seconds() != 0:
            raise ValueError("manifest_freeze_time")
    except (TypeError, ValueError) as exc:
        raise ValueError("manifest_freeze_time") from exc
    sources = source_bindings()
    if sources["config/research-candidates-117.json"] != DECLARATION_SHA256:
        raise ValueError("fixed_declaration_changed")
    if (manifest["format"] != "FXDL_DAILY118_FREEZE_V1" or manifest["kind"] != "invented_feature_freeze"
            or manifest["fixture_sha256"] != hashlib.sha256(raw).hexdigest()
            or manifest["sources"] != sources
            or _canonical(manifest["rules"]) != _canonical(rule_definitions())
            or _canonical(manifest["schema"]) != _canonical(schema_definitions())
            or manifest["rules_sha256"] != _digest(rule_definitions())
            or manifest["schema_sha256"] != _digest(schema_definitions())
            or manifest["market_admission"] is not False or manifest["returns_computed"] is not False):
        raise ValueError("freeze_binding_mismatch")
    value = _json(raw)
    _fields(value, FIXTURE_FIELDS, "fixture_fields")
    if ((manifest["case"], manifest["target_session_id"], manifest["decision_msc"])
            != (value["case"], value["target_session_id"], value["decision_msc"])):
        raise ValueError("freeze_target_mismatch")
    evaluated = decisions(value)
    report = {"format": "FXDL_DAILY118_REPORT_V1", "kind": "invented_feature_decisions",
              "case": value["case"], "fixture_sha256": hashlib.sha256(raw).hexdigest(),
              "manifest_sha256": hashlib.sha256(_read(manifest_path)).hexdigest(),
              "rules_sha256": _digest(rule_definitions()), "schema_sha256": _digest(schema_definitions()),
              "decisions": {k: asdict(v) for k, v in evaluated.items()},
              "returns": None, "positions": None, "fills": None,
              "market_data_qualified": False, "paper_evaluation_available": False,
              "strategy_selected": False, "orders_available": False, "real_money_execution_available": False}
    write_new(output_path, report)
    return report
