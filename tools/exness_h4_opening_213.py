"""Find first scheduled H1 opening evidence at H4 edges in the pinned July file."""

import argparse
from collections import Counter
import csv
import hashlib
import http.client
import json
import zipfile

from forex_demo_lab.elliott_sessions_146 import HOUR
from forex_demo_lab.exness_diagnostics_b import month_bounds
from forex_demo_lab.trendline import data, entry_timing
from tools.exness_2022_timing import clipped_buckets, ordinary_weeks
from tools.exness_opening_212 import archive_rows, download, first_pairs, month_schedule, summarize_month

MONTH = "2022-07"
PATH = "/ticks/EURUSD/2022/07/Exness_EURUSD_2022_07.zip"
LENGTH = 11_300_072
SHA256 = "b6ea0b6122cd87cd922eaccc19e2ce896f1004f70ce32243a944fea8cf2b7bd6"


def classify_edge(first, children, sampled_h1, timing):
    opening = timing["first_scheduled_open"]
    if opening not in sampled_h1 or timing["status"] == "NO_SCHEDULED_ENTRY":
        return "no_entry_opening_in_sample"
    if any(child not in first for child in children):
        return "missing_trigger_child"
    if opening not in first:
        return "no_opening_quote"
    if first[opening][0] > 0:
        return "first_quote_after_open"
    return "exact_source_open_" + {
        "EARLIEST_PUBLICATION_BEFORE_OPEN": "decision_early",
        "TIED_AT_EARLIEST_PUBLICATION": "same_time_order_unverified",
        "LATE_AT_EARLIEST_PUBLICATION": "decision_late",
    }[timing["status"]]


def compare_boundaries(first, h1, h4, start, end):
    starts = tuple(a for a, _ in h1)
    closes = tuple(b for _, b in h4)
    sampled_h1 = {a for a, b in h1 if start <= a < b <= end}
    triggers = {b: [child for child, child_end in h1 if a <= child < child_end <= b]
                for a, b in h4 if start <= a < b <= end}
    cases = []
    for delay in (0, 2000):
        timing = entry_timing.compare_schedule(starts, closes, delay=delay)
        counts = Counter(classify_edge(first, triggers[row["h4_end"]], sampled_h1, row)
                         for row in timing if row["h4_end"] in triggers)
        cases.append({"finalization_delay_ms": delay, "status_counts": dict(counts),
                      "exact_edges_not_ruled_out_by_modeled_time":
                          counts["exact_source_open_decision_early"] + counts["exact_source_open_same_time_order_unverified"]})
    return {"h4_intervals_in_sample": len(triggers), "timing_cases": cases}


def diagnose_july(body):
    windows, weekends = month_schedule(MONTH)
    rows = archive_rows(body, length=LENGTH, sha256=SHA256, member="Exness_EURUSD_2022_07.csv")
    first, total, outside = first_pairs(rows, windows)
    if total != 1_626_091:
        raise ValueError("prior audit row count mismatch")
    start, end = (int(stamp.timestamp()) * 1000 for stamp in month_bounds(MONTH))
    weeks = ordinary_weeks()
    boundaries = compare_boundaries(first, clipped_buckets(weeks, HOUR), clipped_buckets(weeks, 4 * HOUR), start, end)
    return {**summarize_month(first, total, outside, windows, weekends), "h4_boundaries": boundaries}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", help="new JSON diagnostic report path")
    args = parser.parse_args()
    scope = (data.ROOT / "docs/trendline/RESULTS-213.md").read_bytes().split(b"\n## Results\n", 1)[0]
    receipt = {"kind": "exness_july_2022_h4_opening_diagnostic", "expected_archive_sha256": SHA256,
               "scope_sha256": hashlib.sha256(scope).hexdigest(), "status": "stopped"}
    with data.no_links(args.output).open("x", encoding="utf-8", newline="\n") as output:
        try:
            result = diagnose_july(download(path=PATH, length=LENGTH))
            receipt.update(result, status="complete", archive_sha256=SHA256)
        except (OSError, http.client.HTTPException, ValueError, zipfile.BadZipFile, csv.Error) as error:
            receipt["error_type"] = type(error).__name__
        output.write(json.dumps(receipt, indent=2) + "\n")
    if receipt["status"] != "complete":
        raise SystemExit("H4 opening diagnostic stopped")


if __name__ == "__main__":
    main()
