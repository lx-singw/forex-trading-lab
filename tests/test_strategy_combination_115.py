from copy import deepcopy
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
import hashlib
from itertools import product
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from forex_demo_lab.model import Bar, Config
from forex_demo_lab.strategies import Decision
from forex_demo_lab.strategy_experiment_028 import decision
from forex_demo_lab.strategy_adapter_114 import _CandidateTicks, Replay as OldReplay, freeze_fixture as old_freeze
from forex_demo_lab.strategy_fixture_114 import START, fixture as old_fixture
from forex_demo_lab.strategy_combination_115 import (
    MEMBERS, RULES, Replay, VERSION, _CombinationTicks, _canonical, _trace, arbitrate,
    evaluate_fixture, freeze_fixture, inspect_capture, rule_definitions, scenarios, write_new,
)
from forex_demo_lab.combination_fixture_115 import CASES, fixture
from test_forward_capture_111 import encode, payloads
from test_private_recorder_107 import complete as complete107, encode as encode107

ROOT = Path(__file__).resolve().parents[1]
BASE = datetime.fromtimestamp(START / 1000, timezone.utc)


def votes(sides=(1, 1, 1), distances=(.001, .002, .003)):
    return {m: Decision(side, distance, "test_vote", {})
            for m, side, distance in zip(MEMBERS, sides, distances)}


def reference(rule, values):
    active = [v for v in values.values() if v.side]
    directions = {v.side for v in active}
    required = {"UNANIMOUS": 3, "AGREE2": 2, "CASH": 4}[rule]
    if len(directions) != 1 or len(active) < required:
        return 0, 0.0
    return active[0].side, max(v.stop_distance for v in active)


class ReferenceTicks(_CandidateTicks):
    """Independent rule calculation on the retained 114 single-position engine."""
    def __init__(self, config, rule):
        super().__init__(config)
        self.rule = rule

    def _decision(self):
        hour = self.current["hour"] * 3600000
        if len(self.history) < 201 or hour < self.evaluation_start_msc:
            return 0, 0.0
        values = {m: decision(m, self.history, self.config) for m in MEMBERS}
        side, distance = reference(self.rule, values)
        self.decisions.append({"hour_msc": hour, "side": side, "stop_distance": distance,
                               "votes": {m: asdict(v) for m, v in values.items()}})
        return side, distance


