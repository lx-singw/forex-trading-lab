"""Freeze and evaluate every predeclared candidate; no selection or broker execution."""
import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import sys
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from forex_demo_lab.cli import code_digest, write_json
from forex_demo_lab.model import Config
from forex_demo_lab.research_simulation import ResearchTickSimulator
from forex_demo_lab.strategies import CANDIDATES
from forex_demo_lab.tick_audit import sha256
from forex_demo_lab.tick_dataset import read_ticks

SPEC = Path("config/research-candidates-008.json")
PROTOCOL = Path("docs/COMPARISON-008-PLAN.md")
LEDGER = Path("reports/comparison-008-ledger.json")
ARCHIVE = Path("reports/comparison-008-source.zip")
SAMPLES = {
    "january": (Path("data/research-004-january-mt5"), Path("reports/research-quality-004.json")),
    "april": (Path("data/research-005-april-new-york"), Path("reports/research-quality-005.json")),
    "july": (Path("data/research-004-july-new-york"), Path("reports/research-quality-004.json")),
}


def load(path):
    return json.loads(path.read_text())


def reviewed_dataset(folder, quality):
    review = load(quality)
    digest = sha256(folder / "provenance.json")
    matches = [d for d in review.get("datasets", []) if d.get("provenance_sha256") == digest]
    if (review.get("performance_evaluation_ready") is not True or len(matches) != 1
            or matches[0].get("status") != "ready_for_development_research"):
        raise ValueError("Dataset-specific quality review does not permit research")
    p = load(folder / "provenance.json")
    if p["data_sha256"] != sha256(folder / "ticks.csv.gz"):
        raise ValueError("Dataset changed")
    return {"provenance_sha256": digest, "data_sha256": p["data_sha256"], "quality_sha256": sha256(quality)}


def freeze_batch():
    if LEDGER.exists() or ARCHIVE.exists():
        raise FileExistsError("Batch already frozen")
    spec = load(SPEC)
    if tuple(c["id"] for c in spec["candidates"]) != CANDIDATES:
        raise ValueError("Candidate set differs from declared implementation")
    datasets = {}
    for sample, (folder, quality) in SAMPLES.items():
        binding = reviewed_dataset(folder, quality)
        hours, count, last = [], 0, None
        for tick in read_ticks(folder):
            hour = tick["time_msc"] // 3600000
            if not hours or hour != hours[-1]:
                hours.append(hour)
            count += 1
            last = tick["time_msc"]
        if len(hours) <= 202:
            raise ValueError("Insufficient history after shared warmup")
        datasets[sample] = {**binding, "ticks": count, "observed_hours": len(hours), "warmup_hours": 201,
                            "evaluation_start_ms": hours[201] * 3600000, "last_quote_ms": last,
                            "evaluation_start_utc": datetime.fromtimestamp(hours[201] * 3600, timezone.utc).isoformat()}
        print(f"Reviewed {sample}: {count} ticks; evaluation from {datasets[sample]['evaluation_start_utc']}", flush=True)
    configs = {}
    for cost in ("base", "adverse"):
        path = Path("config/tick-pilot-003.json" if cost == "base" else "config/tick-pilot-003-adverse.json")
        configs[cost] = asdict(Config(**load(path)))
        if configs[cost] != load(Path(f"reports/research-005-april-new-york-{cost}-manifest.json"))["config"]:
            raise ValueError("Shared risk/cost configuration changed")
    scenarios = [{"id": f"{sample}-{candidate}-{cost}", "sample": sample, "candidate": candidate,
                  "cost": cost, "config": configs[cost]} for sample in SAMPLES for candidate in CANDIDATES for cost in configs]
    with zipfile.ZipFile(ARCHIVE, "x", compression=zipfile.ZIP_DEFLATED) as z:
        for root in (Path("src"), Path("scripts"), Path("tests")):
            for path in sorted(root.rglob("*.py")):
                z.write(path, path.as_posix())
        for path in (SPEC, PROTOCOL, Path("config/tick-pilot-003.json"), Path("config/tick-pilot-003-adverse.json")):
            z.write(path, path.as_posix())
    write_json(LEDGER, {"kind": "fixed_candidate_development_batch", "code_sha256": code_digest(),
               "spec_sha256": sha256(SPEC), "protocol_sha256": sha256(PROTOCOL),
               "runner_sha256": sha256(Path(__file__)), "archive_sha256": sha256(ARCHIVE),
               "datasets": datasets, "scenarios": scenarios, "independent_starting_capital": True,
               "data_role": "reused_development", "selection_or_promotion_authorized": False,
               "demo_execution_ready": False, "cash_reference_net_pnl": 0})
    print(f"Frozen {len(scenarios)} scenarios before returns", flush=True)


