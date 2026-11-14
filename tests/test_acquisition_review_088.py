from collections import Counter
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import PureWindowsPath
import ctypes as C
import unittest

from forex_demo_lab.acquisition_review_088 import *
from forex_demo_lab.synchronization_086 import Transport086
from forex_demo_lab.windows_adapter_086 import Api086, WindowsAdapter086
from test_native_bindings_087 import fixture087, model_guard087, ROOT
from test_synchronization_086 import run086_case
from test_windows_adapter_086 import World, Table


MUTATIONS=('file_replace','root_replace','ancestor_replace','ancestor_reparse',
    'acl_change','peer_change','account_real','account_contest','account_change','source_change')


class World088(World):
    """Historical Oct 8 model, with stable descriptor identities and fresh paths.

    Raw APIs remain Api086, with the original clock cap. This is a test fixture,
    not a new dated runtime. Sharing error32 is modeled only during the hold.
    """
    def __init__(self, owner, clock, mutation=None):
        super().__init__();self.c=clock;self.b=replace(self.b,peer=owner.pins.peer)
        self.owner=owner;self.mutation=mutation;self.inspect_active=False
        self.changed=False;self.snapshots={};self.sd_paths={};self.reparse=set()
        self.mutation_count=0;self.blocked_controls=0
    def mutate(self):
        if self.changed or self.mutation is None:return
        self.changed=True;self.mutation_count+=1
        paths={'file_replace':self.b.root+'\\synthetic.bin','root_replace':self.b.root,
            'ancestor_replace':str(PureWindowsPath(self.b.root).parent)}
        if self.mutation in paths:
            p=paths[self.mutation];data,i=self.files[p];self.files[p]=(data,(i[0],i[1]+1000,i[2]))
        elif self.mutation=='ancestor_reparse':self.reparse.add(str(PureWindowsPath(self.b.root).parent))
        elif self.mutation=='account_real':self.owner.sdk.account.trade_mode=2
        elif self.mutation=='account_contest':self.owner.sdk.account.trade_mode=1
        elif self.mutation=='account_change':self.owner.sdk.account.login=2
        elif self.mutation=='source_change':
            p=next(iter(self.owner.pins.sources.values()))[0];self.owner.reader.hashes[p]='0'*64
    def call(self,n,*a):
        if n=='CreateFileW' and a[1] in (0x40000000,0x10000) and a[4]==3:
            if self.hold and self.hold<=self.c.boot<self.hold+30000:
                self.call_names.append(n);self.error=32;self.blocked_controls+=1
                return C.c_void_p(-1).value
        if n=='GetFileInformationByHandle' and a[0] in self.snapshots:
            self.call_names.append(n);path=self.handles[a[0]];data,ident=self.snapshots[a[0]];f=a[1]._obj
            f.attributes=(0 if path.endswith('synthetic.bin') else 0x10)|(0x400 if path in self.reparse else 0)
            f.volume=ident[0];f.index_low=ident[1];f.created.low=ident[2];f.links=1;f.size_low=len(data)
            return 1
        value=super().call(n,*a)
        if n=='CreateFileW' and value and value!=C.c_void_p(-1).value:
            self.snapshots[value]=self.files[a[0]]
        if n=='WriteFile' and self.handles[a[0]]!='pipe':
            self.snapshots[a[0]]=self.files[self.handles[a[0]]]
        if n=='WriteFile' and self.handles[a[0]]=='pipe' and self.request[6]==2:self.c.advance(5)
        if n=='GetSecurityInfo':self.sd_paths[a[7]._obj.value]=self.handles[a[0]]
        if n=='LocalFree':self.sd_paths.pop(a[0].value,None)
        if self.inspect_active and n=='GetSecurityDescriptorControl' and self.sd_paths.get(a[0].value)==self.b.root:
            # Root facts and its complete ancestor walk have just been acquired.
            # Mutate now, before the next fresh root/path open in this composite.
            self.mutate()
        if self.inspect_active and self.mutation=='acl_change' and n=='GetSecurityDescriptorControl':
            self.changed=True;self.mutation_count=1;a[1]._obj.value=4
        if self.inspect_active and self.mutation=='peer_change' and n=='GetProcessTimes':
            self.changed=True;self.mutation_count=1;a[1]._obj.low=457
        return value


