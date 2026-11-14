"""Independent SQLite aggregation check; does not validate the underlying feed."""
import argparse
import csv
from datetime import datetime
import gzip
import hashlib
import json
import math
from pathlib import Path
import sqlite3


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check(capture, rebuilt):
    source = json.loads((capture/"capture.json").read_text())
    provenance = json.loads((rebuilt/"provenance.json").read_text())
    if (source["data_sha256"] != digest(capture/"ticks.csv.gz")
            or provenance["source_capture_sha256"] != digest(capture/"capture.json")
            or provenance["data_sha256"] != digest(rebuilt/"diagnostic-bars.csv")):
        raise ValueError("Input integrity mismatch")
    connection = sqlite3.connect(":memory:")
    try:
        connection.execute("CREATE TABLE ticks (sequence INTEGER PRIMARY KEY, ms INTEGER, bid REAL, ask REAL)")
        with gzip.open(capture/"ticks.csv.gz", "rt", newline="") as stream:
            connection.executemany("INSERT INTO ticks VALUES (?,?,?,?)",
                                   ((int(r["sequence"]), int(r["time_msc"]), float(r["bid"]), float(r["ask"]))
                                    for r in csv.DictReader(stream)))
        # sequence breaks ties when multiple events share a millisecond.
        rows = connection.execute("""
            WITH ranked AS (
              SELECT *, ms / 3600000 AS hour,
                ROW_NUMBER() OVER (PARTITION BY ms / 3600000 ORDER BY sequence) AS first,
                ROW_NUMBER() OVER (PARTITION BY ms / 3600000 ORDER BY sequence DESC) AS last,
                ms - LAG(ms) OVER (PARTITION BY ms / 3600000 ORDER BY sequence) AS gap
              FROM ticks)
            SELECT hour, COUNT(*),
              MAX(CASE WHEN first=1 THEN bid END), MAX(bid), MIN(bid), MAX(CASE WHEN last=1 THEN bid END),
              MAX(CASE WHEN first=1 THEN ask END), MAX(ask), MIN(ask), MAX(CASE WHEN last=1 THEN ask END),
              MAX(CASE WHEN first=1 THEN (ask-bid)/0.0001 END),
              MIN(ms)-hour*3600000, (hour+1)*3600000-MAX(ms), COALESCE(MAX(gap),0)
            FROM ranked GROUP BY hour ORDER BY hour
        """).fetchall()
    finally:
        connection.close()
    with (rebuilt/"diagnostic-bars.csv").open(newline="") as stream:
        reader = csv.DictReader(stream)
        fields = reader.fieldnames
        actual = list(reader)
    expected_fields = ["source_hour_label", "ticks", "bid_open", "bid_high", "bid_low", "bid_close",
                       "ask_open", "ask_high", "ask_low", "ask_close", "first_quote_spread_pips",
                       "first_tick_delay_ms", "last_tick_to_end_ms", "largest_internal_gap_ms"]
    if fields != expected_fields or len(actual) != len(rows) or provenance["rows"] != len(rows):
        raise ValueError("Reconstructed coverage/header mismatch")
    for bar, expected in zip(actual, rows):
        if datetime.fromisoformat(bar["source_hour_label"]).timestamp() != expected[0]*3600:
            raise ValueError("Reconstructed hour mismatch")
        for field, value in zip(fields[1:], expected[1:]):
            if not math.isclose(float(bar[field]), value, rel_tol=0, abs_tol=1e-10):
                raise ValueError(f"Independent aggregation mismatch: {field}")
    return {"status": "independent_aggregation_matches", "rows": len(rows),
            "ticks": sum(row[1] for row in rows), "independent_market_feed": False,
            "provenance_sha256": digest(rebuilt/"provenance.json"),
            "checker_code_sha256": digest(Path(__file__)),
            "limitation": "SQL verifies exported aggregates only, not feed accuracy, completeness or timezone"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", type=Path, required=True)
    parser.add_argument("--reconstruction", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = check(args.capture, args.reconstruction)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(f"SQL check matched {report['rows']} candles from {report['ticks']} ticks")


if __name__ == "__main__":
    main()
