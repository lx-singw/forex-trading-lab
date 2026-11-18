"""Invented chronological exits, protection and partition boundaries."""
from dataclasses import replace
from fractions import Fraction
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from forex_demo_lab.trendline import breaks, data, engine, entries, exits, fills, lines
from test_trendline_data_163 import files, rows_for, stream_for
from test_trendline_entries_174 import fixture, replay_for
from test_trendline_levels_180 import target_hours
from test_trendline_selection_169 import declared_line

ROOT = Path(__file__).resolve().parents[1]


def suffix(value, prefix, *prices, delay_index=None):
    rows = rows_for(value)[len(prefix):len(prefix) + len(prices)]
    for index, (row, values) in enumerate(zip(rows, prices, strict=True)):
        row.update(zip(("open", "high", "low", "close"), values, strict=True))
        row["available_at"] = row["end"] + (index == delay_index)
    return rows


def path(replay, rows, *, as_of=None, liquidation=None):
    hours = [data.Hour.from_record(row, "bid_only") for row in rows]
    [result] = exits.evaluate(replay, hours, as_of=hours[-1].available_at if as_of is None else as_of,
                              liquidation_at=liquidation)["paths"]
    return result


class TrendlineExitsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.value, cls.prefix = fixture()
        cls.replay = replay_for(cls.value, cls.prefix)

    def test_late_h4_trail_is_prospective_across_hour_boundary(self):
        inside = ("104.4", "104.9", "103", "104.4")
        rows = suffix(self.value, self.prefix, *([inside] * 4),
                      ("103.5", "104.8", "102.65", "103.5"),
                      ("102.65", "103.5", "102.5", "103.5"), delay_index=3)
        replay = replay_for(self.value, self.prefix + rows)
        result = path(replay, rows)
        [change] = result["protection_events"]
        self.assertEqual(("STOP_TIGHTENED", "102.6", "102.7"),
                         (change["reason"], change["old_stop"], change["stop"]))
        self.assertEqual(rows[4]["start"] + 1, change["decision_at"]["time"])
        self.assertEqual("STOP_OPEN_GAP", result["reason"])
        self.assertEqual(rows[5]["start"], result["exit"]["event"]["time"])
        self.assertEqual("102.64998", result["exit"]["price"])

    def test_close_beyond_latches_and_open_gap_has_priority(self):
        for side in ("LONG", "SHORT"):
            with self.subTest(side=side):
                value, prefix = fixture(side)
                safe = ("104.4", "104.9", "103", "104.4")
                closing = ("104.4", "104.9", "102.7", "102.8")
                openings = (("103.4",) * 4, ("102",) * 4)
                if side == "SHORT":
                    def mirror(prices):
                        opening, high, low, close = map(Fraction, prices)
                        return tuple(fills.text(200 - p) for p in (opening, low, high, close))

                    safe, closing = mirror(safe), mirror(closing)
                    openings = tuple(map(mirror, openings))
                baseline = suffix(value, prefix, safe, safe, safe, closing)
                replay = replay_for(value, prefix + baseline)
                pending = path(replay, baseline)
                [latch] = pending["protection_events"]
                self.assertEqual("SAFETY_CLOSE_BEYOND", latch["reason"])
                self.assertEqual(latch, pending["pending_market_exit"])
                self.assertEqual(pending["entry"]["stop"], pending["position"]["stop"])
                for opening, reason in zip(openings, ("SCHEDULED_OPEN_EXIT", "STOP_OPEN_GAP"), strict=True):
                    [hour] = suffix(value, prefix + baseline, opening)
                    outcome = path(replay, baseline + [hour])
                    self.assertEqual(("CLOSED", reason), (outcome["state"], outcome["reason"]))
                    self.assertEqual(hour["start"], outcome["exit"]["event"]["time"])
                    if reason == "SCHEDULED_OPEN_EXIT":
                        self.assertEqual("SAFETY_CLOSE_BEYOND", outcome["scheduled_cause"])
                    else:
                        self.assertGreater(Fraction(outcome["exit"]["price_risk_excess"]), 0)

    def test_poked_held_stop_waits_for_strictly_better_post_entry_line(self):
        [row] = suffix(self.value, self.prefix, ("104.4",) * 4)
        [attempt] = entries.evaluate(self.replay, [data.Hour.from_record(row, "bid_only")],
                                     as_of=row["available_at"])["attempts"]
        position = fills.Position.from_record(attempt["price_result"]["position"])
        old = declared_line(kind="support", profile=lines.SAFETY_PROFILE)
        pre_entry = declared_line((1, 7, 13), kind="support", profile=lines.SAFETY_PROFILE)
        first = declared_line((2, 8, 14), kind="support", profile=lines.SAFETY_PROFILE)
        tied = declared_line((3, 9, 15), kind="support", profile=lines.SAFETY_PROFILE)
        tied = replace(tied, ray=replace(tied.ray, a_price=tied.ray.a_price + Fraction("0.2"),
                                         b_price=tied.ray.b_price + Fraction("0.2")))
        old_id, pre_id, first_id, tied_id = map(engine.instance_id, (old, pre_entry, first, tied))
        opened = row["start"]
        formed = {i: {"line": line.record(), "valid_since": [t, 1, 63]}
                  for i, line, t in ((old_id, old, opened - 1), (pre_id, pre_entry, opened),
                                     (first_id, first, opened + 1), (tied_id, tied, opened + 1))}
        protect = exits.Protection(old_id, formed, position)

        def update(index, low, candidates):
            at = opened + index
            protect.update({"bar_index": index, "as_of": at,
                            "bar": {"end": at, "close": "106", "low": low},
                            "eligible_line_ids": [engine.instance_id(line) for line in candidates],
                            "selection": {"ranked": [line.record() for line in candidates]}}, Fraction(1))

        update(65, "102.95", (pre_entry, first))
        self.assertTrue(protect.poked)
        self.assertEqual("102.6", protect.position.record()["stop"])
        update(66, "104", (pre_entry, first, tied))
        self.assertEqual(old_id, protect.line_id)
        self.assertEqual("102.6", protect.position.record()["stop"])
        update(67, "104", (pre_entry, first))
        self.assertFalse(protect.poked)
        self.assertEqual((first_id, "102.9"), (protect.line_id, protect.position.record()["stop"]))
        self.assertEqual(["HELD_LINE_POKED", "REPLACEMENT_TIE", "REPLACED_AND_TIGHTENED"],
                         [event["reason"] for event in protect.events])

    def test_declared_closure_preserves_position_for_reopening_gap(self):
        value, prefix = fixture(final_sessions=(8, 4), closures=(0,) * 8 + (48,))
        safe = ("104.4", "104.9", "103", "104.4")
        rows = suffix(value, prefix, *([safe] * 4), ("102",) * 4)
        replay = replay_for(value, prefix + rows)
        result = path(replay, rows)
        self.assertEqual(48 * 3600000, rows[4]["start"] - rows[3]["end"])
        self.assertEqual("STOP_OPEN_GAP", result["reason"])
        self.assertEqual(rows[4]["start"], result["exit"]["event"]["time"])
        self.assertEqual("101.99998", result["exit"]["price"])

    def test_liquidation_requires_declared_open_and_no_intervening_hole(self):
        open_bids = [("104.4",) * 4, ("103.6",) * 4, ("101",) * 4]
        first, second, third = suffix(self.value, self.prefix, *open_bids)
        close = path(self.replay, [first, second, third], liquidation=second["start"])
        self.assertEqual(("SCHEDULED_OPEN_EXIT", "PARTITION_LIQUIDATION", "103.59998"),
                         (close["reason"], close["scheduled_cause"], close["exit"]["price"]))
        missing = path(self.replay, [first, third], liquidation=third["start"])
        self.assertEqual(("UNAVAILABLE", "H1_COVERAGE_INCOMPLETE", second["start"]),
                         (missing["state"], missing["reason"], missing["missing_h1_start"]))
        boundary = self.replay.source.calendar.end
        for rows in ([first, third], [first, {**second, "available_at": boundary + 1}]):
            with self.subTest(rows=len(rows)):
                marked = path(self.replay, rows, as_of=boundary + 1, liquidation=second["start"])
                self.assertEqual(("OPEN_AT_BOUNDARY", "MISSING_LIQUIDATION_OPEN"),
                                 (marked["state"], marked["reason"]))
                self.assertIsNone(marked["exit"])
                self.assertEqual(("104.4", "BID", first["end"]),
                                 (marked["last_mark"]["price"], marked["last_mark"]["side"],
                                  marked["last_mark"]["time"]))
        excluded = path(self.replay, [first], liquidation=first["start"])
        self.assertEqual("NOT_OPENED", excluded["state"])
        self.assertIsNone(excluded["entry"])
        with self.assertRaisesRegex(ValueError, "scheduled H1 open"):
            path(self.replay, [first], liquidation=first["start"] + 1)

    def test_fxr_keeps_fixed_e2_and_prices_unknown_range_order_adversely(self):
        value, rows = target_hours("LONG")
        stream = stream_for(value, rows)
        replay = breaks.BreakReplay(stream.source, "0.1", breaks.FXR_PROFILE)
        for bar in stream.bars():
            if bar.timeframe in ("D1", "H4"):
                replay.observe(bar)
        opening = rows[-1]
        ambiguous = {**opening, "high": "107", "low": "100"}
        adverse = path(replay, [ambiguous])
        self.assertEqual(("STOP_ADVERSE_AMBIGUITY", "100.19998"),
                         (adverse["reason"], adverse["exit"]["price"]))
        self.assertIsNone(adverse["exit"]["event"])
        self.assertEqual(opening["start"], adverse["exit"]["event_window"]["start"])
        [next_hour] = suffix(value, rows, ("107", "107.2", "99", "102.2"))
        target = path(replay, [opening, next_hour], liquidation=next_hour["start"])
        self.assertEqual(("TARGET_OPEN_REACH", "106.8"), (target["reason"], target["exit"]["price"]))
        for result in (adverse, target):
            self.assertEqual(result["entry"], result["position"])
            self.assertEqual([], result["protection_events"])

    def test_cli_exit_report_matches_restored_open_path(self):
        inside = ("104.4", "104.9", "103", "104.4")
        rows = suffix(self.value, self.prefix, *([inside] * 4), ("102",) * 4)
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            source, hours, _ = files(directory, self.value, self.prefix + rows)
            command = [sys.executable, str(ROOT / "scripts/trendline-breaks-173.py"), str(source), str(hours)]

            def run(name, *flags):
                output = folder / name
                result = subprocess.run([*command, str(output), "--tick-size", "0.1", *flags],
                                        capture_output=True, text=True)
                self.assertEqual(0, result.returncode, result.stderr)
                return output

            prefix = run("open", "--as-of", str(rows[3]["available_at"]))
            resumed = run("resumed", "--restore-checkpoint", str(prefix / "checkpoint.json"))
            full = run("full")
            self.assertEqual((full / "exits.json").read_bytes(), (resumed / "exits.json").read_bytes())
            [opened] = json.loads((prefix / "exits.json").read_text())["paths"]
            [closed] = json.loads((full / "exits.json").read_text())["paths"]
            self.assertEqual(("OPEN", "102.7"), (opened["state"], opened["position"]["stop"]))
            self.assertEqual(("CLOSED", "STOP_OPEN_GAP"), (closed["state"], closed["reason"]))
