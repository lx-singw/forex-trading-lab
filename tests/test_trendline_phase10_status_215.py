"""Phase 10 metadata status and protected-date regressions."""

import unittest
from unittest.mock import patch

from forex_demo_lab.trendline import data, signal_count, study
from test_trendline_study_165 import declared, span


def codes(report, field="development_preflight_issues"):
    return {row["code"] for row in report[field]}


class Phase10StatusTests(unittest.TestCase):
    def test_status_keeps_every_study_issue_and_identifies_the_count_runner(self):
        plan = study.draft()
        original = study.assess(plan)
        with patch.object(data, "read_json", side_effect=AssertionError("metadata must not open data")):
            status = signal_count.admission_status(plan)
        self.assertEqual(signal_count.STATUS_VERSION, status["schema"])
        inherited = [row for row in status["development_preflight_issues"]
                     if row["code"] != "historical_signal_counter_unavailable"]
        self.assertCountEqual(original["issues"], inherited + status["later_study_preflight_issues"])
        for required in ("source_unassigned", "evidence_missing_availability_model",
                         "evidence_missing_entry_spread_semantics", "historical_signal_counter_unavailable"):
            self.assertIn(required, codes(status))
        for later in ("historical_costs_unknown", "evidence_missing_contract_margin_conversion",
                      "uncertainty_sha256_unassigned", "undated_price_exposure_count_missing"):
            self.assertNotIn(later, codes(status))
            self.assertIn(later, codes(status, "later_study_preflight_issues"))
        self.assertIsNone(status["feasibility"]["actual_counts"])
        self.assertFalse(status["market_data_read"])

    def test_unassigned_validation_and_cash_controls_do_not_block_the_count_scope(self):
        plan = declared()
        plan["partitions"]["validation"] = study.draft()["partitions"]["validation"]
        plan["paired_exit"]["planned"] = False
        status = signal_count.admission_status(plan)
        later = codes(status, "later_study_preflight_issues")
        self.assertIn("partition_dates_unassigned", later)
        self.assertIn("paired_exit_analysis_not_declared", later)
        self.assertIn("unchanged_control_input_compatibility_not_qualified", later)
        self.assertNotIn("partition_dates_unassigned", codes(status))
        self.assertIn("independent_qualification_required", codes(status))
        self.assertFalse(status["actual_source_admitted"])

    def test_protects_validation_from_development_and_warmup_overlap(self):
        for validation in (span("2013-07-01", "2015-01-01"), span("2011-07-01", "2013-07-01")):
            plan = declared()
            plan["partitions"]["validation"]["interval"] = validation
            status = signal_count.admission_status(plan)
            self.assertIn("development_scope_overlaps_reserved_validation", codes(status))
        adjacent = signal_count.admission_status(declared())
        self.assertNotIn("development_scope_overlaps_reserved_validation", codes(adjacent))

    def test_development_date_policy_and_warmup_are_preserved(self):
        plan = study.draft()
        plan["partitions"]["development"]["interval"] = span("2026-01-01", "2027-01-01")
        plan["partitions"]["development"]["warmup"]["interval"] = span("2025-01-01", "2026-01-01")
        status = signal_count.admission_status(plan)
        for issue in ("date_consumed", "date_quarantined", "date_reserved_untouched",
                      "fewer_than_24_calendar_months", "complete_warmup_count_missing_H4"):
            self.assertIn(issue, codes(status))

    def test_quote_count_retains_receipt_order_and_entry_cutoff(self):
        plan = declared(level="Q")
        plan["latency"]["availability_assumption"] = "bar_close_hypothesis"
        plan["endpoints"]["development"]["liquidation_at"] = None
        status = signal_count.admission_status(plan)
        self.assertIn("level_Q_requires_observed_receipt_order", codes(status))
        self.assertIn("liquidation_timestamp_unassigned", codes(status))
        plan = declared()
        plan["endpoints"]["development"]["liquidation_at"] = "2016-01-01T00:00:00Z"
        self.assertIn("liquidation_outside_partition", codes(signal_count.admission_status(plan)))

    def test_count_retains_source_use_gaps_and_cost_profile_contradictions(self):
        plan = declared()
        for gate in ("source_use", "commission_swap"):
            plan["evidence"][gate]["intervals"] = [span("2016-01-01", "2018-01-01")]
        plan["costs"]["contradictions"] = True
        status = signal_count.admission_status(plan)
        self.assertIn("evidence_scope_gap_source_use", codes(status))
        self.assertIn("cost_contradiction_requires_new_declared_profile", codes(status))
        self.assertNotIn("evidence_scope_gap_commission_swap", codes(status))
        self.assertIn("evidence_scope_gap_commission_swap", codes(status, "later_study_preflight_issues"))
