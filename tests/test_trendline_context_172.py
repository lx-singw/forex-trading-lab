"""Phase 5 checks on invented completed D1/H4 publications."""
from dataclasses import replace
from decimal import Decimal
from fractions import Fraction
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from forex_demo_lab.trendline import context, data, engine, lines
from test_trendline_data_163 import calendar, descriptor, files, rows_for, stream_for
from test_trendline_pivots_166 import bars_for, golden

ROOT = Path(__file__).resolve().parents[1]


def channel():
    rows = []
    for index in range(34):
        change = Decimal(index) / 10
        low = 100 + change + (0 if index in (16, 22, 28) else 2)
        high = 150 - change - (0 if index in (17, 23, 29) else 2)
        if index == 33:
            low = Decimal("103.29")
        rows.append(("125", str(high), str(low), "125"))
    return rows


def channel_hours():
    value = descriptor(calendar((8,) * 34, partial=True))
    rows = rows_for(value)
    candles = channel()
    for i, row in enumerate(rows):
        for field, price in zip(("open", "high", "low", "close"), candles[i // 8]):
            row[field] = price
    return value, rows


def d1_prefix(rows, source=None):
    source, bars = bars_for(rows, "D1", source)
    daily = context.DailyContext(source)
    return daily, bars


def table_reference(direction, bias):
    """Independent rule interpretation with direction and bias as inputs."""
    if bias == "UNAVAILABLE":
        return "CONTEXT_UNAVAILABLE"
    if bias == "NEUTRAL":
        return "CONTEXT_NEUTRAL"
    bullish_trade = direction == "LONG"
    return "ALLOW" if bullish_trade == (bias == "BULLISH") else "CONTEXT_CONFLICT"


class TrendlineContextTests(unittest.TestCase):
    def test_frozen_eight_cells_and_independent_rule_agree(self):
        for number in range(17, 21):
            for side in ("LONG", "SHORT"):
                case = golden(number, side)
                actual = context.outcome(**case["inputs"])
                self.assertEqual(case["expected"]["outcome"], actual)
                self.assertEqual(table_reference(side, case["inputs"]["bias"]), actual)
        for args in (("support", "BULLISH"), ("LONG", "UNKNOWN"), ([], "NEUTRAL")):
            with self.assertRaises(ValueError):
                context.outcome(*args)

    def test_completed_daily_ohlc_produces_four_biases_and_removes_poked_support(self):
        daily, bars = d1_prefix(channel())
        outcomes = []
        for bar in bars:
            daily.observe(bar)
            outcomes.append(daily.snapshot(bar.available))
        self.assertEqual(["UNAVAILABLE", "BULLISH", "NEUTRAL", "BEARISH"],
                         [snapshot["bias"] for snapshot in outcomes[-4:]])
        bullish, neutral, bearish = outcomes[-3:]
        self.assertEqual({"numerator": 1031, "denominator": 10}, bullish["S_below"]["value"])
        self.assertEqual({"numerator": 734, "denominator": 5}, neutral["R_above"]["value"])
        self.assertIsNone(bearish["S_below"])
        self.assertEqual("CONTEXT_CONFLICT", context.outcome("LONG", bearish["bias"]))

    def test_distance_is_strict_side_inclusive_three_atr_and_retains_ties(self):
        tiny = Fraction(1, 10**30)
        for below, sign in ((True, -1), (False, 1)):
            levels = [("z", 100 + sign * 6), ("a", 100 + sign * 6),
                      ("equal", 100), ("wrong", 100 - sign),
                      ("outside", 100 + sign * (6 + tiny))]
            result = context._nearest(levels, 100, 6, below=below)
            self.assertEqual(["a", "z"], result["line_ids"])
            self.assertEqual({"numerator": 6, "denominator": 1}, result["distance"])
            self.assertIsNone(context._nearest(levels[2:], 100, 6, below=below))
            result = context._nearest(levels + [("closer", 100 + sign * (6 - tiny))],
                                      100, 6, below=below)
            self.assertEqual(["closer"], result["line_ids"])

    def test_due_missing_then_late_receipt_and_historical_queries(self):
        daily, bars = d1_prefix(channel())
        self.assertEqual("NO_COMPLETED_D1_DUE", daily.snapshot(bars[0].start)["reason"])
        for bar in bars[:32]:
            daily.observe(bar)
        self.assertEqual("BULLISH", daily.snapshot(bars[32].available - 1)["bias"])
        self.assertEqual("MISSING_COMPLETED_D1", daily.snapshot(bars[32].available)["reason"])
        late = replace(bars[32], available=bars[32].available + 5000)
        self.assertEqual("UNAVAILABLE", daily.snapshot(late.available - 1)["bias"])
        daily.observe(late)
        self.assertEqual("NEUTRAL", daily.snapshot(late.available)["bias"])
        with self.assertRaises(ValueError):
            daily.snapshot(late.available - 1)

    def test_gap_resets_warmup_and_zero_atr_fails_closed(self):
        daily, bars = d1_prefix(channel())
        for bar in bars[:32]:
            daily.observe(bar)
        daily.observe(bars[33])
        self.assertEqual("D1_ATR_UNAVAILABLE", daily.snapshot(bars[33].available)["reason"])
        flat, bars = d1_prefix([("100",) * 4] * 15)
        for bar in bars:
            flat.observe(bar)
        self.assertEqual("D1_ZERO_ATR", flat.snapshot(bars[-1].available)["reason"])

    def test_declared_closure_keeps_context_and_cap_blocks(self):
        cal = calendar((24,) * 34, (0,) * 31 + (48,))
        daily, bars = d1_prefix(channel(), data.Declaration.from_record(descriptor(cal)))
        for bar in bars[:32]:
            daily.observe(bar)
        self.assertEqual("BULLISH", daily.snapshot(bars[32].start - 1)["bias"])
        with patch.object(lines, "PIVOT_CAP", 0):
            daily.observe(bars[32])
        report = daily.snapshot(bars[32].available)
        self.assertEqual(("UNAVAILABLE", "D1_SEARCH_INCOMPLETE"), (report["bias"], report["reason"]))

    def test_h4_replay_consumes_only_available_daily_snapshot_and_prefix_is_stable(self):
        value, hours = channel_hours()
        stream = stream_for(value, hours)
        bars = [bar for bar in stream.bars() if bar.timeframe in ("D1", "H4")]
        h4 = [bar for bar in bars if bar.timeframe == "H4"]
        before_d1 = h4[-2]
        cutoff = before_d1.available
        complete = context.replay(stream.source, bars, profile=context.PROFILE, as_of=bars[-1].available)
        variant = complete["context"]["decisions"]
        self.assertEqual(["BULLISH", "NEUTRAL", "NEUTRAL", "BEARISH"],
                         [row["snapshot"]["bias"] for row in variant[-4:]])
        self.assertLess(variant[-2]["snapshot"]["d1_bar"]["available"], cutoff)
        self.assertEqual(variant[-1]["snapshot"]["d1_bar"]["available"], bars[-1].available)
        prefix = context.replay(stream.source, [bar for bar in bars if bar.available <= cutoff],
                                profile=context.PROFILE, as_of=cutoff)
        self.assertEqual(variant[:-1], prefix["context"]["decisions"])
        self.assertEqual(complete["frames"][:-1], prefix["frames"])
        self.assertFalse(complete["orders_available"])
        with self.assertRaises(ValueError):
            context.replay(stream.source, bars, profile=context.PROFILE, as_of=cutoff)
        with self.assertRaises(ValueError):
            context.replay(stream.source, bars[:-2] + bars[-2:][::-1],
                           profile=context.PROFILE, as_of=bars[-1].available)

    def test_gate_off_preserves_entire_engine_report_for_each_baseline(self):
        source, bars = bars_for(golden(35)["inputs"]["ohlc"])
        _, daily = bars_for([("100",) * 4], "D1", source)
        combined = sorted(bars + daily, key=lambda bar: (bar.available, bar.timeframe != "D1"))
        for profile in lines.STRATEGIES:
            if profile == context.PROFILE:
                continue
            with self.subTest(profile=profile):
                baseline = engine.Engine(source, profile)
                for bar in bars:
                    baseline.observe(bar)
                with patch.object(context, "DailyContext", side_effect=AssertionError("daily context constructed")):
                    result = context.replay(source, combined, profile=profile, as_of=bars[-1].available)
                self.assertEqual(baseline.report(), result)

    def test_cli_uses_invented_loader_and_writes_exclusively(self):
        with tempfile.TemporaryDirectory() as directory:
            source, hours, record = files(directory, descriptor(calendar((8,), partial=True)))
            output = Path(directory) / "context.json"
            cmd = [sys.executable, str(ROOT / "scripts/trendline-context-172.py"),
                   str(source), str(hours), str(output)]
            run = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(0, run.returncode, run.stderr)
            original = output.read_bytes()
            report = json.loads(original)
            self.assertEqual(["NO_COMPLETED_D1_DUE", "D1_ATR_UNAVAILABLE"],
                             [row["snapshot"]["reason"] for row in report["context"]["decisions"]])
            self.assertNotEqual(0, subprocess.run(cmd, capture_output=True).returncode)
            self.assertEqual(original, output.read_bytes())
            record["kind"] = "market_trendline_source"
            source.write_text(json.dumps(record))
            blocked = output.with_name("blocked.json")
            self.assertNotEqual(0, subprocess.run(cmd[:-1] + [str(blocked)], capture_output=True).returncode)
            self.assertFalse(blocked.exists())
