"""Exercise the historical reader with a fabricated calendar, H1 bytes and a test-only pin."""

from datetime import datetime, timezone
import hashlib
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from forex_demo_lab.elliott_sessions_146 import HOUR
from forex_demo_lab.trendline import data, historical_calendar, historical_input, study
from test_trendline_study_165 import declared, span


def midnight(year):
    return int(datetime(year, 1, 1, tzinfo=timezone.utc).timestamp()) * 1000


def row(start, end=None):
    if end is None:
        end = start + HOUR
    return {"start": start, "end": end, "available_at": end,
            "open": "1.1", "high": "1.1002", "low": "1.0998", "close": "1.1", "spread_pips": "1.2"}


def session(start, end):
    return {"kind": "session", "start": start, "end": end, "partial": end - start < 23 * HOUR,
            "h1": [*range(start, end, HOUR), end], "h4": [*range(start, end, 4 * HOUR), end]}


def closure(start, end):
    return {"kind": "closure", "start": start, "end": end, "reason": "holiday"}


class HistoricalInputTests(unittest.TestCase):
    def setUp(self):
        self.work = tempfile.TemporaryDirectory()
        self.addCleanup(self.work.cleanup)
        self.root = Path(self.work.name)
        self.prices = self.root / "bars.json"
        self.manifest = self.root / "manifest.json"
        self.plan_path = self.root / "plan.json"
        self.calendar_path = self.root / "calendar.json"
        self.plan = declared()
        self.plan.update(case="current_unassigned", source={"alias": "source_existing_export", "route": "existing_export"})
        self.plan["partitions"]["validation"] = study.draft()["partitions"]["validation"]
        development = self.plan["partitions"]["development"]
        development["interval"] = span("2021-01-01", "2023-01-01")
        development["warmup"]["interval"] = span("2020-01-01", "2021-01-01")
        self.plan["endpoints"]["development"]["liquidation_at"] = None
        for evidence in self.plan["evidence"].values():
            evidence["intervals"] = [span("2020-01-01", "2023-01-01")]

        self.seam = midnight(2021)
        day = 24 * HOUR
        first = self.seam - 253 * day
        short_end = self.seam + 5 * HOUR + HOUR // 2
        sessions = [session(start, start + day) for start in range(first, self.seam, day)]
        sessions.append(session(self.seam, short_end))
        self.calendar = {"kind": historical_calendar.KIND, "segments": [
            closure(midnight(2020), first), *sessions, closure(short_end, midnight(2023)),
        ]}
        self.rows = [row(left, right) for item in sessions for left, right in zip(item["h1"], item["h1"][1:])]

    def bundle(self, **override):
        prices = data.canonical(self.rows)
        self.prices.write_bytes(prices)
        self.plan["input_sha256"] = hashlib.sha256(prices).hexdigest()
        calendar = data.canonical(self.calendar)
        self.calendar_path.write_bytes(calendar)
        self.plan["calendar_sha256"] = hashlib.sha256(calendar).hexdigest()
        plan = data.canonical(self.plan)
        self.plan_path.write_bytes(plan)
        manifest = {"schema": historical_input.VERSION, "kind": historical_input.MANIFEST_KIND,
                    "symbol": "EURUSD", "partition": "development", "plan_file": "plan.json",
                    "plan_file_sha256": hashlib.sha256(plan).hexdigest(), "calendar_file": "calendar.json",
                    "price_file": "bars.json", **override}
        content = data.canonical(manifest)
        self.manifest.write_bytes(content)
        return patch.object(historical_input, "REVIEWED_MANIFESTS", frozenset({hashlib.sha256(content).hexdigest()}))

    def test_unreviewed_manifest_leaves_plan_and_prices_unopened(self):
        self.bundle()
        self.plan_path.unlink()
        with patch.object(historical_input, "strict_json", side_effect=AssertionError("no parsing expected")):
            with self.assertRaisesRegex(ValueError, "no recorded qualification"):
                historical_input.load_level_b(self.manifest)

    def test_reviewed_input_yields_typed_rows_with_separate_warmup(self):
        with self.bundle():
            result = historical_input.load_level_b(self.manifest)
        receipt = result.receipt
        self.assertEqual(6072, len(result.warmup))
        self.assertEqual(6, len(result.development))
        self.assertEqual(data.Hour.from_record(self.rows[-1], "bid_only"), result.development[-1])
        self.assertIsNone(receipt["actual_counts"])
        self.assertEqual(self.plan["input_sha256"], receipt["input_sha256"])
        self.assertEqual(self.plan["calendar_sha256"], result.calendar.sha256)
        self.assertEqual(253, receipt["warmup_at_development_start"]["D1"]["complete_by_cutoff"])
        self.assertEqual(2, receipt["development_at_scope_end"]["H4"]["complete_by_cutoff"])

    def test_changed_plan_and_overlapping_holdout_stop_before_price_read(self):
        with self.bundle(), patch.object(historical_input, "_read_hours", side_effect=AssertionError("no prices expected")):
            self.plan_path.write_bytes(b"changed")
            with self.assertRaisesRegex(ValueError, "plan differs"):
                historical_input.load_level_b(self.manifest)
        self.plan["partitions"]["validation"]["interval"] = span("2022-01-01", "2024-01-01")
        with self.bundle(), patch.object(historical_input, "_read_hours", side_effect=AssertionError("no prices expected")):
            with self.assertRaisesRegex(ValueError, "development_scope_overlaps_reserved_validation"):
                historical_input.load_level_b(self.manifest)

    def test_price_hash_is_checked_before_decoding(self):
        with self.bundle(), patch.object(historical_input, "strict_json", wraps=historical_input.strict_json) as decode:
            self.prices.write_bytes(b"malformed price contents")
            with self.assertRaisesRegex(ValueError, "before parsing"):
                historical_input.load_level_b(self.manifest)
        self.assertEqual(3, decode.call_count)

    def test_late_warmup_receipt_does_not_count_at_development_start(self):
        self.rows[6071]["available_at"] = self.seam + 1
        with self.bundle():
            with self.assertRaisesRegex(ValueError, "warmup coverage"):
                historical_input.load_level_b(self.manifest)

    def test_reader_rejects_outside_rows_missing_warmup_and_path_traversal(self):
        self.rows.append(row(midnight(2023)))
        with self.bundle():
            with self.assertRaisesRegex(ValueError, "outside reviewed"):
                historical_input.load_level_b(self.manifest)
        self.rows = self.rows[1:-1]
        with self.bundle():
            with self.assertRaisesRegex(ValueError, "warmup coverage"):
                historical_input.load_level_b(self.manifest)
        with self.bundle(price_file="../other.json"):
            with self.assertRaisesRegex(ValueError, "relative reviewed filename"):
                historical_input.load_level_b(self.manifest)

    def test_calendar_hash_and_segment_gap_reject_before_price_read(self):
        with self.bundle(), patch.object(historical_input, "_read_hours", side_effect=AssertionError("no prices expected")):
            self.calendar_path.write_bytes(b"changed")
            with self.assertRaisesRegex(ValueError, "calendar file differs"):
                historical_input.load_level_b(self.manifest)
        self.calendar["segments"][0]["end"] -= HOUR
        with self.bundle(), patch.object(historical_input, "_read_hours", side_effect=AssertionError("no prices expected")):
            with self.assertRaisesRegex(ValueError, "without gaps or overlaps"):
                historical_input.load_level_b(self.manifest)

    def test_parent_edges_and_seam_are_enforced_before_price_read(self):
        short = self.calendar["segments"][-2]
        with patch.object(historical_input, "_read_hours", side_effect=AssertionError("no prices expected")):
            short["h4"][1] += HOUR // 2
            with self.bundle():
                with self.assertRaisesRegex(ValueError, "only terminal intraday bar may be shortened"):
                    historical_input.load_level_b(self.manifest)
            short["h4"][1] -= HOUR // 2
            self.calendar["segments"][-3]["end"] += HOUR
            with self.bundle():
                with self.assertRaisesRegex(ValueError, "session crosses"):
                    historical_input.load_level_b(self.manifest)

    def test_missing_child_marks_development_parents_incomplete(self):
        gap = self.rows.pop(-1)["start"]
        with self.bundle():
            receipt = historical_input.load_level_b(self.manifest).receipt
        coverage = receipt["development_at_scope_end"]
        self.assertEqual([gap], coverage["H1"]["missing_due_starts"])
        self.assertEqual([self.seam + 4 * HOUR], coverage["H4"]["missing_due_starts"])
        self.assertEqual([self.seam], coverage["D1"]["missing_due_starts"])

    def test_h1_observation_must_match_a_scheduled_window_exactly(self):
        final = self.rows[-1]
        final["end"] = final["available_at"] = final["start"] + HOUR
        with self.bundle():
            with self.assertRaisesRegex(ValueError, "outside reviewed calendar window"):
                historical_input.load_level_b(self.manifest)
        self.rows[-1] = row(self.seam + 6 * HOUR)
        with self.bundle():
            with self.assertRaisesRegex(ValueError, "outside reviewed calendar window"):
                historical_input.load_level_b(self.manifest)

    def test_warmup_checks_h4_and_calendar_finalization(self):
        counts = self.plan["partitions"]["development"]["warmup"]["declared_complete_bars"]
        counts["H4"] += 1
        with self.bundle():
            with self.assertRaisesRegex(ValueError, "H4 warmup coverage"):
                historical_input.load_level_b(self.manifest)
        counts["H4"] -= 1
        self.plan["latency"]["finalization_delay_ms"] = 1
        with self.bundle():
            with self.assertRaisesRegex(ValueError, "D1 warmup coverage"):
                historical_input.load_level_b(self.manifest)

    def test_three_year_fabricated_weekday_calendar_fits_input_limits(self):
        start, end = midnight(2020), midnight(2023)
        day = 24 * HOUR
        self.rows = []
        segments = []
        for left in range(start, end, day):
            if datetime.fromtimestamp(left // 1000, timezone.utc).weekday() < 5:
                segments.append(session(left, left + day))
                self.rows.extend(row(hour) for hour in range(left, left + day, HOUR))
            elif segments[-1]["kind"] == "closure":
                segments[-1]["end"] += day
            else:
                segments.append({"kind": "closure", "start": left, "end": left + day, "reason": "weekend"})
        self.calendar["segments"] = segments
        with self.bundle():
            result = historical_input.load_level_b(self.manifest)
        self.assertEqual(18792, len(result.calendar.frame("H1")))
        self.assertEqual(262, result.receipt["warmup_at_development_start"]["D1"]["complete_by_cutoff"])
        self.assertEqual(521, result.receipt["development_at_scope_end"]["D1"]["complete_by_cutoff"])

    def test_cli_current_repository_cannot_read_historical_data_through_self_approval(self):
        self.bundle()
        report = self.root / "receipt.json"
        entry = data.ROOT / "tools/signal_count.py"
        run = subprocess.run([sys.executable, str(entry), "historical-input", str(self.manifest), str(report)],
                             capture_output=True, text=True)
        self.assertNotEqual(0, run.returncode)
        self.assertIn("no recorded qualification before price read", run.stderr)
        self.assertFalse(report.exists())

    def test_cli_writes_coverage_receipt_for_a_test_reviewed_bundle(self):
        report = self.root / "receipt.json"
        entry = data.ROOT / "tools/signal_count.py"
        args = [str(entry), "historical-input", str(self.manifest), str(report)]
        with self.bundle(), patch.object(sys, "argv", args):
            runpy.run_path(str(entry), run_name="__main__")
        receipt, _ = data.read_json(report)
        self.assertEqual(253, receipt["warmup_at_development_start"]["D1"]["complete_by_cutoff"])
        self.assertIsNone(receipt["actual_counts"])
