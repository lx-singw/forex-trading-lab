"""Independent rational Level Q accounting on invented tapes."""
from collections import Counter
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from fractions import Fraction as F
from math import ceil, floor
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from forex_demo_lab import daily_features_118, daily_fills_120, elliott_execution_125
from forex_demo_lab.daily_fills_fixture_120 import fixture as daily_fixture
from forex_demo_lab.elliott_execution_fixture_125 import fixture as elliott_fixture
from forex_demo_lab.trendline import quote_replay, quotes
from test_trendline_data_163 import calendar
from test_trendline_entries_174 import fixture
from test_trendline_ledger_183 import shift_calendar
from test_trendline_quotes_185 import document, history, midpoint, row

HOUR = 3_600_000
DAY = 24 * HOUR
TICK = F("0.0001")
CAPITAL = F(10000)
TERMS = {
    "base": (F("0.00002"), F(7), F(0), (F(-3), F("-1.5"))),
    "adverse": (F("0.00005"), F(10), F("0.00012"), (F("-4.5"), F("-2.25"))),
}


@dataclass(frozen=True)
class Opportunity:
    close: int
    published: int
    expiry: int
    side: int = 1
    stop: str = "1.0985"
    atr: str = "0.0016"
    levels: tuple = ("1.104",)


def h4_ends(cal):
    return [edge for segment in cal["segments"] if segment["kind"] == "session" for edge in segment["h4"][1:]]


def rational(value):
    return {"numerator": value.numerator, "denominator": value.denominator}


def constructed(tape, opportunities, as_of, cost, tick=TICK):
    """Supply already selected setup publications to the normal accounting path."""
    frames, decisions = [], []
    for i, signal in enumerate(opportunities):
        if signal.published > as_of:
            continue
        identity = f"fixture-{i}"
        frames.append({"id": identity, "bar": {"end": signal.close, "available": signal.published}})
        decisions.append({"state": "READY", "h4_frame_id": identity, "selected_line_id": identity,
                          "safety_frame_id": identity, "atr_sma14": rational(F(signal.atr)),
                          "direction": "LONG" if signal.side > 0 else "SHORT",
                          "safety": {"line_id": identity, "stop": rational(F(signal.stop)),
                                     "atr_sma14": rational(F(signal.atr))},
                          "target_levels": {"clusters": [
                              {"kind": "high" if signal.side > 0 else "low", "eligible": True,
                               "price": rational(F(level))} for level in signal.levels]}})
    report = {"tick": rational(tick), "safety_replay": {"frames": [], "journal": {"lines": []}},
              "action_replay": {"profile": "TRL_FXR_M", "frames": frames}, "decisions": decisions}
    return quote_replay._account_replay(tape, tuple(tape.prefix(as_of)), report, as_of, cost)


