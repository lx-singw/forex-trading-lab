from copy import deepcopy
from dataclasses import FrozenInstanceError, asdict
from decimal import Decimal, localcontext
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from forex_demo_lab.daily_features_118 import (
    CANDIDATES, DAY, DailyBar, decisions, evaluate_fixture, freeze_fixture,
    mix_sides, reentry_side, snapshot, source_bindings, write_new,
)
from forex_demo_lab.daily_fixture_118 import CASES, fixture

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = {
    "trend_up_reentry_long": (1, 1, 1, 1.0),
    "trend_up_reentry_none": (1, 0, 1, 0.5),
    "trend_up_reentry_short": (1, -1, 0, 0.0),
    "trend_flat_reentry_long": (0, 1, 1, 0.5),
    "trend_flat_reentry_none": (0, 0, 0, 0.0),
    "trend_flat_reentry_short": (0, -1, -1, 0.5),
    "trend_down_reentry_long": (-1, 1, 0, 0.0),
    "trend_down_reentry_none": (-1, 0, -1, 0.5),
    "trend_down_reentry_short": (-1, -1, -1, 1.0),
}


def reline(value, bar):
    """Independent encoding of the specified content lineage."""
    body = {"format": "FXDL_DAILY118_V1", "kind": "invented_daily_fixture",
            "clock": "invented_utc_milliseconds", "symbol": "EURUSD", "case": value["case"],
            "calendar_id": value["calendar"]["calendar_id"],
            "session": value["calendar"]["sessions"][bar["session_id"]],
            "bar": {k: v for k, v in bar.items() if k != "lineage_sha256"}}
    bar["lineage_sha256"] = hashlib.sha256(json.dumps(
        body, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def price(value, index, close, width=.0004):
    bar = value["bars"][index]
    bar.update(open=close, high=close + width, low=close - width, close=close)
    reline(value, bar)


def oracle(value):
    """Decimal moments and independent TR indexing; no production feature methods."""
    bars = [b for b in value["bars"] if b["session_id"] <= value["target_session_id"]][-253:]
    with localcontext() as ctx:
        ctx.prec = 70
        d = lambda x: Decimal(str(x))
        closes = [d(b["close"]) for b in bars]
        ret = closes[-1] / closes[0] - 1
        zs = []
        for window in (closes[-21:-1], closes[-20:]):
            mean = sum(window) / Decimal(20)
            sd = (sum((x - mean) ** 2 for x in window) / Decimal(20)).sqrt()
            zs.append(None if not sd else (window[-1] - mean) / sd)
        ranges = [max(d(new["high"]) - d(new["low"]),
                      abs(d(new["high"]) - d(old["close"])),
                      abs(d(new["low"]) - d(old["close"])))
                  for old, new in zip(bars[-15:-1], bars[-14:])]
        return float(ret), tuple(None if z is None else float(z) for z in zs), float(sum(ranges) / 14 * 2)


class Daily118Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.value = fixture()

    def bundle(self, value=None):
        path, manifest = self.root / "fixture.json", self.root / "manifest.json"
        write_new(path, self.value if value is None else value)
        freeze_fixture(path, manifest)
        return path, manifest

    def reject(self, value, reason):
        with self.assertRaisesRegex(ValueError, "^" + reason + "$"):
            decisions(value)

    def test_all_nine_real_history_side_pairs(self):
        for case, (trend, reentry, mixed, risk) in EXPECTED.items():
            with self.subTest(case=case):
                result = decisions(fixture(case))
                self.assertEqual(result["T12_D"].side, trend)
                self.assertEqual(result["MR20_D"].side, reentry)
                self.assertEqual(result["MIX50_D"].side, mixed)
                self.assertEqual(result["MIX50_D"].risk_multiplier, risk)
                self.assertEqual(result["MIX50_D"].score, (trend + reentry) / 2)
                self.assertEqual(result["MIX50_D"].component_sides, (("T12_D", trend), ("MR20_D", reentry)))
                self.assertEqual(result["CASH"].side, 0)

    def test_independent_decimal_moments_and_atr(self):
        for case in EXPECTED:
            with self.subTest(case=case):
                value = fixture(case)
                ret, (old_z, new_z), distance = oracle(value)
                actual = decisions(value)["T12_D"]
                self.assertAlmostEqual(actual.trend_return, ret, delta=1e-12)
                if old_z is None or new_z is None:
                    self.assertIsNone(actual.previous_z)
                    self.assertIsNone(actual.current_z)
                else:
                    self.assertAlmostEqual(actual.previous_z, old_z, delta=1e-11)
                    self.assertAlmostEqual(actual.current_z, new_z, delta=1e-11)
                self.assertAlmostEqual(actual.stop_distance, distance, delta=1e-12)

    def test_common_253_session_warmup_and_cash(self):
        value = fixture("warmup")
        for candidate, result in decisions(value).items():
            self.assertEqual((result.side, result.risk_multiplier, result.stop_distance), (0, 0, 0))
            self.assertEqual(result.reason, "cash" if candidate == "CASH" else "warmup")
        self.assertEqual(len(snapshot(value).history), 252)
        self.assertEqual(len(snapshot(self.value).history), 253)

    def test_exact_reentry_crossing_boundaries(self):
        cases = [(-2, 0, 0), (2, 0, 0), (-3, -2, 1), (3, 2, -1),
                 (-3, math.nextafter(-2, -math.inf), 0),
                 (3, math.nextafter(2, math.inf), 0),
                 (math.nextafter(-2, -math.inf), -2, 1),
                 (math.nextafter(2, math.inf), 2, -1)]
        for old, new, expected in cases:
            self.assertEqual(reentry_side(old, new), expected)

    def test_exact_old_two_sigma_population_history(self):
        for previous, expected_z in [([100.] * 16 + [200.] * 4, 2.),
                                     ([200.] * 16 + [100.] * 4, -2.)]:
            with self.subTest(z=expected_z):
                value = deepcopy(self.value)
                for i, close in enumerate(previous + [150.], start=len(value["bars"]) - 21):
                    price(value, i, close, 1.)
                result = decisions(value)["MR20_D"]
                self.assertEqual(result.previous_z, expected_z)
                self.assertEqual(result.side, 0)
                self.assertAlmostEqual(result.current_z, oracle(value)[1][1], delta=1e-12)

    def test_zero_previous_deviation_abstains(self):
        for i in range(-21, -1):
            price(self.value, i, 1.1)
        price(self.value, -1, 1.2)
        result = decisions(self.value)["MR20_D"]
        self.assertEqual((result.side, result.reason), (0, "zero_price_deviation"))

    def test_zero_current_deviation_abstains(self):
        price(self.value, -21, 1.0)
        for i in range(-20, 0):
            price(self.value, i, 1.1)
        self.assertEqual(decisions(self.value)["MR20_D"].reason, "zero_price_deviation")

    def test_zero_true_range_blocks_active_signals(self):
        for i in range(-15, 0):
            price(self.value, i, 1.1, 0.)
        result = decisions(self.value)["T12_D"]
        self.assertEqual((result.side, result.risk_multiplier, result.stop_distance), (0, 0, 0))
        self.assertEqual(result.reason, "zero_true_range")
        self.assertEqual(result.score, 1)

    def test_flat_zero_range_fixture_cash(self):
        for candidate, result in decisions(fixture("zero_range")).items():
            self.assertEqual(result.side, 0)
            self.assertEqual(result.stop_distance, 0)
            self.assertEqual(result.reason, "cash" if candidate == "CASH" else "zero_true_range")

    def test_atr_uses_gap_and_exact_fourteen_ranges(self):
        price(self.value, -15, 1.5)
        price(self.value, -14, 1.1)
        self.assertAlmostEqual(decisions(self.value)["T12_D"].stop_distance, oracle(self.value)[2], delta=1e-12)
        original = decisions(self.value)["T12_D"].stop_distance
        price(self.value, -16, 8.)
        self.assertEqual(decisions(self.value)["T12_D"].stop_distance, original)

    def test_trend_uses_253rd_not_252nd_close(self):
        price(self.value, 0, 1.2)
        price(self.value, 1, 1.0)
        self.assertEqual(decisions(self.value)["T12_D"].side, -1)
        price(self.value, 0, 1.1)
        self.assertEqual(decisions(self.value)["T12_D"].side, 0)

    def test_latest_253_sessions_after_longer_history(self):
        # Evaluate an earlier prefix inside a valid full invented fixture.
        value = deepcopy(self.value)
        target = value["bars"][-2]
        value.update(target_session_id=target["session_id"], decision_msc=target["available_msc"])
        self.assertEqual(decisions(value)["T12_D"].reason, "warmup")
        self.assertEqual(len(decisions(value)["T12_D"].used_bar_hashes), 252)

    def test_future_prices_do_not_change_earlier_decision(self):
        value = deepcopy(self.value)
        target = value["bars"][-2]
        value.update(target_session_id=target["session_id"], decision_msc=target["available_msc"])
        old = decisions(value)
        price(value, -1, 19.0, 2.0)
        self.assertEqual(decisions(value), old)

    def test_future_calendar_continuation_does_not_change_decision(self):
        old = decisions(self.value)
        value = deepcopy(self.value)
        for _ in range(5):
            previous = value["calendar"]["sessions"][-1]
            row = {"session_id": previous["session_id"] + 1, "start_msc": previous["end_msc"],
                   "end_msc": previous["end_msc"] + DAY, "status": "trading"}
            value["calendar"]["sessions"].append(row)
            bar = {"session_id": row["session_id"], "start_msc": row["start_msc"], "end_msc": row["end_msc"],
                   "observation_msc": row["end_msc"] - 1, "available_msc": row["end_msc"] + 1000,
                   "open": 10., "high": 12., "low": 8., "close": 11.}
            reline(value, bar)
            value["bars"].append(bar)
        self.assertEqual(decisions(value), old)
        value.update(target_session_id=bar["session_id"], decision_msc=bar["available_msc"])
        observed = snapshot(value)
        self.assertEqual(len(observed.history), 253)
        self.assertEqual(observed.history[0].session_id, value["bars"][5]["session_id"])
        self.assertAlmostEqual(decisions(value)["T12_D"].trend_return, 10.0, delta=1e-12)

    def test_identical_replay_is_idempotent_and_decision_immutable(self):
        first = decisions(self.value)
        self.assertEqual(first, decisions(deepcopy(self.value)))
        with self.assertRaises(FrozenInstanceError):
            first["MIX50_D"].side = -1

    def test_all_mixture_pairs_and_invalid_sides(self):
        expected = {(1, 1): (1, 1., 1.), (1, 0): (1, .5, .5), (1, -1): (0, 0., 0.),
                    (0, 1): (1, .5, .5), (0, 0): (0, 0., 0.), (0, -1): (-1, -.5, .5),
                    (-1, 1): (0, 0., 0.), (-1, 0): (-1, -.5, .5), (-1, -1): (-1, -1., 1.)}
        for pair, result in expected.items():
            self.assertEqual(mix_sides(*pair), result)
        for bad in (True, False, 1., 2, "1", None):
            with self.assertRaisesRegex(ValueError, "component_side"):
                mix_sides(bad, 0)

    def test_reentry_rejects_boolean_and_nonfinite_values(self):
        for bad in (True, float("inf"), float("nan"), "2"):
            with self.assertRaisesRegex(ValueError, "feature_arithmetic"):
                reentry_side(bad, 0)

    def test_missing_trading_session_not_a_closure(self):
        del self.value["bars"][12]
        self.reject(self.value, "missing_required_session")

    def test_predeclared_closures_need_no_bars(self):
        observed = snapshot(self.value)
        self.assertGreater(len(self.value["calendar"]["sessions"]), len(observed.history))
        self.assertEqual(len(observed.history), 253)

    def test_bar_on_closure_rejected(self):
        row = next(s for s in self.value["calendar"]["sessions"] if s["status"] == "closure")
        bar = deepcopy(self.value["bars"][0])
        bar.update(session_id=row["session_id"], start_msc=row["start_msc"], end_msc=row["end_msc"],
                   observation_msc=row["end_msc"] - 1, available_msc=row["end_msc"] + 1)
        reline(self.value, bar)
        self.value["bars"].append(bar)
        self.value["bars"].sort(key=lambda b: b["session_id"])
        self.reject(self.value, "bar_on_closure")

    def test_target_closure_rejected(self):
        self.value["target_session_id"] = next(s["session_id"] for s in self.value["calendar"]["sessions"] if s["status"] == "closure")
        self.reject(self.value, "target_is_closure")

    def test_unavailable_target_rejected(self):
        self.value["decision_msc"] -= 1
        self.reject(self.value, "session_unavailable")

    def test_late_prior_bar_unavailable_rejected(self):
        self.value["bars"][0]["available_msc"] = self.value["decision_msc"] + 1
        reline(self.value, self.value["bars"][0])
        self.reject(self.value, "session_unavailable")

    def test_open_bar_and_outside_observation_rejected(self):
        for field, new, reason in [("available_msc", self.value["bars"][-1]["end_msc"] - 1, "bar_not_completed"),
                                   ("observation_msc", self.value["bars"][-1]["end_msc"], "observation_time")]:
            value = deepcopy(self.value)
            value["bars"][-1][field] = new
            self.reject(value, reason)

    def test_reversed_duplicate_conflicting_bar_order(self):
        for mode in ("reverse", "duplicate", "conflicting"):
            value = deepcopy(self.value)
            if mode == "reverse":
                value["bars"][0], value["bars"][1] = value["bars"][1], value["bars"][0]
            else:
                value["bars"].insert(1, deepcopy(value["bars"][0]))
                if mode == "conflicting":
                    price(value, 1, 1.3)
            self.reject(value, "bar_sequence")

    def test_calendar_gap_or_id_skip_rejected(self):
        for field in ("session_id", "start_msc"):
            value = deepcopy(self.value)
            value["calendar"]["sessions"][1][field] += 1 if field == "session_id" else DAY
            if field == "start_msc":
                value["calendar"]["sessions"][1]["end_msc"] += DAY
            self.reject(value, "calendar_sequence")

    def test_calendar_must_be_predeclared(self):
        self.value["calendar"]["available_msc"] = self.value["calendar"]["sessions"][0]["start_msc"] + 1
        self.reject(self.value, "calendar_not_predeclared")

    def test_ohlc_and_invalid_price_types(self):
        cases = [("low", 2., "bar_ohlc"), ("close", 0., "bar_price"), ("close", -1., "bar_price"),
                 ("open", True, "bar_price"), ("high", float("inf"), "bar_price"),
                 ("low", float("nan"), "bar_price"), ("close", "1.1", "bar_price"),
                 ("close", 10 ** 1000, "bar_price")]
        for field, new, reason in cases:
            value = deepcopy(self.value)
            value["bars"][-1][field] = new
            self.reject(value, reason)

    def test_direct_dailybar_validates_types(self):
        row = deepcopy(self.value["bars"][0])
        row["session_id"] = True
        with self.assertRaisesRegex(ValueError, "session_id"):
            DailyBar(**row)

    def test_boolean_times_and_ids_rejected(self):
        for key, reason in [("target_session_id", "target_session_id"), ("decision_msc", "decision_time")]:
            value = deepcopy(self.value)
            value[key] = True
            self.reject(value, reason)
        for field, reason in [("session_id", "session_id"), ("start_msc", "session_time"),
                              ("observation_msc", "observation_time"), ("available_msc", "bar_not_completed")]:
            value = deepcopy(self.value)
            value["bars"][0][field] = True
            self.reject(value, reason)

    def test_corrupt_lineage_or_changed_prices_rejected(self):
        for mode in ("digest", "price"):
            value = deepcopy(self.value)
            if mode == "digest":
                value["bars"][0]["lineage_sha256"] = "0" * 64
            else:
                value["bars"][0]["open"] += .00001
            self.reject(value, "bar_lineage_mismatch")

    def test_session_mismatch_and_invented_boundary(self):
        value = deepcopy(self.value)
        value["bars"][0]["start_msc"] += DAY
        value["bars"][0]["end_msc"] += DAY
        value["bars"][0]["observation_msc"] += DAY
        value["bars"][0]["available_msc"] += DAY
        self.reject(value, "bar_session_mismatch")
        value = deepcopy(self.value)
        value["calendar"]["sessions"][0]["start_msc"] += 1
        self.reject(value, "invented_day_boundary")

    def test_unknown_fields_no_boolean_qualification_escape(self):
        for location, reason in [("fixture", "fixture_fields"), ("calendar", "calendar_fields"),
                                 ("bar", "bar_fields"), ("session", "session_fields")]:
            value = deepcopy(self.value)
            target = {"fixture": value, "calendar": value["calendar"], "bar": value["bars"][0],
                      "session": value["calendar"]["sessions"][0]}[location]
            target["qualified"] = True
            self.reject(value, reason)

    def test_native_historical_market_labels_rejected(self):
        for field, label in [("kind", "native_capture"), ("kind", "historical_data"),
                             ("kind", "market_data"), ("clock", "broker_clock"), ("symbol", "GBPUSD")]:
            value = deepcopy(self.value)
            value[field] = label
            self.reject(value, "invented_fixture_required")
        self.value["calendar"]["kind"] = "qualified_market_calendar"
        self.reject(self.value, "invented_calendar_required")

    def test_reserved_timestamp_not_admitted_as_invented(self):
        self.value["calendar"]["sessions"][0]["start_msc"] = 1_793_491_200_000
        self.reject(self.value, "session_time")

    def test_oversized_calendar_and_bar_counts(self):
        for field, reason in [("calendar", "calendar_count"), ("bars", "bar_count")]:
            value = deepcopy(self.value)
            if field == "calendar":
                value["calendar"]["sessions"] = [{}] * 801
            else:
                value["bars"] = [{}] * 801
            self.reject(value, reason)

    def test_arithmetic_overflow_rejected_not_zero_signal(self):
        price(self.value, 0, 1e-300, 0.)
        price(self.value, -1, 1e308, 0.)
        self.reject(self.value, "feature_arithmetic")

    def test_frozen_report_contains_only_features_and_bindings(self):
        path, manifest = self.bundle()
        report = evaluate_fixture(path, manifest, self.root / "report.json")
        self.assertEqual(tuple(report["decisions"]), CANDIDATES)
        self.assertIsNone(report["returns"])
        self.assertIsNone(report["positions"])
        self.assertIsNone(report["fills"])
        self.assertFalse(report["orders_available"])
        self.assertFalse(report["market_data_qualified"])
        self.assertFalse(report["paper_evaluation_available"])
        self.assertFalse(report["real_money_execution_available"])
        for result in report["decisions"].values():
            self.assertEqual(len(result["used_bar_hashes"]), 253)
            self.assertLessEqual(result["available_msc"], result["decision_msc"])

    def test_fixture_byte_change_after_freeze_rejected(self):
        path, manifest = self.bundle()
        path.write_bytes(path.read_bytes() + b"\n")
        with self.assertRaisesRegex(ValueError, "freeze_binding_mismatch"):
            evaluate_fixture(path, manifest, self.root / "report.json")
        self.assertFalse((self.root / "report.json").exists())

    def test_rehashed_invalid_fixture_shape_rejected_safely(self):
        path, manifest = self.bundle()
        original = json.loads(manifest.read_text())
        for bad in ({}, [], {"unrelated": True}):
            raw = json.dumps(bad).encode()
            path.write_bytes(raw)
            altered = {**original, "fixture_sha256": hashlib.sha256(raw).hexdigest()}
            manifest.write_text(json.dumps(altered))
            with self.assertRaisesRegex(ValueError, "^fixture_fields$"):
                evaluate_fixture(path, manifest, self.root / "report.json")
            self.assertFalse((self.root / "report.json").exists())

    def test_schema_and_rule_boolean_substitution_rejected(self):
        path, manifest = self.bundle()
        original = json.loads(manifest.read_text())
        for section, key in [("schema", "market_admission"), ("rules", "cash_interest")]:
            value = deepcopy(original)
            value[section][key] = 0 if section == "schema" else False
            manifest.write_text(json.dumps(value))
            with self.assertRaisesRegex(ValueError, "freeze_binding_mismatch"):
                evaluate_fixture(path, manifest, self.root / "report.json")

    def test_manifest_target_boolean_and_freeze_time_rejected(self):
        path, manifest = self.bundle()
        original = json.loads(manifest.read_text())
        for field, new, reason in [("target_session_id", True, "manifest_target"),
                                   ("decision_msc", True, "manifest_target"),
                                   ("frozen_at_utc", "2001-01-01T00:00:00", "manifest_freeze_time"),
                                   ("frozen_at_utc", 1, "manifest_freeze_time")]:
            value = deepcopy(original)
            value[field] = new
            manifest.write_text(json.dumps(value))
            with self.assertRaisesRegex(ValueError, reason):
                evaluate_fixture(path, manifest, self.root / "report.json")

    def test_source_change_and_fixed_declaration_change_rejected(self):
        path, manifest = self.bundle()
        sources = source_bindings()
        drift = {**sources, "scripts/daily-features-118.py": "0" * 64}
        with patch("forex_demo_lab.daily_features_118.source_bindings", return_value=drift):
            with self.assertRaisesRegex(ValueError, "freeze_binding_mismatch"):
                evaluate_fixture(path, manifest, self.root / "report.json")
        drift = {**sources, "config/research-candidates-117.json": "0" * 64}
        with patch("forex_demo_lab.daily_features_118.source_bindings", return_value=drift):
            with self.assertRaisesRegex(ValueError, "fixed_declaration_changed"):
                freeze_fixture(path, self.root / "other-manifest.json")
            with self.assertRaisesRegex(ValueError, "fixed_declaration_changed"):
                evaluate_fixture(path, manifest, self.root / "report.json")

    def test_strict_json_duplicate_nonfinite_and_malformed(self):
        path = self.root / "bad.json"
        raw = json.dumps(self.value)
        cases = [(raw.replace('"format":', '"format": "x", "format":', 1), "duplicate_json_field"),
                 (raw.replace('"open": 1.0', '"open": NaN', 1), "nonfinite_json"),
                 ("{", "invalid_json")]
        for body, reason in cases:
            path.write_text(body)
            with self.assertRaisesRegex(ValueError, reason):
                freeze_fixture(path, self.root / "manifest.json")

    def test_input_symlink_and_size_rejected(self):
        path = self.root / "huge.json"
        path.write_bytes(b" " * (8 * 1024 * 1024 + 1))
        with self.assertRaisesRegex(ValueError, "input_size"):
            freeze_fixture(path, self.root / "manifest.json")
        link = self.root / "link.json"
        link.symlink_to(path)
        with self.assertRaisesRegex(ValueError, "invalid_input_file"):
            freeze_fixture(link, self.root / "manifest.json")

    def test_existing_output_not_overwritten(self):
        path, manifest = self.bundle()
        output = self.root / "report.json"
        output.write_text("preserve")
        with self.assertRaises(FileExistsError):
            evaluate_fixture(path, manifest, output)
        self.assertEqual(output.read_text(), "preserve")

    def test_invalid_freeze_creates_no_manifest(self):
        self.value["decision_msc"] -= 1
        path = self.root / "fixture.json"
        write_new(path, self.value)
        with self.assertRaisesRegex(ValueError, "session_unavailable"):
            freeze_fixture(path, self.root / "manifest.json")
        self.assertFalse((self.root / "manifest.json").exists())

    def test_cli_create_freeze_evaluate_and_reject_overwrite(self):
        script = ROOT / "scripts/daily-features-118.py"
        path, manifest, output = self.root / "cli.json", self.root / "frozen.json", self.root / "out.json"
        for args in [("create-fixture", "trend_down_reentry_long", path), ("freeze", path, manifest),
                     ("evaluate", path, manifest, output)]:
            proc = subprocess.run([sys.executable, str(script), *map(str, args)], capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
            json.loads(proc.stdout)
        report = json.loads(output.read_text())
        self.assertEqual(report["decisions"]["MIX50_D"]["reason"], "opposing_components")
        proc = subprocess.run([sys.executable, str(script), "evaluate", str(path), str(manifest), str(output)],
                              capture_output=True, text=True)
        self.assertEqual(proc.returncode, 1)
        self.assertEqual(json.loads(proc.stdout)["reason"], "artifact_exists")


if __name__ == "__main__":
    unittest.main()
