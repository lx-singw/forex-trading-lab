from dataclasses import replace
import importlib.util
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from forex_demo_lab.sharing_runtime_066 import *
from forex_demo_lab.sharing_companion_065 import Companion065
from forex_demo_lab.sharing_probe_062 import Open
from forex_demo_lab.private_guard_065 import Identity065
from test_sharing_companion_065 import Files
from test_transport_lifecycle_060 import Clock
from test_mql_sharing_064 import record,text

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('entry066',ROOT/'scripts/runtime-native-sharing-066.py')
entry=importlib.util.module_from_spec(spec);spec.loader.exec_module(entry)


class ExternalFiles(Files):
    """Synthetic external peer, deliberately NOT an owned helper handle."""
    def __init__(self,meter,clock):
        super().__init__(meter);self.clock=clock;self.external=True;self.error='sharing_violation'
    def open(self,role):
        if self.external and role.startswith('control_') and 100000<=self.clock.boot<=130000:
            self.meter.consume('opens');return Open(None,self.error)
        return super().open(role)


class Runtime066Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        self.clock=Clock();self.clock.boot=99000;self.m=Meter066(self.clock)
        self.bindings=dict.fromkeys(('source','ex5','terminal','editor','preparation','policy'),'a'*64)
        self.s=Reservation066(self.root/'reservation',self.bindings,self.m)
        self.f=ExternalFiles(self.m,self.clock);self.guard=lambda:True
        self.c=Companion065(self.f,self.m,lambda:self.guard())
        self.log=self.root/'private.log';self.log.write_bytes('old\r\n'.encode('utf-16-le'))
        self.r=Runtime066(self.c,self.s,self.m,lambda:self.guard(),self.log,self.clock.advance)
    def until_enabled(self):
        for command in COMMANDS[:3]:self.r.command(command)
        self.clock.advance(1000);self.r.command('arm-enabled')
    def saved(self,rows=None):
        with self.log.open('ab') as f:
            f.write(('\r\n'.join(text(r) for r in (rows if rows is not None else [record(),record(True)]))+'\r\n').encode('utf-16-le'))
    def success(self,rows=None):
        self.until_enabled();self.r.command('probe');self.saved(rows);self.r.command('logs-saved')
        return self.r.finish()
    def rejected_command(self,command):
        with self.assertRaises(ProbeRejected):self.r.command(command)
        result=self.r.finish();self.assertFalse(result['completed']);self.assertFalse(self.f.active)
        return result
    def test_complete_sequence_and_exact_native_window_match(self):
        result=self.success();self.assertTrue(result['completed'])
        self.assertFalse(result['native_mql_verified']);self.assertFalse(result['orders_available'])
        self.assertEqual([p.error for p in self.c.probes],[0,0,32,32,0,0])
        self.assertEqual([p.blocking_companion_handles for p in self.c.probes],[0]*6)
        self.assertEqual(self.m.counts['log_reads'],1);self.assertEqual(self.m.counts['script_arms'],2)
    def test_enabled_before_disabled_is_stopped(self):self.rejected_command('arm-enabled')
    def test_missing_baseline_rejected_before_launch(self):self.rejected_command('arm-disabled')
    def test_duplicate_disabled_arm_rejected(self):
        self.r.command('baseline-saved');self.r.command('arm-disabled');self.rejected_command('arm-disabled')
    def test_duplicate_enabled_launch_rejected(self):
        self.until_enabled();self.rejected_command('arm-enabled')
    def test_extra_command_after_saved_is_rejected(self):
        self.until_enabled();self.r.command('probe');self.saved();self.r.command('logs-saved')
        self.rejected_command('logs-saved')
    def test_missing_launch_confirmation_rejected(self):
        self.r.command('baseline-saved');self.r.command('arm-disabled');self.rejected_command('probe')
    def test_no_external_reader_is_not_success(self):
        self.f.external=False;self.until_enabled();self.rejected_command('probe')
    def test_access_denied_is_not_sharing_violation(self):
        self.f.error='access_denied';self.until_enabled();self.rejected_command('probe')
    def test_owned_helper_reader_invalidates_independence(self):
        self.until_enabled();self.c.opened('reader');self.rejected_command('probe')
    def test_late_probe_stops_without_retry(self):
        self.until_enabled();self.clock.advance(10001);self.rejected_command('probe')
        self.assertEqual(len(self.c.probes),2)
    def test_slow_full_guards_can_miss_hold_and_fail(self):
        self.until_enabled()
        def slow():self.clock.advance(3000);return True
        self.guard=slow;self.rejected_command('probe')
    def test_bad_wait_clock_discontinuity_rejected(self):
        self.until_enabled();self.r.wait=lambda ms:setattr(self.clock,'boot',self.clock.boot+ms)
        self.rejected_command('probe')
    def test_no_progress_wait_is_finitely_bounded(self):
        self.until_enabled();calls=[];self.r.wait=lambda ms:calls.append(ms)
        self.rejected_command('probe');self.assertEqual(len(calls),36)
    def test_native_hold_window_must_match_not_log_arrival(self):
        r=record(True);r['hold_start_boot_ms']=140000;r['hold_end_boot_ms']=170000
        self.assertFalse(self.success([record(),r])['completed'])
    def test_stale_or_repeated_native_records_rejected(self):
        self.assertFalse(self.success([record(),record(True),record(True)])['completed'])
    def test_failed_enabled_native_record_rejected(self):
        r=record(True);r['reason_code']=18;self.assertFalse(self.success([record(),r])['completed'])
    def test_missing_disabled_native_record_rejected(self):
        self.assertFalse(self.success([record(True)])['completed'])
    def test_reversed_log_records_rejected(self):
        self.assertFalse(self.success([record(True),record()])['completed'])
    def test_empty_final_saved_range_stops_no_second_read(self):
        self.until_enabled();self.r.command('probe');self.rejected_command('logs-saved')
        self.assertEqual(self.m.counts['log_reads'],1)
    def test_truncated_saved_log_rejected(self):
        self.until_enabled();self.r.command('probe');self.log.write_bytes(b'');self.rejected_command('logs-saved')
    def test_replaced_saved_log_rejected(self):
        self.until_enabled();self.r.command('probe');self.log.rename(self.root/'old');self.log.write_bytes(b'\0'*100)
        self.rejected_command('logs-saved')
    def test_guard_changes_stop_and_cleanup_owned_handles(self):
        self.until_enabled();self.guard=lambda:False;self.rejected_command('probe')
    def test_expiry_cleanup_still_attempted(self):
        self.until_enabled();self.clock.advance(900000);self.rejected_command('probe')
    def test_uncertain_close_invalidates_cleanup(self):
        self.until_enabled();self.f.close_ok=False;result=self.r.finish()
        self.assertFalse(result['completed']);self.assertGreater(result['cleanup']['unconfirmed_handles'],0)
        self.f.close_ok=True;self.f.finish()
    def test_finish_is_once_and_missing_steps_fail(self):
        self.assertFalse(self.r.finish()['completed'])
        with self.assertRaises(ProbeRejected):self.r.finish()
    def test_private_exceptions_are_fixed_reason(self):
        def fail():raise RuntimeError('account secret SID private-path')
        self.guard=fail;result=self.rejected_command('baseline-saved')
        self.assertNotIn('secret',json.dumps(result));self.assertNotIn('SID',json.dumps(result))
    def test_reservation_is_exclusive_and_phase_new(self):
        r=json.loads((self.root/'reservation').read_text());self.assertEqual(r['phase'],PHASE)
        with self.assertRaises(ProbeRejected):Reservation066(self.root/'reservation',self.bindings,Meter066(Clock()))
    def test_bad_binding_schema_or_boolean_budget_rejected(self):
        with self.assertRaises(ProbeRejected):Reservation066(self.root/'x',{'source':'a'*64},self.m)
        with self.assertRaises(ProbeRejected):self.m.consume('commands',True)
    def test_extra_native_authorization_fields_and_bools_rejected(self):
        a=dict(version='sharing_native_067_v1',preparation_sha256='a'*64,policy_sha256='b'*64,
            phase=PHASE,date=DATE,maximum_sdk_connections=1,maximum_launches=2,maximum_log_reads=1,
            maximum_log_bytes=65536,maximum_market_reads=0,maximum_orders=0,maximum_receipt_permissions=0)
        entry.authorization(a,'a'*64,'b'*64)
        for change in ({'maximum_orders':True},{'extra':0},{'date':'2026-10-08'},{'preparation_sha256':'c'*64}):
            with self.assertRaises(ProbeRejected):entry.authorization({**a,**change},'a'*64,'b'*64)
    def test_sdk_single_attempt_and_cleanup_ownership_on_failure(self):
        peer=Identity065(7,11,'terminal','a'*64,1,'hidden');reader=type('R',(),dict(unique_pid=lambda s:7,identity=lambda s,p:peer))()
        calls=[];sdk=type('SDK',(),dict(__version__='5.0.6231',initialize=lambda s,*a,**k:calls.append(1) or False))()
        with self.assertRaises(ProbeRejected):attach_existing(sdk,self.s,reader,peer,self.m)
        self.assertTrue(self.s.spent);self.assertEqual(calls,[1])
        with self.assertRaises(ProbeRejected):attach_existing(sdk,self.s,reader,peer,self.m)
        self.assertEqual(calls,[1])
    def test_sdk_wrong_version_or_changed_process_never_initialize(self):
        peer=Identity065(7,11,'terminal','a'*64,1,'hidden');calls=[]
        sdk=type('SDK',(),dict(__version__='wrong',initialize=lambda s,*a,**k:calls.append(1)))()
        reader=type('R',(),dict(unique_pid=lambda s:8,identity=lambda s,p:peer))()
        with self.assertRaises(ProbeRejected):attach_existing(sdk,self.s,reader,peer,self.m)
        sdk.__version__='5.0.6231'
        with self.assertRaises(ProbeRejected):attach_existing(sdk,self.s,reader,peer,self.m)
        self.assertFalse(self.s.spent);self.assertEqual(calls,[])
    def test_sdk_peer_changes_after_initialize_rejected(self):
        peer=Identity065(7,11,'terminal','a'*64,1,'hidden');pids=iter([7,8])
        reader=type('R',(),dict(unique_pid=lambda s:next(pids),identity=lambda s,p:peer))()
        sdk=type('SDK',(),dict(__version__='5.0.6231',initialize=lambda s,*a,**k:True))()
        with self.assertRaises(ProbeRejected):attach_existing(sdk,self.s,reader,peer,self.m)
        self.assertTrue(self.s.spent)
    def test_helper_identity_and_logon_rechecked_uncached(self):
        h=Identity065(9,11,'python','a'*64,1,'hidden');peer=replace(h,pid=7,image='terminal')
        calls=[];base=type('B',(),dict(identity=lambda s,p:calls.append(p) or (h if p==9 else peer)))()
        r=PrivateReader066(base,h);self.assertEqual(r.identity(7),peer);self.assertEqual(r.identity(7),peer)
        self.assertEqual(calls,[9,7,9,7]);base.identity=lambda p:replace(h,creation=12) if p==9 else peer
        with self.assertRaises(ProbeRejected):r.identity(7)
    def test_helper_peer_session_or_logon_mismatch_rejected(self):
        h=Identity065(9,11,'python','a'*64,1,'hidden')
        for change in ({'session':2},{'logon':'other'}):
            peer=replace(h,pid=7,**change);base=type('B',(),dict(identity=lambda s,p:h if p==9 else peer))()
            with self.assertRaises(ProbeRejected):PrivateReader066(base,h).identity(7)
    def test_deployment_exclusive_hash_bound_and_no_overwrite(self):
        src=self.root/'build.ex5';src.write_bytes(b'compiled');scripts=self.root/'Scripts';scripts.mkdir()
        import hashlib
        expected=hashlib.sha256(src.read_bytes()).hexdigest()
        reader=type('R',(),dict(hash_file=lambda s,p:hashlib.sha256(Path(p).read_bytes()).hexdigest()))()
        name='ForexDemoLab066-'+'a'*32
        out=deploy_owned(src,scripts,name,expected,reader,lambda:True,self.m)
        self.assertEqual(out.read_bytes(),b'compiled');self.assertEqual(self.m.counts['deployment_writes'],1)
        with self.assertRaises(Exception):deploy_owned(src,scripts,name,expected,reader,lambda:True,Meter066(Clock()))
        self.assertEqual(out.read_bytes(),b'compiled')
    def test_deployment_hash_change_or_symlink_rejected(self):
        src=self.root/'build.ex5';src.write_bytes(b'compiled');scripts=self.root/'Scripts';scripts.mkdir()
        reader=type('R',(),dict(hash_file=lambda s,p:'b'*64))()
        with self.assertRaises(ProbeRejected):deploy_owned(src,scripts,'ForexDemoLab066-'+'a'*32,'a'*64,reader,lambda:True,self.m)
        link=self.root/'link';link.symlink_to(scripts,target_is_directory=True)
        with self.assertRaises(ProbeRejected):no_reparse(link)
