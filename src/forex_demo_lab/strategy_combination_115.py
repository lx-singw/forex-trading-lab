"""Predetermined single-account agreement on invented quotes. No broker API."""
from collections import Counter
from copy import deepcopy
from dataclasses import asdict
from datetime import datetime
import json
import math

from .model import Config
from .strategies import Decision
from .strategy_experiment_028 import decision
from .strategy_adapter_114 import (
    DEPENDENCIES as PREDECESSOR_DEPENDENCIES, WARMUP_HOURS, _CandidateTicks,
    load_fixture, inspect_capture, scenarios, write_new,
)
from .shadow_engine_113 import (
    ROOT, MAX_BYTES, MAX_EVENTS, MIN_MS, MAX_MS, Replay as EventReplay,
    _canonical, _digest, _integer, _json, _read,
)

MEMBERS = ("C00", "C05", "C06")
RULES = ("UNANIMOUS", "AGREE2", "CASH")
VERSION = "single_account_combination_115_v1"
DEPENDENCIES = (*PREDECESSOR_DEPENDENCIES,
                "src/forex_demo_lab/strategy_combination_115.py",
                "src/forex_demo_lab/combination_fixture_115.py",
                "scripts/strategy-combination-115.py", "tests/test_strategy_combination_115.py",
                "docs/STRATEGY-COMBINATION-115-PROTOCOL.md")


def rule_definitions():
    return {"UNANIMOUS": {"minimum_support": 3, "reject_opposition": True},
            "AGREE2": {"minimum_support": 2, "reject_opposition": True},
            "CASH": {"always_abstain": True},
            "stop_distance": "largest_positive_supporting_vote", "weights": None}


def _vote(value):
    if (type(value) is not Decision or type(value.side) is not int or value.side not in (-1, 0, 1)
            or type(value.stop_distance) not in (int, float) or type(value.reason) is not str
            or type(value.features) is not dict):
        raise ValueError("invalid_member_vote")
    try:
        valid = math.isfinite(value.stop_distance) and value.stop_distance >= 0
    except OverflowError:
        valid = False
    if not valid or (value.side and value.stop_distance <= 0):
        raise ValueError("invalid_member_stop")
    _canonical(asdict(value))


def arbitrate(rule, votes):
    if rule not in RULES or type(votes) is not dict or set(votes) != set(MEMBERS):
        raise ValueError("rule_or_members")
    for value in votes.values():
        _vote(value)
    long = [m for m in MEMBERS if votes[m].side == 1]
    short = [m for m in MEMBERS if votes[m].side == -1]
    supporters, side, distance = [], 0, 0.0
    if rule == "CASH":
        reason = "cash_reference"
    elif long and short:
        reason = "conflicting_votes"
    elif max(len(long), len(short)) < (3 if rule == "UNANIMOUS" else 2):
        reason = "insufficient_agreement"
    else:
        supporters = long or short
        side = votes[supporters[0]].side
        distance = max(votes[m].stop_distance for m in supporters)
        reason = "unanimous_agreement" if rule == "UNANIMOUS" else "two_or_more_agree"
    return Decision(side, distance, reason, {"rule": rule, "votes": {m: asdict(votes[m]) for m in MEMBERS},
                                            "supporters": supporters})


def _trace(value, rule):
    fields = {"hour_msc", "history_size", "last_closed_hour", "side", "stop_distance", "reason", "features"}
    if type(value) is not dict or set(value) != fields:
        raise ValueError("arbitration_trace_fields")
    hour = _integer(value["hour_msc"], MIN_MS, MAX_MS)
    _integer(value["history_size"], WARMUP_HOURS, WARMUP_HOURS)
    if hour % 3600000 or type(value["last_closed_hour"]) is not str:
        raise ValueError("arbitration_history")
    prior = datetime.fromisoformat(value["last_closed_hour"])
    if prior.tzinfo is None or prior.utcoffset().total_seconds() != 0 or int(prior.timestamp() * 1000) >= hour:
        raise ValueError("arbitration_history")
    f = value["features"]
    if type(f) is not dict or set(f) != {"rule", "votes", "supporters"} or f["rule"] != rule:
        raise ValueError("arbitration_features")
    if type(f["votes"]) is not dict or set(f["votes"]) != set(MEMBERS):
        raise ValueError("arbitration_members")
    votes = {}
    for member, row in f["votes"].items():
        if type(row) is not dict or set(row) != {"side", "stop_distance", "reason", "features"}:
            raise ValueError("arbitration_vote_fields")
        votes[member] = Decision(**row)
    expected = arbitrate(rule, votes)
    actual = Decision(value["side"], value["stop_distance"], value["reason"], f)
    _vote(actual)
    if _canonical(asdict(actual)) != _canonical(asdict(expected)):
        raise ValueError("arbitration_semantics")
    return expected


