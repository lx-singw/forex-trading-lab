"""Frozen S/R grouping and FXR fixed targets on invented inputs."""
from dataclasses import replace
from fractions import Fraction
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest

from forex_demo_lab.trendline import breaks, data, entries, fills, levels, selection
from test_trendline_data_163 import files, rows_for, stream_for
from test_trendline_fxr_175 import fixture
from test_trendline_lines_168 import pivot
from test_trendline_pivots_166 import golden, source_for
from test_trendline_fills_164 import setup

ROOT = Path(__file__).resolve().parents[1]


def target_hours(side):
    source, h4 = fixture(side)
    value = source.record()
    rows = rows_for(value)[:1565]
    for index, row in enumerate(rows):
        bar_index = index // 4
        prices = h4[bar_index].record()
        if 60 <= bar_index < 144:
            high = "106.8" if bar_index in (64, 88, 89, 112, 136) else "105"
            if side == "LONG":
                prices = {"open": "103", "high": high, "low": "102", "close": "103"}
            else:
                prices = {"open": "97", "high": "98", "low": fills.text(200 - Fraction(high)), "close": "97"}
        row.update({key: prices[key] for key in ("open", "high", "low", "close")})
        row["available_at"] = row["end"]
    bid = "102.2" if side == "LONG" else "97.8"
    rows[-1].update(open=bid, high=bid, low=bid, close=bid)
    return value, rows


