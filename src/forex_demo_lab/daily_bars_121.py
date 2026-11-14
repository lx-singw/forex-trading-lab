"""Invented causal midpoint bars and offline daily accounting integration only."""
from copy import deepcopy
from dataclasses import asdict
from datetime import datetime, timezone
from decimal import Decimal, localcontext
import hashlib
import json
from pathlib import Path

from . import daily_features_118 as daily
from . import daily_fills_120 as fills

VERSION = "FXDL_DAILYBARS121_V1"
MAX_MESSAGES = 5000
DEPENDENCIES = tuple(dict.fromkeys(daily.DEPENDENCIES + fills.DEPENDENCIES + (
    "src/forex_demo_lab/daily_bars_121.py", "src/forex_demo_lab/daily_bars_fixture_121.py",
    "scripts/daily-bars-121.py", "tests/test_daily_bars_121.py",
    "docs/DAILY-BARS-121-PROTOCOL.md", "docs/DAILY-BARS-121-PLAN.md",
)))


def rules():
    return {"schema": VERSION, "max_messages": MAX_MESSAGES, "quote_age_max_msc": 2000,
            "completion_grace_msc": 2000, "first_last_edge_max_msc": 60000,
            "successive_gap_max_msc": daily.DAY // 2, "minimum_distinct_quotes": 4,
            "session_interval": "half_open", "midpoint_precision": 50, "bar_numbers": "118_float_fields",
            "availability": "observed_finalizer_receipt", "no_interpolation": True,
            "coverage_certifies_market_feed": False, "orders_available": False}


def _calendar(value):
    daily._fields(value, daily.CALENDAR_FIELDS, "calendar_fields")
    if value["kind"] != "invented_calendar":
        raise ValueError("invented_calendar_required")
    daily._name(value["calendar_id"], "calendar_id")
    daily._integer(value["available_msc"], daily.MIN_TIME, daily.MAX_TIME, "calendar_availability")
    rows = value["sessions"]
    if type(rows) is not list or not 1 <= len(rows) <= daily.MAX_SESSIONS:
        raise ValueError("calendar_count")
    previous = None
    for i, row in enumerate(rows):
        daily._fields(row, daily.SESSION_FIELDS, "session_fields")
        session = daily.Session(**row)
        if session.session_id != i or previous and session.start_msc != previous.end_msc:
            raise ValueError("calendar_sequence")
        previous = session
    if value["available_msc"] > rows[0]["start_msc"]:
        raise ValueError("calendar_not_predeclared")


def _message(value):
    if type(value) is not dict or type(value.get("kind")) is not str or value["kind"] not in ("quote", "advance"):
        raise ValueError("message_kind")
    fields = {"sequence", "kind", "receipt_msc"}
    if value["kind"] == "quote":
        fields |= {"source_msc", "bid", "ask"}
    daily._fields(value, fields, "message_fields")
    daily._integer(value["sequence"], 0, MAX_MESSAGES - 1, "message_sequence")
    daily._integer(value["receipt_msc"], daily.MIN_TIME, daily.MAX_TIME, "message_time")
    if value["kind"] == "quote":
        daily._integer(value["source_msc"], daily.MIN_TIME, daily.MAX_TIME, "message_time")
        if value["receipt_msc"] < value["source_msc"]:
            raise ValueError("quote_clock")
        bid = daily._number(value["bid"], "quote_price", positive=True)
        ask = daily._number(value["ask"], "quote_price", positive=True)
        if bid > ask or ask > 1e6:
            raise ValueError("quote_price")


