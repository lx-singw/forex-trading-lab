"""Fixed invented calendar/fault acceptance. No market, account or order input."""
import argparse
from copy import deepcopy
from dataclasses import replace
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path

from forex_demo_lab import elliott_session_comparison_149 as c
from forex_demo_lab.elliott_full.contracts import Quote, D, digest

ROOT = Path(__file__).resolve().parents[1]
CASES = {"ew3_long": ("EW3", 1, "target"), "ew5_short": ("EW5", -1, "gap")}
FAULTS = ("baseline", "wide_retry", "stale_retry", "raw_closed_retry", "repeated_source_retry",
          "expired", "missing_bars_gap", "closure_gap", "duplicate_conflict", "invalid_batch")


def sources():
    files = (Path(__file__), ROOT / "scripts/elliott-session-comparison-149.py",
             ROOT / "scripts/elliott-full-shared-entry.py", ROOT / "tests/test_elliott_full_policy.py")
    return {"runtime": c.source_bindings(), "generators": {
        p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}}


def fixture(case):
    if case not in CASES:
        raise ValueError("fixed_invented_case_required")
    spec = importlib.util.spec_from_file_location("fixture149_for152", ROOT / "scripts/elliott-session-comparison-149.py")
    generator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(generator)
    kind, side, outcome = CASES[case]
    result = generator.fixture("wave", setup=kind, side=side, outcome=outcome)
    segments = result["calendar"]["segments"]
    if any(row["kind"] != "session" for row in segments[:3]):
        raise ValueError("expected_contiguous_invented_prefix")
    cursor = segments[0]["start"]
    replacement = []
    for i, hours in enumerate((12, 12, 23, 25)):
        end = cursor + hours * c.observations.HOUR
        replacement.append({"kind": "session", "label": "session_variable152_" + str(i),
                            "start": cursor, "end": end,
                            "h1": list(range(cursor, end, c.observations.HOUR)) + [end],
                            "h4": list(range(cursor, end, 4*c.observations.HOUR)) + [end],
                            "partial": hours == 12})
        cursor = end
    if cursor != segments[2]["end"]:
        raise ValueError("invented_prefix_duration")
    result["calendar"]["segments"] = replacement + segments[3:]
    result["case"] = "variable152_" + case
    calendar = c.observations.Calendar.from_record(result["calendar"])
    calendar_sha = calendar.sha256
    for row in result["hours"]:
        row["lineage"] = c.hour_lineage(result["case"], calendar_sha, row)
    return c.validate(result)


def prefix(value, profile):
    calendar, part, hours, quotes, bars, events, warm = c.scope(value, "development")
    replay = c.paper.PaperReplay(calendar, profile)
    for event in events:
        if event["kind"] == "quote":
            break
        replay.step(event)
    if replay.pending is None:
        raise AssertionError("automatic pending setup missing")
    return replay, quotes


def packed(path, value):
    with gzip.open(path, "xt", encoding="utf-8") as output:
        json.dump(value, output, separators=(",", ":"))


def resume(checkpoint, continuation, output):
    with gzip.open(checkpoint, "rt", encoding="utf-8") as file:
        replay = c.paper.PaperReplay.restore(json.load(file))
    events = json.loads(Path(continuation).read_text())["events"]
    for event in events:
        replay.step(event)
    result = {"whole_state_sha256": digest(replay.state()), "ledger": replay.ledger.state(),
              "market_cells_run": 0, "orders_available": False}
    c.write(output, result)
    return result


