"""Receipt-aware USD accounting for an independent invented Level B replay."""
from bisect import bisect_left
from fractions import Fraction
import hashlib

from . import data, entries, exits, fills, geometry, risk

VERSION = "TRL_B_LEDGER_183_V1"


def bindings():
    result = risk.bindings()
    path = "src/forex_demo_lab/trendline/ledger.py"
    result[path] = hashlib.sha256((data.ROOT / path).read_bytes()).hexdigest()
    return result


class _Book:
    def __init__(self, source, hours, priced, exit_report):
        self.model = fills.PriceModel(source, priced["cost_profile"]["name"])
        self.terms = risk._terms(self.model.costs["name"])
        costs = risk._costs()
        profile, common = costs[self.model.costs["name"]], costs["common"]
        self.rates = {side: Fraction(str(profile[f"swap_{side.lower()}_usd_per_lot"]))
                      for side in ("LONG", "SHORT")}
        self.triple = common["triple_swap_weekday"]
        if common["rollover_timezone"] != "Etc/UTC":
            raise ValueError("UTC rollover terms required")
        self.initial = self.cash = Fraction(str(common["initial_equity_usd"]))
        calendar = source.calendar
        self.windows = calendar.frame("H1")
        self.starts = tuple(window.start for window in self.windows)
        self.hours = hours
        self.as_of = priced["as_of"]
        self.boundary = calendar.end
        self.through = min(self.as_of, self.boundary - 1)
        self.liquidation = exit_report["liquidation_at"]
        self.day = calendar.start // risk.UTC_DAY_MS
        self.reference, self.paused = self.initial, False
        self.held, self.mark, self.liability = None, None, None
        self.events, self.trades = [], []
        self.flat_confirmed_at = calendar.start
        self._post("DAY_REFERENCE", calendar.start, calendar.start)

    def _floating(self):
        if self.held is None:
            return Fraction(0)
        return self.held["sign"] * (Fraction(self.mark["price"]) - self.held["entry"]) * self.held["units"]

    def _equity(self):
        return self.cash + self._floating()

    def _latch(self):
        if self.reference is not None and self._equity() <= self.reference * risk.DAILY_FLOOR:
            self.paused = True

    def _account(self):
        equity = self._equity()
        margin = Fraction(0) if self.held is None else self.held["margin"]
        return {"cash_usd": fills.text(self.cash), "equity_usd": fills.text(equity),
                "margin_usd": geometry.rational_record(margin),
                "free_margin_usd": geometry.rational_record(equity - margin),
                "utc_day": self.day,
                "reference_equity_usd": None if self.reference is None else fills.text(self.reference),
                "entries_paused": self.paused}

    def _post(self, kind, at, available, **details):
        self._latch()
        self.events.append({"kind": kind, "effective_at": at, "available_at": max(at, available),
                            **details, "account": self._account()})

    def _roll(self, through, available, *, reconciled=True):
        next_day = min(through, self.through) // risk.UTC_DAY_MS
        while self.day < next_day:
            # 1970-01-01 was a Thursday, with Monday numbered zero.
            weekday = (self.day + 3) % 7
            self.day += 1
            at = self.day * risk.UTC_DAY_MS
            self.reference = self._equity() if reconciled and self._equity() > 0 else None
            self.paused = self.reference is None
            self._post("DAY_REFERENCE", at, available)
            if self.held is not None:
                multiplier = 0 if weekday >= 5 else 3 if weekday == self.triple else 1
                amount = self.rates[self.held["direction"]] * self.held["lots"] * multiplier
                self.held["financing"] += amount
                self.cash += amount
                self._post("FINANCING", at, available, attempt_id=self.held["attempt_id"],
                           weekday=weekday, multiplier=multiplier, amount_usd=fills.text(amount))

    def settle_unfilled(self, receipt):
        self.flat_confirmed_at = receipt

    def advance_flat(self, at):
        self._roll(at, max(self.flat_confirmed_at, self.events[-1]["available_at"]))

    def capital_at(self, opening):
        if self.held is not None:
            raise ValueError("position must reconcile before another entry")
        self.advance_flat(opening)
        if self.reference is None and self.cash > 0:
            return None
        floor = Fraction(0) if self.reference is None else self.reference * risk.DAILY_FLOOR
        return self.cash, self.cash, floor, self.paused, None

    def _observe(self, hour, *, opening=False, adverse=False):
        direction = self.held["direction"]
        mark = exits._mark(self.model, hour, direction, at_open=opening)
        if adverse:
            adverse_bid = hour.low if direction == "LONG" else hour.high
            mark["price"] = fills.text(Fraction(mark["price"]) - Fraction(hour.close) + Fraction(adverse_bid))
        observation = "H1_ADVERSE_RANGE" if adverse else "H1_OPEN" if opening else "H1_CLOSE"
        self.record_mark(mark, observation)

    def record_mark(self, mark, observation):
        self.mark = mark
        self._post("MARK", mark["time"], mark["available_at"], attempt_id=self.held["attempt_id"],
                   price=mark["price"], side=mark["side"],
                   observation=observation)

    def _close(self, path, hour):
        exit_fill = path["exit"]
        opening = exit_fill["event"] is not None
        self.close_trade(path["entry"], exit_fill, hour.start if opening else hour.end, hour.available_at)
        return path

    def close_trade(self, position, exit_fill, at, available):
        held = self.held
        price = Fraction(exit_fill["price"])
        gross = held["sign"] * (price - held["entry"]) * held["units"]
        fee = held["fee"]
        self.cash += gross - fee
        net = gross - 2 * fee + held["financing"]
        trade = {"attempt_id": held["attempt_id"], "direction": held["direction"],
                 "lots": fills.text(held["lots"]), "entry_price": fills.text(held["entry"]),
                 "exit_price": exit_fill["price"], "reason": exit_fill["reason"],
                 "entry_at": position["entry_at"], "exit_at": exit_fill["event"],
                 "exit_window": exit_fill["event_window"], "gross_usd": fills.text(gross),
                 "commission_usd": fills.text(2 * fee), "financing_usd": fills.text(held["financing"]),
                 "net_usd": fills.text(net), "estimated_stop_loss_usd": fills.text(held["risk"]),
                 "realized_loss_excess_usd": fills.text(max(0, -net - held["risk"]))}
        self.trades.append(trade)
        self.held, self.mark = None, None
        self._post("EXIT_FILL", at, available,
                   attempt_id=trade["attempt_id"], price=exit_fill["price"], fee_usd=fills.text(fee))

    def open_trade(self, position, sizing, attempt_id, mark):
        if self.held is not None:
            raise ValueError("account slot is occupied")
        start, direction = position["entry_at"]["time"], position["direction"]
        lots, entry = Fraction(sizing["lots"]), Fraction(position["entry_price"])
        units = lots * self.terms["contract_size"]
        fee = Fraction(sizing["estimated_entry_commission_usd"])
        self.held = {"attempt_id": attempt_id, "direction": direction,
                     "sign": 1 if direction == "LONG" else -1, "lots": lots, "units": units,
                     "entry": entry, "fee": fee, "margin": entry * units / self.terms["leverage"],
                     "risk": Fraction(sizing["estimated_stop_loss_usd"]), "financing": Fraction(0)}
        self.mark = mark
        self.cash -= fee
        self._post("ENTRY_FILL", start, mark["available_at"], attempt_id=attempt_id,
                   price=position["entry_price"], fee_usd=fills.text(fee), lots=sizing["lots"], mark=self.mark)

    def admit(self, path, sizing):
        position = path["entry"]
        start = position["entry_at"]["time"]
        mark = exits._mark(self.model, self.hours[start], position["direction"], at_open=True)
        self.open_trade(position, sizing, path["attempt_id"], mark)

        fill = path["exit"]
        closing_start = None if fill is None else (
            fill["event"]["time"] if fill["event"] is not None else fill["event_window"]["start"])
        last_close = path["last_mark"]["time"]
        for window in self.windows[bisect_left(self.starts, start):]:
            at = window.start
            if at != closing_start and window.end > last_close:
                self._roll(min(at, self.liquidation), self.mark["available_at"])
                break
            hour = self.hours[at]
            self._roll(at, self.mark["available_at"])
            closing = at == closing_start
            if closing and fill["event"] is not None:
                return self._close(path, hour)
            if at != start:
                self._observe(hour, opening=True)
            crosses_day = at // risk.UTC_DAY_MS != (hour.end - 1) // risk.UTC_DAY_MS
            if closing:
                if crosses_day:
                    path = {**path, "state": "UNAVAILABLE", "reason": "ROLLOVER_EXIT_ORDER_UNRESOLVED"}
                    break
                return self._close(path, hour)
            if crosses_day:
                self._roll(hour.end - 1, hour.available_at, reconciled=False)
            else:
                self._observe(hour, adverse=True)
            self._observe(hour)
            self._roll(hour.end, hour.available_at)

        self.liability = {"attempt_id": path["attempt_id"], "state": path["state"], "reason": path["reason"],
                          "direction": position["direction"], "lots": sizing["lots"],
                          "entry_price": position["entry_price"],
                          "stop": path["position"]["stop"], "target": path["position"]["target"],
                          "last_mark": self.mark, "floating_usd": fills.text(self._floating()),
                          "unpaid_exit_commission_usd": fills.text(self.held["fee"]),
                          "financing_usd": fills.text(self.held["financing"]),
                          "unmarked_ms": min(self.as_of, self.boundary) - self.mark["time"]}
        return path


