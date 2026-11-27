"""Compare delayed-entry publication assumptions on retained EV timestamp metadata."""

import argparse
from bisect import bisect_left, bisect_right
from collections import Counter
from dataclasses import dataclass

from forex_demo_lab.elliott_sessions_146 import HOUR
from forex_demo_lab.trendline import data, historical_calendar
from tools.ev_holiday_calendar_232 import DEVELOPMENT_START, END, EVIDENCE_SHA256, START, _slots

SCENARIO_SHA256 = "c84f293e341a76c2fdfab24480430afb46263c21b97088e7e40bef33d7025103"
MAX_DELAY = 4 * HOUR
CHECKPOINTS = (0, 2000, 300_000, HOUR // 2, HOUR, 2 * HOUR, 3 * HOUR, MAX_DELAY)


@dataclass(frozen=True)
class EntryWindow:
    close: int
    openings: tuple[int, ...]

    def select(self, delay, *, wait_for_quote):
        if not self.openings:
            return None
        release = self.openings[0] if wait_for_quote else self.close
        index = bisect_right(self.openings, release + delay)
        return self.openings[index] if index < len(self.openings) else None


def windows(calendar):
    starts = tuple(window.start for window in calendar.frame("H1"))
    closes = tuple(window.end for window in calendar.frame("H4") if window.start >= DEVELOPMENT_START)
    for close, expiry in zip(closes, (*closes[1:], starts[-1]), strict=True):
        left = bisect_left(starts, close)
        right = bisect_left(starts, min(expiry, starts[-1]))
        yield EntryWindow(close, starts[left:right])


def comparison(entry_windows, late, delay):
    counts = Counter()
    for window in entry_windows:
        clock_open = window.select(delay, wait_for_quote=False)
        quote_open = window.select(delay, wait_for_quote=True)
        clock_ok = clock_open is not None and clock_open not in late
        quote_ok = quote_open is not None and quote_open not in late
        if clock_ok and quote_ok:
            counts["same_open" if clock_open == quote_open else "different_open"] += 1
        elif clock_ok:
            counts["clock_only"] += 1
        elif quote_ok:
            counts["first_possible_quote_only"] += 1
        else:
            counts["neither"] += 1
        counts["clock_late"] += clock_open in late
        counts["first_possible_quote_late"] += quote_open in late

    return {
        "delay_ms": delay,
        "clock": counts["same_open"] + counts["different_open"] + counts["clock_only"],
        "first_possible_quote": counts["same_open"] + counts["different_open"] + counts["first_possible_quote_only"],
        **{name: counts[name] for name in (
            "same_open", "different_open", "clock_only", "first_possible_quote_only",
            "neither", "clock_late", "first_possible_quote_late",
        )},
    }


def selection_breakpoints(entry_windows):
    """Return nonnegative millisecond delays where selection can change."""
    return sorted({
        opening - release
        for window in entry_windows if window.openings
        for release in (window.close, window.openings[0])
        for opening in window.openings
        if 0 <= opening - release <= MAX_DELAY
    })


def report():
    scenario, digest = data.read_json(data.ROOT / "reports/trendline-source-232/ev-holiday-calendar-scenario.json")
    if digest != SCENARIO_SHA256:
        raise ValueError("holiday scenario differs from Sprint 232")
    calendar = historical_calendar.Calendar.from_record(
        scenario["calendar"], sha256=scenario["calendar_sha256"], start=START,
        development_start=DEVELOPMENT_START, end=END, delay=0,
    )
    if scenario["missing_scheduled_h1"] or scenario["published_h1_outside_scenario"]:
        raise ValueError("sensitivity comparison requires reconciled H1 coverage")

    late = set()
    for year, expected_digest in EVIDENCE_SHA256.items():
        receipt, digest = data.read_json(data.ROOT / f"reports/trendline-source-231/ev-{year}-coverage.json")
        if digest != expected_digest:
            raise ValueError(f"{year} timestamp diagnostic differs from Sprint 231")
        for span in receipt["ordinary_hours_comparison"]["m5_missing_within_published_h1"]:
            stamps = _slots(span["start"], span["end_exclusive"], HOUR // 12)
            late.update(stamp for stamp in stamps if stamp % HOUR == 0)

    entries = tuple(windows(calendar))
    breakpoints = selection_breakpoints(entries)
    delays = set(CHECKPOINTS) | set(breakpoints) | {point - 1 for point in breakpoints if point > 0}
    return {
        "kind": "ev_delayed_entry_publication_sensitivity_scenario",
        "scenario_report_sha256": SCENARIO_SHA256,
        "calendar_sha256": calendar.sha256,
        "timestamp_report_sha256": EVIDENCE_SHA256,
        "development_h4_closes": len(entries),
        "selection_breakpoints_ms": breakpoints,
        "rows": [comparison(entries, late, delay) for delay in sorted(delays)],
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
