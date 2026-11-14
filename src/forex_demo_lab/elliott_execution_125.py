"""Standalone invented Elliott ledger from coherent quotes; no broker/order API."""
from copy import deepcopy
from datetime import datetime, timezone
from decimal import Decimal, ROUND_FLOOR, localcontext
import hashlib
from pathlib import Path
import re

from . import daily_features_118 as daily
from . import daily_fills_120 as fills
from . import daily_bars_121 as bars
from . import daily_runs_122 as runs
from . import elliott_waves_124 as waves

D, S = fills.D, fills.S
VERSION = "FXDL_EWEXEC125_V1"
MODELS = (waves.CANDIDATE, "CASH")
DEPENDENCIES = tuple(dict.fromkeys(runs.DEPENDENCIES + waves.DEPENDENCIES + (
    "src/forex_demo_lab/elliott_execution_125.py", "src/forex_demo_lab/elliott_execution_fixture_125.py",
    "scripts/elliott-execution-125.py", "tests/test_elliott_execution_125.py",
    "docs/ELLIOTT-EXECUTION-125-PLAN.md", "docs/ELLIOTT-EXECUTION-125-PROTOCOL.md",
)))


def rules():
    return {"schema": VERSION, "models": list(MODELS), "wave_rules": waves.rules(), "precision": 50,
            "stop": "unchanged_observed_wave_invalidation", "target": "2R_from_actual_slipped_entry",
            "risk_fraction": ".0025", "entry_opportunities_per_feature": 1, "positions": 1,
            "quality": "new_fresh_trading_source_strictly_after_latest_feature",
            "held_arrival_prevents_same_quote_reentry": True, "cash_per_partition_usd": "10000",
            "inherited_accounting": fills.rules(), "aggregation": bars.rules(),
            "endpoint": "declared_final_new_fresh_trading_quote_including_cash",
            "market_data_qualified": False, "orders_available": False}


def source_bindings():
    return {n: hashlib.sha256(daily._read(daily.ROOT / n)).hexdigest() for n in DEPENDENCIES}


def validate_fixture(value):
    daily._fields(value, {"format", "kind", "clock", "symbol", "case", "stream", "partitions"}, "elliott_execution_fields")
    if value["format"] != VERSION or value["kind"] != "invented_elliott_execution":
        raise ValueError("invented_elliott_execution_required")
    runs.validate_fixture({**value, "format": runs.VERSION, "kind": "invented_partitioned_daily_run"})
    return value


def _hash(path):
    return hashlib.sha256(daily._read(path)).hexdigest()


def freeze_fixture(path, output):
    raw = daily._read(path)
    value = validate_fixture(daily._json(raw))
    sources = source_bindings()
    if sources["config/research-candidates-117.json"] != daily.DECLARATION_SHA256:
        raise ValueError("fixed_declaration_changed")
    manifest = {"format": "FXDL_EWEXEC125_FREEZE_V1", "kind": "invented_elliott_execution_freeze",
        "frozen_at_utc": datetime.now(timezone.utc).isoformat(), "fixture_sha256": hashlib.sha256(raw).hexdigest(),
        "case": value["case"], "partitions": value["partitions"], "sources": sources,
        "rules": rules(), "profiles": fills.risk.profiles(), "orders_available": False, "market_data_qualified": False}
    daily.write_new(output, manifest)
    return manifest


def _load(path, manifest_path):
    raw, mraw = daily._read(path), daily._read(manifest_path)
    value, m = daily._json(raw), daily._json(mraw)
    daily._fields(m, {"format", "kind", "frozen_at_utc", "fixture_sha256", "case", "partitions", "sources",
                     "rules", "profiles", "orders_available", "market_data_qualified"}, "elliott_manifest_fields")
    if (m["format"] != "FXDL_EWEXEC125_FREEZE_V1" or m["kind"] != "invented_elliott_execution_freeze"
            or m["fixture_sha256"] != hashlib.sha256(raw).hexdigest()
            or daily._canonical(m["sources"]) != daily._canonical(source_bindings())
            or daily._canonical(m["rules"]) != daily._canonical(rules())
            or daily._canonical(m["profiles"]) != daily._canonical(fills.risk.profiles())
            or m["orders_available"] is not False or m["market_data_qualified"] is not False):
        raise ValueError("elliott_freeze_binding")
    waves._utc_freeze(m["frozen_at_utc"])
    validate_fixture(value)
    if m["case"] != value["case"] or daily._canonical(m["partitions"]) != daily._canonical(value["partitions"]):
        raise ValueError("elliott_freeze_partitions")
    return value, hashlib.sha256(raw).hexdigest(), hashlib.sha256(mraw).hexdigest()


