"""Model timing on the published ordinary Exness forex hours in 2022."""

import argparse
from datetime import UTC, datetime, timedelta

from forex_demo_lab.elliott_sessions_146 import HOUR
from forex_demo_lab.trendline import data, entry_timing


def ordinary_weeks():
    """Repeat the winter and summer snapshots over the corresponding US DST weeks."""
    sunday = datetime(2022, 1, 2, tzinfo=UTC)
    summer_from = datetime(2022, 3, 13, tzinfo=UTC)
    winter_from = datetime(2022, 11, 6, tzinfo=UTC)
    weeks = []
    while sunday.year == 2022:
        summer = summer_from <= sunday < winter_from
        opening = sunday.replace(hour=21 if summer else 22, minute=5)
        friday = sunday + timedelta(days=5)
        closing = friday.replace(hour=20 if summer else 21, minute=59)
        weeks.append((opening, closing, "summer" if summer else "winter"))
        sunday += timedelta(days=7)
    return weeks


def clipped_buckets(weeks, width):
    buckets = []
    for opening, closing, _ in weeks:
        start, end = int(opening.timestamp()) * 1000, int(closing.timestamp()) * 1000
        aligned_start = start - (start % width)
        buckets.extend((max(edge, start), min(edge + width, end))
                       for edge in range(aligned_start, end, width))
    return buckets


def report(*, wait_for_first_open=False):
    weeks = ordinary_weeks()
    starts = tuple(start for start, _ in clipped_buckets(weeks, HOUR))
    h4 = clipped_buckets(weeks, 4 * HOUR)
    closes = tuple(end for _, end in h4)
    cases = []
    for delay in (0, 2000):
        rows = entry_timing.compare_schedule(starts, closes, delay=delay, wait_for_first_open=wait_for_first_open)
        full = [row for row, (start, end) in zip(rows, h4, strict=True) if end - start == 4 * HOUR]
        cases.append({"finalization_delay_ms": delay, "all_h4": entry_timing.summarize(rows),
                      "full_h4_only": entry_timing.summarize(full)})
    return {
        "kind": ("exness_2022_next_quote_timing_scenario" if wait_for_first_open
                 else "exness_2022_ordinary_hours_timing_scenario"),
        "schedule_qualified": False, "actual_counts": None, "scheduled_h1": len(starts),
        "weekly_windows": [{"opens_at": start.isoformat(), "closes_at": end.isoformat(), "season": season}
                           for start, end, season in weeks],
        "timing_cases": cases,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", help="new JSON report path")
    parser.add_argument("--wait-for-first-open", action="store_true",
                        help="assume publication needs a quote arriving no earlier than the first scheduled open")
    args = parser.parse_args()
    data.write_new(args.output, report(wait_for_first_open=args.wait_for_first_open))


if __name__ == "__main__":
    main()