def validate_fixture(value):
    daily._fields(value, {"format", "kind", "clock", "symbol", "case", "calendar", "initial_account",
                          "execution_start_msc", "messages"}, "bars_fixture_fields")
    if (value["format"] != VERSION or value["kind"] != "invented_quote_bar_pipeline"
            or value["clock"] != "invented_utc_milliseconds" or value["symbol"] != "EURUSD"):
        raise ValueError("invented_quote_pipeline_required")
    daily._name(value["case"], "bars_fixture_case")
    _calendar(value["calendar"])
    calendar = value["calendar"]["sessions"]
    start, end = calendar[0]["start_msc"], calendar[-1]["end_msc"]
    partition = value["execution_start_msc"]
    if partition is not None:
        daily._integer(partition, start, end - 1, "execution_start")
    account = value["initial_account"]
    daily._fields(account, {"kind", "trade_mode", "currency", "available_msc", "balance_usd"}, "fill_account_fields")
    if account["kind"] != "invented_flat_cash" or account["currency"] != "USD":
        raise ValueError("invented_flat_USD_cash_required")
    if type(account["trade_mode"]) is not int or account["trade_mode"] != 0:
        raise ValueError("synthetic_demo_account_required")
    daily._integer(account["available_msc"], daily.MIN_TIME, daily.MAX_TIME, "account_time")
    if fills.risk._money(account["balance_usd"]) <= 0:
        raise ValueError("initial_balance")
    if partition is not None and account["available_msc"] > partition:
        raise ValueError("account_unavailable")
    messages = value["messages"]
    if type(messages) is not list or not 1 <= len(messages) <= MAX_MESSAGES:
        raise ValueError("message_count")
    previous_quote = None
    for i, message in enumerate(messages):
        _message(message)
        if message["sequence"] != i:
            raise ValueError("message_sequence")
        if i and message["receipt_msc"] < messages[i - 1]["receipt_msc"]:
            raise ValueError("receipt_order")
        if not start <= message["receipt_msc"] < end:
            raise ValueError("message_outside_calendar")
        if message["kind"] == "quote":
            if not start <= message["source_msc"] < end:
                raise ValueError("message_outside_calendar")
            if previous_quote:
                if message["source_msc"] < previous_quote["source_msc"]:
                    raise ValueError("source_order")
                if message["source_msc"] == previous_quote["source_msc"] and any(
                        message[k] != previous_quote[k] for k in ("bid", "ask")):
                    raise ValueError("source_price_conflict")
            previous_quote = message
    return value


def source_bindings():
    return {n: hashlib.sha256(daily._read(daily.ROOT / n)).hexdigest() for n in DEPENDENCIES}


def freeze_fixture(path, output):
    raw = daily._read(path)
    value = validate_fixture(daily._json(raw))
    sources = source_bindings()
    if sources["config/research-candidates-117.json"] != daily.DECLARATION_SHA256:
        raise ValueError("fixed_declaration_changed")
    manifest = {"format": "FXDL_DAILYBARS121_FREEZE_V1", "kind": "invented_pipeline_freeze",
                "frozen_at_utc": datetime.now(timezone.utc).isoformat(), "fixture_sha256": hashlib.sha256(raw).hexdigest(),
                "case": value["case"], "sources": sources, "aggregation_rules": rules(),
                "feature_rules": daily.rule_definitions(), "fill_rules": fills.rules(), "profiles": fills.risk.profiles(),
                "orders_available": False, "market_data_qualified": False}
    daily.write_new(output, manifest)
    return manifest


