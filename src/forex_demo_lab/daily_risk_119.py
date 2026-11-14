"""Invented daily entry proposals only; no fills, returns or broker/order interface."""
from copy import deepcopy
from dataclasses import asdict, replace
from datetime import datetime, timezone
from decimal import Decimal, ROUND_FLOOR, localcontext
import hashlib
import json
from pathlib import Path

from . import daily_features_118 as daily
from .model import Config

ROOT = Path(__file__).resolve().parents[2]
VERSION = "FXDL_DAILYRISK119_V1"
MAX_EVENTS = 256
EVENT_FIELDS = {"sequence", "source_msc", "receipt_msc", "bid", "ask", "target_session_id",
                "feature_decision_msc", "equity_usd", "free_margin_usd"}
ACCOUNT_FIELDS = {"kind", "trade_mode", "currency", "available_msc", "equity_usd", "free_margin_usd", "held"}
HELD_FIELDS = {"kind", "name", "side", "lots", "entry", "stop", "target", "opened_msc"}
DEPENDENCIES = (
    "src/forex_demo_lab/daily_risk_119.py", "src/forex_demo_lab/daily_risk_fixture_119.py",
    "scripts/daily-risk-119.py", "tests/test_daily_risk_119.py",
    "src/forex_demo_lab/daily_features_118.py", "src/forex_demo_lab/daily_fixture_118.py",
    "src/forex_demo_lab/model.py", "src/forex_demo_lab/shadow_engine_113.py",
    "config/research-candidates-117.json", "docs/DAILY-RISK-119-PROTOCOL.md", "docs/DAILY-RISK-119-PLAN.md",
)


def profiles():
    base = Config()
    return {"base": {"config": asdict(base), "spread_floor_pips": 0.0},
            "adverse": {"config": asdict(replace(base, commission_per_lot_round_turn=10.,
                          slippage_pips=.5, swap_long_per_lot=-4.5, swap_short_per_lot=-2.25)),
                        "spread_floor_pips": 1.2}}


def rules():
    return {"schema": VERSION, "candidates": list(daily.CANDIDATES), "feature_rules": daily.rule_definitions(),
            "quote_age_max_msc": 2000, "max_events": MAX_EVENTS, "risk_cap": .0025,
            "daily_loss_cap": .01, "opportunities_per_session": 1, "aggregate_entry_slots": 1,
            "proposal_reservations_released": False, "source_strictly_after_feature": True,
            "decimal_policy": "JSON_decimal_spelling", "positions_fills_returns_orders": False}


def _money(value):
    value = daily._number(value, "account_money")
    if abs(value) > 1e9:
        raise ValueError("account_money")
    return value


def _margin(equity, free):
    if free > max(0, equity):
        raise ValueError("free_margin_exceeds_equity")


def _held(value):
    if value is None:
        return
    daily._fields(value, HELD_FIELDS, "held_fields")
    if value["kind"] != "invented_held_position":
        raise ValueError("invented_held_required")
    daily._name(value["name"], "held_name")
    if type(value["side"]) is not int or value["side"] not in (-1, 1):
        raise ValueError("held_side")
    for key in ("lots", "entry", "stop", "target"):
        daily._number(value[key], "held_value", positive=True)
    lots = Decimal(str(value["lots"]))
    if lots > 1 or lots % Decimal(".01"):
        raise ValueError("held_volume")
    side, entry, stop, target = (value[k] for k in ("side", "entry", "stop", "target"))
    if not (stop < entry < target if side == 1 else target < entry < stop):
        raise ValueError("held_geometry")
    daily._integer(value["opened_msc"], daily.MIN_TIME, daily.MAX_TIME, "held_time")


def _request(features, event):
    value = {**features, "target_session_id": event["target_session_id"],
             "decision_msc": event["feature_decision_msc"]}
    return value


