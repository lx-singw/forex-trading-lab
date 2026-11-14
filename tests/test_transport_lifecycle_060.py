import json
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
import unittest

from forex_demo_lab.capture_budget_047 import Policy, start_authority, PermitRejected
from forex_demo_lab.transport_lifecycle_060 import (
    OfflineLifecycle, Observation, Cleanup, issue_frame, native_error, MQL_ERRORS)
from forex_demo_lab.windows_pipe_047 import PipeRejected

ROOT = Path(__file__).resolve().parents[1]
POLICY = Policy('60'*16, '60'*32)  # Synthetic; reservations only in TemporaryDirectory.


class Clock:
    def __init__(self):
        self.utc, self.mono, self.boot = 1791352800000, 0, 100000
    def __call__(self):
        return self.utc, self.mono, self.boot
    def advance(self, ms):
        self.utc += ms; self.mono += ms*1000000; self.boot += ms


class Channel:
    """Explicit readiness/message boundaries in a model; no native operations."""
    def __init__(self, clock, authority):
        self.clock, self.authority = clock, authority
        self.delay = 3000
        self.elapsed = 0
        self.frame = None
        self.open = True
        self.events = []
        self.mutate = lambda x: x
        self.boundary = True
        self.error = 0
        self.ack_delay = 0
        self.ack_mutate = lambda x: x
        self.cleanup = Cleanup(True)
        self.wait_step = 100
    def observe(self):
        self.events.append(('observe', self.open))
        if self.elapsed < self.delay:
            return Observation('pending')
        if self.frame is None:
            self.frame = issue_frame(self.authority, POLICY)
        return Observation('ready', self.mutate(self.frame), self.boundary, self.error)
    def wait(self):
        self.events.append(('wait', self.open))
        self.clock.advance(self.wait_step); self.elapsed += self.wait_step
    def ack(self, raw, remaining):
        self.events.append(('ack', self.open, remaining))
        self.clock.advance(self.ack_delay)
        return Observation('written', self.ack_mutate(raw), True)
    def finish(self):
        self.events.append(('finish', self.open))
        if self.cleanup.closed and not self.cleanup.pending_retained:
            self.open = False
        return self.cleanup


