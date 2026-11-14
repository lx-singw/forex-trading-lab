"""Invented events and temporary files only; no prices or terminal calls."""
from dataclasses import replace
import hashlib
import json
import random
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from forex_demo_lab.acquisition_lifecycle_138 import AccountMode, Checks, Lifecycle, Policy, State, HOUR_US, MAX_JOB_US
from forex_demo_lab.segment_journal_138 import (CONTROL_RESERVE, MAX_FRAME, DiskStore, Event,
    Journal, Reason, inspect_segments)
from forex_demo_lab.paired_replay_133 import canonical, DENIED

GOOD = Checks(actual_mode=AccountMode.DEMO, query_ok=True, identity_unchanged=True,
              connected=True, non_tester=True, eurusd_visible=True, currency_usd=True, clock_safe=True)
LOST = replace(GOOD, connected=False)
ROOT = Path(__file__).resolve().parents[1]


class FaultStream:
    def __init__(self, stream, fault): self.stream, self.fault = stream, fault
    def write(self, data):
        self.fault['writes'] += 1
        if self.fault['mode'] == 'write': raise OSError('invented_write')
        if self.fault['mode'] == 'short': return self.stream.write(data[:len(data) // 2])
        return self.stream.write(data)
    def flush(self): self.stream.flush()
    def fileno(self): return self.stream.fileno()
    def close(self):
        self.fault['closes'] += 1; self.stream.close()
        if self.fault['mode'] == 'close': raise OSError('invented_close')


class FaultStore(DiskStore):
    def __init__(self, root, job, fault): super().__init__(root, job); self.fault = fault
    def open(self, segment):
        self.fault['opens'] += 1
        if self.fault['mode'] == 'open': raise OSError('invented_open')
        return FaultStream(super().open(segment), self.fault)
    def sync(self, stream):
        self.fault['syncs'] += 1
        if self.fault['mode'] == 'flush': raise OSError('invented_flush')
        stream.flush()
        if self.fault['mode'] == 'fsync': raise OSError('invented_fsync')
        super().sync(stream)


def blobs(root, job='a' * 32):
    return [p.read_bytes() for p in sorted((Path(root) / ('InventedJob138-' + job)).glob('*.journal'))]


def frames(root, job='a' * 32):
    return [json.loads(line.rsplit(b'\t', 1)[0]) for raw in blobs(root, job) for line in raw.splitlines()]


def rewrite(raw, change):
    rows = [json.loads(line.rsplit(b'\t', 1)[0]) for line in raw.splitlines()]
    change(rows); head = rows[0]['previous']; result = []
    for row in rows:
        row['previous'] = head; payload = canonical(row); head = hashlib.sha256(payload).hexdigest()
        result.append(payload + b'\t' + head.encode('ascii') + b'\n')
    return b''.join(result)


class Acquisition138Tests(unittest.TestCase):
    def make(self, root, *, enabled=True, retry=False, limit=MAX_JOB_US, job='a' * 32,
             file_limit=32 * 1024 * 1024, job_limit=128 * 1024 * 1024):
        fault = dict(mode=None, writes=0, syncs=0, opens=0, closes=0)
        journal = Journal(job, lambda name: FaultStore(root, name, fault), file_limit, job_limit)
        return Lifecycle(journal, Policy(enabled, retry, limit)), fault

    def ready(self, machine):
        self.assertTrue(machine.start(0, GOOD))
        self.assertTrue(machine.record_context(0, 1, GOOD, GOOD))

    def test_defaults_off_create_no_files_and_never_grant_admission(self):
        with tempfile.TemporaryDirectory() as root:
            journal = Journal('a' * 32, lambda name: DiskStore(root, name))
            machine = Lifecycle(journal)
            self.assertFalse(machine.start(0, GOOD)); self.assertEqual(list(Path(root).iterdir()), [])
            self.assertFalse(machine.policy.retry_enabled)
            for key, value in DENIED.items(): self.assertEqual(machine.snapshot()[key], value)
            self.assertFalse(machine.snapshot()['native_acquisition_available'])

    def test_actual_enum_unknown_identity_and_fatal_guards_dominate_disconnection(self):
        bad = [(replace(LOST, actual_mode=mode), Reason.ACCOUNT) for mode in (AccountMode.REAL, AccountMode.CONTEST, None, 1, True)]
        bad += [(replace(LOST, identity_unchanged=False), Reason.IDENTITY),
                (replace(LOST, algo_enabled=True), Reason.ALGO), (replace(LOST, clock_safe=False), Reason.CLOCK),
                (replace(LOST, currency_usd=False), Reason.SYMBOL), (replace(LOST, query_ok=False), Reason.QUERY)]
        for check, reason in bad:
            with self.subTest(reason=reason), tempfile.TemporaryDirectory() as root:
                machine, _ = self.make(root, retry=True)
                self.assertFalse(machine.start(0, check))
                self.assertEqual((machine.state, machine.reason), (State.STOPPED, reason))
                self.assertEqual(machine.journal.attempt, 0)
                self.assertTrue(inspect_segments(blobs(root))['stopped_record_present'])

    def test_default_no_reconnect_and_after_guard_failure_aborts_without_commit(self):
        with tempfile.TemporaryDirectory() as root:
            machine, _ = self.make(root); self.ready(machine)
            self.assertTrue(machine.begin_triple(1_000_000, GOOD))
            self.assertFalse(machine.finish_triple(1_000_010, LOST))
            self.assertEqual(machine.reason, Reason.DISCONNECTED)
            result = inspect_segments(blobs(root))
            self.assertEqual(result['committed_sequence_present'], 0)
            self.assertFalse(result['pending_triple']); self.assertFalse(result['resume_available'])
            self.assertIn('triple_abort', [f['event'] for f in frames(root)])

    def test_after_read_actual_account_change_never_commits_or_retries(self):
        for bad in [replace(GOOD, actual_mode=AccountMode.REAL), replace(GOOD, identity_unchanged=False)]:
            with tempfile.TemporaryDirectory() as root:
                machine, _ = self.make(root, retry=True); self.ready(machine)
                machine.begin_triple(1_000_000, GOOD)
                machine.finish_triple(1_000_010, bad)
                self.assertEqual(machine.state, State.STOPPED)
                self.assertEqual(machine.journal.committed, 0); self.assertEqual(machine.journal.attempt, 0)

    def test_reconnect_wait_boundaries_new_segment_and_context_requirement(self):
        with tempfile.TemporaryDirectory() as root:
            machine, _ = self.make(root, retry=True); self.ready(machine)
            machine.begin_triple(1_000_000, GOOD); machine.finish_triple(1_000_010, LOST)
            due = machine.wait_until; count = machine.journal.frame
            self.assertFalse(machine.retry(due - 1, GOOD)); self.assertEqual(machine.journal.frame, count)
            self.assertTrue(machine.retry(due, GOOD)); self.assertEqual(machine.journal.segment, 2)
            self.assertFalse(machine.begin_triple(due, GOOD))
            self.assertTrue(machine.record_context(due, due + 10, GOOD, GOOD))
            self.assertTrue(machine.begin_triple(due + 10, GOOD)); machine.finish_triple(due + 20, GOOD)
            machine.stop(due + 30, GOOD)
            result = inspect_segments(blobs(root)); self.assertEqual(result['committed_sequence_present'], 1)
            self.assertEqual(result['segment_count'], 2); self.assertEqual(result['retry_attempts'], 1)
            second = [f['event'] for f in frames(root) if f['segment'] == 2]
            self.assertEqual(second[:4], ['open', 'ready', 'context', 'triple_begin'])

    def test_failed_attempts_backoff_and_job_global_budget_do_not_reset(self):
        with tempfile.TemporaryDirectory() as root:
            machine, _ = self.make(root, retry=True); self.ready(machine)
            machine.interrupt(1, GOOD)
            self.assertEqual(machine.wait_until, 5_000_001)
            machine.retry(machine.wait_until, LOST); self.assertEqual(machine.wait_until, 35_000_001)
            machine.retry(machine.wait_until, GOOD); self.assertEqual(machine.journal.attempt, 2)
            machine.interrupt(35_000_002, GOOD); self.assertEqual(machine.wait_until, 155_000_002)
            machine.retry(machine.wait_until, LOST)
            self.assertEqual(machine.reason, Reason.RETRIES); self.assertEqual(machine.journal.attempt, 3)
            self.assertFalse(machine.retry(999_000_000, GOOD))
            self.assertEqual(inspect_segments(blobs(root))['retry_attempts'], 3)

    def test_deadline_includes_waits_and_exact_boundary_aborts_pending(self):
        for pending in (False, True):
            with tempfile.TemporaryDirectory() as root:
                machine, _ = self.make(root, retry=True, limit=2_000_000); self.ready(machine)
                if pending:
                    machine.begin_triple(1_000_000, GOOD); machine.finish_triple(2_000_000, GOOD)
                else:
                    machine.interrupt(1, GOOD); machine.retry(2_000_000, GOOD)
                self.assertEqual(machine.reason, Reason.DEADLINE)
                self.assertEqual(machine.journal.committed, 0)
                self.assertTrue(inspect_segments(blobs(root))['stopped_record_present'])

    def test_rollback_and_fatal_guard_during_wait_latch_stop(self):
        with tempfile.TemporaryDirectory() as root:
            machine, _ = self.make(root, retry=True); self.ready(machine)
            machine.begin_triple(100, GOOD); machine.finish_triple(99, GOOD)
            self.assertEqual(machine.reason, Reason.CLOCK)
            self.assertTrue(inspect_segments(blobs(root))['stopped_record_present'])
        with tempfile.TemporaryDirectory() as root:
            machine, _ = self.make(root, retry=True); self.ready(machine); machine.interrupt(2, GOOD)
            machine.retry(3, replace(LOST, actual_mode=AccountMode.CONTEST))
            self.assertEqual(machine.reason, Reason.ACCOUNT); self.assertEqual(machine.journal.attempt, 0)

    def test_spacing_has_no_catchup_and_context_refresh_uses_elapsed_time(self):
        with tempfile.TemporaryDirectory() as root:
            machine, _ = self.make(root); self.ready(machine)
            machine.begin_triple(10, GOOD); machine.finish_triple(11, GOOD)
            self.assertFalse(machine.begin_triple(1_000_009, GOOD))
            self.assertTrue(machine.begin_triple(1_000_010, GOOD)); machine.finish_triple(1_000_011, GOOD)
            self.assertFalse(machine.begin_triple(HOUR_US + 1, GOOD))
            self.assertTrue(machine.record_context(HOUR_US + 1, HOUR_US + 2, GOOD, GOOD))
            self.assertTrue(machine.begin_triple(HOUR_US + 2, GOOD)); machine.finish_triple(HOUR_US + 3, GOOD)
            self.assertFalse(machine.begin_triple(HOUR_US + 4, GOOD))
            machine.stop(HOUR_US + 5, GOOD)
            self.assertEqual(inspect_segments(blobs(root))['committed_sequence_present'], 3)

    def test_context_result_discarded_on_after_guard_failure(self):
        with tempfile.TemporaryDirectory() as root:
            machine, _ = self.make(root, retry=True); machine.start(0, GOOD)
            machine.record_context(1, 2, GOOD, replace(GOOD, algo_enabled=True))
            self.assertEqual(machine.reason, Reason.ALGO)
            self.assertNotIn('context', [f['event'] for f in frames(root)])

    def test_rotation_before_triple_and_new_context_in_each_segment(self):
        with tempfile.TemporaryDirectory() as root:
            machine, _ = self.make(root, file_limit=CONTROL_RESERVE + 4 * MAX_FRAME, job_limit=128 * 1024)
            self.ready(machine)
            for index in range(60):
                now = (index + 1) * 1_000_000
                if not machine.begin_triple(now, GOOD):
                    self.assertEqual(machine.state, State.RECORDING)
                    self.assertTrue(machine.context_due(now))
                    self.assertTrue(machine.record_context(now, now, GOOD, GOOD))
                    self.assertTrue(machine.begin_triple(now, GOOD))
                machine.finish_triple(now + 1, GOOD)
            machine.stop(61_000_000, GOOD)
            data = blobs(root); self.assertGreater(len(data), 1)
            self.assertTrue(all(len(raw) <= machine.journal.file_limit for raw in data))
            self.assertLessEqual(sum(map(len, data)), machine.journal.job_limit)
            self.assertEqual(inspect_segments(data)['committed_sequence_present'], 60)
            for segment in range(1, len(data) + 1):
                events = [f['event'] for f in frames(root) if f['segment'] == segment]
                self.assertEqual(events[:4], ['open', 'ready', 'context', 'triple_begin'])

    def test_pending_triple_cannot_rotate_or_refresh_context(self):
        with tempfile.TemporaryDirectory() as root:
            machine, _ = self.make(root); self.ready(machine); machine.begin_triple(10, GOOD)
            with self.assertRaises(ValueError): machine.begin_triple(11, GOOD)
            with self.assertRaises(ValueError): machine.record_context(11, 12, GOOD, GOOD)
            self.assertEqual(machine.journal.segment, 1)
            machine.stop(12, GOOD); self.assertEqual(inspect_segments(blobs(root))['committed_sequence_present'], 0)

    def test_write_short_flush_and_fsync_failure_poison_without_retry_or_ack(self):
        for mode in ('write', 'short', 'flush', 'fsync'):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as root:
                machine, fault = self.make(root, retry=True); self.ready(machine)
                machine.begin_triple(10, GOOD); fault['mode'] = mode
                self.assertFalse(machine.finish_triple(11, GOOD))
                self.assertEqual((machine.state, machine.reason), (State.STOPPED, Reason.STORAGE))
                self.assertEqual(machine.journal.committed, 0)
                self.assertTrue(machine.journal.poisoned)
                counts = dict(fault)
                machine.retry(100, GOOD); machine.begin_triple(100, GOOD); machine.stop(100, GOOD)
                self.assertEqual(fault, counts)
                result = inspect_segments(blobs(root))
                self.assertFalse(result['durability_ack_proven']); self.assertFalse(result['resume_available'])
                if mode == 'short': self.assertGreater(result['trailing_partial_bytes'], 0)

    def test_close_failure_and_failed_reconnect_open_stop_new_writes(self):
        for mode in ('close', 'open'):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as root:
                machine, fault = self.make(root, retry=True); self.ready(machine); machine.interrupt(2, GOOD)
                fault['mode'] = mode
                self.assertFalse(machine.retry(machine.wait_until, GOOD))
                self.assertEqual(machine.reason, Reason.STORAGE); self.assertTrue(machine.journal.poisoned)
                count = fault['writes']; machine.start(999, GOOD); self.assertEqual(fault['writes'], count)

    def test_job_byte_budget_and_creation_collision_fail_closed(self):
        with tempfile.TemporaryDirectory() as root:
            cap = CONTROL_RESERVE + 4 * MAX_FRAME
            machine, _ = self.make(root, file_limit=cap, job_limit=cap); self.ready(machine)
            for i in range(1, 100):
                if not machine.begin_triple(i * 1_000_000, GOOD):
                    if machine.state is State.STOPPED: break
                    if not machine.record_context(i * 1_000_000, i * 1_000_000, GOOD, GOOD): break
                    if not machine.begin_triple(i * 1_000_000, GOOD): break
                machine.finish_triple(i * 1_000_000 + 1, GOOD)
            self.assertEqual(machine.reason, Reason.STORAGE)
            self.assertLessEqual(machine.journal.reserved_job, cap)
            collision, _ = self.make(root); self.assertFalse(collision.start(0, GOOD))
            self.assertEqual(collision.reason, Reason.STORAGE)

    def test_context_capacity_rotation_discards_pre_boundary_result(self):
        with tempfile.TemporaryDirectory() as root:
            machine, _ = self.make(root, file_limit=CONTROL_RESERVE + 4 * MAX_FRAME)
            self.ready(machine)
            for now in range(2, 100):
                if not machine.record_context(now, now, GOOD, GOOD): break
            self.assertEqual(machine.journal.segment, 2)
            self.assertIsNone(machine.context_at)
            self.assertFalse(machine.begin_triple(now, GOOD))
            self.assertTrue(machine.record_context(now, now + 1, GOOD, GOOD))
            machine.stop(now + 2, GOOD)
            self.assertTrue(inspect_segments(blobs(root))['stopped_record_present'])

    def test_store_refuses_symlink_and_existing_segment_overwrite(self):
        with tempfile.TemporaryDirectory() as root:
            alias = Path(root) / 'alias'; alias.symlink_to(root, target_is_directory=True)
            machine, _ = self.make(alias)
            self.assertFalse(machine.start(0, GOOD)); self.assertEqual(machine.reason, Reason.STORAGE)
            store = DiskStore(root, 'b' * 32)
            stream = store.open(1); stream.write(b'invented-existing'); store.sync(stream); stream.close()
            from forex_demo_lab.segment_journal_138 import StorageFailure
            with self.assertRaises(StorageFailure): store.open(1)
            self.assertEqual((store.folder / 'Segment0001.journal').read_bytes(), b'invented-existing')

    def test_restart_preserves_pending_prefix_and_requires_independent_job(self):
        with tempfile.TemporaryDirectory() as root:
            machine, _ = self.make(root); self.ready(machine); machine.begin_triple(10, GOOD)
            machine.journal.poison()  # Invented crash; no terminal frame is written.
            old = blobs(root); result = inspect_segments(old)
            self.assertTrue(result['pending_triple']); self.assertFalse(result['final_close_present'])
            restarted, _ = self.make(root, job='b' * 32); self.ready(restarted)
            restarted.stop(2, GOOD)
            self.assertEqual(blobs(root), old)
            self.assertFalse(inspect_segments(blobs(root, 'b' * 32))['cross_job_identity_established'])
            with self.assertRaises(ValueError): inspect_segments(old + blobs(root, 'b' * 32))

    def test_corrupt_rehashed_semantics_and_tail_after_close_are_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            machine, _ = self.make(root); self.ready(machine)
            with self.assertRaises(ValueError): machine.journal.append('private-text', 2)
            machine.begin_triple(10, GOOD); machine.finish_triple(11, GOOD); machine.stop(12, GOOD)
            raw = blobs(root)[0]
            with self.assertRaises(ValueError): inspect_segments([raw.replace(b'context', b'contexx', 1)])
            def bad_commit(rows):
                next(f for f in rows if f['event'] == 'triple_commit')['sequence'] = 99
            with self.assertRaises(ValueError): inspect_segments([rewrite(raw, bad_commit)])
            with self.assertRaises(ValueError): inspect_segments([raw + b'partial'])

    def test_missing_middle_close_and_forged_context_across_boundary_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            machine, _ = self.make(root, retry=True); self.ready(machine); machine.interrupt(2, GOOD)
            machine.retry(machine.wait_until, GOOD); machine.record_context(machine.last, machine.last, GOOD, GOOD)
            machine.begin_triple(machine.last, GOOD); machine.finish_triple(machine.last, GOOD); machine.stop(machine.last, GOOD)
            data = blobs(root)
            first = b'\n'.join(data[0].split(b'\n')[:-2]) + b'\n'
            with self.assertRaises(ValueError): inspect_segments([first, data[1]])
            def no_context(rows): next(f for f in rows if f['event'] == 'context')['event'] = 'ready'
            # Rehash the second segment; the state error cannot become valid context.
            with self.assertRaises(ValueError): inspect_segments([data[0], rewrite(data[1], no_context)])

    def test_invalid_policy_inputs_and_unknown_guards_are_not_native_evidence(self):
        for kwargs in ({'enabled': 1}, {'retry_enabled': 1}, {'max_elapsed_us': 0}, {'max_elapsed_us': MAX_JOB_US + 1}):
            with self.assertRaises(ValueError): Policy(**kwargs)
        with tempfile.TemporaryDirectory() as root:
            machine, _ = self.make(root); machine.start(0, Checks())
            self.assertEqual(machine.reason, Reason.QUERY)
            for key, value in DENIED.items(): self.assertEqual(machine.snapshot()[key], value)

    def test_builtin_cli_and_library_are_repeatable_including_optimized_python(self):
        from forex_demo_lab.acquisition_fixture_138 import run_demo
        command = [sys.executable, str(ROOT / 'scripts/acquisition-138.py')]
        normal = subprocess.run(command, capture_output=True, check=True)
        optimized = subprocess.run([sys.executable, '-O', *command[1:]], capture_output=True, check=True)
        self.assertEqual(normal.stdout, optimized.stdout)
        self.assertEqual(json.loads(normal.stdout), run_demo())
        report = json.loads(normal.stdout)
        self.assertEqual(report['scenarios'][0]['status']['acknowledged_committed_sequence'], 40)
        self.assertEqual(report['scenarios'][1]['status']['segments'], 2)
        self.assertEqual(report['scenarios'][2]['status']['retry_attempts'], 3)
        self.assertTrue(report['scenarios'][3]['old_prefix']['pending_triple'])
        self.assertFalse(report['actual_account_queried']); self.assertFalse(report['actual_quotes_read'])
        self.assertIsNone(report['collection_dates'])

    def test_invalid_clock_markers_stop_and_overflow_origin_never_opens_storage(self):
        for marker in (-1, True, 1.5, 2**64):
            with tempfile.TemporaryDirectory() as root:
                machine, _ = self.make(root); self.ready(machine)
                machine.begin_triple(10, GOOD); machine.finish_triple(marker, GOOD)
                self.assertEqual(machine.reason, Reason.CLOCK)
                self.assertEqual(machine.journal.committed, 0)
                self.assertTrue(inspect_segments(blobs(root))['stopped_record_present'])
        with tempfile.TemporaryDirectory() as root:
            machine, _ = self.make(root)
            with self.assertRaises(ValueError): machine.start(2**64 - 1, GOOD)
            self.assertEqual(list(Path(root).iterdir()), [])

    def test_generated_transition_paths_match_independent_journal_state(self):
        rng = random.Random(138)
        for _ in range(24):
            with tempfile.TemporaryDirectory() as root:
                machine, _ = self.make(root, retry=True, file_limit=CONTROL_RESERVE + 4 * MAX_FRAME)
                self.ready(machine); now = 1
                for _ in range(30):
                    now += rng.choice([0, 1, 999_999, 1_000_000, 5_000_000, 30_000_000])
                    if machine.state is State.STOPPED: break
                    if machine.state is State.INTERRUPTED:
                        if rng.randrange(2): now = max(now, machine.wait_until)
                        machine.retry(now, GOOD if rng.randrange(2) else LOST)
                    elif machine.pending is not None:
                        machine.finish_triple(now, GOOD if rng.randrange(4) else LOST)
                    elif machine.context_due(now):
                        machine.record_context(now, now, GOOD, GOOD)
                    elif rng.randrange(4): machine.begin_triple(now, GOOD)
                    else: machine.interrupt(now, GOOD)
                machine.stop(max(now, machine.last), GOOD)
                report = inspect_segments(blobs(root))
                self.assertEqual(report['committed_sequence_present'], machine.journal.committed)
                self.assertEqual(report['retry_attempts'], machine.journal.attempt)
                self.assertLessEqual(machine.journal.attempt, 3)
                self.assertFalse(report['resume_available'])


if __name__ == '__main__': unittest.main()
