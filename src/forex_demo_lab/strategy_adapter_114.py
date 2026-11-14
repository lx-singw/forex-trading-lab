"""Fixed offline comparisons on frozen invented quotes. No execution interface."""
from copy import deepcopy
from dataclasses import asdict
from datetime import datetime
import json
import re

from .model import Config
from .strategies import Decision
from .strategy_experiment_028 import decision
from .shadow_engine_113 import (
    DEPENDENCIES as PREDECESSOR_DEPENDENCIES, ROOT, MAX_BYTES, MAX_EVENTS,
    MIN_MS, MAX_MS, Replay as PredecessorReplay, _CostedTicks,
    _canonical, _digest, _event, _integer, _json, _read,
    inspect_capture, scenarios, write_new,
)

CANDIDATES = ("C00", "C05", "C06", "CASH")
WARMUP_HOURS = 201
DEPENDENCIES = (*PREDECESSOR_DEPENDENCIES,
                "src/forex_demo_lab/strategy_experiment_028.py",
                "src/forex_demo_lab/strategy_adapter_114.py",
                "src/forex_demo_lab/strategy_fixture_114.py",
                "scripts/strategy-adapter-114.py", "tests/test_strategy_adapter_114.py",
                "docs/STRATEGY-ADAPTER-114-PROTOCOL.md")


