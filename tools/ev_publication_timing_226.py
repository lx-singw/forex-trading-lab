"""Compare EV's UTC bucket end and scenario session end using retained metadata."""

import argparse
from collections import Counter
from datetime import datetime

from forex_demo_lab.elliott_sessions_146 import HOUR
from forex_demo_lab.trendline import data, entry_timing
from tools.ev_calendar_224 import END, START, ordinary_open
from tools.ev_parent_resample_225 import buckets

EVIDENCE = "reports/trendline-source-224/ev-2024-calendar.json"
EVIDENCE_SHA256 = "d2ec6118a38533979f1907b001895e97c43309fa03e68cd85cffb6d14b43985f"
BEFORE = "EARLIEST_PUBLICATION_BEFORE_OPEN"
TIED = "TIED_AT_EARLIEST_PUBLICATION"


def missing_hours(coverage):
    hours = set()
    for span in coverage["h1_missing"]:
        left, right = (int(datetime.fromisoformat(span[key]).timestamp()) * 1000
                       for key in ("start", "end_exclusive"))
        hours.update(range(left, right, HOUR))
    return hours


def timing_case(starts, closes, missing_parent, missing_h1, *, delay, wait_for_first_open):
    rows = entry_timing.compare_schedule(starts, closes, delay=delay, wait_for_first_open=wait_for_first_open)
    eligible = Counter()
    blocked = Counter()
    for row in rows:
        status = row["status"]
        if status not in (BEFORE, TIED):
            continue
        reasons = []
        if row["h4_end"] in missing_parent:
            reasons.append("missing_h4_child")
        if row["first_scheduled_open"] in missing_h1:
            reasons.append("missing_first_h1")
        if reasons:
            blocked[" and ".join(reasons)] += 1
        else:
            eligible[status] += 1
    return {
        "finalization_delay_ms": delay,
        "wait_for_first_open": wait_for_first_open,
        **entry_timing.summarize(rows),
        "timely_or_tied_slots_blocked_by_coverage": dict(sorted(blocked.items())),
        "coverage_adjusted_ceiling_without_same_time_order": eligible[BEFORE],
        "coverage_adjusted_ceiling_with_decision_before_tied_open": eligible[BEFORE] + eligible[TIED],
    }


def compare(starts, missing_h1):
    groups = buckets(starts, 4 * HOUR)
    incomplete_buckets = {start for start, children in groups.items() if missing_h1.intersection(children)}
    end_models = {
        "utc_bucket_end": {start: start + 4 * HOUR for start in groups},
        "ordinary_session_end": {start: children[-1] + HOUR for start, children in groups.items()},
    }
    schedules = {}
    slot_by_model = {}
    for model, ends in end_models.items():
        closes = tuple(ends.values())
        missing_parent = {ends[start] for start in incomplete_buckets}
        rows = entry_timing.compare_schedule(starts, closes, delay=0)
        slot_by_model[model] = tuple(row["first_scheduled_open"] for row in rows)
        lead_hours = Counter(
            (row["first_scheduled_open"] - row["h4_end"]) // HOUR for row in rows if row["status"] == BEFORE
        )
        schedules[model] = {
            "h4_close_to_first_open_hours_when_strictly_early": dict(sorted(lead_hours.items())),
            "timing_cases": [
                timing_case(starts, closes, missing_parent, missing_h1, delay=delay, wait_for_first_open=wait)
                for wait in (False, True)
                for delay in (0, 2000)
            ],
        }

    utc_ends, session_ends = end_models.values()
    advanced = Counter(
        (utc_ends[start] - end) // HOUR for start, end in session_ends.items() if end < utc_ends[start]
    )
    return {
        "scheduled_h1": len(starts),
        "scheduled_h4": len(groups),
        "h4_buckets_missing_one_or_more_scheduled_children": len(incomplete_buckets),
        "h4_close_advance_hours_when_clipped": dict(sorted(advanced.items())),
        "first_scheduled_open_changed": sum(
            a != b for a, b in zip(*slot_by_model.values(), strict=True)
        ),
        "models": schedules,
    }


def report():
    coverage, digest = data.read_json(data.ROOT / EVIDENCE)
    if digest != EVIDENCE_SHA256:
        raise ValueError("retained timestamp diagnostic differs from Sprint 224")
    starts = tuple(stamp * 1000 for stamp in range(START, END, HOUR // 1000) if ordinary_open(stamp))
    missing = missing_hours(coverage)
    if (len(starts) != coverage["ordinary_h1_slots"] or not missing.issubset(starts)
            or len(starts) - len(missing) != coverage["published_h1_slots"]):
        raise ValueError("ordinary calendar does not reconcile with the retained evidence")
    return {
        "kind": "ev_2024_h4_publication_timing_scenario",
        "timestamp_report_sha256": digest,
        **compare(starts, missing),
        "same_time_order": "unresolved",
        "historical_receipt_verified": False,
        "schedule_qualified": False,
        "market_source_admitted": False,
        "market_data_read": False,
        "actual_counts": None,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", help="new JSON diagnostic report path")
    data.write_new(parser.parse_args().output, report())


if __name__ == "__main__":
    main()
