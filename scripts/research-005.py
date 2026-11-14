"""Predeclared development study; data gates never authorize broker execution."""
import argparse
import csv
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import sys
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from forex_demo_lab.cli import code_digest, write_json
from forex_demo_lab.histdata import archive_ticks, hourly
from forex_demo_lab.reconstruction import checked_capture
from forex_demo_lab.research_data import build
from forex_demo_lab.tick_audit import sha256
from forex_demo_lab.tick_workflow import freeze, evaluate

PROTOCOL = Path("docs/RESEARCH-005-PLAN.md")
QUALITY = Path("reports/research-quality-005.json")
MONTHS = {"april": ("202404", "20240410", "20240501"),
          "october": ("202410", "20241010", "20241101")}
WINDOWS = {"april": (("april09", 3),), "october": (("october09", 3), ("october29", 2))}


def load(path):
    return json.loads(path.read_text())


def epoch(label):
    return int(datetime.strptime(label, "%Y%m%d").replace(tzinfo=timezone.utc).timestamp() * 1000)


def event_screen(source, day):
    lower = epoch(day)
    groups = {minute: {"ticks": 0, "low": None, "high": None} for minute in (450, 510)}
    for tick in archive_ticks(source):
        relative = tick["time_msc"] - 5 * 3600000 - lower
        minute = relative // 60000
        if minute not in groups:
            continue
        g = groups[minute]
        g["ticks"] += 1
        g["low"] = tick["bid"] if g["low"] is None else min(g["low"], tick["bid"])
        g["high"] = tick["bid"] if g["high"] is None else max(g["high"], tick["bid"])
    for g in groups.values():
        g["range_pips"] = (g["high"] - g["low"]) / .0001 if g["ticks"] else 0
    a, b = groups[450], groups[510]
    return {"date": day, "minutes": {"0730": a, "0830": b},
            "passed": a["ticks"] > 0 and a["range_pips"] > 0
            and b["range_pips"] >= 3 * a["range_pips"] and b["ticks"] >= 2 * a["ticks"]}


def coverage_failures(metadata, lower, upper):
    failures = []
    if metadata["observed_hours"] < 500:
        failures.append("fewer_than_500_observed_hours")
    if not lower <= metadata["first_ms"] <= lower + 6 * 3600000:
        failures.append("start_boundary_coverage")
    if not upper - 6 * 3600000 <= metadata["last_ms"] < upper:
        failures.append("end_boundary_coverage")
    if any(g["classification"] != "weekend_pattern_not_certified" for g in metadata["gaps_over_one_hour"]):
        failures.append("unresolved_gap_over_one_hour")
    return failures


