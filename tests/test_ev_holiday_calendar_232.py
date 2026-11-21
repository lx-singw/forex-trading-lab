"""Verify calendar edges at the proposed holidays and development seam."""

from datetime import datetime
import unittest

from tools.ev_holiday_calendar_232 import DEVELOPMENT_START, HOUR, scenario_calendar


def utc(value):
    return int(datetime.fromisoformat(value + "+00:00").timestamp()) * 1000


class EvHolidayCalendarTests(unittest.TestCase):
    def test_holiday_at_the_development_seam_is_one_continuous_closure(self):
        record, calendar = scenario_calendar()
        holiday = next(segment for segment in record["segments"]
                       if segment["start"] < DEVELOPMENT_START < segment["end"])
        self.assertEqual("holiday", holiday["reason"])
        self.assertEqual(DEVELOPMENT_START - 2 * HOUR, holiday["start"])
        self.assertEqual(DEVELOPMENT_START + 22 * HOUR, holiday["end"])
        starts = {window.start for window in calendar.frame("H1")}
        self.assertIn(holiday["start"] - HOUR, starts)
        first = min(stamp for stamp in starts if stamp >= DEVELOPMENT_START)
        self.assertEqual(utc("2021-01-03T22:00"), first)

    def test_christmas_clips_parent_and_keeps_its_preclosure_children(self):
        _, calendar = scenario_calendar()
        christmas = utc("2020-12-25T00:00")
        last_h4 = next(item for item in calendar.frame("H4") if item.start == christmas + 4 * HOUR)
        self.assertEqual(christmas + 8 * HOUR, last_h4.end)
        self.assertEqual(tuple(range(christmas + 4 * HOUR, last_h4.end, HOUR)), last_h4.children)
        self.assertTrue(all(not christmas + 8 * HOUR <= item.start < christmas + 22 * HOUR
                            for item in calendar.frame("H1")))