def _event(event):
    daily._fields(event, EVENT_FIELDS, "event_fields")
    daily._integer(event["sequence"], 0, MAX_EVENTS - 1, "event_sequence")
    for key in ("source_msc", "receipt_msc", "feature_decision_msc"):
        daily._integer(event[key], daily.MIN_TIME, daily.MAX_TIME, "event_time")
    daily._integer(event["target_session_id"], 0, daily.MAX_SESSIONS - 1, "target_session_id")
    if event["receipt_msc"] < event["source_msc"]:
        raise ValueError("quote_clock")
    if event["feature_decision_msc"] > event["receipt_msc"]:
        raise ValueError("future_feature_request")
    bid = daily._number(event["bid"], "quote_price", positive=True)
    ask = daily._number(event["ask"], "quote_price", positive=True)
    if bid > ask or ask > 1e6:
        raise ValueError("quote_price")
    equity, free = _money(event["equity_usd"]), _money(event["free_margin_usd"])
    _margin(equity, free)


def _latest(features, receipt):
    bars = {b["session_id"]: b for b in features["bars"]}
    ids = []
    for row in features["calendar"]["sessions"]:
        if row["status"] == "trading" and row["end_msc"] <= receipt:
            if row["session_id"] not in bars:
                raise ValueError("missing_completed_session")
            if bars[row["session_id"]]["available_msc"] <= receipt:
                ids.append(row["session_id"])
    return max(ids) if ids else None


def validate_fixture(value):
    daily._fields(value, {"format", "kind", "clock", "symbol", "case", "features", "initial_account", "events"},
                  "risk_fixture_fields")
    if (value["format"] != VERSION or value["kind"] != "invented_daily_risk_fixture"
            or value["clock"] != "invented_utc_milliseconds" or value["symbol"] != "EURUSD"):
        raise ValueError("invented_risk_fixture_required")
    daily._name(value["case"], "risk_fixture_case")
    daily.snapshot(value["features"])
    account = value["initial_account"]
    daily._fields(account, ACCOUNT_FIELDS, "account_fields")
    if account["kind"] != "invented_account_state" or account["currency"] != "USD":
        raise ValueError("invented_USD_account_required")
    if type(account["trade_mode"]) is not int or account["trade_mode"] != 0:
        raise ValueError("synthetic_demo_account_required")
    daily._integer(account["available_msc"], daily.MIN_TIME, daily.MAX_TIME, "account_time")
    equity, free = _money(account["equity_usd"]), _money(account["free_margin_usd"])
    if equity <= 0:
        raise ValueError("initial_equity")
    _margin(equity, free)
    _held(account["held"])
    if account["held"] and account["held"]["opened_msc"] > account["available_msc"]:
        raise ValueError("held_unavailable")
    events = value["events"]
    if type(events) is not list or not 1 <= len(events) <= MAX_EVENTS:
        raise ValueError("event_count")
    calendar = value["features"]["calendar"]["sessions"]
    for i, event in enumerate(events):
        _event(event)
        if event["sequence"] != i:
            raise ValueError("event_sequence")
        if i and (event["source_msc"] < events[i - 1]["source_msc"]
                  or event["receipt_msc"] < events[i - 1]["receipt_msc"]):
            raise ValueError("event_order")
        if i and event["source_msc"] == events[i - 1]["source_msc"] and any(
                event[s] != events[i - 1][s] for s in ("bid", "ask")):
            raise ValueError("source_price_conflict")
        if not calendar[0]["start_msc"] <= event["source_msc"] <= event["receipt_msc"] < calendar[-1]["end_msc"]:
            raise ValueError("quote_outside_calendar")
        daily.snapshot(_request(value["features"], event))
        _latest(value["features"], event["receipt_msc"])
    if account["available_msc"] > events[0]["source_msc"]:
        raise ValueError("account_unavailable")
    return value


def source_bindings():
    return {n: hashlib.sha256(daily._read(ROOT / n)).hexdigest() for n in DEPENDENCIES}


