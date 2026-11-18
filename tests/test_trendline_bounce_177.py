"""BNC contact, spacing and entry replay on invented candles."""
from dataclasses import replace
from decimal import Decimal
from fractions import Fraction
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from forex_demo_lab.trendline import breaks, data, entries, fills, selection
from test_trendline_data_163 import calendar, descriptor, files, rows_for
from test_trendline_entries_174 import opening_hour
from test_trendline_pivots_166 import bars_for, golden

ROOT = Path(__file__).resolve().parents[1]


def fixture(*, end=51, approaches=None, side="LONG"):
    # Preserve the G35 support at pivots 20 and 26. The final fourteen
    # consecutive candles each span two price units in the boundary paths.
    rows = [tuple(map(Decimal, row)) for row in golden(35)["inputs"]["ohlc"][:37]]
    approaches = approaches or {}
    for index in range(37, end + 1):
        ray = Decimal(100) + Decimal(".1") * (index - 20)
        distance, close_above_low = approaches.get(index, (".75", "1"))
        low = ray + Decimal(distance)
        high = low + 2
        close = low + Decimal(close_above_low)
        rows.append((close, high, low, close))
    if side == "SHORT":
        rows = [(200 - op, 200 - low, 200 - high, 200 - close)
                for op, high, low, close in rows]
    value = descriptor(calendar((24,) * 12))
    value["calendar"]["finalization_delay_ms"] = 0
    source, bars = bars_for([list(map(str, row)) for row in rows],
                            source=data.Declaration.from_record(value))
    return source, tuple(replace(bar, available=bar.end) for bar in bars)


def run(source, bars):
    replay = breaks.BreakReplay(source, "0.1", breaks.BNC_PROFILE)
    for bar in bars:
        replay.observe(bar)
    return replay


