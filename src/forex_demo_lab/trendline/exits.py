"""Chronological, independent Level B price paths on invented observations."""
from bisect import bisect_left
from fractions import Fraction
import hashlib

from . import breaks, data, engine, entries, fills, selection

VERSION = "TRL_B_EXITS_181_V1"


def bindings():
    result = entries.bindings()
    path = "src/forex_demo_lab/trendline/exits.py"
    result[path] = hashlib.sha256((data.ROOT / path).read_bytes()).hexdigest()
    return result


class Protection:
    """E1 held ray, prospective hard stop, and irrevocable close-beyond latch."""

    def __init__(self, line_id, registered, position):
        self.line_id = line_id
        self.registered = registered
        self.line = selection.ValidatedLine.from_record(registered[line_id]["line"])
        self.position = position
        self.poked = False
        self.market_exit = None
        self.events = []

    def update(self, frame, atr):
        if self.market_exit is not None:
            return
        record = self.position.record()
        opened = fills.Event.from_record(record["entry_at"])
        bar = frame["bar"]
        if bar["end"] <= opened.time:
            return
        index = frame["bar_index"]
        ray = self.line.ray
        at = fills.Event(frame["as_of"], entries.H4_DECISION_ORDINAL).record()
        if ray.correct_side_distance(index, bar["close"]) < 0:
            self.market_exit = {"reason": "SAFETY_CLOSE_BEYOND", "decision_at": at,
                                "line_id": self.line_id, "h4_index": index}
            self.events.append(self.market_exit)
            return

        extreme = bar["low"] if ray.kind == "support" else bar["high"]
        if not self.poked and ray.correct_side_distance(index, extreme) < 0:
            self.poked = True
            self.events.append({"reason": "HELD_LINE_POKED", "decision_at": at, "line_id": self.line_id,
                                "h4_index": index})
        if atr is None or atr <= 0:
            return

        direction = record["direction"]
        side = 1 if direction == "LONG" else -1
        old_stop = Fraction(record["stop"])
        tick = Fraction(record["tick"])
        stop = old_stop
        if not self.poked:
            _, candidate = breaks._stop(ray.value(index), atr, tick, direction)
            if side * (candidate - stop) > 0 and candidate > 0:
                stop = candidate

        eligible = []
        for line in breaks._eligible_safety(frame):
            line_id = engine.instance_id(line)
            if line_id == self.line_id or line.ray.kind != ray.kind:
                continue
            formed = self.registered[line_id]["valid_since"]
            if formed is None or fills.Event(formed[0], entries.H4_DECISION_ORDINAL) <= opened:
                continue
            _, candidate = breaks._stop(line.ray.value(index), atr, tick, direction)
            if candidate > 0 and side * (candidate - stop) > 0:
                eligible.append(line)
        replacement, reason = breaks._safety_choice(eligible, direction, bar["close"], index)
        if reason == "SAFETY_LINE_TIE":
            self.events.append({"reason": "REPLACEMENT_TIE", "decision_at": at,
                                "line_id": self.line_id, "h4_index": index})
        previous_line_id = self.line_id
        if replacement is not None:
            self.line = replacement
            self.line_id = engine.instance_id(replacement)
            self.poked = False
            _, stop = breaks._stop(replacement.ray.value(index), atr, tick, direction)

        if stop != old_stop:
            record.update(stop=fills.text(stop), stop_effective_at=at)
            self.position = fills.Position.from_record(record)
            self.events.append({
                "reason": "REPLACED_AND_TIGHTENED" if replacement is not None else "STOP_TIGHTENED",
                "decision_at": at, "line_id": self.line_id, "previous_line_id": previous_line_id,
                "h4_index": index, "old_stop": fills.text(old_stop), "stop": fills.text(stop),
            })


def _mark(model, hour, direction, *, at_open=False):
    price = Fraction(hour.open if at_open else hour.close)
    if direction == "SHORT":
        price += max(Fraction(hour.spread_pips), Fraction(model.costs["spread_floor_pips"])) * fills.PIP
    return {"time": hour.start if at_open else hour.end, "available_at": hour.available_at,
            "price": fills.text(price), "side": "BID" if direction == "LONG" else "ASK"}