def _structural_size(signal, event, profile, equity, free, day_floor, binding):
    """Pure cost-aware variable-stop sizing; no account connection or execution."""
    c = profile["config"]
    bid, ask, spread = fills._quote(event, profile)
    slip, units, fee = D(c["slippage_pips"]) * D(".0001"), D(c["contract_size"]), D(c["commission_per_lot_round_turn"])
    side, stop = signal["side"], D(signal["prospective_invalidation"])
    if type(side) is not int or side not in (-1, 1):
        raise ValueError("structural_side")
    entry = ask + slip if side == 1 else bid - slip
    distance = side * (entry - stop)
    target = entry + side * 2 * distance
    if distance <= spread + slip or min(entry, stop, target) <= 0:
        return None, "price_geometry"
    if equity <= 0:
        return None, "nonpositive_equity"
    budget = equity * D(c["risk_fraction"])
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
        raise ValueError("structural_proposal_bound")
    if equity - immediate <= day_floor:
        return None, "daily_headroom"
    proposal = {"candidate": waves.CANDIDATE, "side": side, "feature_binding": binding, "pattern_id": signal["pattern_id"],
        "sequence": event["sequence"], "source_msc": event["source_msc"], "target_session_id": event["feature"]["session_id"],
        **{k: S(v) for k, v in {"lots": lots, "entry": entry, "stop": stop, "target": target, "stop_distance": distance,
           "risk_fraction": D(c["risk_fraction"]), "risk_budget_usd": budget, "estimated_stop_risk_usd": estimated,
           "immediate_liquidation_debit_usd": immediate, "margin_usd": margin, "entry_fee_usd": entry_fee}.items()}}
    proposal["proposal_id"] = daily._digest(proposal)
    return proposal, "entry_filled"


def structural_size(signal, event, profile, equity, free, day_floor, binding):
    with localcontext() as ctx:
        ctx.prec = 50
        return _structural_size(signal, event, profile, D(equity), D(free), D(day_floor), binding)


def _demo_guard(account):
    daily._fields(account, {"kind", "trade_mode", "currency", "available_msc", "balance_usd"}, "elliott_account_fields")
    if type(account["trade_mode"]) is not int or account["trade_mode"] != 0:
        raise ValueError("synthetic_demo_account_required")
    if account["kind"] != "invented_flat_cash" or account["currency"] != "USD" or D(account["balance_usd"]) != 10000:
        raise ValueError("fixed_fresh_elliott_cash_required")


