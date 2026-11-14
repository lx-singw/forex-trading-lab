from copy import deepcopy
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from forex_demo_lab.model import Config
from forex_demo_lab.shadow_engine_113 import (
    MAX_BYTES, MAX_EVENTS, Replay, _canonical, evaluate_fixture, freeze_fixture,
    inspect_capture, load_fixture, scenarios, write_new,
)
from forex_demo_lab.shadow_fixture_113 import START, fixture
from forex_demo_lab.execution_metrics import ExecutableEquityTickSimulator
from test_forward_capture_111 import encode, payloads
from test_private_recorder_107 import complete as complete107, encode as encode107

ROOT = Path(__file__).resolve().parents[1]


class Shadow113Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.input = self.root / "fixture.json"
        self.manifest = self.root / "manifest.json"
        self.make(fixture())

    def make(self, value, name="fixture"):
        path = self.root / (name + ".json")
        manifest = self.root / (name + "-frozen.json")
        write_new(path, value)
        freeze_fixture(path, manifest)
        if name == "fixture":
            self.input, self.manifest = path, manifest
        return path, manifest

    def replay(self, **kw):
        return Replay(self.input, self.manifest, **kw)

    def run_to(self, replay, count):
        for event in replay.events[:count]:
            replay.step(event)

    def rewrite_checkpoint(self, checkpoint, change):
        value = json.loads(checkpoint)
        change(value["payload"])
        value["sha256"] = hashlib.sha256(_canonical(value["payload"])).hexdigest()
        return json.dumps(value)

    def test_base_and_adverse_only_change_declared_costs(self):
        s = scenarios()
        self.assertEqual(s["base"]["config"], asdict(Config()))
        differences = {k for k in s["base"]["config"] if s["base"]["config"][k] != s["adverse"]["config"][k]}
        self.assertEqual(differences, {"commission_per_lot_round_turn", "slippage_pips", "swap_long_per_lot", "swap_short_per_lot"})
        self.assertEqual(s["adverse"]["spread_floor_pips"], 1.2)

    def test_all_four_partition_scenarios_reconcile_costs(self):
        report = evaluate_fixture(self.input, self.manifest, self.root / "out.json")
        self.assertEqual(len(report["results"]), 4)
        self.assertIsNone(report["selected_strategy"])
        for r in report["results"]:
            costs = r["cost_totals"]
            self.assertAlmostEqual(costs["reference_gross"] - sum(costs[k] for k in ("spread", "slippage", "commission", "financing_debit")), costs["net"])
            self.assertAlmostEqual(costs["net"], r["metrics"]["net_pnl"])
            self.assertGreater(r["metrics"]["closed_trades"], 0)
            for t, a in zip(r["trades"], r["cost_audit"]):
                rate = 7 if r["scenario"] == "base" else 10
                self.assertAlmostEqual(t["lots"] * rate, a["commission"])
                self.assertAlmostEqual(-t["swap"], a["financing_debit"])
                self.assertGreaterEqual(a["spread"], -1e-8)
                self.assertGreater(a["slippage"], 0)
            for key in ("market_validation", "paper_evaluation_available", "orders_available", "real_money_execution_available"):
                self.assertFalse(r[key])

    def test_fixed_paths_exercise_winning_and_losing_trades(self):
        a = self.replay().run()
        f, m = self.make(fixture("reversal"), "reversal")
        b = Replay(f, m).run()
        self.assertTrue(any(t["net_pnl"] > 0 for t in a["trades"]))
        self.assertTrue(any(t["net_pnl"] < 0 for t in b["trades"]))
        self.assertEqual(a["kind"], "invented_software_check")
        self.assertFalse(a["market_validation"])

    def test_adapter_prefix_and_final_results_match_existing_tick_engine(self):
        a, direct = self.replay(), ExecutableEquityTickSimulator(Config())
        for event in a.events:
            a.step(event)
            direct.step_tick({"sequence": event["sequence"], "time_msc": event["receipt_msc"],
                              "bid": event["bid"], "ask": event["ask"]})
            if event["sequence"] in (0, 1, 203, 211, 215, 216, 383):
                for key, value in vars(direct).items():
                    self.assertEqual(getattr(a.sim, key), value, key)
        a.finish(); direct.finish()
        self.assertEqual(a.report()["metrics"], direct.metrics())
        self.assertEqual(a.report()["trades"], direct.trades)

    def test_future_suffix_changes_cannot_change_entry_prefix(self):
        changed = fixture("reversal")
        f, m = self.make(changed, "future")
        a, b = self.replay(), Replay(f, m)
        # Only the fixed continuation/reversal suffix differs from hour54 onward.
        self.run_to(a, 216); self.run_to(b, 216)
        self.assertEqual(a.sim.checkpoint(), b.sim.checkpoint())
        self.assertIsNotNone(a.sim.position)
        opened, lots = a.sim.position.entry, a.sim.position.lots
        a.run(); b.run()
        self.assertEqual(a.sim.trades[0]["entry"], opened)
        self.assertEqual(b.sim.trades[0]["entry"], opened)
        self.assertEqual(b.sim.trades[0]["lots"], lots)

    def test_no_warmup_trading_and_no_current_hour_signal(self):
        r = self.replay()
        self.run_to(r, 204)
        self.assertIsNone(r.sim.position)
        self.assertFalse(r.sim.trades)
        self.assertFalse(r.sim.decisions)
        r.step(r.events[204])
        self.assertTrue(all(d["history_size"] >= 51 for d in r.sim.decisions))

    def test_insufficient_history_produces_no_trades(self):
        value = fixture()
        value["events"] = value["events"][:80]
        value["development_start_msc"] = START
        value["validation_start_msc"] = START + 10 * 3600000
        f, m = self.make(value, "short")
        for partition in ("development", "validation"):
            report = Replay(f, m, partition=partition).run()
            self.assertEqual(report["metrics"]["closed_trades"], 0)
            self.assertEqual(report["cost_totals"]["net"], 0)

    def test_financing_rollover_and_final_market_exit_costs_reconcile(self):
        value = fixture()
        for e in value["events"]:
            hour = (e["receipt_msc"] - START) // 3600000
            if 54 <= hour < 96:
                wiggle = (e["bid"] - 1.106)
                e["bid"] = round(1.103 + wiggle, 8)
                e["ask"] = round(e["bid"] + .0001, 8)
        f, m = self.make(value, "financing")
        for scenario in ("base", "adverse"):
            r = Replay(f, m, scenario=scenario)
            self.run_to(r, 288)
            restored = Replay.restore(f, m, r.checkpoint(), scenario=scenario)
            self.assertEqual(r.run(), restored.run())
            t = r.sim.trades[0]
            self.assertEqual(t["reason"], "end_of_sample")
            self.assertLess(t["swap"], 0)
            a = r.sim.cost_audit[0]
            self.assertAlmostEqual(a["financing_debit"], -t["swap"])
            self.assertGreater(a["spread"], 0)
            self.assertGreater(a["slippage"], 0)

    def test_development_cannot_consume_validation_quote(self):
        r = self.replay()
        r.run()
        self.assertTrue(all(e["receipt_msc"] < START + 96 * 3600000 for e in r.events))
        self.assertTrue(all(t["closed"] < "2001-01-05T00:00:00" for t in r.sim.trades))
        with self.assertRaisesRegex(ValueError, "replay_finished"):
            r.step(r.fixture["events"][384])

    def test_validation_capital_and_warmup_do_not_carry_development_trades(self):
        r = self.replay(partition="validation")
        self.run_to(r, 384)
        self.assertEqual(r.sim.balance, 10000)
        self.assertIsNone(r.sim.position)
        self.assertFalse(r.sim.trades)
        r.run()
        self.assertTrue(all(t["opened"] >= "2001-01-05T00:00:00" for t in r.sim.trades))
        self.assertTrue(r.report()["final_hour_partial"])

    def test_open_position_restart_equals_uninterrupted_and_duplicate_is_noop(self):
        a = self.replay()
        self.run_to(a, 216)
        self.assertIsNotNone(a.sim.position)
        saved = a.checkpoint()
        b = Replay.restore(self.input, self.manifest, saved)
        self.assertFalse(b.step(b.events[215]))
        self.assertEqual(b.checkpoint(), saved)
        self.assertEqual(a.run(), b.run())
        self.assertEqual(a.checkpoint(), b.checkpoint())

    def test_empty_and_completed_checkpoints_restore_and_finish_is_idempotent(self):
        r = self.replay()
        empty = Replay.restore(self.input, self.manifest, r.checkpoint())
        self.assertEqual(empty.checkpoint(), r.checkpoint())
        r.run()
        saved = r.checkpoint()
        b = Replay.restore(self.input, self.manifest, saved)
        b.finish()
        self.assertEqual(b.checkpoint(), saved)
        self.assertFalse(b.step(b.events[-1]))

    def test_restore_rejects_scenario_partition_and_fixture_switch(self):
        r = self.replay(); self.run_to(r, 216)
        for kw in ({"scenario": "adverse"}, {"partition": "validation"}):
            with self.assertRaisesRegex(ValueError, "checkpoint_binding"):
                Replay.restore(self.input, self.manifest, r.checkpoint(), **kw)
        f, m = self.make(fixture("reversal"), "other")
        with self.assertRaisesRegex(ValueError, "checkpoint_binding"):
            Replay.restore(f, m, r.checkpoint())

    def test_restore_rejects_corrupt_checksum_cursor_and_repetition_counts(self):
        r = self.replay(); self.run_to(r, 216)
        bad = json.loads(r.checkpoint()); bad["payload"]["next_sequence"] = 0
        with self.assertRaisesRegex(ValueError, "checkpoint_binding"):
            Replay.restore(self.input, self.manifest, json.dumps(bad))
        for field, value in (("next_sequence", 217), ("repeats", 1)):
            bad = self.rewrite_checkpoint(r.checkpoint(), lambda p: p.update({field: value}))
            with self.assertRaisesRegex(ValueError, "checkpoint_cursor"):
                Replay.restore(self.input, self.manifest, bad)

    def test_inner_checkpoint_changed_config_and_invalid_types_reject(self):
        r = self.replay(); self.run_to(r, 216)
        for section, field, value in (("config", "risk_fraction", .001), ("state", "cost_audit", None)):
            def change(p):
                inner = json.loads(p["simulator"])
                inner["payload"][section][field] = value
                body = json.dumps(inner["payload"], sort_keys=True, allow_nan=False)
                inner["sha256"] = hashlib.sha256(body.encode()).hexdigest()
                p["simulator"] = json.dumps(inner)
            bad = self.rewrite_checkpoint(r.checkpoint(), change)
            with self.assertRaises(ValueError): Replay.restore(self.input, self.manifest, bad)

    def test_target_overshoot_never_credits_unattainable_peak_equity(self):
        r = self.replay(); self.run_to(r, 216)
        target = r.sim.position.target
        self.assertGreater(r.events[216]["bid"], target)
        r.step(r.events[216])
        self.assertEqual(r.sim.trades[0]["exit"], target)
        self.assertAlmostEqual(r.sim.peak_tick_equity, r.sim.balance)
        self.assertEqual(r.sim.execution_metric_version, "executable_fill_equity_019b_v1")

    def test_checkpoint_without_corrected_metric_version_is_rejected(self):
        r = self.replay(); self.run_to(r, 216)
        def change(p):
            inner = json.loads(p["simulator"])
            del inner["payload"]["state"]["execution_metric_version"]
            body = json.dumps(inner["payload"], sort_keys=True, allow_nan=False)
            inner["sha256"] = hashlib.sha256(body.encode()).hexdigest()
            p["simulator"] = json.dumps(inner)
        bad = self.rewrite_checkpoint(r.checkpoint(), change)
        with self.assertRaisesRegex(ValueError, "metric checkpoint"):
            Replay.restore(self.input, self.manifest, bad)

    def test_incomplete_partition_cannot_report_or_finish(self):
        r = self.replay(); self.run_to(r, 1)
        with self.assertRaisesRegex(ValueError, "partition_not_exhausted"): r.finish()
        with self.assertRaisesRegex(ValueError, "unfinished_report"): r.report()

    def test_conflicting_older_missing_and_future_events_leave_state_unchanged(self):
        r = self.replay(); self.run_to(r, 2)
        before = r.checkpoint()
        conflict = dict(r.events[1], bid=1.099)
        for event in (conflict, r.events[0], r.events[3], r.fixture["events"][-1]):
            with self.assertRaises(ValueError): r.step(event)
            self.assertEqual(r.checkpoint(), before)

    def test_duplicate_cannot_bypass_strict_types(self):
        r = self.replay(); self.run_to(r, 2)
        with self.assertRaisesRegex(ValueError, "integer_range"):
            r.step(dict(r.events[1], sequence=True))

    def test_repeated_latest_quote_is_retained_but_no_duplicate_execution(self):
        value = fixture()
        value["events"][1] = {**value["events"][0], "sequence": 1, "receipt_msc": value["events"][0]["receipt_msc"] + 500}
        f, m = self.make(value, "repeat")
        r = Replay(f, m); self.run_to(r, 2)
        self.assertEqual(r.repeats, 1)
        self.assertEqual(r.sim.last_tick["sequence"], 1)
        self.assertFalse(r.step(r.events[1]))
        self.assertEqual(r.next_sequence, 2)

    def test_missing_hour_never_forward_fills_or_replays_cross_signal(self):
        value = fixture()
        value["events"] = [e for e in value["events"] if not START + 53 * 3600000 <= e["receipt_msc"] < START + 54 * 3600000]
        for i, e in enumerate(value["events"]): e["sequence"] = i
        f, m = self.make(value, "gap")
        r = Replay(f, m)
        self.run_to(r, 213)
        self.assertIsNone(r.sim.position)
        self.assertFalse(any(d["hour_msc"] == START + 54 * 3600000 for d in r.sim.decisions))
        self.assertFalse(any(b.time.hour == 5 and b.time.day == 3 for b in r.sim.history))

    def test_gap_through_stop_can_exceed_estimated_trade_loss_and_latch_pause(self):
        f, m = self.make(fixture("reversal"), "loss")
        r = Replay(f, m)
        self.run_to(r, 216)
        p = deepcopy(r.sim.position)
        self.assertIsNotNone(p)
        estimate = (abs(p.entry - p.stop) + .00002) * p.lots * 100000 + p.lots * 7
        self.assertLessEqual(estimate, 25 + 1e-8)
        r.step(r.events[216])
        t = r.sim.trades[0]
        self.assertAlmostEqual(t["exit"], r.events[216]["bid"] - .00002)
        self.assertLess(t["net_pnl"], -estimate)
        self.assertTrue(r.sim.paused)
        r.step(r.events[217])
        self.assertTrue(r.sim.paused)

    def test_long_and_short_fill_sides_and_one_position_limit(self):
        for partition, side in (("development", 1), ("validation", -1)):
            r = self.replay(partition=partition)
            self.run_to(r, 216 if side == 1 else 600)
            p = r.sim.position
            self.assertIsNotNone(p)
            self.assertEqual(p.side, side)
            entry_event = r.events[212 if side == 1 else 596]
            quote = entry_event["ask"] if side == 1 else entry_event["bid"]
            self.assertAlmostEqual(p.entry, quote + side * .00002)
            self.assertLessEqual(p.lots, 1.0)
            before = r.sim.checkpoint()
            self.assertFalse(r.step(r.events[r.next_sequence - 1]))
            self.assertEqual(r.sim.checkpoint(), before)

    def test_changed_fixture_bytes_config_or_sources_reject_before_simulator(self):
        for field in ("fixture_sha256", "sources", "scenarios"):
            m = json.loads(self.manifest.read_text())
            m[field] = "changed"
            p = self.root / (field + ".json"); write_new(p, m)
            with patch("forex_demo_lab.shadow_engine_113._CostedTicks") as ctor:
                with self.assertRaisesRegex(ValueError, "frozen_fixture"): Replay(self.input, p)
                ctor.assert_not_called()

    def test_market_json_and_extra_identity_fields_rejected_before_simulation(self):
        for change in ({"kind": "market_declared"}, {"account_id": "not_an_account"}, {"clock": "raw_unverified"}):
            value = fixture(); value.update(change)
            p = self.root / (str(len(list(self.root.iterdir()))) + ".json"); write_new(p, value)
            with patch("forex_demo_lab.shadow_engine_113._CostedTicks") as ctor:
                with self.assertRaises(ValueError): freeze_fixture(p, self.root / "never.json")
                ctor.assert_not_called()

    def test_age_future_source_reversal_crossed_nonfinite_bool_and_sequence_rejected(self):
        for change in ({"source_msc": START - 2001}, {"source_msc": START + 1}, {"bid": 1.2},
                       {"bid": True}, {"sequence": True}, {"sequence": 1}, {"receipt_msc": "bad"}):
            v = fixture(); v["events"][0].update(change)
            p = self.root / (str(len(list(self.root.iterdir()))) + ".json"); write_new(p, v)
            with self.assertRaises(ValueError): load_fixture(p)
        p = self.root / "nan.json"; p.write_text(self.input.read_text().replace('"bid": 1.1', '"bid": NaN', 1))
        with self.assertRaises(ValueError): load_fixture(p)

    def test_same_source_time_changed_and_out_of_order_receipts_reject(self):
        for fields in ({"source_msc": START - 50, "receipt_msc": START + 500, "bid": 1.099},
                       {"source_msc": START - 51, "receipt_msc": START - 1}):
            v = fixture(); v["events"][1].update(fields)
            p = self.root / (str(len(list(self.root.iterdir()))) + ".json"); write_new(p, v)
            with self.assertRaises(ValueError): load_fixture(p)

    def test_size_count_duplicate_json_fields_and_split_boundaries_reject(self):
        big = self.root / "big.json"; big.write_bytes(b" " * (MAX_BYTES + 1))
        with self.assertRaisesRegex(ValueError, "input_size"): load_fixture(big)
        duplicate = self.root / "dup.json"; duplicate.write_text(self.input.read_text().replace('"symbol": "EURUSD"', '"symbol": "EURUSD", "symbol": "EURUSD"'))
        with self.assertRaisesRegex(ValueError, "duplicate_json_field"): load_fixture(duplicate)
        for change in ({"events": []}, {"validation_start_msc": START + 1}, {"development_start_msc": START - 3600000}):
            v = fixture(); v.update(change)
            p = self.root / (str(len(list(self.root.iterdir()))) + ".json"); write_new(p, v)
            with self.assertRaises(ValueError): load_fixture(p)
        v = fixture(); v["events"] = [v["events"][0]] * (MAX_EVENTS + 1)
        p = self.root / "many.json"; write_new(p, v)
        with self.assertRaisesRegex(ValueError, "event_count"): load_fixture(p)

    def test_changed_source_and_fixture_bytes_invalidate_frozen_binding(self):
        self.input.write_bytes(self.input.read_bytes() + b" ")
        with self.assertRaisesRegex(ValueError, "frozen_fixture"):
            self.replay()
        self.input.write_bytes(self.input.read_bytes()[:-1])
        with patch("forex_demo_lab.shadow_engine_113.source_bindings", return_value={"changed": "code"}):
            with self.assertRaisesRegex(ValueError, "frozen_fixture"):
                self.replay()

    def test_public_fixture_event_and_manifest_views_cannot_change_frozen_replay(self):
        r, control = self.replay(), self.replay()
        view = r.events; view[0]["bid"] = .5
        f = r.fixture; f["case"] = "changed"; f["events"][0]["ask"] = 2.0
        m = r.manifest; m["scenarios"]["base"]["spread_floor_pips"] = 100
        self.assertEqual(r.events, control.events)
        self.assertEqual(r.manifest, control.manifest)
        self.assertEqual(r.fixture, control.fixture)
        self.assertEqual(r.run(), control.run())

    def test_existing_artifacts_are_never_overwritten(self):
        before = self.manifest.read_bytes()
        with self.assertRaises(FileExistsError): freeze_fixture(self.input, self.manifest)
        self.assertEqual(self.manifest.read_bytes(), before)
        with self.assertRaises(FileExistsError): write_new(self.input, {})

    def test_native111_complete_stopped_and_partial_never_construct_simulator(self):
        for count, terminal in ((7200, "E"), (1, "S")):
            run = self.root / ("run" + str(count)); run.mkdir()
            for name, data in encode(payloads(count, terminal=terminal, kind="market_declared")):
                (run / name).write_bytes(data)
            with patch("forex_demo_lab.shadow_engine_113._CostedTicks") as ctor:
                result = inspect_capture(run)
                ctor.assert_not_called()
            self.assertEqual(result["status"], "performance_unavailable")
            self.assertNotIn("metrics", result)
            self.assertFalse(result["paper_evaluation_available"])
        partial = self.root / "partial"; partial.mkdir()
        data = encode(payloads(1))[0][1]
        (partial / "Segment111-001.txt").write_bytes(data[:data.find(b"Q\t1")])
        r = inspect_capture(partial)
        self.assertEqual(r["diagnostics"]["pending_attempt"], 1)
        self.assertEqual(r["diagnostics"]["capture_status"], "incomplete")

    def test_107_and109_capture_inspection_never_grants_performance(self):
        p = self.root / "capture.txt"; p.write_bytes(encode107(complete107("market_declared")))
        for fmt in ("107", "109"):
            with patch("forex_demo_lab.shadow_engine_113._CostedTicks") as ctor:
                result = inspect_capture(p, fmt)
                ctor.assert_not_called()
            self.assertEqual(result["status"], "performance_unavailable")

    def test_invented_capture_label_cannot_unlock_native_performance_route(self):
        run = self.root / "label"; run.mkdir()
        for name, data in encode(payloads(1, kind="invented_fixture")):
            (run / name).write_bytes(data)
        with patch("forex_demo_lab.shadow_engine_113._CostedTicks") as ctor:
            result = inspect_capture(run)
            ctor.assert_not_called()
        self.assertTrue(result["diagnostics"]["synthetic"])
        self.assertFalse(result["paper_evaluation_available"])

    def test_cli_roundtrip_fixed_error_and_output_immutability(self):
        cli = ROOT / "scripts/shadow-engine-113.py"
        def call(*args):
            return subprocess.run([sys.executable, str(cli), *map(str, args)], capture_output=True, text=True, timeout=20)
        out = self.root / "cli.json"
        r = call("evaluate", self.input, self.manifest, out)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(json.loads(r.stdout)["kind"], "invented_software_check")
        before = out.read_bytes()
        r = call("evaluate", self.input, self.manifest, out)
        self.assertEqual(r.returncode, 1)
        self.assertEqual(out.read_bytes(), before)
        self.assertNotIn(str(self.root), r.stdout + r.stderr)


if __name__ == "__main__":
    unittest.main()
