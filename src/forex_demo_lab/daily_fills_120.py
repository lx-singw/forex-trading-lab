"""Offline invented daily fills and accounting. No broker or order interface."""
from copy import deepcopy
from dataclasses import asdict
from datetime import datetime, timezone
from decimal import Decimal, ROUND_FLOOR, localcontext
import hashlib
import json

from . import daily_features_118 as daily
from . import daily_risk_119 as risk

VERSION = "FXDL_DAILYFILLS120_V1"
EVENT_FIELDS = risk.EVENT_FIELDS - {"equity_usd", "free_margin_usd"}
DEPENDENCIES = risk.DEPENDENCIES + (
    "src/forex_demo_lab/daily_fills_120.py", "src/forex_demo_lab/daily_fills_fixture_120.py",
    "scripts/daily-fills-120.py", "tests/test_daily_fills_120.py",
    "docs/DAILY-FILLS-120-PROTOCOL.md", "docs/DAILY-FILLS-120-PLAN.md",
)


def D(value):
    return Decimal(str(value))


def S(value):
    return "0" if value == 0 else format(value.normalize(), "f")


def rules():
    return {"schema": VERSION, "feature_rules": daily.rule_definitions(), "precision": 50,
            "admission": "119_first_eligible_per_completed_session",
            "acceptance": "same_quote_invented_atomic_acceptance", "max_positions": 1,
            "exit_quality": "new_fresh_trading_source", "exit_spread_cap": None,
            "held_at_arrival_prevents_reentry": True, "stop": "observed_adverse_slippage",
            "target": "original_limit_no_overshoot_or_extra_slippage",
            "financing": "every_elapsed_UTC_midnight_previous_weekday_Wednesday_triple",
            "equity": "019B_raw_open_mark_actual_breach_fill", "margin": "original_entry_notional_over_30",
            "finish": "final_executable_quote_only", "orders_available": False}


def _event(event):
    daily._fields(event, EVENT_FIELDS, "fill_event_fields")
    # Reuse119's strict quote/time checks, without admitting any supplied marks.
    risk._event({**event, "equity_usd": 0, "free_margin_usd": 0})


def validate_fixture(value):
    daily._fields(value, {"format", "kind", "clock", "symbol", "case", "features", "initial_account", "events"},
                  "fill_fixture_fields")
    if (value["format"] != VERSION or value["kind"] != "invented_daily_fills_fixture"
            or value["clock"] != "invented_utc_milliseconds" or value["symbol"] != "EURUSD"):
        raise ValueError("invented_fills_fixture_required")
    daily._name(value["case"], "fill_fixture_case")
    daily.snapshot(value["features"])
    account = value["initial_account"]
    daily._fields(account, {"kind", "trade_mode", "currency", "available_msc", "balance_usd"}, "fill_account_fields")
    if account["kind"] != "invented_flat_cash" or account["currency"] != "USD":
        raise ValueError("invented_flat_USD_cash_required")
    if type(account["trade_mode"]) is not int or account["trade_mode"] != 0:
        raise ValueError("synthetic_demo_account_required")
    daily._integer(account["available_msc"], daily.MIN_TIME, daily.MAX_TIME, "account_time")
    if risk._money(account["balance_usd"]) <= 0:
        raise ValueError("initial_balance")
    events = value["events"]
    if type(events) is not list or not 1 <= len(events) <= risk.MAX_EVENTS:
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
                event[k] != events[i - 1][k] for k in ("bid", "ask")):
            raise ValueError("source_price_conflict")
        if not calendar[0]["start_msc"] <= event["source_msc"] <= event["receipt_msc"] < calendar[-1]["end_msc"]:
            raise ValueError("quote_outside_calendar")
        daily.snapshot(risk._request(value["features"], event))
        risk._latest(value["features"], event["receipt_msc"])
    if account["available_msc"] > events[0]["source_msc"]:
        raise ValueError("account_unavailable")
    return value


def source_bindings():
    return {n: hashlib.sha256(daily._read(risk.ROOT / n)).hexdigest() for n in DEPENDENCIES}


def freeze_fixture(path, output):
    raw = daily._read(path)
    value = validate_fixture(daily._json(raw))
    sources = source_bindings()
    if sources["config/research-candidates-117.json"] != daily.DECLARATION_SHA256:
        raise ValueError("fixed_declaration_changed")
    manifest = {"format": "FXDL_DAILYFILLS120_FREEZE_V1", "kind": "invented_fills_freeze",
                "frozen_at_utc": datetime.now(timezone.utc).isoformat(), "fixture_sha256": hashlib.sha256(raw).hexdigest(),
                "case": value["case"], "sources": sources, "rules": rules(), "profiles": risk.profiles(),
                "rules_sha256": daily._digest(rules()), "profiles_sha256": daily._digest(risk.profiles()),
                "orders_available": False, "market_data_qualified": False}
    daily.write_new(output, manifest)
    return manifest


