"""Phase 4 acceptance through the public replay API, using invented OHLC only."""
from dataclasses import replace
from decimal import Decimal as D
from fractions import Fraction
import random
import unittest

from forex_demo_lab.trendline import data, engine, geometry, lifecycle, lines, selection
from test_trendline_pivots_166 import bars_for, golden, source_for
from test_trendline_lines_168 import pivot
from test_trendline_selection_169 import declared_line, declared_snapshot


def mirror(rows):
    return [[str(300 - D(value)) for value in (o, low, high, c)]
            for o, high, low, c in rows]


def candle(low, high):
    mid = (low + high) / 2
    return list(map(str, (mid, high, low, mid)))


def union_rows():
    # AB slope 3.4/12, BC slope .175, AC slope .2. B is one unit
    # above AC and within B's frozen tolerance. Narrow recent candles
    # admit BC first, then the wider bar at 76 admits AC.
    rows = []
    for i in range(79):
        if i <= 56:
            low = D(100) + D(".28") * (i - 20) + 2
            high = low + 6
            low = {20: D(100), 32: D("103.4")}.get(i, low)
        elif i < 72:
            low = D("110.75")
            high = low + D(".36")
        else:
            low = D("110.4") + (i - 72) * D(".2")
            high = low + (D(2) if i >= 76 else D(".36"))
        rows.append(candle(low, high))
    return rows


def replay(rows, profile):
    source, bars = bars_for(rows)
    book = engine.Engine(source, profile)
    frames = [book.observe(bar) for bar in bars]
    return book, frames


