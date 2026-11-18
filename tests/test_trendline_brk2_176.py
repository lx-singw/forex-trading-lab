"""BRK2 replay on two-touch and three-touch invented candle paths."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from forex_demo_lab.trendline import breaks, entries, fills
from test_trendline_data_163 import files, stream_for
from test_trendline_entries_174 import fixture, opening_hour
from test_trendline_pivots_166 import golden

ROOT = Path(__file__).resolve().parents[1]


def two_touch_fixture(side="LONG", *, third_at_trigger=False):
    value, rows = fixture(side)
    for row in rows[23 * 4:24 * 4]:
        if side == "LONG":
            row["high"] = "108"
        else:
            row["low"] = "92"
    if third_at_trigger:
        if side != "LONG":
            raise ValueError("the third-touch fixture is authored for LONG")
        for row in rows[45 * 4:46 * 4]:
            row["high"] = "104.4"
        for row in rows[48 * 4:49 * 4]:
            row.update(high="104.2", close="104.1")
    return value, rows


def setups(value, rows, profile):
    stream = stream_for(value, rows)
    replay = breaks.BreakReplay(stream.source, "0.1", profile)
    for bar in stream.bars():
        if bar.timeframe == "H4":
            replay.observe(bar)
    return replay


def action_candidate(frame, first=17, last=29):
    return next(item for item in frame["candidates"]
                if (item["ray"]["a_index"], item["ray"]["b_index"]) == (first, last))


class TrendlineBRK2Tests(unittest.TestCase):
    def test_mirrored_two_touch_breaks_consume_groups_and_use_current_e1_stop(self):
        for side, bid, expected in (("LONG", "104.4", "104.40014"), ("SHORT", "95.6", "95.59998")):
            with self.subTest(side=side):
                replay = setups(*two_touch_fixture(side), breaks.BRK2_PROFILE)
                report = replay.report()
                self.assertEqual("invented_brk2_setup_replay", report["kind"])
                action = report["action_replay"]
                self.assertFalse(action["frames"][46]["eligible_line_ids"])
                self.assertTrue(action["frames"][47]["eligible_line_ids"])
                self.assertFalse(report["decisions"][47]["triggered"])
                decision = report["decisions"][-1]
                self.assertEqual((48, "READY", side), (decision["bar_index"], decision["state"], decision["direction"]))
                [line] = action["journal"]["lines"]
                self.assertEqual([17, 29], line["line"]["touch_indices"])
                self.assertEqual("TRIGGERED", line["status"])
                self.assertTrue(line["group_consumed"])
                self.assertNotIn("projected_index", decision["safety"])
                self.assertIsNone(decision["context"])
                trigger = replay.publications[-1]
                window = fills.PriceModel(replay.source).entry_window(trigger.end)
                hour = opening_hour(window, bid)
                entry = entries.evaluate(replay, [hour], as_of=hour.available_at)
                self.assertEqual("invented_brk2_b_entry_replay", entry["kind"])
                [attempt] = entry["attempts"]
                self.assertEqual(("FILLED", "E1"), (attempt["status"], attempt["request"]["exit_model"]))
                self.assertEqual(expected, attempt["price_result"]["price"])
                self.assertEqual(golden(35, side)["expected"]["rounded_stop"],
                                 attempt["price_result"]["position"]["stop"])

    def test_same_ray_has_disjoint_break_profiles_on_two_and_three_touches(self):
        for expected_profile, supplied in (
                (breaks.BRK2_PROFILE, two_touch_fixture()),
                ("TRL_BRK3_E1", fixture())):
            for profile in (breaks.BRK2_PROFILE, "TRL_BRK3_E1"):
                with self.subTest(expected=expected_profile, profile=profile):
                    replay = setups(*supplied, profile)
                    report = replay.report()
                    frame = report["action_replay"]["frames"][47]
                    candidate = action_candidate(frame)
                    self.assertEqual(profile == expected_profile, candidate["profile_valid"])
                    self.assertEqual(profile == expected_profile, bool(report["decisions"][48]["triggered"]))
                    if profile != expected_profile:
                        self.assertIn("TOUCH_COUNT", candidate["reasons"])
                        as_of = replay.publications[-1].available
                        self.assertEqual([], entries.evaluate(replay, [], as_of=as_of)["attempts"])

    def test_third_touch_confirmed_on_trigger_bar_blocks_existing_brk2(self):
        replay = setups(*two_touch_fixture(third_at_trigger=True), breaks.BRK2_PROFILE)
        report = replay.report()
        frames = report["action_replay"]["frames"]
        previous = action_candidate(frames[47])
        current = action_candidate(frames[48])
        self.assertTrue(previous["profile_valid"])
        self.assertEqual([17, 29], previous["touches"]["touch_indices"])
        self.assertEqual([17, 29, 45], current["touches"]["touch_indices"])
        self.assertIn("TOUCH_COUNT", current["reasons"])
        self.assertEqual([], frames[48]["action_line_ids"])
        self.assertEqual([], report["decisions"][48]["triggered"])
        [line] = report["action_replay"]["journal"]["lines"]
        self.assertEqual("POKED", line["status"])
        self.assertFalse(line["group_consumed"])

    def test_cli_replays_brk2_hourly_prefix_and_resumes_identically(self):
        value, rows = two_touch_fixture()
        source = stream_for(value, rows).source
        trigger_end = rows[-1]["end"]
        window = fills.PriceModel(source).entry_window(trigger_end)
        hour = opening_hour(window)
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            source_path, hours_path, _ = files(temp, value, rows + [hour.record()])
            command = [sys.executable, str(ROOT / "scripts/trendline-breaks-173.py"),
                       str(source_path), str(hours_path)]

            def run(name, *options):
                target = folder / name
                result = subprocess.run(
                    [*command, str(target), "--profile", breaks.BRK2_PROFILE, "--tick-size", "0.1", *options],
                    capture_output=True, text=True)
                self.assertEqual(0, result.returncode, result.stderr)
                return target

            prefix = run("prefix", "--as-of", str(trigger_end))
            checkpoint = prefix / "checkpoint.json"
            self.assertEqual(breaks.BRK2_PROFILE, json.loads(checkpoint.read_text())["profile"])
            [pending] = json.loads((prefix / "entries.json").read_text())["attempts"]
            self.assertEqual("PENDING", pending["status"])
            resumed = run("resumed", "--restore-checkpoint", str(checkpoint))
            uninterrupted = run("uninterrupted")
            for name in ("checkpoint.json", "entries.json", "setups.json"):
                self.assertEqual((resumed / name).read_bytes(), (uninterrupted / name).read_bytes())
            [filled] = json.loads((resumed / "entries.json").read_text())["attempts"]
            self.assertEqual(pending["id"], filled["id"])
            self.assertEqual("FILLED", filled["status"])
