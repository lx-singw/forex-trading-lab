from dataclasses import replace
import ctypes as C
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from forex_demo_lab.sharing_companion_065 import *
from forex_demo_lab.private_guard_065 import FullGuard065, Identity065, NativeIdentity065, PROCESS_ENTRY, SID_ATTRIBUTE
from forex_demo_lab.native_files_065 import NativeFiles065, FILEINFO, FILETIME, SECURITY
from forex_demo_lab.sharing_session_065 import LaunchSession065, SavedRange065
from forex_demo_lab.readiness_adapter_061 import sharing_compatible
from test_fresh_data_031 import API as AccountAPI
from test_transport_lifecycle_060 import Clock
from test_mql_sharing_064 import record, text


class Files:
    def __init__(self,meter):
        self.meter=meter;self.active={};self.data=b'';self.ident=(1,2,3)
        self.created=False;self.proof={};self.events=[];self.hook=lambda role:None
        self.close_ok=True;self.finished=False;self.metadata_masks=False
    def setup(self):self.meter.consume('directories');self.created=True
    def open(self,role):
        self.meter.consume('opens');self.hook(role);self.events.append(role)
        access,share,_,_=ROLE_SPECS[role]
        # Attribute-only/READ_CONTROL access is modeled separately from data access.
        bits=(1 if access&0x80000000 else 0)|(2 if access&0x40000000 else 0)|(4 if access&0x10000 else 0)
        if role=='metadata' and self.metadata_masks:bits,share=1,1
        for r,a,s,pos in self.active.values():
            if role!='directory' and r!='directory' and not sharing_compatible(a,s,bits,share):
                return Open(None,'sharing_violation')
        h=object();self.active[h]=[role,bits,share,0];return Open(h)
    def stamp(self,h,directory=False):
        self.meter.consume('stamps');role,_,_,pos=self.active[h]
        return replace(Stamp(self.ident,0 if directory else len(self.data),
            -1 if role in ('metadata','control_write','control_delete') else pos,
            directory,True,True,False,1),**self.proof)
    def write(self,h,raw):self.meter.consume('writes');self.data=raw;self.active[h][3]=len(raw);return len(raw)
    def read(self,h,n):self.meter.consume('reads');self.active[h][3]=len(self.data);return self.data,len(self.data)
    def close(self,h):
        self.meter.cleanup('closes')
        if h not in self.active:return False
        if self.close_ok:del self.active[h]
        return self.close_ok
    def blocking_readers(self):return sum(v[0] in ('seal','reader') for v in self.active.values())
    def finish(self):
        self.finished=True
        for h in list(self.active):self.close(h)
        return dict(all_handles_closed=not self.active,unconfirmed_handles=len(self.active),
                    allocations_released=True,synthetic_directory_retained=self.created)


class Reader:
    def __init__(self,peer,meter):self.peer=peer;self.meter=meter;self.identities=0;self.hashes=[];self.pids=[]
    def unique_pid(self):self.pids.append(self.peer.pid);return self.peer.pid
    def identity(self,pid):self.identities+=1;return self.peer
    def hash_file(self,path):self.meter.consume('hash_reads');self.hashes.append(path);return 'a'*64


