from dataclasses import replace
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from forex_demo_lab.capture_budget_047 import Policy, PermitRejected, private_guard, start_authority
from forex_demo_lab.publication_063 import FileProof, Publication063
from forex_demo_lab.readiness_adapter_061 import sharing_compatible
from forex_demo_lab.transport_lifecycle_060 import Cleanup
from forex_demo_lab.windows_pipe_047 import PipeRejected
from test_fresh_data_031 import API as AccountAPI
from test_transport_lifecycle_060 import Clock

POLICY = Policy('63'*16, '63'*32)  # Temporary offline reservation only.


class Files:
    """Independent injected file/share simulator. No Windows calls or IPC."""
    def __init__(self):
        self.files = {}; self.handles = {}; self.events = []; self.hooks = {}
        self.cleanup = Cleanup(True); self.finished = False
        self.proofs = {}; self.generation = 0

    def event(self, op, kind):
        self.events.append((op, kind))
        action = self.hooks.get((op, kind))
        if action: action(self)

    def open(self, kind, access, share):
        for h in self.handles.values():
            if h['kind'] == kind and not sharing_compatible(h['access'], h['share'], access, share):
                raise RuntimeError('private sharing error')
        token = object()
        self.handles[token] = dict(kind=kind, access=access, share=share, pos=0)
        return token

    def create_new(self, kind):
        self.event('create', kind)
        if kind in self.files: raise RuntimeError('private existing path')
        self.generation += 1
        self.files[kind] = dict(data=b'', identity=self.generation.to_bytes(16, 'little'))
        return self.open(kind, 3, 3)

    def write(self, handle, raw):
        h = self.handles[handle]; kind = h['kind']
        self.event('write', kind)
        self.files[kind]['data'] = raw; h['pos'] = len(raw)
        self.event('wrote', kind)
        return len(raw)

    def close_writer(self, handle):
        kind = self.handles[handle]['kind']; self.event('close', kind)
        del self.handles[handle]
        self.event('closed', kind)
        return True

    def acquire_seal(self, kind):
        self.event('seal', kind)
        return self.open(kind, 1, 1)

    def open_reader(self, kind):
        self.event('reader', kind)
        return self.open(kind, 1, 1)

    def snapshot(self, handle):
        h = self.handles[handle]; kind = h['kind']; self.event('snapshot', kind)
        f = self.files[kind]
        seal = any(x['kind'] == kind and x['share'] == 1 for x in self.handles.values())
        p = FileProof(f['identity'], len(f['data']), h['pos'],
                      True, True, True, True, True, seal, seal)
        return replace(p, **self.proofs.get(kind, {}))

    def read(self, handle, size):
        h = self.handles[handle]; kind = h['kind']; self.event('read', kind)
        raw = self.files[kind]['data'][h['pos']:h['pos']+size]; h['pos'] += len(raw)
        self.event('read_done', kind)
        return raw

    def attack(self, kind, access):
        try: self.open(kind, access, 7)
        except RuntimeError: return False
        return True

    def finish(self):
        self.finished = True
        if self.cleanup.closed and not self.cleanup.pending_retained: self.handles.clear()
        return self.cleanup


