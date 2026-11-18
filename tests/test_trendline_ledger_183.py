"""Invented USD accounting and receipt-boundary checks."""
from fractions import Fraction as F
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from forex_demo_lab.trendline import data, exits, fills, ledger, risk
from test_trendline_data_163 import calendar, descriptor, files
from test_trendline_entries_174 import fixture
from test_trendline_exits_181 import suffix
from test_trendline_fills_164 import setup

ROOT = Path(__file__).resolve().parents[1]
HOUR = 3_600_000
DAY = 24 * HOUR


def shift_calendar(value, delta):
    for segment in [value["scope"], *value["segments"]]:
        for edge in ("start", "end"):
            segment[edge] += delta
        for frame in ("h1", "h4"):
            if frame in segment:
                segment[frame] = [edge + delta for edge in segment[frame]]
    return value


class Scenario:
    def __init__(self, lengths, *, shift=0, closures=(), cost="base", direction="LONG"):
        value = descriptor(shift_calendar(calendar(lengths, closures, partial=True), shift))
        self.model, self.request, _ = setup(direction, "E2", cost, value)
        self.source = self.model.source
        self.windows = self.source.calendar.frame("H1")
        self.hourly = {}
        self.direction = direction

    def hour(self, index, bid="1.1004", low=None, high=None, close=None, delay=0):
        window = self.windows[index]
        hour = data.Hour.from_record({
            "start": window.start, "end": window.end, "available_at": window.end + delay,
            "open": bid, "low": low or bid, "high": high or bid, "close": close or bid, "spread_pips": "1.2",
        }, "bid_only")
        self.hourly[window.start] = hour
        return hour

    def run(self, indices, *, as_of=None, liquidation=None, target=None):
        if as_of is None:
            as_of = max(hour.available_at for hour in self.hourly.values())
        cutoff = self.windows[-1].start if liquidation is None else self.windows[liquidation].start
        hours = {t: hour for t, hour in self.hourly.items() if hour.available_at <= as_of}
        attempts, paths = [], []
        for index in indices:
            at = self.windows[index].start
            if at > as_of:
                continue
            hour = hours.get(at)
            trigger = max(window.end for window in self.source.calendar.frame("H4") if window.end <= at)
            request = {**self.request, "trigger_end": trigger, "decision_at": fills.Event(trigger, 0).record()}
            if target is not None:
                request["target"] = target
            price = None if hour is None else self.model.entry(request, fills.Opening.from_hour(hour, 1))
            attempt = {"id": str(index), "first_scheduled_open": at,
                       "expires_at": at + 4 * HOUR, "price_result": price,
                       "status": "PENDING" if price is None else price["status"],
                       "reason": "AWAITING_ENTRY_BAR" if price is None else price["reason"]}
            attempts.append(attempt)
            if attempt["status"] == "FILLED":
                paths.append(exits._path(self.model, self.windows[index:], hours, as_of,
                                         self.source.calendar.end, cutoff, attempt, (), {}))
        report = {"profile": "TRL_FXR_M", "cost_profile": self.model.costs,
                  "attempts": attempts, "as_of": as_of}
        return ledger._evaluate(self.source, tuple(hours.values()), report,
                                {"paths": paths, "liquidation_at": cutoff})


