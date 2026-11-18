"""Causal break setup decisions from completed invented publications."""
from copy import copy
from dataclasses import replace
import hashlib
import json

from ..elliott_full.contracts import Bar
from . import context, data, engine, geometry, lines, selection

VERSION = "TRL_BREAKS_173_V1"
FXR_PROFILE = "TRL_FXR_M"
FXR_STOP_PROJECTION = 4
PROFILES = ("TRL_BRK3_E1", FXR_PROFILE, context.PROFILE)


def bindings():
    result = context.bindings()
    for path in ("src/forex_demo_lab/trendline/breaks.py", "scripts/trendline-breaks-173.py"):
        result[path] = hashlib.sha256((data.ROOT / path).read_bytes()).hexdigest()
    return result


def trade_direction(line):
    return "LONG" if line.ray.kind == "resistance" else "SHORT"


def _triggered(states, action_ids, previous, bar, index, tick):
    if previous is None:
        return ()
    eligible = set(action_ids)
    return tuple(state for state in states
                 if state.line_id in eligible
                 and state.line.ray.correct_side_distance(index - 1, previous.close) >= 0
                 and state.line.ray.correct_side_distance(index, bar.close) <= -tick)


def _rank(states, index):
    if len({trade_direction(state.line) for state in states}) > 1:
        return None, "OPPOSING_SIGNAL"
    ranked = sorted(states, key=lambda state: _economic_key(state, index))
    if len(ranked) > 1 and _economic_key(ranked[0], index) == _economic_key(ranked[1], index):
        return None, "ECONOMIC_TIE"
    return ranked[0], None


def _economic_key(state, index):
    line = state.line
    return replace(line, age=index - line.ray.a_index).economic_key


def _safety_choice(lines, direction, close, index):
    kind = "support" if direction == "LONG" else "resistance"
    candidates = []
    for line in lines:
        if line.ray.kind == kind:
            distance = line.ray.correct_side_distance(index, close)
            if distance > 0:
                candidates.append(((distance, -len(line.touch_ids)), line))
    if not candidates:
        return None, "NO_SAFETY_LINE"
    candidates.sort(key=lambda item: item[0])
    if len(candidates) > 1 and candidates[0][0] == candidates[1][0]:
        return None, "SAFETY_LINE_TIE"
    return candidates[0][1], None


