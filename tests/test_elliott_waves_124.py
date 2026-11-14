"""Independent rational pattern checks, causal timing and strict replay recovery."""
from copy import deepcopy
from fractions import Fraction
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from forex_demo_lab import elliott_waves_124 as waves
from forex_demo_lab.elliott_fixture_124 import CASES, TAIL, bundle, fixture

daily = waves.daily
F = lambda n: Fraction(str(n))


def oracle(value):
    """Independent Fraction reference; no production pivot/form/step/rules methods."""
    bars = [b for b in value["daily"]["bars"] if b["session_id"] <= value["daily"]["target_session_id"]]
    prices = [F(b["close"]) for b in bars]
    turns = {}
    for center in range(1, len(bars) - 1):
        before, middle, after = prices[center - 1:center + 2]
        if middle < min(before, after):
            turns[center + 1] = (center, "low")
        elif middle > max(before, after):
            turns[center + 1] = (center, "high")
    journal, chain, considered, signals, reasons = [], [], set(), [], []
    pending = None
    for i, row in enumerate(bars):
        if pending is not None:
            p0, p1, p2, side, armed, level, stop = pending
            touch = F(row["low"]) <= stop if side > 0 else F(row["high"]) >= stop
            crossed = (prices[i - 1] <= level < prices[i]) if side > 0 else (prices[i - 1] >= level > prices[i])
            outcome = "setup_invalidated" if touch else "setup_expired" if i - armed > 10 else None
            if outcome is None and crossed:
                if i < 252:
                    outcome = "breakout_suppressed_warmup"
                else:
                    trend = (prices[i] > prices[i - 252]) - (prices[i] < prices[i - 252])
                    outcome = "breakout_observed" if trend == side else "breakout_suppressed_trend"
                    if trend == side:
                        signals.append({"side": side, "index": i, "pivots": [p0, p1, p2], "armed": armed,
                                        "level": level, "stop": stop})
            if outcome:
                reasons.append((i, outcome))
                pending = None
        if i not in turns:
            continue
        center, kind = turns[i]
        journal.append((center, kind, i, row["available_msc"]))
        if chain and chain[-1][1] == kind:
            prior = chain[-1][0]
            improves = prices[center] > prices[prior] if kind == "high" else prices[center] < prices[prior]
            if not improves:
                continue
            chain[-1] = (center, kind)
        else:
            chain.append((center, kind))
        if len(chain) < 3:
            continue
        a, b, c = [item[0] for item in chain[-3:]]
        key = (a, b, c)
        if key in considered:
            continue
        considered.add(key)
        side = 1 if chain[-3][1] == "low" else -1
        if not (prices[a] < prices[c] < prices[b] if side > 0 else prices[a] > prices[c] > prices[b]):
            reasons.append((i, "invalid_pullback_geometry")); continue
        length = abs(prices[b] - prices[a])
        if length < prices[a] / 100:
            reasons.append((i, "insufficient_impulse")); continue
        ratio = abs(prices[b] - prices[c]) / length
        if ratio < F(".382") or ratio > F(".618"):
            reasons.append((i, "retracement_outside_band")); continue
        stop = min(F(x["low"]) for x in bars[b:c + 1]) if side > 0 else max(F(x["high"]) for x in bars[b:c + 1])
        origin = F(bars[a]["low" if side > 0 else "high"])
        if (stop <= origin if side > 0 else stop >= origin):
            reasons.append((i, "origin_invalidated_by_pullback")); continue
        level = F(bars[b]["high" if side > 0 else "low"])
        if (F(row["low"]) <= stop if side > 0 else F(row["high"]) >= stop):
            reasons.append((i, "confirmation_invalidation")); continue
        if (prices[i] > level if side > 0 else prices[i] < level):
            reasons.append((i, "breakout_before_confirmation")); continue
        if pending is not None:
            reasons.append((i, "setup_slot_busy")); continue
        pending = (a, b, c, side, i, level, stop)
        reasons.append((i, "setup_armed"))
    return {"pivots": journal, "chain": chain, "signals": signals, "reasons": reasons, "pending": pending}