class Publication063Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name)/'phase'
        self.clock = Clock(); self.files = Files(); self.guard_calls = 0
        self.guard_action = lambda: True
        def guard():
            self.guard_calls += 1
            return self.guard_action()
        self.guard = guard
        self.authority = start_authority(self.path, POLICY, self.clock, self.guard, lambda r: True)
        self.engine = Publication063(self.files, self.authority, POLICY, self.clock, self.guard)

    def failure(self):
        r = self.engine.run()
        self.assertFalse(r['completed']); self.assertTrue(self.files.finished)
        self.assertTrue(self.authority.summary()['closed'])
        with self.assertRaisesRegex(PipeRejected, '^publication_unavailable$'): self.engine.run()
        return r

    def crash(self, op, kind='response'):
        def fail(f): raise RuntimeError('private account path SID')
        self.files.hooks[op, kind] = fail

    def test_complete_exact_response_ack_and_closed_handles(self):
        r = self.engine.run()
        self.assertTrue(r['completed']); self.assertEqual(r['reply_bytes'], 84)
        self.assertTrue(r['ack_written']); self.assertEqual(r['attempts']['reads'], 4)
        self.assertEqual(r['authority'], dict(permissions_consumed=1, closed=True))
        self.assertEqual(len(self.files.files['ack']['data']), 40)
        self.assertEqual(self.files.handles, {}); self.assertGreater(self.guard_calls, 40)

    def test_writer_closed_before_seal_and_reader(self):
        self.assertTrue(self.engine.run()['completed'])
        for kind in ('response', 'ack'):
            e = self.files.events
            self.assertLess(e.index(('closed', kind)), e.index(('seal', kind)))
            self.assertLess(e.index(('seal', kind)), e.index(('reader', kind)))

    def test_response_seal_blocks_suffix_during_ack(self):
        denied = []
        self.files.hooks['write', 'ack'] = lambda f: denied.append(f.attack('response', 2))
        self.assertTrue(self.engine.run()['completed']); self.assertEqual(denied, [False])

    def test_response_seal_blocks_delete_during_ack(self):
        denied = []
        self.files.hooks['read', 'ack'] = lambda f: denied.append(f.attack('response', 4))
        self.assertTrue(self.engine.run()['completed']); self.assertEqual(denied, [False, False])

    def test_ack_seal_blocks_future_writer(self):
        denied = []
        self.files.hooks['reader', 'ack'] = lambda f: denied.append(f.attack('ack', 2))
        self.assertTrue(self.engine.run()['completed']); self.assertEqual(denied, [False])

    def test_crash_before_creation_burns_issued_permission(self):
        self.crash('create'); self.assertEqual(self.failure()['authority']['permissions_consumed'], 1)

    def test_crash_before_write_no_reader(self):
        self.crash('write'); self.failure()
        self.assertNotIn(('reader', 'response'), self.files.events)

    def test_crash_after_write_closes_tracked_writer(self):
        self.crash('wrote'); self.failure(); self.assertEqual(self.files.handles, {})

    def test_crash_after_writer_close_never_publishes_reader(self):
        self.crash('closed'); self.failure()
        self.assertNotIn(('reader', 'response'), self.files.events)

    def test_crash_after_seal_before_reader(self):
        self.crash('reader'); self.failure(); self.assertEqual(self.files.handles, {})

    def test_lost_ack_no_refund(self):
        self.crash('create', 'ack'); r = self.failure()
        self.assertFalse(r['ack_written']); self.assertEqual(r['authority']['permissions_consumed'], 1)
        with self.assertRaisesRegex(PermitRejected, 'permission_unavailable'):
            self.authority.issue(POLICY.phase, POLICY.digest)

    def test_crash_after_ack_write_no_success(self):
        self.crash('wrote', 'ack'); self.failure()

    def test_restart_same_reservation_rejected(self):
        self.crash('write'); self.failure()
        with self.assertRaisesRegex(PermitRejected, 'reservation_unavailable_or_already_exists'):
            start_authority(self.path, POLICY, self.clock, self.guard, lambda r: True)

    def test_existing_response_never_overwritten(self):
        stale = dict(data=b'stale', identity=b'x'*16); self.files.files['response'] = stale.copy()
        self.failure(); self.assertEqual(self.files.files['response'], stale)

    def test_existing_ack_never_overwritten(self):
        self.files.files['ack'] = dict(data=b'old-ack', identity=b'y'*16)
        self.failure(); self.assertEqual(self.files.files['ack']['data'], b'old-ack')

    def test_replacement_in_close_seal_gap_rejected(self):
        self.files.hooks['closed', 'response'] = lambda f: f.files['response'].update(identity=b'z'*16)
        self.failure(); self.assertNotIn(('reader', 'response'), self.files.events)

    def test_reparse_owner_sandbox_and_link_proofs_required(self):
        # Direct validation is shared by writer, seal, peer and final checks.
        from forex_demo_lab.publication_063 import valid_proof
        p = FileProof(b'x'*16, 84, 0, True, True, True, True, True, True, True)
        for key in ('regular','owner','sandbox','no_reparse','single_link','write_excluded','delete_excluded'):
            for value in (False, 1):
                self.assertFalse(valid_proof(replace(p, **{key:value}), 84, 0, sealed=True))

    def test_reparse_change_after_writer_close_rejected(self):
        self.files.hooks['closed', 'response'] = lambda f: f.proofs.update(response=dict(no_reparse=False))
        self.failure()

    def test_retained_writer_prevents_seal(self):
        self.files.close_writer = lambda h: True   # Dishonest close assertion, actual writer still open.
        self.failure(); self.assertNotIn(('reader', 'response'), self.files.events)

    def test_partial_write_not_accumulated_or_retried(self):
        def partial(h, raw):
            self.files.files['response']['data'] = raw[:20]; return 20
        self.files.write = partial
        r = self.failure(); self.assertEqual(r['attempts']['writes'], 1)

    def test_boolean_write_count_rejected(self):
        self.files.write = lambda h, raw: True; self.failure()

    def test_delayed_suffix_before_seal_rejected(self):
        self.files.hooks['closed', 'response'] = lambda f: f.files['response'].update(data=f.files['response']['data']+b'x')
        self.failure()

    def test_same_length_corruption_after_close_rejected(self):
        self.files.hooks['closed', 'response'] = lambda f: f.files['response'].update(data=b'x'*84)
        self.failure()

    def test_read_zero_short_extra_and_wrong_bytes_rejected(self):
        from forex_demo_lab.publication_063 import valid_proof
        # Backend return is checked as bytes with exact equality, not byte count alone.
        for raw in (b'', b'x'*83, b'x'*85, b'x'*84):
            with TemporaryDirectory() as tmp:
                a = start_authority(Path(tmp)/'p', POLICY, self.clock, self.guard, lambda r: True)
                f = Files(); f.read = lambda h, size, data=raw: data
                e = Publication063(f, a, POLICY, self.clock, self.guard)
                self.assertFalse(e.run()['completed']); self.assertTrue(f.finished)
        self.assertFalse(valid_proof(FileProof(b'x'*16, True, 0), 84, 0))

    def test_identity_change_during_read_rejected(self):
        self.files.hooks['read_done', 'response'] = lambda f: f.files['response'].update(identity=b'q'*16)
        self.failure()

    def test_seal_loss_during_ack_rejected(self):
        self.files.hooks['wrote', 'ack'] = lambda f: f.proofs.update(response=dict(delete_excluded=False))
        self.failure()

    def test_wrong_phase_and_policy_receipts_rejected(self):
        for key, value in (('phase', '64'*16), ('policy_sha256', '64'*32)):
            with TemporaryDirectory() as tmp:
                a = start_authority(Path(tmp)/'p', POLICY, self.clock, self.guard, lambda r: True)
                original = a.issue
                def issue(phase, digest, k=key, v=value):
                    r = original(phase, digest); r[k] = v; return r
                a.issue = issue
                f = Files(); e = Publication063(f, a, POLICY, self.clock, self.guard)
                self.assertFalse(e.run()['completed']); self.assertNotIn(('create','ack'), f.events)

    def test_spent_authority_never_issues_second_receipt(self):
        self.authority.issue(POLICY.phase, POLICY.digest)
        r = self.failure(); self.assertEqual(r['attempts']['creates'], 0)

    def test_slow_full_guard_before_issue_keeps_900s_window(self):
        # Expensive guard before issuance does not eat a freshly issued receipt.
        count = [0]
        def guard():
            count[0] += 1
            if count[0] == 1: self.clock.advance(3000)
            return True
        self.guard_action = guard
        self.assertTrue(self.engine.run()['completed'])

    def test_session_expired_before_issue_no_permission(self):
        self.clock.advance(900000); r = self.failure()
        self.assertEqual(r['authority']['permissions_consumed'], 0)

    def test_delayed_publication_uses_original_two_second_receipt(self):
        self.files.hooks['write', 'response'] = lambda f: self.clock.advance(2000)
        r = self.failure(); self.assertNotIn(('create', 'ack'), self.files.events)
        self.assertEqual(r['authority']['permissions_consumed'], 1)

    def test_ack_overrun_detected_after_return_cleanup_runs(self):
        self.files.hooks['write', 'ack'] = lambda f: self.clock.advance(2000)
        r = self.failure(); self.assertFalse(r['ack_written']); self.assertEqual(self.files.handles, {})

    def test_clock_reverse_during_publication_rejected(self):
        self.clock.advance(1)
        self.files.hooks['write', 'response'] = lambda f: setattr(self.clock, 'mono', self.clock.mono-1)
        self.failure()

    def test_cleanup_uncertainty_blocks_success(self):
        self.files.cleanup = Cleanup(False, True)
        r = self.failure(); self.assertEqual(r['reason'], 'cleanup_unconfirmed')
        self.assertTrue(self.files.handles)

    def test_private_actual_account_guard_rechecked_after_close(self):
        account = AccountAPI(); guard = private_guard(account)
        self.engine.guard = guard; self.engine.timer.guard = guard
        self.files.hooks['closed', 'response'] = lambda f: setattr(account.account, 'trade_mode', 2)
        self.failure(); self.assertNotIn(('seal','response'), self.files.events)
        for mode in (1, 2):
            account.account.trade_mode = mode
            with self.assertRaises(PermitRejected): private_guard(account)

    def test_report_redacts_paths_identity_and_upstream_errors(self):
        self.crash('write'); r = self.failure(); s = json.dumps(r)
        for private in ('private account', 'SID', str(self.path), 'identity', 'files'):
            self.assertNotIn(private, s)
        self.assertEqual(r['quote_reads'], 0); self.assertEqual(r['orders'], 0)
        for key in ('native_publication_verified','native_mql_verified','orders_available','fresh_performance_eligible','annual_eligible'):
            self.assertIs(r[key], False)

    def test_ack_hash_mismatch_rejected_before_ack_creation(self):
        ack = self.engine.ack
        self.engine.ack = lambda raw, remaining: ack(raw[:8]+b'z'*32, remaining)
        self.failure(); self.assertNotIn(('create','ack'), self.files.events)

    def test_ack_remaining_time_not_restarted_or_boolean(self):
        ack = self.engine.ack
        self.engine.ack = lambda raw, remaining: ack(raw, True)
        self.failure(); self.assertNotIn(('create','ack'), self.files.events)

    def test_unconfirmed_writer_close_stops_before_seal(self):
        self.files.close_writer = lambda h: False
        self.failure(); self.assertNotIn(('seal','response'), self.files.events)

    def test_cleanup_overrun_cannot_keep_completed_true(self):
        finish = self.files.finish
        def delayed():
            self.clock.advance(2000); return finish()
        self.files.finish = delayed
        self.failure(); self.assertEqual(self.files.handles, {})

    def test_clock_discontinuity_before_seal_rejected(self):
        self.files.hooks['closed','response'] = lambda f: setattr(self.clock, 'utc', self.clock.utc+2001)
        self.failure(); self.assertNotIn(('seal','response'), self.files.events)

    def test_new_model_cannot_resume_closed_spent_authority(self):
        self.crash('wrote'); self.failure()
        other = Files(); e = Publication063(other, self.authority, POLICY, self.clock, self.guard)
        self.assertFalse(e.run()['completed']); self.assertEqual(other.files, {})