def scenario(original, quotes, fault, *, checkpoint_path=None):
    if fault not in FAULTS:
        raise ValueError("fixed_fault_required")
    replay = original.fork()
    first, exit_quote = quotes[:2]
    side = original.pending.side
    trace = []
    saved = False
    continuation = []
    def step(kind, value, reject=False):
        event = {"kind": kind, "value": value.record() if isinstance(value, Quote) else value}
        before = replay.state() if reject else None
        if reject:
            try:
                replay.step(event)
            except ValueError:
                if replay.state() != before:
                    raise AssertionError("rejected event mutated automatic replay")
                trace.append({"kind": kind, "rejected": True, "whole_state_unchanged": True})
                return
            raise AssertionError("expected rejection")
        result = replay.step(event)
        trace.append({"kind": kind, "result": result, "time": replay.time})
        if saved:
            continuation.append(event)
        return result
    def save():
        nonlocal saved
        if checkpoint_path is not None:
            packed(checkpoint_path, replay.checkpoint())
            saved = True
    if fault in ("wide_retry", "repeated_source_retry", "duplicate_conflict", "expired"):
        bad = replace(first, ask=first.bid+D(".0003"))
        step("quote", bad)
        if fault == "wide_retry":
            save()
        if fault == "repeated_source_retry":
            step("quote", replace(bad, time=bad.time+1, sequence=1))
        if fault == "duplicate_conflict":
            step("clock", bad.time+1)
            step("quote", bad)
            step("quote", replace(bad, ask=bad.ask+D(".00001")), reject=True)
        if fault == "expired":
            when = original.pending.formed+60001
            step("clock", when)
            first = replace(first, time=when+1, source=when+1, sequence=1)
        else:
            offset = 2 if fault in ("repeated_source_retry", "duplicate_conflict") else 1
            first = replace(first, time=first.time+offset, source=first.source+offset,
                            sequence=2 if fault == "repeated_source_retry" else 1)
    elif fault == "stale_retry":
        step("quote", replace(first, source=first.time-2001))
        first = replace(first, time=first.time+1, source=first.source+1, sequence=1)
    elif fault == "raw_closed_retry":
        step("quote", replace(first, session_open=False))
        first = replace(first, time=first.time+1, source=first.source+1, sequence=1)
    elif fault == "invalid_batch":
        last = next(row for row in reversed(replay.events) if row["kind"] == "bars")
        h1 = next(row for row in last["value"] if row["timeframe"] == "H1")
        step("bars", [h1, h1], reject=True)
    entered = step("quote", first)
    position = None if replay.ledger.position is None else deepcopy(replay.ledger.state()["position"])
    if fault == "expired":
        step("finish", first)
    else:
        if entered != "entered":
            raise AssertionError("automatic fault retry did not enter: " + str(entered))
        if fault == "missing_bars_gap":
            future = next(w for w in replay.decisions.coverage.calendar.frame("H1")
                          if w.end+replay.decisions.coverage.calendar.delay > first.time)
            when = future.end+replay.decisions.coverage.calendar.delay
            step("clock", when)
            bid = first.bid-side*D(".02")
            exit_quote = Quote(when+1, when+1, first.sequence+1, bid, bid+D(".0001"))
        elif fault == "closure_gap":
            calendar = replay.decisions.coverage.calendar
            closure = next(row for row in calendar.record()["segments"]
                           if row["kind"] == "closure" and row["start"] > first.time)
            bid = first.bid-side*D(".02")
            closed = Quote(closure["start"]+1000, closure["start"]+1000, first.sequence+1, bid, bid+D(".0001"), True)
            step("quote", closed)
            step("finish", closed, reject=True)
            save()
            exit_quote = Quote(closure["end"]+1000, closure["end"]+1000, first.sequence+2, bid, bid+D(".0001"))
        else:
            exit_quote = replace(exit_quote, sequence=first.sequence+1)
        step("quote", exit_quote)
        step("finish", exit_quote)
    if replay.decisions.strategy.snapshots != original.decisions.strategy.snapshots:
        raise AssertionError("future fault rewrote published snapshots")
    result = {"fault": fault, "trace": trace, "ledger": replay.ledger.state(), "entry_position": position,
              "pending": c.paper.setup_record(replay.pending), "cancellations": replay.cancellations,
              "quote_gates": replay.quote_gates, "snapshot_history_unchanged": True,
              "final_coverage": replay.decisions.coverage.record(replay.decisions.strategy.bars, replay.time),
              "quotes": [e["value"] for e in replay.events[len(original.events):] if e["kind"] == "quote"],
              "market_cells_run": 0, "orders_available": False}
    if saved:
        result["whole_state_sha256"] = digest(replay.state())
        c.write(checkpoint_path.with_suffix(".continuation.json"), {"events": continuation})
    return result


def exercise(output, case, profile):
    if case not in CASES or profile not in c.PROFILES:
        raise ValueError("fixed_case_profile_required")
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    initial_sources = sources()
    c.write(output/"declaration.json", {"kind": "invented_fault152_pre_return_declaration", "case": case,
            "profile": profile, "faults": list(FAULTS), "sources": initial_sources,
            "scope": "independent_operational_software_branches_not_funded_study_partitions",
            "variable_sessions": "first72hours_only_12_12_23_25_then_original_schedule",
            "market_cells_run": 0, "orders_available": False})
    value = fixture(case)
    c.write(output/"input.json", value)
    replay, quotes = prefix(value, profile)
    kind, side, _ = CASES[case]
    if (replay.pending.kind, replay.pending.side) != (kind, side):
        raise AssertionError("wrong automatic setup")
    prefix_record = {"signal": c.paper.setup_record(replay.pending), "contexts": replay.decisions.strategy.contexts,
                     "bars": {f: len(bars) for f, bars in replay.decisions.strategy.bars.items()},
                     "coverage": replay.decisions.coverage.record(replay.decisions.strategy.bars, replay.time),
                     "snapshot_sha256": digest(replay.decisions.strategy.snapshots),
                     "input_sha256": c.file_hash(output/"input.json"), "calendar_sha256": replay.decisions.coverage.calendar.sha256}
    c.write(output/"automatic-prefix.json", prefix_record)
    results = []
    for fault in FAULTS:
        witness = (case, profile, fault) in (("ew5_short", "adverse", "wide_retry"), ("ew3_long", "base", "closure_gap"))
        result = scenario(replay, quotes, fault, checkpoint_path=output/(fault+".json.gz") if witness else None)
        results.append(result)
    if initial_sources != sources():
        raise ValueError("fault152_sources_changed")
    c.write(output/"cases.json", {"kind": "invented_automatic_fault152_results", "case": case, "profile": profile,
                                "prefix": prefix_record, "cases": results, "market_cells_run": 0, "orders_available": False})
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    create = commands.add_parser("fixture");create.add_argument("output");create.add_argument("--case", choices=tuple(CASES), required=True)
    run = commands.add_parser("exercise");run.add_argument("output");run.add_argument("--case", choices=tuple(CASES), required=True);run.add_argument("--profile", choices=c.PROFILES, default="base")
    restore = commands.add_parser("resume");restore.add_argument("checkpoint");restore.add_argument("continuation");restore.add_argument("output")
    args = parser.parse_args()
    if args.command == "fixture":
        c.write(args.output, fixture(args.case))
    elif args.command == "exercise":
        exercise(args.output, args.case, args.profile)
    else:
        resume(args.checkpoint, args.continuation, args.output)
    print(json.dumps({"status": "INVENTED_SOFTWARE_EVIDENCE_ONLY", "orders_available": False, "market_cells_run": 0}))


if __name__ == "__main__":
    main()