class Lifecycle060Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.clock = Clock()
        self.guards = 0
        self.guard_action = lambda: True
        def guard():
            self.guards += 1
            return self.guard_action()
        self.guard = guard
        self.path = Path(self.tmp.name)/'phase.json'
        self.authority = start_authority(self.path, POLICY, self.clock, self.guard, lambda r: True)
        self.channel = Channel(self.clock, self.authority)
        self.loop = OfflineLifecycle(POLICY, self.clock, self.guard)
    def run_model(self):
        return self.loop.run(self.channel)
    def rejected(self, reason=None):
        result = self.run_model()
        self.assertFalse(result['completed'])
        if reason is not None:
            self.assertEqual(result['reason'], reason)
        return result
    def test_delayed_guards_keep_handle_alive_until_ack(self):
        for delay in (2800, 3000, 3200):
            with self.subTest(delay=delay), TemporaryDirectory() as tmp:
                clock = Clock()
                authority = start_authority(Path(tmp)/'phase', POLICY, clock, lambda: True, lambda r: True)
                channel = Channel(clock, authority); channel.delay = delay
                result = OfflineLifecycle(POLICY, clock, lambda: True).run(channel)
                self.assertTrue(result['completed'])
                self.assertTrue(all(e[1] for e in channel.events))
                self.assertEqual(channel.events[-2][0], 'ack')
                self.assertEqual(channel.events[-2][2], 2000)
                self.assertEqual(authority.summary()['permissions_consumed'], 1)
    def test_real_issuer_guard_latency_precedes_receipt(self):
        # Expensive guard work is inside unchanged047 issuer, before issuance.
        self.guard_action = lambda: (self.clock.advance(800) or True)
        result = self.run_model()
        self.assertTrue(result['completed'])
        self.assertEqual(self.channel.events[-2][2], 1200)
        self.assertGreater(self.clock.boot, 106000)
    def test_early_zero_is_failure_without_retry(self):
        self.channel.mutate = lambda x: b''
        self.rejected('frame_length_rejected')
        self.assertEqual(sum(e[0]=='observe' for e in self.channel.events), 31)
        self.assertFalse(any(e[0]=='ack' for e in self.channel.events))
    def test_unclassified_positive_read_error_stays_other(self):
        self.channel.error = 9001
        self.rejected('read_error')
        self.assertEqual(native_error(9001), 6)
    def test_disconnect_before_issue_spends_no_permission(self):
        self.channel.observe = lambda: Observation('disconnected')
        self.rejected('peer_disconnected')
        self.assertEqual(self.authority.summary()['permissions_consumed'], 0)
    def test_disconnect_after_issue_does_not_refund(self):
        def lost():
            issue_frame(self.authority, POLICY)
            return Observation('disconnected')
        self.channel.observe = lost
        self.rejected('peer_disconnected')
        self.assertEqual(self.authority.summary()['permissions_consumed'], 1)
    def test_partial_frame_rejected(self):
        self.channel.mutate = lambda x: x[:83]
        self.rejected('frame_length_rejected')
    def test_extra_frame_rejected(self):
        self.channel.mutate = lambda x: x+b'x'
        self.rejected('frame_length_rejected')
    def test_unread_suffix_requires_independent_boundary_proof(self):
        self.channel.boundary = False  # Returned84 alone cannot prove suffix absent.
        self.rejected('frame_boundary_unproven')
    def test_lost_ack_rejects_without_retry(self):
        self.channel.ack_mutate = lambda x: b''
        self.rejected('ack_unconfirmed')
        self.assertEqual(sum(e[0]=='ack' for e in self.channel.events), 1)
        self.assertEqual(self.authority.summary()['permissions_consumed'], 1)
    def test_wrong_ack_binding_rejected(self):
        self.channel.ack_mutate = lambda x: x[:-1]+bytes([x[-1]^1])
        self.rejected('ack_unconfirmed')
    def test_reply_write_failure_redacted(self):
        def fail(*args): raise RuntimeError('private login and server')
        self.channel.ack = fail
        result = self.rejected('operation_failed_details_redacted')
        self.assertNotIn('login', json.dumps(result))
    def test_read_failure_redacted(self):
        def fail(): raise RuntimeError('private account identifier')
        self.channel.observe = fail
        self.rejected('operation_failed_details_redacted')
    def test_event_close_failure_cannot_pass(self):
        self.channel.cleanup = Cleanup(False)
        self.rejected('cleanup_unconfirmed')
    def test_undrained_pending_memory_retains_handle(self):
        self.channel.cleanup = Cleanup(False, True)
        result = self.rejected('cleanup_unconfirmed')
        self.assertTrue(result['pending_retained']); self.assertTrue(self.channel.open)
    def test_cleanup_exception_redacted(self):
        def fail(): raise RuntimeError('secret process session')
        self.channel.finish = fail
        self.rejected('cleanup_failed_details_redacted')
    def test_repeat_request_unavailable_even_after_failure(self):
        self.channel.mutate = lambda x: b''
        self.rejected()
        with self.assertRaisesRegex(PipeRejected, '^request_unavailable$'):
            self.run_model()
    def test_restart_cannot_reuse_phase_reservation(self):
        self.run_model()
        with self.assertRaisesRegex(PermitRejected, '^reservation_unavailable_or_already_exists$'):
            start_authority(self.path, POLICY, self.clock, self.guard, lambda r: True)
    def test_clock_reversal_during_read_rejected(self):
        self.clock.advance(1)  # Keep reversal inside the valid nonnegative domain.
        def read():
            self.clock.mono -= 1
            return Observation('pending')
        self.channel.observe = read
        self.rejected('clock_reversed')
    def test_clock_discontinuity_rejected(self):
        self.clock.utc += 1001
        self.rejected('clock_discontinuity')
    def test_session_wait_does_not_extend_900_seconds(self):
        self.channel.delay = 900000; self.channel.wait_step = 900000
        self.rejected('session_expired')
        self.assertEqual(self.authority.summary()['permissions_consumed'], 0)
    def test_expired_receipt_after_read_guard_rejected(self):
        def guard():
            if self.channel.frame is not None: self.clock.advance(2000)
            return True
        self.guard_action = guard
        self.rejected('validation_failed_details_redacted')
    def test_ack_blocking_overrun_detected_only_after_return(self):
        self.channel.ack_delay = 2000
        self.rejected('receipt_expired')
        self.assertFalse(self.channel.open)
    def test_ack_final_guard_expiry_rejected(self):
        def guard():
            if any(e[0]=='ack' for e in self.channel.events): self.clock.advance(2000)
            return True
        self.guard_action = guard
        self.rejected('receipt_expired')
    def test_ack_uses_remaining_deadline_not_new_two_seconds(self):
        def guard():
            if self.channel.frame is not None: self.clock.advance(700)
            return True
        self.guard_action = guard
        self.channel.ack_delay = 500
        self.assertTrue(self.run_model()['completed'])
        self.assertEqual(self.channel.events[-2][2], 1300)
    def test_actual_guard_failure_before_ack_rejected(self):
        self.guard_action = lambda: self.channel.frame is None
        self.rejected('validation_failed_details_redacted')
        self.assertFalse(any(e[0]=='ack' for e in self.channel.events))
    def test_phase_and_policy_binding_stays_frozen(self):
        self.channel.mutate = lambda x: x[:8]+b'\x01'*16+x[24:]
        self.rejected('validation_failed_details_redacted')
    def test_pending_cannot_carry_unvalidated_data(self):
        self.channel.observe = lambda: Observation('pending', b'x')
        self.rejected('pending_observation_rejected')
    def test_invalid_native_codes_remain_unknown(self):
        for value in (True, None, -1, 2**31, 'private'):
            self.assertEqual(native_error(value), 7)
        self.assertEqual(native_error(5028), 6)
    def test_catalogue_differential_actual_pure_header(self):
        codes = [-1, 0, *range(5001, 5028), 5028, 9001, 2147483647]
        with TemporaryDirectory() as tmp:
            exe = Path(tmp)/'readiness060'
            subprocess.run(['g++','-std=c++17',str(ROOT/'mt5/Tests/CaptureReadiness060.cpp'),'-o',str(exe)],check=True,capture_output=True)
            proc = subprocess.run([str(exe)], input=''.join(f'{c}\n' for c in codes),text=True,capture_output=True,check=True)
        self.assertEqual(list(map(int,proc.stdout.split())), [native_error(c) for c in codes])
        self.assertEqual(len(codes),32)
        self.assertEqual(len(set(MQL_ERRORS.values())),27)
    def test_schema_errors_do_not_export_private_payload(self):
        self.channel.observe = lambda: Observation('ready','private login')
        result = self.rejected('observation_rejected')
        self.assertNotIn('login',json.dumps(result))
    def test_cleanup_malformed_status_cannot_pass(self):
        self.channel.cleanup = Cleanup(True, 1)
        self.rejected('cleanup_failed_details_redacted')
    def test_cleanup_overrun_prevents_success(self):
        def finish():
            self.clock.advance(2000)
            return Cleanup(True)
        self.channel.finish = finish
        self.rejected('cleanup_failed_details_redacted')
    def test_pending_spin_has_fixed_budget_with_frozen_clock(self):
        self.channel.observe = lambda: Observation('pending')
        self.channel.wait = lambda: None
        result = self.rejected('poll_budget_exhausted')
        self.assertEqual(result['polls'], 900001)
    def test_ack_monotonic_deadline_independent_of_tolerated_clock_skew(self):
        def ack(raw, remaining):
            self.clock.utc += 1000; self.clock.boot += 1000; self.clock.mono += 2000000000
            return Observation('written', raw, True)
        self.channel.ack = ack
        self.rejected('receipt_expired')