def _validate_compiled(value):
    daily._fields(value, {"format", "kind", "clock", "symbol", "case", "partition", "calendar", "initial_account", "events", "derivation"}, "compiled_elliott_fields")
    if (value["format"] != "FXDL_EWEXEC125_COMPILED_V1" or value["kind"] != "invented_elliott_compiled"
            or value["clock"] != "invented_utc_milliseconds" or value["symbol"] != "EURUSD"):
        raise ValueError("invented_elliott_compiled_required")
    _demo_guard(value["initial_account"])
    daily._integer(value["initial_account"]["available_msc"], daily.MIN_TIME, daily.MAX_TIME, "account_time")
    daily._name(value["case"], "compiled_case")
    daily._fields(value["calendar"], daily.CALENDAR_FIELDS, "calendar_fields")
    for i, session in enumerate(value["calendar"]["sessions"]):
        daily._fields(session, daily.SESSION_FIELDS, "session_fields")
        daily.Session(**session)
        if session["session_id"] != i:
            raise ValueError("calendar_sequence")
    if type(value["events"]) is not list or not 1 <= len(value["events"]) <= 256:
        raise ValueError("execution_event_count")
    previous = None
    for i, event in enumerate(value["events"]):
        daily._fields(event, {"sequence", "message_sequence", "source_msc", "receipt_msc", "bid", "ask", "feature"}, "compiled_event_fields")
        daily._integer(event["sequence"], i, i, "execution_sequence")
        daily._integer(event["message_sequence"], 0, bars.MAX_MESSAGES - 1, "message_sequence")
        bars._message({k: event[k] for k in ("source_msc", "receipt_msc", "bid", "ask")} | {"sequence": i, "kind": "quote"})
        if not value["partition"]["start_msc"] <= event["source_msc"] <= event["receipt_msc"] < value["partition"]["end_msc"]:
            raise ValueError("execution_outside_partition")
        if previous and (event["source_msc"] < previous["source_msc"] or event["receipt_msc"] < previous["receipt_msc"]):
            raise ValueError("execution_order")
        if previous and event["source_msc"] == previous["source_msc"] and any(event[k] != previous[k] for k in ("bid", "ask")):
            raise ValueError("source_price_conflict")
        feature = event["feature"]
        daily._fields(feature, {"session_id", "available_msc", "bar_lineage_sha256", "observed_prefix_sha256", "signal"}, "compiled_feature_fields")
        if feature["session_id"] is None:
            if any(feature[k] is not None for k in feature):
                raise ValueError("unpublished_feature_fields")
        else:
            daily._integer(feature["session_id"], 0, len(value["calendar"]["sessions"]) - 1, "feature_session")
            session = value["calendar"]["sessions"][feature["session_id"]]
            daily._integer(feature["available_msc"], session["end_msc"], event["receipt_msc"], "feature_availability")
            for k in ("bar_lineage_sha256", "observed_prefix_sha256"):
                if type(feature[k]) is not str or not re.fullmatch("[0-9a-f]{64}", feature[k]):
                    raise ValueError("feature_lineage")
            if feature["signal"] is not None:
                signal = feature["signal"]
                if (type(signal) is not dict or signal.get("candidate") != waves.CANDIDATE
                        or type(signal.get("side")) is not int or signal["side"] not in (-1, 1)
                        or signal.get("available_msc") != feature["available_msc"]
                        or signal.get("breakout_session_id") != feature["session_id"]
                        or signal.get("observed_prefix_sha256") != feature["observed_prefix_sha256"]
                        or signal.get("rules_sha256") != daily._digest(waves.rules())
                        or not D(signal["prospective_invalidation"]).is_finite() or D(signal["prospective_invalidation"]) <= 0):
                    raise ValueError("compiled_signal_binding")
        previous = event
    if value["initial_account"]["available_msc"] > value["events"][0]["source_msc"]:
        raise ValueError("account_unavailable")
    return value


def _freeze_compiled(path, output, artifacts):
    value = _validate_compiled(daily._json(daily._read(path)))
    manifest = {"format": "FXDL_EWEXEC125_LEDGER_FREEZE_V1", "compiled_sha256": _hash(path), "sources": source_bindings(),
                "rules": rules(), "profiles": fills.risk.profiles(), "artifacts": artifacts, "orders_available": False,
                "market_data_qualified": False, "case": value["case"]}
    daily.write_new(output, manifest)
    return manifest


