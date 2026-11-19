"""Offline checks for the pinned-archive opening diagnostic."""

import unittest

from tools.exness_opening_212 import archive_rows, diagnose, january_schedule


class ExnessOpeningDiagnosticTests(unittest.TestCase):
    def test_first_pair_retains_its_own_spread_and_source_lag(self):
        windows = [(1000, 2000), (5000, 7500), (7500, 10_000), (10_000, 12_000)]
        rows = [(1000, "1.1", "1.1001"), (1000, "1.1", "1.105"),
                (2000, "1.1", "1.101"), (5100, "1.2", "1.2003"),
                (8500, "1.3", "1.3002")]
        result = diagnose(rows, windows, [(5000, [1000])])
        self.assertEqual(1, result["outside_modeled_h1"])
        self.assertEqual(1, result["h1_with_no_quote"])
        self.assertEqual({"paired_proxies": 3, "exact_source_edge": 1, "positive_below_one_second": 1,
                          "at_least_one_second": 1, "spread_pips_p50": "2", "spread_pips_p95": "3"},
                         result["h1_openings"])
        self.assertEqual("3", result["sunday_openings"]["spread_pips_p50"])
        self.assertEqual(0, result["sunday_openings"]["exact_source_edge"])
        self.assertEqual(1, result["friday_h4_with_all_children_present"])
        self.assertIsNone(result["actual_strategy_counts"])

    def test_missing_child_and_opening_do_not_use_a_closure_row(self):
        result = diagnose([(3000, "1.1", "1.101")], [(1000, 2000), (5000, 7500)], [(5000, [1000])])
        self.assertEqual(0, result["friday_h4_with_all_children_present"])
        self.assertEqual(0, result["sunday_openings"]["paired_proxies"])
        self.assertIsNone(result["sunday_openings"]["spread_pips_p95"])

    def test_only_the_declared_archive_bytes_can_be_opened(self):
        with self.assertRaisesRegex(ValueError, "audited January bytes"):
            next(archive_rows(b"different file"))

    def test_schedule_contains_only_four_complete_friday_to_sunday_pairs(self):
        windows, weekends = january_schedule()
        self.assertEqual(506, len(windows))
        self.assertEqual(4, len(weekends))
        self.assertTrue(all(len(children) == 2 for _, children in weekends))
        self.assertTrue(all(opening in dict(windows) for opening, _ in weekends))
