"""Causal H1 opening diagnostics and integration with the Level B entry rule."""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from forex_demo_lab.trendline import opening_evidence as evidence, quotes
from test_trendline_data_163 import calendar, descriptor
from test_trendline_fills_164 import setup
from test_trendline_quotes_185 import document, row


HOUR = 3_600_000


class OpeningEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.calendar = calendar((8, 4), (48,), partial=True)
        self.source = descriptor(self.calendar)
        self.start = self.calendar["scope"]["start"]
        self.open = self.start + 4 * HOUR

    def tape(self, *rows):
        return quotes.Tape(document(self.source, rows))

    def at_open(self, tape, as_of):
        return evidence.inspect(tape, as_of=as_of)[4]

    def test_exact_boundary_uses_first_pair_in_feed_order(self):
        first = row(self.open, "1.1004", "1.10052")
        later_pair = row(self.open, "1.1001", "1.1002")
        opening = self.at_open(self.tape(first, later_pair), self.open)
        self.assertEqual({
            "start": self.open, "end": self.open + HOUR, "status": "BOUNDARY_QUOTE_OBSERVED",
            "first_source_at": self.open, "first_received_at": self.open, "first_quote_sequence": 1,
            "bid": "1.1004", "spread_pips": "1.2",
        }, opening.record())
        self.assertEqual(opening.record(), self.at_open(self.tape(first), self.open).record())

    def test_opening_assumption_preserves_exact_small_decimal_values(self):
        tape = self.tape(row(self.open, "0.000000000001", "0.000000000002"))
        assumption = self.at_open(tape, self.open).assumption(opening_ordinal=2).record()
        self.assertEqual("0.000000000001", assumption["bid"])
        self.assertEqual("0.00000001", assumption["spread_pips"])

    def test_late_receipt_is_invisible_at_open_and_never_backdated(self):
        tape = self.tape(row(self.open, "1.1004", "1.10052", self.open + 5))
        before = self.at_open(tape, self.open)
        after = self.at_open(tape, self.open + 5)
        self.assertEqual("NO_QUOTE_OBSERVED", before.status)
        self.assertEqual("BOUNDARY_QUOTE_RECEIVED_AFTER_OPEN", after.status)
        self.assertEqual(self.open, after.record()["first_source_at"])
        self.assertEqual(self.open + 5, after.record()["first_received_at"])
        for value in (before, after):
            self.assertIsNone(value.assumption(opening_ordinal=1))
            self.assertNotIn("bid", value.record())

    def test_late_source_can_form_geometry_without_an_opening_assumption(self):
        tape = self.tape(row(self.open + 1, "1.1004", "1.10052"))
        as_of = self.open + HOUR + tape.calendar.delay
        opening = self.at_open(tape, as_of)
        self.assertEqual("FIRST_SOURCE_AFTER_OPEN", opening.status)
        self.assertIsNone(opening.assumption(opening_ordinal=1))
        self.assertNotIn("spread_pips", opening.record())
        [bar] = tape.publications(tuple(tape.prefix(as_of)), as_of)
        self.assertEqual(self.open, bar.start)

    def test_empty_open_and_closure_never_borrow_nearby_quotes(self):
        closure = self.start + 8 * HOUR
        tape = self.tape(row(self.open - 1, "1.1", "1.1001", self.open),
                         row(self.open + HOUR, "1.1", "1.1001"),
                         row(closure, "1.1", "1.1001"))
        self.assertEqual(4, len(evidence.inspect(tape, as_of=self.open - 1)))
        rows = evidence.inspect(tape, as_of=closure + HOUR)
        self.assertEqual(8, len(rows))
        self.assertEqual("NO_QUOTE_OBSERVED", rows[4].status)
        self.assertEqual("BOUNDARY_QUOTE_OBSERVED", rows[5].status)
        model, request, _ = setup(source=self.source)
        for candidate in (rows[4].assumption(opening_ordinal=1), rows[5].assumption(opening_ordinal=1)):
            self.assertEqual("MISSING_ENTRY_BAR", model.entry(request, candidate)["reason"])

    def test_price_model_checks_declared_cross_stream_order(self):
        tape = self.tape(row(self.open, "1.1004", "1.10052"))
        value = self.at_open(tape, self.open)
        opening = value.assumption(opening_ordinal=2)
        model, request, _ = setup(source=self.source)
        result = model.entry(request, opening)
        self.assertEqual(("FILLED", "1.10054"), (result["status"], result["price"]))
        for ordinal in (2, 3):
            request["decision_at"]["ordinal"] = ordinal
            self.assertEqual("UNRESOLVED_OPEN_ORDER", model.entry(request, opening)["reason"])
        request["decision_at"] = {"time": self.open + 1, "ordinal": 0}
        self.assertEqual("LATE_DECISION", model.entry(request, opening)["reason"])

    def test_cli_writes_invented_report_and_rejects_validation(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "tape.json"
            report = Path(directory) / "report.json"
            value = document(self.source, [row(self.open, "1.1004", "1.10052")])
            source.write_text(json.dumps(value), encoding="utf-8")
            command = [sys.executable, "-m", evidence.__name__, str(source), str(report),
                       "--as-of", str(self.open)]
            subprocess.run(command, check=True, capture_output=True)
            result = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual("invented_level_b_opening_evidence", result["kind"])
            self.assertEqual(5, result["scheduled_opens_reached"])
            self.assertEqual({"NO_QUOTE_OBSERVED": 4, "BOUNDARY_QUOTE_OBSERVED": 1}, result["status_counts"])
            report.unlink()
            source.write_text(json.dumps({**value, "partition": "validation"}), encoding="utf-8")
            rejected = subprocess.run(command, capture_output=True, text=True)
            self.assertNotEqual(0, rejected.returncode)
            self.assertIn("validation unlock required", rejected.stderr)
            self.assertFalse(report.exists())
