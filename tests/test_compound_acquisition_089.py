from collections import Counter
from dataclasses import replace
import ctypes as C
import hashlib
from pathlib import PureWindowsPath
import struct
import unittest

from forex_demo_lab.compound_acquisition_089 import *
from forex_demo_lab.synchronization_083 import LIMITS
from forex_demo_lab.windows_adapter_086 import NATIVE_CAPS
from test_acquisition_review_088 import World088, MUTATIONS
from test_native_bindings_087 import fixture087, model_guard087, ROOT
from test_windows_adapter_086 import Table, SID


def sd089(control=0x9004):
    acl=struct.pack('<BBHHH',2,0,16+len(SID),1,0)+struct.pack('<BBHI',0,3,8+len(SID),0x1f01ff)+SID
    return struct.pack('<BBHIIII',1,0,control,20,0,0,20+len(SID))+SID+acl


class World089(World088):
    def __init__(self,owner,c,**cfg):
        super().__init__(owner,c,cfg.get('mutation'));self.cfg=cfg
        self.inspection_calls=[];self.metadata_security_handles=[];self.control_fact_reads=0
        self.begin_chains=self.end_chains=0;self.owned_controls=set()
    def mutate(self):
        if len(self.inspection_calls)+1<self.cfg.get('mutation_at_inspection',1):return
        if self.mutation=='source_change' and self.cfg.get('new_source_only') and not self.changed:
            self.changed=True;self.mutation_count+=1;self.owner.reader.hashes[self.source_path]='0'*64
        else:super().mutate()
    def call(self,n,*a):
        self.c.advance(self.cfg.get('api_latency',0))
        was_control=n=='CloseHandle' and a[0] in self.owned_controls
        if n=='GetKernelObjectSecurity':
            self.call_names.append(n);h,mask,buf,size,needed=a
            assert mask==5 and size==65536 and h in self.handles
            # Demonstrate that DELETE-only handles cannot supply this query.
            self.metadata_security_handles.append(h);assert h not in self.owned_controls
            control=4 if self.inspect_active and self.mutation=='acl_change' else 0x9004
            raw=self.cfg.get('security_raw',sd089(control))
            if self.cfg.get('needed_overflow'):self.pointer(needed,65537);self.error=122;return 0
            self.pointer(needed,len(raw));C.memmove(buf,raw,len(raw))
            if self.inspect_active and self.handles[h]==self.b.root:
                self.mutate()
                if self.mutation=='source_change':self.owner.reader.hashes[self.source_path]='0'*64
                if self.cfg.get('detach_clock'):self.api.clock=lambda:self.c()
            if self.inspect_active and self.mutation=='acl_change':self.changed=True;self.mutation_count=1
            if self.cfg.get('interrupt_security'):raise KeyboardInterrupt()
            return 1
        value=super().call(n,*a)
        if n=='CreateFileW' and a[1] in (WRITE,DELETE) and a[4]==3 and value!=C.c_void_p(-1).value:
            self.owned_controls.add(value)
            if self.cfg.get('control_substitution'):
                data,identity=self.snapshots[value];self.snapshots[value]=(data,(identity[0],identity[1]+1,identity[2]))
        if n=='GetFileInformationByHandle' and a[0] in self.owned_controls:self.control_fact_reads+=1
        if n=='CloseHandle':self.owned_controls.discard(a[0])
        if was_control and self.cfg.get('control_close_uncertain'):value=0
        return value


class AuditedAdapter089(Adapter089):
    def inspect(self,h):
        w=self.api.world;w.inspect_active=True;before=self.api.calls
        try:
            value=super().inspect(h);w.inspection_calls.append(self.api.calls-before);return value
        finally:w.inspect_active=False


