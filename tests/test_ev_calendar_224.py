"""Verify DST-sensitive ordinary hours and timestamp-only discrepancies."""

from datetime import datetime
import unittest

from tools.ev_calendar_224 import compare, ordinary_open


def stamp(utc):
    return int(datetime.fromisoformat(utc + "+00:00").timestamp())


class EvCalendarTests(unittest.TestCase):
    def test_ordinary_hours_follow_new_york_clock_changes(self):
        boundaries = (
            ("2024-03-08T21:00", True), ("2024-03-08T22:00", False),
            ("2024-03-10T20:55", False), ("2024-03-10T21:00", True),
            ("2024-11-01T20:55", True), ("2024-11-01T21:00", False),
            ("2024-11-03T21:55", False), ("2024-11-03T22:00", True),
        )
        for utc, expected in boundaries:
            with self.subTest(utc=utc):
                self.assertEqual(expected, ordinary_open(stamp(utc)))

    def test_absence_and_outside_hours_are_retained(self):
        holiday = stamp("2024-01-01T00:00")
        weekday = stamp("2024-01-08T00:00")
        outside = stamp("2024-01-06T00:00")
        report = compare(
            {weekday, outside},
            {weekday + minute * 60 for minute in range(0, 50, 5)} | {outside},
            {holiday, weekday, weekday + 3600},
        )
        self.assertEqual(1, report["h1_slots_in_common"])
        self.assertEqual(1, report["h1_missing_inside_holiday_notice_windows"])
        self.assertEqual(1, report["h1_missing_outside_holiday_notice_windows"][0]["slots"])
        self.assertEqual(1, report["h1_outside_ordinary_hours"][0]["slots"])
        self.assertEqual({"start": "2024-01-08T00:50:00+00:00",
                          "end_exclusive": "2024-01-08T01:00:00+00:00", "slots": 2},
                         report["m5_missing_within_published_h1"][1])
        self.assertEqual(1, report["m5_outside_ordinary_hours"][0]["slots"])
