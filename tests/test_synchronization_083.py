from dataclasses import replace
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
from types import SimpleNamespace as NS
import unittest

from forex_demo_lab.synchronization_083 import *

ROOT=Path(__file__).resolve().parents[1]


class Clock083:
    def __init__(self):
        self.utc=int(datetime(2026,10,8,tzinfo=timezone.utc).timestamp()*1000)
        self.mono=0;self.boot=100000
    def __call__(self):return self.utc,self.mono,self.boot
    def advance(self,ms):
        integer(ms,0,120000);self.utc+=ms;self.mono+=ms*1000000;self.boot+=ms


class Lease083:
    def __init__(self,peer,snapshot):self.peer=peer;self.value=snapshot;self.reads=0;self.closed=False
    def snapshot(self):
        require(not self.closed);self.reads+=1
        if self.peer.cfg.get('replaced_snapshot') and self.reads>1:
            return replace(self.value,proof=replace(self.value.proof,signal_identity=(999,88,77)))
        return self.value
    def close(self):
        if self.closed:return False
        self.closed=True;self.peer.lease_closes+=1
        return not self.peer.cfg.get('lease_close_failed',False)


class Peer083:
    model_only=True
    def __init__(self,clock,bindings,cfg):
        self.clock,self.b,self.cfg=clock,bindings,cfg
        self.proof=Private083(bindings.file_identity,bindings.signal_identity)
        self.hold_start=self.hold_end=None;self.leases=[];self.release_calls=0
        self.cleanup_calls=0;self.lease_closes=0;self.pending=cfg.get('pending',0)
    def operation(self,stage,op,access):
        self.clock.advance(self.cfg.get('io_ms',50))
        if self.cfg.get('blocked_return') and stage=='independent' and op=='open':self.clock.advance(30000)
        if self.cfg.get('interrupt_operation') and stage=='independent':raise KeyboardInterrupt('private-account-logon')
        proof=self.proof
        if (stage,op)==self.cfg.get('bad_proof_operation'):
            proof=replace(proof,**self.cfg.get('bad_private',{'same_file':False}))
        blocked=stage=='independent' and op=='open'
        error=32 if blocked else 0
        if self.cfg.get('wrong_control_error') and blocked:error=5
        return Reply083(stage,op,proof,error,op=='open' and not blocked,op=='close')
    def release(self,raw,b,ep,seq,deadline):
        self.release_calls+=1;require(self.release_calls==1)
        self.clock.advance(self.cfg.get('io_ms',50))
        parsed=decode_signal083(raw,'release',seq,b,ep,self.clock.boot,deadline,0)
        self.hold_start=parsed['issued']+self.cfg.get('launch_delay',50)
        self.hold_end=self.hold_start+30000+self.cfg.get('hold_extra',0)
        if self.cfg.get('release_error'):raise ValueError('private-path')
        return Reply083('signal','release',self.proof)
    def exchange(self,kind,seq,b,ep,deadline):
        self.clock.advance(self.cfg.get('io_ms',50));pending=False
        if self.cfg.get('pending_forever') and kind=='ready':pending=True
        if kind=='holding' and (self.clock.boot<self.hold_start or self.pending>0):
            pending=True;self.pending=max(0,self.pending-1)
        if kind=='closed' and self.clock.boot<self.hold_end:pending=True
        hs=self.hold_start if kind in ('holding','closed') else 0
        he=self.hold_end if kind=='closed' else 0
        raw=b'' if pending else encode_signal083(kind,seq,b,ep,
            self.clock.boot-self.cfg.get('stale_ms',0),deadline,hs,he)
        if not pending and self.cfg.get('wire_change'):
            r=bytearray(raw);r[self.cfg['wire_change']]+=1;raw=bytes(r)
        s=Snapshot083('pending' if pending else 'boundary',raw,self.proof,not pending)
        if self.cfg.get('bad_snapshot'):s=replace(s,**self.cfg['bad_snapshot'])
        lease=Lease083(self,s);self.leases.append(lease);return lease
    def cleanup_model(self):
        self.cleanup_calls+=1
        for lease in self.leases:
            if not lease.closed:lease.close()
        return Cleanup083(all_handles_closed=not self.cfg.get('cleanup_failed',False))


