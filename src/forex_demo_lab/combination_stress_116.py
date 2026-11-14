"""Frozen invented stress matrix and reconstructed-prefix restore. No execution API."""
from copy import deepcopy
import json
from pathlib import Path

from .model import Config
from .fill_audit_116 import audit
from .stress_fixture_116 import ACCEPTED, REJECTED, HOUR, START, definitions, fixture_bytes
from .strategy_combination_115 import (
    DEPENDENCIES as PREDECESSOR_DEPENDENCIES, RULES, Replay, freeze_fixture,
    load_fixture, scenarios, rule_definitions, inspect_capture, write_new,
)
from .shadow_engine_113 import ROOT, _canonical, _digest, _json, _read

DEPENDENCIES = (*PREDECESSOR_DEPENDENCIES,
                "src/forex_demo_lab/stress_fixture_116.py",
                "src/forex_demo_lab/fill_audit_116.py",
                "src/forex_demo_lab/combination_stress_116.py",
                "scripts/combination-stress-116.py", "tests/test_combination_stress_116.py",
                "docs/COMBINATION-STRESS-116-PROTOCOL.md")


def sources():
    return {n: _digest(_read(ROOT / n, 1024 * 1024)) for n in DEPENDENCIES}


def _manifest(directory):
    directory = Path(directory)
    if directory.is_symlink() or not directory.is_dir():
        raise ValueError("matrix_directory")
    inputs = {}
    for case in (*ACCEPTED, *REJECTED):
        raw = _read(directory / (case + ".json"))
        if raw != fixture_bytes(case):
            raise ValueError("fixed_transformation_changed")
        row = {"fixture": case + ".json", "sha256": _digest(raw),
               "expected": "accepted" if case in ACCEPTED else REJECTED[case]}
        if case in ACCEPTED:
            row.update(manifest=case + "-frozen.json",
                       manifest_sha256=_digest(_read(directory / (case + "-frozen.json"), 65536)))
        inputs[case] = row
    return {"schema": "stress116_frozen_matrix_v1", "kind": "invented_fixture_matrix",
            "definitions": definitions(), "inputs": inputs, "sources": sources(),
            "rules": list(RULES), "rule_definitions": rule_definitions(), "scenarios": scenarios(),
            "partitions": ["development", "validation"], "accepted_paths": 96,
            "rejected_inputs": 9, "checkpoint_faults": 576,
            "market_validation": False, "orders_available": False}


def create_matrix(directory):
    """Create all predetermined inputs and bind them before any evaluation."""
    directory = Path(directory)
    directory.mkdir(exist_ok=False)
    for case in (*ACCEPTED, *REJECTED):
        path = directory / (case + ".json")
        with path.open("xb") as handle:
            handle.write(fixture_bytes(case))
        if case in ACCEPTED:
            freeze_fixture(path, directory / (case + "-frozen.json"))
    manifest = _manifest(directory)
    write_new(directory / "matrix-frozen.json", manifest)
    return manifest


def bound_matrix(directory):
    raw = _read(Path(directory) / "matrix-frozen.json", 65536)
    value = _json(raw)
    if value != _manifest(directory):
        raise ValueError("frozen_matrix_input_code_or_definitions_changed")
    # Validate every accepted115 binding before starting any path.
    for case in ACCEPTED:
        Replay(Path(directory) / (case + ".json"), Path(directory) / (case + "-frozen.json"))
    return value, _digest(raw)


def restore_checked(fixture, manifest, checkpoint, scenario="base", partition="development", rule="UNANIMOUS"):
    """Reconstruct only the declared prefix before accepting any restored state."""
    restored = Replay.restore(fixture, manifest, checkpoint, scenario, partition, rule)
    # The retained simulator uses json.loads internally. Reject duplicate fields
    # in its original envelope before accepting the normalized restored state.
    _json(_json(checkpoint)["payload"]["simulator"])
    reference = Replay(fixture, manifest, scenario, partition, rule)
    for event in reference.events[:restored.next_sequence]:
        reference.step(event)
    if restored.sim.finished:
        reference.finish()
    actual = _json(restored.sim.checkpoint())["payload"]
    expected = _json(reference.sim.checkpoint())["payload"]
    if (_canonical(actual) != _canonical(expected) or restored.repeats != reference.repeats
            or restored.next_sequence != reference.next_sequence):
        raise ValueError("reconstructed_checkpoint_state_mismatch")
    return restored


def fault_checkpoint(checkpoint, fault):
    """Predetermined corruptions for this offline test; never edit an input file."""
    value = _json(checkpoint)
    payload = value["payload"]
    if fault == "checksum":
        value["sha256"] = "0" * 64
        return json.dumps(value)
    if fault == "boolean_cursor":
        payload["next_sequence"] = True
    elif fault in ("rehashed_balance", "metric_version", "rehashed_protection"):
        inner = _json(payload["simulator"])
        state = inner["payload"]["state"]
        if fault == "rehashed_balance":
            state["balance"] += 1.0
        elif fault == "metric_version":
            state["execution_metric_version"] = "obsolete"
        elif state["position"] is not None:
            state["position"]["stop"] += .0001
        else:
            state["paused"] = not state["paused"]
        inner["sha256"] = _digest(json.dumps(inner["payload"], sort_keys=True, allow_nan=False).encode())
        payload["simulator"] = json.dumps(inner)
    elif fault != "cross_rule":
        raise ValueError("checkpoint_fault")
    value["sha256"] = _digest(_canonical(payload))
    return json.dumps(value)


