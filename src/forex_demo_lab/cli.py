"""Freeze data/parameters before chronological evaluation; standard library only."""
import argparse
import csv
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
import hashlib
import json
import math
from pathlib import Path
import random

from .model import Bar, Config, timestamp
from .simulation import Simulator

ENGINE_VERSION = 2


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def code_digest() -> str:
    value = hashlib.sha256()
    for path in sorted(Path(__file__).parent.glob("*.py")):
        value.update(path.name.encode())
        value.update(path.read_bytes())
    return value.hexdigest()


def read_bars(path: Path) -> list[Bar]:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != ["time", "open", "high", "low", "close", "spread_pips"]:
            raise ValueError("CSV header must be time,open,high,low,close,spread_pips")
        bars = []
        for row in reader:
            bar = Bar(timestamp(row["time"]), *(float(row[k]) for k in reader.fieldnames[1:]))
            if bars and (bar.time <= bars[-1].time or (bar.time - bars[-1].time).total_seconds() % 3600):
                raise ValueError("CSV timestamps must be unique, increasing and on the same H1 grid")
            bars.append(bar)
    if not bars:
        raise ValueError("CSV contains no bars")
    return bars


def write_json(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive creation prevents silently replacing a frozen experiment or result.
    content = json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"
    with path.open("x", encoding="utf-8") as stream:
        stream.write(content)


def freeze(data: Path, config_path: Path, split: str, manifest: Path,
           source: str, cost_notes: str, synthetic: bool, provenance_path: Path | None = None):
    config = Config(**json.loads(config_path.read_text(encoding="utf-8")))
    bars = read_bars(data)
    boundary = timestamp(split)
    if boundary.minute or boundary.second or boundary.microsecond or not bars[0].time < boundary <= bars[-1].time:
        raise ValueError("Holdout boundary must be an hour inside dataset coverage")
    development = sum(b.time < boundary for b in bars)
    if development <= config.slow + 1 or len(bars) - development < 2:
        raise ValueError("Need development warmup plus observations and at least two holdout candles")
    if not source.strip() or not cost_notes.strip():
        raise ValueError("Document data source and cost assumptions")
    provenance = None
    if not synthetic:
        if provenance_path is None:
            raise ValueError("Market-data experiments require --provenance from import-mt5")
        provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
        if (provenance.get("schema_version") != 1 or provenance.get("kind") != "normalized_mt5_h1"
                or provenance.get("symbol") != config.symbol or provenance.get("timeframe") != "H1"
                or provenance.get("price_side") != "bid" or provenance.get("synthetic") is not False
                or provenance.get("data_sha256") != digest(data)):
            raise ValueError("Market-data provenance does not match dataset")
        if (provenance["coverage"]["rows"] != len(bars)
                or provenance["coverage"]["first_bar"] != bars[0].time.isoformat()
                or provenance["coverage"]["last_bar"] != bars[-1].time.isoformat()):
            raise ValueError("Provenance coverage mismatch")
    elif provenance_path:
        raise ValueError("Do not attach market-data provenance to a synthetic experiment")
    write_json(manifest, {"engine_version": ENGINE_VERSION, "code_sha256": code_digest(),
                         "created_utc": datetime.now(timezone.utc).isoformat(),
                         "data_sha256": digest(data), "config": asdict(config),
                         "holdout_start": boundary.isoformat(), "rows": len(bars),
                         "development_rows": development, "holdout_rows": len(bars) - development,
                         "first_bar": bars[0].time.isoformat(), "last_bar": bars[-1].time.isoformat(),
                         "source": source, "cost_notes": cost_notes, "synthetic": synthetic,
                         "provenance": provenance,
                         "provenance_sha256": digest(provenance_path) if provenance_path else None})


def evaluate(data: Path, manifest_path: Path, partition: str, output: Path):
    if partition not in ("development", "holdout"):
        raise ValueError("Unknown partition")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest["engine_version"] != ENGINE_VERSION or manifest["code_sha256"] != code_digest():
        raise ValueError("Research code changed since freeze; create a new experiment")
    if digest(data) != manifest["data_sha256"]:
        raise ValueError("Dataset changed since freeze")
    config = Config(**manifest["config"])
    bars = read_bars(data)
    boundary = timestamp(manifest["holdout_start"])
    simulation = Simulator(config)
    if partition == "holdout":
        # Indicators use earlier history; positions, capital and daily state start fresh.
        simulation.history = [b for b in bars if b.time < boundary][-config.slow-1:]
        selected = [b for b in bars if b.time >= boundary]
    else:
        selected = [b for b in bars if b.time < boundary]
    for bar in selected:
        simulation.step(bar)
    simulation.finish()
    report = {"status": "synthetic_software_check" if manifest["synthetic"] else "unvalidated_ohlc_research",
              "partition": partition, "manifest_sha256": digest(manifest_path), "experiment": manifest,
              "first_bar": selected[0].time.isoformat(), "last_bar": selected[-1].time.isoformat(),
              "rows": len(selected),
              "missing_hours": sum(int((b.time - a.time).total_seconds() / 3600) - 1
                                   for a, b in zip(selected, selected[1:])),
              "metrics": simulation.metrics(), "trades": simulation.trades, "equity": simulation.curve,
              "limitations": ["H1 bid OHLC; constant spread within each candle; no tick ordering",
                              "Stop-first when stop and target both touch; gap losses can exceed risk estimate",
                              "Daily pause prevents new entries; existing positions retain stops and targets",
                              "Close-sampled drawdown understates possible intrabar drawdown",
                              "Hypothetical costs and simplified margin; no broker fills or margin liquidation",
                              "No historical profitability or forward performance has been established"]}
    write_json(output, report)
    return report


def synthetic_data(path: Path, count: int = 1200):
    """Deterministic test fixture, never presented as market evidence."""
    if count < 100:
        raise ValueError("Use at least 100 synthetic bars")
    rng = random.Random(741)
    path.parent.mkdir(parents=True, exist_ok=True)
    start = datetime(2024, 1, 1, tzinfo=timezone.utc)
    previous = 1.10
    with path.open("x", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(["time", "open", "high", "low", "close", "spread_pips"])
        for i in range(count):
            close = 1.10 + 0.005 * math.sin(i / 18) + rng.uniform(-0.0003, 0.0003)
            high = max(previous, close) + rng.uniform(0.0001, 0.0005)
            low = min(previous, close) - rng.uniform(0.0001, 0.0005)
            writer.writerow([(start + timedelta(hours=i)).isoformat(), *[f"{v:.6f}" for v in
                             (previous, high, low, close)], "1.0"])
            previous = close


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    fixture = commands.add_parser("synthetic", help="Generate software-test data, not market evidence")
    fixture.add_argument("--output", type=Path, required=True)
    fixture.add_argument("--bars", type=int, default=1200)
    importer = commands.add_parser("import-mt5", help="Normalize a bid H1 export with explicit costs and time provenance")
    importer.add_argument("--input", type=Path, required=True)
    importer.add_argument("--output", type=Path, required=True, help="New directory for bars.csv and provenance.json")
    importer.add_argument("--source", required=True)
    importer.add_argument("--as-of", required=True, help="Offset-aware extraction time; unfinished last bar is omitted")
    importer.add_argument("--spread-pips", type=float, required=True, help="Explicit hypothetical constant entry/exit spread")
    importer.add_argument("--spread-notes", required=True)
    importer.add_argument("--point-size", type=float, required=True)
    importer.add_argument("--source-timezone", help="Verified IANA timezone; only for native MT5 exports")
    importer.add_argument("--capture", type=Path, help="Collector capture.json to verify input hash and coverage")
    importer.add_argument("--api-timezone", help="Explicit IANA interpretation of raw API labels, including Etc/UTC if confirmed")
    importer.add_argument("--timezone-notes", help="Evidence and limitations for the chosen historical time mapping")
    lock = commands.add_parser("freeze", help="Record split, costs, code and data before evaluation")
    lock.add_argument("--data", type=Path, required=True)
    lock.add_argument("--config", type=Path, required=True)
    lock.add_argument("--holdout-start", required=True)
    lock.add_argument("--manifest", type=Path, required=True)
    lock.add_argument("--source", required=True, help="Public market-data provenance; no account identifiers")
    lock.add_argument("--cost-notes", required=True)
    lock.add_argument("--synthetic", action="store_true")
    lock.add_argument("--provenance", type=Path, help="Required normalized provenance.json for market data")
    run = commands.add_parser("run")
    run.add_argument("--data", type=Path, required=True)
    run.add_argument("--manifest", type=Path, required=True)
    run.add_argument("--partition", choices=("development", "holdout"), required=True)
    run.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "synthetic":
            synthetic_data(args.output, args.bars)
        elif args.command == "import-mt5":
            from .ingestion import normalize
            provenance = normalize(args.input, args.output, args.source, timestamp(args.as_of),
                                   args.spread_pips, args.spread_notes, args.point_size,
                                   args.source_timezone, args.capture, args.api_timezone, args.timezone_notes)
            print(json.dumps({"coverage": {k: v for k, v in provenance["coverage"].items() if k != "gaps"},
                              "dropped_incomplete_rows": provenance["dropped_incomplete_rows"],
                              "spread_policy": provenance["spread_policy"]}, indent=2))
        elif args.command == "freeze":
            freeze(args.data, args.config, args.holdout_start, args.manifest, args.source, args.cost_notes,
                   args.synthetic, args.provenance)
        else:
            report = evaluate(args.data, args.manifest, args.partition, args.output)
            print(json.dumps({"status": report["status"], "metrics": report["metrics"]}, indent=2))
    except (ValueError, OSError, KeyError, TypeError) as exc:
        parser.exit(2, f"Error: {exc}\n")


if __name__ == "__main__":
    main()