def _evaluate(source, hours, priced, exit_report):
    bound = bindings()
    hourly = {hour.start: hour for hour in hours}
    book = _Book(source, hourly, priced, exit_report)
    decisions, positions, active = risk._timeline(priced, exit_report, hourly, book.capital_at, book.terms,
                                                  admit=book.admit, settle_unfilled=book.settle_unfilled)
    for row in decisions:
        if row["reason"] == "RISK_SNAPSHOT_UNAVAILABLE":
            row["reason"] = "DAY_REFERENCE_UNAVAILABLE"
    if active is None:
        book.advance_flat(book.through)
    basis = source.record()["geometry_basis"]
    status = "AVAILABLE" if basis == "bid_only" else "UNAVAILABLE"
    if book.liability is not None:
        status = book.liability["state"]
    elif active is not None:
        status = "RESERVED"
    if bindings() != bound:
        raise ValueError("account replay source bindings changed")
    return {"schema": VERSION, "kind": "invented_b_usd_ledger", "data_level": "B",
            "source_sha256": source.sha256, "source_bindings": bound, "profile": priced["profile"],
            "cost_profile": priced["cost_profile"]["name"], "as_of": priced["as_of"],
            "liquidation_at": book.liquidation, "initial_cash_usd": fills.text(book.initial),
            "status": status, "account": book._account(), "decisions": decisions,
            "positions": positions, "active": active, "events": book.events, "trades": book.trades,
            "open_liability": book.liability, "market_cells_run": 0, "orders_available": False}


def evaluate(replay, hours, *, as_of, cost_profile="base", liquidation_at=None):
    """Derive account state from an invented price and publication prefix."""
    priced = entries.evaluate(replay, hours, as_of=as_of, cost_profile=cost_profile)
    paths = exits._evaluate(replay, hours, priced, liquidation_at)
    return _evaluate(replay.source, hours, priced, paths)
