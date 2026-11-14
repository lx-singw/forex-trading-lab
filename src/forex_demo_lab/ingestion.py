"""Strict normalization of MT5 H1 exports with explicit time and cost provenance."""
import csv
from datetime import datetime, timedelta, timezone
import hashlib
import io
import json
import math
from pathlib import Path
from zoneinfo import ZoneInfo

from .collection import RAW_FIELDS
from .model import Bar, timestamp

NATIVE_FIELDS = ["<DATE>", "<TIME>", "<OPEN>", "<HIGH>", "<LOW>", "<CLOSE>",
                 "<TICKVOL>", "<VOL>", "<SPREAD>"]
FIELDS = ["time", "open", "high", "low", "close", "spread_pips"]


def local_to_utc(value: datetime, zone: ZoneInfo) -> datetime:
    candidates = set()
    for fold in (0, 1):
        utc = value.replace(tzinfo=zone, fold=fold).astimezone(timezone.utc)
        if utc.astimezone(zone).replace(tzinfo=None) == value:
            candidates.add(utc)
    if len(candidates) != 1:
        raise ValueError("Ambiguous or nonexistent broker timestamp; explicit per-row UTC offsets required")
    return candidates.pop()


def audit(bars: list[Bar]) -> dict:
    gaps = [{"after": a.time.isoformat(), "before": b.time.isoformat(),
             "missing_hours": int((b.time-a.time).total_seconds()/3600)-1}
            for a, b in zip(bars, bars[1:]) if b.time-a.time > timedelta(hours=1)]
    return {"rows": len(bars), "first_bar": bars[0].time.isoformat(), "last_bar": bars[-1].time.isoformat(),
            "missing_hours": sum(g["missing_hours"] for g in gaps), "gaps": gaps,
            "gap_classification": "Unclassified: may include market closures and outages; never filled"}