def verify_batch():
    ledger = load(LEDGER)
    if (ledger["code_sha256"] != code_digest() or ledger["spec_sha256"] != sha256(SPEC)
            or ledger["protocol_sha256"] != sha256(PROTOCOL) or ledger["archive_sha256"] != sha256(ARCHIVE)
            or ledger["runner_sha256"] != sha256(Path(__file__))):
        raise ValueError("Frozen implementation, specification or protocol changed")
    for sample, (folder, quality) in SAMPLES.items():
        checked = reviewed_dataset(folder, quality)
        if any(ledger["datasets"][sample][key] != value for key, value in checked.items()):
            raise ValueError("Frozen data/review changed")
    return ledger


def reconcile(sim, metrics, start):
    if any(int(datetime.fromisoformat(t["opened"]).timestamp() * 1000) < start for t in sim.trades):
        raise ValueError("Warmup trade contamination")
    for trade in sim.trades:
        if not math.isclose(trade["gross_pnl"] - trade["commission"] + trade["swap"], trade["net_pnl"], abs_tol=1e-8):
            raise ValueError("Trade accounting mismatch")
    for key in ("net_pnl", "commission", "swap"):
        if not math.isclose(sum(t[key] for t in sim.trades), metrics[key], abs_tol=1e-8):
            raise ValueError("Aggregate accounting mismatch")
    if not (len(sim.trades) == metrics["closed_trades"]
            and math.isclose(sim.config.initial_equity + metrics["net_pnl"], sim.curve[-1]["equity"], abs_tol=1e-8)
            and math.isclose(metrics["net_return"], metrics["net_pnl"] / sim.config.initial_equity, abs_tol=1e-10)):
        raise ValueError("Final equity/count/return mismatch")


def run_batch():
    ledger = verify_batch()
    outputs = [Path(f"reports/comparison-008-{s['id']}.json") for s in ledger["scenarios"]]
    if any(p.exists() for p in outputs) or Path("reports/comparison-008-summary.json").exists():
        raise FileExistsError("Batch output exists; do not overwrite or silently rerun")
    summaries = []
    for sample, (folder, _) in SAMPLES.items():
        selected = [s for s in ledger["scenarios"] if s["sample"] == sample]
        start = ledger["datasets"][sample]["evaluation_start_ms"]
        simulations = [(s, ResearchTickSimulator(Config(**s["config"]), s["candidate"], start)) for s in selected]
        # One ordered read, isolated account state for every candidate/cost scenario.
        for count, tick in enumerate(read_ticks(folder), 1):
            for _, sim in simulations:
                sim.step_tick(tick)
            if count % 1000000 == 0:
                print(f"{sample}: processed {count} / {ledger['datasets'][sample]['ticks']} ticks for all ten scenarios", flush=True)
        for scenario, sim in simulations:
            sim.finish()
            metrics = sim.metrics()
            if metrics["ticks_processed"] != ledger["datasets"][sample]["ticks"] or metrics["warmup_hours"] != 201:
                raise ValueError("Frozen input coverage differs")
            reconcile(sim, metrics, start)
            output = Path(f"reports/comparison-008-{scenario['id']}.json")
            curve = [p for p in sim.curve if int(datetime.fromisoformat(p["time"]).timestamp() * 1000) >= start]
            write_json(output, {"status": "exploratory_reused_development_not_validation", "ledger_sha256": sha256(LEDGER),
                       "scenario": scenario["id"], "metrics": metrics, "trades": sim.trades, "equity": curve,
                       "flat_account_decisions": sim.decision_log, "demo_execution_ready": False})
            row = {"scenario": scenario["id"], "candidate": scenario["candidate"], "sample": sample,
                   "cost": scenario["cost"], "metrics": metrics, "report_sha256": sha256(output), "reconciled": True}
            summaries.append(row)
            print(json.dumps({"scenario": scenario["id"], "trades": metrics["closed_trades"],
                              "net_pnl": metrics["net_pnl"], "max_tick_drawdown": metrics["max_tick_drawdown"]}), flush=True)
    write_json(Path("reports/comparison-008-summary.json"), {"ledger_sha256": sha256(LEDGER), "scenarios": summaries,
               "status": "completed_exploratory_batch_no_selection", "cash_reference_net_pnl": 0,
               "demo_execution_ready": False, "not_independent_trials": "Costs/candidates reuse observations; monthly capital restarts"})


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("freeze", "run", "verify"))
    args = parser.parse_args()
    {"freeze": freeze_batch, "run": run_batch, "verify": verify_batch}[args.action]()
