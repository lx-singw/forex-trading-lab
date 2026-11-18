"""Invented synchronized tape, quote ordering, execution and restart."""
from copy import deepcopy
from fractions import Fraction as F
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from forex_demo_lab.trendline import breaks, data, fills, quote_replay, quotes
from test_trendline_data_163 import calendar
from test_trendline_entries_174 import fixture
from test_trendline_exits_181 import suffix
from test_trendline_ledger_183 import shift_calendar
from test_trendline_levels_180 import target_hours

ROOT = Path(__file__).resolve().parents[1]


def row(at, bid, ask, received=None):
    return {"source_at": at, "received_at": at if received is None else received,
            "bid": bid, "ask": ask}


def scale(price):
    return F("1.1") + (F(price) - 100) / 1000


def midpoint(at, value, received=None, spread="0.0001"):
    offset = F(spread) / 2
    return row(at, fills.text(scale(value) - offset), fills.text(scale(value) + offset), received)


def history(hours):
    result = []
    for hour in hours:
        for at, key in zip((hour["start"], hour["start"] + 1, hour["start"] + 2, hour["end"] - 1),
                           ("open", "high", "low", "close"), strict=True):
            result.append(midpoint(at, hour[key]))
    return result


def document(value, rows, liquidation=None):
    cal = value["calendar"]
    return {"schema": quotes.VERSION, "kind": quotes.KIND, "symbol": "EURUSD", "data_level": "Q",
            "geometry_basis": "mid_sync", "partition": "development", "calendar": cal,
            "liquidation_at": cal["scope"]["end"] - 1 if liquidation is None else liquidation,
            "quotes": [{**quote, "sequence": i + 1} for i, quote in enumerate(rows)]}


def run(value, as_of=None, *, cost="base", profile="TRL_BRK3_E1"):
    tape = quotes.Tape(value)
    return quote_replay.evaluate(tape, as_of=tape.calendar.end if as_of is None else as_of,
                                 tick="0.0001", cost=cost, profile=profile)


class QuoteTapeTests(unittest.TestCase):
    def test_geometry_uses_synchronized_midpoints_and_seals_at_deadline(self):
        cal = calendar((4,), partial=True)
        cal["finalization_delay_ms"] = 1000
        start = cal["scope"]["start"]
        hour = 3_600_000
        raw = [row(start, "1.1", "1.3"),
               row(start + 1, "1.19", "1.21"),
               row(start + 2, "1.13", "1.15"),
               row(start + hour - 1, "1.2", "1.4", start + hour + 1001)]
        tape = quotes.Tape(document({"calendar": cal}, raw))
        before = start + hour + 999
        self.assertEqual((), tape.publications(tuple(tape.prefix(before)), before))
        later = start + hour + 1001
        [bar] = tape.publications(tuple(tape.prefix(later)), later)
        self.assertEqual(("H1", start + hour + 1000, F("1.2"), F("1.2"), F("1.14"), F("1.14")),
                         (bar.timeframe, bar.available, F(bar.open), F(bar.high), F(bar.low), F(bar.close)))

    def test_source_receipt_sequence_and_scope_reject_before_replay(self):
        cal = calendar((8,), partial=True)
        start = cal["scope"]["start"]
        original = document({"calendar": cal}, [row(start + 1, "1.1", "1.1001"),
                                                 row(start + 1, "1.1001", "1.1002")])
        self.assertEqual(2, len(quotes.Tape(original).quotes))
        for change in (lambda x: x.update(kind="market_quotes"), lambda x: x.update(geometry_basis="bid_only"),
                       lambda x: x.update(partition="validation"),
                       lambda x: x.update(liquidation_at=cal["scope"]["end"]),
                       lambda x: x["quotes"][1].update(sequence=1),
                       lambda x: x["quotes"][1].update(source_at=start),
                       lambda x: x["quotes"][1].update(received_at=start),
                       lambda x: x["quotes"][1].update(ask="1"),
                       lambda x: x["quotes"][1].update(account_id="invented")):
            invalid = deepcopy(original)
            change(invalid)
            with self.assertRaises(ValueError):
                quotes.Tape(invalid)
        validation = {**original, "partition": "validation"}
        unlock = quotes.validation_unlock(validation)
        self.assertEqual(unlock["input_sha256"], quotes.Tape(validation, unlock).sha256)


class QuoteReplayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.value, cls.hours = fixture()
        cls.trigger = cls.hours[-1]["end"]
        cls.prefix = history(cls.hours)

    def test_entry_freshness_boundary_and_wide_stop_on_same_timestamp(self):
        t = self.trigger
        rows = self.prefix + [midpoint(t, "104.4"), midpoint(t + 1, "104.4", t + 2002),
                              midpoint(t + 2, "104.4", t + 2002, "0.00016"),
                              midpoint(t + 3, "104.4", t + 2003, "0.00015"),
                              midpoint(t + 3, "104.4", t + 2003, "0.00015"),
                              midpoint(t + 3, "102", t + 2003, "0.001")]
        result = run(document(self.value, rows), t + 2003)
        [attempt] = result["decisions"]
        self.assertEqual("SIZED_QUOTE", attempt["reason"])
        self.assertEqual(len(self.prefix) + 4, attempt["quote"]["sequence"])
        self.assertEqual(1, result["quote_quality"]["STALE_QUOTE"])
        self.assertEqual(1, result["quote_quality"]["REPEATED_QUOTE"])
        self.assertEqual(2, result["quote_quality"]["ENTRY_SPREAD_EXCEEDED"])
        [trade] = result["trades"]
        self.assertEqual(("STOP_QUOTE", "1.104495", "1.10148", "0.12", "-37.02"),
                         tuple(trade[key] for key in ("reason", "entry_price", "exit_price", "lots", "net_usd")))
        self.assertEqual(trade["entry_at"]["time"], trade["exit_at"]["time"])
        self.assertLess(trade["entry_at"]["ordinal"], trade["exit_at"]["ordinal"])

    def test_first_eligible_price_rejection_consumes_attempt(self):
        t = self.trigger
        result = run(document(self.value, self.prefix + [midpoint(t + 1, "102"), midpoint(t + 2, "104.4")]), t + 2)
        [attempt] = result["decisions"]
        self.assertEqual("STOP_ALREADY_CROSSED", attempt["reason"])
        self.assertEqual(t + 1, attempt["quote"]["source"])
        self.assertEqual([], result["positions"])

    def test_late_receipt_cannot_backdate_post_entry_protection(self):
        value = deepcopy(self.value)
        value["calendar"]["finalization_delay_ms"] = 1000
        t = self.trigger
        candles = suffix(value, self.hours, *([("104.4", "104.9", "103.2", "104.4")] * 8))
        # The opening extrema precede a strictly post-publication entry quote.
        continuation = history(candles)
        continuation.insert(3, midpoint(t + 1001, "104.4"))
        receipt = candles[-1]["end"] + 1000
        continuation += [row(receipt - 500, "1.10265", "1.10275", receipt + 1),
                         row(receipt + 2, "1.10265", "1.10275")]
        result = run(document(value, self.prefix + continuation), receipt + 2)
        [position] = result["positions"]
        [change] = position["protection_events"]
        self.assertEqual(("STOP_TIGHTENED", receipt), (change["reason"], change["decision_at"]["time"]))
        self.assertGreater(F(change["stop"]), F("1.10265"))
        self.assertEqual(receipt + 2, position["closing_quote"]["source"])

    def test_liquidation_uses_first_eligible_observation_and_excludes_late_receipt(self):
        t = self.trigger
        boundary = self.value["calendar"]["scope"]["end"]
        tape = self.prefix + [midpoint(t + 1, "104.4")]
        rows = tape + [midpoint(boundary - 1, "110", boundary)]
        report = run(document(self.value, rows, t + 10))
        self.assertEqual("OPEN_AT_BOUNDARY", report["status"])
        self.assertEqual(1, report["quote_quality"]["OUTSIDE_PARTITION"])
        self.assertEqual([], report["trades"])
        self.assertEqual(t + 1, report["open_liability"]["last_mark"]["time"])
        resolved = run(document(self.value, tape + [midpoint(t + 9, "104.4", t + 10),
                                                     midpoint(t + 11, "104.5"), midpoint(t + 12, "106")], t + 10))
        [trade] = resolved["trades"]
        self.assertEqual(("PARTITION_LIQUIDATION", t + 11, "1.10443"),
                         (trade["reason"], trade["exit_at"]["time"], trade["exit_price"]))

    def test_fxr_uses_frozen_target_and_observed_quote_order(self):
        value, hours = target_hours("LONG")
        t = hours[-1]["start"]
        rows = history(hours[:-1]) + [midpoint(t + 1, "102.2"), midpoint(t + 2, "108"),
                                     midpoint(t + 3, "99")]
        result = run(document(value, rows), t + 3, profile=breaks.FXR_PROFILE)
        [trade] = result["trades"]
        self.assertEqual(("TARGET_QUOTE", t + 2, "1.1068"), (trade["reason"], trade["exit_at"]["time"],
                                                             trade["exit_price"]))

    def test_same_quote_capacity_and_realized_daily_pause(self):
        cal = calendar((8,), partial=True)
        at = cal["scope"]["start"]
        value = document({"calendar": cal}, [row(at, "1.1", "1.1001"), row(at + 1, "1.08", "1.0801"),
                                              row(at + 2, "1.1", "1.1001")])
        tape = quotes.Tape(value)
        action = {"journal": {"lines": []}, "frames": []}
        runner = quote_replay._Execution(tape, {"action_replay": action, "safety_replay": None, "decisions": []},
                                         at + 2, "base")
        attempts = [{"id": str(i), "request": {"direction": "LONG", "stop": "1.0985", "target": "1.105",
                                              "atr": "0.0015", "tick": "0.0001", "exit_model": "E2"}}
                    for i in range(3)]
        for quote, attempt in zip(tape.quotes, attempts, strict=True):
            runner.on_quote(quote, (attempt, None))
        self.assertEqual(["SIZED_QUOTE", "POSITION_LIMIT", "DAILY_PAUSE"], [a["reason"] for a in attempts])
        self.assertTrue(runner.book.paused)
        self.assertGreater(F(runner.book.trades[0]["realized_loss_excess_usd"]), 100)

    def test_adverse_short_finances_declared_closure_and_uses_modeled_ask(self):
        hour = 3_600_000
        cal = shift_calendar(calendar((4, 4), (96,), partial=True), 94 * hour)
        before_close = cal["scope"]["start"] + 4 * hour - 1000
        reopening = cal["scope"]["end"] - 4 * hour
        rows = [row(before_close, "1.0995", "1.09952"), row(before_close + 2000, "1.08", "1.0801"),
                row(reopening + 1, "1.0995", "1.09952")]
        tape = quotes.Tape(document({"calendar": cal}, rows, reopening))
        first, closed, last = tape.quotes
        self.assertEqual("OUTSIDE_SESSION", quote_replay._quality(tape, closed, first))
        action = {"journal": {"lines": []}, "frames": []}
        runner = quote_replay._Execution(tape, {"action_replay": action, "safety_replay": None, "decisions": []},
                                         last.time, "adverse")
        candidate = {"id": "short", "request": {"direction": "SHORT", "stop": "1.1015", "target": "1.095",
                                                "atr": "0.0015", "tick": "0.0001", "exit_model": "E2"}}
        runner.on_quote(first, (candidate, None))
        runner.on_quote(last, None)
        [trade] = runner.book.trades
        self.assertEqual(("PARTITION_LIQUIDATION", "1.09945", "1.09967", "0.11", "-1.2375", "-4.7575"),
                         tuple(trade[key] for key in ("reason", "entry_price", "exit_price", "lots",
                                                      "financing_usd", "net_usd")))
        swaps = [e["multiplier"] for e in runner.book.events if e["kind"] == "FINANCING"]
        self.assertEqual([3, 1, 1, 0, 0], swaps)
        self.assertIsNotNone(runner.book.reference)

    def test_cli_restart_matches_and_refuses_changed_tape(self):
        t = self.trigger
        value = document(self.value, self.prefix + [midpoint(t + 1, "104.4"), midpoint(t + 2, "102")])
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            fixture_path = folder / "tape.json"
            fixture_path.write_text(json.dumps(value))
            command = [sys.executable, str(ROOT / "scripts/trendline-quotes-185.py"), str(fixture_path)]

            def execute(name, *flags):
                output = folder / name
                result = subprocess.run([*command, str(output), "--tick-size", "0.0001", *flags],
                                        capture_output=True, text=True)
                return output, result

            before, result = execute("before", "--as-of", str(t + 1))
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertEqual("OPEN", json.loads((before / "quote-ledger.json").read_text())["status"])
            saved = str(before / "checkpoint.json")
            resumed, result = execute("resumed", "--restore-checkpoint", saved)
            self.assertEqual(0, result.returncode, result.stderr)
            full, result = execute("full")
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertEqual((full / "quote-ledger.json").read_bytes(), (resumed / "quote-ledger.json").read_bytes())
            value["quotes"][-1]["ask"] = "1.1021"
            fixture_path.write_text(json.dumps(value))
            rejected, result = execute("changed", "--restore-checkpoint", saved)
            self.assertNotEqual(0, result.returncode)
            self.assertIn("scope or prefix mismatch", result.stderr)
            self.assertFalse(rejected.exists())