def compare_window(reference, capture, offset):
    metadata, ticks, lower, upper = checked_capture(capture)
    shift = offset * 3600000
    bars = list(hourly({**t, "time_msc": t["time_msc"] - shift} for t in ticks))
    expected = set(range((lower - shift) // 3600000, (upper - shift) // 3600000))
    broker = {b["hour"]: b["bid_close"] for b in bars}
    missing = sorted(expected - (reference.keys() & broker.keys()))
    errors = [{"hour": h, "difference_pips": abs(reference[h] - broker[h]) / .0001}
              for h in sorted(expected & reference.keys() & broker.keys())]
    within = sum(e["difference_pips"] <= 1 + 1e-9 for e in errors) / len(errors) if errors else 0
    maximum = max((e["difference_pips"] for e in errors), default=None)
    return {"capture_sha256": sha256(capture / "capture.json"), "offset_hours": offset,
            "expected_hours": len(expected), "missing_hours": missing, "differences": errors,
            "within_one_pip_fraction": within, "maximum_difference_pips": maximum,
            "passed": len(expected) == 6 and not missing and within >= .95 and maximum is not None and maximum <= 5}


def build_datasets():
    for month, (label, day, end) in MONTHS.items():
        source = Path(f"data/histdata-eurusd-{label}-original")
        evidence = {"protocol_sha256": sha256(PROTOCOL), "archive_sha256": sha256(source / "original.zip"),
                    "event": event_screen(source, day)}
        write_json(Path(f"reports/research-005-{month}-clock.json"), evidence)
        for clock, shift in (("new-york", -3600000), ("fixed-est", 0)):
            ticks = ({**t, "time_msc": t["time_msc"] + shift} for t in archive_ticks(source))
            result = build(ticks, Path(f"data/research-005-{month}-{clock}"),
                           {"kind": "normalized_histdata_ticks", "scenario": f"{month}-{clock}",
                            "source_archive_sha256": evidence["archive_sha256"],
                            "source_metadata_sha256": sha256(source / "download.json"),
                            "protocol_sha256": sha256(PROTOCOL), "clock": clock,
                            "clock_evidence_sha256": sha256(Path(f"reports/research-005-{month}-clock.json"))})
            print(f"Built {month}/{clock}: {result['ticks']} ticks, {result['observed_hours']} hours", flush=True)


def review():
    datasets, months = [], {}
    for month, (label, day, end) in MONTHS.items():
        evidence = load(Path(f"reports/research-005-{month}-clock.json"))
        if evidence["protocol_sha256"] != sha256(PROTOCOL):
            raise ValueError("Protocol changed")
        with Path(f"data/research-005-{month}-new-york/hourly-diagnostic.csv").open() as stream:
            reference = {int(r["hour"]): float(r["bid_close"]) for r in csv.DictReader(stream)}
        windows = [compare_window(reference, Path(f"data/research-005-mt5-{name}"), offset)
                   for name, offset in WINDOWS[month]]
        common = []
        if not evidence["event"]["passed"]:
            common.append("event_clock_screen_failed")
        if not all(w["passed"] for w in windows):
            common.append("independent_price_window_failed")
        month_rows = []
        for clock, hours in (("new-york", 4), ("fixed-est", 5)):
            folder = Path(f"data/research-005-{month}-{clock}")
            p = load(folder / "provenance.json")
            if (sha256(folder / "ticks.csv.gz") != p["data_sha256"]
                    or sha256(folder / "hourly-diagnostic.csv") != p["hourly_sha256"]
                    or p["source_archive_sha256"] != evidence["archive_sha256"]
                    or sha256(Path(f"data/histdata-eurusd-{label}-original/original.zip")) != evidence["archive_sha256"]
                    or sha256(Path(f"data/histdata-eurusd-{label}-original/download.json")) != p["source_metadata_sha256"]
                    or p["clock_evidence_sha256"] != sha256(Path(f"reports/research-005-{month}-clock.json"))
                    or p["protocol_sha256"] != sha256(PROTOCOL)):
                raise ValueError("Dataset/protocol integrity failure")
            failures = common + coverage_failures(p, epoch(label + "01") + hours * 3600000, epoch(end) + hours * 3600000)
            month_rows.append({"scenario": f"{month}-{clock}", "provenance_sha256": sha256(folder / "provenance.json"),
                               "ticks": p["ticks"], "observed_hours": p["observed_hours"],
                               "gaps": p["gaps_over_one_hour"], "failures": failures})
        passed = not any(d["failures"] for d in month_rows)
        for d in month_rows:
            d["status"] = "ready_for_development_research" if passed else "blocked_data_quality"
        datasets.extend(month_rows)
        months[month] = {"event": evidence["event"], "price_windows": windows, "passed": passed}
    write_json(QUALITY, {"protocol_sha256": sha256(PROTOCOL), "months": months, "datasets": datasets,
                        "performance_evaluation_ready": any(m["passed"] for m in months.values()),
                        "demo_execution_ready": False, "scope": "Bounded provisional development only"})
    print(json.dumps({m: v["passed"] for m, v in months.items()}), flush=True)


def freeze_all():
    quality = load(QUALITY)
    if quality["protocol_sha256"] != sha256(PROTOCOL):
        raise ValueError("Protocol changed")
    manifests = {}
    for d in quality["datasets"]:
        if d["status"] != "ready_for_development_research":
            continue
        for cost in ("base", "adverse"):
            scenario = f"{d['scenario']}-{cost}"
            config = Path("config/tick-pilot-003.json" if cost == "base" else "config/tick-pilot-003-adverse.json")
            manifest = Path(f"reports/research-005-{scenario}-manifest.json")
            freeze(Path(f"data/research-005-{d['scenario']}"), config, QUALITY, manifest)
            manifests[scenario] = sha256(manifest)
    if not manifests:
        raise ValueError("All declared months blocked; no performance evaluation")
    archive = Path("reports/research-005-source.zip")
    with zipfile.ZipFile(archive, "x", compression=zipfile.ZIP_DEFLATED) as z:
        for root in (Path("src"), Path("scripts"), Path("tests")):
            for path in sorted(root.rglob("*.py")):
                z.write(path, path.as_posix())
        for path in (PROTOCOL, Path("config/tick-pilot-003.json"), Path("config/tick-pilot-003-adverse.json")):
            z.write(path, path.as_posix())
    write_json(Path("reports/research-005-freeze.json"), {"manifests": manifests, "code_sha256": code_digest(),
               "protocol_sha256": sha256(PROTOCOL), "quality_sha256": sha256(QUALITY), "source_archive_sha256": sha256(archive)})
    print(f"Frozen {len(manifests)} scenarios", flush=True)


def run_all():
    frozen = load(Path("reports/research-005-freeze.json"))
    if (frozen["protocol_sha256"] != sha256(PROTOCOL) or frozen["code_sha256"] != code_digest()
            or frozen["quality_sha256"] != sha256(QUALITY)
            or frozen["source_archive_sha256"] != sha256(Path("reports/research-005-source.zip"))):
        raise ValueError("Frozen study changed")
    for scenario, digest in frozen["manifests"].items():
        if sha256(Path(f"reports/research-005-{scenario}-manifest.json")) != digest:
            raise ValueError("Frozen manifest changed")
    summaries = []
    for scenario in frozen["manifests"]:
        manifest = Path(f"reports/research-005-{scenario}-manifest.json")
        output = Path(f"reports/research-005-{scenario}.json")
        r = evaluate(Path("data/research-005-" + scenario.rsplit("-", 1)[0]), manifest, QUALITY, output)
        total = sum(t["net_pnl"] for t in r["trades"])
        initial = load(manifest)["config"]["initial_equity"]
        if not (math.isclose(total, r["metrics"]["net_pnl"], abs_tol=1e-8)
                and math.isclose(initial + total, r["hourly_equity"][-1]["equity"], abs_tol=1e-8)):
            raise ValueError("P&L reconciliation failed")
        summary = {"scenario": scenario, "report_sha256": sha256(output), "metrics": r["metrics"], "reconciled": True}
        summaries.append(summary)
        print(json.dumps(summary), flush=True)
    write_json(Path("reports/research-005-summary.json"), {"scenarios": summaries, "demo_execution_ready": False,
               "status": "completed_provisional_development_study", "freeze_sha256": sha256(Path("reports/research-005-freeze.json"))})


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("build", "review", "freeze", "run"))
    args = parser.parse_args()
    {"build": build_datasets, "review": review, "freeze": freeze_all, "run": run_all}[args.action]()
