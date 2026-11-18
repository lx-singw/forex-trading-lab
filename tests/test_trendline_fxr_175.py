"""FXR action and projected protection checks on invented H4 paths."""
from dataclasses import replace
from decimal import Decimal
from fractions import Fraction
import unittest

from forex_demo_lab.trendline import breaks, data, entries, fills, lines, selection
from test_trendline_data_163 import calendar, descriptor
from test_trendline_entries_174 import opening_hour
from test_trendline_pivots_166 import bars_for


def fixture(side="LONG", *, first_touch=290, wide_at=5):
    # Resistance is 112 - .10*(i-290). Support is 100 + .12*(i-390)
    # after index 365. A single early wide candle supplies angle range.
    rows = []
    for index in range(392):
        if index < 286:
            low, high = Decimal(104), Decimal(114)
            if index == wide_at:
                low = Decimal(80)
        else:
            high = 112 - Decimal(".10") * (index - 290)
            if index not in (first_touch, 335, 380):
                high -= Decimal(".4")
            low = high - 2
            if index >= 366:
                low = 100 + Decimal(".12") * (index - 390)
                if index not in (370, 382):
                    low += Decimal(".5")
        midpoint = (high + low) / 2
        rows.append((midpoint, high, low, midpoint))
    rows[390] = tuple(map(Decimal, ("101.2", "102.3", "100.3", "102.2")))
    if side == "SHORT":
        rows = [(200 - op, 200 - low, 200 - high, 200 - close)
                for op, high, low, close in rows]
    value = descriptor(calendar((24,) * 66))
    value["calendar"]["finalization_delay_ms"] = 0
    source, bars = bars_for([list(map(str, row)) for row in rows],
                            source=data.Declaration.from_record(value))
    return source, tuple(replace(bar, available=bar.end) for bar in bars)


def candidate(snapshot, anchor, endpoint=380):
    return next(row for row in snapshot["candidates"]
                if row["ray"]["a_index"] == anchor and row["ray"]["b_index"] == endpoint)


def replay_prefix(source, bars):
    replay = breaks.BreakReplay(source, "0.1", breaks.FXR_PROFILE)
    for bar in bars:
        replay.observe(bar)
    return replay


class TrendlineFXRTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.finished = {}
        for side in ("LONG", "SHORT"):
            source, bars = fixture(side)
            cls.finished[side] = replay_prefix(source, bars[:391]), bars

    def test_formation_requires_390_angle_bars_and_triggers_on_next_bar(self):
        for side, (replay, _) in self.finished.items():
            with self.subTest(side=side):
                report = replay.report()
                self.assertEqual("invented_fxr_m_setup_replay", report["kind"])
                action = report["action_replay"]
                self.assertIn("ANGLE_HISTORY_UNAVAILABLE",
                              candidate(action["frames"][388], 290)["reasons"])
                self.assertTrue(action["frames"][389]["eligible_line_ids"])
                formed = candidate(action["frames"][389], 290)
                self.assertEqual(90, formed["profile_tests"]["formation_span_bars"])
                self.assertEqual([290, 335, 380], formed["touches"]["touch_indices"])
                ratio = formed["profile_tests"]["slope_tests"]["normalized_angle_ratio"]
                self.assertEqual(Fraction(39, 68), selection.fraction(ratio))
                self.assertEqual([], report["decisions"][389]["triggered"])
                result = report["decisions"][390]
                self.assertEqual(("READY", side, 390), (result["state"], result["direction"], result["bar_index"]))
                self.assertEqual(1, len(result["triggered"]))
                self.assertTrue(action["journal"]["groups"][0]["consumed"])

    def test_four_index_projection_and_rounded_stops_are_exact_mirrors(self):
        for side, (replay, _) in self.finished.items():
            safety = replay.report()["decisions"][-1]["safety"]
            sign = 1 if side == "LONG" else -1
            self.assertEqual(394, safety["projected_index"])
            self.assertEqual(100, selection.fraction(safety["line_value"]))
            self.assertEqual(100 + sign * Fraction(".48"), selection.fraction(safety["projected_line_value"]))
            self.assertEqual(Fraction(1861, 700), selection.fraction(safety["atr_sma14"]))
            self.assertEqual(100 + sign * Fraction(".2"), selection.fraction(safety["stop"]))

    def test_stop_checks_use_projected_protection_and_e2_target_is_required(self):
        for side, (replay, bars) in self.finished.items():
            trigger = bars[390]
            window = fills.PriceModel(replay.source).entry_window(trigger.end)
            pending = entries.evaluate(replay, [], as_of=trigger.available)["attempts"][0]
            self.assertEqual(("PENDING", "E2"), (pending["status"], pending["request"]["exit_model"]))
            for bid, reason in (("102.2" if side == "LONG" else "97.8", "E2_TARGET_SELECTION_UNAVAILABLE"),
                                ("100.15" if side == "LONG" else "99.85", "STOP_ALREADY_CROSSED")):
                hour = opening_hour(window, bid)
                report = entries.evaluate(replay, [hour], as_of=hour.available_at)
                outcome = report["attempts"][0]
                self.assertEqual(pending["id"], outcome["id"])
                self.assertEqual(reason, outcome["reason"])
                self.assertNotEqual("FILLED", outcome["status"])
                self.assertFalse(report["orders_available"])

    def test_shorter_formation_span_has_full_history_but_fails(self):
        source, bars = fixture(first_touch=291)
        inspector = lines.Inspector(source)
        for bar in bars[:390]:
            inspector.observe(bar)
        snapshot = inspector.snapshot(breaks.FXR_PROFILE)
        line = candidate(snapshot, 291)
        self.assertEqual(89, line["profile_tests"]["formation_span_bars"])
        self.assertEqual(["FORMATION_TOO_SHORT"], line["reasons"])
        self.assertEqual([], snapshot["profile_valid_ids"])

    def test_rolloff_can_invalidate_angle_at_break_despite_atr_slope_pass(self):
        source, bars = fixture(wide_at=0)
        inspector = lines.Inspector(source)
        for bar in bars[:390]:
            inspector.observe(bar)
        self.assertTrue(candidate(inspector.snapshot(breaks.FXR_PROFILE), 290)["profile_valid"])
        inspector.observe(bars[390])
        snapshot = inspector.snapshot(breaks.FXR_PROFILE, "action_break")
        line = candidate(snapshot, 290)
        self.assertEqual(["ANGLE_TOO_STEEP"], line["reasons"])
        tests = line["profile_tests"]["slope_tests"]
        self.assertEqual(Fraction(195, 164), selection.fraction(tests["normalized_angle_ratio"]))
        self.assertLess(selection.fraction(tests["atr_slope"]), Fraction(1, 2))
        self.assertEqual([], snapshot["profile_valid_ids"])

    def test_restart_preserves_projection_and_future_wick_cannot_change_decision(self):
        original, bars = self.finished["LONG"]
        checkpoint = original.checkpoint()
        replay = breaks.BreakReplay.restore(original.source, checkpoint)
        self.assertEqual(original.report(), replay.report())
        current = replay.report()["decisions"][-1]
        future = replace(bars[391], low=Decimal("98"))
        self.assertFalse(replay.observe(future)["triggered"])
        self.assertEqual(current, replay.report()["decisions"][390])