class TrendlineLevelsTests(unittest.TestCase):
    def test_g26_lowest_anchor_and_same_physical_observation(self):
        for side in ("LONG", "SHORT"):
            case = golden(26, side)
            kind = "low" if case["inputs"]["side"] == "support" else "high"
            tolerance = Fraction(case["inputs"]["tolerance"])
            samples = [(pivot(i, price, kind=kind), i) for i, price in enumerate(case["inputs"]["prices"])]
            partitions = levels.cluster(samples, tolerance)
            self.assertEqual([[Fraction(price) for price in group] for group in case["expected"]["clusters"]],
                             [[selection.fraction(row["price"]) for row in cluster["members"]]
                              for cluster in partitions])
            self.assertEqual(Fraction(case["expected"]["first_median"]),
                             selection.fraction(partitions[0]["price"]))
            samples = [(pivot(i, price, kind=kind, frame=frame), i)
                       for frame, i, price in case["inputs"]["observations"]]
            [cluster] = levels.cluster(samples, tolerance)
            self.assertTrue(cluster["eligible"])
            self.assertEqual(case["expected"]["distinct_physical_observations"], len(cluster["members"]))
            self.assertEqual(["D1", "H4"], [item["timeframe"] for item in cluster["members"][0]["sources"]])

    def test_window_bound_and_confirmation_clock(self):
        source = source_for(510)
        finder = levels.LevelFinder(source)
        current = source.calendar.frame("H4")[501].end
        samples = tuple(replace(pivot(i, "108"), confirmed_at=receipt)
                        for i, receipt in ((1, current - 1), (2, current - 1),
                                           (3, current), (4, current + 1)))
        inspector = SimpleNamespace(metrics=SimpleNamespace(bar_index=501), clock=current,
                                    indexed=(), pivot_journal=samples)
        report = finder.capture(inspector, Fraction(2))
        self.assertEqual((2, 501), (report["first_h4_index"], report["last_h4_index"]))
        [cluster] = report["clusters"]
        self.assertEqual([2, 3], [member["h4_index"] for member in cluster["members"]])

    def test_g37_and_rounding_recheck_choose_first_level_after_open_checks(self):
        for side, bid, shifted, rounded_outcome in (
                ("LONG", "104.99986", "105.00986", "109.2"),
                ("SHORT", "95.00002", "94.99002", "90.8")):
            with self.subTest(side=side):
                case = golden(37, side)
                model, request, original = setup(side, "E2")
                request.update(tick="0.1", target=None, stop=case["inputs"]["stop"], atr="2")

                def at(price, values):
                    opening = fills.Opening.from_record({**original.record(), "bid": price})
                    return model.entry(request, opening, target_levels=tuple(map(Fraction, values)))

                exactly = at(bid, reversed(case["inputs"]["profit_side_levels"]))
                self.assertEqual(case["inputs"]["entry"], exactly["price"])
                self.assertEqual(case["expected"]["target"], exactly["position"]["target"])
                close, farther = ("109.05", "109.21") if side == "LONG" else ("90.95", "90.79")
                self.assertEqual(case["expected"]["no_target_reason"], at(shifted, (close,))["reason"])
                selected = at(shifted, (farther, close))
                self.assertEqual(rounded_outcome, selected["position"]["target"])
                self.assertEqual(Fraction(farther), selection.fraction(selected["target_level"]))

    def test_long_h1_replay_freezes_confirmed_levels_and_makes_fixed_e2_fill(self):
        value, rows = target_hours("LONG")
        stream = stream_for(value, rows)
        replay = breaks.BreakReplay(stream.source, "0.1", breaks.FXR_PROFILE)
        for bar in stream.bars():
            if bar.timeframe in ("H4", "D1"):
                replay.observe(bar)
        decision = replay.report()["decisions"][-1]
        self.assertEqual(("READY", 390), (decision["state"], decision["bar_index"]))
        snapshot = decision["target_levels"]
        self.assertEqual(decision["available_at"], snapshot["as_of"])
        chosen = next(level for level in snapshot["clusters"]
                      if selection.fraction(level["price"]) == Fraction("106.8"))
        self.assertTrue(chosen["eligible"])
        self.assertEqual([64, 112, 136], [member["h4_index"] for member in chosen["members"]])
        self.assertEqual(["D1", "H4"], [p["timeframe"] for p in chosen["members"][1]["sources"]])
        self.assertIn("D1_H4_OCCURRENCE_AMBIGUOUS", {row["reason"] for row in snapshot["unresolved_daily"]})
        self.assertTrue(all(p["confirmed_at"] <= snapshot["as_of"] for member in chosen["members"]
                            for p in member["sources"]))
        hour = data.Hour.from_record(rows[-1], "bid_only")
        [attempt] = entries.evaluate(replay, [hour], as_of=hour.available_at)["attempts"]
        price = attempt["price_result"]
        self.assertEqual(("FILLED", "102.20014", "100.2", "106.8"),
                         (attempt["status"], price["price"], price["position"]["stop"], price["position"]["target"]))
        restored = breaks.BreakReplay.restore(replay.source, replay.checkpoint())
        self.assertEqual(replay.report(), restored.report())
        self.assertEqual([attempt], entries.evaluate(restored, [hour], as_of=hour.available_at)["attempts"])

    def test_short_normal_cli_writes_e2_fill_and_level_evidence(self):
        value, rows = target_hours("SHORT")
        with tempfile.TemporaryDirectory() as temporary:
            source, hours, _ = files(temporary, value, rows)
            output = Path(temporary) / "fxr"
            proc = subprocess.run([
                sys.executable, str(ROOT / "scripts/trendline-breaks-173.py"), str(source), str(hours), str(output),
                "--profile", breaks.FXR_PROFILE, "--tick-size", "0.1",
            ], capture_output=True, text=True)
            self.assertEqual(0, proc.returncode, proc.stderr)
            setup_report = json.loads((output / "setups.json").read_text())
            entry_report = json.loads((output / "entries.json").read_text())
            [attempt] = entry_report["attempts"]
            price = attempt["price_result"]
            self.assertEqual(("FILLED", "97.79998", "99.8", "93.2"),
                             (attempt["status"], price["price"], price["position"]["stop"], price["position"]["target"]))
            decision = setup_report["decisions"][-1]
            self.assertEqual("SHORT", decision["direction"])
            self.assertEqual(Fraction("93.2"), selection.fraction(price["target_level"]))
            self.assertTrue(any(item["eligible"] and item["kind"] == "low"
                                for item in decision["target_levels"]["clusters"]))
