from types import SimpleNamespace
import unittest

from tools.level_b_opening_deadline_236 import deadline_counts


class OpeningDeadlineTests(unittest.TestCase):
    def test_completed_opening_exactly_at_expiry_is_allowed(self):
        hours = [SimpleNamespace(start=20, end=30), SimpleNamespace(start=35, end=45)]
        equal = deadline_counts(hours, (10, 31), decision_delay=1, opening_delay=1, wait_for_quote=False)
        late = deadline_counts(hours, (10, 31), decision_delay=1, opening_delay=2, wait_for_quote=False)
        self.assertEqual({1: 1}, equal["expiry_minus_h1_end_ms"])
        self.assertEqual(1, equal["completed_bar_timing_ceiling"])
        self.assertEqual(0, late["completed_bar_timing_ceiling"])
        self.assertEqual(1, late["excluded_by_completed_bar_deadline"])

    def test_quote_floor_selects_later_opening_and_misses_completed_bar_deadline(self):
        hours = [SimpleNamespace(start=time, end=time + 10) for time in (20, 30, 40)]
        clock = deadline_counts(hours, (10, 40), decision_delay=1, opening_delay=1, wait_for_quote=False)
        quote = deadline_counts(hours, (10, 40), decision_delay=1, opening_delay=1, wait_for_quote=True)
        self.assertEqual({10: 1}, clock["expiry_minus_h1_end_ms"])
        self.assertEqual({0: 1}, quote["expiry_minus_h1_end_ms"])
        self.assertEqual(0, quote["completed_bar_timing_ceiling"])

    def test_opening_at_expiry_or_liquidation_is_excluded(self):
        hours = [SimpleNamespace(start=time, end=time + 10) for time in (20, 30)]
        for closes in ((10, 20), (28, 39)):
            with self.subTest(closes=closes):
                counts = deadline_counts(hours, closes, decision_delay=1, opening_delay=0, wait_for_quote=False)
                self.assertEqual(0, counts["selected_h1_slots"])
