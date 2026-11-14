"""Fresh October clock evidence and explicitly separate provisional study."""
import argparse
import csv
import importlib.util
import json
import math
from pathlib import Path
import shutil
import zipfile

spec = importlib.util.spec_from_file_location("research005", Path(__file__).with_name("research-005.py"))
prior = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prior)
from forex_demo_lab.cli import code_digest, write_json
from forex_demo_lab.histdata import archive_ticks
from forex_demo_lab.reconstruction import checked_capture
from forex_demo_lab.tick_audit import sha256
from forex_demo_lab.tick_workflow import freeze, evaluate

PROTOCOL = Path("docs/RESEARCH-006-PLAN.md")
EVIDENCE = Path("reports/research-006-clock.json")
QUALITY = Path("reports/research-quality-006.json")
SOURCE = Path("data/histdata-eurusd-202410-original")


def activity(ticks, minutes, shift=0):
    groups = {m: {"ticks": 0, "low": None, "high": None} for m in minutes}
    for tick in ticks:
        minute = (tick["time_msc"] + shift) // 60000
        if minute not in groups:
            continue
        g = groups[minute]
        g["ticks"] += 1
        g["low"] = min(g["low"], tick["bid"]) if g["low"] is not None else tick["bid"]
        g["high"] = max(g["high"], tick["bid"]) if g["high"] is not None else tick["bid"]
    for g in groups.values():
        g["range_pips"] = (g["high"] - g["low"]) / .0001 if g["ticks"] else 0
    return groups


def event_passes(control, event):
    return (control["ticks"] > 0 and control["range_pips"] > 0
            and event["ticks"] >= 2 * control["ticks"]
            and event["range_pips"] >= 3 * control["range_pips"])


def expected_capture(folder, day):
    metadata, ticks, lower, upper = checked_capture(folder)
    start = prior.epoch(day) + 12 * 3600000
    if (lower, upper) != (start, start + 6 * 3600000):
        raise ValueError("Capture bounds differ from declared date/window")
    return ticks


def all_evidence_passes(events, coverage):
    return (len(events) == 2 and {e["date"] for e in events} == {"20241030", "20241031"}
            and all(e["histdata_event_passed"] and e["broker_event_passed"]
                    and e["utc_plus_3_comparison"]["passed"] for e in events)
            and len(coverage) == 2 and all(not v for v in coverage.values()))


