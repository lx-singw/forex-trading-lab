"""Chronological metadata and immutable declarations; no provider/price inputs."""
from copy import deepcopy
from datetime import date
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from forex_demo_lab import elliott_study_145 as legacy
from forex_demo_lab.trendline import data, study as s


def span(start,end):
    return {"start":start,"end":end}


def declared(level="B",track="hypothetical_cost_sensitivity"):
    p = s.draft()
    p.update(case="invented_claims",data_level=level,track=track,
             source={"alias":"source_invented_claims","route":"existing_export"},
             geometry_basis="bid_only" if level == "B" else "mid_sync",
             spread_semantics="constant_per_h1_assumption" if level == "B" else "recorded_bid_ask",
             input_sha256="1"*64,calendar_sha256="2"*64,uncertainty_sha256="3"*64)
    for name,start,end,warm in (("development","2014-01-01","2016-01-01","2013-01-01"),
                                ("validation","2016-01-01","2018-01-01","2015-01-01")):
        p["partitions"][name] = {"interval":span(start,end),"warmup":{"interval":span(warm,start),
                                       "declared_complete_bars":{"H1":6072,"H4":1518,"D1":253}}}
    p["endpoints"] = {"development":{"liquidation_at":"2015-12-31T23:00:00Z"},
                      "validation":{"liquidation_at":"2017-12-31T23:00:00Z"}}
    p["history"].update(complete=True,undated_price_exposure_count=0,tried_alternatives_count=0)
    p["latency"] = {"availability_assumption":"bar_close_hypothesis" if level == "B" else "recorded_receipt_order",
                      "finalization_delay_ms":0}
    p["costs"]["status"] = "hypothetical_117" if track == "hypothetical_cost_sensitivity" else "broker_evidence_declared"
    for gate in s.GATES:
        p["evidence"][gate] = {"sha256":"a"*64,"intervals":[span("2013-01-01","2018-01-01")],"timeframes":list(s.FRAMES)}
    return p


def codes(report,scope=None):
    return {i["code"] for i in report["issues"] if scope is None or i["scope"] == scope}