class AuditedAdapter088(WindowsAdapter086):
    def inspect(self,h):
        w=self.api.world;w.inspect_active=True;before=self.api.calls
        if w.mutation in ('account_real','account_contest','account_change','source_change'):w.mutate()
        try:
            result=super().inspect(h);self.inspection_calls.append(self.api.calls-before);return result
        finally:w.inspect_active=False


def combined088(mutation=None, enabled=True):
    owner,guard,runner,c=fixture087();w=World088(owner,c,mutation)
    api=Api086(Table(w),Table(w),c,guard.boot,lambda:w.error,lambda v:setattr(w,'error',v));api.world=w
    backend=AuditedAdapter088(api,w.b,guard,lambda ms:c.advance(ms));api.backend=backend;backend.inspection_calls=[]
    def factory(o,b):
        made=backend.factory(o,b);w.bound_b=made[2];return made
    t=Transport086(w.b,c,guard,factory);ok=False;reason=None;target_entered=False
    try:
        if t.start(enabled):
            target_entered=True
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
        reason=str(e) if str(e) in ('sync_clock_rejected','guard087_binding_rejected') else 'proof_rejected'
    finally:
        if t.counts['cleanup']==0:ok=t.finish() and ok
        shutdown=owner.close()
    return dict(modeled_completed=ok,default_off=not enabled,full_six_control_target_entered=target_entered,
        historical_model_date='2026-10-08',new_runtime_admission=False,
        stop_reason=reason,controls=len(t.probes),summary=t.summary(),
        api_calls=api.calls,api_clock_samples=api.meter.counts['clock_samples'],
        completed_inspection_call_counts=backend.inspection_calls,
        raw_call_counts=dict(sorted(Counter(w.call_names).items())),
        bridge_calls=guard.calls,sdk_queries=guard.metadata.queries,boot_queries=runner.calls,
        mutation_injected=w.changed,mutation_count=w.mutation_count,blocked_controls=w.blocked_controls,
        remaining_handles=len(w.handles),remaining_allocations=len(w.buffers),
        sdk_shutdown_attempts=owner.sdk.shutdowns,sdk_cleanup_confirmed=shutdown,
        scope='historical_raw_api_full_bridge_six_control_target',
        dependencies_injected=True,native_invocations=0,sdk_connections=0,
        market_reads=0,orders=0,runtime_authorized=False,orders_available=False)


def schedule088():
    r=run086_case()
    return dict(modeled_completed=r['modeled_completed'],controls=len(r['controls']),
        total_guards=r['full_guards'],valid_guard_spans=r['valid_guard_spans'],
        raw_inspections=r['full_guards']-1,frame_kinds=r['frame_kinds'],
        scope='typed_schedule_only_no_raw_api_or_full_bridge',
        full_combined_success=False,runtime_authorized=False,orders_available=False)


