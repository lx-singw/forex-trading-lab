"""Price-only invented scenarios; no account ledger or broker order interface."""
from copy import deepcopy
from decimal import localcontext
from fractions import Fraction as F
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from forex_demo_lab.daily_risk_119 import profiles as old_profiles
from forex_demo_lab.trendline import data as d
from forex_demo_lab.trendline import fills as f
from test_trendline_data_163 import descriptor, calendar


def setup(direction="LONG", exit_model="E1", cost="base", source=None):
    value = source or descriptor()
    declared = d.Declaration.from_record(value)
    model = f.PriceModel(declared,cost)
    window = declared.calendar.frame("H4")[0]
    request = {"kind":"invented_b_price_request", "direction":direction,
               "trigger_end":window.end,"decision_at":{"time":window.end,"ordinal":0},
               "stop":"1.0985" if direction == "LONG" else "1.1015",
               "target":None if exit_model == "E1" else ("1.105" if direction == "LONG" else "1.095"),
               "atr":"0.0015","tick":"0.00001","exit_model":exit_model}
    opening = f.Opening.from_record({"kind":"invented_b_opening_assumption",
                                    "start":window.end,"end":window.end+3600000,"ordinal":1,
                                    "bid":"1.1004" if direction == "LONG" else "1.09948",
                                    "spread_pips":"1.2"})
    return model,request,opening


def filled(direction="LONG",exit_model="E1",cost="base"):
    model,request,opening = setup(direction,exit_model,cost)
    result = model.entry(request,opening)
    if result["status"] != "FILLED":
        raise AssertionError(result["reason"])
    return model, f.Position.from_record(result["position"]), opening


def next_open(opening, bid, spread="1.2"):
    value = opening.record()
    value.update(start=opening.end,end=opening.end+3600000,bid=bid,spread_pips=spread)
    return f.Opening.from_record(value)


def hour_for(opening, low, high, close=None, available=None):
    return d.Hour.from_record({"start":opening.start,"end":opening.end,
                              "available_at":opening.end if available is None else available,
                              "open":f.text(opening.bid),"low":low,"high":high,
                              "close":close or f.text(opening.bid),
                              "spread_pips":f.text(opening.spread_pips)},"bid_only")


