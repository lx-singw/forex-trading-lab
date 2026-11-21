"""Test a holiday-hours scenario against the retained EV timestamp audit."""

import argparse
from bisect import bisect_right
from datetime import datetime
from itertools import groupby

from forex_demo_lab.elliott_sessions_146 import FRAMES, HOUR
from forex_demo_lab.trendline import data, entry_timing, historical_calendar
from tools.ev_calendar_224 import intervals, ordinary_open
from tools.ev_opening_resample_223 import year_bounds
from tools.exness_2022_calendar_220 import _edges

DAY = 24 * HOUR
START = year_bounds(2020)[0] * 1000
DEVELOPMENT_START = year_bounds(2021)[0] * 1000
END = year_bounds(2022)[1] * 1000
DELAY = 2000
EVIDENCE_SHA256 = {
    2020: "4268eef3ad9109c88a30dc9a69e5d6488ce0f22748b929797ce539c5a9f7e780",
    2021: "adf0c20c2dcb87add2d4a76679861db88372b666d3f1790082afda8ff697dc4f",
    2022: "f852ef28b52fe46603b2fe9b7a9dc8b675de8b39d43a5898fd750ee36eba590d",
}
HOLIDAY_RANGES = (
    ("2020-01-01T00:00:00+00:00", "2020-01-01T22:00:00+00:00"),
    ("2020-12-25T08:00:00+00:00", "2020-12-25T22:00:00+00:00"),
    ("2020-12-31T22:00:00+00:00", "2021-01-01T22:00:00+00:00"),
)


def _slots(left, right, width):
    bounds = (int(datetime.fromisoformat(value).timestamp()) * 1000 for value in (left, right))
    start, end = bounds
    return range(start, end, width)


def _observed_starts(coverage, year):
    start, end = (value * 1000 for value in year_bounds(year))
    starts = {stamp for stamp in range(start, end, HOUR) if ordinary_open(stamp // 1000)}
    for row in coverage["h1_missing"]:
        starts.difference_update(_slots(row["start"], row["end_exclusive"], HOUR))
    for row in coverage["h1_outside_ordinary_hours"]:
        starts.update(_slots(row["start"], row["end_exclusive"], HOUR))
    if len(starts) != coverage["published_h1_slots"]:
        raise ValueError(f"{year} timestamp coverage does not reconcile")
    return starts


def scenario_calendar():
    holiday = {stamp for left, right in HOLIDAY_RANGES for stamp in _slots(left, right, HOUR)}

    def segment_key(stamp):
        if stamp in holiday:
            return "holiday", None
        if ordinary_open(stamp // 1000):
            return "session", stamp // DAY
        return "weekend", None

    segments = []
    for (kind, _), hours in groupby(range(START, END, HOUR), key=segment_key):
        stamps = list(hours)
        left, right = stamps[0], stamps[-1] + HOUR
        if kind != "session":
            segments.append({"kind": "closure", "start": left, "end": right, "reason": kind})
            continue
        session = {"kind": "session", "start": left, "end": right, "partial": right - left != DAY,
                   "h1": _edges(left, right, HOUR), "h4": _edges(left, right, 4 * HOUR)}
        if left % (4 * HOUR):
            session["leading_partial"] = True
        segments.append(session)
    record = {"kind": historical_calendar.KIND, "segments": segments}
    return record, historical_calendar.Calendar.from_record(
        record, sha256=data.digest(record), start=START, development_start=DEVELOPMENT_START, end=END, delay=DELAY,
    )


def report():
    observed, late_opening = set(), set()
    for year, expected_digest in EVIDENCE_SHA256.items():
        path = data.ROOT / f"reports/trendline-source-231/ev-{year}-coverage.json"
        receipt, digest = data.read_json(path)
        if digest != expected_digest:
            raise ValueError(f"{year} timestamp diagnostic differs from Sprint 231")
        coverage = receipt["ordinary_hours_comparison"]
        observed.update(_observed_starts(coverage, year))
        for span in coverage["m5_missing_within_published_h1"]:
            late_opening.update(t for t in _slots(span["start"], span["end_exclusive"], HOUR // 12) if t % HOUR == 0)

    record, calendar = scenario_calendar()
    starts = tuple(window.start for window in calendar.frame("H1"))
    count_hours = set(starts)
    windows = {
        frame: {
            "scheduled": len(calendar.frame(frame)),
            "modeled_warmup_complete_by_development_start": sum(
                window.end + DELAY <= DEVELOPMENT_START and observed.issuperset(window.children)
                for window in calendar.frame(frame)
            ),
        }
        for frame in FRAMES
    }
    development = tuple(window for window in calendar.frame("H4") if window.start >= DEVELOPMENT_START)
    closes = tuple(window.end for window in development)
    timing = {}
    for name, wait in (("clock", False), ("first_possible_quote", True)):
        slots = 0
        rows = entry_timing.compare_schedule(starts, closes, delay=DELAY, wait_for_first_open=wait)
        for window, row in zip(development, rows, strict=True):
            earliest, expiry = row["earliest_decision_at"], row["expires_at"]
            if earliest is None or expiry is None or not observed.issuperset(window.children):
                continue
            index = bisect_right(starts, earliest)
            if index < len(starts) - 1 and starts[index] < expiry:
                slots += starts[index] in observed and starts[index] not in late_opening
        timing[name] = slots

    return {
        "kind": "ev_2020_2022_holiday_calendar_scenario",
        "calendar": record,
        "calendar_sha256": calendar.sha256,
        "timestamp_report_sha256": EVIDENCE_SHA256,
        "holiday_hours": sum(len(_slots(left, right, HOUR)) for left, right in HOLIDAY_RANGES),
        "windows": windows,
        "missing_scheduled_h1": intervals({stamp // 1000 for stamp in count_hours - observed}, HOUR // 1000),
        "published_h1_outside_scenario": intervals({stamp // 1000 for stamp in observed - count_hours}, HOUR // 1000),
        "delayed_entry_timing_slots": timing,
        "calendar_qualified": False,
        "market_source_admitted": False,
        "market_data_read": False,
        "actual_counts": None,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", help="new JSON diagnostic report path")
    args = parser.parse_args()
    data.write_new(args.output, report())


if __name__ == "__main__":
    main()
