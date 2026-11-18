"""Chronological Level B entry checks from the invented BRK3 replay."""
from dataclasses import replace
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from forex_demo_lab.trendline import breaks, context, data, entries, fills
from test_trendline_data_163 import calendar, files, stream_for
from test_trendline_geometry_167 import hourly_fixture
from test_trendline_pivots_166 import golden

ROOT = Path(__file__).resolve().parents[1]


def fixture(side="LONG", *, delay=0, final_sessions=(), closures=(), basis="bid_only"):
    value, rows = hourly_fixture(side)
    if final_sessions:
        value["calendar"] = calendar((24,) * 8 + final_sessions, closures, partial=True)
    value["calendar"]["finalization_delay_ms"] = delay
    if basis == "mid_candles_source":
        value.update(geometry_basis=basis, spread_semantics="not_available")
    for row in rows:
        row["available_at"] = row["end"] + delay
        if basis == "mid_candles_source":
            row["spread_pips"] = None
    return value, rows


def replay_for(value, rows, profile="TRL_BRK3_E1"):
    stream = stream_for(value, rows)
    replay = breaks.BreakReplay(stream.source, "0.1", profile)
    frames = ("D1", "H4") if profile == context.PROFILE else ("H4",)
    for bar in stream.bars():
        if bar.timeframe in frames:
            replay.observe(bar)
    return replay


def opening_hour(window, bid="104.4", spread="1.2", available=None):
    return data.Hour.from_record({
        "start": window.start, "end": window.end,
        "available_at": window.end if available is None else available,
        "open": bid, "high": bid, "low": bid, "close": bid, "spread_pips": spread,
    }, "bid_only")


def attempt(replay, hours, as_of, cost="base"):
    return entries.evaluate(replay, hours, as_of=as_of, cost_profile=cost)["attempts"][0]


class TrendlineEntriesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.replays = {}
        for side in ("LONG", "SHORT"):
            replay = replay_for(*fixture(side))
            trigger = replay.publications[-1]
            window = fills.PriceModel(replay.source).entry_window(trigger.end)
            expiry = next(bar.end for bar in replay.source.calendar.frame("H4") if bar.start == trigger.end)
            cls.replays[side] = replay, trigger, window, expiry

    def test_both_directions_reuse_frozen_rational_atr_and_rounding(self):
        for side, bid, expected in (("LONG", "104.4", "104.40014"), ("SHORT", "95.6", "95.59998")):
            replay, trigger, window, _ = self.replays[side]
            opening = opening_hour(window, bid)
            result = attempt(replay, [opening], opening.available_at)
            self.assertEqual("FILLED", result["status"])
            self.assertEqual(expected, result["price_result"]["price"])
            self.assertEqual(golden(35, side)["expected"]["rounded_stop"],
                             result["price_result"]["position"]["stop"])
            self.assertEqual({"numerator": 263, "denominator": 140}, result["request"]["atr"])
            self.assertEqual({"time": trigger.end, "ordinal": 0}, result["request"]["decision_at"])
            self.assertEqual({"time": trigger.end, "ordinal": 1},
                             result["price_result"]["position"]["entry_at"])

    def test_pending_then_resolved_and_no_later_h1_substitution(self):
        replay, trigger, window, expiry = self.replays["LONG"]
        pending = attempt(replay, [], trigger.available)
        self.assertEqual(("PENDING", "AWAITING_ENTRY_BAR"), (pending["status"], pending["reason"]))
        windows = replay.source.calendar.frame("H1")
        later = opening_hour(next(hour for hour in windows if hour.start == window.end))
        self.assertEqual("PENDING", attempt(replay, [later], expiry - 1)["status"])
        expired = attempt(replay, [later], expiry)
        self.assertEqual(("EXPIRED", "MISSING_ENTRY_BAR"), (expired["status"], expired["reason"]))
        self.assertEqual(pending["id"], expired["id"])
        self.assertIsNone(expired["price_result"])
        journal = replay.report()["action_replay"]["journal"]
        self.assertTrue(journal["groups"][0]["consumed"])

    def test_expiry_stays_terminal_when_first_hour_arrives_after_deadline(self):
        replay, _, window, expiry = self.replays["LONG"]
        late = opening_hour(window, available=expiry + 1)
        self.assertEqual(attempt(replay, [], expiry), attempt(replay, [late], expiry + 1))
        at_deadline = replace(late, available_at=expiry)
        self.assertEqual("FILLED", attempt(replay, [at_deadline], expiry)["status"])

    def test_receipt_after_first_open_skips_without_reading_any_later_hour(self):
        replay = replay_for(*fixture(delay=2000))
        trigger = replay.publications[-1]
        result = attempt(replay, [], trigger.available)
        self.assertEqual(("SKIPPED", "LATE_DECISION"), (result["status"], result["reason"]))
        self.assertEqual(trigger.end, result["first_scheduled_open"])

    def test_late_decision_at_expiry_cannot_use_first_open(self):
        replay = replay_for(*fixture(delay=2000))
        bars = replay.publications
        replay = breaks.BreakReplay(replay.source, "0.1")
        for bar in bars[:-1]:
            replay.observe(bar)
        deadline = next(w.end for w in replay.source.calendar.frame("H4") if w.start == bars[-1].end)
        # The next H4 is not due for publication until after its close.
        # The entry deadline still falls at its scheduled close.
        decision = replay.observe(replace(bars[-1], available=deadline))
        self.assertEqual("READY", decision["state"])
        result = attempt(replay, [], deadline)
        self.assertEqual(("EXPIRED", "ENTRY_WINDOW_EXPIRED"), (result["status"], result["reason"]))

    def test_entry_after_declared_closure_uses_reopening_and_short_h4_deadline(self):
        replay = replay_for(*fixture(final_sessions=(4, 1), closures=(0,) * 8 + (48,)))
        trigger = replay.publications[-1]
        window = fills.PriceModel(replay.source).entry_window(trigger.end)
        self.assertEqual(48 * 3600000, window.start - trigger.end)
        opening = opening_hour(window)
        result = attempt(replay, [opening], opening.available_at)
        self.assertEqual(window.end, result["expires_at"])
        self.assertEqual("FILLED", result["status"])

    def test_final_partition_has_no_scheduled_open(self):
        replay = replay_for(*fixture(final_sessions=(4,)))
        result = attempt(replay, [], replay.publications[-1].available)
        self.assertEqual(("SKIPPED", "NO_SCHEDULED_ENTRY"), (result["status"], result["reason"]))
        self.assertIsNone(result["first_scheduled_open"])

    def test_crossed_stop_checks_bid_for_long_and_ask_for_short(self):
        for side, bid in (("LONG", "102.6"), ("SHORT", "97.39988")):
            replay, _, window, _ = self.replays[side]
            opening = opening_hour(window, bid)
            result = attempt(replay, [opening], opening.available_at)
            self.assertEqual(golden(12, side)["expected"]["crossed_reason"], result["reason"])

    def test_exact_atr_and_spread_boundary_checks_in_setup_to_price_path(self):
        replay, _, window, _ = self.replays["LONG"]
        for bid, spread, expected in (
                ("103.53914", "1.2", "STOP_OUT_OF_WINDOW"),
                ("103.53915", "1.2", "H1_OPEN_PRICE"),
                ("107.29628", "1.2", "H1_OPEN_PRICE"),
                ("107.29629", "1.2", "STOP_OUT_OF_WINDOW"),
                ("103.49998", "1000", "H1_OPEN_PRICE"),
                ("103.49998", "1001", "SPREAD_TOO_WIDE")):
            opening = opening_hour(window, bid, spread)
            self.assertEqual(expected, attempt(replay, [opening], opening.available_at)["reason"])

    def test_price_uses_only_open_and_applies_hypothetical_costs_once(self):
        replay, _, window, expiry = self.replays["LONG"]
        opening = opening_hour(window, spread="0.2")
        modified = replace(opening, high=opening.high + 20, low=opening.low - 20,
                           close=opening.close + 10, available_at=opening.end + 1)
        for cost, expected in (("base", "104.40004"), ("adverse", "104.40017")):
            a = attempt(replay, [opening], expiry, cost)
            b = attempt(replay, [modified], expiry, cost)
            self.assertEqual(a, b)
            self.assertEqual(expected, a["price_result"]["price"])
        with self.assertRaises(ValueError):
            attempt(replay, [opening], opening.available_at - 1)
        with self.assertRaises(ValueError):
            attempt(replay, [opening, opening], expiry)

    def test_mid_only_and_context_abstention_cannot_supply_a_fill(self):
        mid = replay_for(*fixture(basis="mid_candles_source"))
        result = attempt(mid, [], mid.publications[-1].available)
        self.assertEqual(("UNAVAILABLE", "EXECUTION_SIDE_DATA_UNAVAILABLE"),
                         (result["status"], result["reason"]))
        gated = replay_for(*fixture(), profile=context.PROFILE)
        self.assertEqual("CONTEXT_UNAVAILABLE", gated.report()["decisions"][-1]["reason"])
        report = entries.evaluate(gated, [], as_of=gated.publications[-1].available)
        self.assertEqual([], report["attempts"])
        self.assertFalse(report["orders_available"])

    def test_cli_entry_report_matches_checkpoint_continuation(self):
        value, rows = fixture()
        _, trigger, window, _ = self.replays["LONG"]
        hourly = opening_hour(window, spread="0.2").record()
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            descriptor_path, hours_path, _ = files(directory, value, rows + [hourly])
            command = [sys.executable, str(ROOT / "scripts/trendline-breaks-173.py"),
                       str(descriptor_path), str(hours_path)]

            def run(name, *options):
                output = folder / name
                result = subprocess.run(
                    [*command, str(output), "--tick-size", "0.1", "--cost-profile", "adverse", *options],
                    capture_output=True, text=True)
                self.assertEqual(0, result.returncode, result.stderr)
                return output

            prefix = run("pending", "--as-of", str(trigger.available))
            self.assertEqual("PENDING", json.loads((prefix / "entries.json").read_text())["attempts"][0]["status"])
            resumed = run("resumed", "--restore-checkpoint", str(prefix / "checkpoint.json"))
            full = run("full")
            self.assertEqual((full / "entries.json").read_bytes(), (resumed / "entries.json").read_bytes())
            result = json.loads((full / "entries.json").read_text())["attempts"][0]
            self.assertEqual("104.40017", result["price_result"]["price"])
