"""Audit the earliest Level B entry decision times on an invented calendar."""

import argparse
from bisect import bisect_left
from collections import Counter

from ..elliott_sessions_146 import Calendar
from . import data


def audit(calendar_record):
    """Compare each H4 publication lower bound with its first scheduled H1 open."""
    calendar = Calendar.from_record(calendar_record)
    starts = tuple(window.start for window in calendar.frame("H1"))
    closes = tuple(window.end for window in calendar.frame("H4"))
    rows = compare_schedule(starts, closes, delay=calendar.delay)
    return {
        "kind": "invented_level_b_entry_timing_audit", "calendar_sha256": calendar.sha256,
        "finalization_delay_ms": calendar.delay, **summarize(rows), "h4": rows,
    }


def compare_schedule(h1_starts, h4_closes, *, delay, wait_for_first_open=False):
    """Compare schedule edges and a delay in milliseconds without reading prices.

    If publication needs the next quote and none can arrive during the gap,
    the first scheduled H1 open is an optimistic lower bound for that quote.
    """
    data.integer(delay)
    for edges in (h1_starts, h4_closes):
        for edge in edges:
            data.integer(edge)
        if any(left >= right for left, right in zip(edges, edges[1:])):
            raise ValueError("strictly increasing schedule edges required")
    rows = []
    for close, expiry in zip(h4_closes, (*h4_closes[1:], None), strict=True):
        index = bisect_left(h1_starts, close)
        first_open = h1_starts[index] if index < len(h1_starts) else None
        publication_floor = first_open if wait_for_first_open else close
        earliest = publication_floor + delay if publication_floor is not None else None
        if first_open is None or expiry is None or first_open >= expiry:
            status = "NO_SCHEDULED_ENTRY"
        elif earliest > first_open:
            status = "LATE_AT_EARLIEST_PUBLICATION"
        elif earliest == first_open:
            status = "TIED_AT_EARLIEST_PUBLICATION"
        else:
            status = "EARLIEST_PUBLICATION_BEFORE_OPEN"
        rows.append({"h4_end": close, "first_scheduled_open": first_open, "expires_at": expiry,
                     "earliest_decision_at": earliest, "status": status})
    return rows


def summarize(rows):
    counts = Counter(row["status"] for row in rows)
    before = counts["EARLIEST_PUBLICATION_BEFORE_OPEN"]
    return {
        "scheduled_h4_closes": len(rows),
        "status_counts": dict(counts), "ceiling_without_same_time_order": before,
        "ceiling_if_decision_precedes_tied_open": before + counts["TIED_AT_EARLIEST_PUBLICATION"],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("calendar", help="invented calendar JSON")
    parser.add_argument("report", help="new JSON report path")
    args = parser.parse_args()
    value, _ = data.read_json(args.calendar)
    data.write_new(args.report, audit(value))


if __name__ == "__main__":
    main()