def _quote(event, profile):
    bid = D(event["bid"])
    spread = max(D(event["ask"]) - bid, D(profile["spread_floor_pips"]) * D(".0001"))
    return bid, bid + spread, spread


def _size(feature, event, profile, equity, free, day_floor, binding, candidate):
    """119 sizing with exact persistent decimal levels instead of float estimates."""
    c = profile["config"]
    bid, ask, spread = _quote(event, profile)
    slip, units, fee = D(c["slippage_pips"]) * D(".0001"), D(c["contract_size"]), D(c["commission_per_lot_round_turn"])
    side, distance = feature.side, D(feature.stop_distance)
    entry = ask + slip if side == 1 else bid - slip
    stop, target = entry - side * distance, entry + side * distance * D(c["reward_risk"])
    if distance <= spread + slip or min(entry, stop, target) <= 0:
        return None, "price_geometry"
    fraction = D(c["risk_fraction"]) * D(feature.risk_multiplier)
    budget = equity * fraction
    stop_per_lot = (distance + slip) * units + fee
    immediate_per_lot = (spread + 2 * slip) * units + fee
    margin_per_lot = entry * units / D(c["leverage"])
    raw_risk = budget / stop_per_lot
    raw_margin = max(D(0), free) / (margin_per_lot + fee / 2)
    step, minimum = D(c["lot_step"]), D(c["lot_min"])
    lots = (min(raw_risk, raw_margin, D(c["lot_max"])) / step).to_integral_value(rounding=ROUND_FLOOR) * step
    if lots < minimum:
        return None, "minimum_lot_risk" if raw_risk < minimum else "minimum_lot_margin"
    estimated, margin, immediate, entry_fee = lots * stop_per_lot, lots * margin_per_lot, lots * immediate_per_lot, lots * fee / 2
    if estimated > budget or margin + entry_fee > free:
        raise ValueError("proposal_bound")
    if equity - immediate <= day_floor:
        return None, "daily_headroom"
    proposal = {"candidate": candidate, "side": side, "feature_binding": binding,
                "sequence": event["sequence"], "source_msc": event["source_msc"], "target_session_id": feature.target_session_id,
                **{k: S(v) for k, v in {"lots": lots, "entry": entry, "stop": stop, "target": target,
                   "risk_fraction": fraction, "risk_budget_usd": budget, "estimated_stop_risk_usd": estimated,
                   "immediate_liquidation_debit_usd": immediate, "margin_usd": margin, "entry_fee_usd": entry_fee}.items()}}
    proposal["proposal_id"] = daily._digest(proposal)
    return proposal, "entry_filled"


