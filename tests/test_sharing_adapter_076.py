from dataclasses import FrozenInstanceError
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch

from forex_demo_lab.sharing_adapter_076 import *
from forex_demo_lab.sharing_integration_072 import Companion072,FullGuard072,ObservedCompanion069,Trace069
from forex_demo_lab.private_guard_065 import Identity065
from forex_demo_lab.sharing_runtime_069 import LIMITS069
from test_sharing_runtime_066 import ExternalFiles
from test_transport_lifecycle_060 import Clock
from test_sharing_companion_065 import Reader
from test_fresh_data_031 import API as AccountAPI
from test_sharing_integration_072 import record072,text072


def sha(raw):return hashlib.sha256(raw).hexdigest()


class Build076Tests(unittest.TestCase):
    def setUp(self):
        self.contract=source_contract072(dict.fromkeys(SOURCE_INPUTS,'a'*64))
        self.log='Result: 0 errors, 0 warnings, 1000 ms elapsed\n'
        self.artifact=dict(sha256='b'*64,size=100,raw=None)
        self.record=build_record075(self.contract,1,self.log,self.artifact,'c'*64,'d'*64)
    def validate(self,**changes):
        args=dict(record=self.record,contract=self.contract,log_text=self.log,artifact=self.artifact,
            compiler_sha256='c'*64,terminal_sha256='d'*64)
        return validate_build076(**{**args,**changes})
    def test_actual_exit_one_source_bound_build_is_retained(self):
        build=self.validate();self.assertEqual(build.record(),self.record)
        self.assertEqual(build.record()['compiler_exit_code'],1)
        self.assertFalse(build.record()['runtime_authorized'])
    def test_boolean_missing_and_unknown_fields_are_rejected(self):
        for r in ({**self.record,'errors':False},{**self.record,'compiler_invocations':True},
            {**self.record,'compiled':1},{**self.record,'extra':0},{k:v for k,v in self.record.items() if k!='warnings'}):
            with self.assertRaises(ProbeRejected):self.validate(record=r)
    def test_old_schema_source_phase_and_build_phase_rejected(self):
        for changes in ({'version':'sharing_build_074_v1'},{'build_phase':'74'*16},{'phase':'64'*16},
            {'date':'2026-10-07'},{'artifact_name':'ForexDemoSharing064.ex5'},{'compiler_exit_code':0}):
            with self.assertRaises(ProbeRejected):self.validate(record={**self.record,**changes})
    def test_build_can_never_grant_runtime_or_orders(self):
        for changes in ({'runtime_authorized':True},{'orders_available':True},{'terminal_build':6245}):
            with self.assertRaises(ProbeRejected):self.validate(record={**self.record,**changes})
    def test_independent_artifact_compiler_terminal_and_source_pins_required(self):
        for changes in ({'artifact':{**self.artifact,'sha256':'e'*64}},{'artifact':{**self.artifact,'size':99}},
            {'compiler_sha256':'e'*64},{'terminal_sha256':'e'*64},
            {'contract':source_contract072(dict.fromkeys(SOURCE_INPUTS,'e'*64))}):
            with self.assertRaises(ProbeRejected):self.validate(**changes)
    def test_warning_missing_and_duplicate_compiler_summaries_rejected(self):
        for log in ('',self.log+self.log,self.log.replace('0 warnings','1 warnings')):
            with self.assertRaises(ProbeRejected):self.validate(log_text=log)
    def test_build_snapshot_is_immutable_and_defensive(self):
        build=self.validate();original=build.raw
        self.record['input_bindings'][SOURCE_INPUTS[0]]='e'*64
        build.record()['input_bindings'][SOURCE_INPUTS[1]]='f'*64
        self.assertEqual(build.raw,original)
        with self.assertRaises(FrozenInstanceError):build.raw=b'changed'
    def test_complete_runtime_bindings_include_hold_and_private_profile_hash(self):
        out=runtime_bindings076(self.validate(),'e'*64,'f'*64,'1'*64)
        self.assertEqual(set(out),BINDING_KEYS);self.assertEqual(out['ex5'],'b'*64)
        self.assertEqual(out['hold'],'a'*64)
        with self.assertRaises(ProbeRejected):runtime_bindings076(self.validate(),'private','f'*64,'1'*64)
    def test_malformed_or_duplicate_build_json_has_fixed_private_error(self):
        for raw in (b'private account',encoded076(self.record).replace(b'"errors":0',b'"errors":0,"errors":0'),
            b'x'*4097,bytearray(encoded076(self.record))):
            with self.assertRaisesRegex(ProbeRejected,'^adapter_build_rejected$') as e:VerifiedBuild076(raw)
            self.assertNotIn('private',str(e.exception))


