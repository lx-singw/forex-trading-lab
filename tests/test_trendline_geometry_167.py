"""Exact geometry acceptance on invented inputs; no eligible-line claim."""
from copy import deepcopy
from dataclasses import FrozenInstanceError, replace
from decimal import Decimal, localcontext
from fractions import Fraction as F
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from forex_demo_lab.trendline import data as d, geometry as g, pivots as p
from test_trendline_data_163 import calendar, descriptor, files, rows_for
from test_trendline_pivots_166 import bars_for, golden, source_for

ROOT = Path(__file__).resolve().parents[1]
FLAT = ["100","101","99","100"]


def observe(rows,frame="H4",source=None):
    source,bars = bars_for(rows,frame,source)
    stream = g.GeometryStream(source,frame)
    for bar in bars:stream.observe(bar)
    return stream,bars


def hourly_fixture(side="LONG"):
    prices = golden(35,side)["inputs"]["ohlc"]
    value = descriptor(calendar((24,)*9))
    rows = rows_for(value)[:len(prices)*4]
    for index,row in enumerate(rows):
        row.update(dict(zip(("open","high","low","close"),prices[index//4])))
    return value,rows


class TrendlineGeometry167Tests(unittest.TestCase):
    def test_exact_ray_interpolation_projection_and_mirror(self):
        long = g.Ray("resistance",17,"110",23,"108.8")
        short = g.Ray("support",17,"90",23,"91.2")
        self.assertEqual(-F(1,5),long.slope)
        self.assertEqual(F(519,5),long.value(48))
        self.assertEqual(F(101),long.project(48,14))
        for index in (0,17,20,23,29,48,62):
            self.assertEqual(200,long.value(index)+short.value(index))
        self.assertTrue(long.record()["geometry_only"])

    def test_ray_rejects_wrong_sign_horizontal_spacing_and_frame(self):
        for args in (("support",0,100,5,101),("support",0,100,6,100),
                     ("support",0,100,6,99),("resistance",0,100,6,101),
                     ("support",6,100,0,101),("other",0,100,6,101),
                     ("support",True,100,6,101),("support",0,100,6,101,"H1")):
            with self.subTest(args=args),self.assertRaises(ValueError):g.Ray(*args)
        self.assertEqual(F(1,6),g.Ray("support",0,100,6,101).slope)

    def test_float_bool_nonfinite_and_ambiguous_number_spellings_refused(self):
        for value in (True,1.0,float("nan"),Decimal("NaN"),Decimal("Infinity"),"1e2","1/3","+1"):
            with self.subTest(value=value),self.assertRaises(ValueError):g.exact(value)
        self.assertEqual(F(1,10),g.exact(Decimal("0.1")))

    def test_penetration_is_signed_exact_and_never_tolerance_rounded(self):
        ray = g.Ray("support",0,100,6,101)
        price = ray.value(7)
        tiny = F(1,10**30)
        self.assertEqual(0,ray.correct_side_distance(7,price))
        self.assertEqual(-tiny,ray.correct_side_distance(7,price-tiny))
        self.assertEqual(tiny,ray.correct_side_distance(7,price+tiny))
        mirrored = g.Ray("resistance",0,100,6,99)
        self.assertEqual(-tiny,mirrored.correct_side_distance(7,mirrored.value(7)+tiny))

    def test_true_range_accounts_for_both_gap_directions_and_zero(self):
        self.assertEqual(5,g.true_range(105,103,100))
        self.assertEqual(5,g.true_range(97,95,100))
        self.assertEqual(2,g.true_range(101,99,100))
        self.assertEqual(0,g.true_range(100,100,100))
        for args in ((99,101,100),(100,0,100),(101,99,0)):
            with self.assertRaises(ValueError):g.true_range(*args)

    def test_g38_sma14_differs_from_wilder_rma(self):
        ranges = [14]+[0]*14
        self.assertIsNone(g.atr_sma14(ranges[:13]))
        self.assertEqual(1,g.atr_sma14(ranges[:14]))
        self.assertEqual(0,g.atr_sma14(ranges))
        rma = F(1)*13/14+F(ranges[-1],14)
        self.assertEqual(F(13,14),rma)
        self.assertNotEqual(rma,g.atr_sma14(ranges))
        with self.assertRaises(ValueError):g.atr_sma14([0]*13+[-1])

    def test_first_atr_requires_prior_close_and_fourteen_true_ranges(self):
        for frame in ("H4","D1"):
            stream,bars = observe([FLAT]*15,frame)
            self.assertIsNone(stream.snapshots[0].true_range)
            self.assertIsNone(stream.snapshots[13].atr_sma14)
            self.assertEqual(14,stream.snapshots[14].true_range_count)
            self.assertEqual(2,stream.snapshots[14].atr_sma14)

    def test_g35_full_example_exact_atr_and_both_geometry_rays(self):
        for side in ("LONG","SHORT"):
            stream,_ = observe(golden(35,side)["inputs"]["ohlc"])
            self.assertEqual(F(263,140),stream.snapshots[-1].atr_sma14)
            self.assertIsNone(stream.snapshots[-1].angle_range)
            by_index = {v.bar_index:v for v in stream.journal}
            action = stream.ray(by_index[17].id,by_index[23].id)
            safety = stream.ray(by_index[20].id,by_index[26].id)
            self.assertEqual(F(519 if side == "LONG" else 481,5),action.value(48))
            self.assertEqual(F(514 if side == "LONG" else 486,5),safety.value(48))
            self.assertTrue(stream.test_ray(action)["passes"])

    def test_confirmed_pivot_metadata_and_same_clock_ordinal_gate(self):
        stream,_ = observe(golden(35)["inputs"]["ohlc"])
        a,b = [v for v in stream.journal if v.kind == "high"][:2]
        cursor = g.Cursor("H4",b.confirmed_at,b.confirmed_ordinal)
        self.assertEqual(-F(1,5),g.Ray.from_pivots(a,b,cursor).slope)
        for altered,clock in ((b,replace(cursor,ordinal=cursor.ordinal-1)),
                              (b,replace(cursor,available_at=cursor.available_at-1)),
                              (replace(b,segment=b.segment+1),cursor),
                              (replace(b,timeframe="D1"),cursor),
                              (replace(b,kind="low"),cursor),
                              (replace(b,radius=2),cursor),
                              (replace(b,confirmation_index=b.confirmation_index+1),cursor),
                              (replace(b,id="invalid"),cursor)):
            with self.assertRaises(ValueError):g.Ray.from_pivots(a,altered,clock)
        with self.assertRaises(ValueError):stream.ray(a.id,"0"*64)

    def test_confirmation_atr_and_tolerance_frozen_at_each_pivot(self):
        stream,bars = observe(golden(35)["inputs"]["ohlc"])
        for pivot in stream.journal:
            metrics = stream.confirmation_metrics(pivot.id)
            self.assertEqual(pivot.confirmation_index,metrics.bar_index)
            self.assertEqual(pivot.confirmed_at,metrics.available_at)
            self.assertEqual(metrics.atr_sma14/4,stream.touch_tolerance(pivot.id))
            self.assertIs(metrics,stream.snapshots[pivot.confirmation_index])
        with self.assertRaises(ValueError):stream.touch_tolerance("0"*64)

    def test_early_unavailable_pivot_atr_never_repaired_by_future_bars(self):
        rows = golden()["inputs"]["ohlc"]+[FLAT]*20
        source,bars = bars_for(rows)
        stream = g.GeometryStream(source)
        for bar in bars[:7]:stream.observe(bar)
        pivot = stream.journal[0]
        original = stream.confirmation_metrics(pivot.id)
        self.assertIsNone(stream.touch_tolerance(pivot.id))
        for bar in bars[7:]:stream.observe(bar)
        self.assertIsNotNone(stream.snapshots[-1].atr_sma14)
        self.assertIs(original,stream.confirmation_metrics(pivot.id))
        self.assertIsNone(stream.touch_tolerance(pivot.id))

    def test_atr_and_45degree_boundaries_are_inclusive_and_exact(self):
        for slope,passes in (("0.49",True),("0.5",True),("0.51",False)):
            self.assertEqual(passes,g.slope_tests(slope,1)["passes"])
        for slope,passes in (("0.39",True),("0.4",True),("0.41",False)):
            self.assertEqual(passes,g.slope_tests(slope,1,78,require_angle=True)["passes"])
        tiny = F(1,10**40)
        self.assertTrue(g.slope_tests(F(2,5),1,78,require_angle=True)["passes"])
        self.assertFalse(g.slope_tests(F(2,5)+tiny,1,78,require_angle=True)["passes"])
        self.assertTrue(g.slope_tests(F(2,5)-tiny,1,78,require_angle=True)["passes"])
        self.assertEqual({"numerator":1,"denominator":1},
                         g.slope_tests("0.4",1,78,require_angle=True)["normalized_angle_ratio"])

    def test_unavailable_zero_and_invalid_indicator_gates(self):
        for atr,range_,reason in ((None,78,"ATR_UNAVAILABLE"),(0,78,"ZERO_ATR"),
                                  (1,None,"ANGLE_HISTORY_UNAVAILABLE"),(1,0,"ZERO_ANGLE_RANGE")):
            result = g.slope_tests("0.1",atr,range_,require_angle=True)
            self.assertFalse(result["passes"]);self.assertIn(reason,result["reasons"])
        for kwargs in ({"atr":-1},{"atr":1,"price_range":-1,"require_angle":True},
                       {"atr":1,"require_angle":1}):
            with self.assertRaises(ValueError):g.slope_tests("0.1",**kwargs)
        self.assertTrue(g.slope_tests("0.1",1)["passes"])

    def test_angle_requires390_bars_and_rolls_off_old_extreme(self):
        stream,_ = observe([["100","110","90","100"]]+[FLAT]*390)
        self.assertIsNone(stream.snapshots[388].angle_range)
        self.assertEqual(20,stream.snapshots[389].angle_range)
        self.assertEqual(2,stream.snapshots[390].angle_range)
        self.assertEqual(390,stream.snapshots[-1].angle_bar_count)

    def test_missing_scheduled_bar_resets_all_indicator_windows(self):
        source,bars = bars_for([FLAT]*40)
        stream = g.GeometryStream(source)
        for bar in bars[:18]+bars[19:]:stream.observe(bar)
        reset = stream.snapshots[18]
        self.assertEqual((19,1,0),(reset.bar_index,reset.angle_bar_count,reset.true_range_count))
        self.assertIsNone(reset.true_range);self.assertIsNone(reset.atr_sma14)
        self.assertIsNone(stream.snapshots[31].atr_sma14)
        self.assertEqual(2,stream.snapshots[32].atr_sma14)
        self.assertEqual(1,stream.snapshots[-1].segment)

    def test_declared_weekend_preserves_prior_close_and_gap_true_range(self):
        source = d.Declaration.from_record(descriptor(calendar((24,24),(48,))))
        rows = [FLAT]*6+[["105","106","104","105"]]*6
        stream,_ = observe(rows,source=source)
        point = stream.snapshots[6]
        self.assertEqual(6,point.true_range)
        self.assertEqual(6,point.true_range_count)
        self.assertEqual(0,point.segment)
        self.assertEqual([],stream.report()["gaps"])

    def test_overdue_missing_bar_blocks_current_slope_assessment(self):
        source,bars = bars_for([FLAT]*18)
        stream = g.GeometryStream(source)
        for bar in bars[:15]:stream.observe(bar)
        ray = g.Ray("support",0,100,6,101)
        self.assertTrue(stream.test_ray(ray)["passes"])
        stream.advance(bars[15].available)
        self.assertFalse(stream.test_ray(ray)["passes"])
        self.assertIn("MISSING_COMPLETED_BAR",stream.test_ray(ray)["reasons"])
        stream.observe(bars[16])
        self.assertEqual("CURRENT",stream.coverage_state())
        self.assertIn("ATR_UNAVAILABLE",stream.test_ray(ray)["reasons"])

    def test_declared_closure_does_not_make_indicators_stale(self):
        source = d.Declaration.from_record(descriptor(calendar((24,24),(48,))))
        stream,bars = observe([FLAT]*6,source=source)
        stream.advance(bars[-1].available+24*3600000)
        self.assertEqual("CURRENT",stream.coverage_state())

    def test_duplicate_latest_retry_does_not_recompute_metrics(self):
        stream,bars = observe([FLAT]*15)
        before = stream.report()
        self.assertEqual((),stream.observe(bars[-1]))
        self.assertEqual(before,stream.report())
        stream.advance(bars[-1].available+1)
        self.assertEqual((),stream.observe(bars[-1]))
        self.assertEqual(15,len(stream.snapshots))

    def test_rejected_bars_are_atomic_including_lineage_collision(self):
        source,bars = bars_for([FLAT]*18)
        stream = g.GeometryStream(source)
        for bar in bars[:15]:stream.observe(bar)
        before = stream.report()
        for bar in (replace(bars[15],lineage=bars[0].lineage),bars[13],
                    replace(bars[15],available=bars[15].end),
                    replace(bars[15],timeframe="D1"),
                    replace(bars[14],close=Decimal("100.5"))):
            with self.assertRaises(ValueError):stream.observe(bar)
            self.assertEqual(before,stream.report())
        stream.observe(bars[15])
        self.assertEqual(16,len(stream.snapshots))

    def test_typed_inputs_and_frame_mismatch_refused(self):
        source = source_for()
        stream = g.GeometryStream(source)
        with self.assertRaises(ValueError):stream.observe({})
        with self.assertRaises(ValueError):stream.test_ray(g.Ray("support",0,100,6,101,"D1"))
        self.assertFalse(stream.test_ray(g.Ray("support",0,100,6,101))["passes"])

    def test_snapshots_and_report_cannot_rewrite_history(self):
        stream,_ = observe(golden(35)["inputs"]["ohlc"])
        before = stream.report()
        report = stream.report()
        report["snapshots"][0]["bar_index"] = 999
        report["confirmations"][0]["metrics"]["atr_sma14"]["numerator"] = -1
        self.assertEqual(before,stream.report())
        with self.assertRaises(FrozenInstanceError):stream.snapshots[0].bar_index = 999

    def test_future_suffix_change_keeps_published_prefix_and_confirmations(self):
        prefix = golden(35)["inputs"]["ohlc"]
        source = source_for(60)
        left,_ = observe(prefix+[FLAT]*5,source=source)
        right,_ = observe(prefix+[["110","120","80","110"]]*5,source=source)
        self.assertEqual(left.snapshots[:49],right.snapshots[:49])
        for pivot in left.journal[:5]:
            self.assertEqual(left.confirmation_metrics(pivot.id),right.confirmation_metrics(pivot.id))

    def test_low_decimal_context_does_not_change_exact_computations(self):
        rows = golden(35)["inputs"]["ohlc"]
        regular,_ = observe(rows)
        with localcontext() as context:
            context.prec = 2
            low,_ = observe(rows)
            ray = g.Ray("resistance",17,"110",23,"108.8")
            self.assertEqual(F(519,5),ray.value(48))
        self.assertEqual(regular.report(),low.report())

    def test_fork_stages_pivot_mutations_independently(self):
        source,bars = bars_for(golden()["inputs"]["ohlc"])
        original = p.PivotStream(source)
        for bar in bars[:6]:original.observe(bar)
        before = original.report()
        fork = original.fork()
        fork.observe(bars[6])
        self.assertEqual(before,original.report())
        self.assertEqual(1,len(fork.journal))
        original.observe(bars[6])
        self.assertEqual(fork.report(),original.report())

    def test_bindings_changed_refuse_before_mutation(self):
        source,bars = bars_for([FLAT]*18)
        stream = g.GeometryStream(source)
        stream.observe(bars[0]);before = stream.report()
        with patch.object(g,"bindings",return_value={}):
            with self.assertRaises(ValueError):stream.observe(bars[1])
            with self.assertRaises(ValueError):stream.report()
        self.assertEqual(before,stream.report())

    def test_invented_report_preserves_geometry_basis_and_orders_off(self):
        source = source_for(15,basis="mid_candles_source")
        stream,_ = observe([FLAT]*15,source=source)
        report = stream.report()
        self.assertEqual("B",report["data_level"])
        self.assertEqual("mid_candles_source",report["geometry_basis"])
        for key in ("returns_computed","qualified_market_source","demo_eligible","orders_available"):
            self.assertIs(False,report[key])
        self.assertEqual(0,report["market_cells_run"])

    def test_cli_exports_exact_g35_and_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            value,rows = hourly_fixture()
            meta,hours,_ = files(directory,value,rows)
            output = Path(directory)/"out"
            command = [sys.executable,str(ROOT/"scripts/trendline-geometry-167.py"),str(meta),str(hours),str(output),"--timeframe","H4"]
            run = subprocess.run(command,capture_output=True,text=True)
            self.assertEqual(0,run.returncode,run.stderr)
            report = json.loads((output/"geometry.json").read_text())
            self.assertEqual({"numerator":263,"denominator":140},report["frames"]["H4"]["latest"]["atr_sma14"])
            before = (output/"geometry.json").read_bytes()
            self.assertNotEqual(0,subprocess.run(command,capture_output=True).returncode)
            self.assertEqual(before,(output/"geometry.json").read_bytes())

    def test_cli_prefix_and_source_validation_cannot_bypass_loader(self):
        with tempfile.TemporaryDirectory() as directory:
            value,rows = hourly_fixture()
            meta,hours,value = files(directory,value,rows)
            def run(name,extra=()):
                output = Path(directory)/name
                result = subprocess.run([sys.executable,str(ROOT/"scripts/trendline-geometry-167.py"),str(meta),str(hours),str(output),"--timeframe","H4",*extra],capture_output=True,text=True)
                return result,output
            result,output = run("prefix",["--as-of",str(rows[27]["available_at"])])
            self.assertEqual(0,result.returncode,result.stderr)
            frame = json.loads((output/"geometry.json").read_text())["frames"]["H4"]
            self.assertEqual(7,len(frame["snapshots"]));self.assertIsNone(frame["latest"]["atr_sma14"])
            for change in ({"partition":"validation"},{"kind":"market_trendline_source"}):
                invalid = deepcopy(value);invalid.update(change);meta.write_text(json.dumps(invalid))
                result,output = run(next(iter(change)))
                self.assertNotEqual(0,result.returncode);self.assertFalse(output.exists())


if __name__ == "__main__":unittest.main()