def _stop(safety_value, atr, tick, direction):
    buffer = max(tick, atr / 10)
    if direction == "LONG":
        return buffer, ((safety_value - buffer) // tick) * tick
    return buffer, -((-(safety_value + buffer)) // tick) * tick


class BreakReplay:
    """Replay completed-bar break setups on the selected profile."""

    def __init__(self, source, tick, profile="TRL_BRK3_E1"):
        if profile not in PROFILES:
            raise ValueError("implemented break profile required")
        self._tick = geometry.exact(tick)
        if self._tick <= 0:
            raise ValueError("positive declared price tick required")
        self._h4 = engine.Engine(source, profile)
        self._safety = engine.Engine(source, lines.SAFETY_PROFILE)
        self._daily = context.DailyContext(source) if profile == context.PROFILE else None
        self._bindings = bindings()
        self._events = []
        self._decisions = []
        self._last = None
        self._bytes = 0

    @property
    def publications(self):
        return tuple(Bar(**json.loads(event)) for event in self._events)

    @property
    def source(self):
        return self._h4.source

    def _check(self):
        if self._bindings != bindings():
            raise ValueError("setup source/protocol bindings changed")

    def observe(self, bar):
        self._check()
        if not isinstance(bar, Bar) or bar.timeframe not in ("D1", "H4"):
            raise ValueError("completed D1/H4 publication required")
        bar = Bar(**bar.record())
        if bar == self._last:
            return None if bar.timeframe == "D1" else json.loads(self._decisions[-1])
        if self._last is not None and _receipt_key(bar) <= _receipt_key(self._last):
            raise ValueError("ordered D1-first receipt prefix required")
        if len(self._events) >= data.ROW_LIMIT:
            raise ValueError("bounded setup publication count")

        if bar.timeframe == "D1":
            if self._daily is None:
                raise ValueError("D1 context is enabled only for the D1 variant")
            self._daily.observe(bar)
            result = None
        else:
            result = self._observe_h4(bar)
        self._events.append(data.canonical(bar.record()).decode())
        self._last = bar
        return result

    def _observe_h4(self, bar):
        # The copies stage new frontiers. Neither engine publishes into this
        # replay until trigger consumption and the setup decision both succeed.
        action_engine = copy(self._h4)
        safety_engine = copy(self._safety)
        staged = action_engine._prepare_bar(bar)
        inspector, _, action, action_ids = staged
        prior = action_engine._journal.states
        indexed = inspector.indexed
        index = indexed[-1][0]
        previous = indexed[-2][1] if len(indexed) > 1 and indexed[-2][0] == index - 1 else None
        triggered = _triggered(prior, action_ids, previous, bar, index, self._tick)
        frame = action_engine._finish_bar(bar, staged, tuple(sorted(state.line_id for state in triggered)))
        safety_frame = safety_engine.observe(bar)
        decision = self._decision(bar, index, action, prior, triggered, frame, safety_frame,
                                  safety_engine.metrics.atr_sma14)
        encoded = data.canonical(decision)
        if self._bytes + len(encoded) > engine.MAX_TRACE_BYTES:
            raise ValueError("bounded setup decision trace")
        self._check()
        self._h4, self._safety = action_engine, safety_engine
        self._decisions.append(encoded.decode())
        self._bytes += len(encoded)
        return json.loads(encoded)

    def _decision(self, bar, index, action, prior, triggered, frame, safety_frame, atr):
        known = {state.line_id for state in prior}
        missed = sorted(engine.instance_id(line) for line in action.selected
                        if engine.instance_id(line) not in known
                        and line.ray.correct_side_distance(index, bar.close) < 0)
        decision = {
            "h4_frame_id": frame["id"],
            "safety_frame_id": safety_frame["id"],
            "bar_index": index,
            "available_at": bar.available,
            "triggered": [{"line_id": state.line_id, "group_id": state.group_id,
                           "direction": trade_direction(state.line)} for state in triggered],
            "missed_break_ids": missed,
            "selected_line_id": None,
            "direction": None,
            "safety": None,
            "context": None,
        }
        if not triggered:
            reason = _no_trigger_reason(frame, missed)
            state = {"MISSED_BREAK": "DISCARDED", "POKED": "INVALIDATED"}.get(reason, "FORMING")
            decision.update(state=state, reason=reason)
            return decision
        winner, reason = _rank(triggered, index)
        if reason:
            decision.update(state="ABSTAINED", reason=reason)
            return decision

        direction = trade_direction(winner.line)
        decision.update(selected_line_id=winner.line_id, direction=direction)
        eligible = set(safety_frame["eligible_line_ids"])
        candidates = (selection.ValidatedLine.from_record(row)
                      for row in safety_frame["selection"]["ranked"])
        safety, reason = _safety_choice((line for line in candidates if engine.instance_id(line) in eligible),
                                        direction, bar.close, index)
        if reason:
            decision.update(state="ABSTAINED", reason=reason)
            return decision

        value = safety.ray.value(index)
        projection = FXR_STOP_PROJECTION if self._h4.profile == FXR_PROFILE else 0
        stop_reference = safety.ray.project(index, projection)
        buffer, stop = _stop(stop_reference, atr, self._tick, direction)
        decision["safety"] = {
            "line_id": engine.instance_id(safety),
            "line_value": geometry.rational_record(value),
            "atr_sma14": geometry.rational_record(atr),
            "buffer": geometry.rational_record(buffer),
            "stop": geometry.rational_record(stop),
        }
        if projection:
            decision["safety"].update(projected_index=index + projection,
                                      projected_line_value=geometry.rational_record(stop_reference))
        if stop <= 0:
            decision.update(state="SKIPPED", reason="INVALID_STOP_PRICE")
            return decision
        if self._daily is not None:
            snapshot = self._daily.snapshot(bar.available)
            gate = context.outcome(direction, snapshot["bias"])
            decision["context"] = {"snapshot": snapshot, "outcome": gate}
            if gate != "ALLOW":
                decision.update(state="SKIPPED", reason=gate)
                return decision
        decision.update(state="READY", reason=None)
        return decision

    def report(self):
        self._check()
        return {
            "schema": VERSION,
            "kind": ("invented_fxr_m_setup_replay" if self._h4.profile == FXR_PROFILE
                     else "invented_brk3_setup_replay"),
            "data_level": "B",
            "tick": geometry.rational_record(self._tick),
            "source_bindings": dict(self._bindings),
            "action_replay": self._h4.report(),
            "safety_replay": self._safety.report(),
            "decisions": [json.loads(row) for row in self._decisions],
            "trigger_detection_available": True,
            "actual_source_admitted": False,
            "entry_ready": False,
            "orders_available": False,
        }

    def checkpoint(self):
        report = self.report()
        bars = [json.loads(row) for row in self._events]
        record = {
            "schema": VERSION,
            "profile": self._h4.profile,
            "tick": report["tick"],
            "source_bindings": report["source_bindings"],
            "source_sha256": self._h4.source.sha256,
            "bars": bars,
            "state_sha256": data.digest([report, bars]),
        }
        if len(data.canonical(record)) > engine.MAX_CHECKPOINT_BYTES:
            raise ValueError("bounded setup checkpoint required")
        return record

    @classmethod
    def restore(cls, source, record):
        data.fields(record, ("schema", "profile", "tick", "source_bindings", "source_sha256", "bars", "state_sha256"))
        if (record["schema"] != VERSION or record["source_sha256"] != source.sha256
                or record["source_bindings"] != bindings()
                or type(record["bars"]) is not list or len(record["bars"]) > data.ROW_LIMIT
                or len(data.canonical(record)) > engine.MAX_CHECKPOINT_BYTES):
            raise ValueError("matching bounded setup checkpoint required")
        result = cls(source, selection.fraction(record["tick"]), record["profile"])
        for count, row in enumerate(record["bars"], 1):
            result.observe(Bar(**row))
            if len(result._events) != count:
                raise ValueError("duplicate setup checkpoint publication")
        if data.digest([result.report(), [bar.record() for bar in result.publications]]) != record["state_sha256"]:
            raise ValueError("setup checkpoint replay state mismatch")
        return result


def _receipt_key(bar):
    return bar.available, bar.timeframe != "D1", bar.start


def _no_trigger_reason(frame, missed):
    if frame["search_incomplete"]:
        return "SEARCH_INCOMPLETE"
    if frame["coverage_state"] != "CURRENT":
        return "DATA_GAP"
    if missed:
        return "MISSED_BREAK"
    if any(row["view"]["status"] == "POKED" and row["at"]["bar_index"] == frame["bar_index"]
           for row in frame["revisions"]):
        return "POKED"
    return "NO_BREAK" if frame["action_line_ids"] else "NO_VALID_LINE"