class Timing076Tests(unittest.TestCase):
    def test_fast_declared_schedule_fits_without_native_permission(self):
        r=TimingBounds076(100,1000,100,1).report()
        self.assertTrue(r['modeled_admission']);self.assertEqual(r['independent_completion_upper_ms'],22706)
        self.assertTrue(r['requires_native_timing_evidence']);self.assertFalse(r['runtime_authorized'])
    def test_slow_guards_reject_launch_gate(self):
        r=TimingBounds076(6000,0,0,0).report()
        self.assertFalse(r['launch_gate_fits'])
        with self.assertRaises(ProbeRejected):TimingBounds076(6000,0,0,0).require()
    def test_launch_fits_but_independent_controls_can_overrun_hold(self):
        r=TimingBounds076(2000,0,0,1).report()
        self.assertTrue(r['launch_gate_fits']);self.assertFalse(r['end_margin_fits'])
        self.assertEqual(r['independent_completion_upper_ms'],52006)
    def test_strict_start_margin_boundary(self):
        self.assertFalse(TimingBounds076(0,4750,0,0).report()['start_margin_fits'])
        self.assertTrue(TimingBounds076(0,4749,0,0).report()['modeled_admission'])
    def test_strict_end_margin_boundary(self):
        self.assertFalse(TimingBounds076(1500,0,750,0,wait_overshoot_ms=0).report()['end_margin_fits'])
        self.assertTrue(TimingBounds076(1500,0,749,0,wait_overshoot_ms=0).report()['modeled_admission'])
    def test_unchanged_inclusive_ten_second_launch_boundary(self):
        self.assertTrue(TimingBounds076(1,0,9998,0,wait_overshoot_ms=0).report()['modeled_admission'])
        self.assertFalse(TimingBounds076(1,0,9999,0).report()['launch_gate_fits'])
    def test_default_includes_entire_existing_wait_overshoot_allowance(self):
        r=TimingBounds076(1000,1000,0,1).report()
        self.assertTrue(r['launch_gate_fits']);self.assertFalse(r['modeled_admission'])
        self.assertEqual(r['bounds']['wait_overshoot_ms'],15000)
        self.assertTrue(TimingBounds076(1000,1000,0,1,wait_overshoot_ms=0).report()['modeled_admission'])
    def test_scheduler_clock_and_dispatch_overhead_is_budgeted_explicitly(self):
        a=TimingBounds076(100,1000,100,1).report()
        b=TimingBounds076(100,1000,100,1,overhead_ms=500).report()
        for name in ('launch_gate_upper_ms','latest_mql_start_ms','independent_completion_upper_ms'):
            self.assertEqual(b[name]-a[name],500)
        for changes in ({'overhead_ms':True},{'overhead_ms':10001},{'wait_overshoot_ms':True},
            {'wait_overshoot_ms':-1},{'wait_overshoot_ms':15001}):
            with self.assertRaises(ProbeRejected):TimingBounds076(1,1,1,1,**changes)
    def test_boolean_float_negative_and_unbounded_costs_rejected(self):
        for value in (True,1.0,-1,10001,None):
            for i in range(4):
                values=[1]*4;values[i]=value
                with self.assertRaises(ProbeRejected):TimingBounds076(*values)