def freeze_fixture(path, output):
    raw = daily._read(path)
    value = validate_fixture(daily._json(raw))
    sources = source_bindings()
    if sources["config/research-candidates-117.json"] != daily.DECLARATION_SHA256:
        raise ValueError("fixed_declaration_changed")
    manifest = {"format": "FXDL_DAILYRISK119_FREEZE_V1", "kind": "invented_risk_freeze",
                "frozen_at_utc": datetime.now(timezone.utc).isoformat(),
                "fixture_sha256": hashlib.sha256(raw).hexdigest(), "case": value["case"],
                "sources": sources, "rules": rules(), "rules_sha256": daily._digest(rules()),
                "profiles": profiles(), "profiles_sha256": daily._digest(profiles()),
                "orders_available": False, "returns_computed": False}
    daily.write_new(output, manifest)
    return manifest


def _propose(decision, event, profile, candidate, feature_binding, day_floor):
    if (type(decision.side) is not int or decision.side not in (-1, 1)
            or daily._number(decision.risk_multiplier, "proposal_signal") not in (.5, 1)):
        raise ValueError("proposal_signal")
    daily._number(decision.stop_distance, "proposal_signal", positive=True)
    with localcontext() as ctx:
        ctx.prec = 50
        d = lambda x: Decimal(str(x))
        config, floor = profile["config"], d(profile["spread_floor_pips"]) * d(.0001)
        bid, spread = d(event["bid"]), max(d(event["ask"]) - d(event["bid"]), floor)
        slip, units = d(config["slippage_pips"]) * d(.0001), d(config["contract_size"])
        distance, side = d(decision.stop_distance), decision.side
        entry = bid + spread + slip if side == 1 else bid - slip
        stop, target = entry - side * distance, entry + side * distance * d(config["reward_risk"])
        if distance <= spread + slip or min(entry, stop, target) <= 0:
            return None, "price_geometry"
        fraction = d(config["risk_fraction"]) * d(decision.risk_multiplier)
        budget = d(event["equity_usd"]) * fraction
        fee = d(config["commission_per_lot_round_turn"])
        stop_per_lot = (distance + slip) * units + fee
        immediate_per_lot = (spread + 2 * slip) * units + fee
        margin_per_lot = entry * units / d(config["leverage"])
        raw_risk = budget / stop_per_lot
        raw_margin = max(d(0), d(event["free_margin_usd"])) / (margin_per_lot + fee / 2)
        raw = min(raw_risk, raw_margin, d(config["lot_max"]))
        step, minimum = d(config["lot_step"]), d(config["lot_min"])
        lots = (raw / step).to_integral_value(rounding=ROUND_FLOOR) * step
        if lots < minimum:
            return None, "minimum_lot_risk" if raw_risk < minimum else "minimum_lot_margin"
        risk, margin, immediate, entry_fee = lots * stop_per_lot, lots * margin_per_lot, lots * immediate_per_lot, lots * fee / 2
        if risk > budget or margin + entry_fee > d(event["free_margin_usd"]):
            raise ValueError("proposal_bound")
        if d(event["equity_usd"]) - immediate <= d(day_floor):
            return None, "daily_headroom"
        proposal = {"kind": "invented_entry_proposal", "candidate": candidate, "side": side,
                    "lots": float(lots), "entry_estimate": float(entry), "stop": float(stop), "target": float(target),
                    "risk_fraction": float(fraction), "risk_budget_usd": float(budget),
                    "estimated_stop_risk_usd": float(risk), "immediate_liquidation_debit_usd": float(immediate),
                    "estimated_margin_usd": float(margin), "entry_fee_estimate_usd": float(entry_fee),
                    "effective_spread_pips": float(spread / d(.0001)), "feature_binding": feature_binding,
                    "source_msc": event["source_msc"], "receipt_msc": event["receipt_msc"],
                    "sequence": event["sequence"], "target_session_id": decision.target_session_id}
        proposal["proposal_id"] = daily._digest(proposal)
        return proposal, "proposal_reserved"


