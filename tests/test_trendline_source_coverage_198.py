"""Invented archive-clock coverage and opening evidence checks."""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from forex_demo_lab.elliott_sessions_146 import HOUR, START
from forex_demo_lab.trendline import data, source_coverage as coverage


DAY = 24 * HOUR


def session(start, hours=24, label="session_0"):
    end = start + hours * HOUR
    return {"kind": "session", "label": label, "start": start, "end": end,
            "h1": list(range(start, end, HOUR)) + [end], "h4": list(range(start, end, 4 * HOUR)) + [end],
            "partial": hours < 23}


def calendar(*segments, delay=0):
    return {"kind": "invented_session_calendar_146",
            "scope": {"start": segments[0]["start"], "end": segments[-1]["end"]},
            "finalization_delay_ms": delay, "segments": list(segments)}


def annual_fixture(start, days):
    segments = []
    timestamps = []
    for index in range(days):
        cursor = start + index * DAY
        if datetime.fromtimestamp(cursor // 1000, timezone.utc).weekday() < 5:
            row = session(cursor, label=f"session_{index}")
            timestamps.extend(row["h1"][:-1])
        else:
            row = {"kind": "closure", "start": cursor, "end": cursor + DAY, "reason": "weekend"}
        segments.append(row)
    return calendar(*segments), timestamps


class SourceCoverage198Tests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.folder = Path(temporary.name)
        self.meta = self.folder / "scope.json"
        self.timestamps = self.folder / "timestamps.json"
        self.end = START + 4 * HOUR
        pause = {"kind": "closure", "reason": "weekend", "start": self.end, "end": self.end + HOUR}
        self.dev_start = pause["end"]
        self.descriptor = {"schema": coverage.VERSION, "kind": coverage.DESCRIPTOR_KIND, "symbol": "EURUSD",
                           "warmup_calendar": calendar(session(START, 4), pause, delay=1000),
                           "development_calendar": calendar(session(self.dev_start, 4)), "input_sha256": "0" * 64}

    def write(self, stamps, *, kind=coverage.INPUT_KIND):
        raw = json.dumps({"kind": kind, "timestamps": stamps}).encode()
        self.timestamps.write_bytes(raw)
        self.descriptor["input_sha256"] = hashlib.sha256(raw).hexdigest()
        self.meta.write_text(json.dumps(self.descriptor))

    def audit(self, stamps):
        self.write(stamps)
        return coverage.audit_files(self.meta, self.timestamps)

    def test_seams_closures_ties_and_first_opening_timestamp(self):
        opening = self.dev_start
        report = self.audit([START, START, START + HOUR + 2, START + 3 * HOUR, self.end,
                             opening, opening + HOUR + 5, opening + HOUR + 7, opening + 3 * HOUR])
        warmup = report["warmup"]
        self.assertEqual((5, 1, 1), tuple(warmup[key] for key in
                                        ("timestamps", "tied_timestamp_transitions", "closure_timestamps")))
        self.assertEqual({"exact_source_timestamp": 2, "late_first_quote": 1, "no_quote": 1,
                          "late_first_quotes": [{"start": opening + HOUR, "lag_ms": 5}],
                          "no_quote_starts": [opening + 2 * HOUR]}, report["development"]["h1_opening"])
        self.assertEqual(1, warmup["coverage"]["H4"]["scheduled"])
        self.assertEqual([START], warmup["coverage"]["H4"]["missing_window_starts"])
        self.assertEqual(0, warmup["coverage"]["D1"]["with_all_children_observed"])
        self.assertEqual(1, report["warmup_at_development_start"]["H1"][
            "trailing_complete_due_by_timestamp_coverage"])
        self.assertFalse(report["signal_counts_computed"])

    def test_warmup_uses_only_bars_due_at_the_seam(self):
        self.dev_start = self.end
        self.descriptor["warmup_calendar"] = calendar(session(START, 4), delay=1000)
        self.descriptor["development_calendar"] = calendar(session(self.dev_start, 4))
        warm_stamps = [START + offset * HOUR for offset in range(4)]
        report = self.audit(warm_stamps + [self.dev_start])
        readiness = report["warmup_at_development_start"]
        self.assertEqual(1, report["warmup"]["coverage"]["D1"]["with_all_children_observed"])
        self.assertEqual([START], readiness["D1"]["pending_starts"])
        self.assertEqual(0, readiness["H4"]["complete_due_by_timestamp_coverage"])
        self.assertEqual(3, readiness["H1"]["complete_due_by_timestamp_coverage"])
        self.assertEqual(readiness, self.audit(warm_stamps)["warmup_at_development_start"])

    def test_full_three_year_fixture_reuses_study_minimums(self):
        self.descriptor["warmup_calendar"], warm_stamps = annual_fixture(START, 366)
        self.descriptor["development_calendar"], development_stamps = annual_fixture(START + 366 * DAY, 730)
        report = self.audit(warm_stamps + development_stamps)
        readiness = report["warmup_at_development_start"]
        self.assertEqual({"D1": 253, "H4": 390, "H1": 253}, {key: row["minimum"] for key, row in readiness.items()})
        self.assertEqual(260, readiness["D1"]["complete_due_by_timestamp_coverage"])
        self.assertTrue(all(row["minimum_trailing_complete_due_met"] for row in readiness.values()))
        self.assertEqual(522, report["development"]["coverage"]["D1"]["with_all_children_observed"])
        warm_stamps.pop(-24)
        day = self.audit(warm_stamps + development_stamps)["warmup_at_development_start"]["D1"]
        self.assertEqual(259, day["complete_due_by_timestamp_coverage"])
        self.assertTrue(day["minimum_complete_due_met"])
        self.assertFalse(day["minimum_trailing_complete_due_met"])

    def test_empty_timestamp_file_reports_missing_without_filling(self):
        report = self.audit([])
        self.assertEqual(0, report["warmup"]["h1_opening"]["exact_source_timestamp"])
        self.assertEqual(4, report["warmup"]["h1_opening"]["no_quote"])
        self.assertEqual(4, report["development"]["h1_opening"]["no_quote"])
        self.assertFalse(report["market_source_admitted"])
        self.assertFalse(report["price_rows_read"])

    def test_unordered_bad_type_and_half_open_timestamps_fail(self):
        for stamps, error in (([START + 1, START], "source order"), ([True], "nonnegative integer"),
                              ([START - 1], "half-open"), ([self.dev_start + 4 * HOUR], "half-open")):
            with self.subTest(stamps=stamps), self.assertRaisesRegex(ValueError, error):
                self.audit(stamps)

    def test_scope_and_calendar_validate_before_reading_timestamp_file(self):
        self.descriptor["kind"] = "market_archive"
        self.write([])
        with patch.object(data, "read_json", wraps=data.read_json) as read:
            with self.assertRaisesRegex(ValueError, "invented EURUSD"):
                coverage.audit_files(self.meta, self.timestamps)
            read.assert_called_once_with(self.meta)
        self.descriptor["kind"] = coverage.DESCRIPTOR_KIND
        self.descriptor["development_calendar"] = calendar(session(self.dev_start + HOUR, 4))
        self.write([])
        with patch.object(data, "read_json", wraps=data.read_json) as read:
            with self.assertRaisesRegex(ValueError, "warmup must end"):
                coverage.audit_files(self.meta, self.timestamps)
            read.assert_called_once_with(self.meta)

    def test_hash_and_invented_timestamp_kind_are_enforced(self):
        self.write([START])
        self.timestamps.write_bytes(self.timestamps.read_bytes() + b" ")
        with self.assertRaisesRegex(ValueError, "coverage declaration"):
            coverage.audit_files(self.meta, self.timestamps)
        self.write([START], kind="provider_quotes")
        with self.assertRaisesRegex(ValueError, "invented source timestamp array"):
            coverage.audit_files(self.meta, self.timestamps)

    def test_module_cli_produces_bound_report_once(self):
        self.write([START, self.dev_start + 1])
        output = self.folder / "result.json"
        command = [sys.executable, "-m", "forex_demo_lab.trendline.source_coverage",
                   str(self.meta), str(self.timestamps), str(output)]
        subprocess.run(command, check=True, capture_output=True)
        raw = output.read_bytes()
        self.assertEqual(self.descriptor["input_sha256"], json.loads(raw)["timestamp_file_sha256"])
        self.assertNotEqual(0, subprocess.run(command, capture_output=True).returncode)
        self.assertEqual(raw, output.read_bytes())