class TrendlineBounceTests(unittest.TestCase):
    def test_mirrored_contact_uses_touch_band_and_contact_line_for_e1(self):
        for side, bid, expected_stop, expected_fill in (
                ("LONG", "104.5", "102.9", "104.50014"),
                ("SHORT", "95.5", "97.1", "95.49998")):
            with self.subTest(side=side):
                source, bars = fixture(approaches={51: (".5", "1")}, side=side)
                replay = run(source, bars)
                report = replay.report()
                self.assertIsNone(report["safety_replay"])
                self.assertEqual("invented_bnc_setup_replay", report["kind"])
                result = report["decisions"][-1]
                self.assertEqual(("READY", side, 51), (result["state"], result["direction"], result["bar_index"]))
                [contact] = result["contacts"]
                self.assertEqual("CONTACT", contact["reason"])
                for field in ("distance", "tolerance"):
                    self.assertEqual(Fraction(1, 2), selection.fraction(contact[field]))
                self.assertEqual(Fraction(expected_stop), selection.fraction(result["safety"]["stop"]))
                self.assertEqual(result["selected_line_id"], result["safety"]["line_id"])
                [line] = report["action_replay"]["journal"]["lines"]
                self.assertEqual([20, 26], line["line"]["touch_indices"])
                self.assertTrue(line["group_consumed"])
                opening = opening_hour(fills.PriceModel(source).entry_window(bars[-1].end), bid)
                [attempt] = entries.evaluate(replay, [opening], as_of=opening.available_at)["attempts"]
                self.assertEqual(("FILLED", "E1"), (attempt["status"], attempt["request"]["exit_model"]))
                self.assertEqual(expected_fill, attempt["price_result"]["price"])

    def test_correct_side_and_tolerance_boundaries(self):
        for distance, close_offset, expected in (
                (".5001", "1", "NO_CONTACT"), ("0", "0", "NO_CONTACT"),
                ("-.0001", "1", "POKED"), ("0", "1", "READY")):
            with self.subTest(distance=distance, close_offset=close_offset):
                replay = run(*fixture(approaches={51: (distance, close_offset)}))
                decision = replay.report()["decisions"][-1]
                self.assertEqual(expected, decision["reason"] or decision["state"])
                self.assertEqual(expected == "READY", bool(decision["triggered"]))

    def test_six_indices_since_last_touch(self):
        for index, expected in ((51, "TOUCH_TOO_CLOSE"), (52, "CONTACT")):
            with self.subTest(index=index):
                source, bars = fixture(end=index, approaches={46: ("0", "1"), index: (".3", "1")})
                replay = run(source, bars)
                report = replay.report()
                [contact] = report["decisions"][-1]["contacts"]
                self.assertEqual(expected, contact["reason"])
                [line] = report["action_replay"]["journal"]["lines"]
                self.assertEqual([20, 26, 46], line["line"]["touch_indices"])
                self.assertEqual(expected == "CONTACT", line["group_consumed"])

    def test_early_approaches_reset_spacing_and_survive_checkpoint(self):
        # Equal neighboring lows prevent both early approaches from becoming pivots.
        approaches = {50: (".1", "1"), 51: ("0", "0"),
                      55: (".1", "1"), 56: ("0", "0"), 61: (".1", "1")}
        source, bars = fixture(end=61, approaches=approaches)
        replay = run(source, bars[:56])
        report = replay.report()
        self.assertEqual("FORMATION_BAR_CONTACT", report["decisions"][50]["reason"])
        self.assertEqual("CONTACT_TOO_CLOSE", report["decisions"][55]["reason"])
        self.assertFalse(report["action_replay"]["journal"]["groups"][0]["consumed"])
        resumed = breaks.BreakReplay.restore(source, replay.checkpoint())
        for bar in bars[56:]:
            self.assertEqual(replay.observe(bar), resumed.observe(bar))
        result = resumed.report()
        self.assertEqual("READY", result["decisions"][-1]["state"])
        self.assertEqual([20, 26], result["action_replay"]["journal"]["lines"][0]["line"]["touch_indices"])
        self.assertEqual(replay.checkpoint(), resumed.checkpoint())

    def test_contact_needs_no_pivot_and_spent_group_cannot_trigger_again(self):
        source, bars = fixture(end=59, approaches={
            51: (".5", "1"), 52: (".4", "1"), 58: (".4", "1"), 59: ("-.1", "1"),
        })
        replay = run(source, bars[:52])
        first = replay.report()["decisions"][-1]
        self.assertEqual("READY", first["state"])
        # Index 52 has the same low as 51, so 51 cannot be a strict pivot.
        self.assertEqual(bars[51].low, bars[52].low)
        resumed = breaks.BreakReplay.restore(source, replay.checkpoint())
        for bar in bars[52:]:
            self.assertFalse(resumed.observe(bar)["triggered"])
        report = resumed.report()
        self.assertEqual(first, report["decisions"][51])
        self.assertEqual(1, sum(event["command"]["op"] == "TRIGGER"
                                for event in report["action_replay"]["journal"]["events"]))

    def test_opposing_contacts_consume_both_groups_before_abstaining(self):
        rows = []
        for index in range(52):
            support = 100 + Decimal(".1") * (index - 20)
            resistance = 120 - Decimal(".1") * (index - 17)
            low = support + {20: 0, 26: 0, 51: Decimal(".1")}.get(index, 3)
            high = resistance - {17: 0, 29: 0, 51: Decimal(".1")}.get(index, 3)
            close = (low + high) / 2
            rows.append(list(map(str, (close, high, low, close))))
        source, bars = bars_for(rows)
        replay = run(source, bars)
        report = replay.report()
        last = report["decisions"][-1]
        self.assertEqual(("ABSTAINED", "OPPOSING_SIGNAL"), (last["state"], last["reason"]))
        self.assertCountEqual(("LONG", "SHORT"), [item["direction"] for item in last["triggered"]])
        self.assertEqual([True, True], [group["consumed"] for group in report["action_replay"]["journal"]["groups"]])
        self.assertEqual([], entries.evaluate(replay, [], as_of=bars[-1].available)["attempts"])

    def test_cli_routes_bounce_and_prices_same_replay_after_resume(self):
        source, bars = fixture(approaches={51: (".5", "1")})
        value = source.record()
        rows = rows_for(value)[:len(bars) * 4]
        for index, row in enumerate(rows):
            bar = bars[index // 4].record()
            row.update({field: bar[field] for field in ("open", "high", "low", "close")})
            row["available_at"] = row["end"]
        opening = opening_hour(fills.PriceModel(source).entry_window(bars[-1].end), "104.5")
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            source_path, hours_path, _ = files(folder, value, rows + [opening.record()])

            def cli(name, *args):
                target = folder / name
                proc = subprocess.run(
                    [sys.executable, str(ROOT / "scripts/trendline-breaks-173.py"),
                     str(source_path), str(hours_path), str(target), "--profile", breaks.BNC_PROFILE,
                     "--tick-size", "0.1", *args], capture_output=True, text=True)
                self.assertEqual(0, proc.returncode, proc.stderr)
                return target

            prefix = cli("prefix", "--as-of", str(bars[-1].available))
            full = cli("full")
            resumed = cli("resumed", "--restore-checkpoint", str(prefix / "checkpoint.json"))
            self.assertEqual((full / "entries.json").read_bytes(), (resumed / "entries.json").read_bytes())
            [attempt] = json.loads((resumed / "entries.json").read_text())["attempts"]
            self.assertEqual(("FILLED", "104.50014"), (attempt["status"], attempt["price_result"]["price"]))
