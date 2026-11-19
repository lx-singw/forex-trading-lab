"""Keep the calendar ceiling conditional on matched archive timestamps."""

import unittest
from unittest.mock import patch

from forex_demo_lab.exness_diagnostics_b import timestamp_ms
from forex_demo_lab.trendline import data, historical_calendar
from tools.exness_2022_calendar_220 import END, START, calendar_record
from tools.exness_2022_timing import ordinary_weeks
from tools.exness_source_ceiling_222 import report, sampled_openings, timing_cases


class SourceCeilingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        record = calendar_record(ordinary_weeks())
        cls.calendar = historical_calendar.Calendar.from_record(
            record, sha256=data.digest(record), start=START, development_start=START, end=END, delay=2000,
        )

    def test_only_positive_source_lag_removes_a_strictly_early_candidate(self):
        opening = timestamp_ms("2022-07-03 21:05:00.000Z")
        immediate = timestamp_ms("2022-07-04 04:00:00.000Z")
        for case in timing_cases(self.calendar, {opening: 1000, immediate: 1}):
            self.assertEqual(51, case["ceiling_without_same_time_order"])
            self.assertEqual(1, len(case["sampled_late_openings_excluded"]))
            self.assertEqual(opening, case["sampled_late_openings_excluded"][0]["first_scheduled_open"])
            self.assertEqual(50, case["remaining_candidate_ceiling_before_strategy_filters"])
            self.assertEqual(10, case["minimum_candidates_needed_from_2021_to_reach_two_year_gate"])
        for case in timing_cases(self.calendar, {opening: 0}):
            self.assertEqual(51, case["remaining_candidate_ceiling_before_strategy_filters"])

    def test_time_outside_the_h1_schedule_rejected(self):
        with self.assertRaisesRegex(ValueError, "scheduled H1 start"):
            timing_cases(self.calendar, {START: 1})

    def test_sample_lag_is_bound_to_full_scheduled_start(self):
        sample = {
            "status": "diagnostic_complete", "archive_sha256": "0" * 64, "valid_rows": 4,
            "boundaries": [{"last_friday_label": "2022-07-01 20:58:58.000Z",
                            "first_sunday_label": "2022-07-03 21:05:01.000Z"}],
        }
        coverage = {"status": "complete", "archive_sha256": "0" * 64, "rows": 4,
                    "outside_modeled_h1": 0, "weekends_checked": 1, "observed_receipt_times_available": False}
        start = timestamp_ms("2022-07-03 21:05:00.000Z")
        self.assertEqual(((start, 1000),), sampled_openings(sample, coverage))
        with self.assertRaisesRegex(ValueError, "matching source"):
            sampled_openings(sample, coverage | {"rows": 5})
        with self.assertRaisesRegex(ValueError, "source-time-only"):
            sampled_openings(sample, coverage | {"observed_receipt_times_available": True})

    def test_wrong_retained_receipt_digest_stops_before_using_content(self):
        with patch.object(data, "read_json", return_value=(None, "0" * 64)):
            with self.assertRaisesRegex(ValueError, "differ from Sprint 214"):
                report()