class Account(fills.Replay):
    """125 admission around unchanged120 record/financing/exit/mark primitives."""
    def __init__(self, path, manifest_path, profile="base", candidate=waves.CANDIDATE):
        if type(profile) is not str or profile not in fills.risk.profiles() or type(candidate) is not str or candidate not in MODELS:
            raise ValueError("elliott_profile_or_candidate")
        raw, mraw = daily._read(path), daily._read(manifest_path)
        manifest = daily._json(mraw)
        daily._fields(manifest, {"format", "compiled_sha256", "sources", "rules", "profiles", "artifacts", "orders_available", "market_data_qualified", "case"}, "ledger_manifest_fields")
        if (manifest["format"] != "FXDL_EWEXEC125_LEDGER_FREEZE_V1" or manifest["compiled_sha256"] != hashlib.sha256(raw).hexdigest()
                or daily._canonical(manifest["sources"]) != daily._canonical(source_bindings())
                or daily._canonical(manifest["rules"]) != daily._canonical(rules())
                or daily._canonical(manifest["profiles"]) != daily._canonical(fills.risk.profiles())
                or manifest["orders_available"] is not False or manifest["market_data_qualified"] is not False):
            raise ValueError("ledger_freeze_binding")
        if type(manifest["artifacts"]) is not dict:
            raise ValueError("derived_artifact_binding")
        for n, h in manifest["artifacts"].items():
            if type(n) is not str or Path(n).name != n or _hash(Path(path).parent / n) != h:
                raise ValueError("derived_artifact_binding")
        self._fixture = deepcopy(_validate_compiled(daily._json(raw)))
        if daily._canonical(self._fixture["derivation"]) != daily._canonical(manifest["artifacts"]):
            raise ValueError("compiled_derivation_binding")
        if manifest["case"] != self._fixture["case"]:
            raise ValueError("compiled_case_binding")
        self._binding, self._fixture_sha = hashlib.sha256(mraw).hexdigest(), hashlib.sha256(raw).hexdigest()
        self.profile, self.candidate = profile, candidate
        self._state = {"cursor": 0, "last_event": None, "last_quote": None, "day": None,
            "day_start_equity": "10000", "previous_equity": "10000", "paused": False,
            "balance_usd": "10000", "equity_usd": "10000", "margin_usd": "0", "free_margin_usd": "10000",
            "peak_equity_usd": "10000", "max_drawdown": "0", "held": None, "reservation": None,
            "session_bindings": {}, "consumed_sessions": [], "ledger": [], "outcomes": [], "finished": False}

    def _step(self, event):
        _demo_guard(self._fixture["initial_account"])
        old = self._state
        if old["last_event"] is not None and daily._canonical(event) == daily._canonical(old["last_event"]):
            return False
        if old["finished"]:
            raise ValueError("finished_replay")
        cursor = old["cursor"]
        if cursor >= len(self._fixture["events"]) or daily._canonical(event) != daily._canonical(self._fixture["events"][cursor]):
            raise ValueError("event_binding")
        feature = event["feature"]
        signal = feature["signal"] if self.candidate != "CASH" else None
        side = signal["side"] if signal else 0
        binding = daily._digest({"candidate": self.candidate, "feature": feature})
        key = str(feature["session_id"]) if feature["session_id"] is not None else None
        if key is not None and key in old["session_bindings"] and old["session_bindings"][key] != binding:
            raise ValueError("session_identity_changed")
        new = self.state
        if key is not None:
            new["session_bindings"][key] = binding
        day = event["source_msc"] // daily.DAY
        if day != new["day"]:
            new.update(day=day, day_start_equity=new["previous_equity"], paused=False)
        self._financing(new, event)
        profile = fills.risk.profiles()[self.profile]
        c = profile["config"]
        bid, ask, spread = fills._quote(event, profile)
        slip = D(c["slippage_pips"]) * D(".0001")
        row = next(s for s in self._fixture["calendar"]["sessions"] if s["start_msc"] <= event["source_msc"] < s["end_msc"])
        repeated = old["last_event"] is not None and event["source_msc"] == old["last_event"]["source_msc"]
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
        if key is None:
            reason = "no_completed_feature"
        elif event["source_msc"] <= feature["available_msc"]:
            reason = "before_feature"
        elif event["receipt_msc"] - event["source_msc"] > 2000:
            reason = "stale_quote"
        elif repeated:
            reason = "repeated_source"
        elif row["status"] != "trading":
            reason = "closed_quote"
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
            elif signal is None:
                reason = "inactive_signal"
            elif D(new["equity_usd"]) <= 0:
                reason = "nonpositive_equity"
            else:
                _demo_guard(self._fixture["initial_account"])
                proposal, reason = structural_size(signal, event, profile, D(new["equity_usd"]), D(new["free_margin_usd"]), D(new["day_start_equity"]) * D(".99"), binding)
                if proposal:
                    if new["held"] is not None or new["reservation"] is not None:
                        raise ValueError("aggregate_slot")
                    pid = proposal["proposal_id"]
                    new["reservation"] = {"position_id": pid, "status": "pending"}
                    self._record(new, event, "reserve", position_id=pid)
                    new["balance_usd"] = S(D(new["balance_usd"]) - D(proposal["entry_fee_usd"]))
                    new["held"] = {**proposal, "position_id": pid, "financing_usd": "0", "financed_through_day": day}
                    new["reservation"]["status"] = "held"
                    self._record(new, event, "entry_fill", position_id=pid, side=side, lots=proposal["lots"], price=proposal["entry"], fee_usd=proposal["entry_fee_usd"], balance_usd=new["balance_usd"])
                    self._mark(new)
        new["outcomes"].append({"sequence": event["sequence"], "message_sequence": event["message_sequence"],
            "feature_binding": binding, "target_session_id": feature["session_id"], "feature_side": side,
            "reason": reason, "proposal": proposal, "execution_quote": executable, "held_at_arrival": held_at_arrival,
            "pre_entry_account": pre_entry, "account": {k: new[k] for k in pre_entry}, "paused": new["paused"],
            "day_start_equity": new["day_start_equity"], "peak_equity_usd": new["peak_equity_usd"], "max_drawdown": new["max_drawdown"]})
        new.update(cursor=cursor + 1, previous_equity=new["equity_usd"], last_event=deepcopy(event))
        self._state = new
        return True

    def finish(self):
        if not self._state["finished"] and self._state["cursor"] == len(self._fixture["events"]) and not self._state["outcomes"][-1]["execution_quote"]:
            raise ValueError("missing_executable_endpoint")
        return super().finish()

    def checkpoint(self):
        value = daily._json(super().checkpoint())
        value["payload"]["schema"] = "elliott_execution125_checkpoint_v1"
        value["sha256"] = daily._digest(value["payload"])
        return value

    @classmethod
    def restore(cls, path, manifest_path, checkpoint, profile="base", candidate=waves.CANDIDATE):
        daily._fields(checkpoint, {"payload", "sha256"}, "elliott_checkpoint_envelope")
        p = checkpoint["payload"]
        daily._fields(p, {"schema", "manifest_sha256", "fixture_sha256", "profile", "candidate", "cursor", "finished", "state"}, "elliott_checkpoint_fields")
        result = cls(path, manifest_path, profile, candidate)
        if (checkpoint["sha256"] != daily._digest(p) or p["schema"] != "elliott_execution125_checkpoint_v1"
                or p["manifest_sha256"] != result._binding or p["fixture_sha256"] != result._fixture_sha
                or p["profile"] != profile or p["candidate"] != candidate or type(p["finished"]) is not bool):
            raise ValueError("elliott_checkpoint_binding")
        cursor = daily._integer(p["cursor"], 0, len(result._fixture["events"]), "elliott_checkpoint_cursor")
        for event in result._fixture["events"][:cursor]:
            result.step(event)
        if p["finished"]:
            result.finish()
        if daily._canonical(result.state) != daily._canonical(p["state"]):
            raise ValueError("elliott_checkpoint_reconstructed_state")
        return result

    def report(self):
        result = super().report()
        result.update(format="FXDL_EWEXEC125_ACCOUNT_REPORT_V1", kind="invented_elliott_ledger_only", sample_status="insufficient", market_assessment="unavailable_invented_unqualified")
        result["summary"]["loss_beyond_entry_estimate"] = [r["position_id"] for r in self._state["ledger"] if r["kind"] == "exit_fill" and -D(r["net_trade_usd"]) > D(r["estimated_stop_risk_usd"])]
        return result


