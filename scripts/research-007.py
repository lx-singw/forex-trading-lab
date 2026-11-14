"""October-only interval mapping with explicit quiet-period rejection."""
import argparse
import importlib.util
import json
from pathlib import Path

spec = importlib.util.spec_from_file_location("research006", Path(__file__).with_name("research-006.py"))
old = importlib.util.module_from_spec(spec)
spec.loader.exec_module(old)
prior = old.prior
from forex_demo_lab.cli import write_json
from forex_demo_lab.histdata import archive_ticks, hourly
from forex_demo_lab.reconstruction import checked_capture
from forex_demo_lab.research_data import build
from forex_demo_lab.tick_audit import sha256

HOUR = 3600000
PROTOCOL = Path("docs/RESEARCH-007-PLAN.md")
EVIDENCE = Path("reports/research-007-clock.json")
QUALITY = Path("reports/research-quality-007.json")
DATASET = Path("data/research-007-october-interval")
SOURCE = Path("data/histdata-eurusd-202410-original")


def limits(source):
    if source not in ("histdata", "broker"):
        raise ValueError("Undeclared clock source")
    return (prior.epoch("20241026") + (0 if source == "histdata" else 6 * HOUR),
            prior.epoch("20241027") + (12 if source == "histdata" else 18) * HOUR)


def interval_ticks(ticks, source, require_sides=True, cutoff=None):
    """Inputs: fixed-EST parser timestamps or raw broker labels; never infer DST."""
    quiet_start, quiet_end = limits(source)
    cutoff = prior.epoch("20241027") if cutoff is None else cutoff
    if not quiet_start <= cutoff < quiet_end:
        raise ValueError("Cutoff must lie inside declared quote-free interval")
    first, last = prior.epoch("20241001"), prior.epoch("20241101")
    previous_label = previous_utc = None
    before = after = 0
    for sequence, tick in enumerate(ticks):
        label = tick["time_msc"] - (5 * HOUR if source == "histdata" else 0)
        if (tick["sequence"] != sequence or not first <= label < last
                or previous_label is not None and label < previous_label):
            raise ValueError("Sequence, order or month mismatch")
        if quiet_start <= label < quiet_end:
            raise ValueError("Quote inside declared quiet interval: mapping unsupported")
        early = label < cutoff
        shift = (4 if early else 5) if source == "histdata" else (-3 if early else -2)
        utc = label + shift * HOUR
        if previous_utc is not None and utc < previous_utc:
            raise ValueError("Nonmonotonic mapped timestamp")
        before += early
        after += not early
        previous_label, previous_utc = label, utc
        yield {"sequence": sequence, "time_msc": utc, "bid": tick["bid"], "ask": tick["ask"]}
    if require_sides and (not before or not after):
        raise ValueError("Missing quotes on one side of boundary")


def observe(ticks, source, minutes, stats, boundary):
    quiet_start, quiet_end = limits(source)
    for tick in ticks:
        label = tick["time_msc"] - (5 * HOUR if source == "histdata" else 0)
        if label < quiet_start:
            boundary["last_before_raw_ms"] = label
        elif label >= quiet_end and boundary.get("first_after_raw_ms") is None:
            boundary["first_after_raw_ms"] = label
        minute = label // 60000
        if minute in minutes:
            g = stats.setdefault(minute, {"ticks": 0, "low": tick["bid"], "high": tick["bid"]})
            g["ticks"] += 1
            g["low"], g["high"] = min(g["low"], tick["bid"]), max(g["high"], tick["bid"])
        yield tick


def pair_result(stats, event_minute, control_minute):
    def get(minute):
        g = dict(stats.get(minute, {"ticks": 0, "low": 0, "high": 0}))
        g["range_pips"] = (g["high"] - g["low"]) / .0001
        return g
    event, control = get(event_minute), get(control_minute)
    return {"event": event, "control": control, "passed": old.event_passes(control, event)}


def passed(events, comparisons, boundary):
    return (set(events) == {"20241024", "20241029"}
            and all(e["histdata"]["passed"] and e["broker"]["passed"] for e in events.values())
            and set(comparisons) == {"20241024", "20241025", "20241028"}
            and all(c["passed"] for c in comparisons.values()) and boundary is True)


