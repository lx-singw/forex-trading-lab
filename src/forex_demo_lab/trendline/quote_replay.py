"""Invented Level Q execution against an ordered synchronized quote tape."""
from bisect import bisect_right
from collections import Counter
from fractions import Fraction
import hashlib

from . import breaks, context, data, entries, exits, fills, ledger, quotes, risk, selection

VERSION = "TRL_Q_REPLAY_185_V1"


def bindings():
    result = ledger.bindings()
    for path in ("src/forex_demo_lab/trendline/quotes.py",
                 "src/forex_demo_lab/trendline/quote_replay.py", "scripts/trendline-quotes-185.py"):
        result[path] = hashlib.sha256((data.ROOT / path).read_bytes()).hexdigest()
    return result


def _prices(quote, spread_floor):
    bid = Fraction(quote.bid)
    ask = max(Fraction(quote.ask), bid + spread_floor)
    return bid, ask, ask - bid


def _quality(tape, quote, previous):
    if quote.time >= tape.calendar.end:
        return "OUTSIDE_PARTITION"
    source_slot, receipt_slot = tape.slot(quote.source), tape.slot(quote.time)
    if source_slot is None or receipt_slot is None or receipt_slot.session != source_slot.session:
        return "OUTSIDE_SESSION"
    if quote.time - quote.source > quotes.MAX_AGE:
        return "STALE_QUOTE"
    if previous is not None and (quote.source, quote.bid, quote.ask) == (previous.source, previous.bid, previous.ask):
        return "REPEATED_QUOTE"
    return "EXECUTABLE"


def _decisions(tape, report, candidate_quotes, as_of, cost):
    sources = [quote.source for quote in candidate_quotes]
    decisions, at_quote = [], {}
    for attempt, targets in entries._requests(report, tape.calendar, cost):
        request, expiry = attempt["request"], attempt["expires_at"]
        decision = request["decision_at"]["time"]
        event = {**attempt, "request": {**request, "kind": "invented_q_price_request"},
                 "status": "PENDING", "reason": "AWAITING_ELIGIBLE_QUOTE"}
        decisions.append(event)
        if expiry is None or decision >= expiry:
            event.update(status="EXPIRED", reason="ENTRY_WINDOW_EXPIRED")
            continue
        deadline = min(expiry, tape.liquidation)
        index = bisect_right(sources, decision)
        quote = candidate_quotes[index] if index < len(sources) else None
        if quote is not None and quote.time < deadline:
            if quote.sequence in at_quote:
                raise ValueError("overlapping quote opportunities require resolved setup ordering")
            at_quote[quote.sequence] = event, targets
        elif as_of >= deadline:
            reason = "ENTRY_AT_LIQUIDATION" if deadline == tape.liquidation else "NO_ELIGIBLE_QUOTE"
            event.update(status="EXPIRED", reason=reason)
    return decisions, at_quote