def oracle(value, opportunities, as_of, cost, tick=TICK):
    """Fold independent fixture facts into the expected account and receipt events."""
    slip, fee_per_lot, spread_floor, swaps = TERMS[cost]
    start, end = (value["calendar"]["scope"][key] for key in ("start", "end"))
    liquidation = value["liquidation_at"]
    sessions = [s for s in value["calendar"]["segments"] if s["kind"] == "session"]
    day, reference, paused = start // DAY, CAPITAL, False
    cash, held, mark, fault = CAPITAL, None, None, None
    events, trades, positions = [], [], []
    quality = Counter()
    signals = [s for s in opportunities if s.published <= as_of]
    decisions = [{"sequence": None, "status": "PENDING", "reason": "AWAITING_ELIGIBLE_QUOTE"}
                 for signal in signals]

    def session(at):
        return next((s for s in sessions if s["start"] <= at < s["end"]), None)

    def account():
        margin, floating = (F(0), F(0)) if held is None else (
            held["lots"] * held["entry"] * F(100000, 30),
            held["side"] * (mark["price"] - held["entry"]) * held["lots"] * 100000)
        equity = cash + floating
        return {"cash_usd": cash, "equity_usd": equity, "margin_usd": margin,
                "free_margin_usd": equity - margin, "utc_day": day,
                "reference_equity_usd": reference, "entries_paused": paused}

    def post(kind, effective, received, **details):
        nonlocal paused
        paused = paused or (reference is not None and account()["equity_usd"] <= reference * F("0.99"))
        events.append({"kind": kind, "effective_at": effective, "available_at": max(effective, received),
                       "account": account(), **details})

    def roll(through, received):
        nonlocal day, reference, paused, cash
        for new_day in range(day + 1, min(through, end - 1) // DAY + 1):
            at = new_day * DAY
            carried = account()["equity_usd"]
            valid = held is None or at - mark["time"] <= 2000
            if not valid:
                closing = session(mark["time"])["end"]
                following = min((s["start"] for s in sessions if s["start"] >= closing), default=end)
                valid = closing <= at <= following and closing - mark["time"] <= 2000
            day, reference = new_day, carried if valid and carried > 0 else None
            paused = reference is None
            post("DAY_REFERENCE", at, received)
            if held is not None:
                weekday = datetime.fromtimestamp((at - DAY) // 1000, timezone.utc).weekday()
                multiple = (1, 1, 3, 1, 1, 0, 0)[weekday]
                debit = swaps[0 if held["side"] > 0 else 1] * held["lots"] * multiple
                cash += debit
                held["financing"] += debit
                post("FINANCING", at, received, weekday=weekday, multiplier=multiple, amount_usd=debit)

    post("DAY_REFERENCE", start, start)
    previous = None
    for quote in value["quotes"]:
        at, receipt, sequence = (quote[k] for k in ("source_at", "received_at", "sequence"))
        if receipt > as_of:
            break
        bid, raw_ask = F(quote["bid"]), F(quote["ask"])
        current = at, bid, raw_ask
        if receipt >= end:
            quality["OUTSIDE_PARTITION"] += 1
        elif session(at) is None or session(at) != session(receipt):
            quality["OUTSIDE_SESSION"] += 1
        elif receipt - at > 2000:
            quality["STALE_QUOTE"] += 1
        elif current == previous:
            quality["REPEATED_QUOTE"] += 1
        else:
            quality["EXECUTABLE"] += 1
            ask = max(raw_ask, bid + spread_floor)
            spread = ask - bid
            occupied = held is not None
            if not occupied:
                roll(at, receipt)
            elif fault is None:
                roll(at, receipt)
                side = held["side"]
                price = bid if side > 0 else ask
                stop_reached = side * (price - held["stop"]) <= 0
                target_reached = held["target"] is not None and side * (price - held["target"]) >= 0
                reason = ("STOP_QUOTE" if stop_reached else "TARGET_QUOTE" if target_reached
                          else "PARTITION_LIQUIDATION" if at >= liquidation else None)
                if reason is None:
                    mark = {"time": at, "available_at": receipt, "sequence": sequence,
                            "price": price, "side": "BID" if side > 0 else "ASK"}
                    post("MARK", at, receipt, price=price, side=mark["side"], observation="EXECUTABLE_QUOTE")
                else:
                    exit_price = held["target"] if reason == "TARGET_QUOTE" else price - side * slip
                    if exit_price <= 0:
                        fault = "NONPOSITIVE_EXIT_MODEL"
                    else:
                        gross = side * (exit_price - held["entry"]) * 100000 * held["lots"]
                        net = gross - 2 * held["fee"] + held["financing"]
                        cash += gross - held["fee"]
                        trades.append({"entry_price": held["entry"], "exit_price": exit_price, "lots": held["lots"],
                                       "entry_at": held["event"], "exit_at": {"time": at, "ordinal": sequence},
                                       "reason": reason, "gross_usd": gross, "commission_usd": 2 * held["fee"],
                                       "financing_usd": held["financing"], "net_usd": net,
                                       "estimated_stop_loss_usd": held["estimate"],
                                       "realized_loss_excess_usd": max(F(0), -net - held["estimate"])})
                        closing_fee = held["fee"]
                        held, mark = None, None
                        positions[-1].update(state="CLOSED", closing_sequence=sequence, release_at=receipt)
                        post("EXIT_FILL", at, receipt, price=exit_price, fee_usd=closing_fee)
            if spread > F("0.00015"):
                quality["ENTRY_SPREAD_EXCEEDED"] += 1
            else:
                for signal, decision in zip(signals, decisions, strict=True):
                    if (decision["sequence"] is not None or at <= signal.published
                            or receipt >= min(signal.expiry, liquidation)):
                        continue
                    decision.update(sequence=sequence, status="SKIPPED")
                    if occupied:
                        decision["reason"] = "POSITION_LIMIT"
                        continue
                    if cash <= 0:
                        decision["reason"] = "NONPOSITIVE_EQUITY"
                    elif reference is None:
                        decision.update(status="UNAVAILABLE", reason="DAY_REFERENCE_UNAVAILABLE")
                    elif paused:
                        decision["reason"] = "DAILY_PAUSE"
                    else:
                        side = signal.side
                        entry = ask + slip if side > 0 else bid - slip
                        mark_price = bid if side > 0 else ask
                        stop = (floor if side > 0 else ceil)(F(signal.stop) / tick) * tick
                        distance = side * (entry - stop)
                        levels = [(floor if side > 0 else ceil)(F(level) / tick) * tick for level in signal.levels]
                        target = next((level for level in sorted(levels, reverse=side < 0)
                                       if side * (level - entry) >= 2 * distance), None)
                        if side * (mark_price - stop) <= 0:
                            decision["reason"] = "STOP_ALREADY_CROSSED"
                        elif entry <= 0:
                            decision["reason"] = "NONPOSITIVE_ENTRY"
                        elif not F(signal.atr) / 2 <= distance <= F(signal.atr) * F("2.5"):
                            decision["reason"] = "STOP_OUT_OF_WINDOW"
                        elif spread * 10 > distance:
                            decision["reason"] = "SPREAD_TOO_WIDE"
                        elif signal.levels and target is None:
                            decision["reason"] = "NO_VALID_TARGET"
                        else:
                            loss = (distance + slip) * 100000 + fee_per_lot
                            margin = entry * F(100000, 30)
                            risk_budget = cash / 400
                            lots = F(floor(100 * min(F(1), risk_budget / loss, cash / (margin + fee_per_lot / 2),
                                                     (cash - reference * F("0.99")) / loss)), 100)
                            decision.update(lots=lots, risk_budget_usd=risk_budget)
                            if lots == 0:
                                decision["reason"] = "BELOW_MIN_LOT"
                            else:
                                half_fee = lots * fee_per_lot / 2
                                cash -= half_fee
                                held = {"side": side, "entry": entry, "fee": half_fee, "lots": lots,
                                        "stop": stop, "target": target, "financing": F(0), "estimate": loss * lots,
                                        "event": {"time": at, "ordinal": sequence}}
                                mark = {"time": at, "available_at": receipt, "sequence": sequence,
                                        "price": mark_price, "side": "BID" if side > 0 else "ASK"}
                                post("ENTRY_FILL", at, receipt, price=entry, fee_usd=half_fee, lots=lots, mark=mark)
                                positions.append({"opening_sequence": sequence, "closing_sequence": None,
                                                  "state": "OPEN", "stop": stop, "target": target, "release_at": None})
                                decision.update(status="ADMITTED", reason="SIZED_QUOTE", reserved_at=receipt)
        previous = current

    for signal, decision in zip(signals, decisions, strict=True):
        if decision["sequence"] is not None:
            continue
        deadline = min(signal.expiry, liquidation)
        if signal.published >= signal.expiry:
            decision.update(status="EXPIRED", reason="ENTRY_WINDOW_EXPIRED")
        elif as_of >= deadline:
            decision.update(status="EXPIRED", reason="ENTRY_AT_LIQUIDATION" if deadline == liquidation
                            else "NO_ELIGIBLE_QUOTE")
    if as_of >= end and fault is None:
        roll(end - 1, end)
    status, liability = "AVAILABLE", None
    if held is not None:
        status = "UNAVAILABLE" if fault else "OPEN_AT_BOUNDARY" if as_of >= end else "OPEN"
        positions[-1]["state"] = status
        liability = {"reason": fault or ("MISSING_LIQUIDATION_QUOTE" if as_of >= end else None),
                     "stop": held["stop"], "target": held["target"], "last_mark": mark, "lots": held["lots"],
                     "floating_usd": account()["equity_usd"] - cash, "unpaid_exit_commission_usd": held["fee"],
                     "mark_age_ms": min(as_of, end) - mark["time"]}
    return {"status": status, "account": account(), "events": events, "trades": trades,
            "positions": positions, "decisions": decisions, "open_liability": liability,
            "quote_quality": dict(quality)}


class QuoteAcceptanceTests(unittest.TestCase):
    def same(self, expected, actual):
        if isinstance(expected, F):
            if isinstance(actual, dict):
                actual = F(actual["numerator"], actual["denominator"])
            else:
                actual = F(actual)
        elif isinstance(expected, list):
            self.assertEqual(len(expected), len(actual))
            for left, right in zip(expected, actual, strict=True):
                self.same(left, right)
            return
        elif isinstance(expected, dict):
            for key in expected:
                with self.subTest(field=key):
                    self.same(expected[key], actual[key])
            return
        self.assertEqual(expected, actual)

    def reconcile(self, value, signals, as_of, cost, actual=None, tick=TICK):
        if actual is None:
            actual = constructed(quotes.Tape(value), signals, as_of, cost, tick)
        expected = oracle(value, signals, as_of, cost, tick)
        self.assertEqual(expected["quote_quality"], actual["quote_quality"])
        for key in ("status", "account", "events", "trades", "open_liability"):
            with self.subTest(section=key):
                self.same(expected[key], actual[key])
        decisions = [{**v, "sequence": v.get("quote", {}).get("sequence"), **v.get("sizing", {})}
                     for v in actual["decisions"]]
        positions = [{**p, "opening_sequence": p["opening_quote"]["sequence"],
                      "closing_sequence": p.get("closing_quote", {}).get("sequence")} for p in actual["positions"]]
        self.same(expected["decisions"], decisions)
        self.same(expected["positions"], positions)
        return actual

    def test_entry_clocks_e2_limit_sequence_and_quality(self):
        cal = calendar()
        trigger, deadline = h4_ends(cal)[:2]
        at = trigger + 10
        signal = Opportunity(trigger, at, deadline, levels=("1.101", "1.104"))
        rows = [row(at - 1, "1.1", "1.1001", at + 1), row(at, "1.1", "1.1001", at + 1),
                row(at + 1, "1.1", "1.1001", at + 2002),
                row(at + 2, "1.1", "1.10016", at + 2002),
                row(at + 3, "1.1", "1.10015", at + 2003),
                row(at + 3, "1.1", "1.10015", at + 2003),
                row(at + 3, "1.103", "1.10305", at + 2003),
                row(at + 3, "1.105", "1.10505", at + 2003),
                row(at + 4, "1.098", "1.09805", at + 2004)]
        value = document({"calendar": cal}, rows)
        for cost in TERMS:
            with self.subTest(cost=cost):
                result = self.reconcile(value, [signal], at + 2004, cost)
                [trade] = result["trades"]
                self.assertEqual((5, 8, "1.104", "TARGET_QUOTE"),
                                 (trade["entry_at"]["ordinal"], trade["exit_at"]["ordinal"],
                                  trade["exit_price"], trade["reason"]))

    def test_capacity_gap_pause_and_next_day_account_sizing(self):
        cal = calendar((24, 24))
        closes = h4_ends(cal)
        first, second, third, next_day = (closes[i] for i in (0, 1, 2, 6))
        signals = [Opportunity(first, first, closes[1], -1, "1.1015", "0.0016", ("1.095",)),
                   Opportunity(second, second, closes[2]),
                   Opportunity(third, third, closes[3]),
                   Opportunity(next_day, next_day, closes[7])]
        rows = [row(first + 1, "1.1", "1.1001"), row(second + 2, "1.13", "1.1301"),
                row(third + 1, "1.1", "1.1001"), row(next_day + 1, "1.1", "1.1001"),
                row(next_day + 2, "1.105", "1.1051")]
        value = document({"calendar": cal}, rows)
        result = self.reconcile(value, signals, next_day + 2, "base")
        self.assertEqual(["SIZED_QUOTE", "POSITION_LIMIT", "DAILY_PAUSE", "SIZED_QUOTE"],
                         [d["reason"] for d in result["decisions"]])
        decisions = result["decisions"]
        self.assertLess(F(decisions[-1]["sizing"]["risk_budget_usd"]), F(decisions[0]["sizing"]["risk_budget_usd"]))
        self.assertGreater(F(result["trades"][0]["realized_loss_excess_usd"]), 100)

    def test_closure_rolls_liquidation_and_boundary_liability(self):
        cal = shift_calendar(calendar((4, 8), (96,), partial=True), 94 * HOUR)
        # Prepend a complete H4 slot before the entry decision.
        first_start = cal["scope"]["start"]
        first_session = cal["segments"][0]
        first_session["start"] -= 4 * HOUR
        first_session["h1"] = list(range(first_session["start"], first_session["end"], HOUR)) + [first_session["end"]]
        first_session["h4"].insert(0, first_session["start"])
        cal["scope"]["start"] = first_session["start"]
        closure = first_session["end"]
        reopen = cal["segments"][2]["start"]
        end = cal["scope"]["end"]
        signal = Opportunity(first_start, first_start, closure, -1, "1.1015", "0.0015", ("1.095",))
        rows = [row(closure - 1000, "1.0995", "1.09952"),
                row(closure + 1, "1.12", "1.1201"),
                row(reopen + 9, "1.0995", "1.09952", reopen + 11),
                row(end - 1, "1.105", "1.1051", end)]
        for cost in TERMS:
            for has_close in (False, True):
                with self.subTest(cost=cost, closing_observation=has_close):
                    observed = rows if not has_close else rows[:-1] + [
                        row(reopen + 12, "1.0995", "1.09952"), rows[-1]]
                    value = document({"calendar": cal}, observed, reopen + 10)
                    result = self.reconcile(value, [signal], end, cost)
                    self.assertEqual([3, 1, 1, 0, 0],
                                     [e["multiplier"] for e in result["events"] if e["kind"] == "FINANCING"])
                    if has_close:
                        self.assertEqual(reopen + 12, result["trades"][0]["exit_at"]["time"])
                    else:
                        self.assertEqual("OPEN_AT_BOUNDARY", result["status"])
                        self.assertEqual(reopen + 9, result["open_liability"]["last_mark"]["time"])

    def test_missing_daily_reference_blocks_until_next_reconciled_day(self):
        cal = shift_calendar(calendar((24, 24, 24)), 2 * HOUR)
        closes = h4_ends(cal)
        initial, midnight, later, following = (closes[i] for i in (0, 5, 6, 11))
        signals = [Opportunity(initial, initial, closes[1]),
                   Opportunity(later, later, closes[7]),
                   Opportunity(following, following, closes[12])]
        rows = [row(initial + 1, "1.1", "1.1001"), row(midnight + 1, "1.104", "1.1041"),
                row(later + 1, "1.1", "1.1001"), row(following + 1, "1.1", "1.1001")]
        result = self.reconcile(document({"calendar": cal}, rows), signals, following + 1, "base")
        self.assertEqual(["SIZED_QUOTE", "DAY_REFERENCE_UNAVAILABLE", "SIZED_QUOTE"],
                         [d["reason"] for d in result["decisions"]])

    def test_floating_pause_latches_after_same_day_recovery(self):
        cal = shift_calendar(calendar((24, 24)), 2 * HOUR)
        closes = h4_ends(cal)
        initial, midnight = closes[0], closes[5]
        signal = Opportunity(initial, initial, closes[1], levels=("1.2",))
        rows = [row(initial + 1, "1.1", "1.1001"), row(midnight - 1000, "1.112", "1.1121"),
                row(midnight + 1, "1.1004", "1.1005"), row(midnight + 2, "1.112", "1.1121"),
                row(midnight + 251, "1.112", "1.1121")]
        value = document({"calendar": cal}, rows, midnight + 250)
        result = self.reconcile(value, [signal], midnight + 251, "base")
        recovery = next(e for e in result["events"] if e["kind"] == "MARK" and e["effective_at"] == midnight + 2)
        self.assertTrue(recovery["account"]["entries_paused"])
        self.assertGreater(F(recovery["account"]["equity_usd"]),
                           F(recovery["account"]["reference_equity_usd"]) * F("0.99"))
        self.assertEqual("PARTITION_LIQUIDATION", result["trades"][0]["reason"])

    def test_idle_day_reference_is_published_on_the_advancing_receipt(self):
        cal = calendar((24, 24))
        midnight = (cal["scope"]["start"] // DAY + 1) * DAY
        late = midnight + 600
        rows = [row(midnight - 5, "1.1", "1.1001"), row(midnight + 1, "1.1", "1.1001", late)]
        value = document({"calendar": cal}, rows)
        prior = self.reconcile(value, [], late - 1, "base")
        observed = self.reconcile(value, [], late, "base")
        self.assertEqual(prior["events"], observed["events"][:-1])
        boundary = observed["events"][-1]
        self.assertEqual(("DAY_REFERENCE", midnight, late),
                         (boundary["kind"], boundary["effective_at"], boundary["available_at"]))

    def test_minimum_lot_expiry_and_nonpositive_exit(self):
        cal = calendar()
        trigger, next_close, expiry = h4_ends(cal)[:3]
        signals = [Opportunity(trigger, trigger, next_close, stop="1.05", atr="0.05", levels=("1.21",)),
                   Opportunity(next_close, next_close, expiry)]
        rows = [row(trigger + 1, "1.1", "1.1001"), row(trigger + 2, "1.06", "1.0601"),
                row(expiry - 1, "1.1", "1.1001", expiry), row(expiry + 1, "1.1", "1.1001")]
        result = self.reconcile(document({"calendar": cal}, rows), signals, expiry + 1, "base")
        self.assertEqual(["BELOW_MIN_LOT", "NO_ELIGIBLE_QUOTE"], [d["reason"] for d in result["decisions"]])
        signal = Opportunity(trigger, trigger, next_close, stop="0.0001", atr="0.0002", levels=("0.0008",))
        rows = [row(trigger + 1, "0.0003", "0.00031"), row(trigger + 2, "0.00001", "0.00002"),
                row(trigger + 3, "0.00008", "0.00009"), row(trigger + 4, "0.001", "0.00101")]
        result = self.reconcile(document({"calendar": cal}, rows), [signal], trigger + 4, "base")
        self.assertEqual("NONPOSITIVE_EXIT_MODEL", result["open_liability"]["reason"])
        self.assertEqual([], result["trades"])

    def test_full_midpoint_strategy_restart_and_suffix_causality(self):
        original, hours = fixture()
        trigger = hours[-1]["end"]
        fixture_rows = history(hours) + [
            midpoint(trigger + 1, "104.4"), midpoint(trigger + 2, "103.8"), midpoint(trigger + 3, "102")]
        value = document(original, fixture_rows)
        tape = quotes.Tape(value)
        settings = {"tick": "0.0001", "profile": "TRL_BRK3_E1", "cost": "base", "enable_dly": False}
        signal = Opportunity(trigger, trigger, trigger + 4 * HOUR, stop="1.1026", atr="0.00188", levels=())
        # An already selected opportunity reaches each later stage once.
        before, held, closed = [quote_replay.evaluate(tape, as_of=at, **settings)
                                for at in (trigger, trigger + 2, trigger + 3)]
        for report in (before, held, closed):
            self.reconcile(value, [signal], report["as_of"], "base", actual=report)
        for report in (before, held, closed):
            self.assertEqual(report["events"], [e for e in closed["events"] if e["available_at"] <= report["as_of"]])
        altered = deepcopy(value)
        altered["quotes"][-1].update(bid="1.104", ask="1.1041")
        prior = quote_replay.evaluate(quotes.Tape(altered), as_of=trigger + 2, **settings)
        self.assertNotEqual(held["tape_sha256"], prior["tape_sha256"])
        self.assertEqual({k: v for k, v in held.items() if k != "tape_sha256"},
                         {k: v for k, v in prior.items() if k != "tape_sha256"})
        checkpoint = quote_replay.checkpoint(held)
        self.assertEqual(closed, quote_replay.restore(tape, checkpoint, as_of=trigger + 3, **settings))
        self.assertEqual(closed, quote_replay.restore(tape, quote_replay.checkpoint(closed),
                                                    as_of=trigger + 3, **settings))
        corrupted = {**held, "account": {**held["account"], "cash_usd": "10000"}}
        with self.assertRaisesRegex(ValueError, "replay mismatch"):
            quote_replay.restore(tape, quote_replay.checkpoint(corrupted), as_of=trigger + 3, **settings)
        with self.assertRaisesRegex(ValueError, "scope or prefix mismatch"):
            quote_replay.restore(tape, checkpoint, as_of=trigger + 1, **settings)

    def test_retained_120_and_125_quotes_match_direct_accounting(self):
        for sprint, case in ((120, "long_target"), (125, "short_gap")):
            with TemporaryDirectory() as directory:
                home = Path(directory)
                if sprint == 120:
                    raw, manifest = home / "input.json", home / "freeze.json"
                    daily_features_118.write_new(raw, daily_fixture(case))
                    daily_fills_120.freeze_fixture(raw, manifest)
                    retained = daily_fills_120.Replay
                else:
                    value = elliott_execution_125.validate_fixture(elliott_fixture(case))
                    elliott_execution_125.prepare_partition(value, value["partitions"][0], home)
                    raw, manifest = home / "compiled-input.json", home / "compiled-frozen.json"
                    retained = elliott_execution_125.Account
                for cost in TERMS:
                    with self.subTest(sprint=sprint, cost=cost):
                        old = retained(raw, manifest, cost)
                        old.run()
                        self.compare_retained_quotes(old, sprint, cost)

    def compare_retained_quotes(self, old, sprint, cost):
        state = old.state
        [proposal] = [o["proposal"] for o in state["outcomes"] if o["proposal"] is not None]
        [closing] = [r for r in state["ledger"] if r["kind"] == "exit_fill"]
        observed = old._fixture["events"][proposal["sequence"]:closing["sequence"] + 1]
        self.assertTrue(all(state["outcomes"][q["sequence"]]["execution_quote"] for q in observed))
        first = observed[0]["source_msc"] // DAY * DAY
        end = (observed[-1]["source_msc"] // DAY + 1) * DAY
        start = first - HOUR
        segments = [{"kind": "session", "start": start, "end": first, "label": "session_prior",
                     "partial": True, "h1": [start, first], "h4": [start, first]}]
        legacy = old._fixture["features"]["calendar"] if sprint == 120 else old._fixture["calendar"]
        for original in legacy["sessions"]:
            a, b = original["start_msc"], original["end_msc"]
            if first <= a < end:
                if original["status"] == "closure":
                    segments.append({"kind": "closure", "start": a, "end": b, "reason": "weekend"})
                else:
                    segments.append({"kind": "session", "start": a, "end": b, "label": f"session_{len(segments)}",
                                     "partial": False, "h1": list(range(a, b + 1, HOUR)),
                                     "h4": list(range(a, b + 1, 4 * HOUR))})
        cal = {"kind": "invented_session_calendar_146", "scope": {"start": start, "end": end},
               "segments": segments, "finalization_delay_ms": 0}
        rows = [row(q["source_msc"], str(q["bid"]), str(q["ask"]), q["receipt_msc"]) for q in observed]
        stop = proposal["stop"]
        distance = str(abs(Decimal(proposal["entry"]) - Decimal(stop)))
        signal = Opportunity(first, first, first + 4 * HOUR, proposal["side"], stop, distance,
                             (proposal["target"],))
        value = document({"calendar": cal}, rows)
        result = self.reconcile(value, [signal], rows[-1]["received_at"], cost, tick=F("0.0000000000000000001"))
        [trade] = result["trades"]
        for current, previous in (("exit_price", "price"), ("lots", "lots"), ("gross_usd", "gross_usd"),
                                  ("financing_usd", "financing_usd"), ("net_usd", "net_trade_usd")):
            self.assertEqual(F(trade[current]), F(closing[previous]), current)
        self.assertEqual(F(trade["entry_price"]), F(proposal["entry"]))
        self.assertEqual(F(result["account"]["cash_usd"]), F(state["balance_usd"]))
        self.assertEqual(result["account"]["entries_paused"], state["outcomes"][closing["sequence"]]["paused"])
