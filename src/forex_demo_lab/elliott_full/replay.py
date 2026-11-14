"""Strict fixture replay with deterministic checkpoints and exclusive outputs."""
import json
import csv
import gzip
import io
from pathlib import Path
from .contracts import validate_bundle, digest, bindings
from .strategy import Strategy
from .execution import Ledger
from .report import render
from .admission import study_status
from .engine import Engine


def evaluate(bundle, profile="base"):
    bars, quotes = validate_bundle(bundle)
    engine = Engine(profile)
    cursor, pending = 0, None
    for quote in quotes:
        while cursor < len(bars) and bars[cursor].available <= quote.time:
            engine.step({"kind":"bar","value":bars[cursor].record()})
            cursor += 1
        engine.step({"kind":"quote","value":quote.record()})
    while cursor < len(bars):
        engine.step({"kind":"bar","value":bars[cursor].record()})
        cursor += 1
    strategy,ledger=engine.strategy,engine.ledger
    return {"version": "EW_FULL_V1", "kind": "invented_software_evidence", "input_digest": digest(bundle),
            "profile": profile, "bindings": bindings(), "market_validation": "UNAVAILABLE", "orders_available": False,
            "implementation_status": "prototype_acceptance_incomplete", "study": study_status(),
            "bars": [b.record() for b in bars], "snapshots": strategy.snapshots,
            "ledger": ledger.state(), "checkpoint": engine.checkpoint(),
            "limitations": ["No qualified market adapter or source assigned", "No certified bar aggregation",
                             "Pattern-location and full catalogue acceptance incomplete", "No native execution adapter",
                             "Counts use finite-resolution leaves; market probabilities unavailable"]}


def write_report(bundle, output, profile="base"):
    result = evaluate(bundle, profile)
    path = Path(output)
    path.mkdir(parents=True, exist_ok=False)
    checkpoint=result.pop("checkpoint")
    with (path/"checkpoint.json.gz").open("wb") as raw:
        with gzip.GzipFile(filename="",mode="wb",fileobj=raw,mtime=0,compresslevel=1) as compressed:
            with io.TextIOWrapper(compressed,encoding="utf-8") as text:
                json.dump(checkpoint,text,separators=(",",":"))
    result["checkpoint"]={"path":"checkpoint.json.gz","digest":checkpoint["digest"]}
    result["artifact_schema"]="EW_FULL_V1_REPORT_V2"
    # Complete trees and original events remain in the independently restorable
    # checkpoint. The report retains all alternatives and their source anchors.
    result["snapshots"]=[{**s,"counts":[{k:v for k,v in c.items() if k!="children"} for c in s["counts"]]}
                         for s in result["snapshots"]]
    (path/"report.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    (path/"replay.html").write_text(render(result), encoding="utf-8")
    with (path/"trades.csv").open("w",encoding="utf-8",newline="") as stream:
        writer=csv.DictWriter(stream,fieldnames=("key","reason","gross","net","estimated_risk","exit","time"))
        writer.writeheader()
        writer.writerows(result["ledger"]["trades"])
    return result