def _path(model, windows, hourly, as_of, boundary, liquidation, attempt, h4, registered):
    record = attempt["price_result"]["position"]
    position = fills.Position.from_record(record)
    entry = record["entry_at"]["time"]
    result = {"attempt_id": attempt["id"], "entry": record, "exit": None,
              "state": "OPEN", "reason": None, "liquidation_at": liquidation,
              "last_mark": None, "protection_events": []}
    if entry >= liquidation:
        result.update(state="NOT_OPENED", reason="ENTRY_AT_LIQUIDATION", entry=None)
        return result
    protection = (Protection(attempt["safety_line_id"], registered, position)
                  if record["exit_model"] == "E1" else None)
    result["last_mark"] = _mark(model, hourly[entry], record["direction"], at_open=True)
    publications = iter(h4) if protection is not None else iter(())
    next_h4 = next(publications, None)
    for window in windows:
        if window.start > liquidation:
            break
        while next_h4 is not None and next_h4[0]["as_of"] <= min(window.start, as_of):
            protection.update(*next_h4)
            next_h4 = next(publications, None)
        if window.start > as_of:
            break
        hour = hourly.get(window.start)
        if hour is None or hour.available_at > boundary:
            if window.start == liquidation and as_of >= boundary:
                result.update(state="OPEN_AT_BOUNDARY", reason="MISSING_LIQUIDATION_OPEN")
            elif window.start < liquidation and as_of >= window.end:
                result.update(state="UNAVAILABLE", reason="H1_COVERAGE_INCOMPLETE",
                              missing_h1_start=window.start)
            break
        if protection is not None:
            position = protection.position
        market_exit = None if protection is None else protection.market_exit
        if window.start == liquidation or market_exit is not None:
            priced = model.exit_open(position, fills.Opening.from_hour(hour, entries.H1_OPEN_ORDINAL),
                                     scheduled_exit=True)
            if priced["reason"] == "SCHEDULED_OPEN_EXIT":
                result["scheduled_cause"] = "PARTITION_LIQUIDATION" if market_exit is None else market_exit["reason"]
        else:
            priced = model.exit_hour(position, hour, as_of=as_of, open_ordinal=entries.H1_OPEN_ORDINAL)
        if priced["status"] == "EXIT":
            result.update(state="CLOSED", reason=priced["reason"], exit=priced)
            break
        if priced["status"] != "NO_EXIT":
            result.update(state="UNAVAILABLE", reason=priced["reason"])
            break
        result["last_mark"] = _mark(model, hour, record["direction"])
    if protection is not None:
        result.update(protection_events=protection.events, pending_market_exit=protection.market_exit
                      if result["state"] != "CLOSED" else None, safety_line_id=protection.line_id)
        position = protection.position
    result["position"] = position.record()
    return result


def evaluate(replay, hours, *, as_of, cost_profile="base", liquidation_at=None):
    """Replay exits for independently priced fills, in the declared partition."""
    priced = entries.evaluate(replay, hours, as_of=as_of, cost_profile=cost_profile)
    return _evaluate(replay, hours, priced, liquidation_at)


def _evaluate(replay, hours, priced, liquidation_at):
    bound = bindings()
    as_of, cost_profile = priced["as_of"], priced["cost_profile"]["name"]
    source = replay.source
    calendar = source.calendar
    windows = calendar.frame("H1")
    starts = tuple(window.start for window in windows)
    if not starts:
        raise ValueError("exit replay requires a scheduled H1 partition")
    liquidation = starts[-1] if liquidation_at is None else liquidation_at
    data.integer(liquidation)
    if liquidation not in starts:
        raise ValueError("liquidation requires a scheduled H1 open inside the declared partition")
    hourly = entries._visible_hours(source, hours, as_of, calendar)
    report = replay.report()
    protection = report["safety_replay"] or report["action_replay"]
    registered = {line["line_id"]: line for line in protection["journal"]["lines"]}
    atr = {decision["safety_frame_id"]: decision["atr_sma14"] for decision in report["decisions"]}
    h4 = [(frame, None if atr[frame["id"]] is None else selection.fraction(atr[frame["id"]]))
          for frame in protection["frames"]]
    model = fills.PriceModel(source, cost_profile)

    paths = []
    for attempt in priced["attempts"]:
        if attempt["status"] == "FILLED":
            opened = attempt["price_result"]["position"]["entry_at"]["time"]
            paths.append(_path(model, windows[bisect_left(starts, opened):], hourly, as_of, calendar.end,
                               liquidation, attempt, h4, registered))
    if bindings() != bound:
        raise ValueError("exit replay source bindings changed")
    return {"schema": VERSION, "kind": "invented_independent_b_exit_paths",
            "source_sha256": source.sha256, "source_bindings": bound, "profile": priced["profile"],
            "cost_profile": dict(model.costs), "as_of": as_of, "liquidation_at": liquidation,
            "partition_end": calendar.end, "paths": paths, "price_only": True,
            "account_ledger_available": False, "orders_available": False}
