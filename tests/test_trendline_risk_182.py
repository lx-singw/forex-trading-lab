"""Invented USD admission, one-position ordering and prefix replay."""
from dataclasses import replace
from fractions import Fraction as F
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from forex_demo_lab.trendline import data, fills, risk
from test_trendline_data_163 import files
from test_trendline_entries_174 import fixture, replay_for
from test_trendline_exits_181 import suffix
from test_trendline_fills_164 import hour_for, setup
from test_trendline_pivots_166 import golden

ROOT = Path(__file__).resolve().parents[1]


def snapshot(at, equity="10000", free="10000", reference="10000", paused=False):
    return {"opening_at": at, "equity_usd": equity, "free_margin_usd": free,
            "day_reference_usd": reference, "entry_paused": paused}


def document(source, rows, cost="base"):
    return {"kind": risk.SNAPSHOT_KIND, "source_sha256": source.sha256, "profile": "TRL_BRK3_E1",
            "cost_profile": cost, "snapshots": rows}


class RiskSizingTests(unittest.TestCase):
    def test_g22_exact_size_and_floors(self):
        terms = risk._terms("base")
        for side in ("LONG", "SHORT"):
            case = golden(22, side)
            given, expected = case["inputs"], case["expected"]
            equity = F(given["equity"])
            margin = F(given["margin_per_lot"])
            loss, too_large = map(F, given["per_lot_losses"])
            free, headroom = F(given["free_margin"]), F(given["daily_headroom"])
            self.assertEqual(F(expected["budget"]), equity * risk.RISK_FRACTION)
            self.assertEqual(list(map(F, expected["risk_only_lots"])),
                             [risk._volume(terms, equity, F(10000), F(100), cost, margin)
                              for cost in (loss, too_large)])
            self.assertEqual(F(expected["margin_max_lots"]),
                             risk._volume(terms, equity, free, F(100), loss, margin))
            self.assertEqual(F(expected["final_lots_at_loss250"]),
                             risk._volume(terms, equity, free, headroom, loss, margin))
        self.assertEqual(F(1), risk._volume(terms, F(100000), F(100000), F(1000), F(100), F(1000)))

    def test_cost_estimate_matches_hand_calculation_on_both_sides(self):
        for side in ("LONG", "SHORT"):
            for cost, loss, lots, fee, debit in (
                    ("base", "213", "0.11", "0.385", "2.53"),
                    ("adverse", "222", "0.11", "0.55", "3.52")):
                with self.subTest(side=side, cost=cost):
                    model, request, opening = setup(side, cost=cost)
                    fill = model.entry(request, opening)
                    terms = risk._terms(cost)
                    state = (F(10000), F(10000), F(9900), False, {})
                    size = risk._size(terms, state, fill)
                    self.assertEqual((loss, lots, fee, debit),
                                     (size["stop_loss_per_lot_usd"], size["lots"],
                                      size["estimated_entry_commission_usd"],
                                      size["estimated_immediate_liquidation_debit_usd"]))
                    margin = size["estimated_margin_usd"]
                    used = F(margin["numerator"], margin["denominator"]) + F(fee)
                    self.assertLessEqual(used, 10000)
                    just_below = F("0.01") * (F(fill["price"]) * 100000 / 30 + terms["commission"] / 2)
                    self.assertEqual("0.01", risk._size(terms, (F(10000), just_below, F(9900), False, {}),
                                                       fill)["lots"])
                    self.assertEqual("0", risk._size(terms, (F(10000), just_below - F("0.00001"),
                                                           F(9900), False, {}), fill)["lots"])


