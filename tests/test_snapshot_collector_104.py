"""Meaningful failure, persistence and chronology tests with invented facts."""

import ast
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from forex_demo_lab.snapshot_collector_104 import (
    Clock, Collector, Frame, Guard, Journal, Policy, ReplayClock, ReplaySource, Tick, connect_broker,
)


class SnapshotCollector104Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "invented.sqlite"
        self.start = datetime(2030, 1, 7, tzinfo=timezone.utc)
        self.raw = int(self.start.timestamp() * 1000) + 10800000

    def clock(self, ms, mono_ms=None):
        return Clock(self.start + timedelta(milliseconds=ms), int((ms if mono_ms is None else mono_ms) * 1000000))

    def tick(self, offset=0, **kw):
        return replace(Tick((self.raw + offset) // 1000, self.raw + offset, 1.1, 1.1002), **kw)

    def frame(self, tick="default", before=None, after=None, **kw):
        return Frame(Guard() if before is None else before, self.tick() if tick == "default" else tick,
                     Guard() if after is None else after, **kw)

    def journal(self, **policy):
        j = Journal.create(self.path, Policy(**policy))
        self.addCleanup(j.close)
        return j

    def collector(self, frames=None, readings=None, **policy):
        j = self.journal(**policy)
        s = ReplaySource([self.frame()] if frames is None else frames)
        c = Collector(j, s, ReplayClock([self.clock(x) for x in [0, 100, 110, 120]] if readings is None else readings))
        return j, s, c

    def test_broker_entry_always_rejects(self):
        with self.assertRaisesRegex(ValueError, "broker_entry_disabled"):
            connect_broker()

    def test_external_adapter_rejected_before_any_callback(self):
        class External:
            def __getattr__(self, name):
                raise AssertionError("must not inspect adapter")
        j = self.journal()
        clock = ReplayClock([self.clock(0)])
        with self.assertRaises(ValueError):
            Collector(j, External(), clock)
        self.assertEqual(clock.calls, 0)
        self.assertEqual(j.events(), ())

    def test_subclass_source_is_not_broker_escape(self):
        class External(ReplaySource):
            pass
        j = self.journal()
        with self.assertRaises(ValueError):
            Collector(j, External([]), ReplayClock([]))

    def test_raw_labels_receipts_native_bits_and_guard_time_separate(self):
        j, source, c = self.collector()
        event = c.poll()
        self.assertEqual(source.calls, ["before", "read", "after"])
        self.assertEqual(event["data"]["tick"]["time_msc"], self.raw)
        self.assertEqual(event["data"]["received_after"]["utc"], self.clock(110).utc.isoformat(timespec="microseconds"))
        self.assertEqual(event["data"]["guard_completed"]["utc"], self.clock(120).utc.isoformat(timespec="microseconds"))
        self.assertEqual(event["data"]["tick"]["bid"], {"hex": (1.1).hex(), "decimal_text": "1.1"})
        self.assertIsNone(event["derived"]["source_age_ms"])
        self.assertEqual(j.summary()["attempts"], 1)

    def test_aware_clock_offset_normalized(self):
        offset = timezone(timedelta(hours=2))
        readings = [replace(self.clock(x), utc=self.clock(x).utc.astimezone(offset)) for x in [0, 100, 110, 120]]
        _, _, c = self.collector(readings=readings)
        self.assertEqual(c.poll()["data"]["received_before"]["utc"], self.clock(100).utc.isoformat(timespec="microseconds"))

    def test_real_contest_unknown_bool_modes_reject_without_quote(self):
        j = self.journal()
        for mode in [1, 2, 3, -1, True, False, None, "0"]:
            # A fresh file preserves each rejection, never resetting a stopped journal.
            path = Path(self.temp.name) / ("mode-" + str(type(mode).__name__) + "-" + str(mode) + ".sqlite")
            with Journal.create(path) as other:
                source = ReplaySource([self.frame(before=Guard(trade_mode=mode))])
                c = Collector(other, source, ReplayClock([self.clock(0)]))
                self.assertEqual(c.poll()["derived"]["reason"], "account_mode_rejected")
                self.assertEqual(source.calls, ["before"])
                self.assertTrue(c.stopped)
        self.assertEqual(j.events(), ())

    def test_before_identity_change_blocks_second_quote(self):
        frames = [self.frame(), self.frame(before=Guard(identity=b"SECRET-private-new-role"))]
        _, source, c = self.collector(frames, [self.clock(x) for x in [0, 100, 110, 120]])
        c.poll()
        event = c.poll()
        self.assertEqual(event["derived"]["reason"], "account_changed")
        self.assertEqual(source.calls.count("read"), 1)

    def test_after_identity_change_discards_quote_and_latches(self):
        j, source, c = self.collector([self.frame(after=Guard(identity=b"SECRET-private-key"))])
        event = c.poll()
        self.assertEqual(event["derived"]["reason"], "account_changed")
        self.assertIsNone(event["data"]["tick"])
        calls = source.calls[:]
        with self.assertRaises(ValueError):
            c.poll()
        self.assertEqual(source.calls, calls)
        self.assertNotIn("SECRET", json.dumps(j.events()))
        self.assertNotIn("SECRET", repr(Guard(identity=b"SECRET")))

    def test_after_real_mode_discards_even_valid_quote(self):
        _, _, c = self.collector([self.frame(after=Guard(trade_mode=2))])
        event = c.poll()
        self.assertIsNone(event["data"]["tick"])
        self.assertEqual(event["derived"]["reason"], "account_mode_rejected")

    def test_terminal_exit_after_read_is_persisted_stop(self):
        j, _, c = self.collector([self.frame(after=Guard(connected=False))])
        self.assertEqual(c.poll()["derived"]["reason"], "disconnected")
        self.assertEqual(j.summary()["stop_reason"], "disconnected")

    def test_algo_enabled_before_read_has_no_quote_call(self):
        _, source, c = self.collector([self.frame(before=Guard(algo_trading=True))], [self.clock(0)])
        self.assertEqual(c.poll()["derived"]["reason"], "algo_enabled")
        self.assertNotIn("read", source.calls)

    def test_wrong_instrument_or_visibility_rejects(self):
        for field, value in [("currency", "EUR"), ("symbol", "EURUSD.x"), ("visible", 1), ("base", "USD"), ("quote", "EUR")]:
            with self.subTest(field=field), Journal.create(Path(self.temp.name) / (field + ".sqlite")) as j:
                source = ReplaySource([self.frame(before=replace(Guard(), **{field: value}))])
                c = Collector(j, source, ReplayClock([self.clock(0)]))
                self.assertEqual(c.poll()["derived"]["reason"], "instrument_rejected")
                self.assertNotIn("read", source.calls)

    def test_guard_payload_and_arbitrary_quote_never_exported(self):
        _, _, c = self.collector([Frame({"password": "SECRET"}, {"account": "SECRET"}, Guard())], [self.clock(0)])
        event = c.poll()
        self.assertEqual(event["derived"]["reason"], "guard_unavailable")
        self.assertNotIn("SECRET", json.dumps(event))

    def test_read_failure_still_runs_after_guard_without_exception_text(self):
        _, source, c = self.collector([self.frame(error=RuntimeError("SECRET-credential"))])
        event = c.poll()
        self.assertEqual(source.calls, ["before", "read", "after"])
        self.assertEqual(event["derived"]["reason"], "read_failure")
        self.assertNotIn("SECRET", json.dumps(event))

    def test_missing_quote_is_event_not_carry_forward(self):
        j, _, c = self.collector([self.frame(), self.frame(tick=None)], [self.clock(x) for x in [0, 100, 110, 120, 200, 210, 220]])
        c.poll()
        event = c.poll()
        self.assertEqual(event["derived"]["status"], "missing")
        self.assertIsNone(event["data"]["tick"])
        self.assertEqual(j.summary()["statuses"]["observed_model"], 1)

    def test_crossed_nan_infinite_nonpositive_bool_and_float_clock_reject(self):
        bad = [self.tick(bid=1.2), self.tick(bid=float("nan")), self.tick(ask=float("inf")),
               self.tick(bid=0.0), self.tick(bid=-1.0), self.tick(bid=True), self.tick(time_msc=float(self.raw)),
               self.tick(flags=True), self.tick(volume=-1), self.tick(time_s=0)]
        for i, tick in enumerate(bad):
            with self.subTest(i=i), Journal.create(Path(self.temp.name) / (str(i) + ".sqlite")) as j:
                c = Collector(j, ReplaySource([self.frame(tick=tick)]), ReplayClock([self.clock(x) for x in [0, 100, 110, 120]]))
                event = c.poll()
                self.assertEqual(event["derived"]["status"], "invalid")
                self.assertIsNone(event["data"]["tick"])

    def test_repeated_snapshots_retained_with_duration(self):
        j, _, c = self.collector([self.frame(), self.frame()], [self.clock(x) for x in [0, 100, 110, 120, 200, 210, 220]])
        c.poll()
        event = c.poll()
        self.assertIn("repeated_snapshot", event["derived"]["flags"])
        self.assertEqual(event["derived"]["repeated_snapshot_ms"], 100.0)
        self.assertEqual(j.summary()["statuses"]["observed_model"], 2)

    def test_same_source_time_changed_snapshot_retained(self):
        j, _, c = self.collector([self.frame(), self.frame(tick=self.tick(bid=1.1001))], [self.clock(x) for x in [0, 100, 110, 120, 200, 210, 220]])
        c.poll()
        event = c.poll()
        self.assertIn("same_time_changed_snapshot", event["derived"]["flags"])
        self.assertEqual(j.summary()["statuses"]["observed_model"], 2)

    def test_unknown_flags_and_revision_are_not_masked_or_overwritten(self):
        j, _, c = self.collector([self.frame(tick=self.tick(flags=1026)), self.frame(tick=self.tick(flags=1154))],
                                  [self.clock(x) for x in [0, 100, 110, 120, 200, 210, 220]])
        first = c.poll()
        second = c.poll()
        self.assertEqual(first["data"]["tick"]["flags"], 1026)
        self.assertEqual(second["data"]["tick"]["flags"], 1154)
        self.assertIn("unknown_flags_preserved", second["derived"]["flags"])
        self.assertEqual(j.events()[2], first)

    def test_raw_clock_backwards_diagnostic_preserves_receipt_order(self):
        _, _, c = self.collector([self.frame(), self.frame(tick=self.tick(-1000))], [self.clock(x) for x in [0, 100, 110, 120, 200, 210, 220]])
        c.poll()
        event = c.poll()
        self.assertIn("raw_source_clock_backwards", event["derived"]["flags"])
        self.assertEqual(event["derived"]["status"], "observed_model")
        self.assertIsNone(event["derived"]["source_age_ms"])

    def test_source_and_receipt_gap_flags_do_not_create_ticks(self):
        j, _, c = self.collector([self.frame(), self.frame(tick=self.tick(5000))], [self.clock(x) for x in [0, 100, 110, 120, 5000, 5010, 5020]])
        c.poll()
        event = c.poll()
        self.assertTrue({"raw_source_gap", "receipt_gap"} <= set(event["derived"]["flags"]))
        self.assertEqual(j.summary()["attempts"], 2)

    def test_before_receipt_reversal_stops_without_second_read(self):
        _, source, c = self.collector([self.frame(), self.frame()], [self.clock(x) for x in [0, 100, 110, 120, 119]])
        c.poll()
        self.assertEqual(c.poll()["derived"]["reason"], "receipt_clock_reversed")
        self.assertEqual(source.calls.count("read"), 1)

    def test_monotonic_reversal_stops_even_wall_clock_forward(self):
        _, _, c = self.collector(readings=[self.clock(0), self.clock(100), self.clock(110, 99), self.clock(120)])
        event = c.poll()
        self.assertEqual(event["derived"]["reason"], "receipt_clock_reversed")
        self.assertIsNone(event["data"]["tick"])

    def test_wall_clock_jump_stops_and_discards_read(self):
        _, _, c = self.collector(readings=[self.clock(0), self.clock(100), self.clock(2000, 110), self.clock(2010, 120)])
        self.assertEqual(c.poll()["derived"]["reason"], "receipt_clock_jump")

    def test_naive_or_boolean_monotonic_clock_rejects_before_read(self):
        for i, reading in enumerate([Clock(self.start.replace(tzinfo=None), 0), Clock(self.start, True), None]):
            with self.subTest(i=i), Journal.create(Path(self.temp.name) / (str(i) + ".sqlite")) as j:
                source = ReplaySource([self.frame()])
                c = Collector(j, source, ReplayClock([self.clock(0), reading]))
                self.assertEqual(c.poll()["derived"]["reason"], "invalid_receipt_clock")
                self.assertNotIn("read", source.calls)

    def test_after_clock_failure_still_queries_after_guard(self):
        _, source, c = self.collector(readings=[self.clock(0), self.clock(100), None, self.clock(120)])
        self.assertEqual(c.poll()["derived"]["reason"], "invalid_receipt_clock")
        self.assertEqual(source.calls, ["before", "read", "after"])

    def test_deadline_before_read_rejects_at_exact_bound(self):
        _, source, c = self.collector(readings=[self.clock(0), self.clock(100)], max_session_ms=100)
        self.assertEqual(c.poll()["derived"]["reason"], "session_deadline_exhausted")
        self.assertNotIn("read", source.calls)

    def test_late_return_discards_but_does_not_claim_native_abort(self):
        _, source, c = self.collector(max_session_ms=115)
        event = c.poll()
        self.assertEqual(event["derived"]["reason"], "session_deadline_exhausted")
        self.assertEqual(source.calls.count("read"), 1)
        self.assertIsNone(event["data"]["tick"])

    def test_decision_only_sees_prior_committed_receipts(self):
        j, _, c = self.collector([self.frame(), self.frame(tick=self.tick(100))], [self.clock(x) for x in [0, 100, 110, 120, 130, 200, 210, 220, 230]])
        first = c.poll()
        decision = c.decision()
        second = c.poll()
        later = c.decision()
        self.assertEqual(j.visible(decision["sequence"]), (first["sequence"],))
        self.assertEqual(j.visible(later["sequence"]), (first["sequence"], second["sequence"]))

    def test_unrecorded_or_boolean_decision_cannot_read_model_view(self):
        j, _, c = self.collector()
        c.poll()
        for seq in [True, 1, 3, 999]:
            with self.assertRaises(ValueError):
                j.visible(seq)

    def test_backdated_decision_stops_instead_of_source_time_replay(self):
        _, _, c = self.collector(readings=[self.clock(x) for x in [0, 100, 110, 120, 119]])
        c.poll()
        self.assertEqual(c.decision()["derived"]["reason"], "receipt_clock_reversed")

    def test_late_history_receipt_not_visible_to_earlier_decision(self):
        j, _, c = self.collector([self.frame(), self.frame(tick=self.tick(-1000), kind="late_history_model")],
                                  [self.clock(x) for x in [0, 100, 110, 120, 130, 200, 210, 220, 230]])
        first = c.poll()
        before = c.decision()
        recovered = c.poll()
        after = c.decision()
        self.assertIn("late_history_availability", recovered["derived"]["flags"])
        self.assertEqual(j.visible(before["sequence"]), (first["sequence"],))
        self.assertEqual(j.visible(after["sequence"]), (first["sequence"], recovered["sequence"]))

    def test_restart_segments_preserve_sequence_but_do_not_subtract_monotonic(self):
        j, _, c = self.collector()
        first = c.poll()
        j.close()
        with Journal.resume(self.path) as resumed:
            source = ReplaySource([self.frame()])
            later = Collector(resumed, source, ReplayClock([self.clock(200, 0), self.clock(300, 100), self.clock(310, 110), self.clock(320, 120)]))
            event = later.poll()
            self.assertGreater(event["sequence"], first["sequence"])
            self.assertIn("restart_gap", resumed.events()[3]["derived"]["flags"])
            self.assertIn("repeated_snapshot", event["derived"]["flags"])
            self.assertIsNone(event["derived"]["repeated_snapshot_ms"])
            self.assertEqual(resumed.summary()["sessions"], 2)

    def test_restart_wall_clock_reversal_rejects_without_source_read(self):
        j, _, c = self.collector()
        c.poll()
        source = ReplaySource([self.frame()])
        with self.assertRaises(ValueError):
            Collector(j, source, ReplayClock([self.clock(119, 0)]))
        self.assertEqual(source.calls, [])

    def test_stopped_journal_cannot_restart_or_reset_latch(self):
        j, _, c = self.collector([self.frame(after=Guard(trade_mode=1))])
        c.poll()
        j.close()
        with Journal.resume(self.path) as resumed:
            source = ReplaySource([self.frame()])
            with self.assertRaises(ValueError):
                Collector(resumed, source, ReplayClock([self.clock(200, 0)]))
            self.assertEqual(source.calls, [])
            self.assertEqual(resumed.summary()["stop_reason"], "account_mode_rejected")

    def test_attempt_reservation_survives_interruption_before_read(self):
        j = self.journal()
        session = j.start_session(self.clock(0))
        attempt = j.begin_attempt(session)
        j.close()
        with Journal.resume(self.path) as resumed:
            self.assertEqual(resumed.summary()["pending_attempt"], attempt)
            with self.assertRaises(ValueError):
                Collector(resumed, ReplaySource([self.frame()]), ReplayClock([self.clock(200, 0)]))

    def test_disk_failure_after_read_leaves_pending_attempt_and_redacts_error(self):
        j, source, c = self.collector()
        original = j._insert
        def fail(body):
            if body["kind"] == "outcome":
                original(body)
                raise OSError("SECRET-private-path")
            original(body)
        with patch.object(j, "_insert", side_effect=fail), self.assertRaisesRegex(ValueError, "details_redacted") as caught:
            c.poll()
        self.assertNotIn("SECRET", str(caught.exception))
        self.assertEqual(source.calls.count("read"), 1)
        self.assertEqual(j.summary()["pending_attempt"], 2)
        self.assertEqual(len(j.events()), 2)
        with self.assertRaises(ValueError):
            c.poll()
        j.close()
        with Journal.resume(self.path) as resumed:
            self.assertEqual(resumed.summary()["pending_attempt"], 2)

    def test_interruption_rolls_back_outcome_and_persists_attempt(self):
        j, _, c = self.collector()
        original = j._insert
        def interrupt(body):
            original(body)
            if body["kind"] == "outcome":
                raise KeyboardInterrupt()
        with patch.object(j, "_insert", side_effect=interrupt), self.assertRaises(KeyboardInterrupt):
            c.poll()
        self.assertEqual(j.summary()["pending_attempt"], 2)
        self.assertFalse(j._db.in_transaction)

    def test_writer_lock_before_reservation_means_zero_quote_calls(self):
        j, source, c = self.collector()
        with Journal.resume(self.path) as other:
            other._db.execute("BEGIN IMMEDIATE")
            with self.assertRaises(ValueError):
                c.poll()
            other._db.execute("ROLLBACK")
        self.assertEqual(source.calls, [])
        self.assertIsNone(j.summary()["pending_attempt"])
        self.assertEqual(len(j.events()), 1)

    def test_global_attempt_budget_not_renewed_by_restart(self):
        j, _, c = self.collector(max_reads=1)
        c.poll()
        later_source = ReplaySource([self.frame()])
        later = Collector(j, later_source, ReplayClock([self.clock(200, 0)]))
        with self.assertRaises(ValueError):
            later.poll()
        self.assertEqual(later_source.calls, [])
        self.assertEqual(j.summary()["attempts"], 1)

    def test_event_budget_reserves_room_for_outcome_before_read(self):
        j, source, c = self.collector([self.frame(), self.frame()], [self.clock(x) for x in [0, 100, 110, 120]], max_events=4)
        c.poll()
        with self.assertRaises(ValueError):
            c.poll()
        self.assertEqual(len(j.events()), 3)
        self.assertEqual(source.calls.count("read"), 1)

    def test_two_collectors_cannot_acquire_over_pending_attempt(self):
        j, _, c = self.collector()
        j.begin_attempt(c.session)
        with Journal.resume(self.path) as other, self.assertRaises(ValueError):
            Collector(other, ReplaySource([]), ReplayClock([self.clock(200)]))

    def test_create_existing_or_resume_absent_never_overwrites_or_creates(self):
        with self.assertRaises(ValueError):
            Journal.resume(self.path)
        self.assertFalse(self.path.exists())
        self.path.write_bytes(b"unrelated")
        with self.assertRaises(FileExistsError):
            Journal.create(self.path)
        self.assertEqual(self.path.read_bytes(), b"unrelated")

    def test_mutated_policy_rejected_before_file_creation(self):
        policy = Policy()
        object.__setattr__(policy, "max_reads", True)
        with self.assertRaises(ValueError):
            Journal.create(self.path, policy)
        self.assertFalse(self.path.exists())

    def test_policy_arbitrary_extra_fields_never_enter_metadata(self):
        policy = Policy()
        object.__setattr__(policy, "private_extra", "SECRET")
        with Journal.create(self.path, policy) as j:
            metadata = j._db.execute("SELECT value FROM metadata").fetchone()[0]
            self.assertNotIn("SECRET", metadata)
            self.assertNotIn("private_extra", metadata)

    def test_policy_bounds_reject_bool_zero_and_excess(self):
        for key, value in [("max_reads", 0), ("max_reads", 1001), ("max_events", 3),
                           ("max_events", 10001), ("max_session_ms", True), ("max_session_ms", 60001),
                           ("gap_ms", 0), ("jump_tolerance_ms", 1001)]:
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                Policy(**{key: value})

    def test_oversized_file_rejected_before_sqlite(self):
        with self.path.open("xb") as stream:
            stream.truncate(16 * 1024 * 1024 + 1)
        with self.assertRaises(ValueError):
            Journal.resume(self.path)

    def test_market_relabeling_rejected(self):
        j = self.journal()
        data = json.loads(j._db.execute("SELECT value FROM metadata").fetchone()[0])
        data.update(source="market-feed", synthetic=False, market_data_qualified=True)
        j._db.execute("UPDATE metadata SET value=?", (json.dumps(data),))
        j.close()
        with self.assertRaises(ValueError):
            Journal.resume(self.path)

    def test_tail_deletion_and_wrong_rehashed_decision_rejected(self):
        j, _, c = self.collector()
        c.poll()
        body = j.events()[2]
        body["derived"]["status"] = "market_eligible"
        text = json.dumps(body, sort_keys=True, separators=(",", ":"))
        digest = hashlib.sha256(text.encode()).hexdigest()
        j._db.execute("UPDATE events SET payload=?,sha256=? WHERE sequence=3", (text, digest))
        j._db.execute("UPDATE head SET sha256=?", (digest,))
        with self.assertRaises(ValueError):
            j.events()
        j._db.execute("DELETE FROM events WHERE sequence=3")
        with self.assertRaises(ValueError):
            j.events()

    def test_schema_trigger_rejected_before_attempt_or_read(self):
        j, source, c = self.collector()
        j._db.execute("CREATE TRIGGER unexpected AFTER INSERT ON events BEGIN DELETE FROM head; END")
        with self.assertRaises(ValueError):
            c.poll()
        self.assertEqual(source.calls, [])

    def test_fixed_synthetic_metadata_and_no_external_imports(self):
        j = self.journal()
        summary = j.summary()
        self.assertTrue(summary["synthetic"])
        for flag in ["broker_entry_available", "market_data_qualified", "orders_available"]:
            self.assertFalse(summary[flag])
        tree = ast.parse((Path(__file__).resolve().parents[1] / "src/forex_demo_lab/snapshot_collector_104.py").read_text())
        names = {n.module.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
        names.update(a.name.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names)
        self.assertLessEqual(names, {"dataclasses", "datetime", "decimal", "hashlib", "json", "math", "pathlib", "sqlite3"})


if __name__ == "__main__":
    unittest.main()
