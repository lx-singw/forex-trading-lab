"""Calendar-only bounds for the frozen first-opening rule."""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from forex_demo_lab.trendline import entry_timing
from test_trendline_data_163 import calendar, descriptor
from test_trendline_fills_164 import setup


class EntryTimingTests(unittest.TestCase):
    def test_closure_and_partition_boundary_match_price_model(self):
        cal = calendar((8, 4), (48,), partial=True)
        report = entry_timing.audit(cal)
        early, after_closure, terminal = report["h4"]
        self.assertEqual("LATE_AT_EARLIEST_PUBLICATION", early["status"])
        self.assertEqual(early["first_scheduled_open"] + 2000, early["earliest_decision_at"])
        self.assertEqual("EARLIEST_PUBLICATION_BEFORE_OPEN", after_closure["status"])
        self.assertEqual(48 * 3_600_000, after_closure["first_scheduled_open"] - after_closure["h4_end"])
        self.assertEqual("NO_SCHEDULED_ENTRY", terminal["status"])
        self.assertIsNone(terminal["first_scheduled_open"])
        self.assertIsNone(terminal["expires_at"])
        model, _, _ = setup(source=descriptor(cal))
        for row in report["h4"]:
            expected = model.entry_window(row["h4_end"])
            self.assertEqual(expected.start if expected else None, row["first_scheduled_open"])

    def test_zero_delay_reports_equal_time_as_conditional(self):
        cal = calendar((8, 4), (48,), partial=True)
        cal["finalization_delay_ms"] = 0
        report = entry_timing.audit(cal)
        self.assertEqual("TIED_AT_EARLIEST_PUBLICATION", report["h4"][0]["status"])
        self.assertEqual(1, report["ceiling_without_same_time_order"])
        self.assertEqual(2, report["ceiling_if_decision_precedes_tied_open"])

    def test_closure_exactly_consumed_by_delay_is_also_conditional(self):
        cal = calendar((4, 4), (1,), partial=True)
        _, closure, second = cal["segments"]
        adjustment = 3_600_000 - cal["finalization_delay_ms"]
        for key in ("start", "end"):
            second[key] -= adjustment
        for key in ("h1", "h4"):
            second[key] = [at - adjustment for at in second[key]]
        closure["end"] = second["start"]
        cal["scope"]["end"] = second["end"]
        report = entry_timing.audit(cal)
        self.assertEqual("TIED_AT_EARLIEST_PUBLICATION", report["h4"][0]["status"])
        self.assertEqual(0, report["ceiling_without_same_time_order"])
        self.assertEqual(1, report["ceiling_if_decision_precedes_tied_open"])

    def test_cli_audits_calendar_and_rejects_other_kinds(self):
        cal = calendar((4,), partial=True)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "calendar.json"
            report = Path(directory) / "report.json"
            command = [sys.executable, "-m", entry_timing.__name__, str(path), str(report)]
            path.write_text(json.dumps(cal), encoding="utf-8")
            subprocess.run(command, check=True, capture_output=True)
            self.assertEqual(entry_timing.audit(cal), json.loads(report.read_text(encoding="utf-8")))
            report.unlink()
            path.write_text(json.dumps({**cal, "kind": "market_calendar"}), encoding="utf-8")
            rejected = subprocess.run(command, capture_output=True, text=True)
            self.assertNotEqual(0, rejected.returncode)
            self.assertIn("invented calendar only", rejected.stderr)
            self.assertFalse(report.exists())
