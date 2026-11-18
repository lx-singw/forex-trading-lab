"""Causal setup decisions from completed invented publications."""
from copy import copy
from dataclasses import replace
import hashlib
import json

from ..elliott_full.contracts import Bar
from . import context, data, delayed, engine, geometry, levels, lines, selection

VERSION = "TRL_BREAKS_173_V1"
FXR_PROFILE = "TRL_FXR_M"
BRK2_PROFILE = "TRL_BRK2_E1"
BNC_PROFILE = "TRL_BNC_E1"
FXR_STOP_PROJECTION = 4
BOUNCE_SPACING = 6
SETUP_FAMILIES = {
    "TRL_BRK3_E1": "brk3",
    FXR_PROFILE: "fxr_m",
    BRK2_PROFILE: "brk2",
    BNC_PROFILE: "bnc",
    context.PROFILE: "brk3",
    lines.DLY_PROFILE: "brk3_dly",
}
PROFILES = tuple(SETUP_FAMILIES)


def bindings():
    result = context.bindings()
    for path in ("src/forex_demo_lab/trendline/breaks.py",
                 "src/forex_demo_lab/trendline/delayed.py",
                 "src/forex_demo_lab/trendline/levels.py", "scripts/trendline-breaks-173.py"):
        result[path] = hashlib.sha256((data.ROOT / path).read_bytes()).hexdigest()
    return result


def trade_direction(line):
    if line.profile == BNC_PROFILE:
        return "LONG" if line.ray.kind == "support" else "SHORT"
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


def _eligible_safety(frame):
    eligible = set(frame["eligible_line_ids"])
    candidates = (selection.ValidatedLine.from_record(row) for row in frame["selection"]["ranked"])
    return tuple(line for line in candidates if engine.instance_id(line) in eligible)