class Adapter076Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        self.clock=Clock();self.clock.utc+=86400000;self.clock.boot=99000
        self.m=Meter072(self.clock);self.trace=Trace069()
        contract=source_contract072(dict.fromkeys(SOURCE_INPUTS,'a'*64))
        artifact=dict(sha256='b'*64,size=100,raw=None);log='Result: 0 errors, 0 warnings, 1 ms elapsed\n'
        r=build_record075(contract,1,log,artifact,'c'*64,'d'*64)
        self.build=validate_build076(r,contract,log,artifact,'c'*64,'d'*64)
        self.timing=TimingBounds076(0,1000,0,0)
        self.bindings=runtime_bindings076(self.build,'e'*64,'f'*64,'1'*64)
        self.dispatch=self.root/'dispatch'
        self.dispatch_proof=reserve_dispatch076(self.dispatch,self.build,'e'*64,'f'*64,'1'*64,self.timing)
        self.reservation=self.root/'reservation';self.s=Reservation072(self.reservation,self.bindings,self.m)
        self.raw=self.reservation.read_bytes()
        self.f=ExternalFiles(self.m,self.clock);self.guard=lambda:self.m.consume('guards') or True
        self.c=ObservedCompanion069(Companion072(self.f,self.m,lambda:self.guard()),self.trace)
        self.log=self.root/'log';self.log.write_bytes('old\r\n'.encode('utf-16-le'))
        self.owner=Resources069(self.s,self.m,self.trace);self.owner.files=self.f
        self.a=self.construct();self.r=self.a.runtime
    def construct(self,**changes):
        args=dict(build=self.build,preparation='e'*64,policy='f'*64,profile='1'*64,timing=self.timing,
            dispatch=self.dispatch_proof,bindings=self.bindings,reservation_raw=self.raw,reservation_sha=sha(self.raw),companion=self.c,
            session=self.s,meter=self.m,guard=lambda:self.guard(),log=self.log,wait=self.clock.advance,
            owner=self.owner,trace=self.trace)
        return Adapter076(**{**args,**changes})
    def prepared(self):
        for cmd in ('baseline-saved','arm-disabled','disabled-done'):self.a.command(cmd)
    def armed(self):self.prepared();self.clock.advance(1000);self.a.command('arm-enabled')
    def probed(self):self.armed();self.a.command('probe')
    def saved(self):
        with self.log.open('ab') as f:f.write(('\r\n'.join(text072(x) for x in [record072(),record072(True)])+'\r\n').encode('utf-16-le'))
        self.a.command('logs-saved')
    def test_complete_graph_uses_actual072_dependencies_and_diagnostics(self):
        self.probed();self.saved();out=self.a.finish();self.assertTrue(out['modeled_completed'])
        self.assertEqual(out['source_phase'],SOURCE_PHASE)
        self.assertEqual(out['ownership']['outcome']['diagnostics']['version'],'sharing_diagnostics_072_v1')
        self.assertEqual([p.error for p in self.c.probes],[0,0,32,32,0,0])
        self.assertFalse(self.f.active);self.assertEqual(self.m.counts['native_calls'],0)
        self.assertFalse(out['native_mql_verified']);self.assertFalse(out['runtime_authorized'])
    def test_critical_window_contains_six_operations_and_sixteen_full_guards(self):
        self.armed();before=self.m.counts['guards'];seen=[];controls=self.c.controls
        def watched(stage):
            counts=dict(self.m.counts);result=controls(stage)
            if stage=='independent':
                seen.append((self.m.counts['guards']-counts['guards'],
                    self.m.counts['stamps']-counts['stamps']+self.m.counts['opens']-counts['opens'],
                    self.m.counts['guards']-before+1))
            return result
        self.c.controls=watched;self.a.command('probe')
        self.assertEqual(seen,[(12,6,16)])
        self.assertLessEqual(self.m.counts['guards'],LIMITS069['guards'])
        self.a.finish()
    def test_exclusive_dispatch_fsyncs_and_cannot_be_restarted(self):
        p=self.root/'second-dispatch'
        with patch('forex_demo_lab.sharing_adapter_076.os.fsync') as sync:
            h=reserve_dispatch076(p,self.build,'e'*64,'f'*64,'1'*64,self.timing);self.assertEqual(sync.call_count,1)
        self.assertEqual(h.sha256,sha(p.read_bytes()))
        with self.assertRaises(FileExistsError):reserve_dispatch076(p,self.build,'e'*64,'f'*64,'1'*64,self.timing)
        self.assertFalse(p.with_suffix('.sha256').exists())
        self.assertFalse(json.loads(p.read_bytes())['execution_authorized'])
    def test_infeasible_dispatch_does_not_create_marker_or_arm(self):
        p=self.root/'rejected'
        with self.assertRaisesRegex(ProbeRejected,'adapter_schedule_infeasible'):
            reserve_dispatch076(p,self.build,'e'*64,'f'*64,'1'*64,TimingBounds076(2000,0,0,1))
        self.assertFalse(p.exists());self.assertEqual(self.s.arms,[])
    def test_claimed_dispatch_cannot_assemble_second_runner(self):
        self.owner.runner=None
        with self.assertRaisesRegex(ProbeRejected,'adapter_dispatch_rejected'):self.construct()
        self.assertTrue(self.dispatch_proof.used);self.assertEqual(self.s.arms,[])
    def test_dispatch_timing_binding_cannot_be_changed(self):
        self.owner.runner=None
        proof=reserve_dispatch076(self.root/'new-dispatch',self.build,'e'*64,'f'*64,'1'*64,self.timing)
        with self.assertRaisesRegex(ProbeRejected,'adapter_dispatch_rejected'):
            self.construct(dispatch=proof,timing=TimingBounds076(0,999,0,0))
        self.assertFalse(proof.used);self.assertIsNone(self.owner.runner)
    def test_raw_reservation_schema_and_digest_cannot_be_substituted(self):
        v=json.loads(self.raw)
        for changes in ({'phase':PHASE},{'date':'2026-10-07'},{'maximum_launches':True},
            {'maximum_receipt_permissions':1},{'extra':'private'}):
            raw=encoded076({**v,**changes})
            with self.assertRaises(ProbeRejected):reservation_bytes076(raw,sha(raw),self.bindings)
        with self.assertRaises(ProbeRejected):reservation_bytes076(self.raw,'0'*64,self.bindings)
    def test_altered_graph_bindings_are_rejected_before_runner_assignment(self):
        self.owner.runner=None
        with self.assertRaisesRegex(ProbeRejected,'adapter_bindings_rejected'):
            self.construct(bindings={**self.bindings,'ex5':'e'*64})
        self.assertIsNone(self.owner.runner)
    def test_wrong_owner_meter_trace_and_existing_runner_rejected(self):
        with self.assertRaises(ProbeRejected):self.construct()
        self.owner.runner=None
        with self.assertRaises(ProbeRejected):self.construct(trace=Trace069())
        with self.assertRaises(ProbeRejected):self.construct(meter=NS())
        self.owner.closed=True
        with self.assertRaises(ProbeRejected):self.construct()
    def test_owner_must_hold_the_exact_companion_backend(self):
        self.owner.runner=None;self.owner.files=NS()
        with self.assertRaisesRegex(ProbeRejected,'adapter_ownership_rejected'):self.construct()
        self.assertIsNone(self.owner.runner);self.assertEqual(self.s.arms,[])
    def test_duplicate_command_stops_without_second_arm_and_closes_handles(self):
        self.a.command('baseline-saved');self.a.command('arm-disabled')
        with self.assertRaises(ProbeRejected):self.a.command('arm-disabled')
        out=self.a.finish();self.assertFalse(out['modeled_completed']);self.assertEqual(self.s.arms,['disabled'])
        self.assertFalse(self.f.active)
    def test_late_probe_keeps_original_diagnostic_and_wait_budget(self):
        self.armed();self.clock.advance(10001)
        with self.assertRaises(ProbeRejected):self.a.command('probe')
        out=self.a.finish();r=out['ownership']['outcome']
        self.assertEqual(r['stop_reason'],'probe_launch_window:window_rejected')
        self.assertEqual(r['counts']['schedule_waits'],0)
    def test_observed_guard_exceeding_assumption_stops_before_arming(self):
        self.guard=lambda:self.clock.advance(1) or True
        with self.assertRaisesRegex(ProbeRejected,'adapter_guard_bound_exceeded'):self.a.command('baseline-saved')
        out=self.a.finish();self.assertFalse(out['modeled_completed'])
        self.assertEqual(self.s.arms,[]);self.assertEqual(out['adapter_stop_reason'],'adapter_guard_bound_exceeded')
        with self.assertRaises(ProbeRejected):self.a.command('arm-disabled')
    def test_wait_exceeding_tighter_model_bound_invalidates_result(self):
        self.owner.runner=None;timing=TimingBounds076(0,1000,0,0,wait_overshoot_ms=0)
        proof=reserve_dispatch076(self.root/'tight-dispatch',self.build,'e'*64,'f'*64,'1'*64,timing)
        self.a=self.construct(dispatch=proof,timing=timing);self.r=self.a.runtime
        self.armed();self.r.wait=lambda ms:self.clock.advance(ms+1)
        with self.assertRaisesRegex(ProbeRejected,'adapter_wait_bound_exceeded'):self.a.command('probe')
        out=self.a.finish();self.assertFalse(out['modeled_completed'])
        self.assertEqual(out['adapter_stop_reason'],'adapter_wait_bound_exceeded')
    def test_actual_real_and_contest_modes_rejected_through_adapter_guard(self):
        for mode in (1,2):
            if mode==2:self.a.finish();self.setUp()
            api=AccountAPI();api.terminal.path=r'C:\Program Files\MetaTrader 5';api.terminal.data_path=r'C:\private-demo';api.terminal.build=6244
            api.account.trade_mode=mode;api.account.server='demo-looking-name'
            peer=Identity065(7,11,r'c:\program files\metatrader 5\terminal64.exe','a'*64,1,'synthetic-logon')
            reader=Reader(peer,self.m);guard=FullGuard072(api,reader,peer,api.terminal.data_path,6244,('editor','a'*64),('artifact','a'*64),self.m)
            self.guard=guard
            with self.assertRaises(ProbeRejected):self.a.command('baseline-saved')
            self.assertEqual(self.s.arms,[])
            self.assertTrue(guard.stopped)
        self.a.finish()
    def test_replaced_saved_log_is_rejected_with_one_read(self):
        self.probed();self.log.rename(self.root/'old');self.log.write_bytes(b'\0'*100)
        with self.assertRaises(ProbeRejected):self.a.command('logs-saved')
        out=self.a.finish();self.assertFalse(out['modeled_completed']);self.assertEqual(self.m.counts['log_reads'],1)
    def test_private_guard_exception_is_redacted_and_cleanup_still_runs(self):
        self.prepared()
        def failed():raise ValueError('private account SID')
        self.guard=failed
        with self.assertRaises(ProbeRejected):self.a.command('arm-enabled')
        out=self.a.finish();self.assertNotIn('private',json.dumps(out));self.assertFalse(self.f.active)
    def test_expiry_shutdown_is_once_even_after_clock_failure(self):
        self.prepared();self.s.sdk_attempt();calls=[];self.owner.sdk=NS(shutdown=lambda:calls.append(1))
        self.clock.advance(900000);out=self.a.finish()
        self.assertFalse(out['modeled_completed']);self.assertFalse(self.f.active);self.assertEqual(calls,[1])
        with self.assertRaises(ProbeRejected):self.a.finish()
        self.assertEqual(calls,[1])
    def test_failed_constructor_leaves_owned_sdk_available_for_one_cleanup(self):
        self.owner.runner=None;self.s.sdk_attempt();calls=[];self.owner.sdk=NS(shutdown=lambda:calls.append(1))
        with self.assertRaises(ProbeRejected):self.construct(reservation_sha='0'*64)
        out=close_owned069(self.owner);self.assertEqual(calls,[1]);self.assertTrue(out['sdk_shutdown_called'])
        self.assertFalse(self.f.active)
    def test_uncertain_file_cleanup_cannot_report_modeled_success(self):
        self.probed();self.saved();self.f.close_ok=False
        out=self.a.finish();self.assertFalse(out['modeled_completed']);self.assertTrue(out['ownership']['errors'])
        self.f.close_ok=True;self.f.finish()
    def test_first_failure_survives_cleanup_exception(self):
        self.armed();self.clock.advance(10001)
        with self.assertRaises(ProbeRejected):self.a.command('probe')
        original=self.c.finish
        def failed():original();raise ValueError('private account')
        self.c.finish=failed;out=self.a.finish()
        self.assertEqual(out['ownership']['outcome']['stop_reason'],'probe_launch_window:window_rejected')
        self.assertNotIn('private',json.dumps(out))


