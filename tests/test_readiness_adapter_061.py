from dataclasses import replace
import json
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
import unittest

from forex_demo_lab.capture_budget_047 import Policy, VERSION, private_guard, start_authority, PermitRejected
from forex_demo_lab.capture_wire_047 import encode_response
from forex_demo_lab.readiness_adapter_061 import *
from forex_demo_lab.transport_lifecycle_060 import Cleanup, issue_frame
from test_fresh_data_031 import API as AccountAPI
from test_transport_lifecycle_060 import Clock

ROOT = Path(__file__).resolve().parents[1]
POLICY = Policy('61'*16,'61'*32)  # Synthetic: no native phase/reservation.
FRAME = encode_response(dict(version=VERSION,phase=POLICY.phase,policy_sha256=POLICY.digest,
    permission=1,issued_boot_ms=100000,expires_boot_ms=102000,expires_utc_ms=1791352802000))


class FileModel:
    """Injected regular-file sharing evidence. No native file or pipe handles."""
    def __init__(self):
        self.data = FRAME; self.sizes = []; self.reads = []
        self.pos = 0; self.error = 0
        self.snap = Snapshot(b'synthetic-fileid',writers_excluded=True,deletion_excluded=True,
                             sandbox_verified=True,owner_verified=True,reparse_rejected=True)
        self.on_read = self.on_size = self.on_snapshot = None
        self.snapshot_calls = 0
    def availability(self):
        if self.on_size: self.on_size(self)
        return Availability(self.sizes.pop(0) if self.sizes else len(self.data), self.error)
    def read(self, requested):
        self.reads.append(requested)
        raw = self.data[:requested]; self.pos = len(raw)
        if self.on_read: self.on_read(self)
        return Read(raw,len(raw),self.error)
    def snapshot(self):
        self.snapshot_calls += 1
        if self.on_snapshot: self.on_snapshot(self)
        return replace(self.snap,position=self.pos)
    def append(self, raw):
        # Both directions of sharing compatibility must hold.
        if not sharing_compatible(1,1,2,1): return False
        self.data += raw
        return True