def _prefix(value, part):
    stream = deepcopy(value["stream"])
    stream["messages"] = [m for m in stream["messages"] if m["receipt_msc"] < part["end_msc"]]
    stream["calendar"]["sessions"] = [s for s in stream["calendar"]["sessions"] if s["start_msc"] < part["end_msc"]]
    stream["case"] = "ew_" + part["name"]
    stream["execution_start_msc"] = part["start_msc"]
    stream["initial_account"]["available_msc"] = part["start_msc"]
    return bars.validate_fixture(stream)


def _compile(prefix, aggregation, wave_report, part, derivation):
    completed = aggregation["final_state"]["bars"]
    outcomes = {o["session_id"]: o for o in wave_report["final_state"]["outcomes"]}
    events = []
    for quote in prefix["messages"]:
        if quote["kind"] != "quote" or quote["source_msc"] < part["start_msc"]:
            continue
        available = [b for b in completed if b["available_msc"] <= quote["receipt_msc"]]
        if available:
            latest = available[-1]
            outcome = outcomes[latest["session_id"]]
            feature = {"session_id": latest["session_id"], "available_msc": latest["available_msc"],
                       "bar_lineage_sha256": latest["lineage_sha256"], "observed_prefix_sha256": outcome["observed_prefix_sha256"], "signal": outcome["signal"]}
        else:
            feature = {k: None for k in ("session_id", "available_msc", "bar_lineage_sha256", "observed_prefix_sha256", "signal")}
        events.append({"sequence": len(events), "message_sequence": quote["sequence"],
                       **{k: quote[k] for k in ("source_msc", "receipt_msc", "bid", "ask")}, "feature": deepcopy(feature)})
    value = {"format": "FXDL_EWEXEC125_COMPILED_V1", "kind": "invented_elliott_compiled", "clock": "invented_utc_milliseconds",
        "symbol": "EURUSD", "case": prefix["case"], "partition": deepcopy(part), "calendar": deepcopy(prefix["calendar"]),
        "initial_account": deepcopy(prefix["initial_account"]), "events": events, "derivation": derivation}
    return _validate_compiled(value)