class TrendlineFills164Tests(unittest.TestCase):
    def test_fixed_profiles_match_retained_profile_numbers(self):
        for name,old in old_profiles().items():
            costs = f.profile(name)
            self.assertEqual(F(str(old["config"]["slippage_pips"])),F(costs["slippage_pips"]))
            self.assertEqual(F(str(old["spread_floor_pips"])),F(costs["spread_floor_pips"]))
            self.assertFalse(costs["commission_and_financing_applied"])

    def test_long_buys_ask_plus_slip_short_sells_bid_minus_slip(self):
        for side,expected in (("LONG","1.10054"),("SHORT","1.09946")):
            model,request,opening = setup(side)
            result = model.entry(request,opening)
            self.assertEqual("FILLED",result["status"])
            self.assertEqual(expected,result["price"])
            self.assertEqual("0.00204",result["stop_distance"])
            self.assertEqual("1.2",result["effective_spread_pips"])

    def test_adverse_spread_floor_and_slippage_are_applied_once(self):
        expected = {"base":"1.10044","adverse":"1.10057"}
        for cost in expected:
            model,request,opening = setup(cost=cost)
            record = opening.record();record["spread_pips"] = "0.2"
            result = model.entry(request,f.Opening.from_record(record))
            self.assertEqual(expected[cost],result["price"])
            self.assertEqual("0.2" if cost == "base" else "1.2",result["effective_spread_pips"])

    def test_equal_timestamp_requires_known_decision_before_open(self):
        model,request,opening = setup()
        self.assertEqual("FILLED",model.entry(request,opening)["status"])
        request["decision_at"]["ordinal"] = opening.ordinal
        self.assertEqual("UNRESOLVED_OPEN_ORDER",model.entry(request,opening)["reason"])
        request["decision_at"]["ordinal"] += 1
        self.assertEqual("UNRESOLVED_OPEN_ORDER",model.entry(request,opening)["reason"])

    def test_late_decision_never_uses_passed_open(self):
        model,request,opening = setup()
        request["decision_at"]["time"] += 1
        self.assertEqual("LATE_DECISION",model.entry(request,opening)["reason"])

    def test_missing_first_hour_never_substitutes_a_later_price(self):
        model,request,opening = setup()
        self.assertEqual("MISSING_ENTRY_BAR",model.entry(request,None)["reason"])
        later = next_open(opening,"1.1001")
        self.assertEqual("MISSING_ENTRY_BAR",model.entry(request,later)["reason"])

    def test_last_h4_close_cannot_borrow_a_later_partition(self):
        model,request,opening = setup()
        request["trigger_end"] = model.source.calendar.frame("H4")[-1].end
        request["decision_at"]["time"] = request["trigger_end"]
        self.assertEqual("NO_SCHEDULED_ENTRY",model.entry(request,None)["reason"])

    def test_entry_window_observes_declared_weekend_closure(self):
        model,request,_ = setup(source=descriptor(calendar((24,24),(48,))))
        request["trigger_end"] = model.source.calendar.frame("D1")[0].end
        request["decision_at"]["time"] = request["trigger_end"]
        window = model.entry_window(request["trigger_end"])
        self.assertEqual(48*3600000,window.start-request["trigger_end"])

    def test_entry_does_not_depend_on_later_hour_range_or_receipt(self):
        model,request,opening = setup()
        first = hour_for(opening,"1.099","1.102")
        future = hour_for(opening,"0.5","9",close="8",available=opening.end+5000)
        a = model.entry(request,f.Opening.from_hour(first,opening.ordinal))
        b = model.entry(request,f.Opening.from_hour(future,opening.ordinal))
        self.assertEqual(a,b)

    def test_long_and_short_stops_round_outward_before_sizing_distance(self):
        for side,raw,expected in (("LONG","1.098509","1.0985"),("SHORT","1.101491","1.1015")):
            model,request,opening = setup(side)
            request["stop"] = raw
            result = model.entry(request,opening)
            self.assertEqual(expected,result["position"]["stop"])
            self.assertEqual("0.00204",result["stop_distance"])

    def test_already_crossed_stop_uses_exit_side_not_entry_side(self):
        for side,stop in (("LONG","1.1004"),("SHORT","1.0996")):
            model,request,opening = setup(side)
            request["stop"] = stop
            self.assertEqual("STOP_ALREADY_CROSSED",model.entry(request,opening)["reason"])

    def test_atr_stop_window_boundaries_are_inclusive(self):
        model,request,opening = setup()
        record = opening.record();record.update(bid="1.1005",spread_pips="0.2")
        opening = f.Opening.from_record(record)  # Same fill1.10054, independent of spread gate.
        for stop,expected in (("1.09954","FILLED"),("1.09554","FILLED"),
                              ("1.09955","SKIPPED"),("1.09553","SKIPPED")):
            request.update(atr="0.002",stop=stop)
            self.assertEqual(expected,model.entry(request,opening)["status"])

    def test_spread_filter_has_inclusive_ten_percent_boundary(self):
        model,request,opening = setup()
        request.update(atr="0.001",stop="1.09934")  # distance0.00120, spread0.00012
        self.assertEqual("FILLED",model.entry(request,opening)["status"])
        request["stop"] = "1.09935"
        self.assertEqual("SPREAD_TOO_WIDE",model.entry(request,opening)["reason"])

    def test_e2_rechecks_two_R_after_target_rounding_and_slippage(self):
        for side,too_near,exact in (("LONG","1.104619","1.10462"),
                                    ("SHORT","1.095381","1.09538")):
            model,request,opening = setup(side,"E2")
            request["target"] = too_near
            self.assertEqual("NO_VALID_TARGET",model.entry(request,opening)["reason"])
            request["target"] = exact
            self.assertEqual("FILLED",model.entry(request,opening)["status"])
            request["target"] = None
            self.assertEqual("NO_VALID_TARGET",model.entry(request,opening)["reason"])

    def test_mid_only_declaration_cannot_make_executable_sides(self):
        model,request,opening = setup(source=descriptor(basis="mid_candles_source"))
        self.assertEqual("UNAVAILABLE",model.entry(request,None)["status"])
        self.assertEqual("EXECUTION_SIDE_DATA_UNAVAILABLE",model.exit_open(None,None)["reason"])

    def test_long_gap_sells_bid_short_gap_buys_ask_with_adverse_slip(self):
        for side,bid,expected in (("LONG","1.097","1.09698"),
                                  ("SHORT","1.10288","1.10302")):
            model,position,opening = filled(side)
            result = model.exit_open(position,next_open(opening,bid))
            self.assertEqual("STOP_OPEN_GAP",result["reason"])
            self.assertEqual(expected,result["price"])
            self.assertEqual("0.00152",result["price_risk_excess"])

    def test_stop_market_slippage_also_applies_to_intrabar_stop(self):
        for side,low,high,expected in (("LONG","1.098","1.101","1.09848"),
                                       ("SHORT","1.099","1.102","1.10152")):
            model,position,opening = filled(side)
            hour = hour_for(opening,low,high)
            result = model.exit_hour(position,hour,as_of=hour.available_at,open_ordinal=1)
            self.assertEqual("STOP_RANGE",result["reason"])
            self.assertEqual(expected,result["price"])
            self.assertEqual("unknown_within_completed_h1",result["event_time_kind"])

    def test_ambiguous_post_fill_bar_selects_stop_in_both_directions(self):
        for side in ("LONG","SHORT"):
            model,position,opening = filled(side,"E2")
            hour = hour_for(opening,"1.09","1.11")
            result = model.exit_hour(position,hour,as_of=hour.available_at,open_ordinal=1)
            self.assertEqual("STOP_ADVERSE_AMBIGUITY",result["reason"])
            self.assertIsNone(result["event"])

    def test_target_only_range_fills_limit_without_slippage_or_overshoot(self):
        for side,low,high,target in (("LONG","1.099","1.106","1.105"),
                                    ("SHORT","1.094","1.1","1.095")):
            model,position,opening = filled(side,"E2")
            hour = hour_for(opening,low,high)
            result = model.exit_hour(position,hour,as_of=hour.available_at,open_ordinal=1)
            self.assertEqual("TARGET_RANGE",result["reason"])
            self.assertEqual(target,result["price"])

    def test_known_target_reach_at_open_precedes_later_stop_range(self):
        for side,bid,target in (("LONG","1.106","1.105"),("SHORT","1.09388","1.095")):
            model,position,opening = filled(side,"E2")
            following = next_open(opening,bid)
            hour = hour_for(following,"1.09","1.11")
            result = model.exit_hour(position,hour,as_of=hour.available_at,open_ordinal=1)
            self.assertEqual("TARGET_OPEN_REACH",result["reason"])
            self.assertEqual(target,result["price"])

    def test_pre_fill_trigger_range_cannot_stop_a_later_position(self):
        model,position,opening = filled()
        previous = deepcopy(opening.record())
        previous.update(start=opening.start-3600000,end=opening.start)
        hour = hour_for(f.Opening.from_record(previous),"0.5","9")
        result = model.exit_hour(position,hour,as_of=hour.available_at,open_ordinal=1)
        self.assertEqual("PRE_ENTRY_BAR",result["reason"])

    def test_new_fill_does_not_exist_before_its_open_event(self):
        model,position,opening = filled()
        self.assertEqual("HELD_NOT_BEFORE_OPEN",model.exit_open(position,opening)["reason"])

    def test_unavailable_hour_range_is_never_used_early(self):
        model,position,opening = filled()
        hour = hour_for(opening,"1.098","1.11",available=opening.end+2000)
        self.assertEqual("HOUR_NOT_AVAILABLE",model.exit_hour(position,hour,as_of=hour.end,open_ordinal=1)["reason"])

    def test_future_stop_cannot_execute_against_earlier_bar_range(self):
        model,position,opening = filled()
        changed = position.record()
        changed.update(stop="1.1002",stop_effective_at={"time":opening.end,"ordinal":0})
        new = f.Position.from_record(changed)
        hour = hour_for(opening,"1.1","1.101")
        result = model.exit_hour(new,hour,as_of=hour.available_at,open_ordinal=1)
        self.assertEqual("PROTECTION_NOT_EFFECTIVE_FOR_WHOLE_BAR",result["reason"])
        self.assertEqual("NO_EXIT",model.exit_hour(position,hour,as_of=hour.available_at,open_ordinal=1)["status"])

    def test_prospective_tightening_can_apply_to_next_open(self):
        model,position,opening = filled()
        changed = position.record()
        changed.update(stop="1.1002",stop_effective_at={"time":opening.end,"ordinal":0})
        new = f.Position.from_record(changed)
        result = model.exit_open(new,next_open(opening,"1.1"))
        self.assertEqual("STOP_OPEN_GAP",result["reason"])

    def test_scheduled_exit_uses_bid_or_ask_with_market_slippage(self):
        for side,bid,expected in (("LONG","1.1004","1.10038"),("SHORT","1.09948","1.09962")):
            model,position,opening = filled(side)
            result = model.exit_open(position,next_open(opening,bid),scheduled_exit=True)
            self.assertEqual("SCHEDULED_OPEN_EXIT",result["reason"])
            self.assertEqual(expected,result["price"])

    def test_protection_continues_even_when_entry_spread_would_fail(self):
        model,position,opening = filled("SHORT")
        wide = next_open(opening,"1.101",spread="20")
        self.assertEqual("STOP_OPEN_GAP",model.exit_open(position,wide)["reason"])

    def test_unknown_same_clock_fill_order_and_mid_hour_fill_are_unavailable(self):
        model,position,opening = filled()
        hour = hour_for(opening,"1.098","1.101")
        self.assertEqual("PARTIAL_ENTRY_INTERVAL",model.exit_hour(position,hour,as_of=hour.available_at,open_ordinal=2)["reason"])
        changed = position.record();changed["entry_at"]["time"] += 1
        changed["stop_effective_at"]["time"] += 1
        with self.assertRaises(ValueError):
            model.exit_hour(f.Position.from_record(changed),hour,as_of=hour.available_at,open_ordinal=1)

    def test_e2_cannot_trail_or_loosen_its_initial_stop(self):
        model,position,opening = filled(exit_model="E2")
        for stop in ("1.0984","1.0986"):
            changed = position.record();changed.update(stop=stop,stop_effective_at={"time":opening.end,"ordinal":0})
            with self.assertRaises(ValueError):f.Position.from_record(changed)

    def test_e1_stop_cannot_loosen_or_backdate_a_change(self):
        _,position,opening = filled()
        changed = position.record();changed["stop"] = "1.0984"
        with self.assertRaises(ValueError):f.Position.from_record(changed)
        changed["stop"] = "1.0986"
        with self.assertRaises(ValueError):f.Position.from_record(changed)

    def test_other_profile_or_other_calendar_position_is_refused(self):
        model,position,opening = filled()
        adverse = f.PriceModel(model.source,"adverse")
        with self.assertRaises(ValueError):adverse.exit_open(position,next_open(opening,"1.1"))
        other = f.PriceModel(d.Declaration.from_record(descriptor(calendar((23,)))))
        with self.assertRaises(ValueError):other.exit_open(position,next_open(opening,"1.1"))

    def test_nonpositive_modeled_price_never_creates_negative_fill(self):
        model,request,opening = setup("SHORT")
        request.update(stop="0.0005",atr="0.0003",tick="0.000001")
        record = opening.record();record.update(bid="0.000001",spread_pips="0")
        self.assertEqual("NONPOSITIVE_ENTRY",model.entry(request,f.Opening.from_record(record))["reason"])

    def test_bad_types_nonfinite_unknown_fields_and_market_kinds_reject(self):
        model,request,opening = setup()
        for key,bad in (("kind","real_order"),("stop","NaN"),("tick","0"),("atr",True),
                        ("trigger_end",True),("direction","BUY"),("extra","blocked")):
            changed = deepcopy(request);changed[key] = bad
            with self.subTest(key=key),self.assertRaises(ValueError):model.entry(changed,opening)
        with self.assertRaises(ValueError):f.Event(opening.start,True)

    def test_profile_source_changes_reject_before_returning_a_price(self):
        model,request,opening = setup()
        with patch.object(f,"bindings",return_value={}):
            with self.assertRaises(ValueError):model.entry(request,opening)
        model.costs["slippage_pips"] = "0"
        with self.assertRaises(ValueError):model.entry(request,opening)

    def test_returned_position_is_detached_and_repeated_calls_are_deterministic(self):
        model,request,opening = setup()
        first = model.entry(request,opening)
        original = deepcopy(first)
        first["position"]["stop"] = "9"
        first["profile"]["slippage_pips"] = "9"
        self.assertEqual(original,model.entry(request,opening))
        self.assertFalse(original["orders_available"])
        self.assertFalse(original["account_ledger_available"])

    def test_exact_arithmetic_is_independent_of_decimal_context(self):
        model,request,opening = setup()
        expected = model.entry(request,opening)
        with localcontext() as context:
            context.prec = 3
            self.assertEqual(expected,model.entry(request,opening))

    def test_tiny_fractional_spread_keeps_all_calculated_ask_places(self):
        model,request,opening = setup()
        value = opening.record();value["spread_pips"] = "0.000000000001"
        result = model.entry(request,f.Opening.from_record(value))
        self.assertEqual("1.1004200000000001",result["price"])
        self.assertEqual(result["price"],f.Position.from_record(result["position"]).record()["entry_price"])

    def test_range_cursor_cannot_extend_beyond_declared_scope(self):
        model,position,opening = filled()
        hour = hour_for(opening,"1.1","1.101")
        with self.assertRaises(ValueError):
            model.exit_hour(position,hour,as_of=model.source.calendar.end+60001,open_ordinal=1)

    def test_changed_future_file_hash_does_not_rename_earlier_price_position(self):
        model,request,opening = setup()
        value = model.source.record();value["input_sha256"] = "f"*64
        other = f.PriceModel(d.Declaration.from_record(value))
        self.assertEqual(model.entry(request,opening)["position"],other.entry(request,opening)["position"])

    def test_price_record_reconstruction_in_fresh_process_preserves_gap_result(self):
        model,position,opening = filled()
        following = next_open(opening,"1.097")
        expected = model.exit_open(position,following)
        payload = {"source":model.source.record(),"position":position.record(),"opening":following.record()}
        program = ("import json,sys; from forex_demo_lab.trendline.data import Declaration; "
                   "from forex_demo_lab.trendline.fills import PriceModel,Position,Opening; "
                   "p=json.load(sys.stdin); "
                   "print(json.dumps(PriceModel(Declaration.from_record(p['source'])).exit_open("
                   "Position.from_record(p['position']),Opening.from_record(p['opening']))))")
        result = subprocess.run([sys.executable,"-c",program],input=json.dumps(payload),text=True,capture_output=True,check=True)
        self.assertEqual(expected,json.loads(result.stdout))

    def test_public_demo_checks_both_directions_and_profiles_without_overwrite(self):
        script = Path(__file__).resolve().parents[1]/"scripts/trendline-fill-demo-164.py"
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)/"new"
            command = [sys.executable,str(script),str(output)]
            subprocess.run(command,capture_output=True,text=True,check=True)
            summary = json.loads((output/"summary.json").read_text())
            self.assertEqual(16,len(summary["cases"]))
            self.assertEqual(4,sum(c["entry_reason"] == "LATE_DECISION" for c in summary["cases"]))
            self.assertFalse(summary["orders_available"])
            original = (output/"summary.json").read_bytes()
            self.assertNotEqual(0,subprocess.run(command,capture_output=True).returncode)
            self.assertEqual(original,(output/"summary.json").read_bytes())


if __name__ == "__main__":
    unittest.main()
