"""BRK3 setup and restart checks on invented candles."""
from copy import deepcopy
from dataclasses import replace
from decimal import Decimal
from fractions import Fraction
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from forex_demo_lab.trendline import breaks, context, selection
from test_trendline_data_163 import files, stream_for
from test_trendline_geometry_167 import hourly_fixture
from test_trendline_pivots_166 import bars_for, golden
from test_trendline_selection_169 import declared_line

ROOT = Path(__file__).resolve().parents[1]


def prefix(side="LONG", length=48):
    source, bars = bars_for(golden(35, side)["inputs"]["ohlc"])
    replay = breaks.BreakReplay(source, "0.1")
    for bar in bars[:length]:
        replay.observe(bar)
    return replay, source, bars


def journal(replay):
    return replay.report()["action_replay"]["journal"]


class TrendlineBreakTests(unittest.TestCase):
    def test_g35_mirrors_trigger_on_48_and_freeze_exact_stop(self):
        for side in ("LONG", "SHORT"):
            with self.subTest(side=side):
                replay, _, bars = prefix(side)
                expected = golden(35, side)["expected"]
                self.assertFalse(replay.report()["decisions"][47]["triggered"])
                result = replay.observe(bars[48])
                self.assertEqual((48, "READY", side), (result["bar_index"], result["state"], result["direction"]))
                for field, key in (("line_value", "safety_value"), ("atr_sma14", "atr_fraction"),
                                   ("stop", "rounded_stop")):
                    self.assertEqual(Fraction(expected[key]), selection.fraction(result["safety"][field]))
                action = journal(replay)
                self.assertEqual(["REGISTER", "VALID", "TRIGGER"],
                                 [event["command"]["op"] for event in action["events"]])
                self.assertTrue(action["groups"][0]["consumed"])
                self.assertFalse(replay.report()["entry_ready"])

    def test_exact_break_margin_and_wick_below_margin(self):
        for close, expected in (("103.9", "READY"), ("103.8999", "POKED")):
            replay, _, bars = prefix()
            result = replay.observe(replace(bars[48], close=Decimal(close)))
            self.assertEqual(expected, result["reason"] or result["state"])
            self.assertEqual(expected == "READY", bool(result["triggered"]))

    def test_previous_close_on_line_allowed_and_beyond_refused(self):
        line = declared_line()
        state = SimpleNamespace(line_id="action", line=line)
        tick = Fraction(1, 10)
        current = SimpleNamespace(close=Fraction("102.1"))
        for prior, expected in (("102.2", True), ("102.2001", False)):
            previous = SimpleNamespace(close=Fraction(prior))
            self.assertEqual(expected, bool(breaks._triggered((state,), ("action",), previous,
                                                             current, 40, tick)))
        self.assertEqual((), breaks._triggered((state,), ("action",), None, current, 40, tick))

    def test_same_formation_bar_break_is_discarded_and_never_backdated(self):
        replay, _, bars = prefix(length=47)
        bar = replace(bars[47], high=Decimal("104.6"), close=Decimal("104.2"))
        result = replay.observe(bar)
        self.assertEqual(("DISCARDED", "MISSED_BREAK"), (result["state"], result["reason"]))
        self.assertEqual(1, len(result["missed_break_ids"]))
        self.assertFalse(result["triggered"])
        self.assertFalse(replay.observe(bars[48])["triggered"])
        self.assertFalse(journal(replay)["events"])

    def test_safety_wick_abstains_after_consumption_and_restart(self):
        replay, source, bars = prefix()
        before = breaks.BreakReplay.restore(source, replay.checkpoint())
        bar = replace(bars[48], low=Decimal("102.79"))
        result = replay.observe(bar)
        self.assertEqual(("ABSTAINED", "NO_SAFETY_LINE"), (result["state"], result["reason"]))
        self.assertEqual(result, before.observe(bar))
        self.assertTrue(journal(replay)["groups"][0]["consumed"])
        restored = breaks.BreakReplay.restore(source, replay.checkpoint())
        self.assertEqual(replay.report(), restored.report())
        self.assertEqual(result, restored.observe(bar))
        self.assertEqual(1, sum(event["command"]["op"] == "TRIGGER" for event in journal(restored)["events"]))

    def test_later_break_after_prior_wick_cannot_trigger_and_gap_blocks(self):
        for gap in (False, True):
            replay, _, bars = prefix(length=47)
            if not gap:
                replay.observe(replace(bars[47], high=Decimal("104.01")))
            self.assertFalse(replay.observe(bars[48])["triggered"])

    def test_simultaneous_rank_uses_economics_and_abstains_on_ties(self):
        def state(indices=(0, 6, 12), kind="resistance", b_index=None):
            return SimpleNamespace(line=declared_line(indices=indices, kind=kind, b_index=b_index))
        low, high = state(), state(indices=(0, 6, 12, 18))
        self.assertEqual((high, None), breaks._rank((low, high), 41))
        self.assertEqual((None, "OPPOSING_SIGNAL"), breaks._rank((low, state(kind="support")), 41))
        self.assertEqual((None, "ECONOMIC_TIE"), breaks._rank((low, state(b_index=6)), 41))

    def test_competing_candle_breaks_consume_both_groups_before_safety_abstention(self):
        rows = []
        low = Decimal(111)
        for index in range(76):
            if index < 38:
                high = Decimal(110) - Decimal(".1") * (index - 16)
                if index not in (16, 24, 32):
                    high -= Decimal(".5")
            else:
                high = Decimal(105) - Decimal(".2") * (index - 44)
                if index not in (44, 52, 60):
                    high -= Decimal(".8")
            low = min(low, high - 2)
            close = low + Decimal(".5")
            rows.append((str(close), str(high), str(low), str(close)))
        rows[-1] = (*rows[-1][:1], "106", rows[-1][2], "105.2")
        source, bars = bars_for(rows)
        replay = breaks.BreakReplay(source, "0.1")
        for bar in bars:
            result = replay.observe(bar)
        self.assertEqual("NO_SAFETY_LINE", result["reason"])
        consumed = {tuple(row["line"]["touch_indices"]) for row in journal(replay)["lines"]
                    if row["status"] == "TRIGGERED" and row["group_consumed"]}
        self.assertTrue({(16, 24, 32), (44, 52, 60)} <= consumed)
        self.assertGreaterEqual(len(result["triggered"]), 2)

    def test_safety_prefers_distance_then_touches_and_refuses_exact_tie(self):
        def support(indices, b_index=None):
            return declared_line(indices=indices, kind="support", b_index=b_index)
        near = support((0, 6, 12))
        far = support((6, 12, 18, 24))
        more = support((0, 6, 12, 18))
        self.assertEqual((near, None), breaks._safety_choice((far, near), "LONG", 100, 40))
        self.assertEqual((more, None), breaks._safety_choice((near, more), "LONG", 100, 40))
        self.assertEqual((None, "SAFETY_LINE_TIE"), breaks._safety_choice(
            (near, support((0, 6, 12), b_index=6)), "LONG", 100, 40))
        self.assertEqual((None, "NO_SAFETY_LINE"), breaks._safety_choice((near,), "LONG", 98, 40))

    def test_d1_unavailable_skips_after_trigger_and_safety(self):
        value, rows = hourly_fixture()
        stream = stream_for(value, rows)
        replay = breaks.BreakReplay(stream.source, "0.1", context.PROFILE)
        for bar in stream.bars():
            if bar.timeframe in ("H4", "D1"):
                result = replay.observe(bar)
        self.assertEqual(("SKIPPED", "CONTEXT_UNAVAILABLE"), (result["state"], result["reason"]))
        self.assertIsNotNone(result["safety"])
        self.assertEqual("D1_ATR_UNAVAILABLE", result["context"]["snapshot"]["reason"])
        self.assertTrue(journal(replay)["groups"][0]["consumed"])

    def test_failed_decision_does_not_publish_or_consume(self):
        replay, _, bars = prefix()
        before = replay.report()
        with patch.object(breaks, "_safety_choice", side_effect=ValueError("fixture failure")):
            with self.assertRaises(ValueError):
                replay.observe(bars[48])
        self.assertEqual(before, replay.report())
        self.assertEqual("READY", replay.observe(bars[48])["state"])

    def test_checkpoint_refuses_tamper_and_invalid_ticks(self):
        replay, source, _ = prefix(length=2)
        for tick in (0, -1, 0.1, True):
            with self.assertRaises(ValueError):
                breaks.BreakReplay(source, tick)
        record = replay.checkpoint()
        for change in ("state_sha256", "source_sha256", "bars"):
            edited = deepcopy(record)
            edited[change] = "a" * 64 if change != "bars" else edited["bars"] + [edited["bars"][-1]]
            with self.assertRaises(ValueError):
                breaks.BreakReplay.restore(source, edited)

    def test_checkpoint_binds_daily_bars_even_before_a_setup(self):
        source, bars = bars_for([("100", "101", "99", "100")], "D1")
        replay = breaks.BreakReplay(source, "0.1", context.PROFILE)
        replay.observe(bars[0])
        record = replay.checkpoint()
        self.assertEqual(replay.report(), breaks.BreakReplay.restore(source, record).report())
        record["bars"][0]["close"] = "99.5"
        with self.assertRaises(ValueError):
            breaks.BreakReplay.restore(source, record)

    def test_cli_checkpoints_resume_and_refuse_overwrite_and_market_source(self):
        with tempfile.TemporaryDirectory() as directory:
            value, rows = hourly_fixture()
            source, hours, descriptor = files(directory, value, rows)
            output = Path(directory)
            cmd = [sys.executable, str(ROOT / "scripts/trendline-breaks-173.py"), str(source), str(hours)]
            def run(name, *args):
                return subprocess.run([*cmd, str(output / name), "--tick-size", "0.1", *args],
                                      capture_output=True, text=True)
            first = run("prefix", "--as-of", str(rows[191]["available_at"]))
            self.assertEqual(0, first.returncode, first.stderr)
            resumed = run("resumed", "--restore-checkpoint", str(output / "prefix/checkpoint.json"))
            self.assertEqual(0, resumed.returncode, resumed.stderr)
            complete = run("complete")
            self.assertEqual(0, complete.returncode, complete.stderr)
            report = (output / "resumed/setups.json").read_bytes()
            self.assertEqual(report, (output / "complete/setups.json").read_bytes())
            self.assertEqual("READY", json.loads(report)["decisions"][-1]["state"])
            self.assertNotEqual(0, run("resumed").returncode)
            descriptor["kind"] = "market_trendline_source"
            source.write_text(json.dumps(descriptor))
            self.assertNotEqual(0, run("market").returncode)
            self.assertFalse((output / "market").exists())
