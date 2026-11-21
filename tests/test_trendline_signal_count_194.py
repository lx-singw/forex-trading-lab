"""Outcome-free development counts and source admission guards."""
from copy import deepcopy
from datetime import datetime, timezone
from fractions import Fraction
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from forex_demo_lab.trendline import breaks, data, exits, fills, ledger, quote_replay, quotes, risk, signal_count
from test_trendline_data_163 import files
from test_trendline_entries_174 import fixture
from test_trendline_exits_181 import suffix
from test_trendline_ledger_183 import HOUR, shift_calendar
from test_trendline_quotes_185 import document, history, midpoint
from test_trendline_viewer_191 import winning_tape


ROOT = Path(__file__).resolve().parents[1]
PROFILE = "TRL_BRK3_E1"


def bar_fixture(*, across_month=False, no_safety=False, mid_only=False):
    value, prefix = fixture(basis="mid_candles_source" if mid_only else "bid_only")
    if no_safety:
        prefix[-1]["low"] = "102.79"
    inside = ("104.4", "104.9", "103.2", "104.4")
    following = suffix(value, prefix, *([inside] * 4))
    rows = prefix + following
    for hour in rows:
        for field in ("open", "high", "low", "close"):
            hour[field] = fills.text(Fraction("1.1") + (Fraction(hour[field]) - 100) / 1000)
    if across_month:
        january = int(datetime(2000, 2, 1, tzinfo=timezone.utc).timestamp()) * 1_000 - HOUR // 2
        shift = january - prefix[-1]["end"]
        shift_calendar(value["calendar"], shift)
        for hour in rows:
            for field in ("start", "end", "available_at"):
                hour[field] += shift
    return value, rows, following[0]


def count_b(value, rows, *, cutoff, **settings):
    source = data.Declaration.from_record(value)
    return signal_count.count_b(source, tuple(data.Hour.from_record(row, value["geometry_basis"]) for row in rows),
                                tick="0.0001", as_of=cutoff, **({"profiles": (PROFILE,), "costs": ("base",)} | settings))


def count_q(value, rows, through, liquidation=None):
    tape = quotes.Tape(document(value, rows, liquidation))
    return signal_count.count_q(tape, tick="0.0001", as_of=through, profiles=(PROFILE,), costs=("base",))


