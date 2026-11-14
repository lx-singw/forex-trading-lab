from datetime import datetime, timedelta, timezone
import unittest

from forex_demo_lab.model import Bar, Config, signal
from forex_demo_lab.strategies import CANDIDATES, decide, efficiency_mode


def bars(closes, width=.00005):
    start = datetime(2024, 1, 1, tzinfo=timezone.utc)
    return [Bar(start + timedelta(hours=i), c, c + width, c - width, c, 1) for i, c in enumerate(closes)]


class StrategyTests(unittest.TestCase):
    def test_baseline_decision_matches_existing_signal(self):
        history = bars([1.0] * 200 + [1.01])
        d = decide("C00", history, Config())
        self.assertEqual((d.side, d.stop_distance), signal(history, Config()))

    def test_slow_trend_waits_for_201_closed_bars_and_detects_cross(self):
        self.assertEqual(decide("C01", bars([1.0] * 199 + [1.1]), Config()).reason, "warmup")
        self.assertEqual(decide("C01", bars([1.0] * 200 + [1.1]), Config()).side, 1)
        self.assertEqual(decide("C01", bars([1.0] * 200 + [.9]), Config()).side, -1)

    def test_breakout_excludes_signal_bar_high_and_low(self):
        for end, side in ((1.102, 1), (1.098, -1)):
            history = bars([1.1] * 21 + [end])
            last = history[-1]
            history[-1] = Bar(last.time, end, 1.2, 1.0, end, 1)
            self.assertEqual(decide("C02", history, Config()).side, side)

    def test_breakout_equality_or_continuation_does_not_retrigger(self):
        self.assertEqual(decide("C02", bars([1.1] * 21 + [1.10005]), Config()).side, 0)
        self.assertEqual(decide("C02", bars([1.1] * 20 + [1.102, 1.103]), Config()).side, 0)

    def test_range_entry_requires_return_from_excursion(self):
        self.assertEqual(decide("C03", bars([1.1] * 19 + [1.09, 1.098]), Config()).side, 1)
        self.assertEqual(decide("C03", bars([1.1] * 19 + [1.11, 1.102]), Config()).side, -1)
        self.assertEqual(decide("C03", bars([1.1] * 20 + [1.09]), Config()).side, 0)

    def test_flat_series_and_zero_atr_abstain(self):
        for candidate in CANDIDATES:
            self.assertEqual(decide(candidate, bars([1.0] * 201, width=0), Config()).side, 0)
        self.assertEqual(decide("C03", bars([1.1] * 21), Config()).reason, "zero_price_deviation")

    def test_selector_thresholds_are_inclusive_and_neutral_band_abstains(self):
        self.assertEqual(efficiency_mode(.20), "range")
        self.assertEqual(efficiency_mode(.35), "trend")
        self.assertEqual(efficiency_mode(.3), "neutral")
        closes = [1.1, 1.1]
        for change in [-.001] * 7 + [.001] * 13:
            closes.append(closes[-1] + change)
        d = decide("C04", bars(closes), Config())
        self.assertEqual(d.side, 0)
        self.assertEqual(d.reason, "selector_neutral")
        for invalid in (-.1, 1.1, float("nan")):
            with self.assertRaises(ValueError):
                efficiency_mode(invalid)

    def test_decisions_do_not_change_when_future_bars_are_appended_elsewhere(self):
        history = bars([1.1] * 200 + [1.102])
        original = {c: decide(c, history, Config()) for c in CANDIDATES}
        future = history + bars([.5, 2.0])
        for candidate in CANDIDATES:
            self.assertEqual(decide(candidate, future[:201], Config()), original[candidate])

    def test_unknown_candidate_and_nonchronological_history_rejected(self):
        with self.assertRaises(ValueError):
            decide("unknown", [], Config())
        history = bars([1.1] * 22)
        history[-1] = history[-2]
        with self.assertRaises(ValueError):
            decide("C02", history, Config())
