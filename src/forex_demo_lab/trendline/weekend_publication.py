"""Check observed Friday H4 availability against the next scheduled H1 opening."""

import argparse

from ..elliott_sessions_146 import Calendar
from . import data, fills

TRACE_KIND = "invented_weekend_publication_trace"
EVENT_KINDS = ("h4_unavailable", "h4_completed", "eurusd_update", "scheduled_h1_open")


def _weekend_window(calendar, h4_end):
    data.integer(h4_end)
    if all(window.end != h4_end for window in calendar.frame("H4")):
        raise ValueError("declared H4 close required")
    opening = next((window for window in calendar.frame("H1") if window.start >= h4_end), None)
    if opening is None or not any(
        segment["kind"] == "closure" and segment["reason"] == "weekend"
        and segment["start"] == h4_end and segment["end"] == opening.start
        for segment in calendar.record()["segments"]
    ):
        raise ValueError("H4 close and next H1 must border a declared weekend")
    return opening


def _observation_order(completed, opening, scheduled_at):
    if completed is None:
        return "COMPLETION_UNOBSERVED"
    if completed.time == scheduled_at and opening is None:
        return "SAME_TIME_ORDER_UNRESOLVED"
    before = completed < opening if opening is not None else completed.time < scheduled_at
    return "BEFORE_OPEN" if before else "AFTER_OPEN"


def audit(trace):
    """Use only the ordering witnessed in one invented observation trace."""
    data.fields(trace, ("kind", "calendar", "h4_end", "events"))
    if trace["kind"] != TRACE_KIND:
        raise ValueError("invented weekend publication trace required")
    calendar = Calendar.from_record(trace["calendar"])
    h4_end = trace["h4_end"]
    window = _weekend_window(calendar, h4_end)
    if type(trace["events"]) is not list or len(trace["events"]) > data.ROW_LIMIT:
        raise ValueError("bounded receipt events required")

    previous = unavailable = completed = opening = first_update = reopening_update = None
    closure_updates = 0
    for row in trace["events"]:
        data.fields(row, ("kind", "time", "ordinal"))
        kind = row["kind"]
        event = fills.Event(row["time"], row["ordinal"])
        if kind not in EVENT_KINDS or not h4_end <= event.time <= calendar.end:
            raise ValueError("unknown or out-of-scope receipt event")
        if previous is not None and event <= previous:
            raise ValueError("receipt events must be strictly ordered by time and then ordinal")
        if kind == "h4_unavailable":
            if completed is not None:
                raise ValueError("H4 visibility regressed within one trace")
            unavailable = event
        elif kind == "h4_completed":
            if completed is None:
                completed = event
        elif kind == "scheduled_h1_open":
            if opening is not None or event.time != window.start:
                raise ValueError("single opening marker at the scheduled time required")
            opening = event
        else:
            if first_update is None:
                first_update = event
            if event.time < window.start:
                closure_updates += 1
            elif reopening_update is None:
                reopening_update = event
        previous = event

    return {
        "kind": "invented_weekend_publication_audit", "calendar_sha256": calendar.sha256,
        "h4_end": h4_end, "scheduled_h1_open": window.start,
        "opening_marker": opening.record() if opening is not None else None,
        "last_unavailable_observed": unavailable.record() if unavailable is not None else None,
        "first_completed_observed": completed.record() if completed is not None else None,
        "first_eurusd_update_observed": first_update.record() if first_update is not None else None,
        "first_eurusd_update_at_or_after_open": reopening_update.record() if reopening_update is not None else None,
        "observed_updates_before_scheduled_open": closure_updates,
        "observed_completion_order": _observation_order(completed, opening, window.start),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trace", help="invented weekend trace JSON")
    parser.add_argument("output", help="new JSON report path")
    args = parser.parse_args()
    trace, input_sha256 = data.read_json(args.trace)
    data.write_new(args.output, {**audit(trace), "input_sha256": input_sha256})


if __name__ == "__main__":
    main()
