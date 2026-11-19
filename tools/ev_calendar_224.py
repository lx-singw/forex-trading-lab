"""Compare the pinned EV 2024 publication with Dukascopy ordinary hours."""

import argparse
from datetime import UTC, datetime
import hashlib
from zoneinfo import ZoneInfo

from forex_demo_lab.trendline import data
from tools.ev_opening_resample_223 import END, FILES, START, download, parse

HOUR = 3600
FIVE_MINUTES = 300
NEW_YORK = ZoneInfo("America/New_York")
PINNED = {
    "H1": "66fa719d8e7d75c11e1c691b232471fe3c9323e91ed998e8b82fe943f85d38b2",
    "M5": "751c4210dd2db4cc1583d10d4e3609551b40f6e14026a01438f6962040df49b3",
}
HOLIDAY_DATES = {(1, 1), (1, 2), (12, 24), (12, 25), (12, 26), (12, 31)}


def ordinary_open(stamp):
    local = datetime.fromtimestamp(stamp, NEW_YORK)
    weekday = local.weekday()
    return (weekday < 4 or (weekday == 4 and local.hour < 17)
            or (weekday == 6 and local.hour >= 17))


def _utc(stamp):
    return datetime.fromtimestamp(stamp, UTC).isoformat()


def intervals(stamps, period):
    ranges = []
    for stamp in sorted(stamps):
        if ranges and stamp == ranges[-1][1]:
            ranges[-1][1] = stamp + period
        else:
            ranges.append([stamp, stamp + period])
    return [
        {"start": _utc(start), "end_exclusive": _utc(end), "slots": (end - start) // period}
        for start, end in ranges
    ]


def compare(hourly, five_minute, expected):
    missing = expected - hourly
    outside = hourly - expected
    missing_in_notice_windows = set()
    for stamp in missing:
        day = datetime.fromtimestamp(stamp, UTC)
        if (day.month, day.day) in HOLIDAY_DATES:
            missing_in_notice_windows.add(stamp)
    missing_m5 = {
        stamp for start in hourly for stamp in range(start, start + HOUR, FIVE_MINUTES)
    } - five_minute
    outside_m5 = {stamp for stamp in five_minute if stamp - stamp % HOUR not in expected}
    return {
        "ordinary_h1_slots": len(expected),
        "published_h1_slots": len(hourly),
        "h1_slots_in_common": len(hourly & expected),
        "h1_missing": intervals(missing, HOUR),
        "h1_missing_inside_holiday_notice_windows": len(missing_in_notice_windows),
        "h1_missing_outside_holiday_notice_windows": intervals(missing - missing_in_notice_windows, HOUR),
        "h1_outside_ordinary_hours": intervals(outside, HOUR),
        "published_m5_slots": len(five_minute),
        "m5_missing_within_published_h1": intervals(missing_m5, FIVE_MINUTES),
        "m5_outside_ordinary_hours": intervals(outside_m5, FIVE_MINUTES),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", help="new JSON diagnostic report path")
    output = parser.parse_args().output
    timestamps = {}
    for frame, (period, length) in FILES.items():
        body = download(frame, length)
        if hashlib.sha256(body).hexdigest() != PINNED[frame]:
            raise ValueError(f"{frame} gzip digest differs from Sprint 223")
        timestamps[frame] = set(parse(body, period))
    expected = {stamp for stamp in range(START, END, HOUR) if ordinary_open(stamp)}
    data.write_new(output, {
        "kind": "ev_2024_ordinary_calendar_diagnostic",
        "symbol": "EURUSD",
        "start_inclusive": _utc(START),
        "end_exclusive": _utc(END),
        "input_sha256": PINNED,
        **compare(timestamps["H1"], timestamps["M5"], expected),
        "calendar_qualified": False,
        "market_source_admitted": False,
        "actual_counts": None,
    })


if __name__ == "__main__":
    main()