class Companion065Tests(unittest.TestCase):
    def setUp(self):
        self.clock=Clock();self.meter=Meter065(self.clock);self.files=Files(self.meter)
    def failed(self):
        r=run_compatibility(self.files,self.meter)
        self.assertFalse(r['passed']);self.assertTrue(self.files.finished);return r
    def guard(self):
        a=AccountAPI();a.terminal.path=r'C:\Program Files\MetaTrader 5'
        a.terminal.data_path=r'C:\private-demo';a.terminal.build=6244
        peer=Identity065(7,11,r'c:\program files\metatrader 5\terminal64.exe','a'*64,1,'private-logon')
        reader=Reader(peer,self.meter)
        g=FullGuard065(a,reader,peer,a.terminal.data_path,6244,('editor','a'*64),('artifact','a'*64),self.meter)
        return a,reader,g
    def test_compatibility_sequence_and_all_closed(self):
        r=run_compatibility(self.files,self.meter)
        self.assertTrue(r['passed']);self.assertFalse(r['native_mql_verified'])
        self.assertEqual([p['error'] for p in r['controls']],[0,0,32,32,0,0])
        self.assertEqual([p['blocking_companion_handles'] for p in r['controls']],[0,0,1,1,0,0])
        self.assertEqual(self.files.active,{})
    def test_metadata_masking_fails_pre_control(self):
        self.files.metadata_masks=True;self.failed()
    def test_unknown_or_access_denied_is_not_error32(self):
        old=self.files.open
        self.files.open=lambda role: Open(None,'access_denied') if role=='control_write' else old(role)
        self.failed()
    def test_short_write_rejected_and_no_refund(self):
        self.files.write=lambda h,raw: 20;self.failed()
        self.assertNotIn('metadata',self.files.events)
    def test_partial_read_rejected(self):
        self.files.read=lambda h,n:(DATA[:83],83);self.failed()
    def test_corrupt_same_length_read_rejected(self):
        self.files.read=lambda h,n:(b'x'*84,84);self.failed()
    def test_identity_changes_before_metadata_rejected(self):
        self.files.hook=lambda r:setattr(self.files,'ident',(1,9,3)) if r=='metadata' else None
        self.failed()
    def test_reparse_owner_path_link_proofs_required(self):
        for proof in (dict(reparse=True),dict(security_verified=False),dict(path_verified=False),dict(links=2)):
            m=Meter065(self.clock);f=Files(m);f.proof=proof
            self.assertFalse(run_compatibility(f,m)['passed']);self.assertTrue(f.finished)
    def test_held_helper_seal_rejected_for_independent_controls(self):
        c=Companion065(self.files,self.meter,lambda:True);c.prepare()
        with self.assertRaisesRegex(ProbeRejected,'helper_seal_masks_observation'):c.controls('independent')
        c.finish()
    def test_extra_helper_reader_blocks_real_observation(self):
        c=Companion065(self.files,self.meter,lambda:True);c.prepare()
        c.opened('reader');c.release_seal()
        with self.assertRaisesRegex(ProbeRejected,'helper_seal_masks_observation'):c.controls('independent')
        c.finish()
    def test_prepare_and_control_cannot_repeat(self):
        c=Companion065(self.files,self.meter,lambda:True);c.prepare()
        with self.assertRaisesRegex(ProbeRejected,'session_unavailable'):c.prepare()
        with self.assertRaisesRegex(ProbeRejected,'session_order_rejected'):c.controls('pre')
        c.finish()
    def test_failed_close_invalidates_and_tracks_uncertainty(self):
        self.files.close_ok=False;r=self.failed();self.assertEqual(r['reason'],'cleanup_unconfirmed')
    def test_native_exception_is_redacted_and_cleanup_runs(self):
        def fail(role):raise RuntimeError('private account secret')
        self.files.hook=fail;r=self.failed();self.assertNotIn('secret',json.dumps(r))
    def test_operation_budget_burned_before_open(self):
        self.meter.counts['opens']=16;self.failed();self.assertEqual(self.files.events,[])
    def test_cleanup_not_prevented_by_expiry(self):
        self.files.hook=lambda r:self.clock.advance(900000) if r=='metadata' else None
        self.failed();self.assertEqual(self.files.active,{})
    def test_clock_reverse_and_discontinuity_rejected(self):
        self.clock.advance(1);self.meter.check();self.clock.mono-=1
        with self.assertRaises(ProbeRejected):self.meter.check()
        m=Meter065(Clock());m.clock.utc+=2001
        with self.assertRaises(ProbeRejected):m.check()
    def test_cleanup_cap_is_counted_even_after_budget_exhaustion(self):
        self.meter.counts['closes']=LIMITS['closes'];self.meter.cleanup('closes')
        self.assertTrue(self.meter.cleanup_exceeded)
    def test_boolean_count_and_unknown_budget_rejected(self):
        for key,amount in (('reads',True),('unknown',1),('opens',0)):
            with self.assertRaises(ProbeRejected):self.meter.consume(key,amount)
    def test_full_guard_rehashes_and_requeries_every_time(self):
        a,r,g=self.guard();self.assertTrue(g());self.assertTrue(g())
        self.assertEqual(r.identities,4);self.assertEqual(r.hashes,['editor','artifact']*2)
        self.assertEqual(len(r.pids),4);self.assertEqual(self.meter.counts['guards'],2)
        self.assertGreater(self.meter.counts['sdk_queries'],10)
    def test_actual_real_contest_rejected_with_demo_server_text(self):
        for mode in (1,2):
            a,r,g=self.guard();a.account.trade_mode=mode;a.account.server='demo-looking-name'
            with self.assertRaisesRegex(ProbeRejected,'private_guard_rejected'):g()
    def test_guard_currency_algo_and_instrument_rechecked(self):
        for field,value,target in (('currency','EUR','account'),('trade_allowed',True,'terminal')):
            a,r,g=self.guard();self.assertTrue(g());setattr(getattr(a,target),field,value)
            with self.assertRaises(ProbeRejected):g()
    def test_guard_account_identity_changes_stop_and_latch(self):
        a,r,g=self.guard();g();a.account.login+=1
        with self.assertRaises(ProbeRejected):g()
        before=r.identities;a.account.login-=1
        with self.assertRaises(ProbeRejected):g()
        self.assertEqual(r.identities,before)
    def test_guard_terminal_root_build_changes_rejected(self):
        for field,value in (('build',6245),('data_path',r'C:\changed'),('path',r'C:\changed')):
            a,r,g=self.guard();setattr(a.terminal,field,value)
            with self.assertRaises(ProbeRejected):g()
    def test_guard_process_creation_hash_logon_session_changes(self):
        for key,value in (('creation',12),('digest','b'*64),('logon','other'),('session',2)):
            a,r,g=self.guard();r.peer=replace(r.peer,**{key:value})
            with self.assertRaises(ProbeRejected):g()
    def test_guard_editor_or_artifact_hash_change(self):
        a,r,g=self.guard();r.hash_file=lambda p:'b'*64
        with self.assertRaises(ProbeRejected):g()
    def test_guard_slow_work_and_date_expiry_stop(self):
        a,r,g=self.guard();original=r.hash_file
        def slow(p):self.clock.advance(900000);return original(p)
        r.hash_file=slow
        with self.assertRaises(ProbeRejected):g()
    def test_terminal_file_binding_cannot_use_temp_folder(self):
        a,r,g=self.guard();self.files.scope='terminal';self.files.parent=Path('wrong')
        with self.assertRaises(ProbeRejected):g.bind_files(self.files)
    def test_guard_repr_hides_private_identity(self):
        a,r,g=self.guard();self.assertNotIn('private-logon',repr(r.peer));self.assertNotIn('terminal64',repr(r.peer))
    def test_process_and_file_abi_layouts(self):
        self.assertEqual(C.sizeof(PROCESS_ENTRY),568);self.assertEqual(PROCESS_ENTRY.exe.offset,44)
        self.assertEqual(C.sizeof(SID_ATTRIBUTE),16);self.assertEqual(C.sizeof(FILETIME),8)
        self.assertEqual(C.sizeof(FILEINFO),52);self.assertEqual(C.sizeof(SECURITY),24)
    def test_backend_has_new_phase_and_metadata_without_pointer_query(self):
        src=(Path(__file__).resolve().parents[1]/'src/forex_demo_lab/native_files_065.py').read_text()
        self.assertNotIn('NativeFiles062',src);self.assertNotIn('ForexDemoSharing062',src)
        self.assertIn('if metadata:position.value=-1',src)
        self.assertEqual(ROLE_SPECS['metadata'][:2],(0x20080,7))
    def test_reservation_restart_and_repeat_launches_rejected(self):
        with TemporaryDirectory() as tmp:
            p=Path(tmp)/'r';bindings=dict.fromkeys(('source','ex5','terminal','editor'),'a'*64)
            s=LaunchSession065(p,bindings,self.meter);s.sdk_attempt();s.arm('disabled');s.arm('enabled')
            with self.assertRaises(ProbeRejected):s.sdk_attempt()
            with self.assertRaises(ProbeRejected):s.arm('enabled')
            with self.assertRaises(ProbeRejected):LaunchSession065(p,bindings,Meter065(self.clock))
    def test_wrong_order_launch_latches_session(self):
        with TemporaryDirectory() as tmp:
            s=LaunchSession065(Path(tmp)/'r',dict.fromkeys(('source','ex5','terminal','editor'),'a'*64),self.meter)
            with self.assertRaises(ProbeRejected):s.arm('enabled')
            with self.assertRaises(ProbeRejected):s.arm('disabled')
    def test_saved_range_exact_once_and_no_raw_identity_export(self):
        with TemporaryDirectory() as tmp:
            p=Path(tmp)/'private.log';p.write_bytes(b'old'.decode().encode('utf-16-le'))
            r=SavedRange065(p,self.meter)
            with p.open('ab') as out:out.write((text(record())+'\r\n'+text(record(True))).encode('utf-16-le'))
            self.assertEqual(r.read(),[record(),record(True)])
            with self.assertRaisesRegex(ProbeRejected,'saved_log_unavailable'):r.read()
    def test_saved_range_truncation_replacement_and_empty_rejected(self):
        for action in ('truncate','replace','empty'):
            with TemporaryDirectory() as tmp:
                p=Path(tmp)/'log';p.write_bytes(b'\0'*10);m=Meter065(self.clock);r=SavedRange065(p,m)
                if action=='truncate':p.write_bytes(b'\0'*2)
                elif action=='replace':p.unlink();p.write_bytes(b'\0'*12)
                with self.assertRaises(ProbeRejected):r.read()
                with self.assertRaises(ProbeRejected):r.read()
    def test_saved_range_size_bound_and_symlink_rejected(self):
        with TemporaryDirectory() as tmp:
            p=Path(tmp)/'log';p.write_bytes(b'');r=SavedRange065(p,self.meter);p.write_bytes(b'\0'*65538)
            with self.assertRaises(ProbeRejected):r.read()
            link=Path(tmp)/'link';link.symlink_to(p)
            with self.assertRaises(ProbeRejected):SavedRange065(link,Meter065(self.clock))
    def test_native_windows_constructor_is_not_called_by_pure_tests(self):
        # Class imports expose no WinDLL calls; all new tests use independent files.
        self.assertEqual(self.meter.counts['native_calls'],0)
        self.assertEqual(self.meter.counts['sdk_connections'],0)
        self.assertFalse(run_compatibility(self.files,self.meter)['native_mql_verified'])