class SignalCounterTests(unittest.TestCase):
    def setUp(self):
        for module, function in ((quote_replay, "_account_replay"), (exits, "_evaluate"),
                                 (ledger, "_evaluate"), (risk, "_timeline"), (fills.PriceModel, "exit_open")):
            blocked = patch.object(module, function, side_effect=AssertionError("outcome or account path called"))
            blocked.start()
            self.addCleanup(blocked.stop)

    def test_b_first_open_counts_and_same_hour_loss_cannot_change_opportunity(self):
        value, rows, opening = bar_fixture()
        cutoff = opening["available_at"]
        model = count_b(value, rows, cutoff=cutoff, costs=signal_count.COSTS)
        altered = deepcopy(rows)
        next(row for row in altered if row["start"] == opening["start"]).update(low="1.085", close="1.09")
        self.assertEqual(model, count_b(value, altered, cutoff=cutoff, costs=signal_count.COSTS))
        self.assertEqual("UNAVAILABLE", model["feasibility"]["status"])
        self.assertEqual(60, model["feasibility"]["minimum_opportunities_per_strategy"])
        self.assertIsNone(model["feasibility"]["actual_counts"])
        self.assertFalse(model["outcomes_computed"])
        for cell in model["cells"]:
            total, profile = cell["total"], cell["cost_profile"]
            self.assertEqual((1, 1, 1, 1), tuple(total["counts"][key] for key in (
                "valid_action_lines_found", "break_setups", "groups_consumed", "entry_eligible_opportunities")))
            self.assertEqual({"ELIGIBLE": 1}, total["entry_statuses"])
            self.assertEqual({"evaluated": 1, "passed": 1}, total["entry_price_filters"]["spread_to_stop_cap"])
            self.assertEqual({"evaluated": 0, "passed": 0}, total["entry_price_filters"]["fxr_target"])
            self.assertEqual({"exactly_two": 0, "three_or_more": 1}, total["diagnostics"]["triggered_lines_by_touches"])
            self.assertEqual(1, total["diagnostics"]["stop_distance_in_atr"][0]["count"], profile)
            self.assertEqual(total["counts"]["observed_h4"], sum(total["diagnostics"]["action_lines_per_h4_histogram"].values()))

    def test_b_pending_liquidation_and_midpoint_admission_have_distinct_counts(self):
        value, rows, opening = bar_fixture()
        before = count_b(value, rows, cutoff=opening["start"])["cells"][0]["total"]
        self.assertEqual({"PENDING": 1}, before["entry_statuses"])
        self.assertEqual([], before["diagnostics"]["stop_distance_in_atr"])
        blocked = count_b(value, rows, cutoff=opening["available_at"],
                          liquidation_at=opening["start"])["cells"][0]["total"]
        self.assertEqual({"ENTRY_AT_LIQUIDATION": 1}, blocked["entry_skip_reasons"])
        value, rows, opening = bar_fixture(mid_only=True)
        unavailable = count_b(value, rows, cutoff=opening["available_at"])["cells"][0]["total"]
        self.assertEqual({"UNAVAILABLE": 1}, unavailable["entry_statuses"])
        self.assertEqual({"EXECUTION_SIDE_DATA_UNAVAILABLE": 1}, unavailable["entry_skip_reasons"])

    def test_delayed_b_waits_for_the_next_open_after_a_late_decision(self):
        value, rows, opening = bar_fixture()
        start = opening["start"]
        second, third = rows[-3:-1]
        self.assertEqual(opening["end"], second["start"])
        rows[-5]["available_at"] = second["start"]
        second.update(open="1.1000", high="1.1000", low="1.1000", close="1.1000")
        baseline = count_b(value, rows, cutoff=third["available_at"])
        variant = count_b(value, rows, cutoff=third["available_at"], delayed_entry=True, costs=signal_count.COSTS)
        self.assertEqual({"LATE_DECISION": 1}, baseline["cells"][0]["total"]["entry_skip_reasons"])
        self.assertEqual(signal_count.DELAYED_ENTRY_VERSION, variant["schema"])
        self.assertEqual("TRL_H1_AFTER_DECISION_230_V1", variant["entry_rule"])
        self.assertEqual(start + 2 * (opening["end"] - start), third["start"])
        for cell in variant["cells"]:
            self.assertEqual({"ELIGIBLE": 1}, cell["total"]["entry_statuses"])
        self.assertIsNone(variant["feasibility"]["actual_counts"])
        self.assertFalse(variant["outcomes_computed"])

    def test_delayed_b_respects_missing_slot_expiry_and_liquidation(self):
        value, rows, opening = bar_fixture()
        second = rows[-3]
        skipped = count_b(value, [row for row in rows if row is not second],
                          cutoff=rows[-1]["available_at"], delayed_entry=True)["cells"][0]["total"]
        self.assertEqual({"MISSING_ENTRY_BAR": 1}, skipped["entry_skip_reasons"])
        self.assertEqual(0, skipped["counts"]["entry_eligible_opportunities"])

        liquidation = count_b(value, rows, cutoff=second["available_at"], liquidation_at=second["start"],
                              delayed_entry=True)["cells"][0]["total"]
        self.assertEqual({"ENTRY_AT_LIQUIDATION": 1}, liquidation["entry_skip_reasons"])

        last_start = rows[-1]["start"]
        for row in rows[-5:]:
            row["available_at"] = max(row["available_at"], last_start)
        expired = count_b(value, rows, cutoff=last_start, delayed_entry=True)["cells"][0]["total"]
        self.assertEqual({"NO_SCHEDULED_ENTRY": 1}, expired["entry_skip_reasons"])

    def test_monthly_counts_use_the_setup_receipt_and_reconcile(self):
        value, rows, _ = bar_fixture(across_month=True)
        report = count_b(value, rows, cutoff=rows[-1]["available_at"], profiles=(PROFILE, breaks.BNC_PROFILE))
        for cell in report["cells"]:
            months = cell["months"]
            self.assertEqual({"2000-01", "2000-02"}, set(months))
            for key, count in cell["total"]["counts"].items():
                self.assertEqual(count, sum(month["counts"][key] for month in months.values()), key)
        months = report["cells"][0]["months"]
        self.assertEqual(1, months["2000-01"]["counts"]["entry_eligible_opportunities"])
        self.assertEqual(0, months["2000-02"]["counts"]["entry_eligible_opportunities"])

    def test_safety_abstention_stays_in_the_break_denominator(self):
        value, rows, opening = bar_fixture(no_safety=True)
        total = count_b(value, rows, cutoff=opening["available_at"])["cells"][0]["total"]
        self.assertEqual(1, total["setup_reasons"]["NO_SAFETY_LINE"])
        self.assertEqual({"NO_SAFETY_LINE": 1}, total["abstention_reasons"])
        self.assertEqual((1, 0, 1), tuple(total["counts"][field] for field in (
            "abstentions", "entry_attempts", "groups_consumed")))
        self.assertEqual({"numerator": 1, "denominator": 1, "ratio": {"numerator": 1, "denominator": 1}},
                         total["diagnostics"]["no_safety_line_break_share"])

    def test_q_first_eligible_quote_and_crossed_stop_use_exact_filter_denominators(self):
        value, prefix = fixture()
        at = prefix[-1]["end"]
        raw = history(prefix) + [midpoint(at, "104.4"), midpoint(at + 1, "104.4", at + 2002),
                                midpoint(at + 2, "104.4", at + 2002, "0.00016")]
        successful = raw + [midpoint(at + 3, "104.4", at + 2003, "0.00015")]
        model = count_q(value, successful, at + 2003)
        self.assertEqual("mid_sync", model["geometry_basis"])
        self.assertEqual({"ELIGIBLE": 1}, model["cells"][0]["total"]["entry_statuses"])
        quality = model["quote_observation_filters_by_cost"]["base"]
        self.assertEqual(len(successful), quality["received"])
        self.assertEqual((1, 1), (quality["reasons"]["STALE_QUOTE"], quality["reasons"]["ENTRY_SPREAD_EXCEEDED"]))
        gap_after = successful + [midpoint(at + 4, "85", at + 2004)]
        self.assertEqual(model["cells"], count_q(value, gap_after, at + 2004)["cells"])

        crossed = raw + [midpoint(at + 3, "102", at + 2003), midpoint(at + 4, "104.4", at + 2004)]
        rejection = count_q(value, crossed, at + 2004)["cells"][0]["total"]
        self.assertEqual({"STOP_ALREADY_CROSSED": 1}, rejection["entry_skip_reasons"])
        self.assertEqual({"evaluated": 1, "passed": 0}, rejection["entry_price_filters"]["stop_side"])
        self.assertEqual({"evaluated": 0, "passed": 0}, rejection["entry_price_filters"]["stop_atr_window"])
        boundary = count_q(value, successful, at + 2003, liquidation=at + 2003)["cells"][0]["total"]
        self.assertEqual({"ENTRY_AT_LIQUIDATION": 1}, boundary["entry_skip_reasons"])

    def test_fxr_target_gate_counts_at_entry_with_no_target_receipt(self):
        raw, at = winning_tape()
        report = signal_count.count_q(quotes.Tape(raw), tick="0.0001", as_of=at + 701,
                                      profiles=(breaks.FXR_PROFILE,), costs=("base",))
        total = report["cells"][0]["total"]
        self.assertEqual(1, total["counts"]["entry_eligible_opportunities"])
        self.assertEqual({"evaluated": 1, "passed": 1}, total["entry_price_filters"]["fxr_target"])
        self.assertFalse(report["outcomes_computed"])


