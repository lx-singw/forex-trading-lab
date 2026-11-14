import ast
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from forex_demo_lab.quote_recorder_102 import Policy, Quote, Recorder, invented_events


class QuoteRecorder102Tests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "quotes.sqlite"
        self.at = datetime(2030, 1, 7, tzinfo=timezone.utc)

    def q(self, identity=1, ms=0, bid="1.1000", ask="1.1002"):
        return Quote(identity, self.at + timedelta(milliseconds=ms), Decimal(bid), Decimal(ask))

    def recorder(self, **policy):
        result = Recorder.create(self.path, Policy(**policy))
        self.addCleanup(result.close)
        return result

    def test_preserves_source_and_normalized_receipt_separately(self):
        r = self.recorder()
        received = (self.at + timedelta(milliseconds=50)).astimezone(timezone(timedelta(hours=2)))
        self.assertEqual(r.record(self.q(), received).status, "accepted")
        row = r.events()[0]
        self.assertEqual(row["quote"]["source_at"], self.at.isoformat(timespec="microseconds"))
        self.assertEqual(row["received_at"], (self.at + timedelta(milliseconds=50)).isoformat(timespec="microseconds"))

    def test_duplicate_across_restart_does_not_become_second_accepted_quote(self):
        with self.recorder() as r:
            r.record(self.q(), self.at)
        with Recorder.resume(self.path) as r:
            result = r.record(self.q(), self.at + timedelta(milliseconds=1))
            self.assertEqual(result.status, "duplicate")
            self.assertEqual(r.summary()["statuses"]["accepted"], 1)

    def test_conflicting_duplicate_preserves_original(self):
        r = self.recorder()
        r.record(self.q(), self.at)
        result = r.record(self.q(bid="1.1001"), self.at)
        self.assertIn("conflicting_duplicate", result.flags)
        self.assertEqual(result.status, "rejected")
        self.assertEqual(r.events()[0]["quote"]["bid"], "1.1")

    def test_equal_source_timestamp_distinct_ids_are_not_dropped(self):
        r = self.recorder()
        r.record(self.q(), self.at)
        self.assertEqual(r.record(self.q(2), self.at).status, "accepted")
        self.assertEqual(r.record(self.q(3, bid="1.1001"), self.at).status, "accepted")

    def test_decimal_and_offset_normalization_preserves_duplicate_identity(self):
        r = self.recorder()
        r.record(self.q(), self.at)
        q = Quote(1, self.at.astimezone(timezone(timedelta(hours=2))), Decimal("1.10"), Decimal("1.100200"))
        self.assertEqual(r.record(q, self.at).status, "duplicate")

    def test_source_time_reversal_is_rejected_without_poisoning_state(self):
        r = self.recorder()
        r.record(self.q(1, 500), self.at + timedelta(milliseconds=500))
        self.assertIn("source_clock_backwards", r.record(self.q(2, 400), self.at + timedelta(milliseconds=600)).flags)
        self.assertEqual(r.record(self.q(2, 700), self.at + timedelta(milliseconds=700)).status, "accepted")

    def test_receipt_reversal_is_rejected_and_watermark_survives_restart(self):
        with self.recorder() as r:
            r.record(self.q(), self.at + timedelta(milliseconds=100))
            self.assertIn("receipt_clock_backwards", r.record(self.q(2), self.at).flags)
        with Recorder.resume(self.path) as r:
            self.assertIn("receipt_clock_backwards", r.record(self.q(3), self.at + timedelta(milliseconds=50)).flags)

    def test_stale_boundary_and_old_duplicate_are_auditable(self):
        r = self.recorder(max_age_ms=100)
        self.assertEqual(r.record(self.q(), self.at + timedelta(milliseconds=100)).status, "accepted")
        result = r.record(self.q(2), self.at + timedelta(milliseconds=101))
        self.assertEqual(result.status, "rejected")
        self.assertIn("stale_quote", result.flags)
        replay = r.record(self.q(), self.at + timedelta(milliseconds=102))
        self.assertEqual(replay.status, "duplicate")
        self.assertIn("stale_quote", replay.flags)

    def test_future_source_time_cannot_enter_accepted_stream(self):
        r = self.recorder()
        result = r.record(self.q(1, 1), self.at)
        self.assertIn("future_source_time", result.flags)
        self.assertEqual(r.summary()["statuses"]["accepted"], 0)

    def test_missing_is_explicit_and_never_filled_from_previous_quote(self):
        r = self.recorder()
        r.record(self.q(), self.at)
        self.assertEqual(r.record(None, self.at).status, "missing")
        self.assertIsNone(r.events()[-1]["quote"])

    def test_gaps_remain_diagnostics_and_do_not_generate_ticks(self):
        r = self.recorder()
        r.record(self.q(), self.at)
        result = r.record(self.q(2, 5000), self.at + timedelta(milliseconds=5000))
        self.assertEqual(result.status, "accepted")
        self.assertEqual(set(result.flags), {"source_gap", "receipt_gap"})
        self.assertEqual(len(r.events()), 2)

    def test_gap_threshold_is_strict(self):
        r = self.recorder()
        r.record(self.q(), self.at)
        self.assertEqual(r.record(self.q(2, 2000), self.at + timedelta(milliseconds=2000)).flags, ())

    def test_invalid_prices_never_saved(self):
        r = self.recorder()
        for i, price in enumerate((Decimal("NaN"), Decimal("Infinity"), Decimal("0"), Decimal("-1"), 1.1)):
            with self.subTest(price=repr(price)):
                result = r.record(Quote(i + 1, self.at, price, Decimal("1.2")), self.at)
                self.assertEqual(result.status, "invalid")
                self.assertIsNone(r.events()[-1]["quote"])
        self.assertEqual(r.summary()["statuses"]["accepted"], 0)

    def test_crossed_quotes_are_invalid(self):
        r = self.recorder()
        self.assertIn("invalid_prices", r.record(self.q(bid="1.3", ask="1.2"), self.at).flags)

    def test_invalid_timestamp_identity_and_arbitrary_payload_not_logged(self):
        r = self.recorder()
        payloads = [Quote(True, self.at, Decimal("1"), Decimal("2")),
                    Quote(1, self.at.replace(tzinfo=None), Decimal("1"), Decimal("2")),
                    {"password": "secret-should-not-be-logged", "account": "private-account"}]
        for item in payloads:
            self.assertEqual(r.record(item, self.at).status, "invalid")
        saved = json.dumps(r.events())
        self.assertNotIn("secret-should-not-be-logged", saved)
        self.assertNotIn("private-account", saved)

    def test_naive_receipt_rejected_without_partial_event(self):
        r = self.recorder()
        with self.assertRaises(ValueError):
            r.record(self.q(), self.at.replace(tzinfo=None))
        self.assertEqual(r.events(), ())

    def test_restart_matches_uninterrupted_journal_exactly(self):
        events = invented_events()
        r = self.recorder()
        for quote, receipt in events:
            r.record(quote, receipt)
        uninterrupted = r.events()
        other = Path(self.directory.name) / "restart.sqlite"
        with Recorder.create(other) as resumed:
            for quote, receipt in events[:7]:
                resumed.record(quote, receipt)
        with Recorder.resume(other) as resumed:
            for quote, receipt in events[7:]:
                resumed.record(quote, receipt)
            self.assertEqual(resumed.events(), uninterrupted)

    def test_insert_interruption_rolls_back_event_and_head(self):
        r = self.recorder()
        insert = r._insert
        def interrupted(body):
            insert(body)
            raise KeyboardInterrupt()
        with patch.object(r, "_insert", side_effect=interrupted), self.assertRaises(KeyboardInterrupt):
            r.record(self.q(), self.at)
        r.close()
        with Recorder.resume(self.path) as resumed:
            self.assertEqual(resumed.events(), ())
            self.assertEqual(resumed.record(self.q(), self.at).sequence, 1)

    def test_uncommitted_transaction_is_rolled_back_on_close(self):
        r = self.recorder()
        r.record(self.q(), self.at)
        r._db.execute("BEGIN IMMEDIATE")
        r._db.execute("DELETE FROM events")
        r.close()
        with Recorder.resume(self.path) as resumed:
            self.assertEqual(len(resumed.events()), 1)

    def test_multiple_instances_refresh_committed_state(self):
        r = self.recorder()
        with Recorder.resume(self.path) as other:
            r.record(self.q(), self.at)
            self.assertEqual(other.record(self.q(), self.at).status, "duplicate")
            self.assertEqual(r.record(self.q(2), self.at).sequence, 3)

    def test_writer_lock_rejects_cleanly_and_retry_is_consistent(self):
        r = self.recorder()
        with Recorder.resume(self.path) as other:
            r._db.execute("BEGIN IMMEDIATE")
            with self.assertRaises(sqlite3.OperationalError):
                other.record(self.q(), self.at)
            r._db.execute("ROLLBACK")
            self.assertEqual(other.record(self.q(), self.at).sequence, 1)

    def test_exclusive_creation_never_overwrites(self):
        self.path.write_bytes(b"existing-content")
        with self.assertRaises(FileExistsError):
            Recorder.create(self.path)
        self.assertEqual(self.path.read_bytes(), b"existing-content")

    def test_resume_missing_file_does_not_create_it(self):
        with self.assertRaises(ValueError):
            Recorder.resume(self.path)
        self.assertFalse(self.path.exists())

    def test_event_limit_survives_resume(self):
        with self.recorder(max_events=1) as r:
            r.record(self.q(), self.at)
        with Recorder.resume(self.path) as r:
            with self.assertRaises(ValueError):
                r.record(self.q(2), self.at)
            self.assertEqual(len(r.events()), 1)

    def test_policy_limits_reject_boolean_zero_and_excessive_values(self):
        for field, value in (("max_age_ms", True), ("gap_ms", 0), ("max_events", 10001)):
            with self.subTest(field=field), self.assertRaises(ValueError):
                Policy(**{field: value})

    def test_mutated_policy_rejected_before_file_creation(self):
        policy = Policy()
        object.__setattr__(policy, "max_events", -1)
        with self.assertRaises(ValueError):
            Recorder.create(self.path, policy)
        self.assertFalse(self.path.exists())

    def test_oversized_file_rejected_before_sqlite_read(self):
        with self.path.open("xb") as stream:
            stream.truncate(16 * 1024 * 1024 + 1)
        with self.assertRaises(ValueError):
            Recorder.resume(self.path)

    def test_metadata_relabeling_rejected(self):
        r = self.recorder()
        metadata = json.loads(r._db.execute("SELECT value FROM metadata").fetchone()[0])
        metadata["source"] = "market-source"
        r._db.execute("UPDATE metadata SET value=?", (json.dumps(metadata),))
        r.close()
        with self.assertRaises(ValueError):
            Recorder.resume(self.path)

    def test_corrupt_payload_rejected(self):
        r = self.recorder()
        r.record(self.q(), self.at)
        r._db.execute("UPDATE events SET payload='{}'")
        r.close()
        with self.assertRaises(ValueError):
            Recorder.resume(self.path)

    def test_tail_deletion_detected_by_transactional_head(self):
        r = self.recorder()
        r.record(self.q(), self.at)
        r._db.execute("DELETE FROM events")
        r.close()
        with self.assertRaises(ValueError):
            Recorder.resume(self.path)

    def test_rehashed_wrong_quality_decision_still_rejected(self):
        r = self.recorder()
        r.record(self.q(), self.at)
        body = r.events()[0]
        body["status"] = "duplicate"
        payload = json.dumps(body, sort_keys=True, separators=(",", ":"))
        digest = hashlib.sha256(payload.encode()).hexdigest()
        r._db.execute("UPDATE events SET payload=?, sha256=?", (payload, digest))
        r._db.execute("UPDATE head SET sha256=?", (digest,))
        r.close()
        with self.assertRaises(ValueError):
            Recorder.resume(self.path)

    def test_unexpected_trigger_is_rejected_before_append(self):
        r = self.recorder()
        r._db.execute("CREATE TRIGGER unexpected AFTER INSERT ON events BEGIN DELETE FROM head; END")
        with self.assertRaises(ValueError):
            r.record(self.q(), self.at)
        self.assertEqual(r._db.execute("SELECT count(*) FROM events").fetchone(), (0,))

    def test_no_eligibility_or_external_capability_in_prototype(self):
        r = self.recorder()
        self.assertFalse(r.summary()["market_data_qualified"])
        self.assertFalse(r.summary()["orders_available"])
        module = Path(__file__).resolve().parents[1] / "src/forex_demo_lab/quote_recorder_102.py"
        imports = {node.module.split(".")[0] for node in ast.walk(ast.parse(module.read_text()))
                   if isinstance(node, ast.ImportFrom)}
        imports.update(alias.name.split(".")[0] for node in ast.walk(ast.parse(module.read_text()))
                       if isinstance(node, ast.Import) for alias in node.names)
        self.assertLessEqual(imports, {"dataclasses", "datetime", "decimal", "hashlib", "json", "pathlib", "sqlite3"})


if __name__ == "__main__":
    unittest.main()
