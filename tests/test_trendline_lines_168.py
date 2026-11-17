"""Invented component and causal-prefix acceptance for Phase4 line inspection."""
from copy import deepcopy
from dataclasses import replace
from decimal import Decimal, localcontext
from fractions import Fraction as F
import json
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from forex_demo_lab.trendline import data as d, geometry as g, lines as l, pivots as p
from test_trendline_data_163 import files
from test_trendline_geometry_167 import hourly_fixture
from test_trendline_pivots_166 import bars_for, golden, source_for

ROOT = Path(__file__).resolve().parents[1]


def pivot(index,price=None,kind="high",frame="H4",segment=0):
    price = Decimal(str(price)) if price is not None else Decimal(10000)-Decimal(index)/100
    return p.Pivot(d.digest(["declared_component_pivot",index,str(price),kind,frame,segment]),
                   kind,index,index+3,index*100+1,(index+3)*100+2,index+4,price,frame,3,segment)


def scan(indices=(0,6,12),prices=("110","108.8","107.6"),side="LONG",tolerance="0.5"):
    values = tuple(pivot(i,price if side == "LONG" else 200-Decimal(price),
                         "high" if side == "LONG" else "low") for i,price in zip(indices,prices))
    a,b = values[0],values[-1]
    ray = g.Ray("resistance" if side == "LONG" else "support",a.bar_index,a.price,b.bar_index,b.price)
    return l.scan_touches(ray,a,b,values,{p.id:F(tolerance) for p in values})


def inspect_g35(side="LONG",length=None,profile="TRL_BRK3_E1",role="action_break"):
    source,bars = bars_for(golden(35,side)["inputs"]["ohlc"])
    return l.inspect(source,bars[:length],profile=profile,role=role),source,bars


def candidate(report,a=17,b=23):
    return next(c for c in report["candidates"] if (c["ray"]["a_index"],c["ray"]["b_index"]) == (a,b))


def support_rows(count=75,centres=(20,32,44),seed=168):
    rng = random.Random(seed)
    rows = []
    for i in range(count):
        low = Decimal(100)+Decimal(i)/10+(0 if i in centres else Decimal(2)+Decimal(rng.randrange(0,5))/100)
        rows.append(["130","150",str(low),"130"])
    return rows


