"""Separate, immutable development tick datasets with explicit provenance."""
import csv
from datetime import datetime, timezone
import gzip
import io
import json
from pathlib import Path

from .cli import code_digest
from .histdata import archive_ticks, hourly
from .tick_audit import sha256

FIELDS = ["sequence","time_msc","bid","ask"]


def normalize(source: Path, output: Path, gate: Path):
    if output.exists():
        raise FileExistsError("Dataset destination exists")
    approval = json.loads(gate.read_text())
    archive_hash = sha256(source/"original.zip")
    if (approval.get("dataset_construction_ready") is not True
            or archive_hash not in {c.get("histdata_archive_sha256") for c in approval.get("checks",[])}):
        raise ValueError("Dataset lacks a passing source-bound diagnostic stage")
    output.mkdir(parents=True,exist_ok=False)
    count=0; first=None; previous=None; maximum=0; gaps=[]; over_minute=0
    partial=output/"ticks.csv.gz.partial"
    with partial.open("xb") as binary, gzip.GzipFile(filename="",mode="wb",fileobj=binary,mtime=0) as zipped, \
            io.TextIOWrapper(zipped,encoding="utf-8",newline="") as stream:
        writer=csv.DictWriter(stream,fieldnames=FIELDS)
        writer.writeheader()
        def record():
            nonlocal count,first,previous,maximum,over_minute
            for tick in archive_ticks(source):
                ms=tick["time_msc"]
                if first is None:first=ms
                if previous is not None:
                    gap=ms-previous;maximum=max(maximum,gap)
                    if gap>60_000:over_minute+=1
                    if gap>3_600_000:gaps.append({"after_ms":previous,"before_ms":ms,"seconds":gap/1000,"classification":"unclassified_never_filled"})
                previous=ms;count+=1;writer.writerow(tick)
                yield tick
        bars=list(hourly(record()))
    if not count:
        raise ValueError("Empty tick dataset")
    partial.rename(output/"ticks.csv.gz")
    with (output/"hourly-diagnostic.csv").open("x",encoding="utf-8",newline="") as stream:
        writer=csv.DictWriter(stream,fieldnames=list(bars[0]))
        writer.writeheader();writer.writerows(bars)
    provenance={"schema_version":1,"kind":"normalized_histdata_ticks","symbol":"EURUSD","role":"development",
                "created_utc":datetime.now(timezone.utc).isoformat(),"source":"HistData Generic ASCII tick ZIP",
                "source_archive_sha256":archive_hash,"source_metadata_sha256":sha256(source/"download.json"),
                "data_sha256":sha256(output/"ticks.csv.gz"),"hourly_sha256":sha256(output/"hourly-diagnostic.csv"),
                "gate_sha256":sha256(gate),"code_sha256":code_digest(),"ticks":count,"observed_hours":len(bars),
                "first_ms":first,"last_ms":previous,"maximum_intertick_gap_seconds":maximum/1000,
                "gaps_over_60_seconds":over_minute,"gaps_over_one_hour":gaps,
                "timezone":"UTC from provider documented fixed EST plus five hours, no DST",
                "timezone_authority":"https://www.histdata.com/f-a-q/data-files-detailed-specification/",
                "complete_market_history_verified":False,"broker_execution_conditions_verified":False,
                "limitations":["Cross-source screening covered selected windows, not every tick or entire month",
                               "No interpolation, silent filtering or reordering; same-millisecond order preserved",
                               "Gaps may represent closures, outages or missing quotes; causes are not certified",
                               "Development-only pilot; neither month is an untouched strategy holdout"]}
    (output/"provenance.json").write_text(json.dumps(provenance,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    return provenance


def read_ticks(folder: Path):
    metadata=json.loads((folder/"provenance.json").read_text())
    if (metadata.get("kind") not in ("normalized_histdata_ticks","normalized_mt5_ticks") or metadata.get("symbol")!="EURUSD"
            or metadata.get("role")!="development" or metadata["data_sha256"]!=sha256(folder/"ticks.csv.gz")):
        raise ValueError("Tick dataset integrity/type mismatch")
    count=0;previous=None;first=None
    with gzip.open(folder/"ticks.csv.gz","rt",newline="") as stream:
        reader=csv.DictReader(stream)
        if reader.fieldnames!=FIELDS:raise ValueError("Invalid normalized tick header")
        for row in reader:
            tick={"sequence":int(row["sequence"]),"time_msc":int(row["time_msc"]),"bid":float(row["bid"]),"ask":float(row["ask"])}
            import math
            if (tick["sequence"]!=count or previous is not None and tick["time_msc"]<previous
                    or not all(math.isfinite(tick[s]) for s in ("bid","ask")) or not 0<tick["bid"]<=tick["ask"]):
                raise ValueError("Invalid normalized tick row")
            if first is None:first=tick["time_msc"]
            count+=1;previous=tick["time_msc"]
            yield tick
    if count!=metadata["ticks"] or first!=metadata["first_ms"] or previous!=metadata["last_ms"]:
        raise ValueError("Tick dataset coverage mismatch")
