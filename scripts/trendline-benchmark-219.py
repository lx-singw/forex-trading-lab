"""Benchmark the Phase 10 counter using temporary fabricated data."""

import argparse
from datetime import datetime, timezone
from resource import RUSAGE_SELF, getrusage
from time import perf_counter

from forex_demo_lab.trendline import data, historical_count
from test_trendline_historical_input_216 import HistoricalInputTests, HOUR, midnight, row, session
from test_trendline_signal_count_194 import bar_fixture, count_b


def full_window(fixture, dense):
    start, end = midnight(2020), midnight(2023)
    day = 24 * HOUR
    fixture.rows = []
    segments = []
    warmup_hours = 0
    for left in range(start, end, day):
        if datetime.fromtimestamp(left // 1000, timezone.utc).weekday() < 5:
            segments.append(session(left, left + day))
            fixture.rows.extend(row(hour) for hour in range(left, left + day, HOUR))
            warmup_hours += 24 if left < fixture.seam else 0
        elif segments[-1]["kind"] == "closure":
            segments[-1]["end"] += day
        else:
            segments.append({"kind": "closure", "start": left, "end": left + day, "reason": "weekend"})
    fixture.calendar["segments"] = segments

    if dense:
        # Frequent tied-price pivots build up rejected-pair trace volume.
        for index, hour in enumerate(fixture.rows):
            phase = index // 4 % 12
            if phase == 0:
                hour["high"] = "1.1020"
            elif phase == 6:
                hour["low"] = "1.0980"
        return

    _, pattern, _ = bar_fixture()
    # The first setup uses warmup state. The rest are spaced beyond the
    # line lookback so the test has recurring setups and bounded pivot density.
    for first in range(warmup_hours - 8 * 24, len(fixture.rows) - len(pattern) + 1, 4 * 720):
        for hour, shaped in zip(fixture.rows[first:first + len(pattern)], pattern, strict=True):
            hour.update({field: shaped[field] for field in ("open", "high", "low", "close", "spread_pips")})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output")
    size = parser.add_mutually_exclusive_group()
    size.add_argument("--short", action="store_true", help="run the 49-H4-bar BRK3 comparison fixture")
    size.add_argument("--dense", action="store_true", help="stress the bounded trace with frequent pivots")
    args = parser.parse_args()
    if args.short:
        value, rows, opening = bar_fixture()
        started = perf_counter()
        report = count_b(value, rows, cutoff=opening["available_at"])
    else:
        fixture = HistoricalInputTests()
        fixture.setUp()
        try:
            full_window(fixture, args.dense)
            with fixture.bundle():
                started = perf_counter()
                try:
                    report = historical_count.count(fixture.manifest)
                except ValueError as error:
                    if not args.dense or "bounded replay trace" not in str(error):
                        raise
                    data.write_new(args.output, {
                        "kind": "fabricated_trendline_count_benchmark",
                        "elapsed_seconds": round(perf_counter() - started, 3),
                        "max_rss_kib": getrusage(RUSAGE_SELF).ru_maxrss,
                        "market_data_read": False,
                        "error": str(error),
                    })
                    return
        finally:
            fixture.doCleanups()
        report["actual_source_admitted"] = False
        report["market_data_read"] = False
        report["input_receipt"]["market_data_read"] = False
        report["fabricated_opportunity_counts"] = report["feasibility"].pop("actual_counts")
        report["feasibility"].update(status="UNAVAILABLE", actual_counts=None)
    data.write_new(args.output, {
        "kind": "fabricated_trendline_count_benchmark",
        "elapsed_seconds": round(perf_counter() - started, 3),
        "max_rss_kib": getrusage(RUSAGE_SELF).ru_maxrss,
        "cells_sha256": data.digest(report["cells"]),
        "count_report": report,
    })


if __name__ == "__main__":
    main()
