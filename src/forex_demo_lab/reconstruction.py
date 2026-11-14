"""Diagnostic bars from captured ticks, deliberately not simulator-ready data."""
import csv
from datetime import datetime, timedelta, timezone
import json
import math
from pathlib import Path

from .tick_audit import load_ticks, sha256, valid_quote
from .cli import code_digest

HOUR = 3_600_000
PRICES = ("open", "high", "low", "close")
FIELDS = ["source_hour_label", "ticks", *[f"{side}_{p}" for side in ("bid", "ask") for p in PRICES],
          "first_quote_spread_pips", "first_tick_delay_ms", "last_tick_to_end_ms", "largest_internal_gap_ms"]


def bound(value):
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None or parsed.utcoffset() != timedelta(0) or any(
            (parsed.minute, parsed.second, parsed.microsecond)):
        raise ValueError("Reconstruction requires explicit zero-offset hourly source labels")
    return int(parsed.timestamp()*1000)


def checked_capture(folder):
    metadata, ticks = load_ticks(folder)
    start, end = bound(metadata["source_label_start"]), bound(metadata["source_label_end_exclusive"])
    if not 0 < end-start <= 48*HOUR or metadata.get("requests_without_api_errors") is not True:
        raise ValueError("Capture must have bounded coverage and no API errors")
    windows = metadata.get("windows", [])
    cursor, offset = start, 0
    for window in windows:
        lower, upper = bound(window["start_label"]), bound(window["end_label_exclusive"])
        if lower != cursor or not lower < upper <= min(lower+6*HOUR, end):
            raise ValueError("Capture request windows must cover the interval without overlap or gaps")
        before = offset
        while offset < len(ticks) and ticks[offset]["time_msc"] < upper:
            offset += 1
        count = offset-before
        if (window["api_error_code"] != 1 or window["ticks"] != count
                or window["status"] != ("returned" if count else "empty")):
            raise ValueError("Capture window status/count disagrees with ticks")
        cursor = upper
    if cursor != end or offset != len(ticks):
        raise ValueError("Capture request coverage is incomplete")
    if not all(valid_quote(t) and all(math.isfinite(t[k]) for k in ("bid", "ask")) for t in ticks):
        raise ValueError("Invalid quotes cannot be silently dropped during reconstruction")
    return metadata, ticks, start, end


def ohlc(events, side):
    prices = [t[side] for t in events]
    return dict(zip(PRICES, (prices[0], max(prices), min(prices), prices[-1])))


def reconstruct(folder: Path, output: Path, reference: Path | None = None, repeat: Path | None = None):
    if output.exists():
        raise FileExistsError("Reconstruction destination exists")
    metadata, ticks, start, end = checked_capture(folder)
    repeated = None
    if repeat is not None:
        other, values, lower, upper = checked_capture(repeat)
        if (lower, upper) != (start, end):
            raise ValueError("Repeat comparison requires identical requested coverage")
        repeated = {"capture_sha256": sha256(repeat/"capture.json"),
                    "ticks_sha256": other["data_sha256"], "rows": len(values),
                    "identical_ordered_events": ticks == values,
                    "independent_feed": False}
    references = {}
    if reference is not None:
        with reference.open(encoding="utf-8-sig", newline="") as stream:
            for row in csv.DictReader(stream):
                hour = bound(row["time"])
                if not start <= hour < end:
                    continue
                prices = {k: float(row[k]) for k in PRICES}
                if (hour in references or not all(math.isfinite(v) and v > 0 for v in prices.values())
                        or not prices["low"] <= min(prices["open"], prices["close"])
                        <= max(prices["open"], prices["close"]) <= prices["high"]):
                    raise ValueError("Invalid or duplicate reference candle")
                references[hour] = prices
    groups = {}
    for tick in ticks:
        groups.setdefault(tick["time_msc"]//HOUR*HOUR, []).append(tick)
    bars, coverage = [], []
    for hour in range(start, end, HOUR):
        label = datetime.fromtimestamp(hour/1000, timezone.utc).isoformat()
        events = groups.get(hour, [])
        item = {"source_hour_label": label, "ticks": len(events),
                "status": "observed_ticks_completeness_unverified" if events else "no_ticks_unclassified"}
        if events:
            bid, ask = ohlc(events, "bid"), ohlc(events, "ask")
            bars.append({"source_hour_label": label, "ticks": len(events),
                         **{f"bid_{k}": v for k,v in bid.items()}, **{f"ask_{k}": v for k,v in ask.items()},
                         "first_quote_spread_pips": (events[0]["ask"]-events[0]["bid"])/.0001,
                         "first_tick_delay_ms": events[0]["time_msc"]-hour,
                         "last_tick_to_end_ms": hour+HOUR-events[-1]["time_msc"],
                         "largest_internal_gap_ms": max((b["time_msc"]-a["time_msc"]
                                                         for a,b in zip(events,events[1:])), default=0)})
            if reference is not None:
                old = references.get(hour)
                if old is None:
                    item["reference_status"] = "missing_reference_candle"
                else:
                    differences = {k: (bid[k]-old[k])/.0001 for k in PRICES}
                    matches = all(abs(v) < .05 for v in differences.values())
                    item.update(reference_status="match" if matches else "mismatch",
                                bid_difference_pips=differences)
                    if not matches:
                        # Search every chronological prefix, not just a chosen favorable endpoint.
                        high = low = events[0]["bid"]
                        found = []
                        for i, tick in enumerate(events):
                            high, low = max(high,tick["bid"]), min(low,tick["bid"])
                            prefix = (events[0]["bid"], high, low, tick["bid"])
                            if all(abs(p-old[k]) < .000005 for p,k in zip(prefix,PRICES)):
                                found.append({"ticks": i+1, "last_tick_time_msc": tick["time_msc"]})
                        item["matching_prefixes"] = {"count": len(found), "first": found[0] if found else None,
                                                     "last": found[-1] if found else None,
                                                     "proves_truncation": False}
        elif reference is not None:
            item["reference_status"] = "reference_without_ticks" if hour in references else "neither_has_data"
        coverage.append(item)
    manifest = {"schema_version": 1, "kind": "diagnostic_tick_reconstruction", "symbol": "EURUSD",
                "status": "not_validated_for_backtesting", "historical_timezone_verified": False,
                "complete_market_history_verified": False, "independent_feed_validation": False,
                "timestamp_convention": "Unconverted source labels; +00:00 is serialization, not verified UTC",
                "source_capture_sha256": sha256(folder/"capture.json"), "source_ticks_sha256": metadata["data_sha256"],
                "reference_sha256": sha256(reference) if reference else None,
                "source_label_start": metadata["source_label_start"],
                "source_label_end_exclusive": metadata["source_label_end_exclusive"],
                "rows": len(bars), "ticks": len(ticks), "coverage": coverage, "repeat_comparison": repeated,
                "limitations": ["No candles fabricated for empty hours; closures versus missing data unresolved",
                                "OHLC uses all valid quote snapshots in captured event order",
                                "First-quote spread is observed after the hour; not a guaranteed executable entry",
                                "Same-feed repeatability and prefix matches do not establish historical truth",
                                "No costs, signals, positions, performance calculation or broker execution"]}
    output.mkdir(parents=True, exist_ok=False)
    with (output/"diagnostic-bars.csv").open("x", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(bars)
    manifest["data_sha256"] = sha256(output/"diagnostic-bars.csv")
    manifest["reconstruction_code_sha256"] = sha256(Path(__file__))
    manifest["package_code_sha256"] = code_digest()
    with (output/"provenance.json").open("x", encoding="utf-8") as stream:
        json.dump(manifest, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
    return manifest