class Combination115Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.input, self.manifest = self.make(fixture())

    def make(self, value, name="fixture"):
        path, manifest = self.root / (name + ".json"), self.root / (name + "-frozen.json")
        write_new(path, value); freeze_fixture(path, manifest)
        return path, manifest

    def replay(self, **kw):
        return Replay(self.input, self.manifest, **kw)

    def prefix(self, obj, count):
        for event in obj.events[:count]:
            obj.step(event)

    def rewrite(self, cp, change):
        envelope = json.loads(cp)
        change(envelope["payload"])
        envelope["sha256"] = hashlib.sha256(_canonical(envelope["payload"])).hexdigest()
        return json.dumps(envelope)

    def alter_sim(self, cp, change):
        def edit(payload):
            inner = json.loads(payload["simulator"])
            change(inner["payload"]["state"])
            body = json.dumps(inner["payload"], sort_keys=True, allow_nan=False)
            inner["sha256"] = hashlib.sha256(body.encode()).hexdigest()
            payload["simulator"] = json.dumps(inner)
        return self.rewrite(cp, edit)

    def manual(self, side=1, spread=1, rule="AGREE2", distance=.001, paused=False):
        obj = _CombinationTicks(Config(), rule)
        obj.history = [Bar(BASE + timedelta(hours=i), 1.1, 1.1, 1.1, 1.1, 1) for i in range(201)]
        obj.current = {"hour": START // 3600000 + 201}
        instant = BASE + timedelta(hours=201)
        obj._quote = {"sequence": 0, "time_msc": START + 201 * 3600000,
                      "bid": 1.1, "ask": 1.1 + spread * .0001}
        values = votes((side, side, side), (distance / 2, distance, distance / 2))
        with patch("forex_demo_lab.strategy_combination_115.decision", side_effect=lambda m, *_: values[m]):
            obj._decision()
        obj.paused = paused
        obj._open(Bar(instant, 1.1, 1.1, 1.1, 1.1, spread), side, distance)
        obj.current = None
        return obj

    def test_fixed_manifest_members_rules_and_unchanged_costs(self):
        m = json.loads(self.manifest.read_bytes())
        self.assertEqual(MEMBERS, ("C00", "C05", "C06"))
        self.assertEqual(RULES, ("UNANIMOUS", "AGREE2", "CASH"))
        self.assertEqual(m["definitions"], rule_definitions())
        self.assertEqual(m["scenarios"], scenarios())
        self.assertEqual(m["initial_equity_per_account"], 10000)
        self.assertEqual(m["common_warmup_hours"], 201)
        self.assertEqual(m["account_model"], "single_account_per_rule")

    def test_all27_direction_combinations_obey_predeclared_rules(self):
        for sides in product((-1, 0, 1), repeat=3):
            values = votes(sides)
            for rule in RULES:
                with self.subTest(sides=sides, rule=rule):
                    result = arbitrate(rule, values)
                    self.assertEqual((result.side, result.stop_distance), reference(rule, values))
                    self.assertEqual(result.features["rule"], rule)
                    self.assertEqual(result.features["votes"], {m: asdict(v) for m, v in values.items()})
                    self.assertEqual(result.features["supporters"],
                                     [m for m in MEMBERS if result.side and values[m].side == result.side])
                    if rule != "CASH" and 1 in sides and -1 in sides:
                        self.assertEqual(result.reason, "conflicting_votes")

    def test_two_votes_never_override_an_opposing_vote(self):
        for sides in ((1, 1, -1), (-1, -1, 1)):
            for rule in RULES[:2]:
                result = arbitrate(rule, votes(sides))
                self.assertEqual(result.side, 0)
                self.assertEqual(result.stop_distance, 0)
                self.assertEqual(result.reason, "conflicting_votes")

    def test_maximum_supporting_stop_ignores_abstaining_distance(self):
        for side in (1, -1):
            values = votes((side, side, 0), (.001, .002, 5))
            result = arbitrate("AGREE2", values)
            self.assertEqual(result.stop_distance, .002)
            self.assertEqual(result.features["supporters"], ["C00", "C05"])
            self.assertEqual(arbitrate("UNANIMOUS", values).side, 0)

    def test_invalid_member_rule_numeric_and_stop_inputs_reject(self):
        for values in ({}, {**votes(), "C07": Decision(1, .001, "bad", {})},
                       {m: v for m, v in votes().items() if m != "C05"}):
            with self.assertRaises(ValueError): arbitrate("AGREE2", values)
        with self.assertRaises(ValueError): arbitrate("majority", votes())
        for bad in (Decision(True, .001, "bad", {}), Decision(2, .001, "bad", {}),
                    Decision(1, 0, "bad", {}), Decision(0, -1, "bad", {}),
                    Decision(1, True, "bad", {}), Decision(1, float("nan"), "bad", {}),
                    Decision(1, float("inf"), "bad", {}), Decision(1, 10**400, "bad", {}),
                    Decision(1, .001, 4, {}), Decision(1, .001, "bad", [])):
            for rule in RULES:
                with self.assertRaises(ValueError): arbitrate(rule, {**votes(), "C00": bad})

    def test_arbitration_is_nonmutating_and_views_are_independent(self):
        values = votes(); values["C00"].features["detail"] = [1]
        before = deepcopy(values)
        result = arbitrate("AGREE2", values)
        result.features["votes"]["C00"]["features"]["detail"].append(2)
        self.assertEqual(values, before)
        definitions = rule_definitions(); definitions["AGREE2"]["minimum_support"] = 1
        self.assertEqual(rule_definitions()["AGREE2"]["minimum_support"], 2)

    def test_control_fixture_prices_and_events_are_exact114(self):
        for case in CASES[:3]:
            self.assertEqual(fixture(case), old_fixture(case))

    def actual_history(self, case, block=0):
        events = fixture(case)["events"][block * 1152:block * 1152 + 804]
        history = []
        for i in range(201):
            group = events[i * 4:i * 4 + 4]
            prices = [e["bid"] for e in group]
            history.append(Bar(BASE + timedelta(hours=block * 288 + i), prices[0], max(prices), min(prices), prices[-1], 1))
        return history

    def test_actual_partial_agreement_long_and_short_votes(self):
        for block, side in ((0, 1), (1, -1)):
            history = self.actual_history("partial_agreement", block)
            values = {m: decision(m, history, Config()) for m in MEMBERS}
            self.assertEqual(tuple(v.side for v in values.values()), (side, side, 0))
            self.assertEqual(arbitrate("UNANIMOUS", values).side, 0)
            self.assertEqual(arbitrate("AGREE2", values).side, side)

    def test_actual_opposition_long_and_short_votes_abstain(self):
        for block, side in ((0, 1), (1, -1)):
            values = {m: decision(m, self.actual_history("conflicting_votes", block), Config()) for m in MEMBERS}
            self.assertEqual(tuple(v.side for v in values.values()), (-side, side, side))
            for rule in RULES[:2]:
                self.assertEqual(arbitrate(rule, values).reason, "conflicting_votes")
                self.assertEqual(arbitrate(rule, values).side, 0)

    def test_replay_records_actual_partial_and_conflicting_entry_votes(self):
        for case in CASES[3:]:
            f, m = self.make(fixture(case), case)
            for rule in RULES[:2]:
                obj = Replay(f, m, rule=rule)
                self.prefix(obj, 805)
                row = obj.sim.decisions[0]
                self.assertEqual(row["hour_msc"], START + 201 * 3600000)
                self.assertEqual(row["side"], 1 if case == "partial_agreement" and rule == "AGREE2" else 0)
                self.assertEqual(obj.sim.position is not None, bool(row["side"]))

    def test_all60_results_reported_with_cost_and_risk_reconciliation(self):
        seen = set()
        for case in CASES:
            f, m = (self.input, self.manifest) if case == "continuation" else self.make(fixture(case), case)
            report = evaluate_fixture(f, m, self.root / (case + "-report.json"))
            self.assertEqual(len(report["results"]), 12)
            self.assertIsNone(report["selected_strategy"])
            self.assertIsNone(report["aggregate_portfolio_result"])
            self.assertIsNone(report["combination_weights"])
            for row in report["results"]:
                seen.add((case, row["rule"], row["scenario"], row["partition"]))
                costs = row["cost_totals"]
                self.assertAlmostEqual(costs["reference_gross"] - sum(costs[k] for k in
                    ("spread", "slippage", "commission", "financing_debit")), costs["net"])
                self.assertAlmostEqual(costs["net"], row["metrics"]["net_pnl"])
                self.assertEqual(len(row["trades"]), len(row["trade_arbitration"]))
                self.assertEqual(len(row["trades"]), len(row["fill_lineage"]))
                self.assertEqual(row["initial_equity_per_account"], 10000)
                for check in row["entry_checks"]:
                    self.assertLessEqual(check["estimated_risk"], check["risk_budget"] + 1e-9)
                for trade, audit, admission in zip(row["trades"], row["cost_audit"], row["trade_arbitration"]):
                    rate = 7 if row["scenario"] == "base" else 10
                    self.assertAlmostEqual(audit["commission"], trade["lots"] * rate)
                    self.assertEqual(_trace(admission["entry_decision"], row["rule"]).side, trade["side"])
                for key in ("market_validation", "paper_evaluation_available", "market_data_qualified",
                            "orders_available", "real_money_execution_available"):
                    self.assertFalse(row[key])
        self.assertEqual(len(seen), 60)

    def test_independent_reference_matches_prefix_fills_and_final_metrics(self):
        for case in CASES:
            f, m = (self.input, self.manifest) if case == "continuation" else self.make(fixture(case), case)
            for rule in RULES[:2]:
                for scenario in ("base", "adverse"):
                    for partition in ("development", "validation"):
                        with self.subTest(case=case, rule=rule, scenario=scenario, partition=partition):
                            obj = Replay(f, m, scenario, partition, rule)
                            direct = ReferenceTicks(obj.sim.config, rule)
                            direct.evaluation_start_msc = obj.start
                            for event in obj.events:
                                obj.step(event); direct.step_tick(obj._tick(event))
                                if event["sequence"] in (0, 803, 804, 808, 816, 908, 1151, 1956, 2060):
                                    self.assertEqual(obj.sim.position, direct.position)
                                    self.assertEqual(obj.sim.trades, direct.trades)
                                    self.assertEqual(obj.sim.metrics(), direct.metrics())
                                    projected = [{"hour_msc": d["hour_msc"], "side": d["side"],
                                                  "stop_distance": d["stop_distance"], "votes": d["features"]["votes"]}
                                                 for d in obj.sim.decisions]
                                    self.assertEqual(projected, direct.decisions)
                            obj.finish(); direct.finish()
                            self.assertEqual(obj.report()["metrics"], direct.metrics())
                            self.assertEqual(obj.report()["trades"], direct.trades)
                            self.assertEqual(obj.report()["cost_audit"], direct.cost_audit)
                            self.assertEqual(obj.report()["fill_lineage"], direct.fill_lineage)

    def test_common_warmup_and_fresh_validation(self):
        for rule in RULES:
            obj = self.replay(rule=rule)
            self.prefix(obj, 804)
            self.assertFalse(obj.sim.decisions)
            self.assertIsNone(obj.sim.position)
            obj.step(obj.events[804])
            self.assertEqual(obj.sim.decisions[0]["history_size"], 201)
            self.assertEqual(obj.sim.decisions[0]["last_closed_hour"], (BASE + timedelta(hours=200)).isoformat())
            val = self.replay(rule=rule, partition="validation")
            self.prefix(val, 1152)
            self.assertEqual(val.sim.balance, 10000)
            self.assertFalse(val.sim.decisions)
            self.assertFalse(val.sim.trades)
            self.assertIsNone(val.sim.position)

    def test_future_suffix_changes_cannot_change_prior_votes_or_state(self):
        f, m = self.make(fixture("reversal"), "reversal")
        for rule in RULES:
            a, b = self.replay(rule=rule), Replay(f, m, rule=rule)
            self.prefix(a, 816); self.prefix(b, 816)
            self.assertEqual(a.sim.checkpoint(), b.sim.checkpoint())
            earlier = deepcopy(a.sim.decisions)
            a.run(); b.run()
            boundary = START + 204 * 3600000
            for obj in (a, b):
                self.assertEqual(earlier, [d for d in obj.sim.decisions if d["hour_msc"] < boundary])

    def test_missing_hour_discards_signal_without_imputation(self):
        value = fixture()
        value["events"] = [e for e in value["events"] if e["receipt_msc"] // 3600000 != START // 3600000 + 201]
        for i, e in enumerate(value["events"]): e["sequence"] = i
        f, m = self.make(value, "gap")
        for rule in RULES:
            obj = Replay(f, m, rule=rule); self.prefix(obj, 805)
            self.assertFalse(obj.sim.decisions)
            self.assertIsNone(obj.sim.position)
            self.assertEqual(obj.sim.history[-1].time, BASE + timedelta(hours=200))

    def test_cash_and_flat_have_no_positions_costs_or_interest(self):
        f, m = self.make(fixture("flat"), "flat")
        for rule in RULES:
            row = Replay(f, m, rule=rule).run()
            self.assertEqual(row["metrics"]["net_pnl"], 0)
            self.assertFalse(row["trades"])
            self.assertFalse(row["entry_checks"])
        for scenario in ("base", "adverse"):
            for partition in ("development", "validation"):
                row = self.replay(rule="CASH", scenario=scenario, partition=partition).run()
                self.assertEqual(row["metrics"]["net_pnl"], 0)
                self.assertEqual(row["metrics"]["max_tick_drawdown"], 0)
                self.assertIsNone(row["metrics"]["win_rate"])
                self.assertTrue(all(v == 0 for v in row["cost_totals"].values()))
                self.assertTrue(all(d["reason"] == "cash_reference" for d in row["decisions"]))
        self.assertIsNone(self.manual(rule="CASH").position)

    def test_single_position_maximum_stop_and_one_risk_budget(self):
        for side in (1, -1):
            obj = self.manual(side=side)
            p = obj.position
            self.assertIsNotNone(p)
            self.assertAlmostEqual(abs(p.entry - p.stop), .001)
            check = obj.entry_checks[0]
            self.assertEqual(check["risk_budget"], 25)
            self.assertLessEqual(check["estimated_risk"], 25)
            self.assertAlmostEqual(round(p.lots / .01) * .01, p.lots)
            obj._open(Bar(BASE + timedelta(hours=201), 1.1, 1.1, 1.1, 1.1, 1), side, .001)
            self.assertIs(obj.position, p)
            self.assertFalse(obj.entry_checks[-1]["opened"])
            self.assertEqual(obj.entry_arbitration["features"]["supporters"], list(MEMBERS))

    def test_spread_and_paused_account_reject_entry(self):
        for obj in (self.manual(spread=3), self.manual(paused=True)):
            self.assertIsNone(obj.position)
            self.assertFalse(obj.entry_checks[0]["opened"])
            self.assertEqual(obj.entry_checks[0]["estimated_risk"], 0)
            self.assertEqual(obj.entry_checks[0]["reason"], "inherited_risk_or_size_guard")

    def test_entry_cannot_bypass_selected_side_stop_or_hour(self):
        obj = self.manual()
        for side, distance, instant in ((-1, .001, BASE + timedelta(hours=201)),
                                        (1, .0001, BASE + timedelta(hours=201)),
                                        (1, .001, BASE + timedelta(hours=202))):
            with self.assertRaises(ValueError):
                obj._open(Bar(instant, 1.1, 1.1, 1.1, 1.1, 1), side, distance)
        self.assertEqual(len(obj.entry_checks), 1)

    def test_gap_stop_can_exceed_entry_budget_and_pause_without_recovery_sizing(self):
        for side in (1, -1):
            obj = self.manual(side=side)
            price = 1.0 if side == 1 else 1.2
            obj.step_tick({"sequence": 0, "time_msc": START + 201 * 3600000, "bid": price, "ask": price + .0001})
            self.assertEqual(obj.trades[0]["reason"], "stop_tick")
            self.assertLess(obj.trades[0]["net_pnl"], -25)
            self.assertTrue(obj.paused)
            obj._open(Bar(BASE + timedelta(hours=201), price, price, price, price, 1), side, .001)
            self.assertIsNone(obj.position)
            self.assertFalse(obj.entry_checks[-1]["opened"])
            self.assertEqual(len(obj.trade_arbitration), 1)

    def test_target_overshoot_keeps_corrected_fill_equity(self):
        for side in (1, -1):
            obj = self.manual(side=side)
            target = obj.position.target
            price = 1.2 if side == 1 else 1.0
            obj.step_tick({"sequence": 0, "time_msc": START + 201 * 3600000, "bid": price, "ask": price + .0001})
            self.assertEqual(obj.trades[0]["exit"], target)
            self.assertAlmostEqual(obj.peak_tick_equity, obj.balance)
            self.assertAlmostEqual(obj.max_tick_drawdown, 0)
            self.assertEqual(obj.execution_metric_version, "executable_fill_equity_019b_v1")

    def test_later_opposition_does_not_remove_held_position_exit_protection(self):
        obj = self.manual()
        stop, target, admission = obj.position.stop, obj.position.target, deepcopy(obj.entry_arbitration)
        obj.current = {"hour": START // 3600000 + 202}
        opposed = votes((1, 1, -1))
        with patch("forex_demo_lab.strategy_combination_115.decision", side_effect=lambda m, *_: opposed[m]):
            self.assertEqual(obj._decision(), (0, 0.0))
        self.assertEqual((obj.position.stop, obj.position.target), (stop, target))
        self.assertEqual(obj.entry_arbitration, admission)
        obj.current = None
        obj.step_tick({"sequence": 0, "time_msc": START + 202 * 3600000, "bid": stop - .001, "ask": stop - .0009})
        self.assertEqual(obj.trades[0]["reason"], "stop_tick")
        self.assertEqual(obj.trade_arbitration[0]["entry_decision"], admission)

    def test_restart_at_warmup_positions_and_after_financing_matches_full_result(self):
        for rule in RULES:
            for scenario in ("base", "adverse"):
                for partition in ("development", "validation"):
                    expected = self.replay(rule=rule, scenario=scenario, partition=partition).run()
                    cursors = (0, 809, 909) if partition == "development" else (1152, 1961, 2061)
                    for cursor in cursors:
                        obj = self.replay(rule=rule, scenario=scenario, partition=partition)
                        self.prefix(obj, cursor)
                        restored = Replay.restore(self.input, self.manifest, obj.checkpoint(), scenario, partition, rule)
                        if cursor: self.assertFalse(restored.step(restored.events[cursor - 1]))
                        self.assertEqual(restored.run(), expected)
                        ended = Replay.restore(self.input, self.manifest, restored.checkpoint(), scenario, partition, rule)
                        self.assertEqual(ended.run(), expected)

    def test_restart_after_reversal_losses_keeps_pause_costs_and_votes(self):
        f, m = self.make(fixture("reversal"), "reversal")
        for rule in RULES[:2]:
            obj = Replay(f, m, rule=rule)
            self.prefix(obj, 910)
            restored = Replay.restore(f, m, obj.checkpoint(), rule=rule)
            self.assertEqual(restored.sim.checkpoint(), obj.sim.checkpoint())
            self.assertEqual(restored.run(), obj.run())
            if obj.sim.trades:
                self.assertTrue(any(t["net_pnl"] < 0 for t in obj.sim.trades))

    def test_cross_rule_scenario_partition_and_legacy_checkpoints_reject(self):
        obj = self.replay(rule="AGREE2"); self.prefix(obj, 809)
        for kw in ({"rule": "UNANIMOUS"}, {"rule": "CASH"}, {"rule": "AGREE2", "scenario": "adverse"},
                   {"rule": "AGREE2", "partition": "validation"}):
            with self.assertRaises(ValueError): Replay.restore(self.input, self.manifest, obj.checkpoint(), **kw)
        old_manifest = self.root / "old-frozen.json"; old_freeze(self.input, old_manifest)
        with self.assertRaises(ValueError): Replay(self.input, old_manifest)
        with self.assertRaises(ValueError): OldReplay(self.input, self.manifest)
        old = OldReplay(self.input, old_manifest)
        with self.assertRaises(ValueError): Replay.restore(self.input, self.manifest, old.checkpoint())

    def test_inner_rule_members_version_and_metric_are_checked(self):
        obj = self.replay(rule="AGREE2"); self.prefix(obj, 809)
        for key, value in (("rule", "UNANIMOUS"), ("combination_version", "old"),
                           ("execution_metric_version", "legacy"), ("candidate", "C05"),
                           ("evaluation_start_msc", START)):
            cp = self.alter_sim(obj.checkpoint(), lambda s, k=key, v=value: s.update({k: v}))
            with self.assertRaises(ValueError): Replay.restore(self.input, self.manifest, cp, rule="AGREE2")
        bad = self.alter_sim(obj.checkpoint(), lambda s: s["decisions"][0]["features"]["votes"].pop("C05"))
        with self.assertRaises(ValueError): Replay.restore(self.input, self.manifest, bad, rule="AGREE2")

    def test_tampered_arbitration_semantics_and_position_risk_reject(self):
        obj = self.replay(rule="AGREE2"); self.prefix(obj, 809)
        self.assertIsNotNone(obj.sim.position)
        for change in (lambda s: s.update(entry_arbitration=None),
                       lambda s: s["entry_arbitration"].update(side=True),
                       lambda s: s["entry_arbitration"].update(stop_distance=.01),
                       lambda s: s["entry_arbitration"]["features"].update(supporters=[]),
                       lambda s: s["entry_checks"][0].update(estimated_risk=100),
                       lambda s: s["entry_checks"][0].update(sequence=900),
                       lambda s: s.update(trade_arbitration={})):
            bad = self.alter_sim(obj.checkpoint(), change)
            with self.assertRaises(ValueError): Replay.restore(self.input, self.manifest, bad, rule="AGREE2")

    def test_completed_trade_arbitration_and_fill_lineage_reject_mismatch(self):
        obj = self.replay(rule="AGREE2"); obj.run()
        self.assertTrue(obj.sim.trades)
        for change in (lambda s: s["trade_arbitration"][0].update(entry_sequence=0),
                       lambda s: s["trade_arbitration"][0].update(trade_index=True),
                       lambda s: s["fill_lineage"][0].update(exit_sequence=True),
                       lambda s: s["entry_checks"][0].update(opened=False)):
            bad = self.alter_sim(obj.checkpoint(), change)
            with self.assertRaises(ValueError): Replay.restore(self.input, self.manifest, bad, rule="AGREE2")

    def test_checksum_cursor_repeats_and_latest_quote_reject_mismatch(self):
        obj = self.replay(); self.prefix(obj, 809)
        for change in (lambda p: p.update(next_sequence=True), lambda p: p.update(next_sequence=808),
                       lambda p: p.update(repeats=1)):
            with self.assertRaises(ValueError): Replay.restore(self.input, self.manifest, self.rewrite(obj.checkpoint(), change))
        bad = self.alter_sim(obj.checkpoint(), lambda s: s["_quote"].update(bid=1.0))
        with self.assertRaises(ValueError): Replay.restore(self.input, self.manifest, bad)
        envelope = json.loads(obj.checkpoint()); envelope["payload"]["next_sequence"] = 5
        with self.assertRaises(ValueError): Replay.restore(self.input, self.manifest, json.dumps(envelope))

    def test_changed_source_rule_manifest_config_or_fixture_rejects(self):
        for key, value in (("members", ["C00"]), ("rules", ["AGREE2"]), ("common_warmup_hours", 51),
                           ("initial_equity_per_account", 30000)):
            manifest = json.loads(self.manifest.read_bytes()); manifest[key] = value
            path = self.root / (key + ".json"); write_new(path, manifest)
            with self.assertRaises(ValueError): Replay(self.input, path)
        manifest = json.loads(self.manifest.read_bytes()); manifest["definitions"]["AGREE2"]["reject_opposition"] = False
        path = self.root / "rule-change.json"; write_new(path, manifest)
        with self.assertRaises(ValueError): Replay(self.input, path)
        with patch("forex_demo_lab.strategy_combination_115.source_bindings", return_value={}):
            with self.assertRaises(ValueError): self.replay()
        path = self.root / "changed-fixture.json"; path.write_bytes(self.input.read_bytes() + b" ")
        with self.assertRaises(ValueError): Replay(path, self.manifest)

    def test_duplicate_event_is_idempotent_and_conflicts_do_not_change_state(self):
        obj = self.replay(rule="AGREE2"); self.prefix(obj, 809)
        before = obj.checkpoint()
        self.assertFalse(obj.step(obj.events[808]))
        for event in (obj.events[807], obj.events[810], {**obj.events[808], "bid": True},
                      {**obj.events[808], "ask": obj.events[808]["ask"] + .0001}):
            with self.assertRaises(ValueError): obj.step(event)
        self.assertEqual(obj.checkpoint(), before)

    def test_public_inputs_and_finished_report_are_defensive_copies(self):
        obj = self.replay(rule="AGREE2")
        obj.events[0]["bid"] = 9; obj.manifest["definitions"]["AGREE2"]["minimum_support"] = 1
        obj.fixture["events"][0]["ask"] = 9
        row = obj.run(); row["trades"].clear(); row["decisions"].clear(); row["entry_checks"].clear()
        self.assertTrue(obj.report()["trades"])
        self.assertTrue(obj.report()["decisions"])
        self.assertTrue(obj.report()["entry_checks"])

    def test_finish_exhaustion_development_exit_boundaries_and_no_final_signal(self):
        obj = self.replay(rule="AGREE2")
        with self.assertRaises(ValueError): obj.finish()
        with self.assertRaises(ValueError): obj.report()
        row = obj.run()
        self.assertEqual(row["events"], 1152)
        self.assertEqual(row["metrics"]["warmup_hours"], 201)
        self.assertEqual(row["metrics"]["evaluation_hours"], 87)
        self.assertTrue(all(t["exit_sequence"] < 1152 for t in row["fill_lineage"]))
        before = obj.checkpoint(); obj.finish()
        self.assertEqual(obj.checkpoint(), before)
        self.assertFalse(obj.step(obj.events[-1]))

    def test_native_routes_remain_diagnostic_and_do_not_construct_simulator(self):
        run = self.root / "native111"; run.mkdir()
        for name, data in encode(payloads(1)): (run / name).write_bytes(data)
        single = self.root / "native107.txt"; single.write_bytes(encode107(complete107()))
        with patch("forex_demo_lab.strategy_combination_115._CombinationTicks", side_effect=AssertionError("constructed")):
            for fmt, path in (("107", single), ("109", single), ("111", run)):
                r = inspect_capture(path, fmt)
                self.assertEqual(r["status"], "performance_unavailable")
                self.assertFalse(r["orders_available"])
                self.assertNotIn("metrics", r)
            with self.assertRaises(ValueError): Replay(single, self.manifest)

    def test_invalid_invented_clock_age_quote_reject_before_engine(self):
        for change in (lambda f: f.update(clock="broker_server"),
                       lambda f: f["events"][1].update(source_msc=f["events"][1]["receipt_msc"] - 2001),
                       lambda f: f["events"][1].update(sequence=True)):
            value = fixture(); change(value)
            path = self.root / ("invalid-" + str(len(list(self.root.iterdir()))) + ".json"); write_new(path, value)
            with patch("forex_demo_lab.strategy_combination_115._CombinationTicks", side_effect=AssertionError("constructed")):
                with self.assertRaises(ValueError): Replay(path, self.manifest)

    def test_cli_round_trip_reports_all_rules_and_never_overwrites(self):
        script = str(ROOT / "scripts/strategy-combination-115.py")
        f, m, out = self.root / "cli.json", self.root / "cli-frozen.json", self.root / "cli-report.json"
        for args in (("create-fixture", "flat", str(f)), ("freeze", str(f), str(m)),
                     ("evaluate", str(f), str(m), str(out))):
            p = subprocess.run([sys.executable, script, *args], text=True, capture_output=True)
            self.assertEqual(p.returncode, 0, p.stderr)
        result = json.loads(p.stdout)
        self.assertEqual(result["comparisons"], 12)
        self.assertTrue(all(r["metrics"]["net_pnl"] == 0 for r in result["results"]))
        self.assertIsNone(result["aggregate_portfolio_result"])
        before = out.read_bytes()
        p = subprocess.run([sys.executable, script, "evaluate", str(f), str(m), str(out)], text=True, capture_output=True)
        self.assertEqual(p.returncode, 1)
        self.assertEqual(out.read_bytes(), before)
        self.assertEqual(json.loads(p.stdout), {"accepted": False, "reason": "invalid_unavailable_or_existing_artifact"})
        self.assertFalse(p.stderr)


if __name__ == "__main__":
    unittest.main()
