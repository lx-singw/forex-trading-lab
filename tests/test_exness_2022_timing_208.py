"""Dated ordinary-hours scenario with no quotes or outcomes."""

from collections import Counter
from datetime import date
import unittest

from forex_demo_lab.elliott_sessions_146 import HOUR
from forex_demo_lab.trendline.entry_timing import compare_schedule
from tools.exness_2022_timing import clipped_buckets, ordinary_weeks, report


class ExnessOrdinaryHoursTimingTests(unittest.TestCase):
    def test_week_seasons_and_transition_openings(self):
        weeks = ordinary_weeks()
        self.assertEqual({"winter": 18, "summer": 34}, Counter(season for _, _, season in weeks))
        windows = {opening.date(): (opening.strftime("%H:%M"), closing.strftime("%H:%M"))
                   for opening, closing, _ in weeks}
        self.assertEqual(("22:05", "21:59"), windows[date(2022, 3, 6)])
        self.assertEqual(("21:05", "20:59"), windows[date(2022, 3, 13)])
        self.assertEqual(("21:05", "20:59"), windows[date(2022, 10, 30)])
        self.assertEqual(("22:05", "21:59"), windows[date(2022, 11, 6)])

    def test_clipping_keeps_the_wall_clock_grid_and_first_scheduled_open(self):
        weeks = ordinary_weeks()[:2]
        h4 = clipped_buckets(weeks, 4 * HOUR)
        starts = tuple(start for start, _ in clipped_buckets(weeks, HOUR))
        self.assertEqual(115 * 60_000, h4[0][1] - h4[0][0])
        self.assertEqual(119 * 60_000, h4[30][1] - h4[30][0])
        self.assertEqual(0, h4[1][0] % (4 * HOUR))
        rows = compare_schedule(starts, tuple(end for _, end in h4), delay=2000)
        friday = rows[30]
        self.assertEqual("EARLIEST_PUBLICATION_BEFORE_OPEN", friday["status"])
        self.assertEqual(starts[120], friday["first_scheduled_open"])
        self.assertEqual(h4[31][1], friday["expires_at"])
        self.assertEqual("LATE_AT_EARLIEST_PUBLICATION", rows[29]["status"])
        self.assertEqual("NO_SCHEDULED_ENTRY", rows[-1]["status"])

    def test_positive_delay_has_zero_full_length_candidates(self):
        result = report()
        zero, positive = result["timing_cases"]
        self.assertEqual(6_240, result["scheduled_h1"])
        self.assertEqual(1_612, positive["all_h4"]["scheduled_h4_closes"])
        self.assertEqual(1_508, positive["full_h4_only"]["scheduled_h4_closes"])
        self.assertEqual(1_560, zero["all_h4"]["status_counts"]["TIED_AT_EARLIEST_PUBLICATION"])
        self.assertEqual(1_560, positive["all_h4"]["status_counts"]["LATE_AT_EARLIEST_PUBLICATION"])
        self.assertEqual(51, positive["all_h4"]["ceiling_if_decision_precedes_tied_open"])
        self.assertEqual(0, positive["full_h4_only"]["ceiling_if_decision_precedes_tied_open"])
        self.assertIsNone(result["actual_counts"])
        self.assertFalse(result["schedule_qualified"])

    def test_comparison_rejects_out_of_order_or_repeated_edges(self):
        for starts, closes in (((10, 5), (1, 2)), ((5, 10), (2, 2))):
            with self.assertRaisesRegex(ValueError, "strictly increasing"):
                compare_schedule(starts, closes, delay=0)