def source_bindings():
    return {name: _digest(_read(ROOT / name, 1024 * 1024)) for name in DEPENDENCIES}


def _manifest(fixture, digest):
    if _json(_read(ROOT / "config/baseline.json", 65536)) != asdict(Config()):
        raise ValueError("frozen_baseline_changed")
    return {"schema": "combination115_frozen_invented_v1", "kind": "invented_fixture",
            "fixture_format": fixture["format"], "fixture_sha256": digest,
            "case": fixture["case"], "events": len(fixture["events"]),
            "development_start_msc": fixture["development_start_msc"],
            "validation_start_msc": fixture["validation_start_msc"], "clock": fixture["clock"],
            "members": list(MEMBERS), "rules": list(RULES), "definitions": rule_definitions(),
            "common_warmup_hours": WARMUP_HOURS, "account_model": "single_account_per_rule",
            "initial_equity_per_account": Config().initial_equity, "cash_interest": 0.0,
            "scenarios": scenarios(), "sources": source_bindings()}


def freeze_fixture(fixture_path, manifest_path):
    fixture, digest = load_fixture(fixture_path)
    manifest = _manifest(fixture, digest)
    write_new(manifest_path, manifest)
    return manifest


def _bound_fixture(fixture_path, manifest_path):
    fixture, digest = load_fixture(fixture_path)
    raw = _read(manifest_path, 65536)
    manifest = _json(raw)
    if manifest != _manifest(fixture, digest):
        raise ValueError("frozen_combination_fixture_rules_config_or_code_changed")
    return fixture, manifest, _digest(raw)


