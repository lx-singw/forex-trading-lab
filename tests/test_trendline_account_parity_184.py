"""Independent accounting comparison on selected retained invented cases."""
from collections import Counter
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
from fractions import Fraction as F
from pathlib import Path
import tempfile
import unittest

from forex_demo_lab import daily_features_118 as daily, daily_fills_120 as retained_daily
from forex_demo_lab import elliott_execution_125 as retained_elliott
from forex_demo_lab.daily_fills_fixture_120 import fixture as daily_fixture
from forex_demo_lab.elliott_execution_fixture_125 import fixture as elliott_fixture
from forex_demo_lab.trendline import data, exits, fills, ledger
from test_trendline_data_163 import descriptor

HOUR = 3_600_000
DAY = HOUR * 24
SATURDAY = 946684800000 // DAY
START_CASH = F(10000)
CONTRACT = 100000
COSTS = {
    "base": (F("0.00002"), F(7), F(0), {1: F(-3), -1: F("-1.5")}),
    "adverse": (F("0.00005"), F(10), F("0.00012"), {1: F("-4.5"), -1: F("-2.25")}),
}
DIRECTIONAL = ("long_target", "short_target", "long_stop", "short_stop", "long_gap", "short_gap")


@dataclass(frozen=True)
class Observation:
    sequence: int
    opening: int
    bid: F
    ask: F

    @property
    def receipt(self):
        return self.opening + HOUR


def project(events):
    """Give each retained executable observation an invented one-hour slot."""
    first_day = events[0]["source_msc"] // DAY
    start_day = SATURDAY + (first_day - SATURDAY) % 7
    counts = Counter()
    observations = []
    for event in events:
        source_day = event["source_msc"] // DAY
        at = (start_day + source_day - first_day) * DAY + (4 + counts[source_day]) * HOUR
        counts[source_day] += 1
        observations.append(Observation(event["sequence"], at, F(str(event["bid"])), F(str(event["ask"]))))
    start = observations[0].opening - HOUR
    segments = []
    cursor = start
    for opening in (start, *(q.opening for q in observations), observations[-1].receipt):
        if opening < cursor:
            raise ValueError("projected openings overlap")
        if opening > cursor:
            segments.append({"kind": "closure", "start": cursor, "end": opening, "reason": "invented"})
        end = opening + HOUR
        segments.append({"kind": "session", "label": f"session_{len(segments)}", "start": opening,
                         "end": end, "partial": True, "h1": [opening, end], "h4": [opening, end]})
        cursor = end
    cal = {"kind": "invented_session_calendar_146", "scope": {"start": start, "end": cursor},
           "finalization_delay_ms": 0, "segments": segments}
    return data.Declaration.from_record(descriptor(cal)), observations


def replay_projection(source, quotes, proposal, profile, boundary, competing=()):
    model = fills.PriceModel(source, profile)
    hours = {q.opening: data.Hour.from_record({
        "start": q.opening, "end": q.receipt, "available_at": q.receipt,
        **dict.fromkeys(("open", "high", "low", "close"), fills.text(q.bid)),
        "spread_pips": fills.text((q.ask - q.bid) * 10000),
    }, "bid_only") for q in quotes}
    windows = source.calendar.frame("H1")
    as_of = quotes[-1].receipt
    liquidation = quotes[-1].opening if boundary else as_of
    attempts, paths = [], []
    for quote in quotes:
        if quote is not quotes[0] and quote.sequence not in competing:
            continue
        trigger = max(w.end for w in windows if w.end <= quote.opening)
        request = {"kind": "invented_b_price_request", "direction": "LONG" if proposal["side"] == 1 else "SHORT",
                   "trigger_end": trigger, "decision_at": {"time": trigger, "ordinal": 0},
                   "atr": fills.text(abs(F(proposal["entry"]) - F(proposal["stop"]))),
                   "tick": "0.0000000000000000001", "stop": proposal["stop"], "target": proposal["target"],
                   "exit_model": "E2"}
        fill = model.entry(request, fills.Opening.from_hour(hours[quote.opening], 1))
        attempt = {"id": str(quote.sequence), "first_scheduled_open": quote.opening, "expires_at": quote.receipt,
                   "status": fill["status"], "reason": fill["reason"], "price_result": fill}
        attempts.append(attempt)
        if fill["status"] == "FILLED":
            paths.append(exits._path(model, [w for w in windows if w.start >= quote.opening], hours, as_of,
                                     source.calendar.end, liquidation, attempt, (), {}))
    priced = {"profile": "TRL_FXR_M", "cost_profile": model.costs, "as_of": as_of, "attempts": attempts}
    return ledger._evaluate(source, tuple(hours.values()), priced, {"paths": paths, "liquidation_at": liquidation})


