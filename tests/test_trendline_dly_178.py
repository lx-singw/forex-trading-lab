"""Disabled DLY transitions and Level B replay on invented candles."""
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

from forex_demo_lab.trendline import breaks, data, delayed, entries, fills, geometry, lines, selection
from test_trendline_data_163 import calendar, descriptor, files, rows_for
from test_trendline_entries_174 import opening_hour
from test_trendline_pivots_166 import bars_for, golden
from test_trendline_selection_169 import declared_line

ROOT = Path(__file__).resolve().parents[1]
PROFILE = lines.DLY_PROFILE


def fixture(*, end=58, safety_pivot=None, side="LONG", immediate=False):
    rows = [list(map(Decimal, row)) for row in golden(35)["inputs"]["ohlc"]]
    if not immediate:
        rows[26][2] = Decimal("101.0")
    for index in range(49, end + 1):
        ray = Decimal(100) + Decimal(".1") * (index - 20)
        low = ray if index == safety_pivot else ray + Decimal(".4")
        close = max(Decimal("104.4"), low + Decimal(".2"))
        rows.append([close, Decimal(106), low, close])
    if side == "SHORT":
        rows = [(200 - op, 200 - low, 200 - high, 200 - close)
                for op, high, low, close in rows]
    value = descriptor(calendar((24,) * 12))
    value["calendar"]["finalization_delay_ms"] = 0
    source, bars = bars_for([list(map(str, row)) for row in rows],
                            source=data.Declaration.from_record(value))
    return source, tuple(replace(bar, available=bar.end) for bar in bars)


def run(source, bars, profile=PROFILE):
    replay = breaks.BreakReplay(source, "0.1", profile, enable_dly=profile == PROFILE)
    for bar in bars:
        replay.observe(bar)
    return replay