class PhaseFourAcceptance(unittest.TestCase):
    def test_returned_debug_bindings_cannot_disable_the_next_snapshot(self):
        source, bars = bars_for(golden(35)["inputs"]["ohlc"])
        inspector = lines.Inspector(source)
        inspector.observe(bars[0])
        snapshot = inspector.snapshot()
        snapshot["source_bindings"].clear()
        inspector.observe(bars[1])
        self.assertEqual(lines.bindings(), inspector.snapshot()["source_bindings"])

    def test_mirrored_golden_spacing_age_slope_and_atr_tables(self):
        for side in ("LONG", "SHORT"):
            spacing, ages, slopes, atr = [golden(n, side) for n in (7, 9, 10, 38)]
            support = side == "SHORT"
            def anchor(i):
                sign = 1 if support else -1
                return pivot(i, D(100) + sign * D(i)/10, "low" if support else "high")
            a, b = anchor(0), anchor(spacing["inputs"]["last_index"])
            ray = geometry.Ray(spacing["inputs"]["kind"], 0, a.price, b.bar_index, b.price)
            accepted = []
            for i in spacing["inputs"]["next_indices"]:
                other = anchor(i)
                values = (a, b, other)
                scan = lines.scan_touches(ray, a, b, values, {p.id: 1 for p in values})
                accepted.append(other in scan.touches)
            self.assertEqual(spacing["expected"]["independent_acceptance"], accepted)
            self.assertEqual(ages["expected"]["core_age_ok"], [
                lines.profile_tests((a, b, anchor(18)), age, "H4", "TRL_BRK3_E1", 1,
                                    slope=ray.slope)["passes"] for age in ages["inputs"]["core_ages"]])
            self.assertEqual(ages["expected"]["fxr_span_ok"], [
                lines.profile_tests((a, b, anchor(span)), 100, "H4", "TRL_FXR_M", 1, 78,
                                    slope=ray.slope)["passes"] for span in ages["inputs"]["fxr_spans"]])
            inputs = slopes["inputs"]
            for label, field, angle in (("atr_slope_ok", "slope_magnitudes", False),
                                        ("angle_ok", "angle_slope_magnitudes", True)):
                self.assertEqual(slopes["expected"][label], [
                    geometry.slope_tests(inputs["sign"] * D(magnitude), inputs["atr"],
                                         inputs["range"], require_angle=angle)["passes"]
                    for magnitude in inputs[field]])
            ranges = atr["inputs"]["true_ranges"]
            self.assertEqual(Fraction(atr["expected"]["SMA14_at_index13"]), geometry.atr_sma14(ranges[:14]))
            self.assertEqual(Fraction(atr["expected"]["SMA14_at_index14"]), geometry.atr_sma14(ranges[1:]))

    def test_fxr_positive_selection_requires_the_last_angle_bar(self):
        rows = []
        for i in range(390):
            base = D(90) + D(i)/100
            rows.append(candle(base + (0 if i in (290, 335, 380) else 2), D(115)))
        for path in (rows, mirror(rows)):
            source, bars = bars_for(path)
            inspector = lines.Inspector(source)
            for bar in bars[:-1]:
                inspector.observe(bar)
            before = inspector.snapshot("TRL_FXR_M")
            self.assertEqual([], before["profile_valid_ids"])
            self.assertTrue(any(c["reasons"] == ["ANGLE_HISTORY_UNAVAILABLE"] for c in before["candidates"]))
            inspector.observe(bars[-1])
            snapshot = selection.from_inspector(inspector, "TRL_FXR_M")
            self.assertEqual([(290, 335, 380)], [v.touch_indices for v in snapshot.selected])

    def test_overdue_next_bar_does_not_hide_a_received_wick(self):
        source, bars = bars_for(golden(35)["inputs"]["ohlc"])
        book = engine.Engine(source)
        for bar in bars[:48]:
            frame = book.observe(bar)
        self.assertEqual(1, len(frame["eligible_line_ids"]))
        old = frame["eligible_line_ids"]
        overdue = source.calendar.frame("H4")[49].end + source.calendar.delay
        late = replace(bars[48], available=overdue)
        with self.assertRaises(ValueError):
            book.observe(late, declared_triggers=old)
        frame = book.observe(late)
        self.assertEqual("MISSING_COMPLETED_BAR", frame["coverage_state"])
        self.assertEqual([], frame["eligible_line_ids"])
        self.assertEqual([], frame["action_line_ids"])
        self.assertEqual("POKED", book.report()["journal"]["lines"][0]["status"])
        self.assertEqual(book.report(), engine.Engine.restore(source, book.checkpoint()).report())

    def test_overdue_age_fact_requires_a_publication_at_the_snapshot_clock(self):
        source = source_for(550)
        journal = lifecycle.Journal(source)
        line = declared_line()
        start = declared_snapshot(source, (line,))
        line_id = journal.register(start, line.geometry_id)
        journal.validate(start, line_id)
        metadata = declared_snapshot(source, index=541).record()
        receipt = source.calendar.frame("H4")[542].end + source.calendar.delay
        metadata.update(coverage_state="MISSING_COMPLETED_BAR", as_of=receipt)
        def snapshot():
            return selection.SelectedSnapshot(data.canonical(metadata).decode(), ())
        with self.assertRaises(ValueError):
            journal.retire(snapshot(), line_id)
        metadata["latest_bar"]["available"] = receipt
        with self.assertRaises(ValueError):
            journal.trigger_many(snapshot(), [line_id])
        journal.retire(snapshot(), line_id)
        self.assertEqual("RETIRED", journal.states[0].status)

    def test_previously_consumed_subset_survives_automatic_candle_union(self):
        for rows in (union_rows(), mirror(union_rows())):
            with self.subTest(open_price=rows[0][0]):
                source, bars = bars_for(rows)
                book = engine.Engine(source, "TRL_BNC_E1")
                for bar in bars[:51]:
                    frame = book.observe(bar)
                self.assertEqual([[20, 32]], [v["touch_indices"] for v in frame["selection"]["ranked"]])
                book.observe(bars[51], declared_triggers=frame["eligible_line_ids"])
                for bar in bars[52:76]:
                    frame = book.observe(bar)
                self.assertEqual([[32, 72]], [v["touch_indices"] for v in frame["selection"]["ranked"]])
                self.assertEqual(1, len(frame["eligible_line_ids"]))
                frame = book.observe(bars[76])
                self.assertEqual([[20, 32, 72]], [v["touch_indices"] for v in frame["selection"]["ranked"]])
                self.assertEqual([], frame["eligible_line_ids"])
                report = book.report()
                self.assertEqual(["REGISTER", "VALID", "MERGE", "RETIRE"],
                                 [e["command"]["op"] for e in report["journal"]["events"][-4:]])
                groups = report["journal"]["groups"]
                self.assertEqual(3, len(groups))
                self.assertEqual(1, len({g["root"] for g in groups}))
                self.assertTrue(all(g["consumed"] for g in groups))
                resumed = engine.Engine.restore(source, book.checkpoint())
                self.assertEqual(book.observe(bars[77]), resumed.observe(bars[77]))
                self.assertEqual([], resumed.observe(bars[78])["action_line_ids"])

    def test_g30_invalid_extreme_reanchor_and_profile_local_subsets(self):
        rows = []
        for i in range(64):
            base = D(100) + (i - 20) * D(".1")
            low = base + {20: 0, 32: 0, 44: D(".02")}.get(i, 2)
            rows.append(candle(low, D(130)))
        for side, path in (("SHORT", rows), ("LONG", mirror(rows))):
            case = golden(30, side)
            for profile, expected in (("TRL_BRK3_E1", [20, 32, 44]), ("TRL_BRK2_E1", [32, 44])):
                with self.subTest(side=side, profile=profile):
                    _, frames = replay(path, profile)
                    frame = frames[-1]
                    self.assertEqual([expected], [v["touch_indices"] for v in frame["selection"]["ranked"]])
                    rejected = next(c for c in frame["candidates"] if
                                    (c["ray"]["a_index"], c["ray"]["b_index"]) == (20, 44))
                    self.assertIn("POKED", rejected["reasons"])
                    penetration = rejected["first_penetration"]
                    self.assertEqual(32, penetration["bar_index"])
                    self.assertEqual(Fraction(case["inputs"]["reanchored_penetration"]),
                                     selection.fraction(penetration["distance"]))

    def test_spec_9_3_late_confirmation_can_only_form_a_new_line(self):
        # Twelve warm-up bars put the example's first anchor beyond ATR seeding.
        rows = []
        for i in range(-12, 72):
            high = D("1.2000") - (i - 10) * D(".0001") - D(".0010")
            high = {10: D("1.2000"), 40: D("1.1970"), 52: D("1.1960"),
                    70: D("1.1942")}.get(i, high)
            low = D("1.1800")
            row = candle(low, high)
            if i in (52, 70):
                row[3] = "1.1949" if i == 52 else "1.1941"
            rows.append(row)
        for path in (rows, mirror(rows)):
            book, frames = replay(path, "TRL_BRK2_E1")
            states = {tuple(v["line"]["touch_indices"]): v for v in book.report()["journal"]["lines"]}
            old, new = states[(22, 52)], states[(52, 64)]
            self.assertEqual("POKED", old["status"])
            self.assertNotEqual(old["group_id"], new["group_id"])
            self.assertFalse(old["group_consumed"])
            self.assertEqual(old["line_id"], frames[63]["eligible_line_ids"][0])
            self.assertTrue(all(old["line_id"] not in f["eligible_line_ids"] for f in frames[64:]))
            self.assertIn(new["line_id"], frames[82]["eligible_line_ids"])
            self.assertNotIn(new["line_id"], frames[81]["eligible_line_ids"])

    def test_generated_competing_lines_rank_and_explain_every_prefix(self):
        for seed in (171, 172, 173):
            rng = random.Random(seed)
            rows = []
            for i in range(60):
                low = D(90) + D(i) / 10
                high = D(140) - D(i) / 10
                if i not in (16, 28, 40, 53):
                    low += 2 + D(rng.randrange(5)) / 100
                if i not in (19, 31, 43):
                    high -= 2 + D(rng.randrange(5)) / 100
                rows.append(candle(low, high))
            mirrored_ranks = []
            for path in (rows, mirror(rows)):
                book, frames = replay(path, "TRL_BRK3_E1")
                ranks = []
                for i, frame in enumerate(frames):
                    ranked = frame["selection"]["ranked"]
                    ranks.append([v["touch_indices"] for v in ranked])
                    valid = []
                    for c in frame["candidates"]:
                        self.assertEqual(c["profile_valid"], not c["reasons"])
                        if not c["profile_valid"]:
                            continue
                        line = selection.ValidatedLine.from_candidate(c, "TRL_BRK3_E1", "H4")
                        valid.append(line)
                        # Independent interpolation and raw wick comparison.
                        a, b = line.ray.a_index, line.ray.b_index
                        col = 2 if line.ray.kind == "support" else 1
                        start, end = Fraction(path[a][col]), Fraction(path[b][col])
                        for k in range(a, i + 1):
                            distance = Fraction(path[k][col]) - (start + (end-start)*(k-a)/(b-a))
                            self.assertGreaterEqual(distance if col == 2 else -distance, 0)
                    self.assertTrue(all(p["reasons"] for p in frame["pair_rejections"]))
                    discarded = frame["selection"]["discarded"]
                    self.assertTrue(all(v["reason"] and v["replaced_by"] for v in discarded))
                    self.assertCountEqual([v.geometry_id for v in valid],
                                          [v["geometry_id"] for v in ranked + discarded])
                    self.assertEqual(frame["selection"], selection.reduce_lines(valid[::-1]).record())
                    keys = [(-len(v["touch_ids"]), -v["age_bars"], -v["touch_indices"][-1],
                             v["touch_ids"][0], v["geometry_id"]) for v in ranked]
                    self.assertEqual(sorted(set(keys)), keys)
                self.assertEqual([[16, 28, 40, 53], [19, 31, 43]], ranks[-1])
                source, bars = bars_for(path)
                again = engine.Engine(source)
                prefix = [again.observe(b) for b in bars[:56]]
                self.assertEqual(prefix, frames[:56])
                self.assertEqual(frames[-1], book.observe(bars[-1]))
                mirrored_ranks.append(ranks)
            self.assertEqual(*mirrored_ranks)