def fraction(value):
    return F(value["numerator"], value["denominator"]) if isinstance(value, dict) else F(value)


def pause_at_close(retained):
    closed, = [row for row in retained["ledger"] if row["kind"] == "exit_fill"]
    if closed["reason"] == "boundary":
        return retained["paused"]
    return retained["outcomes"][closed["sequence"]]["paused"]


def audit(test, report, source, quotes, proposed, profile, boundary):
    """Rebuild every projected account observation with independent exact arithmetic."""
    slip, commission, floor, rates = COSTS[profile]
    side = proposed["side"]
    first = quotes[0]
    effective_spread = max(first.ask - first.bid, floor)
    entry = first.bid + (effective_spread + slip if side > 0 else -slip)
    stop, target = F(proposed["stop"]), F(proposed["target"])
    per_lot = (side * (entry - stop) + slip) * CONTRACT + commission
    margin_per_lot = entry * CONTRACT / 30
    raw_lots = min(F(25) / per_lot, START_CASH / (margin_per_lot + commission / 2), F(1))
    lots = F(raw_lots * 100 // 1, 100)
    fee = lots * commission / 2
    margin = lots * margin_per_lot
    cash, swaps, mark = START_CASH, F(0), None
    reference, paused, utc_day = START_CASH, False, source.calendar.start // DAY
    expected, by_sequence = [], {}

    def value():
        return cash if mark is None else cash + side * (mark - entry) * lots * CONTRACT

    def add(kind, at, receipt, **details):
        nonlocal paused
        equity = value()
        used_margin = F(0) if mark is None else margin
        paused = paused or equity <= reference * F("0.99")
        account = {"cash_usd": cash, "equity_usd": equity, "margin_usd": used_margin,
                   "free_margin_usd": equity - used_margin, "utc_day": utc_day,
                   "reference_equity_usd": reference, "entries_paused": paused}
        expected.append((kind, at, receipt, account, details))
        return account

    add("DAY_REFERENCE", source.calendar.start, source.calendar.start)
    exit_result = None
    for quotation in quotes:
        while utc_day < quotation.opening // DAY:
            weekday = datetime.fromtimestamp(utc_day * DAY // 1000, timezone.utc).weekday()
            utc_day += 1
            at = utc_day * DAY
            reference, paused = value(), False
            add("DAY_REFERENCE", at, at)
            multiple = [1, 1, 3, 1, 1, 0, 0][weekday]
            charge = lots * rates[side] * multiple
            swaps += charge
            cash += charge
            add("FINANCING", at, at, weekday=weekday, multiplier=multiple, amount_usd=charge)
        at, receipt = quotation.opening, quotation.receipt
        bid, ask = quotation.bid, max(quotation.ask, quotation.bid + floor)
        exit_side = bid if side > 0 else ask
        if quotation is first:
            cash -= fee
            mark = exit_side
            add("ENTRY_FILL", at, receipt, price=entry, lots=lots, fee_usd=fee)
        else:
            stop_hit = (exit_side - stop) * side <= 0
            target_hit = (exit_side - target) * side >= 0
            if stop_hit or target_hit or (boundary and quotation is quotes[-1]):
                exit_price = target if target_hit else exit_side - side * slip
                reason = "STOP_OPEN_GAP" if stop_hit else "TARGET_OPEN_REACH" if target_hit else "SCHEDULED_OPEN_EXIT"
                gross = side * (exit_price - entry) * lots * CONTRACT
                net = gross - 2 * fee + swaps
                cash += gross - fee
                mark = None
                add("EXIT_FILL", at, receipt, price=exit_price, fee_usd=fee)
                exit_result = {"entry_price": entry, "exit_price": exit_price, "lots": lots, "gross_usd": gross,
                               "commission_usd": 2 * fee, "financing_usd": swaps, "net_usd": net,
                               "estimated_stop_loss_usd": lots * per_lot,
                               "realized_loss_excess_usd": max(F(0), -net - lots * per_lot)}
                test.assertEqual(reason, report["trades"][0]["reason"])
                test.assertEqual(quotation.sequence, quotes[-1].sequence)
                break
            mark = exit_side
            add("MARK", at, receipt, price=mark, observation="H1_OPEN")
        add("MARK", receipt, receipt, price=mark, observation="H1_ADVERSE_RANGE")
        by_sequence[quotation.sequence] = add("MARK", receipt, receipt, price=mark, observation="H1_CLOSE")

    test.assertIsNotNone(exit_result)
    test.assertEqual(len(expected), len(report["events"]))
    for (kind, at, receipt, account, fields), actual in zip(expected, report["events"], strict=True):
        test.assertEqual((kind, at, receipt), (actual["kind"], actual["effective_at"], actual["available_at"]))
        for key, wanted in {**account, **fields}.items():
            reported = actual["account"][key] if key in account else actual[key]
            test.assertEqual(wanted, fraction(reported) if isinstance(wanted, F) else reported, (kind, key))
    [trade] = report["trades"]
    for key, wanted in exit_result.items():
        test.assertEqual(wanted, F(trade[key]), key)
    test.assertEqual({"time": first.opening, "ordinal": 1}, trade["entry_at"])
    test.assertEqual({"time": quotes[-1].opening, "ordinal": 1}, trade["exit_at"])
    test.assertIsNone(trade["exit_window"])
    [position] = report["positions"]
    test.assertEqual(("CLOSED", quotes[-1].receipt), (position["state"], position["release_at"]))
    for key, wanted in expected[-1][3].items():
        actual = report["account"][key]
        test.assertEqual(wanted, fraction(actual) if isinstance(wanted, F) else actual, key)
    test.assertIsNone(report["active"])
    test.assertIsNone(report["open_liability"])
    return by_sequence


class AccountingParityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workspace = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.workspace.cleanup)
        cls.root = Path(cls.workspace.name)
        cls.paths = {}

    def retained(self, sprint, case, profile):
        key = (sprint, case)
        if key not in self.paths:
            home = self.root / f"{sprint}-{case}"
            home.mkdir()
            if sprint == 120:
                path, manifest = home / "input.json", home / "freeze.json"
                daily.write_new(path, daily_fixture(case))
                retained_daily.freeze_fixture(path, manifest)
            else:
                value = retained_elliott.validate_fixture(elliott_fixture(case))
                retained_elliott.prepare_partition(value, value["partitions"][0], home)
                path, manifest = home / "compiled-input.json", home / "compiled-frozen.json"
            self.paths[key] = (path, manifest)
        runner = retained_daily.Replay if sprint == 120 else retained_elliott.Account
        account = runner(*self.paths[key], profile)
        account.run()
        return account._fixture["events"], account.state

    def compare(self, sprint, case, profile, *, full_cash=True):
        events, retained = self.retained(sprint, case, profile)
        outcome, = [o for o in retained["outcomes"] if o["proposal"] is not None]
        proposal = outcome["proposal"]
        settled, = [row for row in retained["ledger"] if row["kind"] == "exit_fill"]
        first, last = outcome["sequence"], settled["sequence"]
        observed = [e for e in events[first:last + 1] if retained["outcomes"][e["sequence"]]["execution_quote"]]
        source, quotes = project(observed)
        boundary = settled["reason"] == "boundary"
        competing = [o["sequence"] for o in retained["outcomes"][first:last + 1]
                     if o["reason"] == "held_position" and (o["sequence"] != last or not boundary)]
        report = replay_projection(source, quotes, proposal, profile, boundary, competing)
        marks = audit(self, report, source, quotes, proposal, profile, boundary)
        if sprint == 125 and case in ("long_gap", "short_gap"):
            self.assertIn(last, competing)
        self.assertEqual(len(competing) + 1, len(report["decisions"]))
        for decision in report["decisions"][1:]:
            self.assertEqual("POSITION_LIMIT", decision["reason"])
        trade, = report["trades"]
        self.assertEqual(F(proposal["entry"]), F(trade["entry_price"]))
        self.assertEqual(F(settled["price"]), F(trade["exit_price"]))
        old_lots, new_lots = F(settled["lots"]), F(trade["lots"])
        for new, old in (("gross_usd", "gross_usd"), ("financing_usd", "financing_usd"), ("net_usd", "net_trade_usd")):
            self.assertEqual(F(settled[old]) / old_lots, F(trade[new]) / new_lots)
        entry, = [row for row in retained["ledger"] if row["kind"] == "entry_fill"]
        old_commission = F(entry["fee_usd"]) + F(settled["fee_usd"])
        self.assertEqual(old_commission / old_lots, F(trade["commission_usd"]) / new_lots)
        self.assertEqual(F(settled["estimated_stop_risk_usd"]) / old_lots,
                         F(trade["estimated_stop_loss_usd"]) / new_lots)
        old_swaps = [r for r in retained["ledger"] if r["kind"] == "financing"]
        new_swaps = [r for r in report["events"] if r["kind"] == "FINANCING"]
        self.assertEqual([(r["weekday"], r["multiplier"], F(r["amount_usd"]) / old_lots) for r in old_swaps],
                         [(r["weekday"], r["multiplier"], F(r["amount_usd"]) / new_lots) for r in new_swaps])
        if full_cash:
            self.assertEqual(old_lots, new_lots)
            self.assertEqual(F(retained["balance_usd"]), F(report["account"]["cash_usd"]))
            for sequence, mark in marks.items():
                old = retained["outcomes"][sequence]["account"]
                for key in ("cash_usd", "equity_usd", "margin_usd", "free_margin_usd"):
                    name = "balance_usd" if key == "cash_usd" else key
                    delta = abs(F(old[name]) - mark[key])
                    self.assertLessEqual(delta, F("1e-35") if "margin" in key else 0, (sequence, key))
        return report, retained, (source, quotes, proposal, profile, boundary)

    def test_120_directional_fills_and_wide_exit(self):
        for case in (*DIRECTIONAL, "quality_guards"):
            for profile in COSTS:
                with self.subTest(case=case, profile=profile):
                    report, retained, _ = self.compare(120, case, profile)
                    self.assertEqual(pause_at_close(retained), report["account"]["entries_paused"])

    def test_125_directional_fills_boundary_and_held_signal(self):
        for case in (*DIRECTIONAL, "boundary_hold", "held_signal_change", "wide_exit"):
            for profile in COSTS:
                with self.subTest(case=case, profile=profile):
                    report, retained, _ = self.compare(125, case, profile)
                    self.assertEqual(pause_at_close(retained), report["account"]["entries_paused"])

    def test_120_weekend_swap_per_lot_with_distinct_risk_fraction(self):
        for profile in COSTS:
            with self.subTest(profile=profile):
                report, retained, _ = self.compare(120, "weekend_financing", profile, full_cash=False)
                old_entry = next(o for o in retained["outcomes"] if o["proposal"] is not None)
                self.assertEqual(F("0.5"), F(old_entry["risk_multiplier"]))
                self.assertGreater(F(report["trades"][0]["lots"]), F(old_entry["proposal"]["lots"]))

    def test_125_financing_closure_reference_and_adverse_spread_difference(self):
        report, retained, _ = self.compare(125, "financing_pause", "base")
        self.assertTrue(pause_at_close(retained))
        self.assertFalse(report["account"]["entries_paused"])
        self.assertEqual("-92.7", report["trades"][0]["net_usd"])
        events, state = self.retained(125, "financing_pause", "adverse")
        entry = next(o for o in state["outcomes"] if o["proposal"] is not None)
        exit_fill = next(row for row in state["ledger"] if row["kind"] == "exit_fill")
        source, quotes = project(events[entry["sequence"]:exit_fill["sequence"] + 1])
        adverse = replay_projection(source, quotes, entry["proposal"], "adverse", False)
        self.assertEqual("SPREAD_TOO_WIDE", adverse["decisions"][0]["reason"])
        self.assertEqual([], adverse["trades"])

    def test_125_minimum_lot_abstains_with_unchanged_cash(self):
        for profile, (slip, _, floor, _) in COSTS.items():
            with self.subTest(profile=profile):
                events, retained = self.retained(125, "minimum_lot", profile)
                event = events[0]
                signal = event["feature"]["signal"]
                side = signal["side"]
                bid, ask = F(str(event["bid"])), F(str(event["ask"]))
                entry = max(ask, bid + floor) + slip if side == 1 else bid - slip
                stop = F(signal["prospective_invalidation"])
                proposal = {"side": side, "entry": fills.text(entry), "stop": fills.text(stop),
                            "target": fills.text(3 * entry - 2 * stop)}
                source, quotes = project(events[:2])
                report = replay_projection(source, quotes, proposal, profile, False)
                self.assertEqual("minimum_lot_risk", retained["outcomes"][0]["reason"])
                [decision] = report["decisions"]
                self.assertEqual("BELOW_MIN_LOT", decision["reason"])
                self.assertEqual("0", decision["sizing"]["lots"])
                self.assertEqual([], report["trades"])
                self.assertEqual(F(retained["balance_usd"]), F(report["account"]["cash_usd"]))

    def test_independent_audit_detects_changes_to_cash_marks_and_costs(self):
        report, _, oracle = self.compare(125, "boundary_hold", "base")
        for kind, key, value in (("MARK", "price", "1"), ("FINANCING", "amount_usd", "99"),
                                 ("ENTRY_FILL", "fee_usd", "0"), ("EXIT_FILL", "price", "1")):
            with self.subTest(kind=kind):
                changed = deepcopy(report)
                next(row for row in changed["events"] if row["kind"] == kind)[key] = value
                with self.assertRaises(AssertionError):
                    audit(self, changed, *oracle)
        changed = deepcopy(report)
        changed["events"][-1]["account"]["entries_paused"] = True
        with self.assertRaises(AssertionError):
            audit(self, changed, *oracle)