class TrendlineLines168Tests(unittest.TestCase):
    def test_all_same_kind_pairs_and_shape_rejections_are_deterministic(self):
        values = (pivot(0,110),pivot(4,109),pivot(10,108),pivot(20,109))
        cursor = g.Cursor("H4",100000,100000)
        result = l.enumerate_pairs(values,cursor,30,0)
        self.assertEqual([(0,10),(0,20),(4,10)],[(a.bar_index,b.bar_index) for a,b,_ in result.pairs])
        self.assertEqual(["ANCHOR_TOO_CLOSE","WRONG_SLOPE","WRONG_SLOPE"],[r[2] for r in result.rejected])
        self.assertEqual(result,l.enumerate_pairs(tuple(reversed(values)),cursor,30,0))

    def test_g06_earliest_touch_skips_anchor_b_and_rejects_pair(self):
        for side in ("LONG","SHORT"):
            case = golden(6,side)
            values = tuple(pivot(i,v,"high" if side == "LONG" else "low")
                           for i,v in zip(case["inputs"]["candidate_indices"],case["inputs"]["pivot_prices"]))
            ray = g.Ray("resistance" if side == "LONG" else "support",0,values[0].price,12,values[-1].price)
            result = l.scan_touches(ray,values[0],values[-1],values,{v.id:F(1,2) for v in values})
            self.assertEqual(case["expected"]["accepted_indices"],[p.bar_index for p in result.touches])
            self.assertEqual((case["expected"]["reason"],),result.reasons)

    def test_g05_correct_side_tolerance_boundary_and_tiny_penetration(self):
        for side in ("LONG","SHORT"):
            case = golden(5,side);inputs = case["inputs"]
            anchor_prices = (110,Decimal("108.8")) if side == "LONG" else (90,Decimal("91.2"))
            kind = "high" if side == "LONG" else "low"
            a,b = pivot(0,anchor_prices[0],kind),pivot(6,anchor_prices[1],kind)
            ray = g.Ray(inputs["kind"],0,a.price,6,b.price)
            for key,accepted in (("pivot_price",True),("at_boundary",True),
                                 ("outside_tolerance",False),("penetrating",False)):
                touch = pivot(18,inputs[key],kind)
                values = (a,b,touch)
                result = l.scan_touches(ray,a,b,values,{v.id:F(1,2) for v in values})
                self.assertEqual(accepted,touch in result.touches)

    def test_g07_spacing_is_inclusive_at_six(self):
        for index,accepted in zip((17,18,19),(False,True,True)):
            a,b,c = pivot(0,110),pivot(12,"107.6"),pivot(index,str(Decimal(110)-Decimal(index)/5))
            ray = g.Ray("resistance",0,a.price,12,b.price)
            result = l.scan_touches(ray,a,b,(a,b,c),{v.id:F(1,2) for v in (a,b,c)})
            self.assertEqual(accepted,c in result.touches)

    def test_unavailable_anchor_atr_cannot_count_as_a_qualified_touch(self):
        a,b = pivot(0,110),pivot(6,"108.8")
        ray = g.Ray("resistance",0,a.price,6,b.price)
        for unavailable in (None,F(0)):
            result = l.scan_touches(ray,a,b,(a,b),{a.id:unavailable,b.id:F(1,2)})
            self.assertIn("ANCHOR_ATR_UNAVAILABLE",result.reasons)
            self.assertNotIn(a,result.touches)

    def test_missing_negative_or_wrong_anchor_tolerance_binding_refused(self):
        a,b = pivot(0,110),pivot(6,"108.8")
        ray = g.Ray("resistance",0,a.price,6,b.price)
        for values in ({a.id:F(1,2)},{a.id:-1,b.id:F(1,2)}):
            with self.assertRaises(ValueError):l.scan_touches(ray,a,b,(a,b),values)
        with self.assertRaises(ValueError):l.scan_touches(ray,a,replace(b,price=Decimal(108)),(a,b),{a.id:1,b.id:1})

    def test_g08_exactly_two_and_three_plus_profiles_are_disjoint(self):
        for side in ("LONG","SHORT"):
            case = golden(8,side)
            actual2,actual3 = [],[]
            for count in case["inputs"]["touch_counts"]:
                touches = tuple(pivot(i*6) for i in range(count))
                actual2.append(l.profile_tests(touches,40,"H4","TRL_BRK2_E1",1,slope=F(1,10))["passes"])
                actual3.append(l.profile_tests(touches,40,"H4","TRL_BRK3_E1",1,slope=F(1,10))["passes"])
            self.assertEqual(case["expected"]["BRK2"],actual2)
            self.assertEqual(case["expected"]["BRK3"],actual3)

    def test_g09_age29_30_and_formation_span89_90(self):
        case = golden(9)
        touches = tuple(pivot(i) for i in (0,6,12))
        actual = [l.profile_tests(touches,age,"H4","TRL_BRK3_E1",1,slope=F(1,10))["passes"] for age in (29,30)]
        self.assertEqual(case["expected"]["core_age_ok"],actual)
        actual = []
        for span in (89,90):
            points = tuple(pivot(i) for i in (0,6,span))
            result = l.profile_tests(points,100,"H4","TRL_FXR_M",1,78,slope=F(1,10))
            actual.append(result["passes"])
            self.assertEqual(span,result["formation_span_bars"])
            self.assertEqual(100,result["age_bars"])
        self.assertEqual(case["expected"]["fxr_span_ok"],actual)

    def test_d1_diagnostic_inherits_brk3_age15_and_frame_contract(self):
        touches = tuple(pivot(i,frame="D1") for i in (0,6,12))
        with self.assertRaises(ValueError):l.profile_tests(touches,14,"D1","D1_BRK3",1,slope=F(1,10))
        self.assertTrue(l.profile_tests(touches,15,"D1","D1_BRK3",1,slope=F(1,10))["passes"])
        self.assertFalse(l.profile_tests(touches[:2],15,"D1","D1_BRK3",1,slope=F(1,10))["passes"])
        for args in (("D1_BRK3","H4","full"),("TRL_BRK3_E1","D1","full"),
                     ("D1_BRK3","D1","action_break"),("TRL_BNC_E1","H4","action_break"),
                     ("unknown","H4","full"),("TRL_BRK3_E1","H4","unknown")):
            with self.assertRaises(ValueError):l.validate_profile(*args)

    def test_bounce_prior_touch_profile_and_slope_failures(self):
        touches = tuple(pivot(i) for i in (0,6))
        result = l.profile_tests(touches,30,"H4","TRL_BNC_E1",1,slope=F(1,10))
        self.assertTrue(result["passes"])
        for atr,reason in ((None,"ATR_UNAVAILABLE"),(0,"ZERO_ATR"),(F(1,10),"SLOPE_TOO_STEEP")):
            self.assertIn(reason,l.profile_tests(touches,30,"H4","TRL_BNC_E1",atr,slope=F(1,10))["reasons"])
        with self.assertRaises(ValueError):l.profile_tests(touches,6,"H4","TRL_BNC_E1",1,slope=0)

    def test_fxr_needs_angle_history_even_with_long_enough_span(self):
        touches = tuple(pivot(i) for i in (0,45,90))
        result = l.profile_tests(touches,100,"H4","TRL_FXR_M",1,slope=F(1,10))
        self.assertIn("ANGLE_HISTORY_UNAVAILABLE",result["reasons"])
        self.assertNotIn("FORMATION_TOO_SHORT",result["reasons"])

    def test_g04_wick_poke_survives_later_confirmation_cursor(self):
        for side in ("LONG","SHORT"):
            case = golden(4,side);inputs = case["inputs"]
            support = side == "SHORT"
            ray = g.Ray(inputs["kind"],0,90 if support else 110,6,"91.2" if support else "108.8")
            price = inputs["wick_low"] if support else inputs["wick_high"]
            close = inputs["wick_close"]
            row = [close,"110" if support else price,price if support else "90",close]
            _,bars = bars_for([row],offset=29)
            for now in (30,32,40):
                self.assertEqual((29,F(case["expected"]["penetration"])),l.penetration(ray,[(29,bars[0])],now))

    def test_equality_is_not_poke_but_sub_tick_penetration_is(self):
        ray = g.Ray("support",0,100,6,"100.6")
        _,bars = bars_for([["103","105","103","103"]],offset=30)
        self.assertIsNone(l.penetration(ray,[(30,bars[0])],30))
        bad = replace(bars[0],low=Decimal("102.999999999999999999"))
        self.assertEqual((30,F(1,10**18)),l.penetration(ray,[(30,bad)],30))

    def test_g31_current_protection_bar_is_included_and_break_exception_is_explicit(self):
        for side in ("LONG","SHORT"):
            case = golden(31,side);inputs = case["inputs"]
            support = side == "LONG"
            ray = g.Ray(inputs["safety_kind"],0,100,6,"100.6" if support else "99.4")
            close = inputs["current_close"]
            row = [close,"110" if support else inputs["current_high"],inputs["current_low"] if support else "90",close]
            _,bars = bars_for([row],offset=30)
            self.assertIsNotNone(l.penetration(ray,[(30,bars[0])],30))
            self.assertIsNone(l.penetration(ray,[(30,bars[0])],30,include_current=False))
            self.assertIsNotNone(l.penetration(ray,[(30,bars[0])],31,include_current=False))

    def test_g33_cap256_257_blocks_whole_search_without_truncation(self):
        cursor = g.Cursor("H4",1000000,1000000)
        values = tuple(pivot(i) for i in range(257))
        complete = l.enumerate_pairs(values[:256],cursor,600,0)
        self.assertFalse(complete.search_incomplete);self.assertTrue(complete.pairs)
        blocked = l.enumerate_pairs(values,cursor,600,0)
        self.assertTrue(blocked.search_incomplete)
        self.assertEqual(257,len(blocked.pivots));self.assertEqual(257,blocked.high_count)
        self.assertEqual((),blocked.pairs);self.assertEqual((),blocked.rejected)
        recovered = l.enumerate_pairs(values,cursor,601,0)
        self.assertFalse(recovered.search_incomplete);self.assertEqual(256,recovered.high_count)

    def test_window_is_inclusive600_before_cap_and_both_kinds_are_separate(self):
        cursor = g.Cursor("H4",1000000,1000000)
        values = (pivot(0,110),pivot(6,109),pivot(12,100,"low"))
        at600 = l.enumerate_pairs(values,cursor,600,0)
        self.assertEqual((2,1),(at600.high_count,at600.low_count))
        self.assertEqual(1,len(at600.pairs))
        at601 = l.enumerate_pairs(values,cursor,601,0)
        self.assertEqual((1,1),(at601.high_count,at601.low_count))

    def test_incomplete_search_report_blocks_all_candidates_with_reason(self):
        source,bars = bars_for(support_rows())
        stress = l.enumerate_pairs(tuple(pivot(i) for i in range(257)),g.Cursor("H4",1000000,1000000),600,0)
        with patch.object(l,"enumerate_pairs",return_value=stress):
            report = l.inspect(source,bars)
        self.assertTrue(report["search_incomplete"])
        self.assertIn("SEARCH_INCOMPLETE",report["snapshot_reasons"])
        self.assertEqual([],report["profile_valid_ids"])
        self.assertEqual([],report["candidates"])
        self.assertFalse(report["entry_ready"])

    def test_gaps_do_not_bridge_segments_but_cap_counts_window_first(self):
        cursor = g.Cursor("H4",1000000,1000000)
        result = l.enumerate_pairs((pivot(0,110),pivot(6,109,segment=1),pivot(12,108,segment=1)),cursor,30,1)
        self.assertEqual(3,result.high_count)
        self.assertEqual([(6,12)],[(a.bar_index,b.bar_index) for a,b,_ in result.pairs])

    def test_future_or_conflicting_pivot_metadata_cannot_enter_search(self):
        a,b = pivot(0,110),pivot(6,109)
        cursor = g.Cursor("H4",100000,100000)
        for values in ((a,a),(a,replace(b,id=a.id)),(a,replace(b,bar_index=0)),
                       (a,replace(b,radius=True)),(a,replace(b,timeframe="D1")),
                       (a,replace(b,confirmed_ordinal=0)),(a,replace(b,confirmation_index=10)),
                       (a,replace(b,confirmed_ordinal=cursor.ordinal+1)),
                       (a,replace(b,price="109")),(a,replace(b,price=109.0)),
                       (a,replace(b,confirmed_at=cursor.available_at+1))):
            with self.assertRaises(ValueError):l.enumerate_pairs(values,cursor,30,0)
        with self.assertRaises(ValueError):l.enumerate_pairs((a,b),cursor,8,0)
        with self.assertRaises(ValueError):l.enumerate_pairs((a,b),g.Cursor("H4",b.confirmed_at,b.confirmed_ordinal-1),30,0)

    def test_g35_full_prefix_action_and_current_bar_poke_differ(self):
        for side in ("LONG","SHORT"):
            result,source,bars = inspect_g35(side)
            line = candidate(result)
            self.assertEqual([17,23,29],line["touches"]["touch_indices"])
            self.assertTrue(line["profile_valid"]);self.assertIsNone(line["first_penetration"])
            full = l.inspect(source,bars)
            poked = candidate(full)
            self.assertFalse(poked["profile_valid"])
            self.assertEqual(48,poked["first_penetration"]["bar_index"])
            self.assertIn("POKED",poked["reasons"])

    def test_g35_first_age_eligibility47_preserves_duplicate_geometries_for_next_sprint(self):
        early,_,_ = inspect_g35(length=47)
        ready,_,_ = inspect_g35(length=48)
        self.assertIn("LINE_TOO_YOUNG",candidate(early)["reasons"])
        self.assertTrue(candidate(ready)["profile_valid"])
        self.assertEqual(2,len(ready["profile_valid_ids"]))
        self.assertEqual([17,23,29],candidate(ready,17,29)["touches"]["touch_indices"])
        self.assertIs(False,ready["entry_ready"])

    def test_g35_brk2_does_not_admit_three_touches(self):
        result,_,_ = inspect_g35(profile="TRL_BRK2_E1")
        self.assertIn("TOUCH_COUNT",candidate(result)["reasons"])

    def test_duplicate_retry_identical_prefix_is_idempotent_and_reports_defensive(self):
        result,source,bars = inspect_g35()
        before = deepcopy(result)
        retried = l.inspect(source,bars+[bars[-1]],role="action_break")
        self.assertEqual(result,retried)
        result["candidates"][0]["reasons"].append("modified")
        self.assertEqual(before,l.inspect(source,bars,role="action_break"))

    def test_source_identity_does_not_rename_causal_geometry(self):
        original,source,bars = inspect_g35()
        value = source.record();value["input_sha256"] = "1"*64
        other = l.inspect(d.Declaration.from_record(value),bars,role="action_break")
        self.assertNotEqual(original["input_sha256"],other["input_sha256"])
        self.assertEqual(original["candidates"],other["candidates"])

    def test_future_suffix_does_not_mutate_previously_returned_prefix(self):
        source,bars = bars_for(support_rows())
        prefix = l.inspect(source,bars[:65])
        before = deepcopy(prefix)
        changed = list(bars)
        changed[-1] = replace(changed[-1],low=Decimal(1))
        l.inspect(source,changed)
        self.assertEqual(before,prefix)
        self.assertEqual(before,l.inspect(source,bars[:65]))

    def test_missing_scheduled_bar_breaks_old_candidate_segment(self):
        source,bars = bars_for(support_rows())
        result = l.inspect(source,bars[:50]+bars[51:])
        self.assertEqual([],result["profile_valid_ids"])
        self.assertEqual([],result["candidates"])

    def test_missing_due_bar_blocks_otherwise_profile_valid_snapshot(self):
        source,bars = bars_for(support_rows())
        complete = l.inspect(source,bars[:70])
        self.assertTrue(complete["profile_valid_ids"])
        stale = l.inspect(source,bars[:70],as_of=bars[70].available)
        self.assertEqual("MISSING_COMPLETED_BAR",stale["coverage_state"])
        self.assertEqual([],stale["profile_valid_ids"])
        self.assertTrue(all("MISSING_COMPLETED_BAR" in c["reasons"] for c in stale["candidates"]))

    def test_explicit_prefix_refuses_future_wrong_frame_and_backfill(self):
        source,bars = bars_for(support_rows())
        for values,kwargs in ((bars,{"as_of":bars[-2].available}),
                              (bars[:5]+[bars[3]],{}),([replace(bars[0],timeframe="D1")],{})):
            with self.assertRaises(ValueError):l.inspect(source,values,**kwargs)
        value = source.record();value["kind"] = "market_trendline_source"
        with self.assertRaises(ValueError):l.inspect(d.Declaration(json.dumps(value)),bars)

    def test_empty_snapshot_and_code_binding_changes_fail_closed(self):
        source = source_for()
        empty = l.inspect(source,[])
        self.assertEqual([],empty["profile_valid_ids"]);self.assertIsNone(empty["bar_index"])
        original = l.bindings()
        with patch.object(l,"bindings",side_effect=[original,{}]):
            with self.assertRaises(ValueError):l.inspect(source,[])

    def test_seeded_paths_valid_lines_have_no_pokes_and_mirror_exactly(self):
        for seed in range(6):
            rows = support_rows(seed=seed)
            source,bars = bars_for(rows)
            long = l.inspect(source,bars)
            mirrored = [[str(Decimal(300)-Decimal(row[i])) for i in (0,2,1,3)] for row in rows]
            _,short_bars = bars_for(mirrored,source=source)
            short = l.inspect(source,short_bars)
            self.assertTrue(long["profile_valid_ids"])
            self.assertEqual(len(long["candidates"]),len(short["candidates"]))
            for left,right in zip(long["candidates"],short["candidates"]):
                self.assertEqual(left["reasons"],right["reasons"])
                self.assertEqual(left["touches"]["touch_indices"],right["touches"]["touch_indices"])
                if left["profile_valid"]:
                    self.assertIsNone(left["first_penetration"])
                    ray = g.Ray("support",left["ray"]["a_index"],bars[left["ray"]["a_index"]].low,
                                left["ray"]["b_index"],bars[left["ray"]["b_index"]].low)
                    self.assertTrue(all(bar.low >= ray.value(i) for i,bar in enumerate(bars) if i > ray.a_index))

    def test_later_confirmed_pivot_never_repairs_the_same_poked_geometry(self):
        source,bars = bars_for(support_rows())
        changed = list(bars)
        changed[60] = replace(changed[60],low=Decimal("105.9"))
        before = l.inspect(source,changed[:61])
        after = l.inspect(source,changed[:66])
        self.assertEqual(60,candidate(before,20,32)["first_penetration"]["bar_index"])
        self.assertEqual(60,candidate(after,20,32)["first_penetration"]["bar_index"])
        self.assertFalse(candidate(after,20,32)["profile_valid"])

    def test_low_decimal_precision_and_all_five_action_profiles_preserved(self):
        normal,source,bars = inspect_g35()
        with localcontext() as context:
            context.prec = 2
            self.assertEqual(normal,l.inspect(source,bars,role="action_break"))
        self.assertEqual(5,len(l.STRATEGIES))
        for profile in l.STRATEGIES:
            result = l.inspect(source,bars,profile=profile)
            self.assertEqual(profile,result["profile"])
            self.assertFalse(result["orders_available"])

    def test_cli_default_full_and_explicit_action_break_and_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            value,rows = hourly_fixture()
            meta,hours,_ = files(directory,value,rows)
            def run(name,extra=()):
                output = Path(directory)/name
                result = subprocess.run([sys.executable,str(ROOT/"scripts/trendline-lines-168.py"),str(meta),str(hours),str(output),*extra],capture_output=True,text=True)
                return result,output
            result,output = run("full")
            self.assertEqual(0,result.returncode,result.stderr)
            self.assertFalse(candidate(json.loads((output/"lines.json").read_text()))["profile_valid"])
            result,output = run("break",["--role","action_break"])
            self.assertEqual(0,result.returncode,result.stderr)
            report = json.loads((output/"lines.json").read_text())
            self.assertTrue(candidate(report)["profile_valid"])
            self.assertEqual("B",report["data_level"])
            self.assertFalse(report["entry_ready"]);self.assertFalse(report["orders_available"])
            before = (output/"lines.json").read_bytes()
            self.assertNotEqual(0,run("break")[0].returncode)
            self.assertEqual(before,(output/"lines.json").read_bytes())

    def test_cli_validation_market_and_inapplicable_role_cannot_bypass(self):
        with tempfile.TemporaryDirectory() as directory:
            value,rows = hourly_fixture()
            meta,hours,value = files(directory,value,rows)
            for index,(change,extra) in enumerate((({"partition":"validation"},()),
                                                 ({"kind":"market_trendline_source"},()),
                                                 ({},("--profile","TRL_BNC_E1","--role","action_break")))):
                modified = deepcopy(value);modified.update(change);meta.write_text(json.dumps(modified))
                output = Path(directory)/str(index)
                result = subprocess.run([sys.executable,str(ROOT/"scripts/trendline-lines-168.py"),str(meta),str(hours),str(output),*extra],capture_output=True)
                self.assertNotEqual(0,result.returncode);self.assertFalse(output.exists())


if __name__ == "__main__":unittest.main()
