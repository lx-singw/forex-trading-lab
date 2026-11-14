"""Offline invented-quote integration; no market admission or execution interface."""
from dataclasses import asdict, replace
from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
import re

from .model import Config
from .execution_metrics import ExecutableEquityTickSimulator

ROOT = Path(__file__).resolve().parents[2]
MAX_BYTES = 8 * 1024 * 1024
MAX_EVENTS = 20_000
MIN_MS, MAX_MS = 946684800000, 4102444800000
DEPENDENCIES = (
    "src/forex_demo_lab/shadow_engine_113.py",
    "src/forex_demo_lab/shadow_fixture_113.py",
    "scripts/shadow-engine-113.py", "config/baseline.json",
    "src/forex_demo_lab/model.py", "src/forex_demo_lab/simulation.py",
    "src/forex_demo_lab/tick_simulation.py",
    "src/forex_demo_lab/execution_metrics.py",
    "src/forex_demo_lab/research_simulation.py", "src/forex_demo_lab/strategies.py",
)


def _digest(data):
    return hashlib.sha256(data).hexdigest()


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def _pairs(items):
    result = {}
    for key, value in items:
        if key in result:
            raise ValueError("duplicate_json_field")
        result[key] = value
    return result


def _json(data):
    def bad_constant(value):
        raise ValueError("nonfinite_json")
    try:
        return json.loads(data, object_pairs_hook=_pairs, parse_constant=bad_constant)
    except (UnicodeError, TypeError, RecursionError) as exc:
        raise ValueError("invalid_json") from exc


def _read(path, limit=MAX_BYTES):
    path = Path(path)
    if path.is_symlink() or not path.is_file():
        raise ValueError("invalid_input_file")
    with path.open("rb") as handle:
        data = handle.read(limit + 1)
    if len(data) > limit:
        raise ValueError("input_size")
    return data


def write_new(path, value):
    """Create one local JSON artifact without replacing an existing file."""
    data = json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n"
    with Path(path).open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(data)


def _integer(value, low, high):
    if type(value) is not int or not low <= value <= high:
        raise ValueError("integer_range")
    return value


def _event(event, previous=None, check_order=True):
    if type(event) is not dict or set(event) != {"sequence", "receipt_msc", "source_msc", "bid", "ask"}:
        raise ValueError("event_fields")
    seq = _integer(event["sequence"], 0, MAX_EVENTS - 1)
    receipt = _integer(event["receipt_msc"], MIN_MS, MAX_MS)
    source = _integer(event["source_msc"], MIN_MS, MAX_MS)
    if not 0 <= receipt - source <= 2000:
        raise ValueError("invented_quote_age")
    if any(type(event[s]) not in (int, float) for s in ("bid", "ask")):
        raise ValueError("price_type")
    try:
        bid, ask = float(event["bid"]), float(event["ask"])
    except OverflowError as exc:
        raise ValueError("price_range") from exc
    if not math.isfinite(bid) or not math.isfinite(ask) or not 0 < bid <= ask:
        raise ValueError("invalid_quote")
    result = {"sequence": seq, "receipt_msc": receipt, "source_msc": source, "bid": bid, "ask": ask}
    if not check_order:
        return result
    if previous is None:
        if seq != 0:
            raise ValueError("first_sequence")
    elif (seq != previous["sequence"] + 1 or receipt < previous["receipt_msc"]
          or source < previous["source_msc"]):
        raise ValueError("event_order")
    elif source == previous["source_msc"] and (bid, ask) != (previous["bid"], previous["ask"]):
        raise ValueError("same_source_time_changed")
    return result


def load_fixture(path):
    raw = _read(path)
    value = _json(raw)
    fields = {"format", "kind", "clock", "symbol", "case", "development_start_msc", "validation_start_msc", "events"}
    if (type(value) is not dict or set(value) != fields
            or value["format"] != "FXDL_SHADOW113_V1" or value["kind"] != "invented_fixture"
            or value["clock"] != "invented_utc_milliseconds" or value["symbol"] != "EURUSD"
            or type(value["case"]) is not str or not re.fullmatch(r"[a-z][a-z0-9_]{0,63}", value["case"])):
        raise ValueError("invented_fixture_required")
    events = value["events"]
    if type(events) is not list or not 2 <= len(events) <= MAX_EVENTS:
        raise ValueError("event_count")
    normalized = []
    for event in events:
        normalized.append(_event(event, normalized[-1] if normalized else None))
    start = _integer(value["development_start_msc"], MIN_MS, MAX_MS)
    split = _integer(value["validation_start_msc"], MIN_MS, MAX_MS)
    if (start % 3600000 or split % 3600000 or normalized[0]["receipt_msc"] % 3600000
            or not normalized[0]["receipt_msc"] <= start < split <= normalized[-1]["receipt_msc"]):
        raise ValueError("partition_boundaries")
    return {**value, "events": normalized}, _digest(raw)


