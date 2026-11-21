"""Audit the exact EV 2020–2022 EURUSD H1 and M5 catalogue entries."""

import argparse
import hashlib

from forex_demo_lab.trendline import data
from tools import ev_calendar_224 as calendar
from tools import ev_opening_resample_223 as resample

# Compressed bytes, row count, first and last UTC labels in Sprint 229.
INVENTORY = {
    2020: {"H1": (202_167, 6250, 1577916000, 1609448400), "M5": (1_992_465, 74984, 1577916000, 1609451700)},
    2021: {"H1": (192_283, 6240, 1609711200, 1640984400), "M5": (1_876_230, 74863, 1609711200, 1640987700)},
    2022: {"H1": (204_935, 6240, 1641160800, 1672434000), "M5": (2_039_455, 74872, 1641160800, 1672437300)},
}


def audit(year):
    start, end = resample.year_bounds(year)
    inputs, opens = {}, {}
    for frame, (size, rows, first, last) in INVENTORY[year].items():
        body = resample.download(frame, size, year=year)
        entries = resample.parse(body, resample.FILES[frame][0], year=year)
        if (len(entries), min(entries), max(entries)) != (rows, first, last):
            raise ValueError(f"{year} {frame} row count or UTC edges differ from Sprint 229")
        inputs[frame] = {"sha256": hashlib.sha256(body).hexdigest(), "compressed_bytes": len(body)}
        opens[frame] = entries

    hourly, five_minute = opens["H1"], opens["M5"]
    expected = {stamp for stamp in range(start, end, calendar.HOUR) if calendar.ordinary_open(stamp)}
    return {
        "kind": "ev_development_archive_coverage_diagnostic",
        "symbol": "EURUSD",
        "year": year,
        "inputs": inputs,
        "ordinary_hours_comparison": calendar.compare(set(hourly), set(five_minute), expected),
        "opening_pair_comparison": resample.compare(hourly, five_minute),
        "calendar_qualified": False,
        "first_tick_provenance_verified": False,
        "availability_model_qualified": False,
        "market_source_admitted": False,
        "actual_counts": None,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("year", type=int, choices=tuple(INVENTORY))
    parser.add_argument("output", help="new JSON diagnostic report path")
    args = parser.parse_args()
    data.write_new(args.output, audit(args.year))


if __name__ == "__main__":
    main()