def normalize(raw: Path, output: Path, source: str, as_of: datetime, spread_pips: float,
              spread_notes: str, point_size: float, source_timezone: str | None = None,
              capture_path: Path | None = None, api_timezone: str | None = None,
              timezone_notes: str | None = None) -> dict:
    if output.exists():
        raise FileExistsError("Import destination already exists; choose a new directory")
    if as_of.tzinfo is None or as_of > datetime.now(timezone.utc):
        raise ValueError("As-of must be an offset-aware extraction time, not a future time")
    if not source.strip() or not spread_notes.strip():
        raise ValueError("Source and explicit spread assumption notes are required")
    if not math.isfinite(spread_pips) or spread_pips <= 0:
        raise ValueError("A positive finite modeled spread is required")
    if point_size not in (0.00001, 0.0001):
        raise ValueError("Only four/five-digit EURUSD point sizes are supported")
    content = raw.read_bytes()
    raw_hash = hashlib.sha256(content).hexdigest()
    # BOM-aware; desktop MT5 exports may be UTF-16 or UTF-8.
    decoded = content.decode("utf-16" if content[:2] in (b"\xff\xfe", b"\xfe\xff") else "utf-8-sig")
    if not decoded.strip():
        raise ValueError("Empty export")
    delimiter = "\t" if "\t" in decoded.splitlines()[0] else ","
    reader = csv.DictReader(io.StringIO(decoded), delimiter=delimiter)
    if reader.fieldnames == RAW_FIELDS:
        kind = "mt5_python_labels"
        if source_timezone is not None:
            raise ValueError("Use api_timezone for raw API labels, not source_timezone")
        if not api_timezone or not timezone_notes or not timezone_notes.strip():
            raise ValueError("API labels require an explicit IANA interpretation and timezone evidence/assumption notes")
    elif reader.fieldnames == NATIVE_FIELDS:
        kind = "mt5_native_bars"
        if source_timezone is None or api_timezone is not None:
            raise ValueError("Native MT5 export requires a verified IANA source timezone")
    else:
        raise ValueError("Unsupported export header; expected MT5 native bars or read-only collector CSV")
    zone = ZoneInfo(source_timezone or api_timezone)
    capture_summary = None
    if capture_path:
        meta = json.loads(capture_path.read_text(encoding="utf-8"))
        if (meta.get("schema_version") != 2 or meta.get("kind") != "mt5_readonly_capture"
                or meta.get("symbol") != "EURUSD" or meta.get("timeframe") != "H1"
                or meta.get("price_side") != "bid" or meta.get("synthetic") is not False
                or meta.get("raw_sha256") != raw_hash or kind != "mt5_python_labels"):
            raise ValueError("Capture provenance/hash does not match EURUSD H1 bid input")
        if meta["current_snapshot"]["symbol"]["point"] != point_size:
            raise ValueError("Point size conflicts with captured symbol specification")
        if timestamp(meta["captured_utc"]) != as_of:
            raise ValueError("As-of must match the capture's extraction timestamp")
        if api_timezone == "Etc/UTC" and meta["clock_observation"]["status"] == "ahead_of_utc":
            raise ValueError("Current clock observation contradicts UTC; supply a documented source-time mapping")
        # Only harmless, deliberately selected provenance fields cross into reports.
        capture_summary = {k: meta[k] for k in ("captured_utc", "requested_start", "requested_end_exclusive",
                                                "first_bar", "last_bar", "rows", "package_version", "clock_observation")}
    bars, observed_spreads = [], []
    previous = None
    dropped = 0
    input_rows = 0
    first_raw, last_raw = None, None
    for line, row in enumerate(reader, 2):
        try:
            if None in row or any(v is None for v in row.values()):
                raise ValueError("Unexpected column count")
            if kind == "mt5_native_bars":
                naive = datetime.strptime(row["<DATE>"]+" "+row["<TIME>"], "%Y.%m.%d %H:%M:%S")
                time = local_to_utc(naive, zone)
                prices = [float(row[f"<{k.upper()}>"]) for k in ("open", "high", "low", "close")]
                spread = int(row["<SPREAD>"])
                volumes = [int(row[k]) for k in ("<TICKVOL>", "<VOL>")]
            else:
                raw_time = timestamp(row["time"])
                first_raw = first_raw or raw_time.isoformat()
                last_raw = raw_time.isoformat()
                time = local_to_utc(raw_time.replace(tzinfo=None), zone)
                prices = [float(row[k]) for k in ("open", "high", "low", "close")]
                spread = int(row["spread_points"])
                volumes = [int(row[k]) for k in ("tick_volume", "real_volume")]
            bar = Bar(time, *prices, spread_pips)
            if min(spread, *volumes) < 0:
                raise ValueError("Negative spread or volume")
            if previous and (time <= previous or (time-previous).total_seconds() % 3600):
                raise ValueError("Duplicate, reordered or off-grid H1 candle")
            if time > as_of:
                raise ValueError("Future candle relative to extraction time")
            previous = time
            input_rows += 1
            if time + timedelta(hours=1) > as_of:
                dropped += 1
                continue
            bars.append(bar)
            observed_spreads.append(spread * point_size / 0.0001)
        except (ValueError, TypeError):
            # Do not echo raw rows, input values or arbitrary supplied metadata.
            raise ValueError(f"Invalid MT5 candle at CSV line {line}; check time, OHLC, counts and ordering") from None
    if not bars:
        raise ValueError("No completed H1 candles remain")
    if capture_summary and (capture_summary["rows"] != input_rows or
                            capture_summary["first_bar"] != first_raw or capture_summary["last_bar"] != last_raw):
        raise ValueError("Capture row count/coverage does not match raw data")
    output.mkdir(parents=True, exist_ok=False)
    destination = output / "bars.csv"
    with destination.open("x", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(b.to_dict() for b in bars)
    provenance = {"schema_version": 1, "kind": "normalized_mt5_h1", "symbol": "EURUSD",
                  "timeframe": "H1", "price_side": "bid", "synthetic": False, "source": source,
                  "as_of": as_of.isoformat(), "input_format": kind, "source_timezone": source_timezone,
                  "timestamp_convention": "UTC after explicit source-label conversion",
                  "api_label_timezone": api_timezone,
                  "timezone_notes": timezone_notes or "Native export source timezone supplied by operator",
                  "historical_timezone_verified": False,
                  "raw_sha256": raw_hash, "data_sha256": hashlib.sha256(destination.read_bytes()).hexdigest(),
                  "point_size": point_size, "input_rows": input_rows, "dropped_incomplete_rows": dropped,
                  "spread_policy": {"kind": "constant_assumption", "pips": spread_pips, "notes": spread_notes,
                                    "historical_execution_spread_verified": False},
                  "raw_bar_spread_pips": {"min": min(observed_spreads), "max": max(observed_spreads),
                                          "use": "Audit only; not used for entry decisions or fills"},
                  "coverage": audit(bars), "capture": capture_summary,
                  "limitations": ["H1 declaration depends on source export settings; sparse rows cannot prove timeframe",
                                   "No measured opening spread or intrabar bid/ask path",
                                   "Commission, historical swaps, broker day and slippage remain separate assumptions"]}
    (output / "provenance.json").write_text(json.dumps(provenance, indent=2, allow_nan=False)+"\n", encoding="utf-8")
    return provenance
