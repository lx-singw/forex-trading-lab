"""Audit the earliest Level B entry decision times on an invented calendar."""

import argparse
from bisect import bisect_left
from collections import Counter

from ..elliott_sessions_146 import Calendar
from . import data


def audit(calendar_record):
    """Compare each H4 publication lower bound with its first scheduled H1 open."""
    calendar = Calendar.from_record(calendar_record)
    starts = [window.start for window in calendar.frame("H1")]
    h4 = calendar.frame("H4")
    rows = []
    for trigger, following in zip(h4, (*h4[1:], None), strict=True):
        earliest = trigger.end + calendar.delay
        index = bisect_left(starts, trigger.end)
        first_open = starts[index] if index < len(starts) else None
        expiry = following.end if following is not None else None
        if first_open is None or expiry is None or first_open >= expiry:
            status = "NO_SCHEDULED_ENTRY"
        elif earliest > first_open:
            status = "LATE_AT_EARLIEST_PUBLICATION"
        elif earliest == first_open:
            status = "TIED_AT_EARLIEST_PUBLICATION"
        else:
            status = "EARLIEST_PUBLICATION_BEFORE_OPEN"
        rows.append({"h4_end": trigger.end, "first_scheduled_open": first_open, "expires_at": expiry,
                     "earliest_decision_at": earliest, "status": status})

    counts = Counter(row["status"] for row in rows)
    before = counts["EARLIEST_PUBLICATION_BEFORE_OPEN"]
    return {
        "kind": "invented_level_b_entry_timing_audit", "calendar_sha256": calendar.sha256,
        "finalization_delay_ms": calendar.delay, "scheduled_h4_closes": len(rows),
        "status_counts": dict(counts), "ceiling_without_same_time_order": before,
        "ceiling_if_decision_precedes_tied_open": before + counts["TIED_AT_EARLIEST_PUBLICATION"],
        "h4": rows,
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
