from copy import deepcopy
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from forex_demo_lab.model import Bar, Config
from forex_demo_lab.strategy_adapter_114 import (
    CANDIDATES, Replay, WARMUP_HOURS, _CandidateTicks, _canonical,
    evaluate_fixture, freeze_fixture, inspect_capture, load_fixture, scenarios, write_new,
)
from forex_demo_lab.strategy_experiment_028 import Experiment028Simulator, decision
from forex_demo_lab.strategy_fixture_114 import CASES, START, fixture
from forex_demo_lab.shadow_engine_113 import Replay as OldReplay, load_fixture as old_load
from forex_demo_lab.shadow_fixture_113 import fixture as old_fixture
from forex_demo_lab.strategies import decide
from test_forward_capture_111 import encode, payloads
from test_private_recorder_107 import complete as complete107, encode as encode107

ROOT = Path(__file__).resolve().parents[1]
BASE = datetime.fromtimestamp(START / 1000, timezone.utc)


def bars(closes):
    return [Bar(BASE + timedelta(hours=i), p, p, p, p, 1) for i, p in enumerate(closes)]


class Strategy114Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.input, self.manifest = self.make(fixture())

    def make(self, value, name="fixture"):
        path, manifest = self.root / (name + ".json"), self.root / (name + "-frozen.json")
        write_new(path, value)
        freeze_fixture(path, manifest)
        return path, manifest

    def replay(self, **kw):
        return Replay(self.input, self.manifest, **kw)

    def prefix(self, obj, n):
        for event in obj.events[:n]:
            obj.step(event)

    def rewrite(self, checkpoint, change):
        envelope = json.loads(checkpoint)
        change(envelope["payload"])
        envelope["sha256"] = hashlib.sha256(_canonical(envelope["payload"])).hexdigest()
        return json.dumps(envelope)

    def alter_sim(self, checkpoint, change):
        def edit(payload):
            inner = json.loads(payload["simulator"])
            change(inner["payload"]["state"])
            body = json.dumps(inner["payload"], sort_keys=True, allow_nan=False)
            inner["sha256"] = hashlib.sha256(body.encode()).hexdigest()
            payload["simulator"] = json.dumps(inner)
        return self.rewrite(checkpoint, edit)

    def manual(self, side=1, distance=.001, spread=1, candidate="C06"):
        obj = _CandidateTicks(Config(), candidate)
        bid, ask = 1.1, 1.1 + spread * .0001
        obj._quote = {"sequence": 0, "time_msc": START, "bid": bid, "ask": ask}
        obj._open(Bar(BASE, bid, bid, bid, bid, spread), side, distance)
        return obj

    def test_fixed_contract_and_original_cost_settings(self):
        self.assertEqual(CANDIDATES, ("C00", "C05", "C06", "CASH"))
        self.assertEqual(WARMUP_HOURS, 201)
        m = json.loads(self.manifest.read_bytes())
        self.assertEqual(m["candidates"], list(CANDIDATES))
        self.assertEqual(m["scenarios"], scenarios())
        self.assertEqual(m["scenarios"]["base"]["config"], asdict(Config()))
        self.assertEqual(m["initial_equity_per_account"], 10000)
        self.assertEqual(m["common_warmup_hours"], 201)
        self.assertEqual(m["cash_interest"], 0)

    def test_new_fixture_is_versioned_and_predecessor_is_preserved(self):
        old, manifest = self.root / "old.json", self.root / "old-frozen.json"
        write_new(old, old_fixture())
        old_load(old)
        with self.assertRaises(ValueError):
            load_fixture(old)
        with self.assertRaises(ValueError):
            old_load(self.input)
        with self.assertRaises(ValueError):
            OldReplay(self.input, self.manifest)
        self.assertFalse(manifest.exists())

    def test_all_48_fixed_comparisons_and_costs_reported(self):
        seen = set()
        for case in CASES:
            f, m = (self.input, self.manifest) if case == "continuation" else self.make(fixture(case), case)
            report = evaluate_fixture(f, m, self.root / (case + "-report.json"))
            self.assertEqual(len(report["results"]), 16)
            self.assertIsNone(report["selected_strategy"])
            self.assertIsNone(report["portfolio_result"])
            self.assertIsNone(report["combination_weights"])
            for row in report["results"]:
                seen.add((case, row["scenario"], row["partition"], row["candidate"]))
                costs = row["cost_totals"]
                self.assertAlmostEqual(costs["reference_gross"] - sum(costs[k] for k in
                    ("spread", "slippage", "commission", "financing_debit")), costs["net"])
                self.assertAlmostEqual(costs["net"], row["metrics"]["net_pnl"])
                self.assertEqual(row["initial_equity_per_account"], 10000)
                self.assertEqual(len(row["trades"]), len(row["fill_lineage"]))
                for trade, cost in zip(row["trades"], row["cost_audit"]):
                    rate = 7 if row["scenario"] == "base" else 10
                    self.assertAlmostEqual(cost["commission"], trade["lots"] * rate)
                    self.assertAlmostEqual(cost["financing_debit"], -trade["swap"])
                    self.assertGreaterEqual(cost["spread"], -1e-8)
                for key in ("market_validation", "market_data_qualified", "paper_evaluation_available",
                            "orders_available", "real_money_execution_available"):
                    self.assertFalse(row[key])
        self.assertEqual(len(seen), 48)

    def test_prefix_decisions_fills_and_metrics_match_unchanged028_engine(self):
        for candidate in CANDIDATES[:3]:
            for scenario in ("base", "adverse"):
                for partition in ("development", "validation"):
                    with self.subTest(candidate=candidate, scenario=scenario, partition=partition):
                        obj = self.replay(candidate=candidate, scenario=scenario, partition=partition)
                        direct = Experiment028Simulator(obj.sim.config, candidate, obj.start)
                        for event in obj.events:
                            obj.step(event)
                            direct.step_tick(obj._tick(event))
                            if event["sequence"] in (0, 800, 803, 804, 808, 815, 895, 908, 1151):
                                self.assertEqual(obj.sim.trades, direct.trades)
                                self.assertEqual(obj.sim.position, direct.position)
                                self.assertEqual(obj.sim.metrics(), direct.metrics())
                                projected = [{"hour_start_ms": d["hour_msc"],
                                              **{k: d[k] for k in ("side", "stop_distance", "reason", "features")}}
                                             for d in obj.sim.decisions]
                                self.assertEqual(projected, direct.decision_log)
                        obj.finish(); direct.finish()
                        self.assertEqual(obj.report()["trades"], direct.trades)
                        self.assertEqual(obj.report()["metrics"], direct.metrics())
                        self.assertEqual(obj.report()["fill_lineage"], direct.fill_lineage)

    def test_common_warmup_and_prior_completed_history(self):
        for candidate in CANDIDATES:
            obj = self.replay(candidate=candidate)
            self.prefix(obj, 804)
            self.assertFalse(obj.sim.decisions)
            self.assertIsNone(obj.sim.position)
            self.assertEqual(obj.sim.balance, 10000)
            obj.step(obj.events[804])
            self.assertEqual(len(obj.sim.decisions), 1)
            row = obj.sim.decisions[0]
            self.assertEqual(row["hour_msc"], START + 201 * 3600000)
            self.assertEqual(row["history_size"], 201)
            self.assertEqual(row["last_closed_hour"], (BASE + timedelta(hours=200)).isoformat())

    def test_future_suffix_cannot_change_prior_state_or_entry(self):
        f, m = self.make(fixture("reversal"), "reversal")
        for candidate in CANDIDATES:
            a, b = self.replay(candidate=candidate), Replay(f, m, candidate=candidate)
            self.prefix(a, 816); self.prefix(b, 816)
            self.assertEqual(a.sim.checkpoint(), b.sim.checkpoint())
            before = deepcopy(a.sim.decisions)
            a.run(); b.run()
            boundary = START + 204 * 3600000
            self.assertEqual(before, [d for d in a.sim.decisions if d["hour_msc"] < boundary])
            self.assertEqual(before, [d for d in b.sim.decisions if d["hour_msc"] < boundary])

    def test_validation_has_fresh_capital_and_no_development_position(self):
        for candidate in CANDIDATES:
            obj = self.replay(candidate=candidate, partition="validation")
            self.prefix(obj, 1152)
            self.assertEqual(obj.sim.balance, 10000)
            self.assertIsNone(obj.sim.position)
            self.assertFalse(obj.sim.trades)
            self.assertFalse(obj.sim.decisions)
            self.assertEqual(obj.sim.max_tick_drawdown, 0)

    def test_development_has_no_validation_quotes_even_for_exit(self):
        obj = self.replay()
        self.assertEqual(len(obj.events), 1152)
        self.assertLess(obj.events[-1]["receipt_msc"], obj.fixture["validation_start_msc"])
        result = obj.run()
        self.assertEqual(result["events"], 1152)
        self.assertTrue(all(row["exit_sequence"] < 1152 for row in result["fill_lineage"]))
        self.assertEqual(result["metrics"]["warmup_hours"], 201)
        self.assertEqual(result["metrics"]["evaluation_hours"], 87)

    def test_cash_is_unchanged_for_every_case_partition_and_cost(self):
        for case in CASES:
            f, m = (self.input, self.manifest) if case == "continuation" else self.make(fixture(case), case)
            for scenario in ("base", "adverse"):
                for partition in ("development", "validation"):
                    row = Replay(f, m, scenario, partition, "CASH").run()
                    self.assertEqual(row["metrics"]["net_pnl"], 0)
                    self.assertEqual(row["metrics"]["closed_trades"], 0)
                    self.assertIsNone(row["metrics"]["win_rate"])
                    self.assertEqual(row["metrics"]["max_tick_drawdown"], 0)
                    self.assertEqual(row["metrics"]["bar_exposure"], 0)
                    self.assertTrue(all(v == 0 for v in row["cost_totals"].values()))
                    self.assertTrue(all(d["reason"] == "cash_reference" for d in row["decisions"]))
        self.assertIsNone(self.manual(candidate="CASH").position)

    def test_flat_all_candidates_abstain_with_no_costs(self):
        f, m = self.make(fixture("flat"), "flat")
        for candidate in CANDIDATES:
            row = Replay(f, m, candidate=candidate).run()
            self.assertEqual(row["metrics"]["closed_trades"], 0)
            self.assertEqual(row["metrics"]["net_pnl"], 0)
            self.assertTrue(row["decisions"])
            self.assertTrue(all(d["side"] == 0 for d in row["decisions"]))

    def test_trend_only_range_and_zero_path_abstention_matches_existing(self):
        for closes in ([1.1] * 201, [1.1] * 180 + [1.1 + (i % 2) * .01 for i in range(21)]):
            sim = _CandidateTicks(Config(), "C05")
            sim.history, sim.current = bars(closes), {"hour": START // 3600000 + 201}
            value = decision("C05", sim.history, sim.config)
            self.assertEqual(sim._decision(), (value.side, value.stop_distance))
            self.assertEqual(sim.decisions[-1]["reason"], value.reason)
            self.assertEqual(value.side, 0)
            self.assertTrue(value.reason.startswith("trend_only_abstain:"))

    def test_confirmed_long_short_and_slow_disagreement_match_existing(self):
        cases = [([1.125] * 200 + [1.25], 1), ([1.125] * 200 + [1.0], -1),
                 ([1.25] * 151 + [1.125] * 49 + [1.1875], 0)]
        for closes, side in cases:
            sim = _CandidateTicks(Config(), "C06")
            sim.history, sim.current = bars(closes), {"hour": START // 3600000 + 201}
            value = decision("C06", sim.history, sim.config)
            self.assertEqual(sim._decision(), (side, value.stop_distance))
            self.assertEqual(sim.decisions[-1]["features"], value.features)
        self.assertEqual(decide("C02", bars(cases[-1][0]), Config()).side, 1)

    def test_gap_discards_immediate_entry_without_imputing_hours(self):
        value = fixture()
        value["events"] = [e for e in value["events"] if e["receipt_msc"] // 3600000 != START // 3600000 + 201]
        for i, e in enumerate(value["events"]):
            e["sequence"] = i
        f, m = self.make(value, "gap")
        for candidate in CANDIDATES:
            obj = Replay(f, m, candidate=candidate)
            self.prefix(obj, 805)
            self.assertFalse(obj.sim.decisions)
            self.assertIsNone(obj.sim.position)
            self.assertEqual(obj.sim.history[-1].time, BASE + timedelta(hours=200))

    def test_partition_requires_201_observed_prior_hours(self):
        for key in ("development_start_msc", "validation_start_msc"):
            value = fixture()
            value[key] = START + 200 * 3600000
            if key == "validation_start_msc":
                value["development_start_msc"] = START + 199 * 3600000
            path = self.root / (key + ".json")
            write_new(path, value)
            with self.assertRaises(ValueError):
                freeze_fixture(path, self.root / (key + "-manifest.json"))

    def test_risk_floor_single_position_and_spread_limit(self):
        for side in (1, -1):
            sim = self.manual(side=side)
            p = sim.position
            self.assertIsNotNone(p)
            estimated = p.lots * (.001 * 100000 + Config().slippage_pips * .0001 * 100000 + 7)
            self.assertLessEqual(estimated, 25)
            self.assertAlmostEqual(round(p.lots / .01) * .01, p.lots)
            sim._open(Bar(BASE, 1.1, 1.1, 1.1, 1.1, 1), -side, .001)
            self.assertIs(sim.position, p)
            self.assertEqual(sim.pending_entry_sequence, 0)
        self.assertIsNone(self.manual(spread=3).position)

    def test_gap_stop_loss_exceeds_budget_and_daily_pause_prevents_recovery_stakes(self):
        for side in (1, -1):
            sim = self.manual(side=side)
            price = 1.0 if side == 1 else 1.2
            sim.step_tick({"sequence": 0, "time_msc": START, "bid": price, "ask": price + .0001})
            self.assertLess(sim.trades[0]["net_pnl"], -25)
            self.assertEqual(sim.trades[0]["reason"], "stop_tick")
            self.assertTrue(sim.paused)
            self.assertEqual(sim.fill_lineage[0], {"trade_index": 0, "entry_sequence": 0, "exit_sequence": 0})
            sim._open(Bar(BASE, price, price, price, price, 1), side, .001)
            self.assertIsNone(sim.position)

    def test_target_overshoot_uses_corrected_fill_equity_and_costs(self):
        for side in (1, -1):
            sim = self.manual(side=side)
            target = sim.position.target
            price = 1.2 if side == 1 else 1.0
            sim.step_tick({"sequence": 0, "time_msc": START, "bid": price, "ask": price + .0001})
            self.assertEqual(sim.trades[0]["exit"], target)
            self.assertEqual(sim.trades[0]["reason"], "target_tick")
            self.assertAlmostEqual(sim.peak_tick_equity, sim.balance)
            self.assertAlmostEqual(sim.max_tick_drawdown, 0)
            audit = sim.cost_audit[0]
            self.assertAlmostEqual(audit["net"], sim.trades[0]["net_pnl"])
            self.assertEqual(sim.execution_metric_version, "executable_fill_equity_019b_v1")

    def test_restart_before_during_after_position_matches_entire_result(self):
        for candidate in CANDIDATES:
            for partition in ("development", "validation"):
                expected = self.replay(candidate=candidate, partition=partition).run()
                cursors = (0, 804, 809, 817, 909) if partition == "development" else (0, 1152, 1961, 2049, 2060)
                for cursor in cursors:
                    with self.subTest(candidate=candidate, partition=partition, cursor=cursor):
                        obj = self.replay(candidate=candidate, partition=partition)
                        self.prefix(obj, cursor)
                        restored = Replay.restore(self.input, self.manifest, obj.checkpoint(),
                                                  candidate=candidate, partition=partition)
                        if cursor:
                            self.assertFalse(restored.step(restored.events[cursor - 1]))
                        self.assertEqual(restored.run(), expected)
                        checkpoint = restored.checkpoint()
                        ended = Replay.restore(self.input, self.manifest, checkpoint,
                                               candidate=candidate, partition=partition)
                        self.assertEqual(ended.run(), expected)

    def test_adverse_and_reversal_restart_preserves_loss_latch_and_financing(self):
        f, m = self.make(fixture("reversal"), "reversal")
        for candidate in CANDIDATES[:3]:
            for partition, cursor in (("development", 817), ("validation", 2061)):
                obj = Replay(f, m, "adverse", partition, candidate)
                self.prefix(obj, cursor)
                expected_state = obj.sim.checkpoint()
                restored = Replay.restore(f, m, obj.checkpoint(), "adverse", partition, candidate)
                self.assertEqual(restored.sim.checkpoint(), expected_state)
                self.assertEqual(restored.run(), obj.run())
                self.assertTrue(any(t["net_pnl"] < 0 for t in obj.sim.trades))

    def test_cross_candidate_scenario_partition_and_legacy_restore_reject(self):
        obj = self.replay(candidate="C05")
        self.prefix(obj, 809)
        cp = obj.checkpoint()
        for kw in ({"candidate": "C06"}, {"candidate": "C00"}, {"candidate": "CASH"},
                   {"candidate": "C05", "scenario": "adverse"},
                   {"candidate": "C05", "partition": "validation"}):
            with self.assertRaises(ValueError):
                Replay.restore(self.input, self.manifest, cp, **kw)
        with self.assertRaises(ValueError):
            Replay.restore(self.input, self.manifest, Experiment028Simulator(Config(), "C05").checkpoint())

    def test_internal_candidate_identity_and_metric_version_are_checked(self):
        cp = self.replay(candidate="C05").checkpoint()
        for key, value in (("candidate", "C06"), ("adapter_version", "old"),
                           ("execution_metric_version", "legacy"), ("evaluation_start_msc", START)):
            bad = self.alter_sim(cp, lambda s, k=key, v=value: s.update({k: v}))
            with self.assertRaises(ValueError):
                Replay.restore(self.input, self.manifest, bad, candidate="C05")

    def test_checkpoint_cursor_quote_and_repeat_count_are_checked(self):
        obj = self.replay()
        self.prefix(obj, 809)
        for change in (lambda p: p.update(next_sequence=True), lambda p: p.update(next_sequence=808),
                       lambda p: p.update(repeats=1), lambda p: p.update(repeats=True)):
            with self.assertRaises(ValueError):
                Replay.restore(self.input, self.manifest, self.rewrite(obj.checkpoint(), change))
        bad = self.alter_sim(obj.checkpoint(), lambda s: s["_quote"].update(bid=1.0))
        with self.assertRaises(ValueError):
            Replay.restore(self.input, self.manifest, bad)

    def test_checkpoint_position_audit_and_fill_lineage_are_checked(self):
        obj = self.replay(candidate="C05")
        self.prefix(obj, 809)
        self.assertIsNotNone(obj.sim.position)
        for key, value in (("_entry_audit", None), ("pending_entry_sequence", None),
                           ("pending_entry_sequence", True), ("cost_audit", {}), ("fill_lineage", {})):
            bad = self.alter_sim(obj.checkpoint(), lambda s, k=key, v=value: s.update({k: v}))
            with self.assertRaises(ValueError):
                Replay.restore(self.input, self.manifest, bad, candidate="C05")
        obj.run()
        bad = self.alter_sim(obj.checkpoint(), lambda s: s["fill_lineage"][0].update(exit_sequence=True))
        with self.assertRaises(ValueError):
            Replay.restore(self.input, self.manifest, bad, candidate="C05")

    def test_checkpoint_checksum_size_and_duplicate_fields_reject(self):
        obj = self.replay()
        cp = json.loads(obj.checkpoint())
        cp["payload"]["next_sequence"] = 1
        for bad in (json.dumps(cp), "x" * (8 * 1024 * 1024 + 1), '{"payload":{},"payload":{}}'):
            with self.assertRaises(ValueError):
                Replay.restore(self.input, self.manifest, bad)

    def test_changed_fixture_manifest_code_candidates_or_costs_reject(self):
        for key, value in (("candidates", ["C00"]), ("common_warmup_hours", 51),
                           ("cash_interest", 1), ("initial_equity_per_account", 20000)):
            m = json.loads(self.manifest.read_bytes())
            m[key] = value
            path = self.root / (key + ".json")
            write_new(path, m)
            with self.assertRaises(ValueError):
                Replay(self.input, path)
        with patch("forex_demo_lab.strategy_adapter_114.source_bindings", return_value={}):
            with self.assertRaises(ValueError):
                self.replay()
        m = json.loads(self.manifest.read_bytes())
        m["scenarios"]["base"]["config"]["slippage_pips"] = 0
        path = self.root / "cost-change.json"
        write_new(path, m)
        with self.assertRaises(ValueError):
            Replay(self.input, path)
        value = fixture(); value["events"][-1]["ask"] += .0001
        path = self.root / "fixture-change.json"
        write_new(path, value)
        with self.assertRaises(ValueError):
            Replay(path, self.manifest)

    def test_malformed_quotes_age_and_order_reject_before_engine(self):
        for change in (lambda e: e.update(sequence=True), lambda e: e.update(bid=True),
                       lambda e: e.update(ask=float("inf")), lambda e: e.update(bid=0),
                       lambda e: e.update(ask=e["bid"] - .001), lambda e: e.update(source_msc=e["receipt_msc"] + 1),
                       lambda e: e.update(source_msc=e["receipt_msc"] - 2001), lambda e: e.update(sequence=2),
                       lambda e: e.update(source_msc=START - 51)):
            value = fixture(); change(value["events"][1])
            path = self.root / ("bad-" + str(len(list(self.root.iterdir()))) + ".json")
            if value["events"][1]["ask"] == float("inf"):
                path.write_text(json.dumps(value))
            else:
                write_new(path, value)
            with patch("forex_demo_lab.strategy_adapter_114._CandidateTicks", side_effect=AssertionError("constructed")):
                with self.assertRaises(ValueError):
                    Replay(path, self.manifest)

    def test_latest_duplicate_is_idempotent_but_bool_conflicts_and_missing_reject(self):
        obj = self.replay()
        self.prefix(obj, 809)
        before = obj.checkpoint()
        self.assertFalse(obj.step(obj.events[808]))
        self.assertEqual(before, obj.checkpoint())
        for event in (obj.events[807], obj.events[810], {**obj.events[808], "bid": True},
                      {**obj.events[808], "ask": obj.events[808]["ask"] + .0001}):
            with self.assertRaises(ValueError):
                obj.step(event)
        self.assertEqual(before, obj.checkpoint())

    def test_unchanged_same_source_timestamp_is_counted_without_changed_price(self):
        value = fixture()
        value["events"][1].update(source_msc=value["events"][0]["source_msc"],
                                  receipt_msc=value["events"][0]["receipt_msc"] + 500,
                                  bid=value["events"][0]["bid"], ask=value["events"][0]["ask"])
        f, m = self.make(value, "repeat")
        obj = Replay(f, m)
        self.prefix(obj, 2)
        self.assertEqual(obj.repeats, 1)
        restored = Replay.restore(f, m, obj.checkpoint())
        self.assertEqual(restored.repeats, 1)
        value["events"][1]["ask"] += .0001
        path = self.root / "changed-source.json"
        write_new(path, value)
        with self.assertRaises(ValueError):
            load_fixture(path)

    def test_defensive_input_and_result_views(self):
        obj = self.replay()
        obj.events[0]["bid"] = 9
        obj.fixture["events"][0]["bid"] = 9
        obj.manifest["scenarios"]["base"]["config"]["fast"] = 1
        self.assertEqual(obj.events[0]["bid"], fixture()["events"][0]["bid"])
        row = obj.run()
        row["trades"].clear(); row["decisions"].clear(); row["fill_lineage"].clear()
        self.assertTrue(obj.report()["decisions"])
        self.assertTrue(obj.report()["trades"])

    def test_finish_requires_exhaustion_and_is_idempotent(self):
        obj = self.replay()
        with self.assertRaises(ValueError):
            obj.report()
        with self.assertRaises(ValueError):
            obj.finish()
        row = obj.run()
        obj.finish()
        self.assertEqual(obj.report(), row)
        self.assertFalse(obj.step(obj.events[-1]))
        with self.assertRaises(ValueError):
            obj.step(obj.fixture["events"][len(obj.events)])

    def test_native_routes_inspect_only_and_never_construct_engine(self):
        run = self.root / "native111"; run.mkdir()
        for name, data in encode(payloads(1)):
            (run / name).write_bytes(data)
        single = self.root / "native107.txt"
        single.write_bytes(encode107(complete107()))
        with patch("forex_demo_lab.strategy_adapter_114._CandidateTicks", side_effect=AssertionError("constructed")):
            for fmt, path in (("107", single), ("109", single), ("111", run)):
                result = inspect_capture(path, fmt)
                self.assertEqual(result["status"], "performance_unavailable")
                self.assertFalse(result["paper_evaluation_available"])
                self.assertFalse(result["orders_available"])
            with self.assertRaises(ValueError):
                Replay(single, self.manifest)

    def test_unknown_candidate_cost_and_partition_reject(self):
        for kw in ({"candidate": "C02"}, {"candidate": "live"}, {"scenario": "free"}, {"partition": "all"}):
            with self.assertRaises(ValueError):
                self.replay(**kw)

    def test_cli_fixture_freeze_evaluate_and_no_overwrite(self):
        script = str(ROOT / "scripts/strategy-adapter-114.py")
        f, m, out = self.root / "cli.json", self.root / "cli-frozen.json", self.root / "cli-out.json"
        for args in (("create-fixture", "flat", str(f)), ("freeze", str(f), str(m)),
                     ("evaluate", str(f), str(m), str(out))):
            result = subprocess.run([sys.executable, script, *args], text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
        result = json.loads(result.stdout)
        self.assertEqual(result["comparisons"], 16)
        self.assertTrue(all(r["metrics"]["net_pnl"] == 0 for r in result["results"]))
        before = out.read_bytes()
        failed = subprocess.run([sys.executable, script, "evaluate", str(f), str(m), str(out)],
                                text=True, capture_output=True)
        self.assertEqual(failed.returncode, 1)
        self.assertEqual(out.read_bytes(), before)
        self.assertEqual(json.loads(failed.stdout), {"accepted": False, "reason": "invalid_unavailable_or_existing_artifact"})
        self.assertFalse(failed.stderr)

    def test_fixture_json_duplicate_fields_and_native_clock_label_reject(self):
        path = self.root / "duplicate.json"
        path.write_text('{"format":"FXDL_STRATEGY114_V1","format":"FXDL_STRATEGY114_V1"}')
        with self.assertRaises(ValueError):
            load_fixture(path)
        value = fixture(); value["clock"] = "broker_server"
        path = self.root / "native-clock.json"; write_new(path, value)
        with self.assertRaises(ValueError):
            load_fixture(path)


if __name__ == "__main__":
    unittest.main()