def audit(value, state):
    expected = oracle(value)
    bars = value["daily"]["bars"]
    actual = [(p["bar_index"], p["kind"], p["confirmation_bar_index"], p["confirmed_available_msc"]) for p in state["confirmed_pivots"]]
    assert actual == expected["pivots"]
    assert [(p["bar_index"], p["kind"]) for p in state["swing_chain"]] == expected["chain"]
    reasons = [(o["bar_index"], a["reason"]) for o in state["outcomes"] for a in o["setup_actions"]]
    assert reasons == expected["reasons"], (reasons, expected["reasons"])
    assert len(state["signals"]) == len(expected["signals"])
    for actual, wanted in zip(state["signals"], expected["signals"]):
        assert actual["side"] == wanted["side"]
        assert actual["breakout_session_id"] == bars[wanted["index"]]["session_id"]
        assert [p["bar_index"] for p in actual["pivots"]] == wanted["pivots"]
        assert actual["available_msc"] == actual["decision_msc"] == bars[wanted["index"]]["available_msc"]
        assert actual["setup_confirmed_available_msc"] == bars[wanted["armed"]]["available_msc"]
        assert F(actual["breakout_level"]) == wanted["level"] and F(actual["prospective_invalidation"]) == wanted["stop"]
    assert (state["active_setup"] is None) == (expected["pending"] is None)
    return {"bars": state["cursor"], "pivots": len(expected["pivots"]), "signals": len(expected["signals"]), "setup_actions": len(reasons)}


class WaveTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.directory = Path(self.temp.name)
        self.counter = 0

    def tearDown(self):
        self.temp.cleanup()

    def create(self, value):
        self.counter += 1
        p, m = self.directory / f"input-{self.counter}.json", self.directory / f"freeze-{self.counter}.json"
        daily.write_new(p, value)
        waves.freeze_fixture(p, m)
        return p, m, waves.Replay(p, m)

    def run_case(self, case):
        value = fixture(case)
        p, m, run = self.create(value)
        run.run()
        audit(value, run.state)
        return value, p, m, run

    def rehash_bar(self, value, index, **changes):
        bar = value["daily"]["bars"][index]
        bar.update(changes)
        cal = value["daily"]["calendar"]
        session = cal["sessions"][bar["session_id"]]
        bar["lineage_sha256"] = daily.bar_lineage(value["case"], cal["calendar_id"], session, bar)

    def reasons(self, state):
        return [a["reason"] for o in state["outcomes"] for a in o["setup_actions"]]

    def test_long_and_short_match_independent_rational_reference(self):
        for case, side in (("long_breakout", 1), ("short_breakout", -1)):
            value, p, m, run = self.run_case(case)
            self.assertEqual(len(run.state["signals"]), 1)
            self.assertEqual(run.state["signals"][0]["side"], side)
            self.assertEqual(run.state["signals"][0]["decision_msc"], value["daily"]["bars"][263]["available_msc"])

    def test_all_seventeen_fixed_paths_match_reference(self):
        for case in CASES:
            with self.subTest(case=case):
                self.run_case(case)

    def test_pivot_is_published_only_after_right_bar_becomes_available(self):
        value = fixture()
        p, m, run = self.create(value)
        for i in range(255):
            run.step()
        self.assertFalse(any(p["bar_index"] == 254 for p in run.state["confirmed_pivots"]))
        run.step()
        pivot = next(p for p in run.state["confirmed_pivots"] if p["bar_index"] == 254)
        self.assertEqual(pivot["confirmation_bar_index"], 255)
        self.assertGreater(pivot["confirmed_available_msc"], pivot["observation_msc"])

    def test_setup_cannot_trigger_on_its_confirmation_bar(self):
        value, p, m, run = self.run_case("late_confirmation")
        self.assertEqual(run.state["signals"], [])
        self.assertIn("breakout_before_confirmation", self.reasons(run.state))

    def test_delayed_availability_is_retained_in_signal(self):
        value, p, m, run = self.run_case("delayed_availability")
        signal = run.state["signals"][0]
        self.assertEqual(signal["setup_confirmed_available_msc"], value["daily"]["bars"][261]["end_msc"] + 21600000)
        self.assertGreater(signal["decision_msc"], signal["setup_confirmed_available_msc"])

    def test_closure_days_do_not_supply_confirmation_neighbors(self):
        value = bundle(["1.05", "1.04", "1.03", "1.02", "1", "1.03"])
        p, m, run = self.create(value)
        run.run()
        pivot = run.state["confirmed_pivots"][-1]
        self.assertEqual((pivot["bar_index"], pivot["confirmation_bar_index"]), (4, 5))
        self.assertEqual(pivot["confirmation_session_id"] - pivot["session_id"], 3)

    def test_equal_neighbors_never_confirm_pivot(self):
        p, m, run = self.create(bundle(["1.1", "1", "1", "1.2", "1.2"]))
        self.assertEqual(run.run()["confirmed_pivots"], 0)

    def test_same_kind_replacement_keeps_old_confirmed_journal(self):
        value, p, m, run = self.run_case("same_kind_plateau")
        highs = [p["close"] for p in run.state["confirmed_pivots"] if p["kind"] == "high"]
        self.assertEqual(highs, ["1.1", "1.12", "1.115"])
        self.assertEqual([p["close"] for p in run.state["swing_chain"] if p["kind"] == "high"], ["1.12"])
        actions = [o["swing_action"] for o in run.state["outcomes"]]
        self.assertIn("replaced_more_extreme", actions)
        self.assertIn("ignored_same_kind", actions)

    def test_equal_same_kind_pivot_keeps_first_anchor(self):
        p, m, run = self.create(bundle(["1", "1.1", "1.05", "1.05", "1.1", "1.04"]))
        run.run()
        self.assertEqual(len(run.state["confirmed_pivots"]), 2)
        self.assertEqual(run.state["swing_chain"][0]["bar_index"], 1)

    def test_inclusive_retracement_boundaries(self):
        for case in ("retracement_minimum", "retracement_maximum"):
            self.assertEqual(len(self.run_case(case)[3].state["signals"]), 1)

    def test_just_outside_retracement_boundaries_rejects(self):
        for close in (1.0741601, 1.0458399):
            value = fixture()
            self.rehash_bar(value, 260, open=close, close=close, low=close - .0001, high=close + .0001)
            p, m, run = self.create(value)
            run.run()
            self.assertIn("retracement_outside_band", self.reasons(run.state))
            self.assertEqual(run.state["signals"], [])

    def test_minimum_impulse_boundary_is_inclusive(self):
        tail = ["1.002", "1", "1.004", "1.008", "1.01", "1.008", "1.007", "1.005", "1.006", "1.008", "1.011"]
        value = bundle(["1"] + ["1.004"] * 252 + tail)
        p, m, run = self.create(value)
        run.run()
        audit(value, run.state)
        self.assertEqual(len(run.state["signals"]), 1)

    def test_small_impulse_and_deep_pullback_are_preserved_rejections(self):
        for case, reason in (("small_impulse", "insufficient_impulse"), ("deep_pullback", "retracement_outside_band")):
            run = self.run_case(case)[3]
            self.assertIn(reason, self.reasons(run.state))
            self.assertEqual(run.state["signals"], [])

    def test_pullback_wick_cannot_pass_original_swing_origin(self):
        value = fixture()
        self.rehash_bar(value, 257, low=.9998)
        p, m, run = self.create(value)
        run.run()
        self.assertIn("origin_invalidated_by_pullback", self.reasons(run.state))

    def test_confirmation_bar_invalidation_prevents_arm(self):
        value = fixture()
        self.rehash_bar(value, 261, low=1.05)
        p, m, run = self.create(value)
        run.run()
        self.assertIn("confirmation_invalidation", self.reasons(run.state))
        self.assertEqual(run.state["signals"], [])

    def test_ambiguous_ohlc_bar_invalidates_before_breakout(self):
        run = self.run_case("ambiguous_breakout")[3]
        self.assertEqual(run.state["signals"], [])
        self.assertIn("setup_invalidated", self.reasons(run.state))

    def test_touching_invalidation_is_inclusive(self):
        value = fixture()
        self.rehash_bar(value, 263, low=1.0599)
        p, m, run = self.create(value)
        self.assertEqual(run.run()["signal_observations"], 0)
        self.assertIn("setup_invalidated", self.reasons(run.state))

    def test_intrabar_high_alone_does_not_trigger_close_breakout(self):
        value = fixture()
        self.rehash_bar(value, 263, open=1.11, close=1.11, low=1.1099, high=1.15)
        p, m, run = self.create(value)
        self.assertEqual(run.run()["signal_observations"], 0)
        self.assertIsNotNone(run.state["active_setup"])

    def test_expiry_tenth_bar_can_trigger_eleventh_expires(self):
        active = self.run_case("expiry_boundary")[3]
        expired = self.run_case("expired")[3]
        self.assertEqual(len(active.state["signals"]), 1)
        self.assertEqual(expired.state["signals"], [])
        self.assertIn("setup_expired", self.reasons(expired.state))

    def test_warmup_exact_253_bar_boundary(self):
        for count, accepted in ((241, 0), (242, 1)):
            value = bundle(["1"] + ["1.04"] * (count - 1) + list(TAIL))
            p, m, run = self.create(value)
            self.assertEqual(run.run()["signal_observations"], accepted)

    def test_warmup_suppression_consumes_the_setup(self):
        run = self.run_case("warmup")[3]
        self.assertIn("breakout_suppressed_warmup", self.reasons(run.state))
        self.assertIsNone(run.state["active_setup"])

    def test_opposite_and_flat_trend_suppress(self):
        for case in ("opposite_trend", "flat_trend"):
            run = self.run_case(case)[3]
            self.assertIn("breakout_suppressed_trend", self.reasons(run.state))
            self.assertEqual(run.state["signals"], [])

    def test_busy_setup_discards_alternate_candidate_without_replacing(self):
        value = bundle(["1"] + ["1.04"] * 252 + list(TAIL[:9]) + ["1.095", "1.08", "1.13"])
        p, m, run = self.create(value)
        run.run()
        audit(value, run.state)
        self.assertIn("setup_slot_busy", self.reasons(run.state))
        self.assertEqual([s["side"] for s in run.state["signals"]], [1])

    def test_valid_future_continuation_does_not_change_selected_state(self):
        value = fixture()
        old = value["daily"]
        extended = bundle([b["close"] for b in old["bars"]] + ["1.4", ".8", "1.2"], value["case"])
        extended["daily"]["target_session_id"] = old["target_session_id"]
        extended["daily"]["decision_msc"] = old["decision_msc"]
        first = self.create(value)[2]; later = self.create(extended)[2]
        self.assertEqual(first.run()["final_state"], later.run()["final_state"])

    def test_restore_reconstructs_only_observed_prefix(self):
        value = fixture()
        p, m, run = self.create(value)
        for _ in range(262):
            run.step()
        checkpoint = run.checkpoint()
        original = waves.Replay._apply
        def bounded(instance, index, state):
            self.assertLess(index, 262)
            return original(instance, index, state)
        with patch.object(waves.Replay, "_apply", bounded):
            restored = waves.Replay.restore(p, m, checkpoint)
        self.assertEqual(restored.state, run.state)
        self.assertEqual(restored.run(), run.run())

    def test_every_small_fixture_prefix_restore_and_latest_duplicate(self):
        p, m, run = self.create(fixture("warmup"))
        for i in range(len(run._bars) + 1):
            restored = waves.Replay.restore(p, m, run.checkpoint())
            self.assertEqual(restored.state, run.state)
            if i:
                before = run.state
                self.assertFalse(run.step(i - 1, run._bars[i - 1]))
                self.assertEqual(run.state, before)
            run.step()
        self.assertFalse(run.step())

    def test_altered_and_older_duplicate_reject_without_state_change(self):
        p, m, run = self.create(fixture("warmup"))
        run.step(); run.step()
        before = run.state
        with self.assertRaisesRegex(ValueError, "wave_event_sequence"):
            run.step(0)
        altered = deepcopy(run._bars[1]); altered["close"] += .001
        with self.assertRaisesRegex(ValueError, "wave_event_conflict"):
            run.step(1, altered)
        with self.assertRaisesRegex(ValueError, "wave_event_index"):
            run.step(True)
        self.assertEqual(run.state, before)

    def test_rehashed_pivot_setup_and_signal_forgeries_reject(self):
        value, p, m, run = self.run_case("long_breakout")
        changes = [lambda s: s["confirmed_pivots"][0].update(close="99"),
                   lambda s: s["signals"][0].update(prospective_invalidation="0.5"),
                   lambda s: s["considered_patterns"].append("0" * 64),
                   lambda s: s.update(cursor=False)]
        for change in changes:
            checkpoint = run.checkpoint()
            change(checkpoint["payload"]["state"])
            checkpoint["sha256"] = daily._digest(checkpoint["payload"])
            with self.assertRaisesRegex(ValueError, "wave_checkpoint_reconstructed_state"):
                waves.Replay.restore(p, m, checkpoint)

    def test_boolean_and_cross_input_checkpoint_reject(self):
        p, m, run = self.create(fixture("warmup"))
        run.step()
        checkpoint = run.checkpoint()
        checkpoint["payload"]["cursor"] = True
        checkpoint["sha256"] = daily._digest(checkpoint["payload"])
        with self.assertRaisesRegex(ValueError, "wave_checkpoint_cursor"):
            waves.Replay.restore(p, m, checkpoint)
        p2, m2, other = self.create(fixture("no_pivots"))
        with self.assertRaisesRegex(ValueError, "wave_checkpoint_binding"):
            waves.Replay.restore(p2, m2, run.checkpoint())

    def test_state_property_is_defensive_and_completed_run_idempotent(self):
        value, p, m, run = self.run_case("long_breakout")
        report = run.report()
        copy = run.state; copy["signals"][0]["side"] = -1
        self.assertEqual(run.run(), report)
        self.assertEqual(run.state["signals"][0]["side"], 1)

    def test_missing_required_session_and_closure_target_reject(self):
        value = fixture("warmup")
        value["daily"]["bars"].pop(2)
        with self.assertRaisesRegex(ValueError, "missing_required_session"):
            waves.validate_fixture(value)
        value = fixture("warmup")
        value["daily"]["target_session_id"] = 5
        with self.assertRaisesRegex(ValueError, "target_is_closure"):
            waves.validate_fixture(value)

    def test_future_structural_errors_still_reject(self):
        value = fixture("warmup")
        value["daily"]["target_session_id"] = value["daily"]["bars"][5]["session_id"]
        self.rehash_bar(value, -1, low=2)
        with self.assertRaisesRegex(ValueError, "bar_ohlc"):
            waves.validate_fixture(value)

    def test_availability_reversal_and_unavailable_target_reject(self):
        value = fixture("warmup")
        self.rehash_bar(value, 1, available_msc=value["daily"]["bars"][2]["available_msc"] + 1)
        with self.assertRaisesRegex(ValueError, "wave_availability_order"):
            waves.validate_fixture(value)
        value = fixture("warmup"); value["daily"]["decision_msc"] -= 1
        with self.assertRaisesRegex(ValueError, "session_unavailable"):
            waves.validate_fixture(value)

    def test_boolean_numeric_market_account_and_qualification_fields_reject(self):
        for field, value in (("market_data_qualified", True), ("account", {"trade_mode": 2}), ("positions", [])):
            bad = fixture("warmup"); bad[field] = value
            with self.assertRaisesRegex(ValueError, "wave_fixture_fields"):
                waves.validate_fixture(bad)
        bad = fixture("warmup"); bad["clock"] = "broker_utc"
        with self.assertRaisesRegex(ValueError, "invented_wave_fixture_required"):
            waves.validate_fixture(bad)
        bad = fixture("warmup"); self.rehash_bar(bad, 0, close=True)
        with self.assertRaisesRegex(ValueError, "bar_price"):
            waves.validate_fixture(bad)

    def test_source_rules_manifest_and_false_flag_substitutions_reject(self):
        p, m, run = self.create(fixture("warmup"))
        original = daily._json(m.read_bytes())
        for key, replacement in (("orders_available", 0), ("market_data_qualified", True), ("frozen_at_utc", "2001-01-01T00:00:00+01:00")):
            bad = deepcopy(original); bad[key] = replacement
            m.write_text(json.dumps(bad))
            with self.assertRaises(ValueError):
                waves.Replay(p, m)
        bad = deepcopy(original); bad["rules"]["setup_slots"] = True
        m.write_text(json.dumps(bad))
        with self.assertRaisesRegex(ValueError, "wave_freeze_binding"):
            waves.Replay(p, m)

    def test_duplicate_nonfinite_json_and_market_dates_reject(self):
        for raw in ('{"x":1,"x":2}', '{"x":NaN}'):
            with self.assertRaises(ValueError):
                daily._json(raw)
        value = fixture("warmup")
        value["daily"]["decision_msc"] = 1790000000000
        with self.assertRaisesRegex(ValueError, "decision_time"):
            waves.validate_fixture(value)

    def test_report_has_no_execution_performance_or_order_capability(self):
        report = self.run_case("long_breakout")[3].report()
        self.assertIsNone(report["trades"]); self.assertIsNone(report["returns"])
        for flag in ("fill_adapter_implemented", "market_data_qualified", "paper_evaluation_available", "orders_available", "real_money_execution_available"):
            self.assertIs(report[flag], False)
        for signal in report["final_state"]["signals"]:
            self.assertNotIn("lots", signal); self.assertNotIn("entry_fill", signal)

    def test_cli_agrees_and_never_overwrites_existing_output(self):
        value, p, m, run = self.run_case("warmup")
        out = self.directory / "report.json"
        cmd = [sys.executable, str(daily.ROOT / "scripts/elliott-waves-124.py"), "evaluate", str(p), str(m), str(out)]
        result = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(daily._json(out.read_bytes()), run.report())
        before = out.read_bytes()
        repeated = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(repeated.returncode, 1)
        self.assertEqual(json.loads(repeated.stdout)["reason"], "artifact_exists")
        self.assertEqual(out.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
