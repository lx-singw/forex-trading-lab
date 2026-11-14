import csv
from datetime import timedelta
import json
import importlib.util
from pathlib import Path
import tempfile
import unittest

from forex_demo_lab.cli import read_bars
from forex_demo_lab.collection import RAW_FIELDS
from forex_demo_lab.reconstruction import reconstruct
from forex_demo_lab.tick_audit import capture_ticks
from forex_demo_lab.tick_audit import sha256
from test_ingestion import START
from test_tick_audit import TickTerminal, tick


class ReconstructionTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.capture = self.root/"capture"
        self.output = self.root/"rebuilt"
        self.api = TickTerminal()

    def collect(self, hours=1, folder=None):
        capture_ticks(self.api, START, START+timedelta(hours=hours), folder or self.capture)

    def metadata(self, change):
        path = self.capture/"capture.json"
        value = json.loads(path.read_text())
        change(value)
        path.write_text(json.dumps(value))

    def test_bid_ask_ohlc_same_millisecond_order_and_opening_spread(self):
        self.api.events = [tick(30, bid=1.1, ask=1.1002), tick(30, bid=1.099, ask=1.1005),
                           tick(3599999, bid=1.101, ask=1.1011)]
        self.collect()
        result = reconstruct(self.capture, self.output)
        with (self.output/"diagnostic-bars.csv").open() as stream:
            bar = next(csv.DictReader(stream))
        self.assertEqual(float(bar["bid_open"]), 1.1)
        self.assertEqual(float(bar["bid_low"]), 1.099)
        self.assertEqual(float(bar["ask_low"]), 1.1002)
        self.assertEqual(float(bar["ask_close"]), 1.1011)
        self.assertAlmostEqual(float(bar["first_quote_spread_pips"]), 2)
        self.assertEqual(int(bar["last_tick_to_end_ms"]), 1)
        self.assertFalse(result["complete_market_history_verified"])
        self.assertFalse(result["historical_timezone_verified"])
        with self.assertRaises(ValueError):
            read_bars(self.output/"diagnostic-bars.csv")

    def test_empty_hour_is_reported_never_filled(self):
        self.collect(hours=2)
        result = reconstruct(self.capture, self.output)
        self.assertEqual(result["rows"], 1)
        self.assertEqual(len(result["coverage"]), 2)
        self.assertEqual(result["coverage"][1]["status"], "no_ticks_unclassified")

    def test_invalid_quote_rejected_without_output(self):
        self.api.events = [tick(bid=1.2, ask=1.1)]
        self.collect()
        with self.assertRaisesRegex(ValueError, "Invalid quotes"):
            reconstruct(self.capture, self.output)
        self.assertFalse(self.output.exists())

    def test_failed_api_cannot_be_used_even_when_some_ticks_returned(self):
        self.api.error = -1
        self.collect()
        with self.assertRaisesRegex(ValueError, "no API errors"):
            reconstruct(self.capture, self.output)

    def test_window_holes_overlaps_and_wrong_counts_rejected(self):
        self.collect(7)
        original = (self.capture/"capture.json").read_text()
        for change in (
            lambda m: m["windows"].pop(),
            lambda m: m["windows"][1].update(start_label=m["source_label_start"]),
            lambda m: m["windows"][0].update(ticks=100),
            lambda m: m["windows"][0].update(status="empty"),
            lambda m: m["windows"][0].update(api_error_code=-1),
            lambda m: m.update(source_label_start=START.replace(tzinfo=None).isoformat()),
        ):
            with self.subTest(change=change):
                (self.capture/"capture.json").write_text(original)
                self.metadata(change)
                with self.assertRaises(ValueError):
                    reconstruct(self.capture, self.output)
                self.assertFalse(self.output.exists())

    def test_repeat_identical_and_changed_events_reported_without_independence_claim(self):
        self.collect()
        self.collect(folder=self.root/"same")
        report = reconstruct(self.capture, self.output, repeat=self.root/"same")
        self.assertTrue(report["repeat_comparison"]["identical_ordered_events"])
        self.assertFalse(report["repeat_comparison"]["independent_feed"])
        self.api.events[0]["ask"] += .0001
        self.collect(folder=self.root/"changed")
        report = reconstruct(self.capture, self.root/"changed-output", repeat=self.root/"changed")
        self.assertFalse(report["repeat_comparison"]["identical_ordered_events"])

    def test_repeat_different_window_rejected(self):
        self.collect()
        self.collect(hours=2, folder=self.root/"other")
        with self.assertRaisesRegex(ValueError, "identical requested coverage"):
            reconstruct(self.capture, self.output, repeat=self.root/"other")

    def test_matching_prefix_does_not_claim_proven_cause(self):
        self.api.events = [tick(0, bid=1.1, ask=1.101), tick(100, bid=1.1002, ask=1.101),
                           tick(200, bid=1.1001, ask=1.101), tick(300, bid=1.099, ask=1.101)]
        self.collect(hours=2)
        reference = self.root/"raw.csv"
        with reference.open("w", newline="") as stream:
            writer = csv.writer(stream)
            writer.writerow(RAW_FIELDS)
            writer.writerow([START.isoformat(), 1.1, 1.1002, 1.1, 1.1001, 3, 1, 0])
        report = reconstruct(self.capture, self.output, reference)
        item = report["coverage"][0]
        self.assertEqual(item["reference_status"], "mismatch")
        self.assertEqual(item["matching_prefixes"]["count"], 1)
        self.assertEqual(item["matching_prefixes"]["first"]["ticks"], 3)
        self.assertFalse(item["matching_prefixes"]["proves_truncation"])

    def test_existing_destination_never_overwritten(self):
        self.collect()
        self.output.mkdir()
        sentinel = self.output/"keep.txt"
        sentinel.write_text("keep")
        with self.assertRaises(FileExistsError):
            reconstruct(self.capture, self.output)
        self.assertEqual(sentinel.read_text(), "keep")

    def test_tampered_tick_capture_rejected(self):
        self.collect()
        with (self.capture/"ticks.csv.gz").open("ab") as stream:
            stream.write(b"tampered")
        with self.assertRaisesRegex(ValueError, "hash mismatch"):
            reconstruct(self.capture, self.output)

    def test_independent_sql_check_and_deliberately_wrong_close(self):
        spec = importlib.util.spec_from_file_location("checker", Path(__file__).resolve().parents[1]/"scripts/check-reconstruction.py")
        checker = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(checker)
        self.collect()
        reconstruct(self.capture, self.output)
        self.assertEqual(checker.check(self.capture, self.output)["rows"], 1)
        path = self.output/"diagnostic-bars.csv"
        with path.open(newline="") as stream:
            reader = csv.DictReader(stream)
            fields, bars = reader.fieldnames, list(reader)
        bars[0]["bid_close"] = "1.0995"
        with path.open("w", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            writer.writerows(bars)
        provenance = self.output/"provenance.json"
        metadata = json.loads(provenance.read_text())
        metadata["data_sha256"] = sha256(path)
        provenance.write_text(json.dumps(metadata))
        with self.assertRaisesRegex(ValueError, "aggregation mismatch: bid_close"):
            checker.check(self.capture, self.output)