class Replay:
    """Bound prefix admission state; reservations never imply a filled position."""
    def __init__(self, path, manifest_path, profile="base", candidate="MIX50_D"):
        if type(profile) is not str or profile not in profiles() or type(candidate) is not str or candidate not in daily.CANDIDATES:
            raise ValueError("profile_or_candidate")
        raw, manifest_raw = daily._read(path), daily._read(manifest_path)
        manifest = daily._json(manifest_raw)
        daily._fields(manifest, {"format", "kind", "frozen_at_utc", "fixture_sha256", "case", "sources", "rules",
                                "rules_sha256", "profiles", "profiles_sha256", "orders_available", "returns_computed"},
                      "risk_manifest_fields")
        sources = source_bindings()
        if sources["config/research-candidates-117.json"] != daily.DECLARATION_SHA256:
            raise ValueError("fixed_declaration_changed")
        if (manifest["format"] != "FXDL_DAILYRISK119_FREEZE_V1" or manifest["kind"] != "invented_risk_freeze"
                or manifest["fixture_sha256"] != hashlib.sha256(raw).hexdigest() or manifest["sources"] != sources
                or daily._canonical(manifest["rules"]) != daily._canonical(rules())
                or daily._canonical(manifest["profiles"]) != daily._canonical(profiles())
                or manifest["rules_sha256"] != daily._digest(rules()) or manifest["profiles_sha256"] != daily._digest(profiles())
                or manifest["orders_available"] is not False or manifest["returns_computed"] is not False):
            raise ValueError("risk_freeze_binding")
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
            raise ValueError("risk_freeze_case")
        self._binding = hashlib.sha256(manifest_raw).hexdigest()
        self._fixture_sha = hashlib.sha256(raw).hexdigest()
        self.profile, self.candidate = profile, candidate
        account = self._fixture["initial_account"]
        self._state = {"cursor": 0, "last_event": None, "day": None, "day_start_equity": account["equity_usd"],
                       "previous_equity": account["equity_usd"], "paused": False, "session_bindings": {},
                       "consumed_sessions": [], "held": deepcopy(account["held"]), "reservation": None, "outcomes": []}

    @property
    def state(self):
        return deepcopy(self._state)

    def step(self, event):
        _event(event)
        state = self._state
        if state["last_event"] is not None and daily._canonical(event) == daily._canonical(state["last_event"]):
            return False
        cursor = state["cursor"]
        if cursor >= len(self._fixture["events"]) or daily._canonical(event) != daily._canonical(self._fixture["events"][cursor]):
            raise ValueError("event_binding")
        feature = daily.decisions(_request(self._fixture["features"], event))[self.candidate]
        feature_binding = daily._digest(asdict(feature))
        key = str(event["target_session_id"])
        if key in state["session_bindings"] and state["session_bindings"][key] != feature_binding:
            raise ValueError("session_identity_changed")
        new = deepcopy(state)
        new["session_bindings"][key] = feature_binding
        day = event["source_msc"] // daily.DAY
        if new["day"] != day:
            new.update(day=day, day_start_equity=new["previous_equity"], paused=False)
        day_floor = Decimal(str(new["day_start_equity"])) * Decimal(".99")
        if Decimal(str(event["equity_usd"])) <= day_floor:
            new["paused"] = True
        profile = profiles()[self.profile]
        spread = max(Decimal(str(event["ask"])) - Decimal(str(event["bid"])),
                     Decimal(str(profile["spread_floor_pips"])) * Decimal(".0001"))
        row = next(s for s in self._fixture["features"]["calendar"]["sessions"]
                   if s["start_msc"] <= event["source_msc"] < s["end_msc"])
        repeated = state["last_event"] is not None and event["source_msc"] == state["last_event"]["source_msc"]
        proposal = None
        if event["source_msc"] <= feature.decision_msc:
            reason = "before_feature"
        elif event["receipt_msc"] - event["source_msc"] > 2000:
            reason = "stale_quote"
        elif repeated:
            reason = "repeated_source"
        elif row["status"] != "trading":
            reason = "closed_quote"
        elif _latest(self._fixture["features"], event["receipt_msc"]) != feature.target_session_id:
            reason = "stale_feature"
        elif spread > Decimal(str(profile["config"]["max_spread_pips"])) * Decimal(".0001"):
            reason = "wide_quote"
        elif key in new["consumed_sessions"]:
            reason = "session_consumed"
        else:
            new["consumed_sessions"].append(key)
            if new["held"] is not None:
                reason = "held_position"
            elif new["reservation"] is not None:
                reason = "reserved_entry_slot"
            elif new["paused"]:
                reason = "daily_pause"
            elif not feature.side or not feature.risk_multiplier:
                reason = "inactive_signal"
            elif event["equity_usd"] <= 0:
                reason = "nonpositive_equity"
            else:
                proposal, reason = _propose(feature, event, profile, self.candidate, feature_binding, day_floor)
                if proposal:
                    new["reservation"] = deepcopy(proposal)
        new["outcomes"].append({"sequence": event["sequence"], "target_session_id": feature.target_session_id,
                                "feature_binding": feature_binding, "feature_side": feature.side,
                                "risk_multiplier": feature.risk_multiplier, "reason": reason, "proposal": proposal,
                                "paused": new["paused"], "day_start_equity": new["day_start_equity"]})
        new.update(cursor=cursor + 1, previous_equity=event["equity_usd"], last_event=deepcopy(event))
        self._state = new
        return True

    def run(self):
        for event in self._fixture["events"][self._state["cursor"]:]:
            self.step(event)
        return self.report()

    def checkpoint(self):
        payload = {"schema": "daily_risk119_checkpoint_v1", "manifest_sha256": self._binding,
                   "fixture_sha256": self._fixture_sha, "profile": self.profile, "candidate": self.candidate,
                   "cursor": self._state["cursor"], "state": self._state}
        return json.dumps({"payload": payload, "sha256": daily._digest(payload)}, sort_keys=True, allow_nan=False)

    @classmethod
    def restore(cls, path, manifest_path, checkpoint, profile="base", candidate="MIX50_D"):
        if type(checkpoint) is not str or len(checkpoint.encode()) > daily.MAX_BYTES:
            raise ValueError("checkpoint_size")
        value = daily._json(checkpoint)
        daily._fields(value, {"payload", "sha256"}, "checkpoint_envelope")
        payload = value["payload"]
        daily._fields(payload, {"schema", "manifest_sha256", "fixture_sha256", "profile", "candidate", "cursor", "state"},
                      "checkpoint_payload")
        result = cls(path, manifest_path, profile, candidate)
        if (value["sha256"] != daily._digest(payload) or payload["schema"] != "daily_risk119_checkpoint_v1"
                or payload["manifest_sha256"] != result._binding or payload["fixture_sha256"] != result._fixture_sha
                or payload["profile"] != profile or payload["candidate"] != candidate):
            raise ValueError("checkpoint_binding")
        cursor = daily._integer(payload["cursor"], 0, len(result._fixture["events"]), "checkpoint_cursor")
        for event in result._fixture["events"][:cursor]:
            result.step(event)
        if daily._canonical(payload["state"]) != daily._canonical(result._state):
            raise ValueError("checkpoint_reconstructed_state")
        return result

    def report(self):
        if self._state["cursor"] != len(self._fixture["events"]):
            raise ValueError("unfinished_admission_report")
        return {"format": "FXDL_DAILYRISK119_REPORT_V1", "kind": "invented_admission_and_sizing",
                "case": self._fixture["case"], "profile": self.profile, "candidate": self.candidate,
                "fixture_sha256": self._fixture_sha, "manifest_sha256": self._binding,
                "outcomes": deepcopy(self._state["outcomes"]), "final_state": self.state,
                "returns": None, "fills": None, "equity_curve": None, "positions_created": 0,
                "market_data_qualified": False, "paper_evaluation_available": False,
                "strategy_selected": False, "orders_available": False, "real_money_execution_available": False}


def evaluate_fixture(path, manifest_path, output):
    results = [Replay(path, manifest_path, profile, candidate).run()
               for profile in profiles() for candidate in daily.CANDIDATES]
    report = {"kind": "invented_daily_risk_demonstration", "results": results, "returns": None,
              "fills": None, "orders_available": False, "real_money_execution_available": False}
    daily.write_new(output, report)
    return report