def _coverage(observations, session):
    times = [r["source_msc"] for r in observations]
    first = times[0] - session["start_msc"] if times else None
    last = session["end_msc"] - times[-1] if times else None
    gap = max((b - a for a, b in zip(times, times[1:])), default=0)
    return {"count": len(times), "first_edge_msc": first, "last_edge_msc": last, "max_gap_msc": gap,
            "complete": len(times) >= 4 and first <= 60000 and last <= 60000 and gap <= daily.DAY // 2}


class Replay:
    """Bound observed quote/clock prefix; publishes no future or incomplete bars."""
    def __init__(self, path, manifest_path):
        raw, mraw = daily._read(path), daily._read(manifest_path)
        manifest = daily._json(mraw)
        daily._fields(manifest, {"format", "kind", "frozen_at_utc", "fixture_sha256", "case", "sources",
                                "aggregation_rules", "feature_rules", "fill_rules", "profiles",
                                "orders_available", "market_data_qualified"}, "bars_manifest_fields")
        if (manifest["format"] != "FXDL_DAILYBARS121_FREEZE_V1" or manifest["kind"] != "invented_pipeline_freeze"
                or manifest["fixture_sha256"] != hashlib.sha256(raw).hexdigest()
                or daily._canonical(manifest["sources"]) != daily._canonical(source_bindings())
                or daily._canonical(manifest["aggregation_rules"]) != daily._canonical(rules())
                or daily._canonical(manifest["feature_rules"]) != daily._canonical(daily.rule_definitions())
                or daily._canonical(manifest["fill_rules"]) != daily._canonical(fills.rules())
                or daily._canonical(manifest["profiles"]) != daily._canonical(fills.risk.profiles())
                or manifest["orders_available"] is not False or manifest["market_data_qualified"] is not False):
            raise ValueError("bars_freeze_binding")
        if source_bindings()["config/research-candidates-117.json"] != daily.DECLARATION_SHA256:
            raise ValueError("fixed_declaration_changed")
        try:
            if type(manifest["frozen_at_utc"]) is not str:
                raise ValueError("freeze_time")
            instant = datetime.fromisoformat(manifest["frozen_at_utc"])
            if instant.utcoffset() is None or instant.utcoffset().total_seconds() != 0:
                raise ValueError("freeze_time")
        except (TypeError, ValueError) as exc:
            raise ValueError("freeze_time") from exc
        self._fixture = deepcopy(validate_fixture(daily._json(raw)))
        if manifest["case"] != self._fixture["case"]:
            raise ValueError("bars_freeze_case")
        self._binding, self._fixture_sha = hashlib.sha256(mraw).hexdigest(), hashlib.sha256(raw).hexdigest()
        self._state = {"cursor": 0, "last_event": None, "last_quote": None, "clock_msc": None,
                       "next_session": 0, "pending": {}, "bars": [], "publications": [], "outcomes": [],
                       "prefix_sha256": "0" * 64}

    @property
    def state(self):
        return deepcopy(self._state)

    def _finalize(self, new, event):
        finalized = []
        calendar = self._fixture["calendar"]
        sessions = calendar["sessions"]
        while new["next_session"] < len(sessions):
            i = new["next_session"]
            session = sessions[i]
            if session["end_msc"] + 2000 > event["receipt_msc"]:
                break
            observations = new["pending"].pop(str(i), [])
            coverage = _coverage(observations, session)
            status = "closure" if session["status"] == "closure" else "completed" if coverage["complete"] else "incomplete"
            bar = None
            if status == "completed":
                midpoints = [Decimal(r["midpoint"]) for r in observations]
                bar = {"session_id": i, "start_msc": session["start_msc"], "end_msc": session["end_msc"],
                       "observation_msc": observations[-1]["source_msc"], "available_msc": event["receipt_msc"],
                       "open": float(midpoints[0]), "high": float(max(midpoints)), "low": float(min(midpoints)),
                       "close": float(midpoints[-1])}
                bar["lineage_sha256"] = daily.bar_lineage(self._fixture["case"], calendar["calendar_id"], session, bar)
                new["bars"].append(bar)
            evidence = {"session_id": i, "status": status, "published_msc": event["receipt_msc"],
                        "finalizer_sequence": event["sequence"], "finalizer_sha256": daily._digest(event),
                        "quote_evidence": observations, "coverage": coverage,
                        "bar_lineage_sha256": bar["lineage_sha256"] if bar else None,
                        "calendar_prefix_sha256": daily._digest({**calendar, "sessions": sessions[:i + 1]}),
                        "message_prefix_sha256": new["prefix_sha256"]}
            evidence["publication_sha256"] = daily._digest(evidence)
            new["publications"].append(evidence)
            new["next_session"] += 1
            finalized.append(i)
        return finalized

    def _step(self, event):
        _message(event)
        old = self._state
        if old["last_event"] is not None and daily._canonical(event) == daily._canonical(old["last_event"]):
            return False
        cursor = old["cursor"]
        if cursor >= len(self._fixture["messages"]) or daily._canonical(event) != daily._canonical(self._fixture["messages"][cursor]):
            raise ValueError("message_binding")
        # Copy mutable containers only; finalized records are never revised.
        new = {**old, "pending": deepcopy(old["pending"]), "bars": list(old["bars"]),
               "publications": list(old["publications"]), "outcomes": list(old["outcomes"])}
        new["prefix_sha256"] = hashlib.sha256(bytes.fromhex(old["prefix_sha256"]) + daily._canonical(event)).hexdigest()
        finalized = self._finalize(new, event)
        session_id, midpoint = None, None
        reason = "clock_advance"
        if event["kind"] == "quote":
            session = next(s for s in self._fixture["calendar"]["sessions"] if s["start_msc"] <= event["source_msc"] < s["end_msc"])
            session_id = session["session_id"]
            repeated = old["last_quote"] is not None and event["source_msc"] == old["last_quote"]["source_msc"]
            if session_id < new["next_session"]:
                reason = "finalized_quote"
            elif event["receipt_msc"] - event["source_msc"] > 2000:
                reason = "stale_quote"
            elif repeated:
                reason = "repeated_source"
            elif session["status"] == "closure":
                reason = "closed_quote"
            else:
                reason = "accepted_quote"
                midpoint = fills.S((Decimal(str(event["bid"])) + Decimal(str(event["ask"]))) / 2)
                new["pending"].setdefault(str(session_id), []).append({"sequence": event["sequence"],
                    "source_msc": event["source_msc"], "receipt_msc": event["receipt_msc"],
                    "midpoint": midpoint, "quote_sha256": daily._digest(event)})
            new["last_quote"] = deepcopy(event)
        new["outcomes"].append({"sequence": event["sequence"], "reason": reason, "session_id": session_id,
                                "midpoint": midpoint, "finalized_sessions": finalized,
                                "prefix_sha256": new["prefix_sha256"]})
        new.update(cursor=cursor + 1, last_event=deepcopy(event), clock_msc=event["receipt_msc"])
        self._state = new
        return True

    def step(self, event):
        with localcontext() as ctx:
            ctx.prec = 50
            return self._step(event)

    def features(self, target=None, decision_msc=None):
        if not self._state["bars"]:
            raise ValueError("no_completed_bar")
        latest = self._state["bars"][-1]
        value = {"format": daily.VERSION, "kind": "invented_daily_fixture", "clock": "invented_utc_milliseconds",
                 "symbol": "EURUSD", "case": self._fixture["case"], "calendar": deepcopy(self._fixture["calendar"]),
                 "bars": deepcopy(self._state["bars"]), "target_session_id": latest["session_id"] if target is None else target,
                 "decision_msc": latest["available_msc"] if decision_msc is None else decision_msc}
        daily.snapshot(value)
        return value

    def run(self):
        for event in self._fixture["messages"][self._state["cursor"]:]:
            self.step(event)
        return self.report()

    def report(self):
        if self._state["cursor"] != len(self._fixture["messages"]):
            raise ValueError("unfinished_aggregation_report")
        return {"kind": "invented_quote_aggregation_only", "case": self._fixture["case"],
                "fixture_sha256": self._fixture_sha, "manifest_sha256": self._binding, "final_state": self.state,
                "returns": None, "market_data_qualified": False, "orders_available": False,
                "paper_evaluation_available": False, "strategy_selected": False, "real_money_execution_available": False}

    def checkpoint(self):
        p = {"schema": "daily_bars121_checkpoint_v1", "fixture_sha256": self._fixture_sha,
             "manifest_sha256": self._binding, "cursor": self._state["cursor"], "state": self.state}
        return json.dumps({"payload": p, "sha256": daily._digest(p)}, sort_keys=True, allow_nan=False)

    @classmethod
    def restore(cls, path, manifest_path, checkpoint):
        if type(checkpoint) is not str or len(checkpoint.encode()) > daily.MAX_BYTES:
            raise ValueError("checkpoint_size")
        value = daily._json(checkpoint)
        daily._fields(value, {"payload", "sha256"}, "checkpoint_envelope")
        p = value["payload"]
        daily._fields(p, {"schema", "fixture_sha256", "manifest_sha256", "cursor", "state"}, "checkpoint_payload")
        result = cls(path, manifest_path)
        if (value["sha256"] != daily._digest(p) or p["schema"] != "daily_bars121_checkpoint_v1"
                or p["fixture_sha256"] != result._fixture_sha or p["manifest_sha256"] != result._binding):
            raise ValueError("checkpoint_binding")
        cursor = daily._integer(p["cursor"], 0, len(result._fixture["messages"]), "checkpoint_cursor")
        for event in result._fixture["messages"][:cursor]:
            result.step(event)
        if daily._canonical(p["state"]) != daily._canonical(result._state):
            raise ValueError("checkpoint_reconstructed_state")
        return result


def compile_fills(replay):
    """Derive120 inputs from the same observed quotes, never midpoint execution."""
    if type(replay) is not Replay or replay._state["cursor"] != len(replay._fixture["messages"]):
        raise ValueError("unfinished_compilation")
    partition = replay._fixture["execution_start_msc"]
    if partition is None:
        raise ValueError("aggregation_only")
    quotes = [q for q in replay._fixture["messages"] if q["kind"] == "quote" and q["source_msc"] >= partition]
    if not quotes:
        raise ValueError("no_execution_quotes")
    try:
        features = replay.features()
        events = []
        for q in quotes:
            latest = fills.risk._latest(features, q["receipt_msc"])
            if latest is None:
                raise ValueError("no_available_feature")
            bar = next(b for b in features["bars"] if b["session_id"] == latest)
            events.append({"sequence": len(events), **{k: q[k] for k in ("source_msc", "receipt_msc", "bid", "ask")},
                           "target_session_id": latest, "feature_decision_msc": bar["available_msc"]})
        value = {"format": fills.VERSION, "kind": "invented_daily_fills_fixture", "clock": "invented_utc_milliseconds",
                 "symbol": "EURUSD", "case": replay._fixture["case"], "features": features,
                 "initial_account": deepcopy(replay._fixture["initial_account"]), "events": events}
        fills.validate_fixture(value)
    except ValueError as exc:
        if str(exc) in ("missing_required_session", "missing_completed_session"):
            raise ValueError("incomplete_required_session") from exc
        raise
    return value


def evaluate_fixture(path, manifest_path, output_directory):
    replay = Replay(path, manifest_path)
    output = Path(output_directory)
    output.mkdir()  # Exclusive directory; no existing artifacts are overwritten.
    aggregation = replay.run()
    daily.write_new(output / "aggregation.json", aggregation)
    status, reason, report = "unavailable", None, None
    try:
        compiled = compile_fills(replay)
    except ValueError as exc:
        reason = str(exc)
    else:
        daily.write_new(output / "fills-input.json", compiled)
        fills.freeze_fixture(output / "fills-input.json", output / "fills-frozen.json")
        try:
            report = fills.evaluate_fixture(output / "fills-input.json", output / "fills-frozen.json", output / "fills-report.json")
        except ValueError as exc:
            reason = str(exc)
        else:
            status = "invented_accounting_verified_by_pipeline"
    result = {"kind": "invented_coherent_quote_bar_pipeline", "case": replay._fixture["case"],
              "fixture_sha256": replay._fixture_sha, "integration_manifest_sha256": replay._binding,
              "aggregation_sha256": hashlib.sha256(daily._read(output / "aggregation.json")).hexdigest(),
              "status": status, "reason": reason, "returns": None if report is None else "toy_ledger_only",
              "comparisons": 0 if report is None else len(report["results"]),
              "derived_bindings": {p.name: hashlib.sha256(daily._read(p)).hexdigest() for p in sorted(output.iterdir())},
              "market_data_qualified": False, "paper_evaluation_available": False, "strategy_selected": False,
              "orders_available": False, "real_money_execution_available": False}
    daily.write_new(output / "pipeline-report.json", result)
    return result