class RiskTimelineTests(unittest.TestCase):
    def setUp(self):
        self.model, request, first = setup()
        self.source = self.model.source
        self.frontier = self.source.calendar.frame("H4")[1:4]
        self.attempts, self.hours = [], {}
        for j, window in enumerate(self.frontier):
            opening = replace(first, start=window.start, end=window.start + 3600000)
            order = {**request, "trigger_end": window.start,
                     "decision_at": fills.Event(window.start, 0).record()}
            price = self.model.entry(order, opening)
            self.assertEqual("FILLED", price["status"])
            self.attempts.append({"id": str(j), "first_scheduled_open": window.start,
                                  "expires_at": window.end, "price_result": price,
                                  "status": "FILLED", "reason": "H1_OPEN_PRICE"})
            self.hours[window.start] = hour_for(opening, "1.099", "1.101")

    def replay(self, first_path, *, through=None, snapshots=None, liquidation=None):
        as_of = self.frontier[-1].end if through is None else through
        attempts = [attempt for attempt in self.attempts
                    if attempt["first_scheduled_open"] <= as_of]
        price = {"profile": "TRL_BRK3_E1", "cost_profile": self.model.costs,
                 "as_of": as_of, "attempts": attempts}
        result = {"liquidation_at": self.source.calendar.frame("H1")[-1].start if liquidation is None
                  else liquidation,
                  "paths": [first_path, *({"attempt_id": str(i), "state": "OPEN", "reason": None}
                                          for i in (1, 2))]}
        rows = ([snapshot(window.start) for window in self.frontier]
                if snapshots is None else snapshots)
        capital = risk._snapshots(document(self.source, rows), self.source, price)
        return risk._timeline(price, result, self.hours, capital, risk._terms("base"))

    def test_gap_on_same_open_blocks_reentry_then_releases(self):
        _, second, third = self.frontier
        before = fills.Position.from_record(self.attempts[0]["price_result"]["position"])
        gap = data.Hour.from_record({**self.hours[second.start].record(), "open": "1.097", "low": "1.097"},
                                    "bid_only")
        # The opportunity at the gap would independently clear its own price
        # gates with a lower stop. The held position still consumes the slot.
        self.hours[second.start] = gap
        opening = fills.Opening.from_hour(gap, 1)
        _, request, _ = setup()
        request.update(trigger_end=second.start, decision_at=fills.Event(second.start, 0).record(), stop="1.0955")
        candidate = self.model.entry(request, opening)
        self.assertEqual("FILLED", candidate["status"])
        self.attempts[1]["price_result"] = candidate
        exit_fill = self.model.exit_open(before, opening)
        self.assertEqual("STOP_OPEN_GAP", exit_fill["reason"])
        self.assertGreater(F(exit_fill["price_risk_excess"]), 0)
        closed = {"attempt_id": "0", "state": "CLOSED", "reason": exit_fill["reason"], "exit": exit_fill}
        rows, held, active = self.replay(closed)
        self.assertEqual(["SIZED_OPEN", "POSITION_LIMIT", "SIZED_OPEN"], [row["reason"] for row in rows])
        self.assertEqual(["0", "2"], [row["attempt_id"] for row in held])
        self.assertEqual(gap.available_at, held[0]["release_at"])
        self.assertEqual({"kind": "POSITION", "attempt_id": "2"}, active)
        self.assertEqual(third.start, rows[2]["reserved_at"])

    def test_previous_range_releases_only_after_its_receipt(self):
        _, second, _ = self.frontier
        before = fills.Position.from_record(self.attempts[0]["price_result"]["position"])
        opening = fills.Opening(second.start - 3600000, second.start, 1, F("1.1004"), F("1.2"))
        for delay, reason in ((0, "SIZED_OPEN"), (1, "POSITION_LIMIT")):
            candle = hour_for(opening, "1.098", "1.101", available=second.start + delay)
            exit_fill = self.model.exit_hour(before, candle, as_of=candle.available_at, open_ordinal=1)
            self.assertEqual("STOP_RANGE", exit_fill["reason"])
            closed = {"attempt_id": "0", "state": "CLOSED", "reason": exit_fill["reason"], "exit": exit_fill}
            rows, held, _ = self.replay(closed)
            self.assertEqual(reason, rows[1]["reason"])
            self.assertEqual(second.start + delay, held[0]["release_at"])

    def test_unknown_exit_stays_occupied_and_loss_pause_is_snapshot_latched(self):
        first, second, third = self.frontier
        unknown = {"attempt_id": "0", "state": "UNAVAILABLE", "reason": "H1_COVERAGE_INCOMPLETE"}
        rows, held, active = self.replay(unknown)
        self.assertEqual(["SIZED_OPEN", "POSITION_LIMIT", "POSITION_LIMIT"], [row["reason"] for row in rows])
        self.assertIsNone(held[0]["release_at"])
        self.assertEqual("0", active["attempt_id"])
        rows, held, active = self.replay(unknown, snapshots=[snapshot(first.start, equity="9900"),
                                                           snapshot(second.start, equity="9950"),
                                                           snapshot(third.start, equity="10000")])
        self.assertEqual(["DAILY_PAUSE"] * 3, [row["reason"] for row in rows])
        self.assertEqual([], held)
        self.assertIsNone(active)
        rows, _, _ = self.replay(unknown, snapshots=[snapshot(first.start, equity="-1")],
                                 liquidation=third.start)
        self.assertEqual(["NONPOSITIVE_EQUITY", "RISK_SNAPSHOT_UNAVAILABLE", "ENTRY_AT_LIQUIDATION"],
                         [row["reason"] for row in rows])

    def test_pending_reservation_expiry_has_no_later_substitution(self):
        first, second, _ = self.frontier
        path = {"attempt_id": "0", "state": "OPEN", "reason": None}
        attempt = self.attempts[0]
        attempt.update(status="PENDING", reason="AWAITING_ENTRY_BAR", price_result=None)
        rows, held, active = self.replay(path, through=first.start)
        self.assertEqual("RESERVED", rows[0]["status"])
        self.assertIsNone(rows[0]["resolved_at"])
        self.assertEqual([], held)
        self.assertEqual({"kind": "RESERVATION", "attempt_id": "0"}, active)
        attempt.update(status="EXPIRED", reason="MISSING_ENTRY_BAR")
        rows, held, _ = self.replay(path)
        self.assertEqual(["MISSING_ENTRY_BAR", "SIZED_OPEN", "POSITION_LIMIT"],
                         [row["reason"] for row in rows])
        self.assertEqual(second.start, rows[0]["resolved_at"])
        self.assertEqual(["1"], [row["attempt_id"] for row in held])