def scenarios():
    base = Config()
    adverse = replace(base, commission_per_lot_round_turn=10.0, slippage_pips=0.5,
                      swap_long_per_lot=-4.5, swap_short_per_lot=-2.25)
    return {"base": {"config": asdict(base), "spread_floor_pips": 0.0},
            "adverse": {"config": asdict(adverse), "spread_floor_pips": 1.2}}


def source_bindings():
    return {name: _digest(_read(ROOT / name, 1024 * 1024)) for name in DEPENDENCIES}


def freeze_fixture(fixture_path, manifest_path):
    fixture, digest = load_fixture(fixture_path)
    baseline = _json(_read(ROOT / "config/baseline.json", 65536))
    if baseline != asdict(Config()):
        raise ValueError("frozen_baseline_changed")
    manifest = {"schema": "shadow113_frozen_invented_v1", "kind": "invented_fixture",
                "fixture_sha256": digest, "case": fixture["case"], "events": len(fixture["events"]),
                "development_start_msc": fixture["development_start_msc"],
                "validation_start_msc": fixture["validation_start_msc"],
                "clock": fixture["clock"], "scenarios": scenarios(), "sources": source_bindings()}
    write_new(manifest_path, manifest)
    return manifest


def _bound_fixture(fixture_path, manifest_path):
    fixture, digest = load_fixture(fixture_path)
    raw = _read(manifest_path, 65536)
    manifest = _json(raw)
    expected = {"schema": "shadow113_frozen_invented_v1", "kind": "invented_fixture",
                "fixture_sha256": digest, "case": fixture["case"], "events": len(fixture["events"]),
                "development_start_msc": fixture["development_start_msc"],
                "validation_start_msc": fixture["validation_start_msc"],
                "clock": fixture["clock"], "scenarios": scenarios(), "sources": source_bindings()}
    if manifest != expected:
        raise ValueError("frozen_fixture_config_or_code_changed")
    return fixture, manifest, _digest(raw)


class _CostedTicks(ExecutableEquityTickSimulator):
    """Instrument the inherited fills; do not replace the trading decisions."""
    def __init__(self, config):
        super().__init__(config)
        self.evaluation_start_msc = 0
        self.decisions = []
        self.cost_audit = []
        self._quote = None
        self._entry_audit = None

    def _decision(self):
        hour = self.current["hour"] * 3600000
        if hour < self.evaluation_start_msc:
            return 0, 0.0
        side, distance = super()._decision()
        self.decisions.append({"hour_msc": hour, "history_size": len(self.history),
                               "last_closed_hour": self.history[-1].time.isoformat(),
                               "side": side, "stop_distance": distance})
        return side, distance

    def step_tick(self, tick):
        self._quote = dict(tick)
        return super().step_tick(tick)

    def _open(self, bar, side, distance):
        had_position = self.position is not None
        super()._open(bar, side, distance)
        if had_position or self.position is None:
            return
        p = self.position
        midpoint = (self._quote["bid"] + self._quote["ask"]) / 2
        quote = self._quote["ask"] if side == 1 else self._quote["bid"]
        units = p.lots * self.config.contract_size
        self._entry_audit = {"midpoint": midpoint,
                             "spread": side * (quote - midpoint) * units,
                             "slippage": side * (p.entry - quote) * units}

    def _close(self, bar, exit_price, reason):
        p, entry = self.position, self._entry_audit
        if p is None or entry is None:
            raise ValueError("audit_position_state")
        units = p.lots * self.config.contract_size
        if reason == "target_tick":
            midpoint, spread, slippage = exit_price, 0.0, 0.0
        else:
            midpoint = (self._quote["bid"] + self._quote["ask"]) / 2
            quote = self._quote["bid"] if p.side == 1 else self._quote["ask"]
            spread = p.side * (midpoint - quote) * units
            slippage = p.side * (quote - exit_price) * units
        reference = p.side * (midpoint - entry["midpoint"]) * units
        super()._close(bar, exit_price, reason)
        trade = self.trades[-1]
        audit = {"reference_gross": reference, "spread": entry["spread"] + spread,
                 "slippage": entry["slippage"] + slippage, "commission": trade["commission"],
                 "financing_debit": -trade["swap"], "net": trade["net_pnl"], "exit_reason": reason}
        if not math.isclose(reference - sum(audit[k] for k in ("spread", "slippage", "commission", "financing_debit")),
                            audit["net"], abs_tol=1e-8, rel_tol=1e-10):
            raise ValueError("cost_reconciliation")
        self.cost_audit.append(audit)
        self._entry_audit = None