class _Execution:
    def __init__(self, tape, report, as_of, cost):
        self.tape, self.as_of = tape, as_of
        self.book = ledger._Book(tape.geometry_source, {}, {"as_of": as_of, "cost_profile": {"name": cost}},
                                 {"liquidation_at": tape.liquidation})
        self.floor = Fraction(self.book.model.costs["spread_floor_pips"]) * fills.PIP
        safety = report["safety_replay"] or report["action_replay"]
        self.registered = {row["line_id"]: row for row in safety["journal"]["lines"]}
        self.frames = safety["frames"]
        self.frame_times = [frame["as_of"] for frame in self.frames]
        self.atr = {decision["safety_frame_id"]: decision["atr_sma14"] for decision in report["decisions"]}
        self.frame_index = 0
        self.position = self.protection = self.position_record = self.fault = None
        self.positions = []

    def _protect(self, through):
        if self.protection is None:
            return
        start = self.position.record()["entry_at"]["time"]
        while self.frame_index < len(self.frames) and self.frame_times[self.frame_index] < through:
            frame = self.frames[self.frame_index]
            atr = self.atr[frame["id"]]
            self.protection.update(frame, None if atr is None else selection.fraction(atr),
                                   close_only=frame["bar"]["start"] < start)
            self.frame_index += 1
        self.position = self.protection.position

    def _roll_held(self, through, received):
        old_mark = self.book.mark["time"]
        for day in range(self.book.day + 1, through // risk.UTC_DAY_MS + 1):
            at = day * risk.UTC_DAY_MS
            slot = self.tape.slot(old_mark)
            next_index = bisect_right(self.tape.starts, old_mark)
            next_open = self.tape.starts[next_index] if next_index < len(self.tape.starts) else self.tape.calendar.end
            closure = slot.end <= at <= next_open and slot.end - old_mark <= quotes.MAX_AGE
            valid = at - old_mark <= quotes.MAX_AGE or closure
            self.book._roll(at, received, reconciled=valid)

    def _mark(self, quote, prices, direction):
        side = "BID" if direction == "LONG" else "ASK"
        return {"time": quote.source, "available_at": quote.time, "sequence": quote.sequence,
                "price": fills.text(prices[0 if side == "BID" else 1]), "side": side}

    def _manage(self, quote, prices):
        if self.fault is not None:
            return
        self._roll_held(quote.source, quote.time)
        self._protect(quote.source)
        pending = self.protection is not None and self.protection.market_exit is not None
        liquidate = quote.source >= self.tape.liquidation
        position = self.position.record()
        outcome = self.book.model._exit_at(position, prices, fills.Event(quote.source, quote.sequence),
                                           pending or liquidate)
        if outcome["status"] == "UNAVAILABLE":
            self.fault = outcome["reason"]
            return
        if outcome["status"] != "EXIT":
            self.book.record_mark(self._mark(quote, prices, position["direction"]), "EXECUTABLE_QUOTE")
            return
        outcome["reason"] = {"STOP_OPEN_GAP": "STOP_QUOTE", "TARGET_OPEN_REACH": "TARGET_QUOTE",
                             "SCHEDULED_OPEN_EXIT": "PARTITION_LIQUIDATION" if liquidate else
                             "SAFETY_CLOSE_BEYOND"}[outcome["reason"]]
        self.book.close_trade(position, outcome, quote.source, quote.time)
        self.position_record.update(state="CLOSED", release_at=quote.time, closing_quote=quote.record(),
                                    protection_events=[] if self.protection is None else self.protection.events)
        self.position = self.protection = self.position_record = None

    def on_quote(self, quote, attempt):
        prices = _prices(quote, self.floor)
        occupied = self.position is not None
        if occupied:
            self._manage(quote, prices)
        else:
            # Publish idle-day references with the quote receipt that
            # advances the account clock, even when no setup is ready.
            self.book._roll(quote.source, quote.time)
        if attempt is None:
            return
        event, targets = attempt
        event["quote"] = quote.record()
        event["status"] = "SKIPPED"
        if occupied:
            event["reason"] = "POSITION_LIMIT"
            return
        snapshot = self.book.capital_at(quote.source)
        if snapshot is None:
            event.update(status="UNAVAILABLE", reason="DAY_REFERENCE_UNAVAILABLE")
            return
        equity, _, _, paused, _ = snapshot
        if equity <= 0 or paused:
            event["reason"] = "NONPOSITIVE_EQUITY" if equity <= 0 else "DAILY_PAUSE"
            return
        result = self.book.model._entry_at(event["request"], prices, fills.Event(quote.source, quote.sequence),
                                           targets)
        if result["status"] != "FILLED":
            event["reason"] = result["reason"]
            return
        sizing = risk._size(self.book.terms, snapshot, result)
        event["sizing"] = sizing
        if sizing["lots"] == "0":
            event["reason"] = "BELOW_MIN_LOT"
            return
        event.update(status="ADMITTED", reason="SIZED_QUOTE", reserved_at=quote.time)
        position = result["position"]
        self.position = fills.Position.from_record(position)
        if position["exit_model"] == "E1":
            self.protection = exits.Protection(event["safety_line_id"], self.registered, self.position)
            self.frame_index = bisect_right(self.frame_times, quote.source)
        mark = self._mark(quote, prices, position["direction"])
        self.book.open_trade(position, sizing, event["id"], mark)
        self.position_record = {"attempt_id": event["id"], "opening_quote": quote.record(),
                                "stop": position["initial_stop"], "target": position["target"],
                                "state": "OPEN", "release_at": None}
        self.positions.append(self.position_record)

    def finish(self):
        boundary = self.tape.calendar.end
        if self.position is None:
            if self.as_of >= boundary:
                self.book._roll(boundary - 1, boundary)
            return "AVAILABLE", None
        if self.fault is None:
            self._protect(min(self.as_of + 1, boundary))
            if self.as_of >= boundary:
                self._roll_held(boundary - 1, boundary)
        status = "UNAVAILABLE" if self.fault else "OPEN_AT_BOUNDARY" if self.as_of >= boundary else "OPEN"
        position = self.position.record()
        protection = self.protection
        self.position_record.update(state=status, protection_events=[] if protection is None else protection.events)
        liability = {"attempt_id": self.book.held["attempt_id"], "stop": position["stop"], "target": position["target"],
                     "reason": self.fault or ("MISSING_LIQUIDATION_QUOTE" if status == "OPEN_AT_BOUNDARY" else None),
                     "last_mark": self.book.mark, "lots": fills.text(self.book.held["lots"]),
                     "floating_usd": fills.text(self.book._floating()),
                     "unpaid_exit_commission_usd": fills.text(self.book.held["fee"]),
                     "mark_age_ms": min(self.as_of, boundary) - self.book.mark["time"]}
        return status, liability


def _account_replay(tape, prefix, report, as_of, cost):
    """Apply completed setup decisions to the visible quote observations."""
    runner = _Execution(tape, report, as_of, cost)
    quality, executable, candidate_quotes = Counter(), [], []
    previous = None
    for quote in prefix:
        eligibility = _quality(tape, quote, previous)
        quality[eligibility] += 1
        previous = quote
        if eligibility == "EXECUTABLE":
            executable.append(quote)
            if _prices(quote, runner.floor)[2] <= quotes.MAX_ENTRY_SPREAD:
                candidate_quotes.append(quote)
            else:
                quality["ENTRY_SPREAD_EXCEEDED"] += 1
    decisions, at_quote = _decisions(tape, report, candidate_quotes, as_of, cost)
    for quote in executable:
        runner.on_quote(quote, at_quote.get(quote.sequence))
    status, liability = runner.finish()
    return {"quote_quality": dict(quality), "decisions": decisions, "positions": runner.positions,
            "status": status, "account": runner.book._account(), "events": runner.book.events,
            "trades": runner.book.trades, "open_liability": liability}


def evaluate(tape, *, as_of, tick, profile="TRL_BRK3_E1", cost="base", enable_dly=False):
    if not isinstance(tape, quotes.Tape):
        raise ValueError("invented quote tape required")
    fills.decimal(tick, positive=True)
    bound = bindings()
    prefix = tuple(tape.prefix(as_of))
    publications = tape.publications(prefix, as_of)
    engine = breaks.BreakReplay(tape.geometry_source, tick, profile, enable_dly=enable_dly)
    frames = ("D1", "H4") if profile in (context.PROFILE, breaks.FXR_PROFILE) else ("H4",)
    for bar in publications:
        if bar.timeframe in frames:
            engine.observe(bar)
    report = engine.report(as_of=as_of)
    account = _account_replay(tape, prefix, report, as_of, cost)
    if bindings() != bound:
        raise ValueError("quote replay source bindings changed")
    return {"schema": VERSION, "kind": "invented_q_usd_ledger", "data_level": "Q", "geometry_basis": "mid_sync",
            "tape_sha256": tape.sha256, "source_bindings": bound, "as_of": as_of, "tick_size": tick,
            "profile": profile, "cost_profile": cost, "enable_dly": enable_dly,
            "liquidation_at": tape.liquidation, "partition_end": tape.calendar.end,
            "publications": [bar.record() for bar in publications], "setup_decisions": report["decisions"],
            **account, "actual_source_admitted": False,
            "market_cells_run": 0, "orders_available": False}


def checkpoint(report):
    return {key: report[key] for key in ("schema", "tape_sha256", "source_bindings", "as_of", "tick_size",
                                         "profile", "cost_profile", "enable_dly")} | {"state_sha256": data.digest(report)}


def restore(tape, record, *, as_of, tick, profile, cost, enable_dly):
    data.fields(record, ("schema", "tape_sha256", "source_bindings", "as_of", "tick_size", "profile",
                         "cost_profile", "enable_dly", "state_sha256"))
    data.integer(record["as_of"])
    if ((record["schema"], record["tape_sha256"], record["source_bindings"], record["tick_size"],
         record["profile"], record["cost_profile"], record["enable_dly"]) != (
            VERSION, tape.sha256, bindings(), tick, profile, cost, enable_dly)
            or record["as_of"] > as_of or type(record["enable_dly"]) is not bool):
        raise ValueError("quote checkpoint scope or prefix mismatch")
    settings = {"tick": tick, "profile": profile, "cost": cost, "enable_dly": enable_dly}
    prefix = evaluate(tape, as_of=record["as_of"], **settings)
    if record["state_sha256"] != data.digest(prefix):
        raise ValueError("quote checkpoint replay mismatch")
    return prefix if as_of == record["as_of"] else evaluate(tape, as_of=as_of, **settings)
