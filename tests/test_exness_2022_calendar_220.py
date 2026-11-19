"""The historical reader preserves the declared opening grid of the scenario."""

import unittest

from forex_demo_lab.elliott_sessions_146 import HOUR
from forex_demo_lab.trendline import data, historical_calendar
from tools.exness_2022_calendar_220 import END, START, calendar_record, report
from tools.exness_2022_timing import ordinary_weeks, report as previous_timing


def read(record):
    return historical_calendar.Calendar.from_record(
        record, sha256=data.digest(record), start=START, development_start=START, end=END, delay=2000,
    )


class HistoricalCalendarCompatibilityTests(unittest.TestCase):
    def test_scope_and_timing_match_the_predeclared_grid(self):
        result = report()
        self.assertEqual({"H1": 6240, "H4": 1612, "D1": 312}, result["scheduled_by_frame"])
        self.assertEqual(previous_timing()["timing_cases"][1]["all_h4"], result["timing_at_two_seconds"])
        self.assertEqual({str(n): c for n, c in ((55, 52), (59, 52), (60, 6136))},
                         result["duration_counts_by_frame_minutes"]["H1"])
        self.assertEqual(data.digest(result["calendar"]), result["calendar_sha256"])
        self.assertFalse(result["schedule_qualified"])
        self.assertFalse(result["market_data_read"])
        self.assertIsNone(result["actual_counts"])

    def test_shortened_opening_preserves_the_original_child_boundaries(self):
        calendar = read(calendar_record(ordinary_weeks()))
        first, next_hour = calendar.frame("H1")[:2]
        group = calendar.frame("H4")[0]
        self.assertEqual((55 * 60_000, HOUR), (first.end - first.start, next_hour.end - next_hour.start))
        self.assertEqual((first.start, next_hour.start), group.children)
        self.assertEqual(next_hour.end, group.end)

    def test_first_shortened_slot_requires_an_explicit_partial_session(self):
        record = calendar_record(ordinary_weeks())
        leading = record["segments"][1]
        del leading["leading_partial"]
        with self.assertRaisesRegex(ValueError, "only terminal intraday bar may be shortened"):
            read(record)
        leading.update(leading_partial=True, partial=False)
        with self.assertRaisesRegex(ValueError, "leading partial windows require explicit partial session policy"):
            read(record)

    def test_a_shortened_opening_does_not_allow_shifted_interior_edges(self):
        record = calendar_record(ordinary_weeks())
        summer_open = next(segment for segment in record["segments"]
                           if segment.get("leading_partial") and len(segment["h1"]) == 4)
        summer_open["h1"][2] += 5 * 60_000
        with self.assertRaisesRegex(ValueError, "only terminal intraday bar may be shortened"):
            read(record)