def combined089(**cfg):
    owner,oldguard,runner,c=fixture087()
    legacy_count=None;legacy_cap=None
    if cfg.get('native_reader_hash_cap'):
        from forex_demo_lab.sharing_companion_065 import LIMITS as LEGACY_LIMITS
        legacy_count=[0];legacy_cap=LEGACY_LIMITS['hash_reads'];original_hash=owner.reader.hash_file
        def bounded_hash(path):
            require(legacy_count[0]<legacy_cap);legacy_count[0]+=1;return original_hash(path)
        owner.reader.hash_file=bounded_hash
    source_path=str(ROOT/SOURCE);source_hash=hashlib.sha256((ROOT/SOURCE).read_bytes()).hexdigest()
    owner.reader.hashes[source_path]=source_hash
    guard=Bridge089(owner,oldguard.boot,(source_path,source_hash))
    w=World089(owner,c,**cfg);w.source_path=source_path
    api=Api089(Table(w),Table(w),c,guard.boot,lambda:w.error,lambda v:setattr(w,'error',v));api.world=w
    w.api=api
    backend=AuditedAdapter089(api,w.b,guard,lambda ms:c.advance(ms))
    def factory(o,b):
        made=backend.factory(o,b);w.bound_b=made[2];return made
    t=Transport089(w.b,c,guard,factory);ok=False;reason=None
    try:
        if t.start(cfg.get('enabled',True)):
            for access in ('write','delete'):t.control('pre',access)
            t.wait_until(c.boot+300);deadline=c.boot+60000
            t.transaction('ready',deadline).close();t.transaction('release',deadline)
            t.transaction('holding',deadline).close();t.wait_until(t.hold_start+251)
            for access in ('write','delete'):t.control('independent',access)
            t.wait_until(t.hold_start+30251);t.transaction('closed',deadline).close()
            t.wait_until(t.hold_end+251)
            for access in ('write','delete'):t.control('post',access)
            ok=True
    except (Exception,KeyboardInterrupt) as e:
        reason=str(e) if str(e) in ('sync_clock_rejected','sync086_episode_clock_rejected','sync086_frame_rejected',
            'compound089_guard_rejected') else 'proof_or_budget_rejected'
    finally:
        if t.counts['cleanup']==0:ok=t.finish() and ok
        shutdown=owner.close()
    return dict(modeled_completed=ok,stop_reason=reason,summary=t.summary(),
        controls=t.probes,frame_kinds=[f.kind for f in t.frames],
        api_calls=api.calls,api_clock_samples=api.meter.counts['clock_samples'],
        bridge_clock_samples=owner.meter.counts['clock_samples'],
        bridge_calls=guard.calls,sdk_queries=guard.metadata.queries,boot_queries=runner.calls,
        hash_reads=len(owner.reader.hash_calls),inspection_call_counts=w.inspection_calls,
        native_reader_hash_cap=legacy_cap,
        bounded_reader_hash_reads=legacy_count[0] if legacy_count is not None else None,
        bounded_reader_scope='065_hash_count_only' if legacy_count is not None else None,
        raw_call_counts=dict(sorted(Counter(w.call_names).items())),
        control_fact_reads=w.control_fact_reads,blocked_controls=w.blocked_controls,
        mutation_injected=w.changed,remaining_handles=len(w.handles),remaining_allocations=len(w.buffers),
        unconfirmed_api_closes=api.unconfirmed,
        sdk_shutdown_attempts=owner.sdk.shutdowns,sdk_cleanup_confirmed=shutdown,
        source_checks=owner.reader.hash_calls.count(source_path),
        historical_fixture_date=PROTOTYPE_DATE,review_date=REVIEW_DATE,
        dependencies_injected=True,native_invocations=0,sdk_connections=0,
        market_reads=0,orders=0,runtime_authorized=False,orders_available=False,
        native_timing_proven=False,new_reader_implemented=False,new_runtime_admission=False)