class Deployment076Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        self.clock=Clock();self.clock.utc+=86400000;self.m=Meter072(self.clock)
        self.source=self.root/'ForexDemoSharing072.ex5';self.source.write_bytes(b'synthetic compiled artifact')
        contract=source_contract072(dict.fromkeys(SOURCE_INPUTS,'a'*64))
        log='Result: 0 errors, 0 warnings, 1 ms elapsed\n'
        artifact=dict(sha256=sha(self.source.read_bytes()),size=self.source.stat().st_size,raw=None)
        r=build_record075(contract,1,log,artifact,'c'*64,'d'*64)
        self.build=validate_build076(r,contract,log,artifact,'c'*64,'d'*64)
        self.scripts=self.root/'Scripts';self.scripts.mkdir();self.name='ForexDemoLab076-'+'a'*32
        self.reader=NS(hash_file=lambda p:sha(Path(p).read_bytes()));self.guards=[]
        self.guard=lambda:self.guards.append(True) or True
    def deploy(self,**changes):
        args=dict(source=self.source,scripts=self.scripts,name=self.name,build=self.build,
            reader=self.reader,guard=self.guard,meter=self.m)
        return deploy_owned076(**{**args,**changes})
    def test_new_source_named_target_is_exclusively_copied_and_rehashed(self):
        p=self.deploy();self.assertEqual(p.name,'ForexDemoSharing072.ex5')
        self.assertEqual(p.read_bytes(),self.source.read_bytes());self.assertEqual(len(self.guards),2)
        self.assertEqual(self.m.counts['deployment_writes'],1);self.assertEqual(self.m.counts['native_calls'],0)
    def test_existing_folder_never_overwrites_unrelated_file(self):
        directory=self.scripts/self.name;directory.mkdir();p=directory/'unrelated';p.write_bytes(b'keep')
        with self.assertRaises(FileExistsError):self.deploy()
        self.assertEqual(p.read_bytes(),b'keep');self.assertEqual(self.m.counts['deployment_writes'],0)
    def test_wrong_phase_folder_rejected_before_any_creation(self):
        with self.assertRaises(ProbeRejected):self.deploy(name='ForexDemoLab069-'+'a'*32)
        self.assertFalse(list(self.scripts.iterdir()))
    def test_changed_source_digest_rejected_before_copy(self):
        self.source.write_bytes(b'changed')
        with self.assertRaises(ProbeRejected):self.deploy()
        self.assertEqual(self.m.counts['deployment_writes'],0)
    def test_terminal_guard_root_cannot_be_substituted(self):
        self.guard.data_root=str(self.root)
        with self.assertRaises(ProbeRejected):self.deploy()
        self.assertEqual(self.m.counts['deployment_writes'],0)
    def test_source_symlink_and_script_parent_symlink_rejected(self):
        link=self.root/'link';link.symlink_to(self.source)
        with self.assertRaises(ProbeRejected):self.deploy(source=link)
        parent=self.root/'dirlink';parent.symlink_to(self.scripts,target_is_directory=True)
        with self.assertRaises(ProbeRejected):self.deploy(scripts=parent)
    def test_post_copy_guard_change_rejects_without_deleting_evidence(self):
        calls=[]
        def guard():calls.append(1);return len(calls)==1
        with self.assertRaises(ProbeRejected):self.deploy(guard=guard)
        self.assertTrue((self.scripts/self.name/'ForexDemoSharing072.ex5').exists())
        self.assertEqual(self.m.counts['deployment_writes'],1)
    def test_exhausted_byte_budget_consumes_copy_attempt_and_keeps_partial_target(self):
        self.m.counts['deployment_bytes']=LIMITS069['deployment_bytes']
        with self.assertRaises(ProbeRejected):self.deploy()
        self.assertEqual(self.m.counts['deployment_writes'],1)
        self.assertEqual((self.scripts/self.name/'ForexDemoSharing072.ex5').stat().st_size,0)
    def test_replaced_post_copy_digest_rejected(self):
        count=[]
        def hashing(p):
            count.append(1);return sha(Path(p).read_bytes()) if len(count)<3 else '0'*64
        with self.assertRaises(ProbeRejected):self.deploy(reader=NS(hash_file=hashing))
        self.assertEqual(self.m.counts['deployment_writes'],1)