class Review088Tests(unittest.TestCase):
    def test_schedule_counts_from_complete_six_control_execution(self):
        r=schedule088();p=budget_review088()
        self.assertTrue(r['modeled_completed']);self.assertEqual(r['controls'],6)
        self.assertEqual((r['total_guards'],r['valid_guard_spans'],r['raw_inspections']),
            (p['total_guards'],70,69));self.assertFalse(r['full_combined_success'])
    def test_optimistic_floor_exceeds_original_clock_cap_even_without_ancestry(self):
        p=budget_review088();self.assertEqual((p['api_calls_floor'],p['clock_samples_floor']),(2346,4693))
        self.assertEqual(p['maximum_fully_bracketed_api_calls'],2047)
        self.assertGreater(p['clock_samples_floor'],p['clock_samples_limit'])
        self.assertFalse(p['ancestor_deduplication_sufficient'])
    def test_other_bridge_budgets_also_cannot_fit_complete_original_schedule(self):
        p=budget_review088()
        self.assertEqual((p['bridge_calls'],p['sdk_queries'],p['boot_queries']),(139,1668,208))
        for value,cap in (('bridge_calls','bridge_call_limit'),('sdk_queries','sdk_query_limit'),('boot_queries','boot_query_limit')):
            self.assertGreater(p[value],p[cap])
    def test_measured_raw_inspection_matches_decomposed_acquisition_cost(self):
        r=combined088();self.assertEqual(set(r['completed_inspection_call_counts']),{64})
        # Two parents for root, three for file; both descriptor and path walks.
        self.assertEqual(64, budget_review088()['api_calls_per_inspection_floor']+2*3*(2+3))
    def test_combined_full_target_preserves_count_failure_and_cleanup(self):
        r=combined088();self.assertFalse(r['modeled_completed']);self.assertTrue(r['full_six_control_target_entered'])
        self.assertEqual((r['api_calls'],r['api_clock_samples'],r['controls']),(2048,4097,2))
        self.assertEqual((r['summary']['counts']['guards'],r['summary']['valid_guard_spans']),(31,30))
        self.assertEqual((r['bridge_calls'],r['sdk_queries'],r['boot_queries']),(61,732,91))
        self.assertEqual((r['remaining_handles'],r['remaining_allocations'],r['sdk_shutdown_attempts']),(0,0,1))
        self.assertTrue(r['sdk_cleanup_confirmed']);self.assertTrue(r['summary']['cleanup_confirmed'])
    def rejects(self,mutation):
        r=combined088(mutation);self.assertFalse(r['modeled_completed'],r)
        self.assertTrue(r['mutation_injected']);self.assertEqual(r['mutation_count'],1)
        self.assertEqual(r['controls'],0);self.assertEqual(r['summary']['valid_guard_spans'],1)
        self.assertEqual((r['remaining_handles'],r['remaining_allocations'],r['sdk_shutdown_attempts']),(0,0,1))
        self.assertTrue(r['sdk_cleanup_confirmed']);return r
    def test_file_replacement_inside_uncached_composite_rejects(self):self.rejects('file_replace')
    def test_root_replacement_inside_uncached_composite_rejects(self):self.rejects('root_replace')
    def test_ancestor_replacement_inside_uncached_composite_rejects(self):self.rejects('ancestor_replace')
    def test_ancestor_reparse_inside_uncached_composite_rejects(self):self.rejects('ancestor_reparse')
    def test_current_acl_change_rejects(self):self.rejects('acl_change')
    def test_pipe_peer_creation_change_rejects(self):self.rejects('peer_change')
    def test_real_account_after_first_guard_rejects(self):self.rejects('account_real')
    def test_contest_account_after_first_guard_rejects(self):self.rejects('account_contest')
    def test_different_demo_account_after_first_guard_rejects(self):self.rejects('account_change')
    def test_current_source_hash_change_rejects(self):self.rejects('source_change')
    def test_standalone_sdk_cap_remains_independent_rejection(self):
        r=model_guard087(repeat=True);self.assertEqual((r['full_bridge_calls'],r['sdk_queries'],r['boot_queries']),(86,1024,85))
        self.assertFalse(r['modeled_completed']);self.assertTrue(r['cleanup_confirmed'])
    def test_transport_default_off_no_guard_or_raw_api_invocations(self):
        r=combined088(enabled=False);self.assertTrue(r['default_off'])
        self.assertEqual((r['api_calls'],r['bridge_calls'],r['sdk_queries'],r['controls']),(0,0,0,0))
        self.assertFalse(r['modeled_completed'])
    def test_new_dated_requirements_cannot_admit_any_runtime(self):
        p=reader_requirements088(ROOT);self.assertEqual(p['date'],'2026-10-09')
        for d in ('2026-10-08','2026-10-09','2026-10-10'):
            self.assertFalse(admission088(p,d))
        self.assertFalse(p['new_reader_implemented']);self.assertFalse(p['native_entry_available'])
    def test_oct9_clock_still_rejected_by_frozen_oct8_model_meter(self):
        from forex_demo_lab.synchronization_083 import Meter083
        ms=int(datetime(2026,10,9,12,tzinfo=timezone.utc).timestamp()*1000)
        with self.assertRaises(Exception):Meter083(lambda:(ms,0,100000))
    def test_requirements_retain_all_prior_source_bindings_and_windows(self):
        p=reader_requirements088(ROOT);self.assertEqual(len(p['prior_reader_inputs']),37)
        self.assertEqual(len(p['prior_compile_inputs']),6)
        self.assertEqual(tuple(p['required_windows_ms'].values()),(2000,10000,30000,31000,250,60000,120000))
        self.assertFalse(p['new_reader_compiled']);self.assertFalse(p['orders_available'])


if __name__=='__main__':unittest.main()
