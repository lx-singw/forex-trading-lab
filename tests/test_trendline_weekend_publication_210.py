"""Receipt evidence around an invented closure."""

from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from forex_demo_lab.trendline import data, weekend_publication
from test_trendline_data_163 import calendar


def event(kind, time, ordinal=0):
    return {"kind": kind, "time": time, "ordinal": ordinal}


class WeekendPublicationTests(unittest.TestCase):
    def setUp(self):
        self.calendar = calendar((8, 4), (48,), partial=True)
        self.h4_end = self.calendar["segments"][0]["end"]
        self.open_at = self.calendar["segments"][2]["start"]

    def trace(self, *events):
        return {"kind": weekend_publication.TRACE_KIND, "calendar": self.calendar,
                "h4_end": self.h4_end, "events": list(events)}

    def test_records_early_completion_and_observed_closure_update(self):
        missing = event("h4_unavailable", self.h4_end)
        update = event("eurusd_update", self.h4_end + 1)
        complete = event("h4_completed", self.h4_end + 2)
        later = event("h4_completed", self.h4_end + 3)
        reopening = event("eurusd_update", self.open_at + 1)
        report = weekend_publication.audit(self.trace(missing, update, complete, later, reopening))
        self.assertEqual("BEFORE_OPEN", report["observed_completion_order"])
        self.assertEqual(missing["time"], report["last_unavailable_observed"]["time"])
        self.assertEqual(complete["time"], report["first_completed_observed"]["time"])
        self.assertEqual(update["time"], report["first_eurusd_update_observed"]["time"])
        self.assertEqual(reopening["time"], report["first_eurusd_update_at_or_after_open"]["time"])
        self.assertEqual(1, report["observed_updates_before_scheduled_open"])
        self.assertIsNone(report["opening_marker"])

    def test_late_poll_stays_late_observed_and_retains_the_gap(self):
        absent = event("h4_unavailable", self.h4_end)
        opened = event("scheduled_h1_open", self.open_at)
        after = event("h4_completed", self.open_at + 2000)
        report = weekend_publication.audit(self.trace(absent, opened, after))
        self.assertEqual("AFTER_OPEN", report["observed_completion_order"])
        self.assertEqual(self.h4_end, report["last_unavailable_observed"]["time"])
        self.assertEqual(after["time"], report["first_completed_observed"]["time"])
        self.assertIsNone(report["first_eurusd_update_observed"])

    def test_shared_timestamps_use_only_the_recorded_ordinals(self):
        completed = event("h4_completed", self.open_at, 1)
        mark = event("scheduled_h1_open", self.open_at, 2)
        self.assertEqual("BEFORE_OPEN", weekend_publication.audit(
            self.trace(completed, mark))["observed_completion_order"])
        self.assertEqual("AFTER_OPEN", weekend_publication.audit(
            self.trace({**mark, "ordinal": 0}, completed))["observed_completion_order"])
        self.assertEqual("SAME_TIME_ORDER_UNRESOLVED", weekend_publication.audit(
            self.trace(completed))["observed_completion_order"])

    def test_no_completed_observation_remains_unknown(self):
        report = weekend_publication.audit(self.trace(event("scheduled_h1_open", self.open_at)))
        self.assertEqual("COMPLETION_UNOBSERVED", report["observed_completion_order"])
        self.assertIsNone(report["first_completed_observed"])

    def test_rejects_mismatched_open_reversed_events_and_visibility_regression(self):
        complete = event("h4_completed", self.h4_end)
        for trace in (
            self.trace(event("scheduled_h1_open", self.open_at + 1)),
            self.trace(complete, complete),
            self.trace(complete, event("h4_unavailable", self.h4_end + 1)),
            {**self.trace(), "h4_end": self.h4_end - 3_600_000 * 4},
            {**self.trace(), "kind": "market_weekend_publication_trace"},
        ):
            with self.assertRaises(ValueError):
                weekend_publication.audit(trace)
        wrong_closure = deepcopy(self.trace())
        wrong_closure["calendar"]["segments"][1]["reason"] = "maintenance"
        with self.assertRaisesRegex(ValueError, "declared weekend"):
            weekend_publication.audit(wrong_closure)

    def test_cli_writes_a_bound_report_and_refuses_to_overwrite(self):
        trace = self.trace(event("h4_completed", self.h4_end))
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "trace.json"
            report = Path(directory) / "report.json"
            source.write_text(json.dumps(trace), encoding="utf-8")
            command = [sys.executable, "-m", weekend_publication.__name__, str(source), str(report)]
            subprocess.run(command, check=True, capture_output=True)
            content = report.read_bytes()
            result = json.loads(content)
            self.assertEqual(data.read_json(source)[1], result.pop("input_sha256"))
            self.assertEqual(weekend_publication.audit(trace), result)
            self.assertNotEqual(0, subprocess.run(command, capture_output=True).returncode)
            self.assertEqual(content, report.read_bytes())
