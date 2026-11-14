"""Read H1/M1 prices around a known gap, preserving data without patching history."""
import argparse
from datetime import datetime, timedelta, timezone
import json
import math
import os
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"src"))
from forex_demo_lab.collection import require_demo
from forex_demo_lab.model import timestamp


def validate_response(rows, start, end, period_seconds):
    """API success is insufficient: preserve and flag wrong/stale responses."""
    problems = []
    previous = None
    for index, row in enumerate(rows):
        value = timestamp(row["time_label"])
        if not start <= value < end:
            problems.append({"row": index, "problem": "outside_requested_range"})
        if value.timestamp() % period_seconds:
            problems.append({"row": index, "problem": "off_timeframe_grid"})
        if previous is not None and value <= previous:
            problems.append({"row": index, "problem": "duplicate_or_unordered"})
        previous = value
        prices = [row[k] for k in ("open", "high", "low", "close")]
        if (not all(math.isfinite(p) and p > 0 for p in prices)
                or not row["low"] <= min(row["open"], row["close"]) <= max(row["open"], row["close"]) <= row["high"]
                or row["spread_points"] < 0 or row["tick_volume"] < 0):
            problems.append({"row": index, "problem": "invalid_price_or_counts"})
    return problems


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--terminal", type=Path, required=True)
    parser.add_argument("--start", required=True)
    parser.add_argument("--end", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    start, end = timestamp(args.start), timestamp(args.end)
    if os.name != "nt" or not start < end <= datetime.now(timezone.utc) or end-start > timedelta(hours=48):
        parser.exit(2, "Use Windows and a past source-label range no longer than 48 hours.\n")
    if args.output.exists():
        parser.exit(2, "Output already exists.\n")
    status = subprocess.run(["powershell.exe", "-NoProfile", "-Command",
                             "ConvertTo-Json -Compress -InputObject @(Get-Process terminal64 -ErrorAction SilentlyContinue | ForEach-Object { $_.Path })"],
                            capture_output=True, text=True, check=True, timeout=15)
    if os.path.normcase(str(args.terminal.resolve())) not in [os.path.normcase(p) for p in json.loads(status.stdout) if p]:
        parser.exit(2, "The specified terminal must already be running.\n")
    import MetaTrader5 as mt5
    try:
        if not mt5.initialize(str(args.terminal), timeout=15000):
            raise ValueError("Read-only connection failed")
        result = {"kind": "same_feed_history_gap_probe", "symbol": "EURUSD",
                  "captured_utc": datetime.now(timezone.utc).isoformat(),
                  "source_label_start": start.isoformat(), "source_label_end_exclusive": end.isoformat(),
                  "timestamp_convention": "Raw API source labels; UTC mapping unverified", "requests": []}
        # H1 before and after M1 helps expose a cache refresh without claiming its cause.
        for name, period, seconds in (("H1_before_M1", mt5.TIMEFRAME_H1, 3600), ("M1", mt5.TIMEFRAME_M1, 60), ("H1_after_M1", mt5.TIMEFRAME_H1, 3600)):
            require_demo(mt5)
            rates = mt5.copy_rates_range("EURUSD", period, start, end-timedelta(seconds=1))
            error = int(mt5.last_error()[0])
            require_demo(mt5)
            rows = [] if rates is None else [
                {"time_label": datetime.fromtimestamp(int(r["time"]), timezone.utc).isoformat(),
                 **{k: float(r[k]) for k in ("open", "high", "low", "close")},
                 "spread_points": int(r["spread"]), "tick_volume": int(r["tick_volume"])} for r in rates]
            problems = validate_response(rows, start, end, seconds)
            state = "api_error" if rates is None or error != 1 else "invalid_response" if problems else "empty" if not rows else "returned"
            result["requests"].append({"timeframe": name, "rows": rows, "api_error_code": error,
                                       "status": state, "validation_problems": problems})
            print(f"{name}: {len(rows)} rows; API code {error}; {state}", flush=True)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x", encoding="utf-8") as stream:
            json.dump(result, stream, indent=2, allow_nan=False)
    finally:
        mt5.shutdown()


if __name__ == "__main__":
    main()