class _CombinationTicks(_CandidateTicks):
    """Reuse 114 risk/fills/costs; apply one frozen rule to closed-bar member votes."""
    def __init__(self, config, rule="UNANIMOUS"):
        if rule not in RULES:
            raise ValueError("rule")
        super().__init__(config, "C00")
        self.rule = rule
        self.combination_version = VERSION
        self.entry_arbitration = None
        self.trade_arbitration = []
        self.entry_checks = []

    def _decision(self):
        hour = self.current["hour"] * 3600000
        if len(self.history) < WARMUP_HOURS or hour < self.evaluation_start_msc:
            return 0, 0.0
        value = arbitrate(self.rule, {m: decision(m, self.history, self.config) for m in MEMBERS})
        self.decisions.append({"hour_msc": hour, "history_size": len(self.history),
                               "last_closed_hour": self.history[-1].time.isoformat(), **asdict(value)})
        return value.side, value.stop_distance

    def _open(self, bar, side, distance):
        if self.rule == "CASH":
            return
        if not self.decisions:
            raise ValueError("missing_entry_arbitration")
        admission = self.decisions[-1]
        selected = _trace(admission, self.rule)
        if (not selected.side or side != selected.side or distance != selected.stop_distance
                or admission["hour_msc"] != int(bar.time.timestamp() * 1000)):
            raise ValueError("entry_arbitration_mismatch")
        had_position, balance = self.position is not None, self.balance
        super()._open(bar, side, distance)
        opened = not had_position and self.position is not None
        risk = (self.position.lots * ((distance + self.config.slippage_pips * .0001)
                                      * self.config.contract_size + self.config.commission_per_lot_round_turn)
                if opened else 0.0)
        self.entry_checks.append({"sequence": self._quote["sequence"], "hour_msc": admission["hour_msc"],
                                  "opened": opened, "estimated_risk": risk,
                                  "risk_budget": max(balance, 0.0) * self.config.risk_fraction,
                                  "reason": "opened" if opened else "inherited_risk_or_size_guard"})
        if opened:
            self.entry_arbitration = deepcopy(admission)

    def _close(self, bar, exit_price, reason):
        if self.entry_arbitration is None:
            raise ValueError("missing_position_arbitration")
        admission = deepcopy(self.entry_arbitration)
        entry = self.pending_entry_sequence
        super()._close(bar, exit_price, reason)
        self.trade_arbitration.append({"trade_index": len(self.trades) - 1,
                                       "entry_sequence": entry, "entry_decision": admission})
        self.entry_arbitration = None

    @classmethod
    def restore(cls, value, config, *, rule, evaluation_start_msc):
        result = super().restore(value, config, candidate="C00", evaluation_start_msc=evaluation_start_msc)
        if result.rule != rule or result.combination_version != VERSION:
            raise ValueError("checkpoint_combination_rule")
        if (type(result.decisions) is not list or type(result.entry_checks) is not list
                or type(result.trade_arbitration) is not list or type(result.trades) is not list
                or type(result.fill_lineage) is not list):
            raise ValueError("checkpoint_arbitration_types")
        for row in result.decisions:
            _trace(row, rule)
        if (len(result.trade_arbitration) != len(result.trades)
                or len(result.fill_lineage) != len(result.trades)
                or (result.position is None) != (result.entry_arbitration is None)):
            raise ValueError("checkpoint_arbitration_position")
        if result.entry_arbitration is not None and not _trace(result.entry_arbitration, rule).side:
            raise ValueError("checkpoint_abstaining_position")
        opened = 0
        for check in result.entry_checks:
            if (type(check) is not dict or set(check) != {"sequence", "hour_msc", "opened", "estimated_risk", "risk_budget", "reason"}
                    or type(check["opened"]) is not bool
                    or check["reason"] != ("opened" if check["opened"] else "inherited_risk_or_size_guard")):
                raise ValueError("checkpoint_entry_check")
            _integer(check["sequence"], 0, MAX_EVENTS - 1)
            _integer(check["hour_msc"], evaluation_start_msc, MAX_MS)
            for key in ("estimated_risk", "risk_budget"):
                if type(check[key]) not in (int, float) or not math.isfinite(check[key]) or check[key] < 0:
                    raise ValueError("checkpoint_entry_risk")
            if check["estimated_risk"] > check["risk_budget"] + 1e-9:
                raise ValueError("checkpoint_entry_risk")
            if not check["opened"] and check["estimated_risk"] != 0:
                raise ValueError("checkpoint_entry_risk")
            opened += int(check["opened"])
        if opened != len(result.trades) + int(result.position is not None):
            raise ValueError("checkpoint_entry_count")
        for i, row in enumerate(result.trade_arbitration):
            if (type(row) is not dict or set(row) != {"trade_index", "entry_sequence", "entry_decision"}
                    or type(row["trade_index"]) is not int or row["trade_index"] != i
                    or type(row["entry_sequence"]) is not int
                    or row["entry_sequence"] != result.fill_lineage[i]["entry_sequence"]
                    or not _trace(row["entry_decision"], rule).side):
                raise ValueError("checkpoint_trade_arbitration")
        if rule == "CASH" and (result.position is not None or result.trades or result.entry_checks):
            raise ValueError("checkpoint_cash_position")
        return result