class Replay:
    """Frozen invented execution ledger; every economic state is prefix-rebuildable."""
    def __init__(self, path, manifest_path, profile="base", candidate="MIX50_D"):
        if type(profile) is not str or profile not in risk.profiles() or type(candidate) is not str or candidate not in daily.CANDIDATES:
            raise ValueError("profile_or_candidate")
        raw, mraw = daily._read(path), daily._read(manifest_path)
        manifest = daily._json(mraw)
        daily._fields(manifest, {"format", "kind", "frozen_at_utc", "fixture_sha256", "case", "sources", "rules", "profiles",
                                "rules_sha256", "profiles_sha256", "orders_available", "market_data_qualified"}, "fill_manifest_fields")
        if (manifest["format"] != "FXDL_DAILYFILLS120_FREEZE_V1" or manifest["kind"] != "invented_fills_freeze"
                or manifest["fixture_sha256"] != hashlib.sha256(raw).hexdigest()
                or daily._canonical(manifest["sources"]) != daily._canonical(source_bindings())
                or daily._canonical(manifest["rules"]) != daily._canonical(rules())
                or daily._canonical(manifest["profiles"]) != daily._canonical(risk.profiles())
                or manifest["rules_sha256"] != daily._digest(rules()) or manifest["profiles_sha256"] != daily._digest(risk.profiles())
                or manifest["orders_available"] is not False or manifest["market_data_qualified"] is not False):
            raise ValueError("fill_freeze_binding")
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
            raise ValueError("fill_freeze_case")
        self._binding, self._fixture_sha = hashlib.sha256(mraw).hexdigest(), hashlib.sha256(raw).hexdigest()
        self.profile, self.candidate = profile, candidate
        cash = str(self._fixture["initial_account"]["balance_usd"])
        with localcontext() as ctx:
            ctx.prec = 50
            cash = S(D(cash))
        self._state = {"cursor": 0, "last_event": None, "last_quote": None, "day": None,
                       "day_start_equity": cash, "previous_equity": cash, "paused": False,
                       "balance_usd": cash, "equity_usd": cash, "margin_usd": "0", "free_margin_usd": cash,
                       "peak_equity_usd": cash, "max_drawdown": "0", "held": None, "reservation": None,
                       "session_bindings": {}, "consumed_sessions": [], "ledger": [], "outcomes": [], "finished": False}

    @property
    def state(self):
        return deepcopy(self._state)

    def _record(self, state, event, kind, **fields):
        row = {"index": len(state["ledger"]), "sequence": event["sequence"], "source_msc": event["source_msc"],
               "kind": kind, **fields}
        state["ledger"].append(row)

    def _financing(self, state, event):
        held = state["held"]
        if held is None:
            return
        c = risk.profiles()[self.profile]["config"]
        day = event["source_msc"] // daily.DAY
        for old_day in range(held["financed_through_day"], day):
            weekday = datetime.fromtimestamp(old_day * daily.DAY / 1000, timezone.utc).weekday()
            multiplier = 0 if weekday >= 5 else 3 if weekday == c["triple_swap_weekday"] else 1
            rate = D(c["swap_long_per_lot"] if held["side"] == 1 else c["swap_short_per_lot"])
            amount = rate * D(held["lots"]) * multiplier
            state["balance_usd"] = S(D(state["balance_usd"]) + amount)
            held["financing_usd"] = S(D(held["financing_usd"]) + amount)
            self._record(state, event, "financing", position_id=held["position_id"], rollover_msc=(old_day + 1) * daily.DAY,
                         weekday=weekday, multiplier=multiplier, amount_usd=S(amount), balance_usd=state["balance_usd"])
        held["financed_through_day"] = day

    def _exit(self, state, event, reason, price):
        if price <= 0:
            raise ValueError("nonpositive_exit_price")
        held, c = state["held"], risk.profiles()[self.profile]["config"]
        gross = held["side"] * (price - D(held["entry"])) * D(held["lots"]) * D(c["contract_size"])
        fee = D(held["lots"]) * D(c["commission_per_lot_round_turn"]) / 2
        state["balance_usd"] = S(D(state["balance_usd"]) + gross - fee)
        net = gross - fee - D(held["entry_fee_usd"]) + D(held["financing_usd"])
        self._record(state, event, "exit_fill", position_id=held["position_id"], reason=reason, price=S(price),
                     side=held["side"], lots=held["lots"], gross_usd=S(gross), fee_usd=S(fee),
                     financing_usd=held["financing_usd"], net_trade_usd=S(net), balance_usd=state["balance_usd"],
                     estimated_stop_risk_usd=held["estimated_stop_risk_usd"])
        self._record(state, event, "release", position_id=held["position_id"])
        state["held"], state["reservation"] = None, None

    def _mark(self, state):
        equity, margin = D(state["balance_usd"]), D(0)
        held = state["held"]
        if held:
            bid, ask, _ = _quote(state["last_quote"], risk.profiles()[self.profile])
            price = bid if held["side"] == 1 else ask
            equity += held["side"] * (price - D(held["entry"])) * D(held["lots"]) * D(100000)
            margin = D(held["margin_usd"])
        state.update(equity_usd=S(equity), margin_usd=S(margin), free_margin_usd=S(equity - margin))
        peak = max(D(state["peak_equity_usd"]), equity)
        state["peak_equity_usd"] = S(peak)
        state["max_drawdown"] = S(max(D(state["max_drawdown"]), (peak - equity) / peak))
        if equity <= D(state["day_start_equity"]) * D(".99"):
            state["paused"] = True

    def _step(self, event):
        _event(event)
        state = self._state
        if state["last_event"] is not None and daily._canonical(event) == daily._canonical(state["last_event"]):
            return False
        if state["finished"]:
            raise ValueError("finished_replay")
        cursor = state["cursor"]
        if cursor >= len(self._fixture["events"]) or daily._canonical(event) != daily._canonical(self._fixture["events"][cursor]):
            raise ValueError("event_binding")
        features = self._fixture["features"]
        feature = daily.decisions(risk._request(features, event))[self.candidate]
        binding, key = daily._digest(asdict(feature)), str(feature.target_session_id)
        if key in state["session_bindings"] and state["session_bindings"][key] != binding:
            raise ValueError("session_identity_changed")
        new = deepcopy(state)
        new["session_bindings"][key] = binding
        day = event["source_msc"] // daily.DAY
        if new["day"] != day:
            new.update(day=day, day_start_equity=new["previous_equity"], paused=False)
        self._financing(new, event)
        c = risk.profiles()[self.profile]["config"]
        profile = risk.profiles()[self.profile]
        bid, ask, spread = _quote(event, profile)
        slip = D(c["slippage_pips"]) * D(".0001")
        row = next(r for r in features["calendar"]["sessions"] if r["start_msc"] <= event["source_msc"] < r["end_msc"])
        repeated = state["last_event"] is not None and event["source_msc"] == state["last_event"]["source_msc"]
        executable = not repeated and event["receipt_msc"] - event["source_msc"] <= 2000 and row["status"] == "trading"
        held_at_arrival = new["held"] is not None
        if executable:
            new["last_quote"] = deepcopy(event)
            if new["held"]:
                held = new["held"]
                price = bid if held["side"] == 1 else ask
                if held["side"] * (price - D(held["stop"])) <= 0:
                    self._exit(new, event, "stop", price - held["side"] * slip)
                elif held["side"] * (price - D(held["target"])) >= 0:
                    self._exit(new, event, "target", D(held["target"]))
        self._mark(new)
        pre_entry = {k: new[k] for k in ("balance_usd", "equity_usd", "margin_usd", "free_margin_usd")}
        proposal = None
        if event["source_msc"] <= feature.decision_msc:
            reason = "before_feature"
        elif event["receipt_msc"] - event["source_msc"] > 2000:
            reason = "stale_quote"
        elif repeated:
            reason = "repeated_source"
        elif row["status"] != "trading":
            reason = "closed_quote"
        elif risk._latest(features, event["receipt_msc"]) != feature.target_session_id:
            reason = "stale_feature"
        elif spread > D(c["max_spread_pips"]) * D(".0001"):
            reason = "wide_quote"
        elif key in new["consumed_sessions"]:
            reason = "session_consumed"
        else:
            new["consumed_sessions"].append(key)
            if held_at_arrival:
                reason = "held_position"
            elif new["paused"]:
                reason = "daily_pause"
            elif not feature.side or not feature.risk_multiplier:
                reason = "inactive_signal"
            elif D(new["equity_usd"]) <= 0:
                reason = "nonpositive_equity"
            else:
                proposal, reason = _size(feature, event, profile, D(new["equity_usd"]), D(new["free_margin_usd"]),
                                         D(new["day_start_equity"]) * D(".99"), binding, self.candidate)
                if proposal:
                    if new["held"] is not None or new["reservation"] is not None:
                        raise ValueError("aggregate_slot")
                    pid = proposal["proposal_id"]
                    new["reservation"] = {"position_id": pid, "status": "pending"}
                    self._record(new, event, "reserve", position_id=pid)
                    new["balance_usd"] = S(D(new["balance_usd"]) - D(proposal["entry_fee_usd"]))
                    new["held"] = {**proposal, "position_id": pid, "financing_usd": "0", "financed_through_day": day}
                    new["reservation"]["status"] = "held"
                    self._record(new, event, "entry_fill", position_id=pid, side=feature.side, lots=proposal["lots"],
                                 price=proposal["entry"], fee_usd=proposal["entry_fee_usd"], balance_usd=new["balance_usd"])
                    self._mark(new)
        new["outcomes"].append({"sequence": event["sequence"], "feature_binding": binding,
                                "target_session_id": feature.target_session_id, "feature_side": feature.side,
                                "risk_multiplier": feature.risk_multiplier, "reason": reason, "proposal": proposal,
                                "execution_quote": executable, "held_at_arrival": held_at_arrival,
                                "pre_entry_account": pre_entry, "account": {k: new[k] for k in pre_entry},
                                "paused": new["paused"], "day_start_equity": new["day_start_equity"],
                                "peak_equity_usd": new["peak_equity_usd"], "max_drawdown": new["max_drawdown"]})
        new.update(cursor=cursor + 1, previous_equity=new["equity_usd"], last_event=deepcopy(event))
        self._state = new
        return True

    def step(self, event):
        with localcontext() as ctx:
            ctx.prec = 50
            return self._step(event)

    def finish(self):
        state = self._state
        if state["finished"]:
            return False
        if state["cursor"] != len(self._fixture["events"]):
            raise ValueError("unfinished_fills")
        if state["held"] and not state["outcomes"][-1]["execution_quote"]:
            raise ValueError("missing_executable_endpoint")
        with localcontext() as ctx:
            ctx.prec = 50
            new = deepcopy(state)
            if new["held"]:
                bid, ask, _ = _quote(new["last_event"], risk.profiles()[self.profile])
                side = new["held"]["side"]
                slip = D(risk.profiles()[self.profile]["config"]["slippage_pips"]) * D(".0001")
                self._exit(new, new["last_event"], "boundary", (bid if side == 1 else ask) - side * slip)
                self._mark(new)
            new.update(finished=True, previous_equity=new["equity_usd"])
            self._state = new
        return True

    def run(self):
        for event in self._fixture["events"][self._state["cursor"]:]:
            self.step(event)
        self.finish()
        return self.report()

    def checkpoint(self):
        payload = {"schema": "daily_fills120_checkpoint_v1", "manifest_sha256": self._binding,
                   "fixture_sha256": self._fixture_sha, "profile": self.profile, "candidate": self.candidate,
                   "cursor": self._state["cursor"], "finished": self._state["finished"], "state": self.state}
        return json.dumps({"payload": payload, "sha256": daily._digest(payload)}, sort_keys=True, allow_nan=False)

    @classmethod
    def restore(cls, path, manifest_path, checkpoint, profile="base", candidate="MIX50_D"):
        if type(checkpoint) is not str or len(checkpoint.encode()) > daily.MAX_BYTES:
            raise ValueError("checkpoint_size")
        value = daily._json(checkpoint)
        daily._fields(value, {"payload", "sha256"}, "checkpoint_envelope")
        p = value["payload"]
        daily._fields(p, {"schema", "manifest_sha256", "fixture_sha256", "profile", "candidate", "cursor", "finished", "state"},
                      "checkpoint_payload")
        result = cls(path, manifest_path, profile, candidate)
        if (value["sha256"] != daily._digest(p) or p["schema"] != "daily_fills120_checkpoint_v1"
                or p["manifest_sha256"] != result._binding or p["fixture_sha256"] != result._fixture_sha
                or p["profile"] != profile or p["candidate"] != candidate or type(p["finished"]) is not bool):
            raise ValueError("checkpoint_binding")
        cursor = daily._integer(p["cursor"], 0, len(result._fixture["events"]), "checkpoint_cursor")
        for event in result._fixture["events"][:cursor]:
            result.step(event)
        if p["finished"]:
            result.finish()
        if daily._canonical(p["state"]) != daily._canonical(result._state):
            raise ValueError("checkpoint_reconstructed_state")
        return result

    def report(self):
        if not self._state["finished"]:
            raise ValueError("unfinished_fills_report")
        with localcontext() as ctx:
            ctx.prec = 50
            initial = D(self._fixture["initial_account"]["balance_usd"])
            net = D(self._state["balance_usd"]) - initial
            exits = [r for r in self._state["ledger"] if r["kind"] == "exit_fill"]
            summary = {"initial_cash_usd": S(initial), "final_cash_usd": self._state["balance_usd"],
                       "toy_net_usd": S(net), "toy_return": S(net / initial), "closed_positions": len(exits),
                       "max_drawdown": self._state["max_drawdown"],
                       "gross_usd": S(sum((D(r["gross_usd"]) for r in exits), D(0))),
                       "commissions_usd": S(sum((D(r["fee_usd"]) for r in self._state["ledger"] if "fee_usd" in r), D(0))),
                       "financing_usd": S(sum((D(r["amount_usd"]) for r in self._state["ledger"] if r["kind"] == "financing"), D(0)))}
        return {"format": "FXDL_DAILYFILLS120_REPORT_V1", "kind": "invented_ledger_reconciliation_only",
                "case": self._fixture["case"], "profile": self.profile, "candidate": self.candidate,
                "fixture_sha256": self._fixture_sha, "manifest_sha256": self._binding,
                "summary": summary, "final_state": self.state, "market_data_qualified": False,
                "paper_evaluation_available": False, "strategy_selected": False, "orders_available": False,
                "real_money_execution_available": False}


def evaluate_fixture(path, manifest_path, output):
    results = [Replay(path, manifest_path, profile, candidate).run()
               for profile in risk.profiles() for candidate in daily.CANDIDATES]
    report = {"kind": "invented_daily_fills_demonstration", "results": results,
              "market_data_qualified": False, "strategy_selected": False, "orders_available": False}
    daily.write_new(output, report)
    return report