class TrendlineDLYTests(unittest.TestCase):
    def test_explicit_opt_in_and_distinct_baseline_opportunities(self):
        source, bars = fixture()
        with self.assertRaises(ValueError):
            breaks.BreakReplay(source, "0.1", PROFILE)
        with self.assertRaises(ValueError):
            breaks.BreakReplay(source, "0.1", enable_dly=True)
        self.assertNotIn(PROFILE, lines.STRATEGIES)
        self.assertNotIn(PROFILE, data.CANDIDATES)
        base, dly = (run(source, bars[:49], profile) for profile in ("TRL_BRK3_E1", PROFILE))
        left, right = (replay.report()["decisions"][-1] for replay in (base, dly))
        self.assertEqual(("ABSTAINED", "NO_SAFETY_LINE"), (left["state"], left["reason"]))
        self.assertEqual(("AWAITING_SAFETY", "NO_SAFETY_LINE"), (right["state"], right["reason"]))
        self.assertNotEqual(left["selected_line_id"], right["selected_line_id"])
        [group] = dly.report()["action_replay"]["journal"]["groups"]
        self.assertTrue(group["consumed"])
        self.assertEqual([], entries.evaluate(dly, [], as_of=bars[48].available)["attempts"])

    def test_mirrors_price_from_first_safety_close_and_resume(self):
        for side, bid, fill in (("LONG", "104.4", "104.40014"), ("SHORT", "95.6", "95.59998")):
            with self.subTest(side=side):
                source, bars = fixture(end=54, safety_pivot=49, side=side)
                replay = run(source, bars[:49])
                checkpoint = replay.checkpoint()
                with self.assertRaises(ValueError):
                    breaks.BreakReplay.restore(source, checkpoint)
                resumed = breaks.BreakReplay.restore(source, checkpoint, enable_dly=True)
                for bar in bars[49:53]:
                    self.assertEqual(replay.observe(bar), resumed.observe(bar))
                report = resumed.report()
                self.assertEqual(["AWAITING_SAFETY"] * 4,
                                 [row["state"] for row in report["decisions"][48:52]])
                ready = report["decisions"][52]
                self.assertEqual(("READY", side, 48, 52),
                                 (ready["state"], ready["direction"], ready["dly_origin"]["trigger_index"], ready["bar_index"]))
                self.assertEqual(Fraction("103.2" if side == "LONG" else "96.8"),
                                 selection.fraction(ready["safety"]["line_value"]))
                self.assertEqual("READY", ready["dly_transitions"][-1]["state"])
                self.assertEqual([], report["dly_waiting"])
                self.assertEqual([], ready["triggered"])
                opening = opening_hour(fills.PriceModel(source).entry_window(bars[52].end), bid)
                [attempt] = entries.evaluate(resumed, [opening], as_of=opening.available_at)["attempts"]
                self.assertEqual((48, bars[52].end, fill), (
                    attempt["dly_origin"]["trigger_index"], attempt["request"]["trigger_end"],
                    attempt["price_result"]["price"]))
                after = breaks.BreakReplay.restore(source, resumed.checkpoint(), enable_dly=True)
                self.assertFalse(after.observe(bars[53])["triggered"])
                self.assertEqual(ready, after.report()["decisions"][52])

    def test_immediate_safety_uses_existing_e1_path(self):
        source, bars = fixture(immediate=True)
        baseline, opted = (run(source, bars[:49], profile).report()
                           for profile in ("TRL_BRK3_E1", PROFILE))
        result = opted["decisions"][-1]
        self.assertEqual("READY", result["state"])
        self.assertEqual(48, result["dly_origin"]["trigger_index"])
        self.assertEqual(baseline["decisions"][-1]["safety"], result["safety"])
        self.assertEqual([], opted["dly_waiting"])

    def test_frozen_g25_guard_boundaries_and_reasons(self):
        for side in ("LONG", "SHORT"):
            case = golden(25, side)
            inputs = case["inputs"]
            sign = 1 if side == "LONG" else -1
            direction = "resistance" if sign > 0 else "support"
            index = inputs["safety_at_index"]
            value = Fraction(inputs["action_value"])
            slope = -sign * Fraction(".2")
            ray = geometry.Ray(direction, 0, value - index * slope, 6, value - (index - 6) * slope)
            state = SimpleNamespace(line=SimpleNamespace(ray=ray))
            pending = delayed.AwaitingSafety(state, inputs["trigger_index"], "unused",
                                            Decimal(inputs["trigger_close"]), 100)
            atr = Fraction(inputs["atr"])

            def guard(close, at=index):
                return pending.guard(SimpleNamespace(close=Decimal(close), available=99), at, atr,
                                     data_gap=False, search_incomplete=False)

            self.assertEqual(case["expected"]["failed_reason"], guard(inputs["back_across_action_close"])[1])
            self.assertEqual(case["expected"]["chase_reason"], guard(inputs["chase_close"])[1])
            self.assertIsNone(guard(inputs["action_value"]))
            self.assertIsNone(guard(Decimal(inputs["trigger_close"]) + sign * Decimal(inputs["atr"])))
            self.assertEqual(case["expected"]["at_elapsed10"],
                             guard(inputs["action_value"], inputs["trigger_index"] + inputs["expiry_elapsed"])[0])
            late = SimpleNamespace(close=Decimal(inputs["action_value"]), available=100)
            self.assertEqual(("EXPIRED", "DLY_EXPIRED"),
                             pending.guard(late, index, atr, data_gap=True, search_incomplete=False))

    def test_fail_and_chase_are_terminal_before_safety_on_same_bar(self):
        for reason, close, low, high in (
                ("FAILED_BREAK", "102.9", "102.8", "106"),
                ("CHASE_LIMIT", "109", "103.6", "109.5")):
            with self.subTest(reason=reason):
                source, bars = fixture(safety_pivot=49)
                if reason == "FAILED_BREAK":
                    bars = (*bars[:49], replace(bars[49], low=Decimal("102.5")), *bars[50:])
                replay = run(source, bars[:52])
                barrier = replace(bars[52], close=Decimal(close), low=Decimal(low), high=Decimal(high))
                decision = replay.observe(barrier)
                self.assertEqual(("INVALIDATED", reason), (decision["state"], decision["reason"]))
                self.assertFalse(replay.report()["dly_waiting"])
                self.assertIsNone(decision["safety"])
                self.assertTrue(replay.report()["safety_replay"]["frames"][52]["eligible_line_ids"])
                restored = breaks.BreakReplay.restore(source, replay.checkpoint(), enable_dly=True)
                self.assertEqual(replay.report(), restored.report())
                self.assertNotEqual("READY", restored.observe(bars[53])["state"])

    def test_expiry_precedes_safety_and_clock_only_report_is_causal(self):
        source, bars = fixture(safety_pivot=55)
        replay = run(source, bars[:58])
        deadline = bars[58].end
        earlier = replay.report(as_of=deadline - 1)
        expired = replay.report(as_of=deadline)
        self.assertEqual("AWAITING_SAFETY", earlier["dly_waiting"][0]["state"])
        self.assertEqual("EXPIRED", expired["dly_waiting"][0]["state"])
        self.assertEqual(earlier["decisions"], expired["decisions"])
        decision = replay.observe(bars[58])
        self.assertEqual(("EXPIRED", "DLY_EXPIRED"), (decision["state"], decision["reason"]))
        self.assertTrue(replay.report()["safety_replay"]["frames"][-1]["eligible_line_ids"])
        self.assertEqual([], entries.evaluate(replay, [], as_of=deadline)["attempts"])

    def test_missing_h4_invalidates_instead_of_backfilling_a_wait(self):
        source, bars = fixture(safety_pivot=49)
        replay = run(source, bars[:49])
        decision = replay.observe(bars[50])
        self.assertEqual(("INVALIDATED", "DATA_GAP"), (decision["state"], decision["reason"]))
        self.assertEqual([], replay.report()["dly_waiting"])

    def test_opposing_ready_waits_abstain_together(self):
        source, _ = fixture()
        replay = breaks.BreakReplay(source, "0.1", PROFILE, enable_dly=True)
        waits = []
        for kind in ("resistance", "support"):
            line = declared_line(profile=PROFILE, kind=kind)
            state = SimpleNamespace(line=line, line_id=kind, group_id=kind)
            waits.append(delayed.AwaitingSafety(state, 48, kind, Decimal(100), 100))
        replay._waiting = tuple(waits)
        safety = tuple(declared_line(indices=(6, 12, 18), profile=lines.SAFETY_PROFILE, kind=kind)
                       for kind in ("support", "resistance"))
        bar = SimpleNamespace(available=99, close=Decimal(100))
        decision = {"state": "FORMING", "reason": "NO_VALID_LINE"}
        frame = {"coverage_state": "CURRENT", "search_incomplete": False}
        with patch.object(breaks, "_eligible_safety", return_value=safety):
            result = replay._resolve_delays(decision, (), bar, 52, Fraction(2), frame, bar)
        self.assertEqual((), result)
        self.assertEqual(("ABSTAINED", "OPPOSING_SIGNAL"), (decision["state"], decision["reason"]))
        self.assertEqual(["OPPOSING_SIGNAL", "OPPOSING_SIGNAL"],
                         [event["reason"] for event in decision["dly_transitions"]])

    def test_cli_requires_flag_and_resumes_waiting_attempt(self):
        source, bars = fixture(end=52, safety_pivot=49)
        value = source.record()
        hours = rows_for(value)[:len(bars) * 4]
        for index, hour in enumerate(hours):
            record = bars[index // 4].record()
            hour.update({field: record[field] for field in ("open", "high", "low", "close")})
            hour["available_at"] = hour["end"]
        opening = opening_hour(fills.PriceModel(source).entry_window(bars[-1].end), "104.4")
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            source_path, hours_path, _ = files(folder, value, hours + [opening.record()])
            command = [sys.executable, str(ROOT / "scripts/trendline-breaks-173.py"),
                       str(source_path), str(hours_path)]

            def invoke(name, args):
                return subprocess.run([*command, str(folder / name), "--tick-size", "0.1", *args],
                                      capture_output=True, text=True)

            profile = ["--profile", PROFILE]
            for args in (profile, ["--enable-dly"]):
                blocked = invoke("blocked", args)
                self.assertNotEqual(0, blocked.returncode)
                self.assertIn("must be used together", blocked.stderr)
                self.assertFalse((folder / "blocked").exists())
            enabled = [*profile, "--enable-dly"]
            prefix = invoke("prefix", [*enabled, "--as-of", str(bars[48].available)])
            self.assertEqual(0, prefix.returncode, prefix.stderr)
            checkpoint = folder / "prefix/checkpoint.json"
            resumed = invoke("resumed", [*enabled, "--restore-checkpoint", str(checkpoint)])
            full = invoke("full", enabled)
            self.assertEqual(0, resumed.returncode, resumed.stderr)
            self.assertEqual(0, full.returncode, full.stderr)
            for name in ("setups.json", "entries.json", "checkpoint.json"):
                self.assertEqual((folder / "full" / name).read_bytes(), (folder / "resumed" / name).read_bytes())
            [attempt] = json.loads((folder / "resumed/entries.json").read_text())["attempts"]
            self.assertEqual(("FILLED", 48), (attempt["status"], attempt["dly_origin"]["trigger_index"]))