class RiskIntegrationTests(unittest.TestCase):
    def test_normal_replay_reserves_sizes_then_releases_identically_after_restart(self):
        value, prefix = fixture()
        hours = suffix(value, prefix, ("104.4",) * 4, ("102",) * 4)
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            meta, prices, declaration = files(directory, value, prefix + hours)
            source = data.Declaration.from_record(declaration)
            snapshots = folder / "snapshots.json"
            snapshots.write_text(json.dumps(document(source, [snapshot(
                hours[0]["start"], equity="1000000", free="1000000", reference="1000000")])))
            command = [sys.executable, str(ROOT / "scripts/trendline-breaks-173.py"), str(meta), str(prices)]

            def run(name, *options):
                out = folder / name
                result = subprocess.run([*command, str(out), "--tick-size", "0.1",
                                         "--risk-snapshots", str(snapshots), *options],
                                        capture_output=True, text=True)
                self.assertEqual(0, result.returncode, result.stderr)
                return out

            pending = run("pending", "--as-of", str(hours[0]["start"]))
            prefix_risk = json.loads((pending / "risk.json").read_text())
            self.assertEqual("RESERVATION", prefix_risk["active"]["kind"])
            self.assertEqual("RESERVED", prefix_risk["decisions"][0]["status"])
            resumed = run("resumed", "--restore-checkpoint", str(pending / "checkpoint.json"))
            full = run("full")
            self.assertEqual((full / "risk.json").read_bytes(), (resumed / "risk.json").read_bytes())
            report = json.loads((full / "risk.json").read_text())
            [decision] = report["decisions"]
            self.assertEqual(prefix_risk["active"]["attempt_id"], decision["attempt_id"])
            self.assertEqual("ADMITTED", decision["status"])
            self.assertEqual(("0.01", "1800.23"), (decision["sizing"]["lots"],
                                                  decision["sizing"]["estimated_stop_loss_usd"]))
            [position] = report["positions"]
            self.assertEqual(("CLOSED", "STOP_OPEN_GAP", hours[-1]["available_at"]),
                             (position["state"], position["reason"], position["release_at"]))
            self.assertIsNone(report["active"])
            self.assertFalse(report["account_ledger_available"])
            self.assertFalse(report["orders_available"])

    def test_snapshot_validation_and_future_prefix_independence(self):
        value, prefix = fixture()
        replay = replay_for(value, prefix)
        rows = suffix(value, prefix, ("104.4",) * 4, ("104.4",) * 4)
        first, second = [data.Hour.from_record(row, "bid_only") for row in rows]
        snapshot_at = snapshot(first.start)

        def assess(snapshots):
            return risk.evaluate(replay, [first], snapshots, as_of=first.available_at)

        source = replay.source
        base = assess(document(source, [snapshot_at]))
        self.assertEqual("BELOW_MIN_LOT", base["decisions"][0]["reason"])
        # The third opening is still beyond the receipt cutoff of the first H1.
        future = snapshot(second.end, equity="20000")
        self.assertEqual(base, assess(document(source, [snapshot_at, future])))
        for invalid in (document(source, [snapshot_at, snapshot_at]),
                        document(source, [snapshot_at], cost="adverse"),
                        document(source, [snapshot(first.start + 1)]),
                        document(source, [{**snapshot_at, "broker_id": "invented"}]),
                        document(source, [snapshot_at, snapshot(second.start, reference="9000")])):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                assess(invalid)
