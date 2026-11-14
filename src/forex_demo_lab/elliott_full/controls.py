"""Invented control orchestration around unchanged 118/120/121/124/125 engines.

There is deliberately no qualified-market input adapter or broker transport here.
Control accounts retain their original entry/exit clocks and economic rules.
"""
from copy import deepcopy
import hashlib
from pathlib import Path

from .. import daily_features_118 as daily
from .. import daily_bars_121 as bars
from .. import daily_fills_120 as fills
from .. import elliott_execution_125 as old_elliott
from .contracts import bindings, digest

CANDIDATES = ("EWPB_D124", "T12_D", "CASH")
PROFILES = ("base", "adverse")
VERSION = "EW_FULL_V1_INVENTED_CONTROLS"


def source_bindings():
    return {"current": bindings(), "frozen_controls": old_elliott.source_bindings()}


def _hash(path):
    return hashlib.sha256(daily._read(path)).hexdigest()


def freeze(path, output):
    """Declare both chronological partitions and every control cell before outcomes."""
    raw = daily._read(path)
    value = old_elliott.validate_fixture(daily._json(raw))
    result = {"version": VERSION, "kind": "invented_control_freeze",
              "input_sha256": hashlib.sha256(raw).hexdigest(), "sources": source_bindings(),
              "partitions": deepcopy(value["partitions"]), "candidates": list(CANDIDATES),
              "profiles": list(PROFILES), "initial_cash_usd": "10000",
              "orders_available": False, "market_data_qualified": False}
    daily.write_new(output, result)
    return result


def _load(path, manifest_path):
    raw, frozen = daily._read(path), daily._json(daily._read(manifest_path))
    daily._fields(frozen, {"version", "kind", "input_sha256", "sources", "partitions", "candidates",
                          "profiles", "initial_cash_usd", "orders_available", "market_data_qualified"}, "control_freeze_fields")
    value = old_elliott.validate_fixture(daily._json(raw))
    if (frozen["version"] != VERSION or frozen["kind"] != "invented_control_freeze"
            or frozen["input_sha256"] != hashlib.sha256(raw).hexdigest()
            or frozen["sources"] != source_bindings() or frozen["partitions"] != value["partitions"]
            or frozen["candidates"] != list(CANDIDATES) or frozen["profiles"] != list(PROFILES)
            or frozen["initial_cash_usd"] != "10000" or frozen["orders_available"] is not False
            or frozen["market_data_qualified"] is not False):
        raise ValueError("control_freeze_binding")
    return value


def prepare(path, manifest_path, partition, directory):
    """Derive all control features from one frozen raw-quote prefix, exclusively."""
    value = _load(path, manifest_path)
    matches = [p for p in value["partitions"] if p["name"] == partition]
    if len(matches) != 1:
        raise ValueError("control_partition")
    part = matches[0]
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=False)
    # The original125 compiler checks the exact endpoint and derives124 signals
    # from121 bars. No caller-supplied feature, signal or account state is admitted.
    old_elliott.prepare_partition(value, part, directory)
    aggregation = bars.Replay(directory/"prefix-input.json", directory/"prefix-frozen.json")
    aggregation.run()
    compiled = bars.compile_fills(aggregation)
    daily.write_new(directory/"control-fills-input.json", compiled)
    fills.freeze_fixture(directory/"control-fills-input.json", directory/"control-fills-frozen.json")
    record = {"version": VERSION, "kind": "invented_prepared_controls", "sources": source_bindings(),
              "input_sha256": _hash(path), "freeze_sha256": _hash(manifest_path), "partition": part,
              "files": {p.name: _hash(p) for p in sorted(directory.iterdir()) if p.is_file()},
              "orders_available": False, "market_data_qualified": False}
    daily.write_new(directory/"controls-prepared.json", record)
    return record


