"""Read-only tick capture and data diagnostics; no strategy tuning or execution."""
import csv
from datetime import datetime, timedelta, timezone
import gzip
import hashlib
import io
import json
import math
from pathlib import Path

from .collection import require_demo, clock_observation

TICK_FIELDS = ["sequence", "time_msc", "bid", "ask", "flags"]


def sha256(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024*1024), b""):
            value.update(chunk)
    return value.hexdigest()


def capture_ticks(api, start: datetime, end: datetime, output: Path, progress=None) -> dict:
    """Preserve API source labels and event order, including same-millisecond ticks.

    Read at most 48 hours in six-hour chunks. Request each upper boundary then
    filter to [start,end), avoiding loss of the final fractional second.
    Missing/error windows are evidence, never silently treated as complete data.
    """
    now = datetime.now(timezone.utc)
    if (start.tzinfo is None or end.tzinfo is None or not start < end <= now
            or end-start > timedelta(hours=48)
            or any(t.minute or t.second or t.microsecond for t in (start, end))):
        raise ValueError("Use an hourly, offset-aware past interval of at most 48 hours")
    if output.exists():
        raise FileExistsError("Tick capture destination exists")
    terminal, account = require_demo(api)
    symbol = api.symbol_info("EURUSD")
    if (account.currency != "USD" or symbol is None or not symbol.visible
            or symbol.currency_base != "EUR" or symbol.currency_profit != "USD"):
        raise ValueError("A visible EURUSD contract on a USD demo account is required")
    clock = clock_observation(api)
    output.mkdir(parents=True, exist_ok=False)
    partial = output/"ticks.csv.gz.partial"
    total, previous_msc = 0, None
    windows = []
    cursor = start
    with partial.open("xb") as binary:
        with gzip.GzipFile(filename="", mode="wb", fileobj=binary, mtime=0) as zipped:
            with io.TextIOWrapper(zipped, encoding="utf-8", newline="") as text:
                writer = csv.DictWriter(text, fieldnames=TICK_FIELDS)
                writer.writeheader()
                while cursor < end:
                    stop = min(cursor+timedelta(hours=6), end)
                    require_demo(api)
                    ticks = api.copy_ticks_range("EURUSD", cursor, stop, api.COPY_TICKS_ALL)
                    error = int(api.last_error()[0])  # Never log the API's free-text error.
                    require_demo(api)
                    count, excluded = 0, 0
                    lower, upper = int(cursor.timestamp()*1000), int(stop.timestamp()*1000)
                    if ticks is not None:
                        for tick in ticks:
                            msc, seconds = int(tick["time_msc"]), int(tick["time"])
                            bid, ask, flags = float(tick["bid"]), float(tick["ask"]), int(tick["flags"])
                            if msc//1000 != seconds or not all(math.isfinite(v) for v in (bid, ask)) or flags < 0:
                                raise ValueError("Invalid tick timestamp, numeric quote or flags")
                            if msc < lower or msc > upper:
                                raise ValueError("Tick returned outside requested window")
                            if msc == upper:
                                excluded += 1
                                continue
                            if previous_msc is not None and msc < previous_msc:
                                raise ValueError("Out-of-order tick history")
                            writer.writerow(dict(sequence=total, time_msc=msc, bid=bid, ask=ask, flags=flags))
                            previous_msc = msc
                            total += 1
                            count += 1
                    state = "api_error" if ticks is None or error != 1 else "empty" if count == 0 else "returned"
                    windows.append({"start_label": cursor.isoformat(), "end_label_exclusive": stop.isoformat(),
                                    "ticks": count, "status": state, "api_error_code": error,
                                    "excluded_upper_boundary_ticks": excluded})
                    if progress:
                        progress(f"Tick window {len(windows)}: {state}, {count} records")
                    cursor = stop
    require_demo(api)
    destination = output/"ticks.csv.gz"
    partial.rename(destination)
    metadata = {"schema_version": 1, "kind": "mt5_tick_capture", "symbol": "EURUSD",
                "captured_utc": now.isoformat(), "package_version": str(api.__version__),
                "source_label_start": start.isoformat(), "source_label_end_exclusive": end.isoformat(),
                "timestamp_convention": "Unconverted API numeric source labels; not verified UTC",
                "clock_observation": clock, "ticks": total, "windows": windows,
                "requests_without_api_errors": all(w["status"] != "api_error" for w in windows),
                "complete_market_history_verified": False,
                "account_type": "demo", "terminal_algo_trading": bool(terminal.trade_allowed),
                "data_sha256": sha256(destination)}
    (output/"capture.json").write_text(json.dumps(metadata, indent=2, allow_nan=False)+"\n", encoding="utf-8")
    return metadata


