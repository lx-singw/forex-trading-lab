"""Check H1/H4 edge attribution without opening a market archive."""

from fractions import Fraction
import unittest

from forex_demo_lab.elliott_sessions_146 import HOUR
from tools.exness_h4_opening_213 import MONTH, compare_boundaries
from tools.exness_opening_212 import month_schedule


class H4OpeningDiagnosticTests(unittest.TestCase):
    def setUp(self):
        self.h1 = [(i * HOUR, (i + 1) * HOUR) for i in range(13) if i != 8]
        self.h4 = [(0, 4 * HOUR), (4 * HOUR, 8 * HOUR), (9 * HOUR, 13 * HOUR)]
        self.first = {start: (1, Fraction(1)) for start, _ in self.h1}
        for exact in (HOUR, 4 * HOUR, 9 * HOUR):
            self.first[exact] = (0, Fraction(1))

    def test_exact_first_edges_preserve_same_time_condition_and_gap(self):
        result = compare_boundaries(self.first, self.h1, self.h4, 0, 13 * HOUR)
        zero, positive = result["timing_cases"]
        self.assertEqual({"exact_source_open_same_time_order_unverified": 1,
                          "exact_source_open_decision_early": 1, "no_entry_opening_in_sample": 1},
                         zero["status_counts"])
        self.assertEqual({"exact_source_open_decision_late": 1,
                          "exact_source_open_decision_early": 1, "no_entry_opening_in_sample": 1},
                         positive["status_counts"])

    def test_missing_child_and_late_first_quote_are_distinct(self):
        self.first.pop(2 * HOUR)
        self.first[9 * HOUR] = (1, Fraction(1))
        result = compare_boundaries(self.first, self.h1, self.h4, 0, 13 * HOUR)
        for case in result["timing_cases"]:
            self.assertEqual({"missing_trigger_child": 1, "first_quote_after_open": 1,
                              "no_entry_opening_in_sample": 1}, case["status_counts"])
            self.assertEqual(0, case["exact_edges_not_ruled_out_by_modeled_time"])

    def test_july_contains_five_sampled_friday_to_sunday_pairs(self):
        h1, weekends = month_schedule(MONTH)
        self.assertEqual(504, len(h1))
        self.assertEqual(5, len(weekends))
        self.assertTrue(all(len(children) == 1 for _, children in weekends))
