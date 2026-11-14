"""Freeze and replay development ticks only after an explicit data-quality review."""
from dataclasses import asdict
import json
from pathlib import Path

from .cli import code_digest, write_json
from .model import Config
from .tick_audit import sha256
from .tick_dataset import read_ticks
from .tick_simulation import TickSimulator


def freeze(dataset: Path, config_path: Path, quality: Path, manifest: Path):
    review=json.loads(quality.read_text())
    provenance_hash=sha256(dataset/"provenance.json")
    matching=[d for d in review.get("datasets",[]) if d.get("provenance_sha256")==provenance_hash]
    if (review.get("performance_evaluation_ready") is not True or len(matching)!=1
            or matching[0].get("status")!="ready_for_development_research"):
        raise ValueError("Data-quality review blocks performance evaluation for this dataset")
    config=Config(**json.loads(config_path.read_text()))
    TickSimulator(config) # Validate engine-specific constraints before publishing.
    count=sum(1 for _ in read_ticks(dataset))
    if count<2:raise ValueError("Insufficient observations")
    write_json(manifest,{"kind":"frozen_development_tick_experiment","code_sha256":code_digest(),
                         "config":asdict(config),"provenance_sha256":provenance_hash,
                         "data_sha256":sha256(dataset/"ticks.csv.gz"),"quality_review_sha256":sha256(quality),
                         "ticks":count,"role":"development","broker_execution_authorized":False})


def evaluate(dataset: Path, manifest: Path, quality: Path, output: Path):
    frozen=json.loads(manifest.read_text())
    review=json.loads(quality.read_text())
    if (frozen.get("kind")!="frozen_development_tick_experiment" or frozen.get("role")!="development"
            or frozen["code_sha256"]!=code_digest() or frozen["data_sha256"]!=sha256(dataset/"ticks.csv.gz")
            or frozen["provenance_sha256"]!=sha256(dataset/"provenance.json")
            or frozen["quality_review_sha256"]!=sha256(quality) or review.get("performance_evaluation_ready") is not True):
        raise ValueError("Frozen code, dataset or data-quality review changed")
    sim=TickSimulator(Config(**frozen["config"]))
    for tick in read_ticks(dataset):sim.step_tick(tick)
    if sim.metrics()["ticks_processed"]!=frozen["ticks"]:raise ValueError("Frozen tick count mismatch")
    sim.finish()
    report={"status":"development_tick_simulation_not_forward_validation","manifest_sha256":sha256(manifest),
            "metrics":sim.metrics(),"trades":sim.trades,"hourly_equity":sim.curve,
            "limitations":["Quote snapshots are not broker fills; no order queue, latency or available-depth model",
                           "Stops use next observed bid/ask plus assumed slippage; gaps can exceed estimated risk",
                           "Missing hours never fabricated; signals at the first hour after a gap are discarded",
                           "Commission, swaps, UTC daily reset and margin remain model assumptions",
                           "No real or demo order placement, untouched holdout or profitability guarantee"]}
    write_json(output,report)
    return report