def load_ticks(folder: Path):
    metadata = json.loads((folder/"capture.json").read_text(encoding="utf-8"))
    path = folder/"ticks.csv.gz"
    if (metadata.get("schema_version") != 1 or metadata.get("kind") != "mt5_tick_capture"
            or metadata.get("symbol") != "EURUSD" or metadata.get("data_sha256") != sha256(path)):
        raise ValueError("Tick capture metadata/hash mismatch")
    lower = int(datetime.fromisoformat(metadata["source_label_start"]).timestamp()*1000)
    upper = int(datetime.fromisoformat(metadata["source_label_end_exclusive"]).timestamp()*1000)
    ticks = []
    with gzip.open(path, "rt", encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != TICK_FIELDS:
            raise ValueError("Invalid tick capture header")
        for row in reader:
            tick = {"sequence": int(row["sequence"]), "time_msc": int(row["time_msc"]),
                    "bid": float(row["bid"]), "ask": float(row["ask"]), "flags": int(row["flags"])}
            if (tick["sequence"] != len(ticks) or not lower <= tick["time_msc"] < upper
                    or (ticks and tick["time_msc"] < ticks[-1]["time_msc"])
                    or not all(math.isfinite(tick[k]) for k in ("bid", "ask")) or tick["flags"] < 0):
                raise ValueError("Invalid tick sequence or values")
            ticks.append(tick)
    if len(ticks) != metadata["ticks"]:
        raise ValueError("Tick row count mismatch")
    return metadata, ticks


def valid_quote(tick: dict) -> bool:
    return 0 < tick["bid"] <= tick["ask"]


def summarize(folder: Path, raw_bars: Path) -> dict:
    metadata, ticks = load_ticks(folder)
    # Compare in the same source-label clock; no inferred UTC offset is needed.
    bars = {}
    with raw_bars.open(newline="", encoding="utf-8-sig") as stream:
        for row in csv.DictReader(stream):
            key = int(datetime.fromisoformat(row["time"]).timestamp())//3600
            if key in bars:
                raise ValueError("Duplicate reference bar")
            bars[key] = {k: float(row[k]) for k in ("open", "high", "low", "close")}
    groups, spreads = {}, []
    invalid = 0
    for tick in ticks:
        if not valid_quote(tick):
            invalid += 1
            continue
        spreads.append((tick["ask"]-tick["bid"])/.0001)
        groups.setdefault(tick["time_msc"]//3600000, []).append(tick)
    start = int(datetime.fromisoformat(metadata["source_label_start"]).timestamp())//3600
    end = int(datetime.fromisoformat(metadata["source_label_end_exclusive"]).timestamp())//3600
    hourly = []
    for hour in range(start, end):
        events = groups.get(hour, [])
        reference = bars.get(hour)
        record = {"source_hour_label": datetime.fromtimestamp(hour*3600, timezone.utc).isoformat(),
                  "valid_ticks": len(events), "reference_bar_present": reference is not None}
        if events:
            bids = [e["bid"] for e in events]
            rebuilt = dict(open=bids[0], high=max(bids), low=min(bids), close=bids[-1])
            record["rebuilt_bid_ohlc"] = rebuilt
            record["first_quote_spread_pips"] = (events[0]["ask"]-events[0]["bid"])/.0001
            record["first_tick_delay_seconds"] = events[0]["time_msc"]/1000-hour*3600
            record["last_tick_before_hour_end_seconds"] = (hour+1)*3600-events[-1]["time_msc"]/1000
            if reference:
                differences = {k: (rebuilt[k]-reference[k])/.0001 for k in rebuilt}
                record["bid_ohlc_difference_pips"] = differences
                record["status"] = "ohlc_match" if all(abs(v) < .05 for v in differences.values()) else "ohlc_mismatch"
            else:
                record["status"] = "ticks_without_reference_bar"
        else:
            record["status"] = "reference_bar_without_ticks" if reference else "neither_source_has_data"
        hourly.append(record)
    ordered = sorted(spreads)
    n = len(ordered)
    return {"status": "data_diagnostic_only", "tick_capture_sha256": sha256(folder/"capture.json"),
            "reference_bars_sha256": sha256(raw_bars), "capture": metadata,
            "ticks": len(ticks), "invalid_quotes": invalid,
            "same_millisecond_events": sum(a["time_msc"] == b["time_msc"] for a,b in zip(ticks,ticks[1:])),
            "largest_intertick_gap_seconds": max(((b["time_msc"]-a["time_msc"])/1000
                                                    for a,b in zip(ticks,ticks[1:])), default=None),
            "spread_pips": {"minimum": ordered[0] if n else None,
                            "median": (ordered[(n-1)//2]+ordered[n//2])/2 if n else None,
                            "p95": ordered[math.ceil(.95*n)-1] if n else None,
                            "maximum": ordered[-1] if n else None,
                            "fraction_of_ticks_above_1_5": sum(v > 1.5+1e-9 for v in ordered)/n if n else None},
            "hours": hourly,
            "limitations": ["Tick presence does not prove complete or executable historical liquidity",
                             "Both bars and ticks come from the same feed; matching does not independently validate it",
                             "Spreads are event-weighted, not time-weighted; no commission/swap verification",
                             "No full-strategy performance or real broker fills are inferred"]}


def first_exit(ticks: list[dict], side: int, stop: float, target: float, slippage_pips: float) -> dict | None:
    """Conditional diagnostic for an already-open fixed position, not a backtest.

    Caller supplies only ticks at/after the reference entry. No new position,
    sizing, entry selection, commission or swap calculation is performed here.
    """
    if (side not in (-1, 1) or not all(math.isfinite(v) for v in (stop, target, slippage_pips))
            or min(stop, target) <= 0 or slippage_pips < 0
            or (side == 1 and stop >= target) or (side == -1 and stop <= target)):
        raise ValueError("Invalid reference position")
    previous = None
    for tick in ticks:
        if previous is not None and tick["time_msc"] < previous:
            raise ValueError("Ticks must be chronological")
        previous = tick["time_msc"]
        if not valid_quote(tick) or not all(math.isfinite(tick[k]) for k in ("bid", "ask")):
            raise ValueError("Invalid quote prevents a trustworthy exit diagnostic")
        quote = tick["bid"] if side == 1 else tick["ask"]
        stopped = quote <= stop if side == 1 else quote >= stop
        targeted = quote >= target if side == 1 else quote <= target
        if stopped or targeted:
            return {"sequence": tick["sequence"], "time_msc": tick["time_msc"],
                    "reason": "stop" if stopped else "target", "observed_exit_quote": quote,
                    "modeled_exit": quote-side*slippage_pips*.0001 if stopped else target}
    return None
