from copy import deepcopy
from dataclasses import asdict
from decimal import Decimal
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from forex_demo_lab import daily_features_118 as daily
from forex_demo_lab.daily_risk_119 import Replay, _propose, freeze_fixture, profiles, validate_fixture
from forex_demo_lab.daily_risk_fixture_119 import CASES, fixture
from test_daily_features_118 import reline

ROOT = Path(__file__).resolve().parents[1]


def independent_size(feature, event, name):
    """Rational sizing independent of production Decimal operations and Config."""
    f = lambda v: Fraction(str(v))
    slip, fee, floor = (f(.00002), f(7), f(0)) if name == "base" else (f(.00005), f(10), f(.00012))
    spread = max(f(event["ask"]) - f(event["bid"]), floor)
    entry = f(event["bid"]) + spread + slip if feature.side == 1 else f(event["bid"]) - slip
    distance = f(feature.stop_distance)
    budget = f(event["equity_usd"]) * f(.0025) * f(feature.risk_multiplier)
    per_lot = (distance + slip) * 100000 + fee
    margin = entry * 100000 / 30
    upper = min(budget / per_lot, f(event["free_margin_usd"]) / (margin + fee / 2), f(1))
    lots = Fraction(int(upper * 100), 100)
    return lots, entry, budget, lots * per_lot, lots * margin, lots * fee / 2, lots * ((spread + 2 * slip) * 100000 + fee)


