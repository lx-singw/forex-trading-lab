"""Retrospective report and ledger exports from saved Level B and Q runs."""
import csv
import hashlib
from io import StringIO
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from forex_demo_lab.trendline import breaks, data, quote_replay, quotes, replay_exports, replay_viewer
from test_trendline_viewer_187 import create_reports
from test_trendline_viewer_188 import ledger, quote_fixture
from test_trendline_viewer_189 import bounce_files


class SavedReplayExportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        temporary = tempfile.TemporaryDirectory()
        cls.addClassCleanup(temporary.cleanup)
        cls.root = Path(temporary.name)
        cls.b_descriptor, hours, through = bounce_files(cls.root)
        cls.b_saved = cls.root / "b-saved"
        create_reports(cls.b_descriptor, hours, cls.b_saved, "--profile", breaks.BNC_PROFILE, "--as-of", str(through))
        cls.b_export = cls.root / "b-export"
        replay_viewer.export(cls.b_descriptor, cls.b_saved, cls.b_export)

        document, cls.trigger = quote_fixture()
        cls.tape = quotes.Tape(document)
        cls.q_descriptor = cls.root / "tape.json"
        data.write_new(cls.q_descriptor, document)
        report = ledger(cls.tape, cls.trigger + 2004)
        cls.q_saved = cls.root / "q-saved"
        cls.q_saved.mkdir()
        data.write_new(cls.q_saved / "quote-ledger.json", report)
        data.write_new(cls.q_saved / "checkpoint.json", quote_replay.checkpoint(report))
        cls.q_export = cls.root / "q-export"
        replay_viewer.export(cls.q_descriptor, cls.q_saved, cls.q_export)

    def test_both_bundles_bind_exported_files_and_receipt_order(self):
        for directory, level, basis in ((self.b_export, "B", "bid_only"), (self.q_export, "Q", "mid_sync")):
            with self.subTest(level=level):
                manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
                self.assertEqual({"replay.html", "report.html", "ledger.json", "ledger.csv"}, set(manifest["files"]))
                for name, digest in manifest["files"].items():
                    self.assertEqual(digest, hashlib.sha256((directory / name).read_bytes()).hexdigest())
                ledger_data = json.loads((directory / "ledger.json").read_text(encoding="utf-8"))
                self.assertEqual((level, basis, manifest["as_of_ms"]),
                                 (ledger_data["data_level"], ledger_data["geometry_basis"], ledger_data["as_of_ms"]))
                with (directory / "ledger.csv").open(encoding="utf-8", newline="") as handle:
                    csv_rows = list(csv.DictReader(handle))
                rows = ledger_data["rows"]
                self.assertEqual(len(rows), len(csv_rows))
                sort_order = [(row["receipt_at_ms"], row["receipt_order"]) for row in rows]
                self.assertEqual(sorted(set(sort_order)), sort_order)
                for i, (record, table_row) in enumerate(zip(rows, csv_rows, strict=True), 1):
                    self.assertEqual(i, record["row_id"])
                    self.assertEqual((level, basis, str(i)), (table_row["data_level"], table_row["geometry_basis"], table_row["row_id"]))
                    for key in replay_exports.COLUMNS:
                        value = record[key]
                        expected = "" if value is None else str(value).lower() if type(value) is bool else str(value)
                        self.assertEqual(expected, table_row[key])

    def test_readable_and_machine_exports_include_loss_and_skip_with_correct_clocks(self):
        quotes_json = json.loads((self.q_export / "ledger.json").read_text(encoding="utf-8"))
        entry, exit_ = [row for row in quotes_json["rows"] if row["event"] in ("ENTRY_FILL", "EXIT_FILL")]
        self.assertEqual((self.trigger + 3, self.trigger + 2003, self.trigger + 3),
                         (entry["effective_at_ms"], entry["receipt_at_ms"], entry["quote_source_at_ms"]))
        self.assertEqual((self.trigger + 4, self.trigger + 2004, "-37.02"),
                         (exit_["effective_at_ms"], exit_["receipt_at_ms"], exit_["net_usd"]))
        self.assertLess(entry["quote_sequence"], exit_["quote_sequence"])
        self.assertEqual(entry["setup_frame_id"], exit_["setup_frame_id"])
        quote_report = (self.q_export / "report.html").read_text(encoding="utf-8")
        for text in ("Level Q", "mid_sync", "STOP_QUOTE", "-37.02", "9962.98", "2000-01-10 02:00:02.004"):
            self.assertIn(text, quote_report)
        bars_json = json.loads((self.b_export / "ledger.json").read_text(encoding="utf-8"))
        reservation, skip = [row for row in bars_json["rows"] if row["kind"] == "ADMISSION"]
        self.assertEqual(("RESERVED", "STOP_ALREADY_CROSSED"), (reservation["status"], skip["reason"]))
        self.assertGreater(skip["receipt_at_ms"], reservation["receipt_at_ms"])
        bar_report = (self.b_export / "report.html").read_text(encoding="utf-8")
        for text in ("Level B", "bid_only", "STOP_ALREADY_CROSSED", "CONTACT_TOO_CLOSE", "No closed trades"):
            self.assertIn(text, bar_report)

    def test_held_prefix_exports_liability_without_later_trade(self):
        through = self.trigger + 2003
        view = replay_viewer.quote_viewer_data(self.tape, ledger(self.tape, through))
        projected = replay_exports.receipt_ledger(view)
        self.assertTrue(all(row["receipt_at_ms"] <= through for row in projected["rows"]))
        self.assertFalse(any(row["event"] == "EXIT_FILL" for row in projected["rows"]))
        endpoint = projected["rows"][-1]
        self.assertEqual("OPEN", endpoint["status"])
        self.assertEqual(through, endpoint["evidence"]["open_liability"]["last_mark"]["available_at"])
        report = replay_exports.render_report(projected)
        self.assertIn("Unpaid exit commission", report)
        self.assertIn("Position held", report)
        self.assertNotIn("STOP_QUOTE", report)

    def test_partial_write_cleans_created_files_and_allows_retry(self):
        target = self.root / "retry"
        original_open = Path.open

        def fail_on_csv(path, *args, **kwargs):
            if path == target / "ledger.csv":
                raise OSError("invented write failure")
            return original_open(path, *args, **kwargs)

        with patch.object(Path, "open", fail_on_csv):
            with self.assertRaisesRegex(OSError, "invented write failure"):
                replay_viewer.export(self.b_descriptor, self.b_saved, target)
        self.assertFalse(target.exists())
        replay_viewer.export(self.b_descriptor, self.b_saved, target)
        self.assertEqual((self.b_export / "manifest.json").read_bytes(), (target / "manifest.json").read_bytes())

    def test_html_and_csv_serialize_text_safely_and_keep_signed_amounts(self):
        ledger_data = json.loads((self.q_export / "ledger.json").read_text(encoding="utf-8"))
        row = next(row for row in ledger_data["rows"] if row["event"] == "EXIT_FILL")
        row["reason"] = "=1+1"
        ledger_data["geometry_basis"] = "<audit>"
        rendered = replay_exports.render_report(ledger_data)
        self.assertIn("&lt;audit&gt;", rendered)
        self.assertNotIn("<audit>", rendered)
        rows = csv.DictReader(StringIO(replay_exports.csv_ledger(ledger_data).decode("utf-8")))
        exported = next(row for row in rows if row["event"] == "EXIT_FILL")
        self.assertEqual(("'=1+1", "-37.02"), (exported["reason"], exported["net_usd"]))