class LedgerAccountingTests(unittest.TestCase):
    def test_wednesday_and_weekend_rollovers_match_independent_cash(self):
        # Wed 16:00, entry at 20:00, then Thursday through Monday off-session.
        trial = Scenario((8, 8), shift=90 * HOUR, closures=(96,))
        for index in range(4, 8):
            trial.hour(index)
        gap = trial.hour(8, "1.097")
        trial.hour(12)
        prefix = trial.run([4, 8], as_of=gap.start - DAY)
        full = trial.run([4, 8])
        financing = [row for row in full["events"] if row["kind"] == "FINANCING"]
        self.assertEqual([2, 3, 4, 5, 6], [row["weekday"] for row in financing])
        self.assertEqual([3, 1, 1, 0, 0], [row["multiplier"] for row in financing])
        self.assertEqual(["-0.99", "-0.33", "-0.33", "0", "0"], [row["amount_usd"] for row in financing])
        self.assertEqual("OPEN", prefix["status"])
        self.assertEqual(prefix["events"], [row for row in full["events"] if row["available_at"] <= prefix["as_of"]])
        [trade] = full["trades"]
        self.assertEqual(("0.11", "1.09698", "-39.16", "0.77", "-1.65", "-41.58", "18.15"),
                         tuple(trade[key] for key in ("lots", "exit_price", "gross_usd", "commission_usd",
                                                      "financing_usd", "net_usd", "realized_loss_excess_usd")))
        self.assertEqual("9958.42", full["account"]["cash_usd"])
        self.assertEqual("POSITION_LIMIT", full["decisions"][1]["reason"])
        self.assertEqual(gap.available_at, full["positions"][0]["release_at"])

    def test_realized_gap_pauses_today_and_next_day_sizes_from_cash(self):
        trial = Scenario((24, 12), shift=2 * HOUR)
        for index in range(4, 8):
            trial.hour(index)
        trial.hour(8, "1.085")
        trial.hour(12)
        next_day = trial.hour(24)
        report = trial.run([4, 12, 24])
        first, paused, reopened = report["decisions"]
        self.assertEqual(("SIZED_OPEN", "DAILY_PAUSE", "SIZED_OPEN"),
                         (first["reason"], paused["reason"], reopened["reason"]))
        self.assertEqual("24.570175", reopened["sizing"]["risk_budget_usd"])
        self.assertEqual("-171.93", report["trades"][0]["net_usd"])
        reference = next(row for row in report["events"]
                         if row["kind"] == "DAY_REFERENCE" and row["effective_at"] == next_day.start)
        self.assertEqual("9828.07", reference["account"]["reference_equity_usd"])
        self.assertFalse(reference["account"]["entries_paused"])
        self.assertEqual(2, len(report["positions"]))

    def test_adverse_range_latches_during_surviving_position_after_recovery(self):
        # Entry 20:00, gains by midnight set a higher next-day reference.
        trial = Scenario((16,), shift=-6 * HOUR)
        trial.hour(4)
        for index in range(5, 8):
            trial.hour(index, "1.112")
        hour = trial.hour(8, "1.112", low="1.099", high="1.1125", close="1.112")
        report = trial.run([4], target="1.2")
        range_mark, close = [row for row in report["events"]
                             if row["kind"] == "MARK" and row["effective_at"] == hour.end]
        self.assertEqual("H1_ADVERSE_RANGE", range_mark["observation"])
        self.assertLess(F(range_mark["account"]["equity_usd"]), F("10000"))
        self.assertGreater(F(close["account"]["equity_usd"]), F("10100"))
        self.assertTrue(close["account"]["entries_paused"])
        self.assertEqual([], report["trades"])
        self.assertEqual("1.112", report["open_liability"]["last_mark"]["price"])

    def test_missing_boundary_uses_exit_side_and_keeps_commission_liability(self):
        trial = Scenario((16,), cost="adverse", direction="SHORT")
        trial.hour(4, "1.09948")
        marked = trial.hour(5, "1.0997")
        skipped = trial.hour(7, "1.103")
        report = trial.run([4], liquidation=6, as_of=trial.source.calendar.end)
        self.assertEqual("OPEN_AT_BOUNDARY", report["status"])
        self.assertEqual([], report["trades"])
        liability = report["open_liability"]
        self.assertEqual(("ASK", "1.09982", marked.end, "0.55", "-4.29"),
                         (liability["last_mark"]["side"], liability["last_mark"]["price"],
                          liability["last_mark"]["time"], liability["unpaid_exit_commission_usd"],
                          liability["floating_usd"]))
        self.assertNotIn(skipped.start, {row["effective_at"] for row in report["events"]})
        self.assertEqual("9995.16", report["account"]["equity_usd"])

    def test_straddling_exit_cannot_settle_swap_or_release(self):
        trial = Scenario((16,), shift=-5 * HOUR // 2)
        # Last half of this H1 falls in the next UTC day.
        hour = trial.hour(4, low="1.097")
        self.assertEqual(HOUR // 2, hour.start % HOUR)
        self.assertNotEqual(hour.start // DAY, (hour.end - 1) // DAY)
        trial.hour(8)
        report = trial.run([4, 8])
        self.assertEqual("ROLLOVER_EXIT_ORDER_UNRESOLVED", report["open_liability"]["reason"])
        self.assertEqual([], report["trades"])
        self.assertEqual("POSITION_LIMIT", report["decisions"][1]["reason"])
        self.assertEqual([], [row for row in report["events"] if row["kind"] == "FINANCING"])

    def test_surviving_straddle_charges_swap_but_cannot_reset_day_reference(self):
        # Sun 19:30, entry at 23:30. Its complete H1 proves held through midnight.
        trial = Scenario((16,), shift=21 * HOUR + HOUR // 2)
        hour = trial.hour(4)
        self.assertNotEqual(hour.start // DAY, (hour.end - 1) // DAY)
        trial.hour(5, "1.097")
        trial.hour(8)
        report = trial.run([4, 8])
        [financing] = [row for row in report["events"] if row["kind"] == "FINANCING"]
        self.assertEqual((6, "0"), (financing["weekday"], financing["amount_usd"]))
        self.assertEqual("DAY_REFERENCE_UNAVAILABLE", report["decisions"][1]["reason"])
        self.assertTrue(report["account"]["entries_paused"])
        self.assertEqual(1, len(report["trades"]))

    def test_pending_open_delays_flat_day_reference_until_resolution(self):
        trial = Scenario((16,), shift=-5 * HOUR // 2)
        hour = trial.hour(4, "1.097")
        midnight = hour.end // DAY * DAY
        pending = trial.run([4], as_of=midnight)
        self.assertEqual("RESERVED", pending["status"])
        self.assertEqual(midnight // DAY - 1, pending["account"]["utc_day"])
        resolved = trial.run([4])
        self.assertEqual("STOP_ALREADY_CROSSED", resolved["decisions"][0]["reason"])
        self.assertEqual("10000", resolved["account"]["cash_usd"])
        reference = resolved["events"][-1]
        self.assertEqual(("DAY_REFERENCE", midnight, hour.available_at),
                         (reference["kind"], reference["effective_at"], reference["available_at"]))
        self.assertEqual(pending["events"], [row for row in resolved["events"] if row["available_at"] <= midnight])


class LedgerCliTests(unittest.TestCase):
    def test_scaled_g35_cash_gap_and_restart(self):
        value, prefix = fixture()
        continuation = suffix(value, prefix, ("104.4",) * 4, ("102",) * 4)
        rows = prefix + continuation
        for row in rows:
            for key in ("open", "high", "low", "close"):
                row[key] = fills.text(F("1.1") + (F(row[key]) - 100) / 1000)
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            source, hours, _ = files(directory, value, rows)
            command = [sys.executable, str(ROOT / "scripts/trendline-breaks-173.py"), str(source), str(hours)]

            def run(name, *flags):
                out = folder / name
                result = subprocess.run([*command, str(out), "--tick-size", "0.0001", "--ledger", *flags],
                                        capture_output=True, text=True)
                self.assertEqual(0, result.returncode, result.stderr)
                return out

            prefix_dir = run("prefix", "--as-of", str(continuation[0]["end"]))
            prefix_report = json.loads((prefix_dir / "ledger.json").read_text())
            self.assertEqual("OPEN", prefix_report["status"])
            restored = run("resumed", "--restore-checkpoint", str(prefix_dir / "checkpoint.json"))
            full = run("full")
            self.assertEqual((full / "ledger.json").read_bytes(), (restored / "ledger.json").read_bytes())
            report = json.loads((full / "ledger.json").read_text())
            [trade] = report["trades"]
            self.assertEqual(("0.12", "1.10454", "1.10198", "-31.56", "7.2"),
                             tuple(trade[key] for key in ("lots", "entry_price", "exit_price", "net_usd",
                                                          "realized_loss_excess_usd")))
            self.assertEqual("9968.44", report["account"]["cash_usd"])
            self.assertEqual(prefix_report["events"], [row for row in report["events"]
                                                       if row["available_at"] <= prefix_report["as_of"]])
            self.assertFalse(report["orders_available"])