class ControlReplay:
    """Common reporting/checkpoint interface; economics stay in frozen engines."""
    def __init__(self, directory, candidate, profile="base"):
        if type(candidate) is not str or candidate not in CANDIDATES or type(profile) is not str or profile not in PROFILES:
            raise ValueError("control_candidate_or_profile")
        self.directory = Path(directory)
        if self.directory.is_symlink():
            raise ValueError("control_directory")
        path = self.directory/"controls-prepared.json"
        record = daily._json(daily._read(path))
        daily._fields(record, {"version", "kind", "sources", "input_sha256", "freeze_sha256", "partition",
                              "files", "orders_available", "market_data_qualified"}, "control_prepared_fields")
        if (record["version"] != VERSION or record["kind"] != "invented_prepared_controls"
                or record["sources"] != source_bindings() or record["orders_available"] is not False
                or record["market_data_qualified"] is not False or type(record["files"]) is not dict):
            raise ValueError("control_prepared_binding")
        required = {"prefix-input.json", "prefix-frozen.json", "aggregation.json", "wave-input.json",
                    "wave-frozen.json", "wave-report.json", "compiled-input.json", "compiled-frozen.json",
                    "control-fills-input.json", "control-fills-frozen.json"}
        if set(record["files"]) != required:
            raise ValueError("control_prepared_files")
        if any(_hash(self.directory/name) != expected for name, expected in record["files"].items()):
            raise ValueError("control_artifact_binding")
        self.candidate, self.profile = candidate, profile
        self.prepared = record
        self._binding = _hash(path)
        self._paths = (self.directory/"compiled-input.json", self.directory/"compiled-frozen.json") if candidate == "EWPB_D124" else (
            self.directory/"control-fills-input.json", self.directory/"control-fills-frozen.json")
        self._engine_type = old_elliott.Account if candidate == "EWPB_D124" else fills.Replay
        self._engine = self._engine_type(*self._paths, profile, candidate)

    @property
    def state(self):
        return self._engine.state

    @property
    def events(self):
        return deepcopy(self._engine._fixture["events"])

    def step(self, event=None):
        if event is None:
            cursor = self._engine.state["cursor"]
            if cursor == len(self._engine._fixture["events"]):
                return False
            event = self._engine._fixture["events"][cursor]
        return self._engine.step(event)

    def finish(self):
        return self._engine.finish()

    def run(self):
        while self.step():
            pass
        self.finish()
        return self.report()

    def report(self):
        original = self._engine.report()
        return {"kind": "invented_unchanged_control_report", "candidate": self.candidate,
                "profile": self.profile, "partition": deepcopy(self.prepared["partition"]),
                "prepared_sha256": self._binding, "summary": deepcopy(original["summary"]),
                "original_report": original, "economic_engine": "125" if self.candidate == "EWPB_D124" else "120",
                "status": "invented_descriptive_only", "market_data_qualified": False,
                "strategy_selected": False, "orders_available": False, "real_money_execution_available": False}

    def checkpoint(self):
        payload = {"version": VERSION, "sources": source_bindings(), "prepared_sha256": self._binding,
                   "candidate": self.candidate, "profile": self.profile, "original_checkpoint": self._engine.checkpoint()}
        return {"payload": payload, "digest": digest(payload)}

    @classmethod
    def restore(cls, directory, checkpoint):
        daily._fields(checkpoint, {"payload", "digest"}, "control_checkpoint_envelope")
        p = checkpoint["payload"]
        daily._fields(p, {"version", "sources", "prepared_sha256", "candidate", "profile", "original_checkpoint"}, "control_checkpoint_fields")
        if p["version"] != VERSION or p["sources"] != source_bindings() or digest(p) != checkpoint["digest"]:
            raise ValueError("control_checkpoint_binding")
        result = cls(directory, p["candidate"], p["profile"])
        if p["prepared_sha256"] != result._binding:
            raise ValueError("control_checkpoint_partition")
        result._engine = result._engine_type.restore(*result._paths, p["original_checkpoint"], result.profile, result.candidate)
        return result


def evaluate(path, manifest_path, output):
    """Retain all twelve declared invented controls; no market cell is admitted."""
    value = _load(path, manifest_path)
    root = Path(output)
    root.mkdir(parents=True, exist_ok=False)
    daily.write_new(root/"run-binding.json", {"input_sha256": _hash(path), "freeze_sha256": _hash(manifest_path),
                    "sources": source_bindings(), "orders_available": False, "market_data_qualified": False})
    cells = []
    for part in value["partitions"]:
        directory = root/part["name"]
        preparation_error = None
        try:
            prepare(path, manifest_path, part["name"], directory)
        except ValueError as exc:
            preparation_error = str(exc)
        for profile in PROFILES:
            for candidate in ("EW_FULL_V1",) + CANDIDATES:
                reason = "new_strategy_common_input_adapter_unavailable" if candidate == "EW_FULL_V1" else preparation_error
                report = None
                if reason is None:
                    try:
                        report = ControlReplay(directory, candidate, profile).run()
                    except ValueError as exc:
                        reason = str(exc)
                if report is not None:
                    daily.write_new(directory/f"{candidate}-{profile}.json", report)
                cells.append({"candidate": candidate, "profile": profile, "partition": part["name"],
                              "invented_status": "unavailable" if report is None else "invented_descriptive_only",
                              "reason": reason, "summary": None if report is None else report["summary"],
                              "market_status": "UNAVAILABLE", "market_returns": None})
    if source_bindings() != daily._json(daily._read(manifest_path))["sources"]:
        raise ValueError("control_sources_changed_during_run")
    result = {"kind": "invented_control_comparison_status", "cells": cells, "planned_control_cells": 12,
              "computed_control_cells": sum(c["invented_status"] == "invented_descriptive_only" for c in cells),
              "market_cells_run": 0, "capital_summed_as_portfolio": False, "strategy_selected": False,
              "orders_available": False, "real_money_execution_available": False,
              "limitations": ["Invented inputs only; no eligible market source or qualified runner",
                              "Original control clocks and stops retained; new ledger parity is not implied",
                              "EW_FULL_V1 common raw-quote adapter unavailable; do not rank strategies from this report"]}
    daily.write_new(root/"comparison-status.json", result)
    return result
