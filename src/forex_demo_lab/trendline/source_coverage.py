"""Audit invented quote timestamps against declared warmup and development calendars."""

import argparse

from ..elliott_sessions_146 import Calendar, FRAMES
from . import data, study


VERSION = "TRL_SOURCE_COVERAGE_198_V1"
DESCRIPTOR_KIND = "invented_trendline_coverage_scope"
INPUT_KIND = "invented_trendline_source_timestamps"


def _calendars(descriptor):
    data.fields(descriptor, ("schema", "kind", "symbol", "warmup_calendar",
                             "development_calendar", "input_sha256"))
    if (descriptor["schema"], descriptor["kind"], descriptor["symbol"]) != (VERSION, DESCRIPTOR_KIND, "EURUSD"):
        raise ValueError("invented EURUSD coverage scope required")
    data.sha(descriptor["input_sha256"])
    warmup = Calendar.from_record(descriptor["warmup_calendar"])
    development = Calendar.from_record(descriptor["development_calendar"])
    if warmup.end != development.start:
        raise ValueError("warmup must end at the start of development")
    return warmup, development


def _first_quotes(warmup, development, timestamps):
    windows = warmup.frame("H1") + development.frame("H1")
    first = {}
    counters = {name: {"timestamps": 0, "tied_timestamp_transitions": 0, "closure_timestamps": 0}
                for name in ("warmup", "development")}
    index = 0
    previous = None
    for timestamp in timestamps:
        data.integer(timestamp)
        if not warmup.start <= timestamp < development.end:
            raise ValueError("timestamp outside the declared half-open scope")
        if previous is not None and timestamp < previous:
            raise ValueError("timestamps must preserve source order")
        part = counters["warmup" if timestamp < development.start else "development"]
        part["timestamps"] += 1
        part["tied_timestamp_transitions"] += timestamp == previous
        previous = timestamp

        while index < len(windows) and timestamp >= windows[index].end:
            index += 1
        if index < len(windows) and windows[index].start <= timestamp:
            first.setdefault(windows[index].start, timestamp)
        else:
            part["closure_timestamps"] += 1
    return first, counters


def _frame_coverage(calendar, first):
    report = {}
    for frame in FRAMES:
        windows = calendar.frame(frame)
        missing = [window.start for window in windows if any(child not in first for child in window.children)]
        report[frame] = {"scheduled": len(windows), "with_all_children_observed": len(windows) - len(missing),
                         "missing_window_starts": missing}
    return report


def _partition(calendar, first, counts):
    exact, late, missing = 0, [], []
    for window in calendar.frame("H1"):
        timestamp = first.get(window.start)
        if timestamp is None:
            missing.append(window.start)
        elif timestamp == window.start:
            exact += 1
        else:
            late.append({"start": window.start, "lag_ms": timestamp - window.start})
    return {"scope": {"start": calendar.start, "end": calendar.end}, "calendar_sha256": calendar.sha256,
            "finalization_delay_ms": calendar.delay, **counts, "coverage": _frame_coverage(calendar, first),
            "h1_opening": {"exact_source_timestamp": exact, "late_first_quote": len(late), "no_quote": len(missing),
                           "late_first_quotes": late, "no_quote_starts": missing}}


def _warmup_at_boundary(calendar, coverage):
    limits = study.policy()["minimum_complete_prior_bars"]
    readiness = {}
    for frame in FRAMES:
        windows = calendar.frame(frame)
        due = [window for window in windows if window.end + calendar.delay <= calendar.end]
        missing = set(coverage[frame]["missing_window_starts"])
        trailing = 0
        for window in reversed(due):
            if window.start in missing:
                break
            trailing += 1
        observed_due = sum(window.start not in missing for window in due)
        readiness[frame] = {
            "minimum": limits[frame], "scheduled_due": len(due),
            "complete_due_by_timestamp_coverage": observed_due,
            "trailing_complete_due_by_timestamp_coverage": trailing,
            "pending_starts": [window.start for window in windows[len(due):]],
            "minimum_complete_due_met": observed_due >= limits[frame],
            "minimum_trailing_complete_due_met": trailing >= limits[frame],
        }
    return readiness


def audit_files(descriptor_path, timestamp_path):
    """Read only explicitly scoped invented timestamps and publish coverage counts."""
    descriptor, descriptor_sha = data.read_json(descriptor_path)
    warmup, development = _calendars(descriptor)
    source, source_sha = data.read_json(timestamp_path)
    if source_sha != descriptor["input_sha256"]:
        raise ValueError("input bytes do not match the coverage declaration")
    data.fields(source, ("kind", "timestamps"))
    if source["kind"] != INPUT_KIND or type(source["timestamps"]) is not list:
        raise ValueError("invented source timestamp array required")
    first, counts = _first_quotes(warmup, development, source["timestamps"])
    warmup_report = _partition(warmup, first, counts["warmup"])
    return {"schema": VERSION, "kind": "invented_trendline_timestamp_coverage", "symbol": "EURUSD",
            "descriptor_file_sha256": descriptor_sha, "timestamp_file_sha256": source_sha,
            "market_source_admitted": False, "price_rows_read": False, "signal_counts_computed": False,
            "warmup": warmup_report,
            "warmup_at_development_start": _warmup_at_boundary(warmup, warmup_report["coverage"]),
            "development": _partition(development, first, counts["development"])}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("descriptor")
    parser.add_argument("timestamps")
    parser.add_argument("output")
    args = parser.parse_args()
    data.write_new(args.output, audit_files(args.descriptor, args.timestamps))


if __name__ == "__main__":
    main()
