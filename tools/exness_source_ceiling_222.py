"""Bound the strict 2022 first-opening route using retained Exness diagnostics."""

import argparse

from forex_demo_lab.exness_diagnostics_b import timestamp_ms
from forex_demo_lab.trendline import data, entry_timing, historical_calendar, signal_count
from tools.exness_2022_calendar_220 import END, START, calendar_record
from tools.exness_2022_timing import ordinary_weeks
from tools.exness_weekend_opening_214 import SAMPLES, weekend_bounds

# The four retained metadata files already bound by the Sprint 214 receipt.
EVIDENCE_SHA256 = (
    ("10dbe8c1efeb5576c02486520eddc7d5a0fb8e3881023c983dffd71a0ca3ee0f",
     "ffc7a9156352e4bebb27fa8f56d718361651d87ff82d1b63c368956f68ecf075"),
    ("d38b81729422832a8fadf21e2a6f951da4871daa9bcbe2b59d7e63529b06f899",
     "c8a78d666c377d7ca058b7a6493fbe10c57e97e1714d01021c2590ab2cd519d9"),
)


def sampled_openings(sample, coverage):
    if coverage.get("observed_receipt_times_available") is not False:
        raise ValueError("retained source-time-only diagnostics required")
    bounds = weekend_bounds(sample, coverage)
    return tuple((timestamp_ms(pair["first_sunday_label"]) - bound["first_sunday_quote_lag_ms"],
                  bound["first_sunday_quote_lag_ms"])
                 for pair, bound in zip(sample["boundaries"], bounds, strict=True))


def timing_cases(calendar, source_lags):
    h1_starts = tuple(window.start for window in calendar.frame("H1"))
    h4_closes = tuple(window.end for window in calendar.frame("H4"))
    if any(opening not in h1_starts for opening in source_lags):
        raise ValueError("each sampled opening must match a scheduled H1 start")
    result = []
    for delay in (0, 2000):
        timing = entry_timing.compare_schedule(h1_starts, h4_closes, delay=delay)
        early = [row for row in timing if row["status"] == "EARLIEST_PUBLICATION_BEFORE_OPEN"]
        excluded = [
            {**row, "first_source_quote_lag_ms": source_lags[row["first_scheduled_open"]]}
            for row in early if source_lags.get(row["first_scheduled_open"], 0) > 0
        ]
        ceiling = len(early) - len(excluded)
        result.append({
            "finalization_delay_ms": delay,
            **entry_timing.summarize(timing),
            "sampled_late_openings_excluded": excluded,
            "remaining_candidate_ceiling_before_strategy_filters": ceiling,
            "minimum_candidates_needed_from_2021_to_reach_two_year_gate": max(
                0, signal_count.MINIMUM_OPPORTUNITIES - ceiling
            ),
        })
    return result


def report():
    source_lags = {}
    evidence = []
    for (source_path, coverage_path), pinned in zip(SAMPLES, EVIDENCE_SHA256, strict=True):
        sample, source_sha = data.read_json(data.ROOT / source_path)
        coverage, coverage_sha = data.read_json(data.ROOT / coverage_path)
        if (source_sha, coverage_sha) != pinned:
            raise ValueError("retained opening diagnostics differ from Sprint 214")
        opens = sampled_openings(sample, coverage)
        if any(start in source_lags for start, _ in opens):
            raise ValueError("opening evidence overlaps between samples")
        source_lags.update(opens)
        evidence.append({
            "month": sample["declared_month"], "archive_sha256": sample["archive_sha256"],
            "source_report_sha256": source_sha, "coverage_report_sha256": coverage_sha,
            "sampled_weekend_openings": len(opens),
        })

    record = calendar_record(ordinary_weeks())
    calendar = historical_calendar.Calendar.from_record(
        record, sha256=data.digest(record), start=START, development_start=START, end=END, delay=2000,
    )
    return {
        "kind": "exness_2022_strict_opening_ceiling", "calendar_sha256": calendar.sha256,
        "same_time_open_order": "unresolved", "evidence": evidence,
        "minimum_opportunities_per_strategy": signal_count.MINIMUM_OPPORTUNITIES,
        "timing_cases": timing_cases(calendar, source_lags),
        "observed_receipt_times_available": False, "schedule_qualified": False,
        "market_source_admitted": False, "market_data_read": False, "actual_counts": None,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", help="new JSON diagnostic report path")
    data.write_new(parser.parse_args().output, report())


if __name__ == "__main__":
    main()