def _compact(report):
    result = deepcopy(report)
    decisions = result.pop("decisions")
    result.update(decision_count=len(decisions), decisions_sha256=_digest(_canonical(decisions)))
    return result


def evaluate_matrix(directory, output):
    """Retain all results and verification failures; no selective reporting."""
    directory, output = Path(directory), Path(output)
    if output.exists() or output.is_symlink():
        raise ValueError("existing_artifact")
    manifest, digest = bound_matrix(directory)
    rejected, results, faults, failures = [], [], [], []
    for case, expected in REJECTED.items():
        try:
            load_fixture(directory / (case + ".json"))
            reason, passed = "unexpectedly_accepted", False
        except ValueError as exc:
            reason, passed = str(exc), str(exc) == expected
        rejected.append({"case": case, "status": "input_rejected" if reason != "unexpectedly_accepted" else reason,
                         "expected_reason": expected, "reason": reason, "passed": passed, "metrics": None})
        if not passed:
            failures.append({"case": case, "check": "input_rejection"})
    for case in ACCEPTED:
        fixture, frozen = directory / (case + ".json"), directory / (case + "-frozen.json")
        for scenario in ("base", "adverse"):
            for partition in ("development", "validation"):
                for rule in RULES:
                    identity = dict(case=case, scenario=scenario, partition=partition, rule=rule)
                    try:
                        run = Replay(fixture, frozen, scenario, partition, rule)
                        threshold = START + definitions()["restart_hours"][partition] * HOUR
                        for event in run.events:
                            run.step(event)
                            if event["receipt_msc"] >= threshold:
                                break
                        checkpoint = run.checkpoint()
                        state = {"cursor": run.next_sequence, "position_active": run.sim.position is not None,
                                 "daily_pause_active": run.sim.paused, "receipt_msc": run.events[run.next_sequence - 1]["receipt_msc"]}
                        restored = restore_checked(fixture, frozen, checkpoint, scenario, partition, rule)
                        idempotent = restored.step(restored.events[restored.next_sequence - 1]) is False
                        for fault in definitions()["checkpoint_faults"]:
                            target_rule = RULES[(RULES.index(rule) + 1) % len(RULES)] if fault == "cross_rule" else rule
                            try:
                                restore_checked(fixture, frozen, fault_checkpoint(checkpoint, fault),
                                                scenario, partition, target_rule)
                                reason, passed = "unexpectedly_accepted", False
                            except ValueError as exc:
                                reason, passed = str(exc), True
                            faults.append({**identity, "fault": fault, "passed": passed, "reason": reason, "metrics": None})
                            if not passed:
                                failures.append({**identity, "check": fault})
                        full = run.run()
                        resumed = restored.run()
                        finished = restore_checked(fixture, frozen, run.checkpoint(), scenario, partition, rule)
                        restart_equal = _canonical(full) == _canonical(resumed) == _canonical(finished.report())
                        finished_idempotent = finished.step(finished.events[-1]) is False
                        ledger_input = {**full, "evaluation_start_msc": run.start}
                        ledger = audit(ledger_input, run.events, run.sim.config,
                                       run.manifest["scenarios"][scenario]["spread_floor_pips"])
                        if ledger["final_paused"] != run.sim.paused:
                            raise ValueError("independent_audit_final_pause")
                        passed = restart_equal and idempotent and finished_idempotent
                        results.append({**_compact(full), "status": "accepted", "passed": passed,
                                        "restart_state": state, "restart_equal": restart_equal,
                                        "duplicate_idempotent": idempotent and finished_idempotent,
                                        "independent_audit": ledger})
                        if not passed:
                            failures.append({**identity, "check": "restart_equality"})
                    except (ValueError, TypeError, KeyError, IndexError, ArithmeticError) as exc:
                        results.append({**identity, "status": "verification_failed", "passed": False,
                                        "reason": str(exc), "metrics": None})
                        failures.append({**identity, "check": "path_verification", "reason": str(exc)})
    counts_complete = len(results) == 96 and len(rejected) == 9 and len(faults) == 576
    report = {"schema": "stress116_matrix_result_v1", "kind": "invented_software_check",
              "matrix_manifest_sha256": digest, "results": results, "rejected_inputs": rejected,
              "checkpoint_faults": faults, "failures": failures, "counts_complete": counts_complete,
              "verification_passed": counts_complete and not failures,
              "selected_strategy": None, "aggregate_portfolio_result": None, "combination_weights": None,
              "market_validation": False, "market_data_qualified": False,
              "paper_evaluation_available": False, "orders_available": False,
              "real_money_execution_available": False}
    write_new(output, report)
    return report