def fixture083(path,bindings=None,**cfg):
    c=Clock083();b=bindings or Bindings083('a'*64,'b'*64,'c'*64,'d'*64,(500123987,2,3),(700789321,4,5))
    p=Peer083(c,b,cfg);state=NS(guards=0,factories=0)
    def guard():
        state.guards+=1;c.advance(cfg.get('guard_ms',0))
        if state.guards==cfg.get('bad_guard_at'):
            return replace(Guard083(),**cfg.get('bad_guard',{'actual_account_type':2}))
        return Guard083()
    def factory(owner):
        state.factories+=1;owner.adopt(p)
        if cfg.get('factory_interrupt'):raise KeyboardInterrupt('private-owner')
        return p
    def wait(ms):
        c.advance(ms+cfg.get('wait_overshoot',0))
    m=Model083(path,b,b'episode-private!',c,guard,factory,wait)
    return NS(clock=c,bindings=b,peer=p,state=state,model=m)


class Sync083Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
    def f(self,**cfg):return fixture083(self.root/'marker',**cfg)
    def run_case(self,**cfg):
        f=self.f(**cfg);return f,f.model.run(True)
    def failed(self,**cfg):
        f,r=self.run_case(**cfg);self.assertFalse(r['modeled_completed'])
        self.assertEqual(f.peer.cleanup_calls,1);self.assertTrue(all(l.closed for l in f.peer.leases));return f,r
    def test_default_off_no_marker_factory_or_guard(self):
        f=self.f();r=f.model.run();self.assertFalse(r['modeled_completed'])
        self.assertFalse((self.root/'marker').exists());self.assertEqual(f.state.guards,0)
        self.assertEqual(f.state.factories,0);self.assertEqual(f.peer.cleanup_calls,0)
    def test_normal_sequence_six_controls_full_guards_and_owned_cleanup(self):
        f,r=self.run_case();self.assertTrue(r['modeled_completed'])
        self.assertEqual([(p['stage'],p['access'],p['error']) for p in r['probes']],
            [(s,a,32 if s=='independent' else 0) for s in ('pre','independent','post') for a in ('write','delete')])
        self.assertEqual(f.peer.release_calls,1);self.assertEqual(f.peer.cleanup_calls,1)
        self.assertTrue(r['cleanup_confirmed']);self.assertLess(r['episode_elapsed_ms'],60000)
    def test_observed_maximum_scenario_fits_without_claiming_bounds(self):
        f,r=self.run_case(guard_ms=1611);self.assertTrue(r['modeled_completed'])
        self.assertLess(r['outer_elapsed_ms'],120000)
        for k in ('native_launch_ready','latency_guaranteed','runtime_authorized','native_mql_verified'):
            self.assertFalse(r[k])
    def test_slow_guard_exceeds_signal_freshness(self):self.failed(guard_ms=2001)
    def test_pending_holding_reply_and_guarded_wait(self):
        f,r=self.run_case(pending=1,guard_ms=100);self.assertTrue(r['modeled_completed'])
        self.assertGreater(r['counts']['polls'],3);self.assertTrue(all(l.closed for l in f.peer.leases))
    def test_pending_forever_finite_poll_and_outer_clock_stop(self):
        f,r=self.failed(pending_forever=True)
        self.assertLessEqual(r['counts']['polls'],64);self.assertEqual(f.peer.release_calls,0)
    def test_restart_cannot_recreate_marker(self):
        f,r=self.run_case();self.assertTrue(r['modeled_completed'])
        other=fixture083(self.root/'marker');r=other.model.run(True)
        self.assertFalse(r['modeled_completed']);self.assertEqual(other.state.factories,0)
    def test_same_instance_cannot_repeat_or_refund(self):
        f,r=self.run_case(release_error=True);self.assertTrue(r['release_spent'])
        with self.assertRaises(ProbeRejected):f.model.run(True)
        self.assertEqual(f.peer.release_calls,1)
    def test_release_failure_is_spent_before_trailing_guard(self):
        f,r=self.failed(release_error=True);self.assertTrue(r['release_spent'])
        self.assertEqual(f.peer.release_calls,1)
    def test_guard_failure_before_release_still_consumes_attempt(self):
        f,r=self.failed(bad_guard_at=27);self.assertTrue(r['release_spent'])
        self.assertEqual(f.peer.release_calls,0)
    def test_real_and_contest_actual_account_types_rejected(self):
        for mode in (1,2):
            with self.subTest(mode=mode),TemporaryDirectory() as d:
                f=fixture083(Path(d)/'marker',bad_guard_at=1,bad_guard={'actual_account_type':mode})
                self.assertFalse(f.model.run(True)['modeled_completed']);self.assertEqual(f.state.factories,0)
    def test_account_change_after_release_rejected_with_cleanup(self):
        f,r=self.failed(bad_guard_at=31,bad_guard={'same_account':False})
        self.assertTrue(r['release_spent'])
    def test_guard_boolean_type_and_altered_owned_graph_rejected(self):
        for change in ({'actual_account_type':False},{'connected':1},{'same_owned_sdk':False},
                       {'uncached_images_sdk_sources':False},{'same_process_creation_logon_boot':False},
                       {'algo_allowed':True},{'currency':'EUR'},{'supported_eurusd_metadata':False},
                       {'terminal_build':0},{'terminal_paths_stable':False},{'sdk_version':'changed'},
                       {'helper_chain_bound':False}):
            with self.subTest(change=change),TemporaryDirectory() as d:
                f=fixture083(Path(d)/'marker',bad_guard_at=1,bad_guard=change)
                self.assertFalse(f.model.run(True)['modeled_completed'])
    def test_launch_outside_ten_second_gate_rejected(self):self.failed(launch_delay=10001)
    def test_stale_reply_rejected(self):self.failed(stale_ms=2001)
    def test_source_build_phase_episode_sequence_and_padding_changes_rejected(self):
        for offset in (0,8,24,56,88,104,108,109):
            with self.subTest(offset=offset),TemporaryDirectory() as d:
                f=fixture083(Path(d)/'marker',wire_change=offset)
                self.assertFalse(f.model.run(True)['modeled_completed'])
    def test_replaced_snapshot_after_guard_rejected_and_lease_closed(self):self.failed(replaced_snapshot=True)
    def test_missing_boundary_exclusion_or_held_handle_rejected(self):
        for change in ({'boundary':False},{'write_delete_excluded':False},{'handle_held':False}):
            with self.subTest(change=change),TemporaryDirectory() as d:
                f=fixture083(Path(d)/'marker',bad_snapshot=change)
                self.assertFalse(f.model.run(True)['modeled_completed']);self.assertTrue(all(l.closed for l in f.peer.leases))
    def test_changed_file_owner_acl_link_metadata_share_or_seal_rejected(self):
        for change in ({'file_identity':(5,6,7)},{'private_owner':False},
            {'no_reparse_single_link':False},{'metadata_shares_all':False},
            {'companion_blockers':1},{'synthetic_size':83},{'metadata_position':0},{'regular_file':False},
            {'synthetic_pattern_verified':False}):
            with self.subTest(change=change),TemporaryDirectory() as d:
                f=fixture083(Path(d)/'marker',bad_proof_operation=('independent','metadata_after'),bad_private=change)
                self.assertFalse(f.model.run(True)['modeled_completed'])
    def test_other_native_error_cannot_prove_write_delete_exclusion(self):self.failed(wrong_control_error=True)
    def test_blocked_call_returning_after_hold_margin_is_rejected(self):self.failed(blocked_return=True)
    def test_wait_overshoot_is_measured_and_rejected(self):self.failed(wait_overshoot=32000)
    def test_hold_longer_than_declared_close_window_rejected(self):self.failed(hold_extra=1001)
    def test_owned_cleanup_after_interrupted_factory(self):
        f,r=self.failed(factory_interrupt=True);self.assertEqual(r['first_failure']['code'],'interrupted')
        self.assertEqual(f.peer.cleanup_calls,1)
    def test_owned_cleanup_after_interrupted_operation(self):self.failed(interrupt_operation=True)
    def test_cleanup_failure_invalidates_otherwise_completed_model(self):
        f,r=self.failed(cleanup_failed=True);self.assertFalse(r['cleanup_confirmed'])
        self.assertEqual(r['first_failure']['stage'],'cleanup')
    def test_lease_close_failure_invalidates_and_still_cleans_owner(self):self.failed(lease_close_failed=True)
    def test_reports_and_reservation_do_not_export_private_identity(self):
        f,r=self.run_case(factory_interrupt=True)
        public=json.dumps(r)+(self.root/'marker').read_text()
        for v in ('500123987','700789321','private-owner',str(self.root),'episode-private!'):
            self.assertNotIn(v,public)
        self.assertEqual(r['sdk_connections'],0);self.assertEqual(r['orders'],0)
    def test_source_contract_is_exact_uncompiled_and_has_no_authority(self):
        c=source_contract083(dict.fromkeys(SOURCE_INPUTS,'a'*64))
        self.assertFalse(c['compiled']);self.assertFalse(c['execution_authorized'])
        for b in ({SOURCE_INPUTS[0]:'a'*64},{**dict.fromkeys(SOURCE_INPUTS,'a'*64),'extra':'a'*64},
                  dict.fromkeys(SOURCE_INPUTS,True)):
            with self.assertRaises(ProbeRejected):source_contract083(b)
    def test_private_binding_identity_boolean_or_replacement_rejected(self):
        for ident in ((True,2,3),(0,2,3),(1,0,0),[1,2,3]):
            with self.assertRaises(ProbeRejected):Bindings083('a'*64,'b'*64,'c'*64,'d'*64,ident,(1,2,3))
    def test_meter_date_shape_boolean_reversal_and_skew_latch(self):
        for mode in ('date','shape','bool','reverse','skew'):
            c=Clock083();m=Meter083(c)
            if mode=='date':c.utc+=86400000
            elif mode=='shape':m.clock=lambda:(1,2)
            elif mode=='bool':m.clock=lambda:(True,0,0)
            elif mode=='reverse':c.boot-=1
            else:c.utc+=1001
            with self.subTest(mode=mode),self.assertRaises(ProbeRejected):m.check()
            with self.assertRaises(ProbeRejected):m.check()
    def test_outer_clock_expiry_rejected(self):
        c=Clock083();m=Meter083(c);c.advance(120000)
        with self.assertRaises(ProbeRejected):m.check()
    def test_finite_operation_caps_and_unknown_bucket(self):
        for key in ('operations','guards','polls','clock_samples','unapproved'):
            m=Meter083(Clock083())
            if key in m.counts:m.counts[key]=LIMITS[key]
            with self.subTest(key=key),self.assertRaises(ProbeRejected):m.consume(key)
    def test_exact_signal_size_trailing_truncated_and_unknown_bytes(self):
        f=self.f();raw=encode_signal083('ready',1,f.bindings,f.model.episode,100000,160000)
        self.assertEqual(len(raw),144)
        for bad in (raw+b'x',raw[:-1],b'x'*144):
            with self.assertRaises(ProbeRejected):decode_signal083(bad,'ready',1,f.bindings,f.model.episode,100000,160000,0)
    def test_bool_sequence_future_signal_and_wrong_deadline_rejected(self):
        f=self.f();raw=encode_signal083('ready',1,f.bindings,f.model.episode,100000,160000)
        for seq,now,deadline in ((True,100000,160000),(1,99999,160000),(1,100000,160001)):
            with self.assertRaises(ProbeRejected):decode_signal083(raw,'ready',seq,f.bindings,f.model.episode,now,deadline,0)
    def test_ready_release_cannot_claim_hold_times(self):
        self.assertEqual(window_reason083(1,100000,160000,1,0,100000,160000,0),4)
        self.assertEqual(window_reason083(2,100000,160000,0,1,100000,160000,0),4)
    def test_signal_freshness_inclusive_boundary_and_episode_strict_deadline(self):
        self.assertEqual(window_reason083(1,100000,160000,0,0,102000,160000,0),0)
        self.assertEqual(window_reason083(1,100000,160000,0,0,102001,160000,0),2)
        self.assertEqual(window_reason083(1,160000,160000,0,0,160000,160000,0),3)
    def test_launch_gate_inclusive_then_rejects_outside(self):
        self.assertEqual(window_reason083(3,110000,160000,110000,0,110000,160000,100000),0)
        self.assertEqual(window_reason083(3,110001,160000,110001,0,110001,160000,100000),4)
    def test_control_start_and_trailing_guard_end_strict_margins(self):
        self.assertEqual(control_reason083(100250,100251,100252,100000),5)
        self.assertEqual(control_reason083(100251,100252,129749,100000),0)
        self.assertEqual(control_reason083(100251,100252,129750,100000),5)
    def test_closed_signal_requires_full_thirty_second_hold(self):
        self.assertEqual(window_reason083(4,130000,160000,100000,129999,130000,160000,99999),6)
        self.assertEqual(window_reason083(4,130000,160000,100000,130000,130000,160000,99999),0)
    def test_cleanup_record_boolean_is_not_an_integer_proof(self):
        self.assertFalse(same_record(Cleanup083(unconfirmed_handles=False),Cleanup083()))
    def test_default_boolean_type_and_native_peer_refused(self):
        f=self.f()
        with self.assertRaises(ProbeRejected):f.model.run(1)
        with self.assertRaises(ValueError):Owner083().adopt(NS(model_only=False))
    def test_python_and_portable_mql_header_window_decisions_agree(self):
        windows=[]
        for kind in range(6):
            for age in (0,2000,2001):windows.append((kind,100000,160000,0,0,100000+age,160000,0))
        for delay in (0,10000,10001):windows.append((3,100000+delay,160000,100000+delay,0,100000+delay,160000,100000))
        for end in (129999,130000,131000,131001):windows.append((4,132000,160000,100000,end,132000,160000,99999))
        windows.extend([(1,160000,160000,0,0,160000,160000,0),
                        (1,100001,160000,0,0,100000,160000,0),
                        (1,-1,160000,0,0,100000,160000,0)])
        controls=[(s,e,g,100000) for s,e,g in ((100250,100251,100252),(100251,100252,129749),
            (100251,100252,129750),(100251,100250,100252),(-1,1,2),(100251,100252,100251))]
        expected=[window_reason083(*v) for v in windows]+[control_reason083(*v) for v in controls]
        cpp='#include <iostream>\n#include "'+str(ROOT/'mt5/Scripts/Synchronization083.mqh')+'"\nint main(){\n'
        cpp+=''.join('std::cout << SynchronizationWindow083('+','.join(str(x) for x in v)+') << "\\n";\n' for v in windows)
        cpp+=''.join('std::cout << SynchronizationControl083('+','.join(str(x) for x in v)+') << "\\n";\n' for v in controls)+'}\n'
        with TemporaryDirectory() as d:
            p=Path(d);(p/'probe.cpp').write_text(cpp)
            subprocess.run(['g++','-std=c++17',str(p/'probe.cpp'),'-o',str(p/'probe')],check=True,capture_output=True)
            actual=subprocess.run([str(p/'probe')],check=True,capture_output=True,text=True).stdout
        self.assertEqual([int(x) for x in actual.splitlines()],expected);self.assertEqual(len(expected),34)