class Replay(EventReplay):
    def __init__(self, fixture_path, manifest_path, scenario="base", partition="development", rule="UNANIMOUS"):
        fixture, manifest, binding = _bound_fixture(fixture_path, manifest_path)
        if scenario not in ("base", "adverse") or partition not in ("development", "validation") or rule not in RULES:
            raise ValueError("scenario_partition_or_rule")
        self._fixture, self._manifest, self.binding = fixture, manifest, binding
        self.scenario, self.partition, self.rule = scenario, partition, rule
        self.start = fixture[partition + "_start_msc"]
        self._events = [dict(e) for e in fixture["events"] if partition == "validation"
                       or e["receipt_msc"] < fixture["validation_start_msc"]]
        self.next_sequence, self.repeats = 0, 0
        self.sim = _CombinationTicks(Config(**manifest["scenarios"][scenario]["config"]), rule)
        self.sim.evaluation_start_msc = self.start

    def checkpoint(self):
        payload = {"schema": "combination115_checkpoint_v1", "manifest_sha256": self.binding,
                   "fixture_sha256": self._manifest["fixture_sha256"], "rule": self.rule,
                   "scenario": self.scenario, "partition": self.partition,
                   "next_sequence": self.next_sequence, "repeats": self.repeats,
                   "simulator": self.sim.checkpoint()}
        return json.dumps({"payload": payload, "sha256": _digest(_canonical(payload))}, sort_keys=True)

    @classmethod
    def restore(cls, fixture_path, manifest_path, checkpoint, scenario="base", partition="development", rule="UNANIMOUS"):
        if type(checkpoint) is not str or len(checkpoint.encode()) > MAX_BYTES:
            raise ValueError("checkpoint_size")
        result = cls(fixture_path, manifest_path, scenario, partition, rule)
        value = _json(checkpoint)
        if type(value) is not dict or set(value) != {"payload", "sha256"}:
            raise ValueError("checkpoint_envelope")
        p = value["payload"]
        fields = {"schema", "manifest_sha256", "fixture_sha256", "rule", "scenario",
                  "partition", "next_sequence", "repeats", "simulator"}
        if (type(p) is not dict or set(p) != fields or value["sha256"] != _digest(_canonical(p))
                or p["schema"] != "combination115_checkpoint_v1" or p["manifest_sha256"] != result.binding
                or p["fixture_sha256"] != result._manifest["fixture_sha256"]
                or p["rule"] != rule or p["scenario"] != scenario or p["partition"] != partition):
            raise ValueError("checkpoint_binding")
        cursor = _integer(p["next_sequence"], 0, len(result._events))
        repeats = _integer(p["repeats"], 0, max(0, cursor - 1))
        try:
            sim = _CombinationTicks.restore(p["simulator"], result.sim.config,
                                            rule=rule, evaluation_start_msc=result.start)
        except (KeyError, TypeError, OverflowError, AttributeError, IndexError) as exc:
            raise ValueError("checkpoint_simulator") from exc
        expected = result._tick(result._events[cursor - 1]) if cursor else None
        expected_repeats = sum(a["source_msc"] == b["source_msc"]
                               for a, b in zip(result._events[:cursor], result._events[1:cursor]))
        if (type(sim.cost_audit) is not list or type(sim.evaluation_start_msc) is not int
                or _canonical(sim.last_tick) != _canonical(expected) or _canonical(sim._quote) != _canonical(expected)
                or repeats != expected_repeats or type(sim.finished) is not bool
                or (sim.finished and cursor != len(result._events)) or len(sim.cost_audit) != len(sim.trades)
                or (sim.position is None) != (sim._entry_audit is None)
                or (sim.position is None) != (sim.pending_entry_sequence is None)):
            raise ValueError("checkpoint_cursor_or_state")
        if sim.pending_entry_sequence is not None:
            _integer(sim.pending_entry_sequence, 0, cursor - 1)
        for i, row in enumerate(sim.fill_lineage):
            if (type(row) is not dict or set(row) != {"trade_index", "entry_sequence", "exit_sequence"}
                    or type(row["trade_index"]) is not int or row["trade_index"] != i):
                raise ValueError("checkpoint_fill_lineage")
            entry = _integer(row["entry_sequence"], 0, cursor - 1)
            _integer(row["exit_sequence"], entry, cursor - 1)
        if any(check["sequence"] >= cursor for check in sim.entry_checks):
            raise ValueError("checkpoint_entry_cursor")
        result.next_sequence, result.repeats, result.sim = cursor, repeats, sim
        return result

    def report(self):
        result = deepcopy(super().report())
        result.update(schema="combination115_invented_result_v1", rule=self.rule, members=list(MEMBERS),
                      common_warmup_hours=WARMUP_HOURS, account_model="single_account_per_rule",
                      initial_equity_per_account=self.sim.config.initial_equity,
                      fill_lineage=deepcopy(self.sim.fill_lineage),
                      trade_arbitration=deepcopy(self.sim.trade_arbitration),
                      entry_checks=deepcopy(self.sim.entry_checks),
                      arbitration_summary=dict(Counter(d["reason"] for d in self.sim.decisions)))
        return result


def evaluate_fixture(fixture_path, manifest_path, output_path):
    results = [Replay(fixture_path, manifest_path, s, p, rule).run()
               for s in ("base", "adverse") for p in ("development", "validation") for rule in RULES]
    report = {"schema": "combination115_demonstration_v1", "kind": "invented_software_check",
              "results": results, "rules": list(RULES), "members": list(MEMBERS),
              "selected_strategy": None, "aggregate_portfolio_result": None, "combination_weights": None,
              "market_validation": False, "market_data_qualified": False,
              "paper_evaluation_available": False, "orders_available": False,
              "real_money_execution_available": False}
    write_new(output_path, report)
    return report
