"""Check the Exness ordinary-hours scenario against the historical calendar reader."""

import argparse
from collections import Counter
from datetime import UTC, datetime

from forex_demo_lab.elliott_sessions_146 import FRAMES, HOUR
from forex_demo_lab.trendline import data, entry_timing, historical_calendar
from tools.exness_2022_timing import clipped_buckets, ordinary_weeks

DAY = 24 * HOUR
START = int(datetime(2022, 1, 1, tzinfo=UTC).timestamp()) * 1000
END = int(datetime(2023, 1, 1, tzinfo=UTC).timestamp()) * 1000


def _edges(start, end, period):
    next_edge = start - start % period + period
    return [start, *range(next_edge, end, period), end]


def _closure(start, end):
    return {"kind": "closure", "start": start, "end": end, "reason": "weekend"}


def calendar_record(weeks):
    segments = []
    cursor = START
    for opening, closing, _ in weeks:
        start, end = (int(instant.timestamp()) * 1000 for instant in (opening, closing))
        segments.append(_closure(cursor, start))
        for left in (start, *range(start - start % DAY + DAY, end, DAY)):
            right = min(left - left % DAY + DAY, end)
            session = {"kind": "session", "start": left, "end": right, "partial": right - left != DAY,
                       "h1": _edges(left, right, HOUR), "h4": _edges(left, right, 4 * HOUR)}
            if left % HOUR:
                session["leading_partial"] = True
            segments.append(session)
        cursor = end
    segments.append(_closure(cursor, END))
    return {"kind": historical_calendar.KIND, "segments": segments}


def report():
    weeks = ordinary_weeks()
    record = calendar_record(weeks)
    digest = data.digest(record)
    calendar = historical_calendar.Calendar.from_record(
        record, sha256=digest, start=START, development_start=START, end=END, delay=2000,
    )
    h1, h4 = (calendar.frame(frame) for frame in ("H1", "H4"))
    for windows, width in ((h1, HOUR), (h4, 4 * HOUR)):
        if [(window.start, window.end) for window in windows] != clipped_buckets(weeks, width):
            raise ValueError("calendar differs from the declared ordinary-hours grid")
    durations = {}
    for frame in FRAMES:
        counts = Counter((window.end - window.start) // 60_000 for window in calendar.frame(frame))
        durations[frame] = {str(minutes): count for minutes, count in sorted(counts.items())}
    rows = entry_timing.compare_schedule(tuple(window.start for window in h1),
                                         tuple(window.end for window in h4), delay=calendar.delay)
    return {
        "kind": "exness_2022_calendar_compatibility_scenario",
        "calendar_sha256": digest, "calendar": record,
        "scheduled_by_frame": {frame: len(calendar.frame(frame)) for frame in FRAMES},
        "duration_counts_by_frame_minutes": durations,
        "timing_at_two_seconds": entry_timing.summarize(rows),
        "schedule_qualified": False, "market_data_read": False, "actual_counts": None,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", help="new JSON report path")
    data.write_new(parser.parse_args().output, report())


if __name__ == "__main__":
    main()