class Replay:
    """Incremental replay of exactly one frozen invented fixture and partition."""
    def __init__(self, fixture_path, manifest_path, scenario="base", partition="development"):
        fixture, manifest, binding = _bound_fixture(fixture_path, manifest_path)
        if scenario not in ("base", "adverse") or partition not in ("development", "validation"):
            raise ValueError("scenario_or_partition")
        self._fixture = fixture
        self._manifest = manifest
        self.binding = binding
        self.scenario, self.partition = scenario, partition
        self.start = fixture[partition + "_start_msc"]
        self._events = [dict(e) for e in fixture["events"] if partition == "validation"
                       or e["receipt_msc"] < fixture["validation_start_msc"]]
        self.next_sequence = 0
        self.repeats = 0
        self.sim = _CostedTicks(Config(**manifest["scenarios"][scenario]["config"]))
        self.sim.evaluation_start_msc = self.start

    @property
    def fixture(self):
        return deepcopy(self._fixture)

    @property
    def manifest(self):
        return deepcopy(self._manifest)

    @property
    def events(self):
        return [dict(event) for event in self._events]

    def _tick(self, event):
        floor = self._manifest["scenarios"][self.scenario]["spread_floor_pips"] * 0.0001
        return {"sequence": event["sequence"], "time_msc": event["receipt_msc"],
                "bid": event["bid"], "ask": max(event["ask"], event["bid"] + floor)}

    def step(self, event):
        event = _event(event, check_order=False)
        previous = self._events[self.next_sequence - 1] if self.next_sequence else None
        if previous is not None and event == previous:
            return False
        if self.sim.finished:
            raise ValueError("replay_finished")
        event = _event(event, previous)
        if self.next_sequence >= len(self._events) or event != self._events[self.next_sequence]:
            raise ValueError("event_not_in_frozen_partition")
        self.sim.step_tick(self._tick(event))
        if previous and event["source_msc"] == previous["source_msc"]:
            self.repeats += 1
        self.next_sequence += 1
        return True

    def run(self):
        for event in self._events[self.next_sequence:]:
            self.step(event)
        self.finish()
        return self.report()

    def finish(self):
        if self.next_sequence != len(self._events):
            raise ValueError("partition_not_exhausted")
        self.sim.finish()

    def checkpoint(self):
        payload = {"schema": "shadow113_checkpoint_v1", "manifest_sha256": self.binding,
                   "fixture_sha256": self._manifest["fixture_sha256"], "scenario": self.scenario,
                   "partition": self.partition, "next_sequence": self.next_sequence,
                   "repeats": self.repeats, "simulator": self.sim.checkpoint()}
        return json.dumps({"payload": payload, "sha256": _digest(_canonical(payload))}, sort_keys=True)

    @classmethod
    def restore(cls, fixture_path, manifest_path, checkpoint, scenario="base", partition="development"):
        if type(checkpoint) is not str or len(checkpoint.encode()) > MAX_BYTES:
            raise ValueError("checkpoint_size")
        result = cls(fixture_path, manifest_path, scenario, partition)
        value = _json(checkpoint)
        if type(value) is not dict or set(value) != {"payload", "sha256"}:
            raise ValueError("checkpoint_envelope")
        p = value["payload"]
        fields = {"schema", "manifest_sha256", "fixture_sha256", "scenario", "partition", "next_sequence", "repeats", "simulator"}
        if (type(p) is not dict or set(p) != fields or value["sha256"] != _digest(_canonical(p))
                or p["schema"] != "shadow113_checkpoint_v1" or p["manifest_sha256"] != result.binding
                or p["fixture_sha256"] != result._manifest["fixture_sha256"]
                or p["scenario"] != scenario or p["partition"] != partition):
            raise ValueError("checkpoint_binding")
        cursor = _integer(p["next_sequence"], 0, len(result._events))
        repeats = _integer(p["repeats"], 0, max(0, cursor - 1))
        try:
            sim = _CostedTicks.restore(p["simulator"], result.sim.config)
        except (KeyError, TypeError, OverflowError, AttributeError, IndexError) as exc:
            raise ValueError("checkpoint_simulator") from exc
        expected = result._tick(result._events[cursor - 1]) if cursor else None
        expected_repeats = sum(a["source_msc"] == b["source_msc"] for a, b in zip(result._events[:cursor], result._events[1:cursor]))
        if (type(sim.cost_audit) is not list or type(sim.trades) is not list
                or type(sim.decisions) is not list or type(sim.evaluation_start_msc) is not int):
            raise ValueError("checkpoint_state_types")
        if (_canonical(sim.last_tick) != _canonical(expected) or _canonical(sim._quote) != _canonical(expected)
                or repeats != expected_repeats
                or sim.evaluation_start_msc != result.start or type(sim.finished) is not bool
                or (sim.finished and cursor != len(result._events))
                or len(sim.cost_audit) != len(sim.trades)
                or (sim.position is None) != (sim._entry_audit is None)):
            raise ValueError("checkpoint_cursor_or_state")
        result.next_sequence, result.repeats, result.sim = cursor, repeats, sim
        return result

    def report(self):
        if not self.sim.finished:
            raise ValueError("unfinished_report")
        audit = self.sim.cost_audit
        totals = {k: sum(row[k] for row in audit) for k in ("reference_gross", "spread", "slippage", "commission", "financing_debit", "net")}
        metrics = self.sim.metrics()
        if not math.isclose(totals["net"], metrics["net_pnl"], abs_tol=1e-8, rel_tol=1e-10):
            raise ValueError("net_balance_reconciliation")
        return {"schema": "shadow113_invented_result_v1", "kind": "invented_software_check",
                "case": self._fixture["case"], "manifest_sha256": self.binding,
                "scenario": self.scenario, "partition": self.partition,
                "equity_metric_version": self.sim.execution_metric_version,
                "metrics": metrics, "cost_totals": totals, "cost_audit": audit,
                "cost_reference": "entry midpoint; market exit midpoint; target limit at modeled fill",
                "trades": self.sim.trades, "decisions": self.sim.decisions,
                "events": self.next_sequence, "repeated_latest_quotes": self.repeats,
                "warmup_events": sum(e["receipt_msc"] < self.start for e in self._events),
                "evaluation_events": sum(e["receipt_msc"] >= self.start for e in self._events),
                "final_hour_partial": True, "bar_exposure_includes_final_partial_hour": True,
                "market_validation": False, "market_data_qualified": False,
                "paper_evaluation_available": False, "orders_available": False,
                "real_money_execution_available": False}


def evaluate_fixture(fixture_path, manifest_path, output_path):
    results = [Replay(fixture_path, manifest_path, s, p).run()
               for s in ("base", "adverse") for p in ("development", "validation")]
    report = {"schema": "shadow113_demonstration_v1", "kind": "invented_software_check",
              "results": results, "selected_strategy": None, "market_validation": False,
              "orders_available": False, "real_money_execution_available": False}
    write_new(output_path, report)
    return report


def inspect_capture(path, capture_format="111"):
    """Return diagnostic evidence only. No simulator is constructed on this route."""
    if capture_format == "111":
        from .forward_capture_111 import inspect_run, summary
        diagnostic = summary(inspect_run(path))
    elif capture_format in ("107", "109"):
        from .private_recorder_107 import inspect_file, summary
        diagnostic = summary(inspect_file(path))
    else:
        raise ValueError("capture_format")
    return {"schema": "shadow113_capture_unavailable_v1", "capture_format": capture_format,
            "status": "performance_unavailable", "reason": "raw_clock_age_and_quality_unresolved",
            "diagnostics": diagnostic, "paper_evaluation_available": False,
            "market_data_qualified": False, "orders_available": False,
            "real_money_execution_available": False}