def _stop(safety_value, atr, tick, direction):
    buffer = max(tick, atr / 10)
    if direction == "LONG":
        return buffer, ((safety_value - buffer) // tick) * tick
    return buffer, -((-(safety_value + buffer)) // tick) * tick


class BreakReplay:
    """Replay completed-bar setups on the selected profile."""

    def __init__(self, source, tick, profile="TRL_BRK3_E1", *, enable_dly=False):
        if profile not in PROFILES:
            raise ValueError("implemented setup profile required")
        if type(enable_dly) is not bool or enable_dly != (profile == lines.DLY_PROFILE):
            raise ValueError("DLY profile and explicit invented-replay opt-in must agree")
        self._tick = geometry.exact(tick)
        if self._tick <= 0:
            raise ValueError("positive declared price tick required")
        self._h4 = engine.Engine(source, profile)
        self._safety = None if profile == BNC_PROFILE else engine.Engine(source, lines.SAFETY_PROFILE)
        self._daily = context.DailyContext(source) if profile == context.PROFILE else None
        self._levels = levels.LevelFinder(source) if profile == FXR_PROFILE else None
        self._bindings = bindings()
        self._events = []
        self._decisions = []
        self._last = None
        self._bytes = 0
        self._waiting = ()
        self._dly_ends = tuple(window.end for window in source.calendar.frame("H4")) if enable_dly else ()

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
            if self._daily is not None:
                self._daily.observe(bar)
            elif self._levels is not None:
                self._levels.observe_daily(bar)
            else:
                raise ValueError("D1 publications require the D1 context or FXR level profile")
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
        atr = inspector.metrics.atr_sma14
        previous = indexed[-2][1] if len(indexed) > 1 and indexed[-2][0] == index - 1 else None
        contacts = None
        if action_engine.profile == BNC_PROFILE:
            contacts = self._bounce_contacts(action.selected, prior, action_ids, bar, index, atr)
            trigger_ids = {item["line_id"] for item in contacts if item["reason"] == "CONTACT"}
            triggered = tuple(state for state in prior if state.line_id in trigger_ids)
        else:
            triggered = _triggered(prior, action_ids, previous, bar, index, self._tick)
        frame = action_engine._finish_bar(bar, staged, tuple(sorted(state.line_id for state in triggered)))
        safety_frame = frame if safety_engine is None else safety_engine.observe(bar)
        if contacts:
            groups = {state.line_id: state.group_id for state in action_engine._journal.states}
            for item in contacts:
                item["group_id"] = groups[item["line_id"]]
        decision = self._decision(bar, index, action, prior, triggered, frame, safety_frame, atr, contacts)
        waiting = self._waiting
        if self._dly_ends:
            waiting = self._resolve_delays(decision, triggered, bar, index, atr, safety_frame, previous)
        if self._levels is not None and decision["state"] == "READY":
            decision["target_levels"] = self._levels.capture(inspector, atr)
        encoded = data.canonical(decision)
        if self._bytes + len(encoded) > engine.MAX_TRACE_BYTES:
            raise ValueError("bounded setup decision trace")
        self._check()
        self._h4, self._safety = action_engine, safety_engine
        self._waiting = waiting
        self._decisions.append(encoded.decode())
        self._bytes += len(encoded)
        return json.loads(encoded)

    def _bounce_contacts(self, selected, prior, action_ids, bar, index, atr):
        if not selected:
            return []
        eligible = set(action_ids)
        states = {state.line_id: state for state in prior}
        journal = self._h4._journal
        by_geometry, by_group = {}, {}
        for row in self._decisions[-(BOUNCE_SPACING - 1):]:
            previous = json.loads(row)
            for contact in previous["contacts"]:
                if contact["reason"] == "ALREADY_CONSUMED":
                    continue
                root, _ = journal.group_state(contact["group_id"])
                by_group[root] = previous["bar_index"]
                by_geometry[contact["geometry_id"]] = previous["bar_index"]
        tolerance = atr * geometry.TOUCH_TOLERANCE
        contacts = []
        for line in selected:
            line_id = engine.instance_id(line)
            state = states.get(line_id)
            root, consumed = (None, False) if state is None else journal.group_state(state.group_id)
            if state is not None and line_id not in eligible and not consumed:
                continue
            extreme = bar.low if line.ray.kind == "support" else bar.high
            distance = line.ray.correct_side_distance(index, extreme)
            if not 0 <= distance <= tolerance or line.ray.correct_side_distance(index, bar.close) <= 0:
                continue
            last_approach = by_geometry.get(line.geometry_id, -BOUNCE_SPACING)
            if consumed:
                reason = "ALREADY_CONSUMED"
            elif state is None:
                reason = "FORMATION_BAR_CONTACT"
            else:
                last_approach = max(last_approach, by_group.get(root, -BOUNCE_SPACING))
                if index - line.touch_indices[-1] < BOUNCE_SPACING:
                    reason = "TOUCH_TOO_CLOSE"
                elif index - last_approach < BOUNCE_SPACING:
                    reason = "CONTACT_TOO_CLOSE"
                else:
                    reason = "CONTACT"
            contacts.append({
                "line_id": line_id,
                "geometry_id": line.geometry_id,
                "distance": geometry.rational_record(distance),
                "tolerance": geometry.rational_record(tolerance),
                "reason": reason,
            })
        return contacts

    def _decision(self, bar, index, action, prior, triggered, frame, safety_frame, atr, contacts):
        known = {state.line_id for state in prior}
        missed = [] if contacts is not None else sorted(engine.instance_id(line) for line in action.selected
                        if engine.instance_id(line) not in known
                        and line.ray.correct_side_distance(index, bar.close) < 0)
        decision = {
            "h4_frame_id": frame["id"],
            "safety_frame_id": safety_frame["id"],
            "bar_index": index,
            "available_at": bar.available,
            "atr_sma14": geometry.rational_record(atr),
            "triggered": [{"line_id": state.line_id, "group_id": state.group_id,
                           "direction": trade_direction(state.line)} for state in triggered],
            "missed_break_ids": missed,
            "selected_line_id": None,
            "direction": None,
            "safety": None,
            "context": None,
        }
        if contacts is not None:
            decision["contacts"] = contacts
        if not triggered:
            reason = _no_trigger_reason(frame, missed, contacts)
            state = {"MISSED_BREAK": "DISCARDED", "POKED": "INVALIDATED"}.get(reason, "FORMING")
            decision.update(state=state, reason=reason)
            return decision
        winner, reason = _rank(triggered, index)
        if reason:
            decision.update(state="ABSTAINED", reason=reason)
            return decision

        direction = trade_direction(winner.line)
        decision.update(selected_line_id=winner.line_id, direction=direction)
        safety = winner.line
        if contacts is None:
            safety, reason = _safety_choice(_eligible_safety(safety_frame), direction, bar.close, index)
            if reason:
                decision.update(state="ABSTAINED", reason=reason)
                return decision

        decision["safety"] = self._protection(safety, index, atr, direction)
        if selection.fraction(decision["safety"]["stop"]) <= 0:
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

    def _protection(self, safety, index, atr, direction):
        value = safety.ray.value(index)
        projection = FXR_STOP_PROJECTION if self._h4.profile == FXR_PROFILE else 0
        stop_reference = safety.ray.project(index, projection)
        buffer, stop = _stop(stop_reference, atr, self._tick, direction)
        result = {
            "line_id": engine.instance_id(safety),
            "line_value": geometry.rational_record(value),
            "atr_sma14": geometry.rational_record(atr),
            "buffer": geometry.rational_record(buffer),
            "stop": geometry.rational_record(stop),
        }
        if projection:
            result.update(projected_index=index + projection,
                          projected_line_value=geometry.rational_record(stop_reference))
        return result

    def _resolve_delays(self, decision, triggered, bar, index, atr, safety_frame, previous):
        events, ready, waiting = [], {}, []
        safety_lines = _eligible_safety(safety_frame) if self._waiting else ()
        data_gap = previous is None or safety_frame["coverage_state"] != "CURRENT"
        for pending in self._waiting:
            outcome = pending.guard(bar, index, atr, data_gap=data_gap,
                                    search_incomplete=safety_frame["search_incomplete"])
            if outcome:
                events.append(pending.record(*outcome))
                continue
            safety, reason = _safety_choice(safety_lines, pending.direction, bar.close, index)
            if reason == "NO_SAFETY_LINE":
                waiting.append(pending)
            elif reason:
                events.append(pending.record("ABSTAINED", reason))
            else:
                protection = self._protection(safety, index, atr, pending.direction)
                if selection.fraction(protection["stop"]) <= 0:
                    events.append(pending.record("SKIPPED", "INVALID_STOP_PRICE"))
                else:
                    ready[pending.line_state.line_id] = (pending, protection)

        if decision["state"] == "READY" or decision["reason"] == "NO_SAFETY_LINE":
            selected = next(state for state in triggered if state.line_id == decision["selected_line_id"])
            deadline_index = min(index + delayed.EXPIRY_BARS, len(self._dly_ends) - 1)
            fresh = delayed.AwaitingSafety(selected, index, decision["h4_frame_id"],
                                           bar.close, self._dly_ends[deadline_index])
            if decision["state"] == "READY":
                ready[selected.line_id] = (fresh, decision["safety"])
            elif bar.available >= fresh.expires_at:
                decision.update(state="EXPIRED", reason="DLY_EXPIRED")
                events.append(fresh.record("EXPIRED", "DLY_EXPIRED"))
            else:
                decision.update(state="AWAITING_SAFETY", reason="NO_SAFETY_LINE")
                waiting.append(fresh)
                events.append(fresh.record("AWAITING_SAFETY", "NO_SAFETY_LINE"))

        decision["dly_transitions"] = events
        if ready:
            winner, reason = _rank(tuple(pending.line_state for pending, _ in ready.values()), index)
            if winner is None:
                events.extend(pending.record("ABSTAINED", reason) for pending, _ in ready.values())
                decision.update(state="ABSTAINED", reason=reason, selected_line_id=None,
                                direction=None, safety=None)
            else:
                pending, protection = ready[winner.line_id]
                origin = pending.record("READY")
                events.extend(other.record("ABSTAINED", "LOWER_RANKED_SETUP")
                              for line_id, (other, _) in ready.items() if line_id != winner.line_id)
                events.append(origin)
                decision.update(state="READY", reason=None, selected_line_id=winner.line_id,
                                direction=pending.direction, safety=protection, dly_origin=origin)
        elif decision["state"] == "FORMING" and (events or waiting):
            summary = events[0] if events else waiting[0].record("AWAITING_SAFETY", "NO_SAFETY_LINE")
            decision.update(state=summary["state"], reason=summary["reason"],
                            selected_line_id=summary["line_id"], direction=summary["direction"])
        return tuple(waiting)

    def report(self, *, as_of=None):
        self._check()
        result = {
            "schema": VERSION,
            "kind": f"invented_{SETUP_FAMILIES[self._h4.profile]}_setup_replay",
            "data_level": "B",
            "tick": geometry.rational_record(self._tick),
            "source_bindings": dict(self._bindings),
            "action_replay": self._h4.report(),
            "safety_replay": None if self._safety is None else self._safety.report(),
            "decisions": [json.loads(row) for row in self._decisions],
            "trigger_detection_available": True,
            "actual_source_admitted": False,
            "entry_ready": False,
            "orders_available": False,
        }
        if self._dly_ends:
            clock = self._h4.clock if as_of is None else as_of
            data.integer(clock)
            if not self._h4.clock <= clock <= self.source.calendar.end + 60000:
                raise ValueError("DLY report clock outside supplied prefix or source scope")
            result["dly_waiting"] = [
                pending.record("EXPIRED", "DLY_EXPIRED") if clock >= pending.expires_at
                else pending.record("AWAITING_SAFETY", "NO_SAFETY_LINE")
                for pending in self._waiting
            ]
        return result

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
    def restore(cls, source, record, *, enable_dly=False):
        data.fields(record, ("schema", "profile", "tick", "source_bindings", "source_sha256", "bars", "state_sha256"))
        if (record["schema"] != VERSION or record["source_sha256"] != source.sha256
                or record["source_bindings"] != bindings()
                or type(record["bars"]) is not list or len(record["bars"]) > data.ROW_LIMIT
                or len(data.canonical(record)) > engine.MAX_CHECKPOINT_BYTES):
            raise ValueError("matching bounded setup checkpoint required")
        result = cls(source, selection.fraction(record["tick"]), record["profile"], enable_dly=enable_dly)
        for count, row in enumerate(record["bars"], 1):
            result.observe(Bar(**row))
            if len(result._events) != count:
                raise ValueError("duplicate setup checkpoint publication")
        if data.digest([result.report(), [bar.record() for bar in result.publications]]) != record["state_sha256"]:
            raise ValueError("setup checkpoint replay state mismatch")
        return result


def _receipt_key(bar):
    return bar.available, bar.timeframe != "D1", bar.start


def _no_trigger_reason(frame, missed, contacts=None):
    if frame["search_incomplete"]:
        return "SEARCH_INCOMPLETE"
    if frame["coverage_state"] != "CURRENT":
        return "DATA_GAP"
    if missed:
        return "MISSED_BREAK"
    if any(row["view"]["status"] == "POKED" and row["at"]["bar_index"] == frame["bar_index"]
           for row in frame["revisions"]):
        return "POKED"
    if contacts is not None:
        if contacts:
            return contacts[0]["reason"]
        return "NO_CONTACT" if frame["action_line_ids"] else "NO_VALID_LINE"
    return "NO_BREAK" if frame["action_line_ids"] else "NO_VALID_LINE"
