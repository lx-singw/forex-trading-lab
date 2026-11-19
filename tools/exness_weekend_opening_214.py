"""Bound Sunday opening quote age using retained Exness diagnostic summaries."""

import argparse

from forex_demo_lab.exness_diagnostics_b import timestamp_ms
from forex_demo_lab.trendline import data, quotes
from tools.exness_2022_timing import ordinary_weeks

SAMPLES = (
    ("reports/trendline-source-203/sample-audit.json", "reports/trendline-source-212/opening-diagnostic.json"),
    ("reports/trendline-source-204/sample-audit.json", "reports/trendline-source-213/h4-opening-diagnostic.json"),
)


def weekend_bounds(sample, coverage):
    """Use the last Friday label if the matched archive has no closure rows."""
    data.sha(sample["archive_sha256"])
    if (sample["status"] != "diagnostic_complete" or coverage["status"] != "complete"
            or sample["archive_sha256"] != coverage["archive_sha256"]
            or sample["valid_rows"] != coverage["rows"] or coverage["outside_modeled_h1"] != 0
            or len(sample["boundaries"]) != coverage["weekends_checked"]):
        raise ValueError("matching source and zero-closure-row diagnostics required")

    weeks = ordinary_weeks()
    schedule = {(close.date().isoformat(), reopen.date().isoformat()):
                (int(close.timestamp()) * 1000, int(reopen.timestamp()) * 1000)
                for (_, close, _), (reopen, _, _) in zip(weeks, weeks[1:])}
    rows = []
    seen = set()
    for pair in sample["boundaries"]:
        friday, sunday = pair["last_friday_label"], pair["first_sunday_label"]
        key = (friday[:10], sunday[:10])
        if key in seen or key not in schedule:
            raise ValueError("unique adjacent modeled Friday and Sunday dates required")
        seen.add(key)
        close, reopen = schedule[key]
        last, first = timestamp_ms(friday), timestamp_ms(sunday)
        if not last < close < reopen <= first:
            raise ValueError("weekend source labels disagree with the modeled boundaries")
        rows.append({"friday_close_lag_ms": close - last,
                     "minimum_previous_quote_age_at_open_ms": reopen - last,
                     "first_sunday_quote_lag_ms": first - reopen})
    return rows


def summarize(rows):
    ages = [row["minimum_previous_quote_age_at_open_ms"] for row in rows]
    lags = [row["first_sunday_quote_lag_ms"] for row in rows]
    return {
        "weekends": len(rows), "previous_quote_age_floor_min_ms": min(ages),
        "previous_quote_age_floor_max_ms": max(ages),
        "first_sunday_quote_lag_min_ms": min(lags), "first_sunday_quote_lag_max_ms": max(lags),
        "freshness_reference_ms": quotes.MAX_AGE,
        "friday_quote_within_reference_at_close": sum(row["friday_close_lag_ms"] <= quotes.MAX_AGE for row in rows),
        "previous_quote_within_reference_at_sunday_open": sum(age <= quotes.MAX_AGE for age in ages),
        "exact_sunday_source_edges": sum(lag == 0 for lag in lags),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", help="new JSON diagnostic report path")
    args = parser.parse_args()
    evidence = []
    for source_path, coverage_path in SAMPLES:
        source, source_sha = data.read_json(data.ROOT / source_path)
        coverage, coverage_sha = data.read_json(data.ROOT / coverage_path)
        evidence.append({"month": source["declared_month"], "source_report_sha256": source_sha,
                         "coverage_report_sha256": coverage_sha, "weekends": weekend_bounds(source, coverage)})
    rows = [row for sample in evidence for row in sample["weekends"]]
    data.write_new(args.output, {"kind": "exness_weekend_opening_source_bounds", "evidence": evidence,
                                 "totals": summarize(rows), "observed_receipt_times_available": False,
                                 "market_source_admitted": False, "actual_strategy_counts": None})


if __name__ == "__main__":
    main()
