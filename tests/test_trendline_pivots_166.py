"""Invented pivot software acceptance, not qualified-market pattern evidence."""
from copy import deepcopy
from dataclasses import FrozenInstanceError
from decimal import Decimal, localcontext
import json
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from forex_demo_lab.elliott_full.contracts import Bar
from forex_demo_lab.elliott_full.patterns import confirmed
from forex_demo_lab.trendline import data as d
from forex_demo_lab.trendline import pivots as p
from test_trendline_data_163 import calendar, descriptor, files, rows_for, stream_for

ROOT = Path(__file__).resolve().parents[1]


def source_for(count=60,timeframe="H4",basis="bid_only"):
    per_day = 6 if timeframe == "H4" else 1
    value = descriptor(calendar((24,)*((count+per_day-1)//per_day)),basis=basis)
    return d.Declaration.from_record(value)


def bars_for(rows,timeframe="H4",source=None,offset=0):
    source = source or source_for(len(rows)+offset,timeframe)
    windows = source.calendar.frame(timeframe)
    bars = []
    for index,prices in enumerate(rows,offset):
        w = windows[index]
        bars.append(Bar(timeframe,w.start,w.end,w.end+2000,*prices,
                        d.digest(["invented_pivot_bar",timeframe,index,prices])))
    return source,bars


def golden(number=2,side="LONG"):
    book = json.loads((ROOT/"tests/trendline/fixtures/golden-161.json").read_text())
    return next(row for row in book["cases"] if row["id"] == f"G{number:02}_{side}")


def projection(values):
    return [(v.id,v.bar_index,v.occurred_at,v.confirmed_at,v.price,v.kind,v.radius) for v in values]


def legacy_projection(values,offset=0):
    return [(v.id,v.index+offset,v.time,v.available,v.price,v.kind,v.radius) for v in values]


class TrendlinePivots166Tests(unittest.TestCase):
    def test_handwritten_seven_bar_low_and_high_confirm_only_at_seventh(self):
        for side in ("LONG","SHORT"):
            case = golden(side=side)
            source,bars = bars_for(case["inputs"]["ohlc"])
            observer = p.PivotStream(source)
            for bar in bars[:6]:
                self.assertEqual((),observer.observe(bar))
                self.assertEqual((),observer.journal)
            result = observer.observe(bars[6])
            self.assertEqual(1,len(result))
            pivot = result[0]
            self.assertEqual(case["expected"]["kind"],pivot.kind)
            self.assertEqual(Decimal(case["expected"]["price"]),pivot.price)
            self.assertEqual((3,6),(pivot.bar_index,pivot.confirmation_index))
            self.assertEqual((bars[3].end,bars[6].available),(pivot.occurred_at,pivot.confirmed_at))
            self.assertEqual(7,pivot.confirmed_ordinal)

    def test_every_prefix_matches_existing_radius3_batch_on_both_frames(self):
        rng = random.Random(166)
        rows = []
        for _ in range(100):
            mid = Decimal(rng.randrange(1000,2000))/100
            rows.append([str(mid),str(mid+1),str(mid-1),str(mid)])
        for frame in ("H4","D1"):
            source,bars = bars_for(rows,frame)
            observer = p.PivotStream(source,frame)
            for index,bar in enumerate(bars):
                observer.observe(bar)
                journal,chain = confirmed(bars[:index+1],3)
                self.assertEqual(legacy_projection(journal),projection(observer.journal))
                self.assertEqual(legacy_projection(chain),projection(observer.alternating))

    def test_full49_candle_examples_keep_handwritten_pivot_indices(self):
        for side in ("LONG","SHORT"):
            case = golden(35,side)
            source,bars = bars_for(case["inputs"]["ohlc"])
            observer = p.PivotStream(source)
            for bar in bars:observer.observe(bar)
            action,safety = ("high","low") if side == "LONG" else ("low","high")
            self.assertEqual(case["expected"]["action_pivot_indices"],[v.bar_index for v in observer.journal if v.kind == action])
            self.assertEqual(case["expected"]["safety_pivot_indices"],[v.bar_index for v in observer.journal if v.kind == safety])

    def test_equal_high_low_and_dual_extreme_center_are_excluded(self):
        for mode in ("equal_high","equal_low","dual"):
            rows = [["100","103","97","100"] for _ in range(7)]
            if mode == "equal_high":rows[3] = ["100","103","98","100"]
            if mode == "equal_low":rows[3] = ["100","102","97","100"]
            if mode == "dual":rows[3] = ["100","105","95","100"]
            source,bars = bars_for(rows)
            observer = p.PivotStream(source)
            for bar in bars:observer.observe(bar)
            self.assertEqual((),observer.journal)

    def test_appended_or_mutated_future_suffix_never_rewrites_published_pivots(self):
        initial = golden()["inputs"]["ohlc"]
        source,bars = bars_for(initial+[["100","102","98","100"]]*14)
        observer = p.PivotStream(source)
        for bar in bars[:7]:observer.observe(bar)
        original = observer.journal
        for bar in bars[7:]:observer.observe(bar)
        self.assertEqual(original,observer.journal[:len(original)])
        changed = initial+[["90","110","80","90"]]*14
        _,other_bars = bars_for(changed,source=source)
        other = p.PivotStream(source)
        for bar in other_bars:other.observe(bar)
        self.assertEqual(original,other.journal[:len(original)])

    def test_future_file_hash_does_not_rename_earlier_pivots(self):
        source,bars = bars_for(golden()["inputs"]["ohlc"])
        other = source.record();other["input_sha256"] = "f"*64
        a,b = p.PivotStream(source),p.PivotStream(d.Declaration.from_record(other))
        for bar in bars:a.observe(bar);b.observe(bar)
        self.assertEqual(a.journal,b.journal)

    def test_journal_and_pivots_are_immutable_and_reports_are_copied(self):
        source,bars = bars_for(golden()["inputs"]["ohlc"])
        observer = p.PivotStream(source)
        for bar in bars:observer.observe(bar)
        with self.assertRaises(FrozenInstanceError):observer.journal[0].price = Decimal("0")
        report = observer.report();report["pivots"][0]["price"] = "0"
        self.assertNotEqual("0",observer.report()["pivots"][0]["price"])
        with self.assertRaises(AttributeError):observer.timeframe = "D1"

    def test_later_same_kind_extreme_changes_only_diagnostic_chain(self):
        rows = [["100","101","99","100"] for _ in range(22)]
        for index,high in ((3,"110"),(10,"108"),(17,"112")):
            rows[index] = ["100",high,"99","100"]
        source,bars = bars_for(rows)
        observer = p.PivotStream(source)
        for bar in bars[:7]:observer.observe(bar)
        first = observer.journal[0]
        for bar in bars[7:]:observer.observe(bar)
        self.assertEqual([3,10,17],[v.bar_index for v in observer.journal])
        self.assertEqual([17],[v.bar_index for v in observer.alternating])
        self.assertEqual(first,observer.journal[0])

    def test_missing_scheduled_bar_resets_neighbourhood_and_segments_view(self):
        rows = golden()["inputs"]["ohlc"]*3
        source,bars = bars_for(rows)
        observer = p.PivotStream(source)
        for bar in bars[:7]:observer.observe(bar)
        original = observer.journal
        for bar in bars[8:14]:observer.observe(bar)
        self.assertEqual(original,observer.journal)
        self.assertEqual((),observer.alternating)
        self.assertEqual("INSUFFICIENT_CONTIGUOUS_BARS",observer.report()["window_state"])
        self.assertEqual((7,7),(observer.report()["gaps"][0]["missing_first_index"],observer.report()["gaps"][0]["missing_last_index"]))
        for bar in bars[14:]:observer.observe(bar)
        self.assertEqual(original,observer.journal[:len(original)])
        self.assertTrue(all(v.segment == 1 for v in observer.journal[len(original):]))

    def test_initial_missing_prefix_is_reported_without_inventing_left_neighbours(self):
        source,bars = bars_for(golden()["inputs"]["ohlc"]*2)
        observer = p.PivotStream(source)
        observer.observe(bars[3])
        self.assertEqual((),observer.journal)
        self.assertEqual({"missing_first_index":0,"missing_last_index":2,"observed_at":bars[3].available},observer.report()["gaps"][0])

    def test_declared_weekend_closure_is_not_a_missing_bar(self):
        source = d.Declaration.from_record(descriptor(calendar((24,24),(48,))))
        _,bars = bars_for(golden()["inputs"]["ohlc"],source=source)
        observer = p.PivotStream(source)
        for bar in bars:observer.observe(bar)
        self.assertEqual(1,len(observer.journal))
        self.assertEqual(6,observer.journal[0].confirmation_index)
        self.assertEqual([],observer.report()["gaps"])

    def test_elapsed_clock_alone_cannot_supply_missing_confirmation_bars(self):
        source,bars = bars_for(golden()["inputs"]["ohlc"])
        observer = p.PivotStream(source)
        for bar in bars[:6]:observer.observe(bar)
        observer.advance(observer.clock+3*3600000)
        self.assertEqual((),observer.journal)
        self.assertEqual(1,len(observer.observe(bars[6])))

    def test_late_backfill_rejects_without_restoring_or_mutating_past(self):
        source,bars = bars_for(golden()["inputs"]["ohlc"]*2)
        observer = p.PivotStream(source)
        for bar in bars[:3]+bars[4:9]:observer.observe(bar)
        before = observer.report()
        late = bars[3].record();late["available"] = observer.clock+1
        with self.assertRaisesRegex(ValueError,"backfill"):observer.observe(Bar(**late))
        self.assertEqual(before,observer.report())

    def test_identical_latest_retry_does_not_reconfirm_or_refresh_clock(self):
        source,bars = bars_for(golden()["inputs"]["ohlc"])
        observer = p.PivotStream(source)
        for bar in bars:observer.observe(bar)
        observer.advance(observer.clock+1000)
        before = observer.report()
        self.assertEqual((),observer.observe(bars[-1]))
        self.assertEqual(before,observer.report())

    def test_conflicting_duplicate_rejects_atomically(self):
        source,bars = bars_for(golden()["inputs"]["ohlc"])
        observer = p.PivotStream(source)
        observer.observe(bars[0]);before = observer.report()
        value = bars[0].record();value["lineage"] = "f"*64
        with self.assertRaises(ValueError):observer.observe(Bar(**value))
        self.assertEqual(before,observer.report())

    def test_same_clock_confirmations_retain_distinct_publication_ordinals(self):
        rows = [["100","101","99","100"] for _ in range(15)]
        rows[3] = ["100","110","99","100"]
        rows[10] = ["100","111","99","100"]
        source,bars = bars_for(rows)
        now = source.calendar.end
        observer = p.PivotStream(source)
        for bar in bars:
            value = bar.record();value["available"] = now
            observer.observe(Bar(**value))
        self.assertEqual([now,now],[v.confirmed_at for v in observer.journal])
        self.assertEqual([7,14],[v.confirmed_ordinal for v in observer.journal])

    def test_source_frame_timestamp_and_lineage_validation_is_atomic(self):
        source,bars = bars_for(golden()["inputs"]["ohlc"])
        observer = p.PivotStream(source);before = observer.report()
        for key,value in (("timeframe","H1"),("start",bars[0].start+1),("lineage","not_sha256")):
            row = bars[0].record();row[key] = value
            with self.subTest(key=key),self.assertRaises(ValueError):observer.observe(Bar(**row))
            self.assertEqual(before,observer.report())

    def test_backward_receipt_and_advance_reject_without_mutation(self):
        source,bars = bars_for(golden()["inputs"]["ohlc"])
        observer = p.PivotStream(source)
        observer.advance(bars[1].available+1)
        before = observer.report()
        with self.assertRaises(ValueError):observer.observe(bars[1])
        with self.assertRaises(ValueError):observer.advance(source.calendar.start)
        self.assertEqual(before,observer.report())

    def test_bound_rejects_before_state_mutation(self):
        source,bars = bars_for(golden()["inputs"]["ohlc"])
        observer = p.PivotStream(source)
        for bar in bars[:6]:observer.observe(bar)
        before = observer.report()
        with patch.object(p,"MAX_BARS",6):
            with self.assertRaises(ValueError):observer.observe(bars[6])
        self.assertEqual(before,observer.report())

    def test_radius_is_frozen_and_market_source_kind_is_refused(self):
        source = source_for()
        for radius in (2,4,8,True,None):
            with self.assertRaises(ValueError):p.PivotStream(source,radius=radius)
        with self.assertRaises(ValueError):p.PivotStream(source,"H1")
        market = source.record();market["kind"] = "qualified_market"
        with self.assertRaises(ValueError):p.PivotStream(d.Declaration(d.canonical(market).decode()))

    def test_mid_geometry_pivots_never_claim_executable_or_demo_data(self):
        source = source_for(7,basis="mid_candles_source")
        _,bars = bars_for(golden()["inputs"]["ohlc"],source=source)
        observer = p.PivotStream(source)
        for bar in bars:observer.observe(bar)
        report = observer.report()
        self.assertEqual("mid_candles_source",report["geometry_basis"])
        self.assertFalse(report["qualified_market_source"])
        self.assertFalse(report["demo_eligible"])
        self.assertFalse(report["orders_available"])

    def test_unchanged_reference_output_in_low_decimal_precision(self):
        source,bars = bars_for(golden()["inputs"]["ohlc"])
        observer = p.PivotStream(source)
        with localcontext() as context:
            context.prec = 3
            for bar in bars:observer.observe(bar)
        self.assertEqual(legacy_projection(confirmed(bars,3)[0]),projection(observer.journal))

    def test_binding_change_blocks_new_observation_and_report(self):
        source,bars = bars_for(golden()["inputs"]["ohlc"])
        observer = p.PivotStream(source)
        with patch.object(p,"bindings",return_value={}):
            with self.assertRaises(ValueError):observer.observe(bars[0])
            with self.assertRaises(ValueError):observer.report()
        self.assertEqual(0,observer.report()["observed_bars"])

    def test_phase2_holiday_and_maintenance_closures_do_not_create_missing_bars(self):
        for reason in ("holiday","maintenance"):
            cal = calendar((24,24),(24,))
            cal["segments"][1]["reason"] = reason
            report = stream_for(descriptor(cal)).report()
            self.assertEqual(48,report["coverage"]["H1"]["complete_count"])
            self.assertEqual([],report["coverage"]["H1"]["missing_starts"])

    def test_bar_aggregation_to_pivots_matches_batch_on_the_same_publications(self):
        value = descriptor(calendar((24,)*10))
        source = d.Declaration.from_record(value)
        raw = rows_for(value)
        candles = golden(35)["inputs"]["ohlc"]
        for index,prices in enumerate(candles):
            for row in raw[index*4:index*4+4]:
                row.update(dict(zip(("open","high","low","close"),prices)))
        stream = stream_for(value,raw[:len(candles)*4])
        observer = p.PivotStream(source)
        bars = [b for b in stream.bars() if b.timeframe == "H4"]
        for bar in bars:observer.observe(bar)
        self.assertEqual(legacy_projection(confirmed(bars,3)[0]),projection(observer.journal))
        self.assertEqual([17,23,29],[v.bar_index for v in observer.journal if v.kind == "high"])

    def test_public_CLI_honors_prefix_cursor_and_refuses_overwrite(self):
        script = ROOT/"scripts/trendline-pivots-166.py"
        with tempfile.TemporaryDirectory() as tmp:
            value = descriptor(calendar((24,)*10));raw = rows_for(value)
            candles = golden(35)["inputs"]["ohlc"]
            for index,prices in enumerate(candles):
                for row in raw[index*4:index*4+4]:row.update(dict(zip(("open","high","low","close"),prices)))
            meta,hours,_ = files(tmp,value,raw[:len(candles)*4])
            out = Path(tmp)/"out"
            command = [sys.executable,str(script),str(meta),str(hours),str(out)]
            result = subprocess.run(command,capture_output=True,text=True,check=True)
            self.assertEqual(5,json.loads(result.stdout)["confirmed"]["H4"])
            original = (out/"pivots.json").read_bytes()
            self.assertNotEqual(0,subprocess.run(command,capture_output=True).returncode)
            self.assertEqual(original,(out/"pivots.json").read_bytes())
            early = Path(tmp)/"early"
            now = raw[3*4+3]["available_at"]
            subprocess.run([sys.executable,str(script),str(meta),str(hours),str(early),"--as-of",str(now)],capture_output=True,check=True)
            self.assertEqual([],json.loads((early/"pivots.json").read_text())["frames"]["H4"]["pivots"])

    def test_public_CLI_has_no_validation_or_market_bypass(self):
        script = ROOT/"scripts/trendline-pivots-166.py"
        with tempfile.TemporaryDirectory() as tmp:
            value = descriptor(partition="validation")
            meta,hours,_ = files(tmp,value)
            out = Path(tmp)/"out"
            command = [sys.executable,str(script),str(meta),str(hours),str(out)]
            self.assertNotEqual(0,subprocess.run(command,capture_output=True).returncode)
            self.assertFalse(out.exists())
            value = json.loads(meta.read_text());value["kind"] = "qualified_market"
            meta.write_text(json.dumps(value))
            self.assertNotEqual(0,subprocess.run(command,capture_output=True).returncode)
            self.assertFalse(out.exists())


if __name__ == "__main__":
    unittest.main()
