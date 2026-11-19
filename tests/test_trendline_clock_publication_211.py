"""A causal clock model on invented source-time-only weekend quotes."""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from forex_demo_lab.elliott_sessions_146 import HOUR
from forex_demo_lab.trendline import clock_publication, data
from test_trendline_data_163 import calendar


def quote(at, bid="1.1", ask="1.1001"):
    return {"source_at": at, "bid": bid, "ask": ask}


class ClockPublicationTests(unittest.TestCase):
    def setUp(self):
        self.calendar = calendar((6, 4), (48,), partial=True)
        self.close = self.calendar["segments"][0]["end"]
        self.opening = self.calendar["segments"][2]["start"]
        self.first_child = quote(self.close - 2 * HOUR)
        self.last_child = quote(self.close - HOUR)

    def source(self, *rows, delay=0):
        return {"kind": clock_publication.KIND, "calendar": self.calendar, "h4_end": self.close,
                "assumed_delivery_delay_ms": delay, "quotes": list(rows)}

    def test_clock_releases_shortened_bar_during_closure(self):
        source = self.source(self.first_child, self.last_child)
        due = self.close + 2000
        pending = clock_publication.audit(source, as_of=due - 1)
        complete = clock_publication.audit(source, as_of=due)
        self.assertIsNone(pending["h4"]["modeled_available_at"])
        self.assertEqual(due, complete["h4"]["modeled_available_at"])
        self.assertEqual([], complete["h4"]["unpublished_children"])
        self.assertIsNone(complete["modeled_opening_evidence"])
        self.assertFalse(complete["qualified_receipt_evidence"])

    def test_longer_delivery_bound_includes_trailing_quotes_and_rejects_future_revisions(self):
        due = self.close + 5000
        base = (self.first_child, self.last_child)
        trailing = quote(self.close - 1, "1.2", "1.2001")
        future = (quote(self.close, "1.3", "1.3001"), quote(self.opening, "1.4", "1.4001"))
        self.assertIsNone(clock_publication.audit(self.source(*base, trailing, delay=5000),
                                                  as_of=due - 1)["h4"]["modeled_available_at"])
        complete = clock_publication.audit(self.source(*base, trailing, delay=5000), as_of=due)
        without = clock_publication.audit(self.source(*base, delay=5000), as_of=due)
        self.assertEqual(5000, complete["effective_finalization_delay_ms"])
        self.assertEqual(due, complete["h4"]["modeled_available_at"])
        self.assertNotEqual(complete["h4"]["midpoint_publication_sha256"],
                            without["h4"]["midpoint_publication_sha256"])
        after = clock_publication.audit(self.source(*base, trailing, *future, delay=5000),
                                        as_of=self.opening + 5000)
        self.assertEqual(complete["h4"], after["h4"])

    def test_missing_child_cannot_be_replaced_with_a_closure_or_sunday_quote(self):
        source = self.source(self.first_child, quote(self.close), quote(self.opening))
        result = clock_publication.audit(source, as_of=self.opening)
        self.assertIsNone(result["h4"]["modeled_available_at"])
        self.assertEqual([self.close - HOUR], result["h4"]["unpublished_children"])
        self.assertEqual("BOUNDARY_QUOTE_OBSERVED", result["modeled_opening_evidence"]["status"])

    def test_an_early_h4_does_not_supply_an_opening_for_a_late_sunday_quote(self):
        base = (self.first_child, self.last_child)
        late_source = clock_publication.audit(self.source(*base, quote(self.opening + 1)), as_of=self.opening + 1)
        late_receipt = clock_publication.audit(self.source(*base, quote(self.opening), delay=1), as_of=self.opening + 1)
        self.assertEqual("FIRST_SOURCE_AFTER_OPEN", late_source["modeled_opening_evidence"]["status"])
        self.assertEqual("BOUNDARY_QUOTE_RECEIVED_AFTER_OPEN", late_receipt["modeled_opening_evidence"]["status"])
        for result in (late_source, late_receipt):
            self.assertLess(result["h4"]["modeled_available_at"], self.opening)
            self.assertNotIn("bid", result["modeled_opening_evidence"])

    def test_rejects_market_kind_explicit_receipts_and_unsorted_source_rows(self):
        for source in (
            {**self.source(self.first_child), "kind": "market_archive"},
            self.source({**self.first_child, "received_at": self.close}),
            self.source(self.last_child, self.first_child),
        ):
            with self.assertRaises(ValueError):
                clock_publication.audit(source, as_of=self.opening)

    def test_cli_binds_the_named_input(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.json"
            report = Path(directory) / "report.json"
            value = self.source(self.first_child, self.last_child)
            source.write_text(json.dumps(value), encoding="utf-8")
            subprocess.run([sys.executable, "-m", clock_publication.__name__, str(source), str(report),
                            "--as-of", str(self.opening)], check=True, capture_output=True)
            result = json.loads(report.read_bytes())
            self.assertEqual(data.read_json(source)[1], result.pop("input_sha256"))
            self.assertEqual(clock_publication.audit(value, as_of=self.opening), result)
