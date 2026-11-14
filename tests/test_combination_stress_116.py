from copy import deepcopy
from dataclasses import asdict
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from forex_demo_lab.combination_stress_116 import (
    ACCEPTED, REJECTED, RULES, Replay, bound_matrix, create_matrix, definitions,
    evaluate_matrix, fault_checkpoint, restore_checked, scenarios, write_new,
)
from forex_demo_lab.fill_audit_116 import audit
from forex_demo_lab.stress_fixture_116 import HOUR, START, fixture_bytes, invented
from forex_demo_lab.strategy_combination_115 import freeze_fixture, load_fixture
from forex_demo_lab.model import Config
from forex_demo_lab.shadow_engine_113 import _canonical, _digest
from test_strategy_combination_115 import ReferenceTicks
from test_forward_capture_111 import encode, payloads

ROOT = Path(__file__).resolve().parents[1]


class Stress116Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.temp.name)
        cls.directory = cls.root / "matrix"
        cls.manifest = create_matrix(cls.directory)
        cls.result = evaluate_matrix(cls.directory, cls.root / "matrix-report.json")

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def replay(self, case="control", scenario="base", partition="development", rule="AGREE2"):
        return Replay(self.directory / (case + ".json"), self.directory / (case + "-frozen.json"),
                      scenario, partition, rule)

    def row(self, case="control", scenario="base", partition="development", rule="AGREE2"):
        return next(r for r in self.result["results"] if
                    (r["case"], r["scenario"], r["partition"], r["rule"]) == (case, scenario, partition, rule))

    def held_prefix(self, case="control", partition="development"):
        run = self.replay(case, partition=partition)
        threshold = START + (203 if partition == "development" else 491) * HOUR
        for event in run.events:
            run.step(event)
            if event["receipt_msc"] >= threshold:
                break
        return run

    def checked(self, run, cp=None, **kw):
        return restore_checked(self.directory / (run.fixture["case"] + ".json"),
                               self.directory / (run.fixture["case"] + "-frozen.json"),
                               cp or run.checkpoint(), run.scenario, run.partition, kw.get("rule", run.rule))

    def assert_bad_audit(self, change, reason):
        run = self.replay()
        report = {**run.run(), "evaluation_start_msc": run.start}
        change(report)
        with self.assertRaisesRegex(ValueError, reason):
            audit(report, run.events, run.sim.config)

    def test_all_matrix_results_and_rejections_retained(self):
        self.assertTrue(self.result["verification_passed"], self.result["failures"])
        self.assertEqual(len(self.result["results"]), 96)
        self.assertEqual(len(self.result["rejected_inputs"]), 9)
        self.assertEqual(len(self.result["checkpoint_faults"]), 576)
        self.assertTrue(all(r["metrics"] is None for r in self.result["rejected_inputs"]))
        self.assertEqual({r["case"] for r in self.result["rejected_inputs"]}, set(REJECTED))

    def test_all_paths_against_retained_engine_independent_agreement(self):
        for case in ACCEPTED:
            for scenario in ("base", "adverse"):
                for partition in ("development", "validation"):
                    for rule in RULES:
                        with self.subTest(case=case, scenario=scenario, partition=partition, rule=rule):
                            row = self.row(case, scenario, partition, rule)
                            self.assertEqual(row["status"], "accepted", row)
                            run = self.replay(case, scenario, partition, rule)
                            ref = ReferenceTicks(run.sim.config, rule)
                            ref.evaluation_start_msc = run.start
                            for event in run.events:
                                ref.step_tick(run._tick(event))
                            ref.finish()
                            self.assertEqual(row["trades"], ref.trades)
                            self.assertEqual(row["metrics"], ref.metrics())
                            self.assertEqual(row["cost_audit"], ref.cost_audit)
                            self.assertEqual(row["fill_lineage"], ref.fill_lineage)
                            self.assertEqual(row["independent_audit"]["final_paused"], ref.paused)

    def test_all_restarts_equal_and_duplicates_idempotent(self):
        self.assertTrue(all(r.get("restart_equal") and r.get("duplicate_idempotent")
                            for r in self.result["results"]), self.result["failures"])

    def test_all_checkpoint_faults_rejected(self):
        self.assertTrue(all(r["passed"] for r in self.result["checkpoint_faults"]))
        self.assertEqual({r["fault"] for r in self.result["checkpoint_faults"]},
                         set(definitions()["checkpoint_faults"]))

    def test_wide_spread_blocks_new_entries(self):
        row = self.row("wide_entry")
        self.assertGreater(row["metrics"]["spread_rejections"], 0)
        for link in row["fill_lineage"]:
            event = self.replay("wide_entry").events[link["entry_sequence"]]
            self.assertFalse(201 <= (event["receipt_msc"] - START) // HOUR <= 227)

    def test_wide_held_short_exits_on_ask(self):
        base, wide = self.row(partition="validation"), self.row("wide_short", partition="validation")
        self.assertEqual(base["trades"][0]["side"], -1)
        self.assertLess(wide["fill_lineage"][0]["exit_sequence"], base["fill_lineage"][0]["exit_sequence"])
        self.assertEqual(wide["trades"][0]["reason"], "stop_tick")

    def test_both_gap_losses_exceed_entry_estimate(self):
        for case, partition in (("gap_down_long", "development"), ("gap_up_short", "validation")):
            row = self.row(case, partition=partition)
            self.assertTrue(any(r["loss_exceeds_entry_budget"] for r in row["independent_audit"]["trades"]))
            self.assertTrue(row["restart_state"]["daily_pause_active"])

    def test_calendar_outage_retains_time_and_financing(self):
        value = invented("calendar_outage")
        self.assertEqual(len(value["events"]), 2304 - 151 * 4)
        pair = (value["events"][1199], value["events"][1200])
        self.assertGreater(pair[1]["receipt_msc"] - pair[0]["receipt_msc"], 151 * HOUR)
        row = self.row("calendar_outage", partition="validation")
        days = row["independent_audit"]["trades"][0]["financing_days"]
        self.assertTrue(any(d["multiplier"] == 3 for d in days))
        self.assertTrue(any(d["multiplier"] == 0 for d in days))
        self.assertLess(row["trades"][0]["swap"], 0)

    def test_missing_previous_hour_suppresses_stale_entry(self):
        row = self.row("missing_previous_hour")
        self.assertFalse(any(a["entry_decision"]["hour_msc"] == START + 202 * HOUR
                             for a in row["trade_arbitration"]))

    def test_repeats_preserved_without_duplicate_positions(self):
        row = self.row("repeated_quote")
        self.assertEqual(row["repeated_latest_quotes"], 1)
        self.assertEqual(self.row("repeated_quote", partition="validation")["repeated_latest_quotes"], 2)
        self.assertEqual(row["trades"], self.row()["trades"])

    def test_cash_never_places_synthetic_orders(self):
        rows = [r for r in self.result["results"] if r["rule"] == "CASH"]
        self.assertEqual(len(rows), 32)
        self.assertTrue(all(r["metrics"]["net_pnl"] == 0 and not r["trades"] for r in rows))
        self.assertFalse(self.result["orders_available"])
        self.assertFalse(self.result["market_validation"])
        self.assertIsNone(self.result["aggregate_portfolio_result"])

    def test_rehashed_balance_rejected(self):
        run = self.held_prefix()
        with self.assertRaisesRegex(ValueError, "reconstructed_checkpoint_state_mismatch"):
            self.checked(run, fault_checkpoint(run.checkpoint(), "rehashed_balance"))

    def test_rehashed_stop_rejected(self):
        run = self.held_prefix()
        self.assertIsNotNone(run.sim.position)
        with self.assertRaisesRegex(ValueError, "reconstructed_checkpoint_state_mismatch"):
            self.checked(run, fault_checkpoint(run.checkpoint(), "rehashed_protection"))

    def test_duplicate_inner_checkpoint_fields_rejected(self):
        run = self.held_prefix()
        value = json.loads(run.checkpoint())
        inner = value["payload"]["simulator"]
        self.assertIn('"balance": ', inner)
        value["payload"]["simulator"] = inner.replace('"balance": ', '"balance": -1.0, "balance": ', 1)
        value["sha256"] = _digest(_canonical(value["payload"]))
        with self.assertRaisesRegex(ValueError, "duplicate_json_field"):
            self.checked(run, json.dumps(value))

    def test_paused_checkpoint_restores_gap_loss(self):
        run = self.held_prefix("gap_down_long")
        self.assertTrue(run.sim.paused)
        self.assertIsNone(run.sim.position)
        restored = self.checked(run)
        self.assertTrue(restored.sim.paused)
        self.assertEqual(run.run(), restored.run())

    def test_rehashed_pause_rejected(self):
        run = self.held_prefix("gap_down_long")
        with self.assertRaisesRegex(ValueError, "reconstructed_checkpoint_state_mismatch"):
            self.checked(run, fault_checkpoint(run.checkpoint(), "rehashed_protection"))

    def test_zero_cursor_restore(self):
        run = self.replay()
        restored = self.checked(run)
        self.assertEqual(restored.next_sequence, 0)
        self.assertEqual(run.run(), restored.run())

    def test_prefix_restore_reads_no_future_steps(self):
        run = self.held_prefix()
        calls = []
        original = Replay.step
        def record(obj, event):
            calls.append(event["sequence"])
            return original(obj, event)
        with patch.object(Replay, "step", record):
            self.checked(run)
        self.assertEqual(calls, list(range(run.next_sequence)))

    def test_audit_rejects_wrong_fill(self):
        self.assert_bad_audit(lambda r: r["trades"][0].update(exit=r["trades"][0]["exit"] + .001), "exit")

    def test_audit_rejects_wrong_lots(self):
        self.assert_bad_audit(lambda r: r["trades"][0].update(lots=1.0), "lots")

    def test_audit_rejects_wrong_financing(self):
        self.assert_bad_audit(lambda r: r["trades"][-1].update(swap=0), "swap")

    def test_audit_rejects_wrong_equity(self):
        self.assert_bad_audit(lambda r: r["metrics"].update(max_tick_drawdown=.9), "metric_max_tick_drawdown")

    def test_audit_rejects_overlapping_positions(self):
        self.assert_bad_audit(lambda r: r["fill_lineage"][1].update(entry_sequence=0), "one_position")

    def test_invalid_inputs_reject_before_engine(self):
        for case, expected in REJECTED.items():
            with self.subTest(case=case), patch("forex_demo_lab.strategy_combination_115._CombinationTicks",
                                               side_effect=AssertionError("engine_unavailable")):
                with self.assertRaisesRegex(ValueError, expected):
                    load_fixture(self.directory / (case + ".json"))

    def test_changed_input_rejects_before_engine(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp) / "matrix"
            create_matrix(directory)
            path = directory / "control.json"
            value = json.loads(path.read_bytes())
            value["events"][-1]["bid"] -= .00001
            path.write_text(json.dumps(value))
            with patch("forex_demo_lab.combination_stress_116.Replay", side_effect=AssertionError("engine")):
                with self.assertRaisesRegex(ValueError, "fixed_transformation_changed"):
                    bound_matrix(directory)

    def test_changed_source_rejects_before_engine(self):
        from forex_demo_lab.combination_stress_116 import sources
        wrong = sources(); wrong[next(iter(wrong))] = "0" * 64
        with patch("forex_demo_lab.combination_stress_116.sources", return_value=wrong):
            with self.assertRaisesRegex(ValueError, "frozen_matrix_input_code_or_definitions_changed"):
                bound_matrix(self.directory)

    def test_report_overwrite_rejects_before_replay(self):
        path = self.root / "matrix-report.json"
        before = path.read_bytes()
        with patch("forex_demo_lab.combination_stress_116.bound_matrix", side_effect=AssertionError("replay")):
            with self.assertRaisesRegex(ValueError, "existing_artifact"):
                evaluate_matrix(self.directory, path)
        self.assertEqual(before, path.read_bytes())

    def test_symlink_input_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "input.json"
            path.symlink_to(self.directory / "control.json")
            with self.assertRaisesRegex(ValueError, "invalid_input_file"):
                load_fixture(path)

    def test_native_capture_is_inspect_only(self):
        from forex_demo_lab.combination_stress_116 import inspect_capture
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp) / "Run111-1700000000-100-200"
            directory.mkdir()
            # The retained111 encoder creates an invented diagnostic stream.
            for name, raw in encode(payloads()):
                (directory / name).write_bytes(raw)
            with patch("forex_demo_lab.combination_stress_116.Replay", side_effect=AssertionError("engine")):
                value = inspect_capture(directory)
            self.assertFalse(value["paper_evaluation_available"])
            self.assertFalse(value["orders_available"])
            self.assertEqual(value["status"], "performance_unavailable")

    def test_cli_refuses_missing_input_without_traceback(self):
        result = subprocess.run([sys.executable, str(ROOT / "scripts/combination-stress-116.py"),
                                 "evaluate", str(self.root / "absent"), str(self.root / "absent-output.json")],
                                text=True, capture_output=True, check=False)
        self.assertEqual(result.returncode, 1)
        self.assertFalse(json.loads(result.stdout)["accepted"])
        self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()