def load_fixture(path):
    raw = _read(path)
    value = _json(raw)
    fields = {"format", "kind", "clock", "symbol", "case", "development_start_msc",
              "validation_start_msc", "events"}
    if (type(value) is not dict or set(value) != fields
            or value["format"] != "FXDL_STRATEGY114_V1"
            or value["kind"] != "invented_fixture" or value["clock"] != "invented_utc_milliseconds"
            or value["symbol"] != "EURUSD" or type(value["case"]) is not str
            or not re.fullmatch(r"[a-z][a-z0-9_]{0,63}", value["case"])):
        raise ValueError("invented114_fixture_required")
    if type(value["events"]) is not list or not 2 <= len(value["events"]) <= MAX_EVENTS:
        raise ValueError("event_count")
    events = []
    for event in value["events"]:
        events.append(_event(event, events[-1] if events else None))
    start = _integer(value["development_start_msc"], MIN_MS, MAX_MS)
    split = _integer(value["validation_start_msc"], MIN_MS, MAX_MS)
    if (start % 3600000 or split % 3600000 or events[0]["receipt_msc"] % 3600000
            or not events[0]["receipt_msc"] <= start < split <= events[-1]["receipt_msc"]):
        raise ValueError("partition_boundaries")
    for boundary in (start, split):
        if len({e["receipt_msc"] // 3600000 for e in events if e["receipt_msc"] < boundary}) < WARMUP_HOURS:
            raise ValueError("common_warmup_missing")
    return {**value, "events": events}, _digest(raw)


def source_bindings():
    return {name: _digest(_read(ROOT / name, 1024 * 1024)) for name in DEPENDENCIES}


def _manifest(fixture, digest):
    if _json(_read(ROOT / "config/baseline.json", 65536)) != asdict(Config()):
        raise ValueError("frozen_baseline_changed")
    return {"schema": "strategy114_frozen_invented_v1", "kind": "invented_fixture",
            "fixture_sha256": digest, "case": fixture["case"], "events": len(fixture["events"]),
            "development_start_msc": fixture["development_start_msc"],
            "validation_start_msc": fixture["validation_start_msc"], "clock": fixture["clock"],
            "candidates": list(CANDIDATES), "common_warmup_hours": WARMUP_HOURS,
            "account_model": "independent_fresh_capital_single_position",
            "initial_equity_per_account": Config().initial_equity,
            "cash_interest": 0.0, "scenarios": scenarios(), "sources": source_bindings()}


def freeze_fixture(fixture_path, manifest_path):
    fixture, digest = load_fixture(fixture_path)
    manifest = _manifest(fixture, digest)
    write_new(manifest_path, manifest)
    return manifest


def _bound_fixture(fixture_path, manifest_path):
    fixture, digest = load_fixture(fixture_path)
    raw = _read(manifest_path, 65536)
    manifest = _json(raw)
    if manifest != _manifest(fixture, digest):
        raise ValueError("frozen_fixture_candidates_config_or_code_changed")
    return fixture, manifest, _digest(raw)


class _CandidateTicks(_CostedTicks):
    """Reuse 113 fills/risk/costs; change only history and fixed decision dispatch."""
    def __init__(self, config, candidate="C00"):
        if candidate not in CANDIDATES:
            raise ValueError("candidate")
        super().__init__(config)
        self.candidate = candidate
        self.adapter_version = "fixed_strategy_adapter_114_v1"
        self.pending_entry_sequence = None
        self.fill_lineage = []

    def _history_limit(self):
        return WARMUP_HOURS

    def _decision(self):
        hour = self.current["hour"] * 3600000
        if len(self.history) < WARMUP_HOURS or hour < self.evaluation_start_msc:
            return 0, 0.0
        value = (Decision(0, 0.0, "cash_reference", {}) if self.candidate == "CASH"
                 else decision(self.candidate, self.history, self.config))
        self.decisions.append({"hour_msc": hour, "history_size": len(self.history),
                               "last_closed_hour": self.history[-1].time.isoformat(), **asdict(value)})
        return value.side, value.stop_distance

    def _open(self, bar, side, distance):
        if self.candidate == "CASH":
            return
        had_position = self.position is not None
        super()._open(bar, side, distance)
        if not had_position and self.position is not None:
            self.pending_entry_sequence = self._quote["sequence"]

    def _close(self, bar, exit_price, reason):
        entry = self.pending_entry_sequence
        if entry is None or self._quote is None:
            raise ValueError("fill_lineage_state")
        super()._close(bar, exit_price, reason)
        self.fill_lineage.append({"trade_index": len(self.trades) - 1,
                                  "entry_sequence": entry, "exit_sequence": self._quote["sequence"]})
        self.pending_entry_sequence = None

    def metrics(self):
        result = super().metrics()
        evaluated = sum(int(datetime.fromisoformat(p["time"]).timestamp() * 1000)
                        >= self.evaluation_start_msc for p in self.curve)
        result.update(evaluation_hours=evaluated, warmup_hours=len(self.curve) - evaluated,
                      bar_exposure=self.exposed_bars / evaluated if evaluated else 0)
        return result

    @classmethod
    def restore(cls, value, config, *, candidate, evaluation_start_msc):
        result = super().restore(value, config)
        if (result.adapter_version != "fixed_strategy_adapter_114_v1"
                or result.candidate != candidate or result.evaluation_start_msc != evaluation_start_msc):
            raise ValueError("checkpoint_candidate_or_boundary")
        return result


class Replay(PredecessorReplay):
    """Reuse strict event replay and cost reporting, with a separate 114 binding."""
    def __init__(self, fixture_path, manifest_path, scenario="base", partition="development", candidate="C00"):
        fixture, manifest, binding = _bound_fixture(fixture_path, manifest_path)
        if scenario not in ("base", "adverse") or partition not in ("development", "validation"):
            raise ValueError("scenario_or_partition")
        if candidate not in CANDIDATES:
            raise ValueError("candidate")
        self._fixture, self._manifest, self.binding = fixture, manifest, binding
        self.scenario, self.partition, self.candidate = scenario, partition, candidate
        self.start = fixture[partition + "_start_msc"]
        self._events = [dict(e) for e in fixture["events"] if partition == "validation"
                       or e["receipt_msc"] < fixture["validation_start_msc"]]
        self.next_sequence, self.repeats = 0, 0
        self.sim = _CandidateTicks(Config(**manifest["scenarios"][scenario]["config"]), candidate)
        self.sim.evaluation_start_msc = self.start

    def checkpoint(self):
        payload = {"schema": "strategy114_checkpoint_v1", "manifest_sha256": self.binding,
                   "fixture_sha256": self._manifest["fixture_sha256"], "candidate": self.candidate,
                   "scenario": self.scenario, "partition": self.partition,
                   "next_sequence": self.next_sequence, "repeats": self.repeats,
                   "simulator": self.sim.checkpoint()}
        return json.dumps({"payload": payload, "sha256": _digest(_canonical(payload))}, sort_keys=True)

    @classmethod
    def restore(cls, fixture_path, manifest_path, checkpoint, scenario="base", partition="development", candidate="C00"):
        if type(checkpoint) is not str or len(checkpoint.encode()) > MAX_BYTES:
            raise ValueError("checkpoint_size")
        result = cls(fixture_path, manifest_path, scenario, partition, candidate)
        value = _json(checkpoint)
        if type(value) is not dict or set(value) != {"payload", "sha256"}:
            raise ValueError("checkpoint_envelope")
        p = value["payload"]
        fields = {"schema", "manifest_sha256", "fixture_sha256", "candidate", "scenario",
                  "partition", "next_sequence", "repeats", "simulator"}
        if (type(p) is not dict or set(p) != fields or value["sha256"] != _digest(_canonical(p))
                or p["schema"] != "strategy114_checkpoint_v1" or p["manifest_sha256"] != result.binding
                or p["fixture_sha256"] != result._manifest["fixture_sha256"]
                or p["candidate"] != candidate or p["scenario"] != scenario or p["partition"] != partition):
            raise ValueError("checkpoint_binding")
        cursor = _integer(p["next_sequence"], 0, len(result._events))
        repeats = _integer(p["repeats"], 0, max(0, cursor - 1))
        try:
            sim = _CandidateTicks.restore(p["simulator"], result.sim.config,
                                          candidate=candidate, evaluation_start_msc=result.start)
        except (KeyError, TypeError, OverflowError, AttributeError, IndexError) as exc:
            raise ValueError("checkpoint_simulator") from exc
        expected = result._tick(result._events[cursor - 1]) if cursor else None
        expected_repeats = sum(a["source_msc"] == b["source_msc"]
                               for a, b in zip(result._events[:cursor], result._events[1:cursor]))
        if (type(sim.cost_audit) is not list or type(sim.trades) is not list
                or type(sim.decisions) is not list or type(sim.fill_lineage) is not list
                or type(sim.evaluation_start_msc) is not int):
            raise ValueError("checkpoint_state_types")
        if (_canonical(sim.last_tick) != _canonical(expected) or _canonical(sim._quote) != _canonical(expected)
                or repeats != expected_repeats or type(sim.finished) is not bool
                or (sim.finished and cursor != len(result._events))
                or len(sim.cost_audit) != len(sim.trades) or len(sim.fill_lineage) != len(sim.trades)
                or (sim.position is None) != (sim._entry_audit is None)
                or (sim.position is None) != (sim.pending_entry_sequence is None)):
            raise ValueError("checkpoint_cursor_or_state")
        if sim.pending_entry_sequence is not None:
            _integer(sim.pending_entry_sequence, 0, cursor - 1)
        for i, row in enumerate(sim.fill_lineage):
            if (type(row) is not dict or set(row) != {"trade_index", "entry_sequence", "exit_sequence"}
                    or type(row["trade_index"]) is not int or row["trade_index"] != i):
                raise ValueError("checkpoint_fill_lineage")
            entry = _integer(row["entry_sequence"], 0, cursor - 1)
            _integer(row["exit_sequence"], entry, cursor - 1)
        if candidate == "CASH" and (sim.position is not None or sim.trades or sim.cost_audit):
            raise ValueError("cash_position_state")
        result.next_sequence, result.repeats, result.sim = cursor, repeats, sim
        return result

    def report(self):
        result = deepcopy(super().report())
        result.update(schema="strategy114_invented_result_v1", candidate=self.candidate,
                      common_warmup_hours=WARMUP_HOURS,
                      account_model="independent_fresh_capital_single_position",
                      initial_equity_per_account=self.sim.config.initial_equity,
                      fill_lineage=deepcopy(self.sim.fill_lineage))
        return result


def evaluate_fixture(fixture_path, manifest_path, output_path):
    results = [Replay(fixture_path, manifest_path, s, p, c).run()
               for s in ("base", "adverse") for p in ("development", "validation") for c in CANDIDATES]
    report = {"schema": "strategy114_demonstration_v1", "kind": "invented_software_check",
              "results": results, "candidates": list(CANDIDATES), "selected_strategy": None,
              "portfolio_result": None, "combination_weights": None,
              "market_validation": False, "market_data_qualified": False,
              "paper_evaluation_available": False, "orders_available": False,
              "real_money_execution_available": False}
    write_new(output_path, report)
    return report