def check():
    old_quality = Path("reports/research-quality-005.json")
    old_review = prior.load(old_quality)
    reference_folder = Path("data/research-005-october-new-york")
    coverage = {}
    predecessors = {}
    for clock, offset in (("new-york", 4), ("fixed-est", 5)):
        folder = Path(f"data/research-005-october-{clock}")
        p = prior.load(folder / "provenance.json")
        bound = [d for d in old_review["datasets"] if d["scenario"] == f"october-{clock}"]
        if (len(bound) != 1 or bound[0]["provenance_sha256"] != sha256(folder / "provenance.json")
                or p["source_archive_sha256"] != sha256(SOURCE / "original.zip")
                or p["source_metadata_sha256"] != sha256(SOURCE / "download.json")
                or p["data_sha256"] != sha256(folder / "ticks.csv.gz")
                or p["hourly_sha256"] != sha256(folder / "hourly-diagnostic.csv")
                or p["code_sha256"] != code_digest()):
            raise ValueError("Predecessor evidence changed")
        predecessors[clock] = sha256(folder / "provenance.json")
        coverage[clock] = prior.coverage_failures(p, prior.epoch("20241001") + offset * 3600000,
                                                prior.epoch("20241101") + offset * 3600000)
    with (reference_folder / "hourly-diagnostic.csv").open() as stream:
        reference = {int(r["hour"]): float(r["bid_close"]) for r in csv.DictReader(stream)}
    days = ("20241030", "20241031")
    minutes = [prior.epoch(day) // 60000 + m for day in days for m in (450, 510)]
    hist = activity(archive_ticks(SOURCE), minutes, shift=-5 * 3600000)
    events = []
    for day in days:
        folder = Path(f"data/research-006-mt5-october{day[-2:]}")
        ticks = expected_capture(folder, day)
        start = prior.epoch(day) // 60000
        broker = activity(ticks, [start + m for m in (870, 930, 990)])
        events.append({"date": day, "capture_sha256": sha256(folder / "capture.json"),
                       "histdata_minutes": {"0730": hist[start + 450], "0830": hist[start + 510]},
                       "broker_minutes": {"1430": broker[start + 870], "1530": broker[start + 930], "1630": broker[start + 990]},
                       "histdata_event_passed": event_passes(hist[start + 450], hist[start + 510]),
                       "broker_event_passed": event_passes(broker[start + 870], broker[start + 930]),
                       "utc_plus_3_comparison": prior.compare_window(reference, folder, 3),
                       "utc_plus_2_alternative": prior.compare_window(reference, folder, 2)})
    passed = all_evidence_passes(events, coverage)
    report = {"protocol_sha256": sha256(PROTOCOL), "events": events, "coverage_failures": coverage,
              "source_archive_sha256": sha256(SOURCE / "original.zip"), "predecessors": predecessors,
              "prior_quality_sha256": sha256(old_quality), "passed": passed,
              "status": "scoped_clock_hypothesis_supported" if passed else "blocked_clock_evidence",
              "provider_certified": False, "demo_execution_ready": False}
    write_json(EVIDENCE, report)
    datasets = []
    if passed:
        for clock in predecessors:
            old = Path(f"data/research-005-october-{clock}")
            new = Path(f"data/research-006-october-{clock}")
            new.mkdir(parents=True, exist_ok=False)
            for name in ("ticks.csv.gz", "hourly-diagnostic.csv"):
                shutil.copyfile(old / name, new / name)
                if sha256(old / name) != sha256(new / name):
                    raise ValueError("Quote copy changed")
            p = prior.load(old / "provenance.json")
            p.update({"scenario": f"october-{clock}", "protocol_sha256": sha256(PROTOCOL),
                      "predecessor_provenance_sha256": predecessors[clock], "clock_evidence_sha256": sha256(EVIDENCE),
                      "research_version": "006", "prior_blocked_review_sha256": report["prior_quality_sha256"]})
            write_json(new / "provenance.json", p)
            datasets.append({"scenario": f"october-{clock}", "provenance_sha256": sha256(new / "provenance.json"),
                             "ticks": p["ticks"], "status": "ready_for_development_research"})
    write_json(QUALITY, {"protocol_sha256": sha256(PROTOCOL), "clock_evidence_sha256": sha256(EVIDENCE),
                        "datasets": datasets, "performance_evaluation_ready": passed, "demo_execution_ready": False,
                        "scope": "October provisional development only; 005 gate remains unchanged"})
    print(json.dumps(report), flush=True)


def freeze_all():
    review = prior.load(QUALITY)
    if (review["protocol_sha256"] != sha256(PROTOCOL) or review["clock_evidence_sha256"] != sha256(EVIDENCE)
            or review["performance_evaluation_ready"] is not True):
        raise ValueError("New evidence does not permit performance evaluation")
    evidence = prior.load(EVIDENCE)
    if evidence["protocol_sha256"] != sha256(PROTOCOL) or evidence["passed"] is not True:
        raise ValueError("Changed/failed evidence")
    manifests = {}
    for clock in ("new-york", "fixed-est"):
        for cost in ("base", "adverse"):
            scenario = f"october-{clock}-{cost}"
            config = Path("config/tick-pilot-003.json" if cost == "base" else "config/tick-pilot-003-adverse.json")
            old = prior.load(Path(f"reports/research-005-april-new-york-{cost}-manifest.json"))
            if prior.load(config) != old["config"]:
                raise ValueError("Baseline configuration changed")
            manifest = Path(f"reports/research-006-{scenario}-manifest.json")
            freeze(Path(f"data/research-006-october-{clock}"), config, QUALITY, manifest)
            manifests[scenario] = sha256(manifest)
    archive = Path("reports/research-006-source.zip")
    with zipfile.ZipFile(archive, "x", compression=zipfile.ZIP_DEFLATED) as z:
        for root in (Path("src"), Path("scripts"), Path("tests")):
            for path in sorted(root.rglob("*.py")):
                z.write(path, path.as_posix())
        for path in (PROTOCOL, Path("config/tick-pilot-003.json"), Path("config/tick-pilot-003-adverse.json")):
            z.write(path, path.as_posix())
    write_json(Path("reports/research-006-freeze.json"), {"manifests": manifests, "code_sha256": code_digest(),
               "quality_sha256": sha256(QUALITY), "protocol_sha256": sha256(PROTOCOL), "source_archive_sha256": sha256(archive)})
    print("Frozen all four October scenarios", flush=True)


def run():
    frozen = prior.load(Path("reports/research-006-freeze.json"))
    if (frozen["code_sha256"] != code_digest() or frozen["quality_sha256"] != sha256(QUALITY)
            or frozen["protocol_sha256"] != sha256(PROTOCOL)
            or frozen["source_archive_sha256"] != sha256(Path("reports/research-006-source.zip"))):
        raise ValueError("Frozen study changed")
    for scenario, digest in frozen["manifests"].items():
        if sha256(Path(f"reports/research-006-{scenario}-manifest.json")) != digest:
            raise ValueError("Manifest changed")
    summaries = []
    for scenario in frozen["manifests"]:
        manifest = Path(f"reports/research-006-{scenario}-manifest.json")
        output = Path(f"reports/research-006-{scenario}.json")
        r = evaluate(Path("data/research-006-" + scenario.rsplit("-", 1)[0]), manifest, QUALITY, output)
        for t in r["trades"]:
            if not math.isclose(t["gross_pnl"] - t["commission"] + t["swap"], t["net_pnl"], abs_tol=1e-8):
                raise ValueError("Trade accounting failed")
        for key in ("net_pnl", "commission", "swap"):
            if not math.isclose(sum(t[key] for t in r["trades"]), r["metrics"][key], abs_tol=1e-8):
                raise ValueError("Aggregate accounting failed")
        initial = prior.load(manifest)["config"]["initial_equity"]
        if not math.isclose(initial + r["metrics"]["net_pnl"], r["hourly_equity"][-1]["equity"], abs_tol=1e-8):
            raise ValueError("Final equity reconciliation failed")
        summary = {"scenario": scenario, "metrics": r["metrics"], "report_sha256": sha256(output), "reconciled": True}
        summaries.append(summary)
        print(json.dumps(summary), flush=True)
    write_json(Path("reports/research-006-summary.json"), {"scenarios": summaries, "demo_execution_ready": False,
               "status": "completed_provisional_development_study", "freeze_sha256": sha256(Path("reports/research-006-freeze.json"))})


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("check", "freeze", "run"))
    args = parser.parse_args()
    {"check": check, "freeze": freeze_all, "run": run}[args.action]()