class Compound089Tests(unittest.TestCase):
    def test_bounded_relative_security_descriptor_parses_equivalent_private_acl(self):
        r=relative_security089(sd089());check_security084(r,SID)
        self.assertEqual((r.owner,r.control,r.aces[0].mask),(SID,0x9004,0x1f01ff))
    def test_invalid_self_relative_offsets_overlap_truncation_revision_and_null_acl_reject(self):
        samples=[b'',sd089()[:19],sd089()[:-1],sd089(0x1004)]
        for offset,value in ((0,2),(1,1),(4,0),(4,19),(4,65535),(16,0),(16,20),(12,20)):
            raw=bytearray(sd089());width=1 if offset<2 else 4;raw[offset:offset+width]=value.to_bytes(width,'little');samples.append(bytes(raw))
        for raw in samples:
            with self.assertRaises(Exception):relative_security089(raw)
    def test_nonprivate_acl_still_rejected_by_original_security_validator(self):
        for offset in (28,32,36,40,44):
            raw=bytearray(sd089());raw[offset]^=1
            try:r=relative_security089(bytes(raw))
            except Exception:continue
            with self.assertRaises(Exception):check_security084(r,SID)
    def test_complete_raw_bridge_six_control_episode_fits_all_original_counts(self):
        r=combined089();self.assertTrue(r['modeled_completed'],r)
        self.assertEqual(len(r['controls']),6);self.assertEqual(r['frame_kinds'],[1,2,3,4])
        self.assertEqual((r['summary']['counts']['guards'],r['summary']['valid_guard_spans'],r['bridge_calls']),(38,38,38))
        self.assertLessEqual(r['api_clock_samples'],LIMITS['clock_samples'])
        self.assertLessEqual(r['bridge_clock_samples'],LIMITS['clock_samples'])
        self.assertLessEqual(r['api_calls'],NATIVE_CAPS['calls']);self.assertLessEqual(r['sdk_queries'],1024)
        self.assertLessEqual(r['boot_queries'],128)
        self.assertEqual((r['sdk_queries'],r['boot_queries']),(456,75))
        self.assertEqual(r['blocked_controls'],2);self.assertEqual(r['control_fact_reads'],8)
        self.assertEqual(set(r['inspection_call_counts']),{44,46})
        self.assertEqual(r['source_checks'],2*r['bridge_calls'])
        self.assertTrue(r['summary']['cleanup_confirmed']);self.assertTrue(r['sdk_cleanup_confirmed'])
        self.assertEqual((r['remaining_handles'],r['remaining_allocations'],r['sdk_shutdown_attempts']),(0,0,1))
    def rejects(self,**cfg):
        r=combined089(**cfg);self.assertFalse(r['modeled_completed'],r)
        self.assertEqual((r['remaining_handles'],r['remaining_allocations'],r['sdk_shutdown_attempts']),(0,0,1))
        self.assertTrue(r['sdk_cleanup_confirmed']);return r
    def test_mid_composite_file_replacement_rejects(self):self.assertTrue(self.rejects(mutation='file_replace')['mutation_injected'])
    def test_mid_composite_root_replacement_rejects(self):self.assertTrue(self.rejects(mutation='root_replace')['mutation_injected'])
    def test_mid_composite_ancestor_replacement_rejects(self):self.assertTrue(self.rejects(mutation='ancestor_replace')['mutation_injected'])
    def test_mid_composite_ancestor_reparse_rejects(self):self.assertTrue(self.rejects(mutation='ancestor_reparse')['mutation_injected'])
    def test_mid_composite_acl_change_rejects(self):self.assertTrue(self.rejects(mutation='acl_change')['mutation_injected'])
    def test_current_raw_peer_creation_change_rejects(self):self.assertTrue(self.rejects(mutation='peer_change')['mutation_injected'])
    def test_real_account_change_during_raw_acquisition_rejects(self):self.assertTrue(self.rejects(mutation='account_real')['mutation_injected'])
    def test_contest_account_change_during_raw_acquisition_rejects(self):self.assertTrue(self.rejects(mutation='account_contest')['mutation_injected'])
    def test_different_demo_account_during_raw_acquisition_rejects(self):self.assertTrue(self.rejects(mutation='account_change')['mutation_injected'])
    def test_source_changes_during_raw_acquisition_rejects_in_trailing_proof(self):
        r=self.rejects(mutation='source_change');self.assertTrue(r['mutation_injected']);self.assertEqual(r['summary']['valid_guard_spans'],1)
    def test_new_compound_source_alone_changes_during_raw_acquisition_rejects(self):
        r=self.rejects(mutation='source_change',new_source_only=True);self.assertTrue(r['mutation_injected'])
        self.assertEqual(r['summary']['valid_guard_spans'],1)
    def test_file_changed_after_open_is_reacquired_before_close(self):
        r=self.rejects(mutation='file_replace',mutation_at_inspection=4)
        self.assertTrue(r['mutation_injected']);self.assertEqual(r['summary']['valid_guard_spans'],4)
        self.assertEqual(len(r['controls']),0);self.assertGreaterEqual(r['control_fact_reads'],1)
    def test_substituted_control_handle_rejects_before_close_as_success(self):self.rejects(control_substitution=True)
    def test_oversized_security_result_rejects_without_retry_or_dynamic_buffer(self):self.rejects(needed_overflow=True)
    def test_security_interrupt_owned_cleanup_still_attempted_once(self):self.rejects(interrupt_security=True)
    def test_uncertain_close_never_claims_cleanup_success(self):
        r=self.rejects(control_close_uncertain=True);self.assertFalse(r['summary']['cleanup_confirmed'])
        self.assertGreater(r['summary']['unconfirmed_closes'],0)
        self.assertGreater(r['unconfirmed_api_closes'],0)
    def test_uncertain_creator_close_is_reported_by_raw_owner_and_cleanup_false(self):
        r=self.rejects(close_uncertain=True);self.assertFalse(r['summary']['cleanup_confirmed'])
        self.assertEqual(r['unconfirmed_api_closes'],1)
    def test_default_off_has_no_api_sdk_guard_invocations(self):
        r=combined089(enabled=False);self.assertFalse(r['modeled_completed'])
        self.assertEqual((r['api_calls'],r['bridge_calls'],r['sdk_queries'],r['source_checks']),(0,0,0,0))
    def test_nonzero_api_cost_is_measured_not_claimed_bounded(self):
        r=combined089(api_latency=1);self.assertTrue(r['modeled_completed'],r)
        self.assertLess(r['summary']['episode_elapsed_ms'],60000);self.assertFalse(r['native_timing_proven'])
    def test_slow_raw_api_rejects_instead_of_widening_windows(self):self.rejects(api_latency=100)
    def test_standalone_old_sdk_limit_stays_independent(self):
        r=model_guard087(repeat=True);self.assertEqual(r['sdk_queries'],1024);self.assertFalse(r['modeled_completed'])
    def test_existing_native_reader_hash_cap_rejects_even_when_raw_budget_fits(self):
        r=self.rejects(native_reader_hash_cap=True)
        self.assertEqual((r['native_reader_hash_cap'],r['bounded_reader_hash_reads']),(768,768))
        self.assertLess(r['api_clock_samples'],4096);self.assertLess(r['sdk_queries'],1024)
        self.assertLess(len(r['controls']),6)
    def test_nonscoped_nested_guard_and_reuse_after_failure_reject(self):
        o,g,r,c=fixture087();p=str(ROOT/SOURCE);h=hashlib.sha256((ROOT/SOURCE).read_bytes()).hexdigest();o.reader.hashes[p]=h
        b=Bridge089(o,g.boot,(p,h))
        with self.assertRaises(Exception):b()
        with self.assertRaises(Exception):b.acquire(lambda:b.acquire(lambda:None,lambda v:None),lambda v:None)
        self.assertFalse(b.active);self.assertTrue(b.stopped)
        with self.assertRaises(Exception):b.acquire(lambda:None,lambda v:None)
        o.close()
    def test_proofs_are_reacquired_per_scope_and_source_is_not_cached(self):
        o,g,r,c=fixture087();p=str(ROOT/SOURCE);h=hashlib.sha256((ROOT/SOURCE).read_bytes()).hexdigest();o.reader.hashes[p]=h
        b=Bridge089(o,g.boot,(p,h));b.acquire(lambda:None,lambda v:None);first=len(o.reader.hash_calls)
        b.acquire(lambda:None,lambda v:None);self.assertEqual(len(o.reader.hash_calls),2*first)
        o.reader.hashes[p]='0'*64
        with self.assertRaises(Exception):b.acquire(lambda:None,lambda v:None)
        o.close()
    def test_native_entry_and_frozen_date_still_unavailable(self):
        with self.assertRaises(Exception):native_entry089()
        from forex_demo_lab.synchronization_083 import Meter083
        from datetime import datetime,timezone
        ms=int(datetime(2026,10,9,tzinfo=timezone.utc).timestamp()*1000)
        with self.assertRaises(Exception):Meter083(lambda:(ms,0,100000))
    def test_cached_or_other_boot_callback_rejected_before_adapter_factory(self):
        o,g,r,c=fixture087();p=str(ROOT/SOURCE);h=hashlib.sha256((ROOT/SOURCE).read_bytes()).hexdigest();o.reader.hashes[p]=h
        b=Bridge089(o,g.boot,(p,h));w=World089(o,c)
        api=Api089(Table(w),Table(w),c,lambda:o.pins.peer.boot,lambda:w.error,lambda v:setattr(w,'error',v))
        with self.assertRaises(Exception):Adapter089(api,w.b,b,lambda ms:None)
        self.assertEqual(api.calls,0);o.close()
    def test_clock_callback_detached_during_acquisition_rejects_before_valid_span(self):
        r=self.rejects(detach_clock=True);self.assertEqual(r['summary']['valid_guard_spans'],1)


if __name__=='__main__':unittest.main()
