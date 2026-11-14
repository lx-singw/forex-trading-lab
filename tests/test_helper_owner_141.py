"""Invented141 trace frames only; native process checks are a separate harness."""
import hashlib
import json
import unittest

from forex_demo_lab import helper_owner_141 as owner
from forex_demo_lab.paired_replay_133 import canonical, DENIED


def fixture():
    state = dict(Schema=owner.SCHEMA, Job='a' * 32, Sequence=0, Previous='0' * 64,
                 Event='', ElapsedMs=0, HelperPid=0, Contained=False, Ready=False, InventedPending=False)
    rows = []
    for i, event in enumerate(['owner_started','child_created_suspended','child_resumed','helper_ready',
                               'invented_triple_begin','invented_triple_abort','owner_stopped']):
        state = dict(state, Sequence=i+1, Event=event, ElapsedMs=i*100)
        if event == 'child_created_suspended': state.update(HelperPid=42, Contained=True)
        if event == 'helper_ready': state['Ready'] = True
        if event == 'invented_triple_begin': state['InventedPending'] = True
        if event == 'invented_triple_abort': state['InventedPending'] = False
        rows.append(dict(state))
    return rows


def encode(rows):
    head = owner.ZERO; output = []
    for row in rows:
        row = dict(row, Previous=head)
        payload = canonical(row); head = hashlib.sha256(payload).hexdigest()
        output.append(payload+b'\t'+head.encode()+b'\n')
    return b''.join(output)


class HelperOwner141Tests(unittest.TestCase):
    def test_full_trace_and_all_complete_prefixes_never_grant_resume(self):
        rows = fixture()
        for end in range(1, len(rows)+1):
            r = owner.inspect_bytes(encode(rows[:end]))
            self.assertEqual(r['valid_frames'], end)
            self.assertEqual(r['owner_stopped_record_present'], end == 7)
            self.assertEqual(r['invented_pending'], end == 5)
            self.assertFalse(r['resume_available'])
            self.assertFalse(r['actual_process_exit_proven_by_trace'])
            for key, value in DENIED.items(): self.assertEqual(r[key], value)

    def test_suspended_owner_crash_prefix_cannot_imply_power_activation(self):
        r = owner.inspect_bytes(encode(fixture()[:2]))
        self.assertTrue(r['child_created']); self.assertFalse(r['child_resumed'])
        self.assertFalse(r['readiness_ack_recorded']); self.assertFalse(r['invented_pending'])
        self.assertIsNone(r['cause_of_unclosed_prefix'])

    def test_partial_final_frame_is_quarantined_and_no_stop_is_invented(self):
        raw = encode(fixture()[:5])
        r = owner.inspect_bytes(raw+b'{"Schema":')
        self.assertTrue(r['invented_pending']); self.assertGreater(r['truncated_tail_bytes'], 0)
        self.assertFalse(r['owner_stopped_record_present'])
        with self.assertRaises(ValueError): owner.inspect_bytes(encode(fixture())+b'tail')

    def test_digest_corruption_and_rehashed_illegal_order_rejected(self):
        with self.assertRaises(ValueError): owner.inspect_bytes(encode(fixture()).replace(b'helper_ready',b'helper_wrong',1))
        for field, value in [('Event','invented_triple_begin'),('Ready',True),('HelperPid',99),('Sequence',True),('ElapsedMs',-1)]:
            rows = fixture(); rows[2][field] = value
            with self.assertRaises(ValueError): owner.inspect_bytes(encode(rows))

    def test_pending_cannot_be_discarded_by_a_rehashed_stopped_frame(self):
        rows = fixture()[:5]; stop = dict(fixture()[-1], Sequence=6)
        with self.assertRaises(ValueError): owner.inspect_bytes(encode(rows+[stop]))

    def test_foreign_job_unknown_fields_wrong_types_and_extra_frames_rejected(self):
        for change in [dict(Job='b'*32),dict(Contained=1),dict(untrusted_field=True),dict(Schema='market'),dict(ElapsedMs=0.1)]:
            rows = fixture(); rows[3].update(change)
            with self.assertRaises(ValueError): owner.inspect_bytes(encode(rows))
        rows = fixture(); rows.append(dict(rows[-1],Sequence=8))
        with self.assertRaises(ValueError): owner.inspect_bytes(encode(rows))

    def test_empty_oversize_or_newline_injection_rejected(self):
        for raw in (b'', b'x'*(owner.MAX_BYTES+1), b'\n', b'x'*owner.MAX_FRAME+b'\n'):
            with self.assertRaises(ValueError): owner.inspect_bytes(raw)

    def test_json_duplicate_field_is_not_accepted_even_with_valid_hash(self):
        row = fixture()[0]
        payload = json.dumps(row,separators=(',',':')).encode().replace(b'"HelperPid":0',b'"HelperPid":0,"HelperPid":0')
        raw = payload+b'\t'+hashlib.sha256(payload).hexdigest().encode()+b'\n'
        with self.assertRaises(ValueError): owner.inspect_bytes(raw)


if __name__ == '__main__': unittest.main()
