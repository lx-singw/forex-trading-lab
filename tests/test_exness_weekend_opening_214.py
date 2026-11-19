"""Verify the weekend age floor from diagnostic metadata fixtures."""

from copy import deepcopy
import unittest

from tools.exness_weekend_opening_214 import summarize, weekend_bounds


class WeekendOpeningBoundsTests(unittest.TestCase):
    def setUp(self):
        self.sample = {"status": "diagnostic_complete", "archive_sha256": "0" * 64, "valid_rows": 4,
                       "boundaries": [{"last_friday_label": "2022-07-01 20:58:58.000Z",
                                       "first_sunday_label": "2022-07-03 21:05:01.000Z"}]}
        self.coverage = {"status": "complete", "archive_sha256": "0" * 64, "rows": 4,
                         "outside_modeled_h1": 0, "weekends_checked": 1}

    def test_friday_freshness_does_not_make_the_quote_fresh_at_reopen(self):
        rows = weekend_bounds(self.sample, self.coverage)
        self.assertEqual([{"friday_close_lag_ms": 2000,
                           "minimum_previous_quote_age_at_open_ms": 173_162_000,
                           "first_sunday_quote_lag_ms": 1000}], rows)
        result = summarize(rows)
        self.assertEqual(1, result["friday_quote_within_reference_at_close"])
        self.assertEqual(0, result["previous_quote_within_reference_at_sunday_open"])
        self.assertEqual(0, result["exact_sunday_source_edges"])

    def test_an_exact_sunday_label_is_separate_from_the_previous_quote_floor(self):
        self.sample["boundaries"][0]["first_sunday_label"] = "2022-07-03 21:05:00.000Z"
        result = summarize(weekend_bounds(self.sample, self.coverage))
        self.assertEqual(1, result["exact_sunday_source_edges"])
        self.assertEqual(0, result["previous_quote_within_reference_at_sunday_open"])

    def test_closure_quotes_or_mismatched_receipts_invalidate_the_bound(self):
        for override in ({"outside_modeled_h1": 1}, {"archive_sha256": "1" * 64},
                         {"rows": 3}, {"weekends_checked": 2}):
            with self.assertRaisesRegex(ValueError, "matching source"):
                weekend_bounds(self.sample, {**self.coverage, **override})

    def test_rejects_nonadjacent_or_duplicate_weekend_pairs(self):
        invalid = deepcopy(self.sample)
        invalid["boundaries"][0]["first_sunday_label"] = "2022-07-10 21:05:00.000Z"
        with self.assertRaisesRegex(ValueError, "adjacent modeled"):
            weekend_bounds(invalid, self.coverage)
        duplicated = {**self.sample, "boundaries": self.sample["boundaries"] * 2}
        with self.assertRaisesRegex(ValueError, "unique adjacent"):
            weekend_bounds(duplicated, {**self.coverage, "weekends_checked": 2})
