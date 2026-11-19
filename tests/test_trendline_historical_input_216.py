"""Exercise the historical reader with fabricated H1 bytes and a test-only pin."""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from forex_demo_lab.elliott_sessions_146 import HOUR
from forex_demo_lab.trendline import data, historical_input, study
from test_trendline_study_165 import declared, span


def midnight(year):
    return int(datetime(year, 1, 1, tzinfo=timezone.utc).timestamp()) * 1000


def row(start):
    return {"start": start, "end": start + HOUR, "available_at": start + HOUR,
            "open": "1.1", "high": "1.1002", "low": "1.0998", "close": "1.1", "spread_pips": "1.2"}


class HistoricalInputTests(unittest.TestCase):
    def setUp(self):
        self.work = tempfile.TemporaryDirectory()
        self.addCleanup(self.work.cleanup)
        self.root = Path(self.work.name)
        self.prices = self.root / "bars.json"
        self.manifest = self.root / "manifest.json"
        self.plan_path = self.root / "plan.json"
        self.plan = declared()
        self.plan.update(case="current_unassigned", source={"alias": "source_existing_export", "route": "existing_export"})
        self.plan["partitions"]["development"]["warmup"]["declared_complete_bars"]["H1"] = 6000
        self.rows = [row(midnight(2013) + i * HOUR) for i in range(6000)] + [row(midnight(2014))]

    def bundle(self, **override):
        prices = data.canonical(self.rows)
        self.prices.write_bytes(prices)
        self.plan["input_sha256"] = hashlib.sha256(prices).hexdigest()
        plan = data.canonical(self.plan)
        self.plan_path.write_bytes(plan)
        manifest = {"schema": historical_input.VERSION, "kind": historical_input.MANIFEST_KIND,
                    "symbol": "EURUSD", "partition": "development", "plan_file": "plan.json",
                    "plan_file_sha256": hashlib.sha256(plan).hexdigest(), "price_file": "bars.json", **override}
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
        self.plan["partitions"]["validation"] = study.draft()["partitions"]["validation"]
        with self.bundle():
            warmup, development, receipt = historical_input.load_level_b(self.manifest)
        self.assertEqual(6000, len(warmup))
        self.assertEqual(1, len(development))
        self.assertEqual(data.Hour.from_record(self.rows[-1], "bid_only"), development[0])
        self.assertIsNone(receipt["actual_counts"])
        self.assertEqual(6000, receipt["warmup_rows"])
        self.assertEqual(self.plan["input_sha256"], receipt["input_sha256"])

    def test_changed_plan_and_overlapping_holdout_stop_before_price_read(self):
        with self.bundle(), patch.object(historical_input, "_read_hours", side_effect=AssertionError("no prices expected")):
            self.plan_path.write_bytes(b"changed")
            with self.assertRaisesRegex(ValueError, "plan differs"):
                historical_input.load_level_b(self.manifest)
        self.plan["partitions"]["validation"]["interval"] = span("2015-01-01", "2017-01-01")
        with self.bundle(), patch.object(historical_input, "_read_hours", side_effect=AssertionError("no prices expected")):
            with self.assertRaisesRegex(ValueError, "development_scope_overlaps_reserved_validation"):
                historical_input.load_level_b(self.manifest)

    def test_price_hash_is_checked_before_decoding(self):
        with self.bundle(), patch.object(historical_input, "strict_json", wraps=historical_input.strict_json) as decode:
            self.prices.write_bytes(b"malformed price contents")
            with self.assertRaisesRegex(ValueError, "before parsing"):
                historical_input.load_level_b(self.manifest)
        self.assertEqual(2, decode.call_count)

    def test_late_warmup_receipt_does_not_count_at_development_start(self):
        self.rows[-2]["available_at"] = midnight(2014) + 1
        with self.bundle():
            with self.assertRaisesRegex(ValueError, "H1 warmup"):
                historical_input.load_level_b(self.manifest)

    def test_reader_rejects_outside_rows_missing_warmup_and_path_traversal(self):
        self.rows.append(row(midnight(2016)))
        with self.bundle():
            with self.assertRaisesRegex(ValueError, "outside reviewed"):
                historical_input.load_level_b(self.manifest)
        self.rows = self.rows[1:-1]
        with self.bundle():
            with self.assertRaisesRegex(ValueError, "H1 warmup"):
                historical_input.load_level_b(self.manifest)
        with self.bundle(price_file="../other.json"):
            with self.assertRaisesRegex(ValueError, "relative reviewed filename"):
                historical_input.load_level_b(self.manifest)

    def test_cli_current_repository_cannot_read_historical_data_through_self_approval(self):
        self.bundle()
        report = self.root / "receipt.json"
        entry = data.ROOT / "tools/signal_count.py"
        run = subprocess.run([sys.executable, str(entry), "historical-input", str(self.manifest), str(report)],
                             capture_output=True, text=True)
        self.assertNotEqual(0, run.returncode)
        self.assertIn("no recorded qualification before price read", run.stderr)
        self.assertFalse(report.exists())