def prepare_partition(value, part, directory):
    """Only raw quotes accepted; all bars/features/signals are derived and frozen."""
    prefix = _prefix(value, part)
    daily.write_new(directory / "prefix-input.json", prefix)
    bars.freeze_fixture(directory / "prefix-input.json", directory / "prefix-frozen.json")
    aggregate = bars.Replay(directory / "prefix-input.json", directory / "prefix-frozen.json")
    aggregation = aggregate.run()
    daily.write_new(directory / "aggregation.json", aggregation)
    runs.Coordinator._endpoint(prefix, part)
    features = aggregate.features()
    wave_value = {"format": waves.VERSION, "kind": "invented_wave_detector", "clock": "invented_utc_milliseconds",
                  "symbol": "EURUSD", "case": prefix["case"], "daily": features}
    daily.write_new(directory / "wave-input.json", wave_value)
    waves.freeze_fixture(directory / "wave-input.json", directory / "wave-frozen.json")
    observed = waves.Replay(directory / "wave-input.json", directory / "wave-frozen.json").run()
    daily.write_new(directory / "wave-report.json", observed)
    artifacts = {p.name: _hash(p) for p in directory.iterdir() if p.is_file()}
    compiled = _compile(prefix, aggregation, observed, part, artifacts)
    daily.write_new(directory / "compiled-input.json", compiled)
    _freeze_compiled(directory / "compiled-input.json", directory / "compiled-frozen.json", artifacts)
    return compiled


def evaluate_fixture(path, manifest_path, output_root):
    value, input_sha, manifest_sha = _load(path, manifest_path)
    root = Path(output_root)
    root.mkdir()
    daily.write_new(root / "run-binding.json", {"input_sha256": input_sha, "manifest_sha256": manifest_sha, "orders_available": False})
    records = []
    for part in value["partitions"]:
        directory = root / part["name"]
        directory.mkdir()
        results, reason = [], None
        try:
            prepare_partition(value, part, directory)
            for profile in fills.risk.profiles():
                for candidate in MODELS:
                    results.append(Account(directory / "compiled-input.json", directory / "compiled-frozen.json", profile, candidate).run())
        except ValueError as exc:
            reason, results = str(exc), []
        if reason is None:
            daily.write_new(directory / "account-reports.json", {"kind": "invented_elliott_accounts", "results": results})
        record = {"partition": part, "status": "unavailable" if reason else "invented_descriptive_only", "reason": reason,
                  "planned_accounts": 4, "computed_accounts": len(results), "results": results,
                  "returns": None if reason else "toy_ledger_only", "market_assessment": "unavailable_invented_unqualified",
                  "artifacts": {p.name: _hash(p) for p in directory.iterdir() if p.is_file()}, "orders_available": False}
        daily.write_new(directory / "partition-report.json", record)
        records.append(record)
    report = {"kind": "invented_elliott_chronological_report", "case": value["case"], "fixture_sha256": input_sha,
              "manifest_sha256": manifest_sha, "partitions": records, "planned_accounts": 8,
              "capital_summed_as_portfolio": False, "market_cells_run": 0, "strategy_selected": False,
              "market_data_qualified": False, "paper_evaluation_available": False, "orders_available": False,
              "real_money_execution_available": False}
    daily.write_new(root / "run-report.json", report)
    return report