class Adapter061Tests(unittest.TestCase):
    def setUp(self):
        self.clock=Clock();self.file=FileModel();self.guard=lambda:True
        self.reader=ReadinessAdapter061('regular',self.file,POLICY,self.clock,self.guard)
    def rejected(self, reason, reader=None):
        with self.assertRaisesRegex(PipeRejected,'^'+reason+'$'):
            (reader or self.reader).observe()
    def test_regular_exact_snapshot_has_boundary_in_model(self):
        result=self.reader.observe()
        self.assertEqual(result,Observation('ready',FRAME,True))
        self.assertEqual(self.file.reads,[84]); self.assertEqual(self.file.snapshot_calls,2)
        self.assertFalse(self.reader.report()['native_adapter_ready'])
    def test_pipe_exact84_diagnostic_cannot_claim_boundary(self):
        reader=ReadinessAdapter061('pipe',self.file,POLICY,self.clock,self.guard)
        result=reader.observe()
        self.assertFalse(result.boundary); self.assertEqual(self.file.reads,[85])
    def test_availability0_is_pending_and_no_consumption(self):
        self.file.sizes=[0]
        self.assertEqual(self.reader.observe(),Observation('pending'))
        self.assertEqual(self.file.reads,[])
    def test_partial_availability_waits_without_partial_accumulation(self):
        self.file.sizes=[1,83,84,84]
        self.assertEqual(self.reader.observe().status,'pending')
        self.assertEqual(self.reader.observe().status,'pending')
        self.assertTrue(self.reader.observe().boundary)
        self.assertEqual(self.file.reads,[84])
    def test_extra_available_bytes_rejected_before_read(self):
        self.file.data=FRAME+b'x'
        self.rejected('extra_bytes_observed');self.assertEqual(self.file.reads,[])
    def test_delayed_suffix_between_snapshot_and_guard_rejected(self):
        self.file.sizes=[84,85]
        self.rejected('extra_bytes_observed');self.assertEqual(self.file.reads,[])
    def test_stale_readiness_becomes_empty_rejected(self):
        self.file.sizes=[84,0]
        self.rejected('readiness_changed')
    def test_pipe_suffix_arrives_after_size_before_read_rejected(self):
        self.file.sizes=[84,84]; self.file.data=FRAME+b'x'
        reader=ReadinessAdapter061('pipe',self.file,POLICY,self.clock,self.guard)
        self.rejected('read_length_rejected',reader)
    def test_pipe_later_suffix_not_hidden_as_complete_message(self):
        self.file.on_read=lambda f:setattr(f,'data',f.data+b'x')
        reader=ReadinessAdapter061('pipe',self.file,POLICY,self.clock,self.guard)
        self.assertFalse(reader.observe().boundary)
        self.assertEqual(len(self.file.data),85)
    def test_regular_future_append_denied_by_model_contract(self):
        attempts=[]
        self.file.on_read=lambda f:attempts.append(f.append(b'x'))
        self.assertTrue(self.reader.observe().boundary)
        self.assertEqual(attempts,[False]);self.assertEqual(len(self.file.data),84)
    def test_regular_snapshot_proof_defaults_to_unavailable(self):
        self.file.snap=Snapshot(b'synthetic-fileid')
        self.rejected('snapshot_boundary_unproven');self.assertEqual(self.file.reads,[])
    def test_each_missing_lock_path_owner_proof_rejected(self):
        for name in ('writers_excluded','deletion_excluded','sandbox_verified','owner_verified','reparse_rejected'):
            reader=ReadinessAdapter061('regular',self.file,POLICY,self.clock,self.guard)
            old=self.file.snap; self.file.snap=replace(old,**{name:False})
            self.rejected('snapshot_boundary_unproven',reader);self.file.snap=old
    def test_pipe_cannot_be_relabeled_regular_snapshot(self):
        self.file.snap=replace(self.file.snap,kind='pipe')
        self.rejected('snapshot_boundary_unproven')
    def test_identity_replacement_during_read_rejected(self):
        self.file.on_read=lambda f:setattr(f,'snap',replace(f.snap,identity=b'replaced-file-id'))
        self.rejected('snapshot_identity_changed')
    def test_size_change_after_read_rejected(self):
        self.file.on_read=lambda f:setattr(f,'snap',replace(f.snap,size=85))
        self.rejected('snapshot_boundary_unproven')
    def test_lock_loss_after_guard_rejected(self):
        self.file.on_read=lambda f:setattr(f,'snap',replace(f.snap,writers_excluded=False))
        self.rejected('snapshot_boundary_unproven')
    def test_zero_read_is_failure_without_retry(self):
        self.file.read=lambda n:Read(b'',0)
        self.rejected('read_length_rejected')
        self.rejected('consumption_unavailable')
    def test_partial_read_rejected_without_retry(self):
        self.file.read=lambda n:Read(FRAME[:20],20)
        self.rejected('read_length_rejected')
    def test_read_error_even_with_full_bytes_rejected(self):
        self.file.read=lambda n:Read(FRAME,84,5015)
        self.rejected('read_error')
        self.assertEqual(self.reader.report()['events'][-1]['error_category'],5)
    def test_disconnect_availability_error_not_wait(self):
        self.file.error=5007
        self.rejected('availability_error');self.assertEqual(self.file.reads,[])
    def test_unknown_open_error_not_guessed_missing_file(self):
        self.file.error=5004
        self.rejected('availability_error')
    def test_read_exception_redacted_and_attempt_burned(self):
        def fail(n): raise RuntimeError('private account identifier')
        self.file.read=fail
        self.rejected('adapter_operation_failed_details_redacted')
        self.rejected('consumption_unavailable')
        self.assertNotIn('identifier',json.dumps(self.reader.report()))
    def test_failed_availability_latches_session(self):
        self.file.error=9001
        self.rejected('availability_error');self.file.error=0
        self.rejected('consumption_unavailable')
    def test_probe_count_limits_frozen_clock(self):
        self.file.data=b''
        for _ in range(901): self.assertEqual(self.reader.observe().status,'pending')
        self.rejected('probe_budget_exhausted')
    def test_session_elapsed_not_reset_each_poll(self):
        self.file.data=b'';self.reader.observe();self.clock.advance(900000)
        self.rejected('session_expired')
    def test_blocking_call_overrun_detected_after_return(self):
        self.file.on_size=lambda f:self.clock.advance(900000)
        self.rejected('session_expired')
    def test_clock_reversal_after_call_rejected(self):
        self.clock.advance(1)
        self.file.on_size=lambda f:setattr(self.clock,'mono',self.clock.mono-1)
        self.rejected('clock_reversed')
    def test_actual_account_modes_rejected_with_demo_named_server(self):
        for mode in (1,2,7,False):
            account=AccountAPI();account.account.trade_mode=mode;account.account.server='demo-looking-name'
            with self.assertRaises(PermitRejected):private_guard(account)
    def test_actual_currency_and_algo_rejected(self):
        for attr,value,obj in (('currency','EUR','account'),('trade_allowed',True,'terminal')):
            account=AccountAPI();setattr(getattr(account,obj),attr,value)
            with self.assertRaises(PermitRejected):private_guard(account)
    def test_private_identity_change_between_availability_and_read_rejected(self):
        account=AccountAPI();guard=private_guard(account)
        self.file.on_size=lambda f:setattr(account.account,'server','changed-private-server')
        reader=ReadinessAdapter061('regular',self.file,POLICY,self.clock,guard)
        with self.assertRaises(PermitRejected): reader.observe()
        self.assertEqual(self.file.reads,[])
    def test_malformed_boolean_count_size_or_lock_rejected(self):
        for value in (Availability(True),Availability(-1),Availability(84,True)):
            self.file.availability=lambda:value
            reader=ReadinessAdapter061('regular',self.file,POLICY,self.clock,self.guard)
            self.rejected('availability_schema_rejected',reader)
        self.file.availability=lambda:Availability(84)
        self.file.snap=replace(self.file.snap,writers_excluded=1)
        self.rejected('snapshot_boundary_unproven')
    def test_sharing_contract_checks_both_directions(self):
        self.assertTrue(sharing_compatible(1,1,1,1))
        self.assertFalse(sharing_compatible(1,1,2,1))  # Future writer blocked.
        self.assertFalse(sharing_compatible(2,3,1,1))  # Existing writer blocks lock.
        self.assertFalse(sharing_compatible(1,1,4,1))  # Delete/replace blocked.
        self.assertTrue(sharing_compatible(1,3,2,3))  # Sharing-write is insufficient.
        for value in (True,-1,8,None):self.assertFalse(sharing_compatible(value,1,1,1))
    def test_report_excludes_identity_bytes(self):
        self.reader.observe();text=json.dumps(self.reader.report())
        self.assertNotIn('synthetic-fileid',text);self.assertNotIn('identity',text)
        self.assertEqual(self.reader.report()['orders'],0)
    def test_pure_mql_decisions_match_python(self):
        cases=[(s,0,a,t) for s in (0,83,84,85,128) for a,t in ((1,0),(901,899999999),(902,0),(1,900000000))]
        cases += [(84,e,1,0) for e in (-1,5004,5007,5015,9001)]
        cases += [(-1,0,1,0),(84,0,0,0),(84,0,1,-1)]
        with TemporaryDirectory() as tmp:
            exe=Path(tmp)/'readiness061'
            subprocess.run(['g++','-std=c++17','-Wall','-Wextra','-Werror',str(ROOT/'mt5/Tests/CaptureReadiness061.cpp'),'-o',str(exe)],check=True,capture_output=True,timeout=30)
            p=subprocess.run([str(exe)],input=''.join(' '.join(map(str,c))+'\n' for c in cases),capture_output=True,text=True,check=True,timeout=5)
        self.assertEqual(list(map(int,p.stdout.split())),[readiness_decision(*c) for c in cases])
        self.assertEqual(len(cases),28)
    def test_regular_candidate_integrates_with_remaining_deadline_ack(self):
        with TemporaryDirectory() as tmp:
            authority=start_authority(Path(tmp)/'phase',POLICY,self.clock,self.guard,lambda r:True)
            original_size=self.file.availability
            def published_size():
                if self.clock.boot < 103000:return Availability(0)
                if not hasattr(self.file,'published'):
                    self.file.data=issue_frame(authority,POLICY);self.file.published=True
                return original_size()
            self.file.availability=published_size
            channel=type('Channel',(),{})()
            channel.observe=self.reader.observe
            channel.wait=lambda:self.clock.advance(1000)
            channel.ack=lambda raw,remaining:Observation('written',raw,True)
            channel.finish=lambda:Cleanup(True)
            result=OfflineLifecycle(POLICY,self.clock,self.guard).run(channel)
            self.assertTrue(result['completed']);self.assertEqual(result['polls'],4)
            self.assertEqual(authority.summary()['permissions_consumed'],1)
            self.assertEqual(self.file.reads,[84])
    def test_lifecycle_refuses_pipe_diagnostic_boundary(self):
        reader=ReadinessAdapter061('pipe',self.file,POLICY,self.clock,self.guard)
        channel=type('Channel',(),{})()
        channel.observe=reader.observe;channel.wait=lambda:None
        channel.ack=lambda *args:self.fail('No ACK for unproven boundary')
        channel.finish=lambda:Cleanup(True)
        result=OfflineLifecycle(POLICY,self.clock,self.guard).run(channel)
        self.assertFalse(result['completed']);self.assertEqual(result['reason'],'frame_boundary_unproven')