class Risk119Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.serial = 0

    def bundle(self, value=None):
        self.serial += 1
        path = self.root / f"fixture{self.serial}.json"
        manifest = self.root / f"frozen{self.serial}.json"
        daily.write_new(path, fixture() if value is None else value)
        freeze_fixture(path, manifest)
        return path, manifest

    def replay(self, case="full_long", profile="base", candidate="MIX50_D"):
        return Replay(*self.bundle(fixture(case)), profile, candidate)

    def reject(self, value, reason):
        with self.assertRaisesRegex(ValueError, "^" + reason + "$"):
            validate_fixture(value)

    def rewrite(self, checkpoint, change):
        value = json.loads(checkpoint)
        change(value["payload"])
        value["sha256"] = daily._digest(value["payload"])
        return json.dumps(value)

    def direct(self, equity=10000., margin=10000., multiplier=1., side=1, distance=.001,
               bid=1.1, ask=1.1001, profile="base", floor=9900.):
        signal = SimpleNamespace(side=side, risk_multiplier=multiplier, stop_distance=distance, target_session_id=1)
        event = {"equity_usd": equity, "free_margin_usd": margin, "bid": bid, "ask": ask,
                 "source_msc": 1, "receipt_msc": 2, "sequence": 0}
        return _propose(signal, event, profiles()[profile], "MIX50_D", "test_binding", floor)

    def test_all_fixed_cases_validate(self):
        self.assertEqual(len(CASES), 22)
        for case in CASES:
            with self.subTest(case=case):
                validate_fixture(fixture(case))

    def test_full_and_half_risk_golden_values(self):
        full, reason = self.direct()
        half, _ = self.direct(multiplier=.5)
        self.assertEqual(reason, "proposal_reserved")
        self.assertEqual((full["lots"], full["risk_budget_usd"], full["estimated_stop_risk_usd"]), (.22, 25., 23.98))
        self.assertEqual((half["lots"], half["risk_budget_usd"], half["estimated_stop_risk_usd"]), (.11, 12.5, 11.99))
        self.assertEqual(full["immediate_liquidation_debit_usd"], 4.62)
        self.assertEqual((full["entry_estimate"], full["stop"], full["target"]), (1.10012, 1.09912, 1.10212))

    def test_adverse_and_short_golden_values(self):
        proposal, _ = self.direct(profile="adverse", side=-1)
        self.assertEqual((proposal["lots"], proposal["estimated_stop_risk_usd"]), (.21, 24.15))
        self.assertEqual((proposal["entry_estimate"], proposal["stop"], proposal["target"]), (1.09995, 1.10095, 1.09795))
        self.assertEqual(proposal["effective_spread_pips"], 1.2)
        self.assertEqual(proposal["immediate_liquidation_debit_usd"], 6.72)

    def test_independent_rational_sizing_for_actual_features(self):
        for case in ("full_long", "half_long", "full_short", "half_short"):
            value = fixture(case)
            for profile in ("base", "adverse"):
                with self.subTest(case=case, profile=profile):
                    obj = Replay(*self.bundle(value), profile)
                    obj.step(value["events"][0])
                    proposal = obj.state["reservation"]
                    feature = daily.decisions(value["features"])["MIX50_D"]
                    expected = independent_size(feature, value["events"][0], profile)
                    for key, number in zip(["lots", "entry_estimate", "risk_budget_usd", "estimated_stop_risk_usd",
                                            "estimated_margin_usd", "entry_fee_estimate_usd", "immediate_liquidation_debit_usd"], expected):
                        self.assertAlmostEqual(proposal[key], float(number), delta=1e-9)

    def test_independent_hypothetical_stop_debit_includes_exit_fee_slip(self):
        for side in (-1, 1):
            proposal, _ = self.direct(side=side)
            d = lambda x: Decimal(str(x))
            exit_estimate = d(proposal["stop"]) - side * Decimal(".00002")
            debit = side * (d(proposal["entry_estimate"]) - exit_estimate) * d(proposal["lots"]) * 100000 + d(proposal["lots"]) * 7
            self.assertEqual(debit, d(proposal["estimated_stop_risk_usd"]))
            self.assertLessEqual(debit, d(proposal["risk_budget_usd"]))

    def test_risk_minimum_exact_boundary_and_no_round_up(self):
        proposal, _ = self.direct(equity=436., margin=436., floor=0.)
        self.assertEqual(proposal["lots"], .01)
        proposal, reason = self.direct(equity=math.nextafter(436., 0), margin=400., floor=0.)
        self.assertIsNone(proposal)
        self.assertEqual(reason, "minimum_lot_risk")

    def test_margin_minimum_exact_boundary_and_no_round_up(self):
        proposal, _ = self.direct(margin=40.035, bid=1.19988, ask=1.19998)
        self.assertEqual(proposal["lots"], .01)
        proposal, reason = self.direct(margin=math.nextafter(40.035, 0), bid=1.19988, ask=1.19998)
        self.assertIsNone(proposal)
        self.assertEqual(reason, "minimum_lot_margin")

    def test_negative_margin_abstains(self):
        proposal, reason = self.direct(margin=-1.)
        self.assertIsNone(proposal)
        self.assertEqual(reason, "minimum_lot_margin")

    def test_maximum_one_lot_and_one_budget(self):
        result = self.replay("max_lot").run()
        proposal = result["final_state"]["reservation"]
        self.assertEqual(proposal["lots"], 1.)
        self.assertLessEqual(proposal["estimated_stop_risk_usd"], proposal["risk_budget_usd"])
        self.assertEqual(sum(o["proposal"] is not None for o in result["outcomes"]), 1)

    def test_zero_cash_opposing_warmup_and_range_risk(self):
        for case, candidate in [("full_long", "CASH"), ("opposing", "MIX50_D"),
                                ("warmup", "MIX50_D"), ("zero_range", "MIX50_D")]:
            with self.subTest(case=case, candidate=candidate):
                report = self.replay(case, candidate=candidate).run()
                self.assertIsNone(report["final_state"]["reservation"])
                self.assertEqual(report["outcomes"][0]["reason"], "inactive_signal")

    def test_invalid_private_sizing_signal_rejected(self):
        for kw in ({"multiplier": 0}, {"multiplier": 2}, {"multiplier": True}, {"side": True}, {"distance": 0}):
            with self.assertRaisesRegex(ValueError, "proposal_signal"):
                self.direct(**kw)

    def test_price_geometry_and_spread_stop_boundary(self):
        proposal, reason = self.direct(distance=.00012)
        self.assertEqual((proposal, reason), (None, "price_geometry"))
        proposal, reason = self.direct(distance=2.)
        self.assertEqual((proposal, reason), (None, "price_geometry"))

    def test_wide_then_valid_does_not_consume_early(self):
        result = self.replay("wide_then_valid").run()
        self.assertEqual([o["reason"] for o in result["outcomes"]], ["wide_quote", "proposal_reserved", "session_consumed"])

    def test_stale_then_valid_does_not_consume_early(self):
        result = self.replay("stale_then_valid").run()
        self.assertEqual([o["reason"] for o in result["outcomes"]], ["stale_quote", "proposal_reserved", "session_consumed"])

    def test_strict_after_feature_boundary(self):
        result = self.replay("before_then_valid").run()
        self.assertEqual([o["reason"] for o in result["outcomes"]], ["before_feature", "proposal_reserved", "session_consumed"])

    def test_age_2000_inclusive(self):
        value = fixture()
        value["events"] = value["events"][:1]
        value["events"][0]["receipt_msc"] = value["events"][0]["source_msc"] + 2000
        result = Replay(*self.bundle(value)).run()
        self.assertEqual(result["outcomes"][0]["reason"], "proposal_reserved")

    def test_spread_cap_inclusive_without_float_tolerance(self):
        value = fixture()
        value["events"] = value["events"][:1]
        value["events"][0].update(bid=1.0, ask=1.00015)
        result = Replay(*self.bundle(value)).run()
        self.assertEqual(result["outcomes"][0]["reason"], "proposal_reserved")
        value["events"][0]["ask"] = math.nextafter(1.00015, math.inf)
        result = Replay(*self.bundle(value)).run()
        self.assertEqual(result["outcomes"][0]["reason"], "wide_quote")

    def test_closed_quote_not_consumed(self):
        result = self.replay("closed_then_valid").run()
        self.assertEqual([o["reason"] for o in result["outcomes"]], ["closed_quote", "proposal_reserved"])

    def test_stale_feature_not_consumed(self):
        result = self.replay("stale_feature").run()
        self.assertEqual([o["reason"] for o in result["outcomes"]], ["wide_quote", "stale_feature", "proposal_reserved"])

    def test_repeated_source_updates_no_second_proposal(self):
        result = self.replay("repeated_source").run()
        self.assertEqual([o["reason"] for o in result["outcomes"]], ["proposal_reserved", "repeated_source", "session_consumed"])

    def test_exact_latest_event_replay_idempotent(self):
        value = fixture()
        obj = Replay(*self.bundle(value))
        obj.step(value["events"][0])
        state = obj.state
        self.assertFalse(obj.step(deepcopy(value["events"][0])))
        self.assertEqual(obj.state, state)

    def test_altered_or_unbound_event_rejected_without_state_change(self):
        value = fixture()
        obj = Replay(*self.bundle(value))
        obj.step(value["events"][0])
        state = obj.state
        bad = deepcopy(value["events"][0]);bad["bid"] = 1.0
        with self.assertRaisesRegex(ValueError, "event_binding"):
            obj.step(bad)
        self.assertEqual(obj.state, state)

    def test_session_identity_changes_rejected_transactionally(self):
        value = fixture()
        value["events"][1]["feature_decision_msc"] += 1
        obj = Replay(*self.bundle(value))
        obj.step(value["events"][0])
        state = obj.state
        with self.assertRaisesRegex(ValueError, "session_identity_changed"):
            obj.step(value["events"][1])
        self.assertEqual(obj.state, state)

    def test_reservation_blocks_a_later_session_and_stays_unchanged(self):
        obj = self.replay("reservation_next_session")
        report = obj.run()
        self.assertEqual([o["reason"] for o in report["outcomes"]], ["proposal_reserved", "reserved_entry_slot"])
        self.assertEqual(report["outcomes"][1]["risk_multiplier"], .5)
        self.assertEqual(report["final_state"]["reservation"], report["outcomes"][0]["proposal"])

    def test_held_side_size_stop_target_unchanged_when_signal_changes(self):
        value = fixture("held_signal_change")
        report = Replay(*self.bundle(value)).run()
        self.assertEqual(report["final_state"]["held"], value["initial_account"]["held"])
        self.assertIsNone(report["final_state"]["reservation"])
        self.assertEqual([o["reason"] for o in report["outcomes"]], ["held_position", "held_position"])
        self.assertEqual(report["outcomes"][1]["risk_multiplier"], .5)

    def test_pause_exact_one_percent_and_same_day_recovery_latched(self):
        report = self.replay("pause_recovery").run()
        self.assertEqual([o["reason"] for o in report["outcomes"]], ["daily_pause", "session_consumed"])
        self.assertTrue(all(o["paused"] for o in report["outcomes"]))
        self.assertIsNone(report["final_state"]["reservation"])

    def test_open_loss_mark_latches_pause_without_computing_fill(self):
        report = self.replay("open_loss").run()
        self.assertTrue(report["final_state"]["paused"])
        self.assertEqual(report["positions_created"], 0)
        self.assertIsNone(report["fills"])

    def test_gap_uses_prior_mark_not_current_mark_as_anchor(self):
        report = self.replay("gap_pause").run()
        self.assertEqual(report["outcomes"][1]["day_start_equity"], 10000.)
        self.assertEqual(report["outcomes"][1]["reason"], "daily_pause")
        self.assertTrue(report["outcomes"][1]["paused"])

    def test_new_source_day_resets_pause_with_prior_anchor(self):
        value = fixture("gap_pause")
        value["events"][0].update(equity_usd=9900., free_margin_usd=9900., ask=1.1001)
        value["events"][1].update(equity_usd=9900., free_margin_usd=9900.)
        report = Replay(*self.bundle(value)).run()
        self.assertEqual(report["outcomes"][0]["reason"], "daily_pause")
        self.assertEqual(report["outcomes"][1]["day_start_equity"], 9900.)
        self.assertFalse(report["outcomes"][1]["paused"])
        self.assertEqual(report["outcomes"][1]["reason"], "proposal_reserved")

    def test_daily_headroom_abstention_consumes_opportunity(self):
        report = self.replay("daily_headroom").run()
        self.assertEqual([o["reason"] for o in report["outcomes"]], ["daily_headroom", "session_consumed"])
        self.assertFalse(report["outcomes"][0]["paused"])

    def test_immediate_liquidation_at_threshold_rejected(self):
        proposal, reason = self.direct(floor=Decimal("9995.38"))
        self.assertEqual((proposal, reason), (None, "daily_headroom"))
        self.assertIsNotNone(self.direct(floor=Decimal("9995.379999"))[0])

    def test_margin_or_minimum_risk_failure_consumes_opportunity(self):
        for case, first in [("minimum_risk", "minimum_lot_risk"), ("minimum_margin", "minimum_lot_margin")]:
            report = self.replay(case).run()
            self.assertEqual([o["reason"] for o in report["outcomes"]], [first, "session_consumed"])

    def test_no_loss_recovery_stake_increase(self):
        high, _ = self.direct(equity=10000., floor=0.)
        low, _ = self.direct(equity=9500., floor=0.)
        self.assertEqual(high["risk_fraction"], low["risk_fraction"])
        self.assertLess(low["risk_budget_usd"], high["risk_budget_usd"])
        self.assertLessEqual(low["lots"], high["lots"])

    def test_negative_gap_marks_cannot_propose(self):
        value = fixture()
        value["events"][0].update(equity_usd=-1000., free_margin_usd=-1000.)
        report = Replay(*self.bundle(value)).run()
        self.assertTrue(report["outcomes"][0]["paused"])
        self.assertIsNone(report["final_state"]["reservation"])

    def test_future_marks_and_quotes_do_not_change_prefix_outcome(self):
        first = fixture()
        second = deepcopy(first)
        second["events"][1].update(equity_usd=500., free_margin_usd=500., bid=1.0, ask=1.0001)
        a, b = Replay(*self.bundle(first)), Replay(*self.bundle(second))
        a.step(first["events"][0]);b.step(second["events"][0])
        self.assertEqual(a.state, b.state)
        self.assertFalse(a.state["paused"])

    def test_future_daily_prices_do_not_change_prefix_proposal(self):
        first, second = fixture(), fixture()
        bar = second["features"]["bars"][-1]
        bar.update(open=2., high=2.1, low=1.9, close=2.)
        reline(second["features"], bar)
        a, b = Replay(*self.bundle(first)), Replay(*self.bundle(second))
        a.step(first["events"][0]);b.step(second["events"][0])
        self.assertEqual(a.state, b.state)

    def test_future_feature_request_rejected_before_arithmetic(self):
        value = fixture()
        value["events"][0]["feature_decision_msc"] = value["events"][0]["receipt_msc"] + 1
        self.reject(value, "future_feature_request")

    def test_missing_completed_trading_session_not_filled(self):
        value = fixture("gap_pause")
        # Remove a completed future bar not used by the old default target.
        value["events"][1]["target_session_id"] = value["features"]["target_session_id"]
        value["events"][1]["feature_decision_msc"] = value["features"]["decision_msc"]
        del value["features"]["bars"][254]
        self.reject(value, "missing_completed_session")

    def test_fake_decision_field_not_accepted(self):
        value = fixture()
        value["events"][0]["decision"] = {"side": 1, "risk_multiplier": 1}
        self.reject(value, "event_fields")

    def test_demo_guard_real_contest_boolean_unknown(self):
        for mode in (1, 2, True, False, "demo", None):
            value = fixture();value["initial_account"]["trade_mode"] = mode
            self.reject(value, "synthetic_demo_account_required")

    def test_server_name_or_qualification_flag_no_escape(self):
        value = fixture();value["initial_account"]["server"] = "Demo"
        self.reject(value, "account_fields")
        value = fixture();value["qualified"] = True
        self.reject(value, "risk_fixture_fields")

    def test_native_historical_labels_and_clock_rejected(self):
        for field, label in [("kind", "native_capture"), ("kind", "historical_data"), ("clock", "broker_clock")]:
            value = fixture();value[field] = label
            self.reject(value, "invented_risk_fixture_required")

    def test_sequence_clock_price_conflicts_and_boolean_fields(self):
        cases = [("sequence", 2, "event_sequence"), ("source_msc", True, "event_time"),
                 ("bid", True, "quote_price"), ("bid", float("nan"), "quote_price"),
                 ("equity_usd", True, "account_money"), ("target_session_id", True, "target_session_id")]
        for field, change, reason in cases:
            value = fixture();value["events"][0][field] = change
            self.reject(value, reason)
        value = fixture();value["events"][1]["source_msc"] = value["events"][0]["source_msc"]
        value["events"][1]["bid"] = 1.0
        self.reject(value, "source_price_conflict")

    def test_clock_reversal_crossed_quote_and_receipt_before_source(self):
        value = fixture();value["events"][1]["source_msc"] = value["events"][0]["source_msc"] - 1
        self.reject(value, "event_order")
        value = fixture();value["events"][0]["receipt_msc"] = value["events"][0]["source_msc"] - 1
        self.reject(value, "quote_clock")
        value = fixture();value["events"][0]["ask"] = 1.0
        self.reject(value, "quote_price")

    def test_initial_account_unavailable_currency_and_money(self):
        value = fixture();value["initial_account"]["available_msc"] = value["events"][0]["source_msc"] + 1
        self.reject(value, "account_unavailable")
        value = fixture();value["initial_account"]["currency"] = "EUR"
        self.reject(value, "invented_USD_account_required")
        value = fixture();value["events"][0]["free_margin_usd"] = 10001.
        self.reject(value, "free_margin_exceeds_equity")
        value = fixture();value["initial_account"]["equity_usd"] = 1e10
        self.reject(value, "account_money")

    def test_invalid_held_volume_geometry_and_availability(self):
        for field, change, reason in [("lots", .015, "held_volume"), ("lots", 1.1, "held_volume"),
                                      ("side", True, "held_side"), ("stop", 1.3, "held_geometry")]:
            value = fixture("open_loss");value["initial_account"]["held"][field] = change
            self.reject(value, reason)
        value = fixture("open_loss")
        value["initial_account"]["held"]["opened_msc"] = value["initial_account"]["available_msc"] + 1
        self.reject(value, "held_unavailable")

    def test_current_state_and_returned_report_cannot_mutate_backend(self):
        obj = self.replay();report = obj.run();expected = obj.state
        report["final_state"]["reservation"]["lots"] = 99
        copied = obj.state;copied["paused"] = True
        self.assertEqual(obj.state, expected)

    def test_prefix_restart_equals_uninterrupted(self):
        for case in ("full_long", "pause_recovery", "open_loss", "gap_pause"):
            path, manifest = self.bundle(fixture(case))
            obj = Replay(path, manifest)
            obj.step(fixture(case)["events"][0])
            resumed = Replay.restore(path, manifest, obj.checkpoint())
            self.assertEqual(resumed.run(), Replay(path, manifest).run())

    def test_finished_restart_and_latest_replay_equal(self):
        path, manifest = self.bundle()
        obj = Replay(path, manifest);expected = obj.run()
        resumed = Replay.restore(path, manifest, obj.checkpoint())
        self.assertFalse(resumed.step(fixture()["events"][-1]))
        self.assertEqual(resumed.report(), expected)

    def test_restore_replays_only_observed_prefix(self):
        value = fixture("reservation_next_session")
        path, manifest = self.bundle(value)
        obj = Replay(path, manifest);obj.step(value["events"][0])
        calls = [];original = Replay.step
        def count(instance, event):
            calls.append(event["sequence"])
            return original(instance, event)
        with patch.object(Replay, "step", count):
            resumed = Replay.restore(path, manifest, obj.checkpoint())
        self.assertEqual(calls, [0])
        self.assertEqual(resumed.state, obj.state)

    def test_rehashed_state_tampering_rejected(self):
        value = fixture();path, manifest = self.bundle(value)
        obj = Replay(path, manifest);obj.step(value["events"][0]);checkpoint = obj.checkpoint()
        changes = [lambda p:p["state"].update(paused=True), lambda p:p["state"].update(day_start_equity=9999.),
                   lambda p:p["state"].update(previous_equity=9999.), lambda p:p["state"].update(consumed_sessions=[]),
                   lambda p:p["state"]["reservation"].update(lots=.9),
                   lambda p:p["state"]["reservation"].update(stop=.1),
                   lambda p:p["state"]["outcomes"][0].update(reason="inactive_signal"),
                   lambda p:p["state"].update(cursor=True)]
        for change in changes:
            with self.assertRaisesRegex(ValueError, "checkpoint_reconstructed_state"):
                Replay.restore(path, manifest, self.rewrite(checkpoint, change))

    def test_checkpoint_boolean_cursor_cross_candidate_profile_and_checksum(self):
        path, manifest = self.bundle()
        obj = Replay(path, manifest);obj.step(fixture()["events"][0]);checkpoint = obj.checkpoint()
        with self.assertRaisesRegex(ValueError, "checkpoint_cursor"):
            Replay.restore(path, manifest, self.rewrite(checkpoint, lambda p:p.update(cursor=True)))
        for profile, candidate in [("adverse", "MIX50_D"), ("base", "CASH")]:
            with self.assertRaisesRegex(ValueError, "checkpoint_binding"):
                Replay.restore(path, manifest, checkpoint, profile, candidate)
        value = json.loads(checkpoint);value["sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "checkpoint_binding"):
            Replay.restore(path, manifest, json.dumps(value))

    def test_wrong_fixture_or_manifest_after_freeze_rejected(self):
        path, manifest = self.bundle();path.write_bytes(path.read_bytes() + b"\n")
        with self.assertRaisesRegex(ValueError, "risk_freeze_binding"):
            Replay(path, manifest)

    def test_rule_boolean_substitution_and_bad_freeze_time_rejected(self):
        path, manifest = self.bundle();original = json.loads(manifest.read_text())
        value = deepcopy(original);value["rules"]["proposal_reservations_released"] = 0
        manifest.write_text(json.dumps(value))
        with self.assertRaisesRegex(ValueError, "risk_freeze_binding"):
            Replay(path, manifest)
        value = deepcopy(original);value["frozen_at_utc"] = "2001-01-01T00:00:00"
        manifest.write_text(json.dumps(value))
        with self.assertRaisesRegex(ValueError, "freeze_time"):
            Replay(path, manifest)

    def test_strict_json_duplicate_and_nonfinite_constants(self):
        raw = json.dumps(fixture())
        for body, reason in [(raw.replace('"format":', '"format": "x", "format":', 1), "duplicate_json_field"),
                             (raw.replace('"equity_usd": 10000.0', '"equity_usd": NaN', 1), "nonfinite_json")]:
            path = self.root / "bad.json";path.write_text(body)
            with self.assertRaisesRegex(ValueError, reason):
                freeze_fixture(path, self.root / "not_created.json")

    def test_no_fills_returns_equity_curve_or_market_admission(self):
        report = self.replay().run()
        self.assertIsNone(report["returns"]);self.assertIsNone(report["fills"]);self.assertIsNone(report["equity_curve"])
        self.assertEqual(report["positions_created"], 0)
        for key in ("market_data_qualified", "paper_evaluation_available", "strategy_selected", "orders_available", "real_money_execution_available"):
            self.assertIs(report[key], False)

    def test_cli_and_no_overwrite(self):
        script = ROOT / "scripts/daily-risk-119.py"
        path, manifest, output = self.root / "cli.json", self.root / "frozen.json", self.root / "report.json"
        for args in [("create-fixture", "full_long", path), ("freeze", path, manifest), ("evaluate", path, manifest, output)]:
            result = subprocess.run([sys.executable, str(script), *map(str, args)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        summary = json.loads(result.stdout)
        self.assertEqual(summary["comparisons"], 8)
        self.assertIsNone(summary["returns"])
        result = subprocess.run([sys.executable, str(script), "evaluate", str(path), str(manifest), str(output)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(json.loads(result.stdout)["reason"], "artifact_exists")


if __name__ == "__main__":
    unittest.main()