def check():
    original = prior.load(Path("reports/research-006-clock.json"))
    if sha256(SOURCE / "original.zip") != original["source_archive_sha256"]:
        raise ValueError("Original source archive changed")
    specs = {"20241024": (510, 450, 930, 870), "20241029": (540, 600, 960, 1020)}
    minutes = {prior.epoch(d) // 60000 + m for d, v in specs.items() for m in v[:2]}
    stats, boundary_hist = {}, {}
    mapped = interval_ticks(observe(archive_ticks(SOURCE), "histdata", minutes, stats, boundary_hist), "histdata")
    bars = list(hourly(mapped))
    reference = {b["hour"]: b["bid_close"] for b in bars}
    events, captures = {}, {}
    for day, (hm, hc, bm, bc) in specs.items():
        folder = Path("data/research-005-mt5-october29" if day == "20241029" else "data/research-007-mt5-october24")
        ticks = old.expected_capture(folder, day)
        start = prior.epoch(day) // 60000
        groups = old.activity(ticks, [start + bm, start + bc])
        events[day] = {"histdata": pair_result(stats, start + hm, start + hc),
                       "broker": {"event": groups[start + bm], "control": groups[start + bc],
                                  "passed": old.event_passes(groups[start + bc], groups[start + bm])}}
        captures[str(folder)] = sha256(folder / "capture.json")
    comparisons = {}
    for day, offset in (("20241024", 3), ("20241025", 3), ("20241028", 2)):
        folder = Path(f"data/research-007-mt5-october{day[-2:]}")
        old.expected_capture(folder, day)
        comparisons[day] = prior.compare_window(reference, folder, offset)
        captures[str(folder)] = sha256(folder / "capture.json")
    weekend = []
    for suffix, start, end in (("a", prior.epoch("20241025") + 18 * HOUR, prior.epoch("20241027") + 18 * HOUR),
                               ("b", prior.epoch("20241027") + 18 * HOUR, prior.epoch("20241028") + 6 * HOUR)):
        folder = Path(f"data/research-007-mt5-weekend-{suffix}")
        _, ticks, lower, upper = checked_capture(folder)
        if (lower, upper) != (start, end):
            raise ValueError("Weekend request bounds changed")
        captures[str(folder)] = sha256(folder / "capture.json")
        for tick in ticks:
            weekend.append({**tick, "sequence": len(weekend)})
    boundary_broker = {}
    count = sum(1 for _ in interval_ticks(observe(weekend, "broker", set(), {}, boundary_broker), "broker"))
    eligible = passed(events, comparisons, True)
    report = {"protocol_sha256": sha256(PROTOCOL), "source_archive_sha256": sha256(SOURCE / "original.zip"),
              "source_metadata_sha256": sha256(SOURCE / "download.json"), "capture_hashes": captures,
              "events": events, "price_comparisons": comparisons, "boundary_histdata": boundary_hist,
              "boundary_broker": boundary_broker, "weekend_broker_ticks": count,
              "quiet_intervals_verified": True, "passed": eligible, "provider_certified": False,
              "scope": "Observed October intervals only; exact transition instant unobservable"}
    write_json(EVIDENCE, report)
    if not eligible:
        write_json(QUALITY, {"protocol_sha256": sha256(PROTOCOL), "evidence_sha256": sha256(EVIDENCE),
                            "datasets": [], "performance_evaluation_ready": False, "demo_execution_ready": False})
    print(json.dumps(report), flush=True)


def build_dataset():
    evidence = prior.load(EVIDENCE)
    if evidence["protocol_sha256"] != sha256(PROTOCOL) or evidence["passed"] is not True:
        raise ValueError("Interval evidence blocks dataset construction")
    if (evidence["source_archive_sha256"] != sha256(SOURCE / "original.zip")
            or evidence["source_metadata_sha256"] != sha256(SOURCE / "download.json")):
        raise ValueError("Source changed")
    for folder, digest in evidence["capture_hashes"].items():
        if sha256(Path(folder) / "capture.json") != digest:
            raise ValueError("Capture evidence changed")
    p = build(interval_ticks(archive_ticks(SOURCE), "histdata"), DATASET,
              {"kind": "normalized_histdata_ticks", "scenario": "october-interval", "protocol_sha256": sha256(PROTOCOL),
               "source_archive_sha256": evidence["source_archive_sha256"], "clock_evidence_sha256": sha256(EVIDENCE),
               "clock": "October source-label intervals: +4h before Oct 27 00:00, +5h at/after; cutoff in verified empty interval",
               "quiet_interval_raw_ms": limits("histdata"), "representative_cutoff_raw_ms": prior.epoch("20241027"),
               "exact_clock_transition_certified": False})
    failures = prior.coverage_failures(p, prior.epoch("20241001") + 4 * HOUR, prior.epoch("20241101") + 5 * HOUR)
    old_p = prior.load(Path("data/research-005-october-fixed-est/provenance.json"))
    if p["ticks"] != old_p["ticks"]:
        failures.append("quote_count_changed")
    write_json(QUALITY, {"protocol_sha256": sha256(PROTOCOL), "evidence_sha256": sha256(EVIDENCE),
                        "datasets": [{"scenario": "october-interval", "provenance_sha256": sha256(DATASET / "provenance.json"),
                                      "status": "ready_for_development_research" if not failures else "blocked_data_quality"}],
                        "failures": failures, "performance_evaluation_ready": not failures, "demo_execution_ready": False})
    print(json.dumps({"ticks": p["ticks"], "observed_hours": p["observed_hours"], "failures": failures}), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("check", "build"))
    args = parser.parse_args()
    {"check": check, "build": build_dataset}[args.action]()