class TrendlineStudy165Tests(unittest.TestCase):
    def setUp(self):
        self.home = tempfile.TemporaryDirectory()
        self.root = Path(self.home.name)

    def tearDown(self):
        self.home.cleanup()

    def frozen(self,value=None):
        plan,seal = self.root/"plan.json",self.root/"freeze.json"
        data.write_new(plan,s.draft() if value is None else value)
        s.freeze(plan,seal)
        return plan,seal

    def test_current_draft_has_no_assigned_source_dates_or_prices(self):
        p = s.draft();r = s.assess(p)
        self.assertIsNone(p["source"]["alias"])
        self.assertTrue(all(row["interval"] == span(None,None) for row in p["partitions"].values()))
        self.assertIn("source_unassigned",codes(r))
        self.assertIn("uncertainty_sha256_unassigned",codes(r))
        self.assertFalse(r["market_data_read"])

    def test_28_unique_cells_in_each_track_and_no_false_returns(self):
        for track in s.TRACKS:
            p = s.draft();p["track"] = track;r = s.assess(p)
            keys = {(row["candidate"],row["profile"],row["partition"]) for row in r["cells"]}
            self.assertEqual(28,len(keys))
            self.assertTrue(all(row["returns"] is None and row["status"] == "UNAVAILABLE" for row in r["cells"]))
            for flag in ("market_data_read","returns_computed","native_queries","orders_available","demo_eligible"):
                self.assertIs(r[flag],False)

    def test_complete_claims_cannot_self_qualify_or_open_files(self):
        for level,track in (("B","hypothetical_cost_sensitivity"),("Q","qualified")):
            p = declared(level,track)
            with patch.object(data,"read_json",side_effect=AssertionError("no input file expected")):
                result = s.assess(p)
            self.assertEqual("UNAVAILABLE",result["status"])
            self.assertFalse(any(i["state"] in ("MISSING","BLOCKED") for i in result["issues"]))
            self.assertIn("independent_qualification_required",codes(result))
            self.assertIn("evidence_not_independently_qualified_bar_price_semantics",codes(result))

    def test_existing_16_cell_preflight_and_policy_remain_unchanged(self):
        old_policy = legacy.policy()
        before = legacy.assess(legacy.draft())
        s.assess(declared())
        self.assertEqual(old_policy,legacy.policy())
        self.assertEqual(before,legacy.assess(legacy.draft()))
        self.assertEqual(16,len(before["cells"]))
        self.assertEqual(old_policy["date_policy"],s.policy()["date_policy"])

    def test_assessment_does_not_mutate_plan(self):
        p = declared();before = deepcopy(p)
        s.assess(p)
        self.assertEqual(before,p)

    def test_calendar_months_and_leap_day_reuse_reference_policy(self):
        p = declared();p["partitions"]["development"]["interval"] = span("2019-01-01","2020-12-31")
        self.assertIn("fewer_than_24_calendar_months",codes(s.assess(p),"development"))
        self.assertEqual(date(2022,2,28),legacy.add_months(date(2020,2,29),24))

    def test_reversed_and_overlapping_partition_intervals_reject(self):
        p = declared();p["partitions"]["validation"]["interval"] = span("2015-01-01","2017-01-01")
        self.assertIn("partitions_not_chronological_disjoint",codes(s.assess(p)))
        p["partitions"]["validation"]["interval"] = span("2017-01-01","2015-01-01")
        with self.assertRaises(ValueError):s.assess(p)

    def test_warmup_contiguity_and_minimum_bars(self):
        for frame in s.FRAMES:
            p = declared();p["partitions"]["development"]["warmup"]["declared_complete_bars"][frame] = 252
            self.assertIn("insufficient_declared_warmup_"+frame,codes(s.assess(p),"development"))
        p = declared();p["partitions"]["validation"]["warmup"]["interval"]["end"] = "2015-12-31"
        self.assertIn("warmup_not_contiguous_with_partition",codes(s.assess(p),"validation"))

    def test_FXR_angle_history_requires_390_complete_H4_bars(self):
        for count,blocked in ((389,True),(390,False)):
            p = declared();p["partitions"]["development"]["warmup"]["declared_complete_bars"]["H4"] = count
            self.assertEqual(blocked,"insufficient_FXR_390_H4_angle_history" in codes(s.assess(p),"development"))

    def test_declared_parent_counts_cannot_exceed_child_counts(self):
        p = declared();p["partitions"]["development"]["warmup"]["declared_complete_bars"].update(H1=400,H4=500)
        self.assertIn("declared_child_parent_counts_inconsistent",codes(s.assess(p)))

    def test_consumed_quarantined_reserved_dates_include_warmup(self):
        for start,end,code in (("2025-01-01","2026-01-01","date_consumed"),
                               ("2026-10-01","2026-11-01","date_quarantined"),
                               ("2026-11-01","2027-01-01","date_reserved_untouched")):
            for role in ("interval","warmup"):
                p = declared()
                if role == "interval":p["partitions"]["validation"][role] = span(start,end)
                else:p["partitions"]["validation"][role]["interval"] = span(start,end)
                self.assertIn(code,codes(s.assess(p),"validation"))

    def test_seen_2024_validation_block_and_half_open_boundary(self):
        p = declared();p["partitions"]["validation"]["interval"] = span("2024-01-01","2025-01-01")
        result = s.assess(p)
        self.assertIn("date_seen_development_only",codes(result,"validation"))
        self.assertNotIn("date_consumed",codes(result,"validation"))

    def test_prior_prices_returns_rule_changes_and_examples_expose_validation(self):
        for kind in ("prices","returns","rule_adjustment","friend_example"):
            p = declared();p["history"]["exposures"] = [{"interval":span("2016-01-01","2017-01-01"),
                        "kind":kind,"track":"other","joint_study_sha256":None}]
            self.assertIn("validation_previously_exposed",codes(s.assess(p),"validation"))

    def test_undated_banners_cannot_be_silently_counted_unseen(self):
        p = declared();p["history"]["undated_price_exposure_count"] = 1
        self.assertIn("undated_price_exposure_requires_validation_review",codes(s.assess(p),"validation"))
        p["history"]["undated_price_exposure_count"] = None
        self.assertIn("undated_price_exposure_count_missing",codes(s.assess(p)))

    def test_incomplete_variant_history_and_trial_count_are_explicit(self):
        p = declared();p["history"].update(complete=False,tried_alternatives_count=None)
        result = s.assess(p)
        self.assertIn("prior_trial_history_incomplete",codes(result))
        self.assertIn("tried_alternatives_count_missing",codes(result))

    def test_joint_freeze_claim_still_needs_review(self):
        p = declared();p["joint_study_sha256"] = "b"*64
        p["history"]["exposures"] = [{"interval":span("2016-01-01","2017-01-01"),"kind":"prices",
                 "track":"qualified","joint_study_sha256":"b"*64}]
        self.assertIn("joint_pre_return_freeze_requires_review",codes(s.assess(p)))
        self.assertEqual("UNAVAILABLE",s.assess(p)["status"])

    def test_own_28_cell_budget_does_not_reuse_legacy_16_cell_limit(self):
        for track in s.TRACKS:
            p = declared();p["track"] = track;p["prior_cells"][track] = 28
            result = s.assess(p)
            self.assertIn("initial_28_cell_track_budget_exhausted",codes(result))
            self.assertNotIn("initial_track_budget_exhausted",codes(result))
        p = declared();p["prior_cells"]["qualified"] = 28
        self.assertNotIn("initial_28_cell_track_budget_exhausted",codes(s.assess(p)))

    def test_paired_analysis_budget_and_declaration_are_retained(self):
        p = declared();p["paired_exit"]["prior_analyses"] = 1
        self.assertIn("initial_paired_analysis_budget_exhausted",codes(s.assess(p)))
        p["paired_exit"]["planned"] = False
        self.assertIn("paired_exit_analysis_not_declared",codes(s.assess(p)))

    def test_B_level_and_hypothetical_costs_cannot_pass_qualified_track(self):
        p = declared(track="qualified")
        self.assertIn("level_B_not_qualified_execution_data",codes(s.assess(p)))
        p["costs"]["status"] = "hypothetical_117"
        self.assertIn("hypothetical_costs_cannot_pass_qualified_track",codes(s.assess(p)))

    def test_unknown_costs_contradictions_and_fixed_profile_hash(self):
        p = declared();p["costs"].update(status="unknown",contradictions=True)
        result = s.assess(p)
        self.assertIn("historical_costs_unknown",codes(result))
        self.assertIn("cost_contradiction_requires_new_declared_profile",codes(result))
        p["costs"]["profile_declaration_sha256"] = "f"*64
        with self.assertRaises(ValueError):s.assess(p)

    def test_B_midpoint_is_geometry_only_and_cannot_claim_bid_spread(self):
        p = declared();p.update(geometry_basis="mid_candles_source",spread_semantics="not_available")
        self.assertIn("mid_only_execution_side_data_unavailable",codes(s.assess(p)))
        p["spread_semantics"] = "recorded_bid_ask"
        with self.assertRaises(ValueError):s.assess(p)

    def test_Q_requires_observed_receipt_order(self):
        p = declared("Q","qualified");p["latency"]["availability_assumption"] = "bar_close_hypothesis"
        self.assertIn("level_Q_requires_observed_receipt_order",codes(s.assess(p)))
        p["geometry_basis"] = "bid_only"
        with self.assertRaises(ValueError):s.assess(p)

    def test_nonzero_B_delay_retains_first_open_limitation(self):
        p = declared();p["latency"]["finalization_delay_ms"] = 2000
        self.assertIn("nonzero_delay_can_skip_immediate_H1_opens",codes(s.assess(p)))

    def test_evidence_scopes_cover_warmup_and_both_partitions(self):
        for gate in s.GATES:
            p = declared();p["evidence"][gate]["intervals"] = [span("2014-01-01","2018-01-01")]
            self.assertIn("evidence_scope_gap_"+gate,codes(s.assess(p),"development"))
        p = declared();p["evidence"]["bar_price_semantics"]["timeframes"] = ["H1"]
        self.assertIn("evidence_frames_incomplete_bar_price_semantics",codes(s.assess(p)))

    def test_hashed_evidence_gaps_are_not_filled_by_an_endpoint_claim(self):
        p = declared();p["evidence"]["entry_spread_semantics"]["intervals"] = [span("2013-01-01","2015-01-01"),span("2015-01-02","2018-01-01")]
        self.assertIn("evidence_scope_gap_entry_spread_semantics",codes(s.assess(p)))

    def test_liquidation_is_inside_its_own_partition_and_never_at_exclusive_end(self):
        p = declared();p["endpoints"]["development"]["liquidation_at"] = "2016-01-01T00:00:00Z"
        self.assertIn("liquidation_outside_partition",codes(s.assess(p),"development"))
        p["endpoints"]["development"]["liquidation_at"] = "2015-12-31T23:00:00Z"
        self.assertNotIn("liquidation_outside_partition",codes(s.assess(p),"development"))

    def test_source_specific_H1_phase_is_not_guessed_from_UTC_minutes(self):
        p = declared();p["endpoints"]["development"]["liquidation_at"] = "2015-12-31T22:30:00Z"
        result = s.assess(p)
        self.assertNotIn("liquidation_not_on_declared_H1_grid",codes(result))
        self.assertIn("liquidation_calendar_and_quote_coverage_require_review",codes(result))

    def test_no_expired_native_or_closed_route_is_renewed(self):
        for route,code in (("closed_native090","closed_route_not_renewed"),
                           ("sdk_attach_only","closed_route_not_renewed"),
                           ("native_capture","no_bounded_native_capture_assigned")):
            p = declared();p["source"]["route"] = route
            self.assertIn(code,codes(s.assess(p)))

    def test_bad_types_paths_secret_fields_and_overrides_reject(self):
        changes = (("market_enabled",True),("input_sha256","/not/a/hash"),
                   ("data_level","live"),("uncertainty_sha256",True))
        for key,bad in changes:
            p = declared();p[key] = bad
            with self.subTest(key=key),self.assertRaises(ValueError):s.assess(p)
        p = declared();p["source"]["alias"] = "arbitrary_private_identity"
        with self.assertRaises(ValueError):s.assess(p)
        p = declared();p["history"]["tried_alternatives_count"] = True
        with self.assertRaises(ValueError):s.assess(p)

    def test_evidence_hashes_are_not_opened_as_paths(self):
        with patch.object(data,"read_json",side_effect=AssertionError("not a price reader")):
            self.assertEqual("UNAVAILABLE",s.assess(declared())["status"])

    def test_freeze_binds_plan_bytes_content_policy_and_implementation(self):
        plan,seal = self.frozen(declared())
        result = s.run(plan,seal,self.root/"out")
        self.assertEqual(28,result["planned_cells"])
        original = plan.read_text();plan.write_text(original+" ")
        with self.assertRaises(ValueError):s.run(plan,seal,self.root/"changed")
        self.assertFalse((self.root/"changed").exists())

    def test_source_or_policy_changes_invalidate_freeze_before_output(self):
        plan,seal = self.frozen()
        with patch.object(s,"bindings",return_value={}):
            with self.assertRaises(ValueError):s.run(plan,seal,self.root/"bad")
        with patch.object(s,"policy",return_value={}):
            with self.assertRaises(ValueError):s.run(plan,seal,self.root/"bad")
        self.assertFalse((self.root/"bad").exists())

    def test_source_change_during_assessment_is_rejected(self):
        plan,seal = self.frozen()
        before = s.bindings()
        with patch.object(s,"bindings",side_effect=[before,{}]):
            with self.assertRaises(ValueError):s.run(plan,seal,self.root/"bad")
        self.assertFalse((self.root/"bad").exists())

    def test_forged_boolean_flag_cannot_enable_data_access(self):
        plan,seal = self.frozen()
        value = json.loads(seal.read_text());value["orders_available"] = 0
        seal.write_text(json.dumps(value))
        with self.assertRaises(ValueError):s.run(plan,seal,self.root/"bad")
        value["orders_available"] = True;seal.write_text(json.dumps(value))
        with self.assertRaises(ValueError):s.run(plan,seal,self.root/"bad")

    def test_exclusive_output_and_symlinked_metadata_paths(self):
        plan,seal = self.frozen()
        with self.assertRaises(FileExistsError):s.freeze(plan,seal)
        s.run(plan,seal,self.root/"out")
        with self.assertRaises(FileExistsError):s.run(plan,seal,self.root/"out")
        linked = self.root/"linked.json";linked.symlink_to(plan)
        with self.assertRaises(ValueError):s.freeze(linked,self.root/"new.json")

    def test_duplicate_json_nonfinite_and_oversized_metadata_reject(self):
        path = self.root/"bad.json"
        for raw in ('{"schema":1,"schema":2}','{"schema":NaN}'," "*(256*1024+1)):
            path.write_text(raw)
            with self.assertRaises((ValueError,json.JSONDecodeError)):s.freeze(path,self.root/"unused.json")

    def test_public_CLI_draft_freeze_check_has_no_price_argument(self):
        script = Path(__file__).resolve().parents[1]/"scripts/trendline-study-165.py"
        plan,seal,out = self.root/"plan.json",self.root/"freeze.json",self.root/"out"
        for args in (("draft",str(plan)),("freeze",str(plan),str(seal)),("check",str(plan),str(seal),str(out))):
            result = subprocess.run([sys.executable,str(script),*args],capture_output=True,text=True,check=True)
        self.assertEqual(28,json.loads(result.stdout)["planned_cells"])
        self.assertFalse(json.loads(result.stdout)["orders_available"])
        self.assertEqual("UNAVAILABLE",json.loads((out/"preflight.json").read_text())["status"])


if __name__ == "__main__":
    unittest.main()
