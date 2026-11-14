"""Predeclared winter/summer offset diagnostic against a second data provider."""
import argparse
import csv
from datetime import datetime, timezone
import math
import statistics
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"src"))
from forex_demo_lab.cli import code_digest, write_json
from forex_demo_lab.histdata import archive_ticks, hourly
from forex_demo_lab.reconstruction import checked_capture
from forex_demo_lab.tick_audit import sha256


def compare(capture, independent, expected):
    metadata, ticks, start, end = checked_capture(capture)
    mt5 = list(hourly(ticks))
    other = {b["hour"]: b for b in hourly(archive_ticks(independent), start-4*3600000, end)}
    report = assess(mt5, other, start, end, expected)
    report.update(mt5_capture_sha256=sha256(capture/"capture.json"),
                  histdata_archive_sha256=sha256(independent/"original.zip"), comparison_kind="tick_reconstructed_bid_candles")
    return report


def compare_bars(raw, independent, expected, start, end):
    if (start.tzinfo is None or end.tzinfo is None or not start < end
            or any(t.minute or t.second or t.microsecond for t in (start,end))
            or (end-start).total_seconds() > 48*3600):
        raise ValueError("Use an hourly offset-aware window of at most 48 hours")
    lower, upper = int(start.timestamp()*1000), int(end.timestamp()*1000)
    bars = []
    with raw.open(newline="",encoding="utf-8-sig") as stream:
        for row in csv.DictReader(stream):
            time = datetime.fromisoformat(row["time"])
            if time.tzinfo is None:
                raise ValueError("Reference source labels need explicit offsets")
            ms = int(time.timestamp()*1000)
            if not lower <= ms < upper:
                continue
            prices = [float(row[p]) for p in ("open","high","low","close")]
            if (ms%3600000 or not all(math.isfinite(p) and p>0 for p in prices)
                    or not prices[2] <= min(prices[0],prices[3]) <= max(prices[0],prices[3]) <= prices[1]
                    or bars and ms//3600000 <= bars[-1]["hour"]):
                raise ValueError("Invalid or unordered reference bars")
            bars.append(dict(hour=ms//3600000, **dict(zip(("bid_open","bid_high","bid_low","bid_close"),prices))))
    other = {b["hour"]:b for b in hourly(archive_ticks(independent),lower-4*3600000,upper)}
    report = assess(bars,other,lower,upper,expected)
    report.update(mt5_raw_bars_sha256=sha256(raw),histdata_archive_sha256=sha256(independent/"original.zip"),
                  comparison_kind="preserved_h1_bid_candles_not_fresh_ticks")
    return report


def assess(mt5, other, start, end, expected):
    candidates = []
    for offset in range(5):
        differences = []
        for bar in mt5:
            found = other.get(bar["hour"]-offset)
            row = {"mt5_source_hour": datetime.fromtimestamp(bar["hour"]*3600, timezone.utc).isoformat(),
                   "comparison_hour_present": found is not None}
            if found:
                row["bid_difference_pips"] = {p:(bar[f"bid_{p}"]-found[f"bid_{p}"])/.0001
                                               for p in ("open","high","low","close")}
            differences.append(row)
        closes = [abs(r["bid_difference_pips"]["close"]) for r in differences if r["comparison_hour_present"]]
        candidates.append({"mt5_label_ahead_of_utc_hours": offset, "hours": differences,
                           "matched_hours": len(closes), "mean_absolute_close_pips": statistics.mean(closes) if closes else None,
                           "median_absolute_close_pips": statistics.median(closes) if closes else None,
                           "maximum_absolute_close_pips": max(closes) if closes else None})
    chosen = candidates[expected]
    alternatives = [c["mean_absolute_close_pips"] for c in candidates if c is not chosen]
    margin = (min(alternatives)-chosen["mean_absolute_close_pips"]
              if all(v is not None for v in alternatives) and chosen["mean_absolute_close_pips"] is not None else None)
    passed = (len(mt5) == (end-start)//3600000 and chosen["matched_hours"] == len(mt5)
              and chosen["median_absolute_close_pips"] <= 1 and chosen["maximum_absolute_close_pips"] <= 3
              and margin is not None and margin >= 2)
    return {"status": "sample_corroborated" if passed else "sample_not_corroborated", "expected_offset": expected,
            "alternative_mean_error_margin_pips": margin, "candidates": candidates,
            "code_sha256": code_digest(), "full_year_timezone_verified": False,
            "historical_broker_costs_verified": False, "upstream_feed_independence_verified": False,
            "limitations": ["Different providers may share upstream quotes; agreement is corroboration only",
                            "Thresholds apply only to sampled bid closing prices and selected offset candidates",
                            "No completeness, historical trading conditions or executable liquidity guarantee"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--capture", type=Path)
    source.add_argument("--raw-bars", type=Path)
    parser.add_argument("--start")
    parser.add_argument("--end")
    parser.add_argument("--independent", type=Path, required=True)
    parser.add_argument("--expected-offset", type=int, choices=range(5), required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Output exists")
    if args.raw_bars:
        if not args.start or not args.end:
            parser.error("Raw-bar comparison requires start and end")
        report = compare_bars(args.raw_bars,args.independent,args.expected_offset,
                              datetime.fromisoformat(args.start),datetime.fromisoformat(args.end))
    else:
        report = compare(args.capture, args.independent, args.expected_offset)
    write_json(args.output, report)
    print(report["status"])
    for row in report["candidates"]:
        print(row["mt5_label_ahead_of_utc_hours"], row["matched_hours"], row["mean_absolute_close_pips"])


if __name__ == "__main__":
    main()