class SignalCounterCliTests(unittest.TestCase):
    def execute(self, *args):
        return subprocess.run([sys.executable, str(ROOT / "tools" / "signal_count.py"), *map(str, args)],
                              capture_output=True, text=True, check=False)

    def test_metadata_status_and_exclusive_output(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "status.json"
            args = ("status", ROOT / "config" / "trendline-study-v1.json", output)
            first = self.execute(*args)
            self.assertEqual(0, first.returncode, first.stderr)
            original = output.read_bytes()
            status = json.loads(original)
            self.assertIsNone(status["feasibility"]["actual_counts"])
            self.assertFalse(status["market_data_read"])
            self.assertTrue(any(issue["code"].startswith("source_") for issue in status["development_preflight_issues"]))
            self.assertNotEqual(0, self.execute(*args).returncode)
            self.assertEqual(original, output.read_bytes())

    def test_only_invented_development_and_frozen_initial_profiles_are_allowed(self):
        value, rows, opening = bar_fixture()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, hours, _ = files(root, value, rows)
            output = root / "count.json"
            flags = ("--tick-size", "0.0001", "--as-of", opening["available_at"], "--cost-profile", "base")
            run = self.execute("bars", source, hours, output, *flags, "--profile", PROFILE)
            self.assertEqual(0, run.returncode, run.stderr)
            result = json.loads(output.read_bytes())
            self.assertEqual(1, result["cells"][0]["total"]["counts"]["entry_eligible_opportunities"])
            self.assertNotIn("entry_rule", result)
            delayed = root / "delayed.json"
            run = self.execute("bars", source, hours, delayed, *flags, "--profile", PROFILE, "--delayed-entry")
            self.assertEqual(0, run.returncode, run.stderr)
            variant = json.loads(delayed.read_bytes())
            self.assertEqual(signal_count.DELAYED_ENTRY_VERSION, variant["schema"])
            self.assertEqual({"PENDING": 1}, variant["cells"][0]["total"]["entry_statuses"])
            rejected = root / "forbidden.json"
            self.assertNotEqual(0, self.execute("bars", source, hours, rejected, *flags,
                                               "--profile", "TRL_BRK3_DLY").returncode)
            raw = json.loads(source.read_bytes())
            raw["partition"] = "validation"
            source.write_text(json.dumps(raw), encoding="utf-8")
            denied = self.execute("bars", source, root / "missing-hours.json", rejected, *flags)
            self.assertIn("before price read", denied.stderr)
            self.assertFalse(rejected.exists())
            raw.update(partition="development", kind="market_hours")
            source.write_text(json.dumps(raw), encoding="utf-8")
            self.assertIn("invented EURUSD Level B declaration required",
                          self.execute("bars", source, hours, rejected, *flags).stderr)
            tape = root / "quotes.json"
            tape.write_text(json.dumps({"partition": "validation"}), encoding="utf-8")
            self.assertIn("only invented development quotes", self.execute("quotes", tape, rejected, *flags).stderr)
            self.assertFalse(rejected.exists())
