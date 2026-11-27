"""Audit the completed-opening-bar receipt deadline on retained calendar scenarios."""

import argparse
from bisect import bisect_right
from collections import Counter

from forex_demo_lab.trendline import data, entry_timing, historical_calendar
from tools import ev_holiday_calendar_232 as ev
from tools import exness_2022_calendar_220 as exness

DELAY = 2000
SCENARIOS = {
    "exness_2022": (
        "reports/trendline-source-220/exness-2022-calendar.json",
        "c2b0925223b560bbbcc4623b9bf8fbd6150ba05347c893f1cae7d2cf6665373f",
        exness.START, exness.START, exness.END,
    ),
    "ev_2021_2022": (
        "reports/trendline-source-232/ev-holiday-calendar-scenario.json",
        "c84f293e341a76c2fdfab24480430afb46263c21b97088e7e40bef33d7025103",
        ev.START, ev.DEVELOPMENT_START, ev.END,
    ),
}


def deadline_counts(hours, closes, *, decision_delay, opening_delay, wait_for_quote):
    """Measure schedule feasibility before source availability or price checks."""
    data.integer(opening_delay)
    starts = tuple(hour.start for hour in hours)
    liquidation = starts[-1]
    timing = entry_timing.compare_schedule(
        starts, closes, delay=decision_delay, wait_for_first_open=wait_for_quote,
    )
    slack = Counter()
    for row in timing:
        decision = row["earliest_decision_at"]
        expiry = row["expires_at"]
        if decision is None or expiry is None:
            continue
        index = bisect_right(starts, decision)
        if index >= len(starts) or starts[index] >= min(expiry, liquidation):
            continue
        slack[expiry - hours[index].end] += 1

    too_late = sum(count for remaining, count in slack.items() if remaining < opening_delay)
    selected = sum(slack.values())
    return {
        "selected_h1_slots": selected,
        "excluded_by_completed_bar_deadline": too_late,
        "completed_bar_timing_ceiling": selected - too_late,
        "expiry_minus_h1_end_ms": dict(sorted(slack.items())),
    }


def report():
    results = {}
    for name, (path, expected_sha, start, development_start, end) in SCENARIOS.items():
        evidence, digest = data.read_json(data.ROOT / path)
        if digest != expected_sha:
            raise ValueError(f"{name} differs from the retained calendar scenario")
        record = evidence["calendar"]
        calendar = historical_calendar.Calendar.from_record(
            record, sha256=data.digest(record), start=start,
            development_start=development_start, end=end, delay=DELAY,
        )
        if calendar.sha256 != evidence["calendar_sha256"]:
            raise ValueError(f"{name} calendar binding differs")
        hours = calendar.frame("H1")
        closes = tuple(window.end for window in calendar.frame("H4") if window.start >= development_start)
        results[name] = {
            "scenario_report_sha256": digest,
            "calendar_sha256": calendar.sha256,
            "development_h4_closes": len(closes),
            "clock": deadline_counts(
                hours, closes, decision_delay=DELAY, opening_delay=calendar.delay, wait_for_quote=False,
            ),
            "first_possible_quote": deadline_counts(
                hours, closes, decision_delay=DELAY, opening_delay=calendar.delay, wait_for_quote=True,
            ),
        }
    return {
        "kind": "level_b_completed_opening_bar_deadline_scenarios",
        "assumed_decision_delay_ms": DELAY,
        "minimum_bar_opening_delay_ms": DELAY,
        "scenarios": results,
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
