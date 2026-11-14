"""Invented helper observations and temporary journals; no native calls."""
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from forex_demo_lab.acquisition_lifecycle_138 import AccountMode, Lifecycle, Policy, State
from forex_demo_lab.segment_journal_138 import Journal, Reason, inspect_segments
from forex_demo_lab.supervision_140 import (Cause, Ledger, Observation, Supervisor, SyntheticHelper,
    READY_TIMEOUT_US, MAX_STATUS_AGE_US, inspect_ledger)
from forex_demo_lab.paired_replay_133 import canonical, DENIED
from test_acquisition_138 import FaultStore, FaultStream, GOOD, LOST, blobs

READY = Observation(create_ack=True, set_ack=True, ready_signal=True)
ROOT = Path(__file__).resolve().parents[1]


def rewrite(raw, change):
    rows = [json.loads(line.rsplit(b'\t', 1)[0]) for line in raw.splitlines()]
    change(rows); result = []; head = '0' * 64
    for row in rows:
        row['previous'] = head; payload = canonical(row); head = hashlib.sha256(payload).hexdigest()
        result.append(payload + b'\t' + head.encode() + b'\n')
    return b''.join(result)


class Supervision140Tests(unittest.TestCase):
    def make(self, root, *, enabled=True, life_enabled=True, retry=False, budget=60_000_000, job='a' * 32):
        fault = dict(mode=None, writes=0, syncs=0, opens=0, closes=0)
        journal = Journal(job, lambda name: FaultStore(root, name, fault))
        life = Lifecycle(journal, Policy(life_enabled, retry, budget))
        helper = SyntheticHelper(); ledger = Ledger(root, job)
        return Supervisor(life, helper, ledger, enabled=enabled), fault

    def ready(self, supervisor):
        self.assertTrue(supervisor.start(0, GOOD))
        supervisor.helper.report = READY
        self.assertTrue(supervisor.observe(1, GOOD))
        self.assertTrue(supervisor.record_context(2, 3, GOOD, GOOD))

    def audit(self, root, supervisor):
        raw = supervisor.ledger.path.read_bytes()
        segments = blobs(root, supervisor.ledger.job)
        return inspect_ledger(raw, segments)

    def test_default_off_has_no_helper_journal_or_lifecycle_effects(self):
        with tempfile.TemporaryDirectory() as root:
            s, _ = self.make(root, enabled=False)
            self.assertFalse(s.start(0, GOOD)); self.assertFalse(s.begin_triple(1, GOOD))
            self.assertEqual(list(Path(root).iterdir()), [])
            self.assertTrue(all(v == 0 for v in s.helper.calls.values()))
            for key, value in DENIED.items(): self.assertEqual(s.snapshot()[key], value)

    def test_start_ack_is_not_readiness_and_delayed_readiness_gates_context(self):
        with tempfile.TemporaryDirectory() as root:
            s, _ = self.make(root); self.assertTrue(s.start(0, GOOD))
            self.assertFalse(s.begin_triple(1, GOOD)); self.assertEqual(s.life.state, State.OFF)
            self.assertEqual(s.life.journal.segment, 0)
            s.helper.report = READY
            self.assertTrue(s.observe(READY_TIMEOUT_US - 1, GOOD))
            self.assertFalse(s.begin_triple(READY_TIMEOUT_US - 1, GOOD))
            self.assertTrue(s.record_context(READY_TIMEOUT_US - 1, READY_TIMEOUT_US - 1, GOOD, GOOD))
            self.assertTrue(s.begin_triple(READY_TIMEOUT_US, GOOD)); self.assertTrue(s.finish_triple(READY_TIMEOUT_US + 1, GOOD))
            s.stop(READY_TIMEOUT_US + 2, GOOD)
            self.assertEqual(self.audit(root, s)['last_lifecycle_acknowledged_sequence'], 1)

    def test_exact_readiness_timeout_rejects_late_signal(self):
        with tempfile.TemporaryDirectory() as root:
            s, _ = self.make(root); s.start(0, GOOD); s.helper.report = READY
            self.assertFalse(s.observe(READY_TIMEOUT_US, GOOD)); self.assertEqual(s.cause, Cause.TIMEOUT)
            self.assertEqual(s.life.journal.segment, 0)
            self.assertEqual(self.audit(root, s)['cause'], Cause.TIMEOUT.value)

    def test_contradictory_wrong_binding_future_and_bad_reports_stop(self):
        cases = [(replace(READY, create_ack=False), Cause.PROTOCOL), (replace(READY, token='b' * 32), Cause.BINDING),
                 (replace(READY, observed_us=2), Cause.PROTOCOL), (replace(READY, running=1), Cause.PROTOCOL),
                 ('invalid', Cause.PROTOCOL)]
        for report, cause in cases:
            with self.subTest(cause=cause), tempfile.TemporaryDirectory() as root:
                s, _ = self.make(root); s.start(0, GOOD); s.helper.report = report
                self.assertFalse(s.observe(1, GOOD)); self.assertEqual(s.cause, cause)
                self.assertEqual(s.life.journal.segment, 0); self.assertTrue(s.snapshot()['cleanup_complete'])
                self.assertEqual(self.audit(root, s)['cause'], cause.value)

    def test_exact_status_age_boundary_and_stale_duplicate(self):
        with tempfile.TemporaryDirectory() as root:
            s, _ = self.make(root); self.ready(s)
            s.helper.report = replace(READY, observed_us=3)
            self.assertTrue(s.observe(3 + MAX_STATUS_AGE_US, GOOD))
            self.assertFalse(s.observe(4 + MAX_STATUS_AGE_US, GOOD)); self.assertEqual(s.cause, Cause.STALE)
            self.assertFalse(self.audit(root, s)['resume_available'])

    def test_reversed_helper_timestamp_or_supervisor_clock_stops(self):
        with tempfile.TemporaryDirectory() as root:
            s, _ = self.make(root); self.ready(s)
            s.helper.report = replace(READY, observed_us=2)
            s.observe(4, GOOD); self.assertEqual(s.cause, Cause.PROTOCOL)
        with tempfile.TemporaryDirectory() as root:
            s, _ = self.make(root); self.ready(s)
            s.observe(2, GOOD); self.assertEqual(s.cause, Cause.CLOCK)
            self.assertTrue(self.audit(root, s)['stopped_record_present'])

    def test_helper_exit_readiness_loss_and_power_loss_abort_pending(self):
        for report, cause in [(replace(READY, running=False), Cause.EXIT),
                              (replace(READY, ready_signal=False), Cause.LOST), (replace(READY, mains=False), Cause.POWER)]:
            with self.subTest(cause=cause), tempfile.TemporaryDirectory() as root:
                s, _ = self.make(root); self.ready(s); self.assertTrue(s.begin_triple(10, GOOD))
                s.helper.report = report
                self.assertFalse(s.finish_triple(11, GOOD)); self.assertEqual(s.cause, cause)
                self.assertEqual(s.life.journal.committed, 0)
                life = inspect_segments(blobs(root)); self.assertFalse(life['pending_triple'])
                self.assertEqual(s.helper.calls['start'], 1)
                self.assertEqual(self.audit(root, s)['cause'], cause.value)

    def test_owner_loss_stops_pending_and_cleanup_only_once(self):
        with tempfile.TemporaryDirectory() as root:
            s, _ = self.make(root); self.ready(s); s.begin_triple(10, GOOD)
            self.assertFalse(s.finish_triple(11, GOOD, owner_alive=False))
            self.assertEqual(s.cause, Cause.OWNER)
            self.assertEqual(s.helper.calls['cancel'], 1); self.assertEqual(s.helper.calls['confirm_exit'], 1)
            calls = dict(s.helper.calls); raw = s.ledger.path.read_bytes()
            s.observe(12, GOOD); s.start(12, GOOD); s.retry(12, GOOD); s.stop(12, GOOD)
            self.assertEqual(s.helper.calls, calls); self.assertEqual(s.ledger.path.read_bytes(), raw)
            self.assertTrue(self.audit(root, s)['lifecycle_acknowledged_prefix_bound'])

    def test_context_post_read_helper_loss_discards_context(self):
        with tempfile.TemporaryDirectory() as root:
            s, _ = self.make(root); s.start(0, GOOD); s.helper.report = READY; s.observe(1, GOOD)
            original = s.helper.poll
            def poll(now): return replace(original(now), running=now < 3)
            with patch.object(s.helper, 'poll', side_effect=poll):
                self.assertFalse(s.record_context(2, 3, GOOD, GOOD))
            self.assertIsNone(s.life.context_at); self.assertEqual(s.cause, Cause.EXIT)
            self.assertEqual(s.life.journal.committed, 0)

    def test_fatal_account_guard_before_start_and_after_pending_never_retries(self):
        for mode in (AccountMode.REAL, AccountMode.CONTEST):
            with tempfile.TemporaryDirectory() as root:
                s, _ = self.make(root); s.start(0, replace(GOOD, actual_mode=mode))
                self.assertEqual(s.cause, Cause.GUARD); self.assertEqual(s.helper.calls['start'], 0)
                self.assertTrue(self.audit(root, s)['stopped_record_present'])
            with tempfile.TemporaryDirectory() as root:
                s, _ = self.make(root, retry=True); self.ready(s); s.begin_triple(10, GOOD)
                s.finish_triple(11, replace(GOOD, actual_mode=mode))
                self.assertEqual(s.life.reason, Reason.ACCOUNT); self.assertEqual(s.life.journal.committed, 0)

    def test_overall_budget_includes_startup_before_lifecycle_origin(self):
        with tempfile.TemporaryDirectory() as root:
            s, _ = self.make(root, budget=20_000_000); s.start(0, GOOD); s.helper.report = READY
            s.observe(9_000_000, GOOD); s.record_context(9_000_001, 9_000_002, GOOD, GOOD)
            s.begin_triple(19_000_000, GOOD)
            self.assertFalse(s.finish_triple(20_000_000, GOOD)); self.assertEqual(s.cause, Cause.DEADLINE)
            self.assertEqual(s.life.journal.committed, 0)
            self.assertEqual(s.helper.duration_ms, 20000)

    def test_start_failure_or_exception_still_attempts_cancel_and_exit(self):
        for fault in ('false', 'throw'):
            with tempfile.TemporaryDirectory() as root:
                s, _ = self.make(root)
                if fault == 'false': s.helper.start_ack = False
                else: s.helper.throw_at = 'start'
                self.assertFalse(s.start(0, GOOD)); self.assertEqual(s.cause, Cause.START)
                self.assertEqual(s.helper.calls['cancel'], 1); self.assertEqual(s.helper.calls['confirm_exit'], 1)

    def test_cleanup_failures_are_distinct_from_recording_stopped(self):
        for fault in ('cancel_false', 'cancel_throw', 'exit_false', 'exit_throw'):
            with tempfile.TemporaryDirectory() as root:
                s, _ = self.make(root); self.ready(s)
                if fault == 'cancel_false': s.helper.cancel_ack = False
                elif fault == 'exit_false': s.helper.exit_ack = False
                else: s.helper.throw_at = 'cancel' if fault == 'cancel_throw' else 'confirm_exit'
                s.stop(10, GOOD)
                self.assertEqual(s.state, 'stopped'); self.assertFalse(s.snapshot()['cleanup_complete'])
                self.assertEqual(s.helper.calls['confirm_exit'], 1)
                self.assertTrue(self.audit(root, s)['stopped_record_present'])

    def test_network_retry_keeps_helper_but_lost_helper_cannot_reconnect(self):
        with tempfile.TemporaryDirectory() as root:
            s, _ = self.make(root, retry=True); self.ready(s)
            s.begin_triple(10, GOOD); s.finish_triple(11, LOST)
            self.assertEqual(s.life.state, State.INTERRUPTED)
            due = s.life.wait_until
            self.assertTrue(s.retry(due, GOOD)); self.assertEqual(s.life.journal.segment, 2)
            self.assertFalse(s.begin_triple(due, GOOD)); s.record_context(due, due + 1, GOOD, GOOD)
            s.begin_triple(due + 2, GOOD); s.finish_triple(due + 3, LOST)
            s.helper.report = replace(READY, running=False)
            self.assertFalse(s.retry(s.life.wait_until, GOOD)); self.assertEqual(s.cause, Cause.EXIT)
            self.assertEqual(s.helper.calls['start'], 1)
            self.assertTrue(self.audit(root, s)['lifecycle_acknowledged_prefix_bound'])

    def test_supervision_fsync_fault_still_aborts_lifecycle_and_cleans_up(self):
        with tempfile.TemporaryDirectory() as root:
            s, _ = self.make(root); self.ready(s); s.begin_triple(10, GOOD)
            with patch.object(s.ledger, '_sync', side_effect=OSError('invented_sync')):
                s.finish_triple(11, GOOD, owner_alive=False)
            self.assertEqual(s.cause, Cause.STORAGE); self.assertTrue(s.ledger.poisoned)
            self.assertEqual(s.life.state, State.STOPPED); self.assertEqual(s.life.journal.committed, 0)
            self.assertTrue(s.snapshot()['cleanup_complete'])
            prefix = inspect_ledger(s.ledger.path.read_bytes())
            self.assertFalse(prefix['resume_available']); self.assertFalse(prefix['durability_ack_proven'])

    def test_lifecycle_sync_fault_binds_only_acknowledged_prefix(self):
        with tempfile.TemporaryDirectory() as root:
            s, fault = self.make(root); self.ready(s); s.begin_triple(10, GOOD)
            fault['mode'] = 'fsync'; self.assertFalse(s.finish_triple(11, GOOD))
            self.assertEqual(s.cause, Cause.LIFECYCLE); self.assertEqual(s.life.reason, Reason.STORAGE)
            self.assertEqual(s.life.journal.committed, 0)
            self.assertEqual(inspect_segments(blobs(root))['committed_sequence_present'], 1)
            self.assertTrue(self.audit(root, s)['lifecycle_acknowledged_prefix_bound'])

    def test_pre_start_ledger_fault_never_starts_helper(self):
        with tempfile.TemporaryDirectory() as root:
            s, _ = self.make(root)
            with patch.object(s.ledger, '_sync', side_effect=OSError('invented_sync')): s.start(0, GOOD)
            self.assertEqual(s.helper.calls['start'], 0); self.assertEqual(s.state, 'stopped')

    def test_restart_collision_is_rejected_without_touching_old_journals(self):
        with tempfile.TemporaryDirectory() as root:
            s, _ = self.make(root); self.ready(s); s.stop(10, GOOD)
            old = {p: p.read_bytes() for p in Path(root).rglob('*.journal')}
            again, _ = self.make(root); self.assertFalse(again.start(0, GOOD))
            self.assertEqual(again.helper.calls['start'], 0)
            self.assertEqual({p: p.read_bytes() for p in old}, old)

    def test_rehashed_bad_order_cause_and_wrong_lifecycle_binding_reject(self):
        with tempfile.TemporaryDirectory() as root:
            s, _ = self.make(root); self.ready(s); s.stop(10, GOOD); raw = s.ledger.path.read_bytes()
            def wrong_order(rows): rows[1]['event'] = 'lifecycle_started'
            def wrong_cause(rows): rows[-1]['cause'] = Cause.EXIT.value
            def wrong_head(rows): rows[-1]['life_head'] = 'a' * 64
            for change in (wrong_order, wrong_cause, wrong_head):
                with self.assertRaises(ValueError): inspect_ledger(rewrite(raw, change), blobs(root))
            with self.assertRaises(ValueError): inspect_ledger(raw + b'partial')

    def test_disabled_lifecycle_does_not_acquire_helper_and_no_admission(self):
        with tempfile.TemporaryDirectory() as root:
            s, _ = self.make(root, life_enabled=False); s.start(0, GOOD)
            self.assertEqual(s.cause, Cause.DISABLED); self.assertEqual(s.helper.calls['start'], 0)
            for key, value in DENIED.items(): self.assertEqual(s.snapshot()[key], value)
            self.assertFalse(s.snapshot()['native_helper_launch_available'])
            self.assertFalse(s.snapshot()['actual_owner_death_tested'])
            self.assertIsNone(s.snapshot()['collection_dates'])

    def test_poll_exception_and_early_owner_loss_stop_without_extra_start(self):
        with tempfile.TemporaryDirectory() as root:
            s, _ = self.make(root); self.ready(s); s.helper.throw_at = 'poll'
            self.assertFalse(s.begin_triple(10, GOOD)); self.assertEqual(s.cause, Cause.PROTOCOL)
            self.assertEqual(s.helper.calls['start'], 1); self.assertTrue(s.snapshot()['cleanup_complete'])
        with tempfile.TemporaryDirectory() as root:
            s, _ = self.make(root); self.assertFalse(s.start(0, GOOD, owner_alive=False))
            self.assertEqual(s.cause, Cause.OWNER); self.assertEqual(s.helper.calls['start'], 0)

    def test_short_supervision_write_preserves_partial_tail_and_stops_recording(self):
        with tempfile.TemporaryDirectory() as root:
            s, _ = self.make(root); self.ready(s); s.begin_triple(10, GOOD)
            fault = dict(mode='short', writes=0, closes=0)
            s.ledger.stream = FaultStream(s.ledger.stream, fault)
            self.assertFalse(s.finish_triple(11, GOOD, owner_alive=False))
            self.assertEqual(s.life.state, State.STOPPED); self.assertEqual(s.life.journal.committed, 0)
            audit = inspect_ledger(s.ledger.path.read_bytes())
            self.assertGreater(audit['trailing_partial_bytes'], 0)
            self.assertFalse(audit['stopped_record_present']); self.assertFalse(audit['resume_available'])

    def test_supervision_close_failure_is_not_a_durability_receipt(self):
        with tempfile.TemporaryDirectory() as root:
            s, _ = self.make(root); self.ready(s)
            fault = dict(mode='close', writes=0, closes=0)
            s.ledger.stream = FaultStream(s.ledger.stream, fault)
            s.stop(10, GOOD)
            self.assertTrue(s.ledger.poisoned); self.assertEqual(s.cause, Cause.STORAGE)
            self.assertTrue(self.audit(root, s)['stopped_record_present'])
            self.assertFalse(self.audit(root, s)['durability_ack_proven'])

    def test_fixture_cli_library_and_optimized_python_agree(self):
        from forex_demo_lab.supervision_fixture_140 import run_demo
        command = [sys.executable, str(ROOT / 'scripts/supervision-140.py')]
        first = subprocess.run(command, capture_output=True, check=True)
        second = subprocess.run([sys.executable, '-O', *command[1:]], capture_output=True, check=True)
        self.assertEqual(first.stdout, second.stdout); self.assertEqual(json.loads(first.stdout), run_demo())
        r = json.loads(first.stdout)
        self.assertEqual(len(r['scenarios']), 7)
        self.assertFalse(r['scenarios'][-1]['status']['cleanup_complete'])
        self.assertTrue(all(case['audit']['lifecycle_acknowledged_prefix_bound'] for case in r['scenarios']))
        self.assertFalse(r['native_helper_launched']); self.assertFalse(r['actual_owner_death_tested'])


if __name__ == '__main__': unittest.main()
