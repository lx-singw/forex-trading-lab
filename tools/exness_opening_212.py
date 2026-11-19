"""Inspect paired H1 opening proxies from the pinned January 2022 archive."""

import argparse
from bisect import bisect_right
from collections import Counter
import csv
from fractions import Fraction
import hashlib
import http.client
import io
import json
import time
import zipfile

from forex_demo_lab.elliott_sessions_146 import HOUR
from forex_demo_lab.exness_diagnostics_b import HEADER, inspect_archive, month_bounds, timestamp_ms
from forex_demo_lab.trendline import data, fills
from tools.exness_2022_timing import clipped_buckets, ordinary_weeks

HOST = "ticks.ex2archive.com"
PATH = "/ticks/EURUSD/2022/01/Exness_EURUSD_2022_01.zip"
LENGTH = 5_412_286
SHA256 = "d98fc8a0d7b7fb144b8b4be78810e18498e7d43cf1da889c7eb09db5fed07873"


def download():
    connection = http.client.HTTPSConnection(HOST, timeout=10)
    started = time.monotonic()
    try:
        connection.request("GET", PATH)
        response = connection.getresponse()
        if (response.status != 200 or response.getheader("Content-Type") != "application/zip"
                or response.getheader("Content-Length") != str(LENGTH) or response.getheader("Location") is not None):
            raise ValueError("unexpected archive response")
        body = bytearray()
        while len(body) < LENGTH:
            if time.monotonic() - started > 45:
                raise TimeoutError("archive response deadline")
            block = response.read(min(65_536, LENGTH - len(body)))
            if not block:
                break
            body.extend(block)
        if time.monotonic() - started > 45:
            raise TimeoutError("archive response deadline")
        return body
    finally:
        connection.close()


def archive_rows(body):
    if len(body) != LENGTH or hashlib.sha256(body).hexdigest() != SHA256:
        raise ValueError("archive differs from the audited January bytes")
    with zipfile.ZipFile(io.BytesIO(body)) as archive:
        members, _ = inspect_archive(archive, max_members=1)
        if [entry.filename for entry in members] != ["Exness_EURUSD_2022_01.csv"]:
            raise ValueError("unexpected archive member")
        with archive.open(members[0]) as binary:
            reader = csv.reader(io.TextIOWrapper(binary, encoding="utf-8", newline=""), strict=True)
            if next(reader, None) != HEADER:
                raise ValueError("unexpected archive header")
            for provider, symbol, stamp, bid, ask in reader:
                if (provider, symbol) != ("exness", "EURUSD"):
                    raise ValueError("unexpected source or symbol")
                yield timestamp_ms(stamp), bid, ask


def january_schedule():
    start, end = (int(stamp.timestamp()) * 1000 for stamp in month_bounds("2022-01"))
    weeks = ordinary_weeks()
    h1 = [(a, b) for a, b in clipped_buckets(weeks, HOUR) if start <= a < b <= end]
    weekends = []
    for week, next_week in zip(weeks, weeks[1:]):
        reopening = int(next_week[0].timestamp()) * 1000
        if not start <= reopening < end:
            continue
        friday = clipped_buckets([week], 4 * HOUR)[-1]
        children = [a for a, b in h1 if friday[0] <= a < b <= friday[1]]
        if children:
            weekends.append((reopening, children))
    return h1, weekends


def summarize(openings):
    counts = Counter("exact" if lag == 0 else "below_one_second" if lag < 1000 else "at_least_one_second"
                     for lag, _ in openings)
    spreads = sorted(spread for _, spread in openings)
    return {"paired_proxies": len(openings), "exact_source_edge": counts["exact"],
            "positive_below_one_second": counts["below_one_second"],
            "at_least_one_second": counts["at_least_one_second"],
            "spread_pips_p50": fills.text(spreads[(len(spreads) - 1) // 2]) if spreads else None,
            "spread_pips_p95": fills.text(spreads[(95 * len(spreads) - 1) // 100]) if spreads else None}


def diagnose(rows, windows, weekends):
    starts = tuple(start for start, _ in windows)
    first = {}
    total = outside = 0
    previous = None
    for stamp, bid, ask in rows:
        if previous is not None and stamp < previous:
            raise ValueError("archive timestamps out of order")
        previous = stamp
        total += 1
        index = bisect_right(starts, stamp) - 1
        if index < 0 or stamp >= windows[index][1]:
            outside += 1
        elif starts[index] not in first:
            first[starts[index]] = (stamp - starts[index], (Fraction(ask) - Fraction(bid)) / fills.PIP)
    sunday = [first[opening] for opening, _ in weekends if opening in first]
    return {
        "rows": total, "outside_modeled_h1": outside, "scheduled_h1": len(windows),
        "h1_with_no_quote": len(windows) - len(first), "h1_openings": summarize(list(first.values())),
        "weekends_checked": len(weekends), "sunday_openings": summarize(sunday),
        "friday_h4_with_all_children_present": sum(all(child in first for child in children)
                                                   for _, children in weekends),
        "observed_receipt_times_available": False, "market_source_admitted": False,
        "actual_strategy_counts": None,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", help="new JSON diagnostic report path")
    args = parser.parse_args()
    scope = (data.ROOT / "docs/trendline/RESULTS-212.md").read_bytes().split(b"\n## Results\n", 1)[0]
    receipt = {"kind": "exness_january_2022_opening_diagnostic", "expected_archive_sha256": SHA256,
               "scope_sha256": hashlib.sha256(scope).hexdigest(), "status": "stopped"}
    with data.no_links(args.output).open("x", encoding="utf-8", newline="\n") as output:
        try:
            result = diagnose(archive_rows(download()), *january_schedule())
            if result["rows"] != 748_560:
                raise ValueError("prior audit row count mismatch")
            receipt.update(result, status="complete", archive_sha256=SHA256)
        except (OSError, http.client.HTTPException, ValueError, zipfile.BadZipFile, csv.Error) as error:
            receipt["error_type"] = type(error).__name__
        output.write(json.dumps(receipt, indent=2) + "\n")
    if receipt["status"] != "complete":
        raise SystemExit("opening diagnostic stopped")


if __name__ == "__main__":
    main()
