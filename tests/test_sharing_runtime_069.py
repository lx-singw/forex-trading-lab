from dataclasses import replace
import hashlib
import importlib.util
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch

from forex_demo_lab.sharing_runtime_069 import *
from forex_demo_lab.sharing_runtime_066 import COMMANDS
from forex_demo_lab.sharing_companion_065 import Companion065
from forex_demo_lab.private_guard_065 import FullGuard065
from test_sharing_runtime_066 import ExternalFiles
from test_sharing_companion_065 import Reader
from test_fresh_data_031 import API as AccountAPI
from test_transport_lifecycle_060 import Clock
from test_mql_sharing_064 import record,text

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('entry069',ROOT/'scripts/runtime-native-sharing-069.py')
entry=importlib.util.module_from_spec(spec);spec.loader.exec_module(entry)
PROOF=dict(all_handles_closed=True,allocations_released=True,unconfirmed_handles=0)


class BootstrapReader:
    def __init__(self):
        self.peer=Identity065(7,11,'terminal','a'*64,1,'private-logon')
        self.helper=Identity065(9,12,'package/python3.13.exe','c'*64,1,'private-logon')
        self.hashes=[];self.ids=[];self.values={'terminal':'a'*64,'editor':'b'*64,
            'launcher':'d'*64,'config':'e'*64,'library':'f'*64}
    def unique_pid(self):return self.peer.pid
    def identity(self,pid):self.ids.append(pid);return self.helper if pid==9 else self.peer
    def hash_file(self,path):self.hashes.append(str(path));return self.values[str(path)]


class Runtime069Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        self.clock=Clock();self.clock.boot=99000;self.m=Meter069(self.clock);self.trace=Trace069()
        self.bindings=dict.fromkeys(('source','ex5','terminal','editor','preparation','policy','helper_profile'),'a'*64)
        self.s=Reservation069(self.root/'reservation',self.bindings,self.m)
        self.owner=Resources069(self.s,self.m,self.trace);self.calls=[]
        self.sdk=NS(__version__='5.0.6231',initialize=lambda *a,**k:self.calls.append('init') or True,
            shutdown=lambda:self.calls.append('shutdown'))
        self.reader=BootstrapReader()
        self.chain=HelperChain068(('launcher','d'*64),('config','e'*64),
            (('package/python3.13.exe','c'*64),),('library','f'*64),'private-alias')
    def boot(self,**changes):
        args=dict(reader=self.reader,terminal=('terminal','a'*64),editor=('editor','b'*64),
            chain=self.chain,executable='launcher',base_alias='private-alias',loaded_library=lambda:'library',
            helper_pid=9,python_version='3.13.14',trust=lambda:True,import_sdk=lambda:self.sdk,
            resources=self.owner,session=self.s,meter=self.m,trace=self.trace)
        return bootstrap(**{**args,**changes})
    def reject_boot(self,stage,**changes):
        with self.assertRaises(ProbeRejected):self.boot(**changes)
        self.assertEqual(self.trace.current,stage);self.assertFalse(self.calls)
        self.assertFalse(self.s.spent)
    def runtime(self):
        f=ExternalFiles(self.m,self.clock);self.owner.files=f
        c=ObservedCompanion069(Companion065(f,self.m,lambda:True),self.trace)
        log=self.root/'private.log';log.write_bytes('old\r\n'.encode('utf-16-le'))
        r=Runtime069(c,self.s,self.m,lambda:True,log,self.clock.advance,trace=self.trace)
        self.owner.runner=r;return r,f,log
    def finish_success(self,r,log):
        for command in COMMANDS[:3]:r.command(command)
        self.clock.advance(1000);r.command('arm-enabled');r.command('probe')
        with log.open('ab') as f:f.write(('\r\n'.join(text(x) for x in (record(),record(True)))+'\r\n').encode('utf-16-le'))
        r.command('logs-saved');return r.finish()
    def test_measured_package_helper_attaches_when_launcher_differs(self):
        private,peer=self.boot();self.assertEqual(peer,self.reader.peer)
        self.assertNotEqual(self.reader.helper.image,'launcher');self.assertEqual(self.calls,['init'])
        self.assertNotIn('private-alias',self.reader.hashes)
        private.identity(7);self.assertEqual(self.reader.ids[-2:],[9,7])
        self.assertTrue(self.owner.close()['sdk_shutdown_called']);self.assertEqual(self.calls,['init','shutdown'])
    def test_terminal_hash_failure_stops_before_trust_and_sdk(self):
        self.reader.values['terminal']='0'*64;self.reject_boot('terminal_image')
    def test_editor_hash_failure_stops_before_process_and_sdk(self):
        self.reader.values['editor']='0'*64;self.reject_boot('editor_image');self.assertFalse(self.reader.ids)
    def test_signature_rejection_stops_before_process(self):
        self.reject_boot('signature',trust=lambda:False);self.assertFalse(self.reader.ids)
    def test_terminal_native_image_mismatch_rejected(self):
        self.reader.peer=replace(self.reader.peer,image='other');self.reject_boot('terminal_process')
    def test_unmeasured_alternative_package_name_rejected(self):
        self.reader.helper=replace(self.reader.helper,image='package/python.exe');self.reject_boot('helper_chain')
    def test_changed_helper_digest_rejected(self):
        self.reader.helper=replace(self.reader.helper,digest='0'*64);self.reject_boot('helper_chain')
    def test_alias_is_only_exact_launch_input(self):self.reject_boot('helper_chain',base_alias='other')
    def test_loaded_library_change_rejected_before_import(self):self.reject_boot('helper_chain',loaded_library=lambda:'other')
    def test_config_changed_before_attach_rejected(self):
        self.reader.values['config']='0'*64;self.reject_boot('helper_chain')
    def test_python_version_changed_rejected(self):self.reject_boot('helper_chain',python_version='3.13.15')
    def test_helper_peer_session_logon_mismatch_rejected(self):
        for change in ({'session':2},{'logon':'other'}):
            self.reader.helper=replace(BootstrapReader().helper,**change)
            self.reject_boot('helper_chain')
    def test_later_helper_creation_change_is_not_cached(self):
        private,_=self.boot();self.reader.helper=replace(self.reader.helper,creation=13)
        with self.assertRaises(ProbeRejected):private.identity(7)
        self.owner.close();self.assertEqual(self.calls,['init','shutdown'])
    def test_sdk_import_exception_preserves_unspent_sdk_budget(self):
        def fail():raise RuntimeError('private SID account')
        with self.assertRaises(RuntimeError):self.boot(import_sdk=fail)
        self.assertEqual(self.trace.current,'sdk_import');self.assertFalse(self.s.spent)
        self.assertFalse(self.owner.close()['sdk_shutdown_called']);self.assertNotIn('private',json.dumps(self.trace.public()))
    def test_initialize_failure_still_shuts_down_once(self):
        self.sdk.initialize=lambda *a,**k:self.calls.append('init') or False
        with self.assertRaises(ProbeRejected):self.boot()
        self.assertEqual(self.trace.current,'sdk_attach');self.assertTrue(self.s.spent)
        self.owner.close()
        with self.assertRaises(ProbeRejected):self.owner.close()
        self.assertEqual(self.calls,['init','shutdown']);self.assertEqual(self.m.counts['sdk_shutdowns'],1)
    def test_sdk_wrong_version_never_burns_initialize(self):
        self.sdk.__version__='wrong'
        with self.assertRaises(ProbeRejected):self.boot()
        self.assertFalse(self.s.spent);self.owner.close();self.assertFalse(self.calls)
    def test_actual_real_and_contest_rejected_before_file_preparation(self):
        for mode in (1,2):
            a=AccountAPI();a.terminal.path=r'C:\Program Files\MetaTrader 5';a.terminal.data_path=r'C:\private-demo';a.terminal.build=6244
            a.account.trade_mode=mode;a.account.server='demo-looking-name'
            peer=Identity065(7,11,r'c:\program files\metatrader 5\terminal64.exe','a'*64,1,'private-logon')
            g=FullGuard065(a,Reader(peer,self.m),peer,a.terminal.data_path,6244,('editor','a'*64),('artifact','a'*64),self.m)
            with self.assertRaises(ProbeRejected):g()
        self.assertEqual(self.m.counts['directories'],0)
    def test_complete_sequence_cleanup_owner_does_not_repeat_finish(self):
        self.boot();r,f,log=self.runtime();out=self.finish_success(r,log)
        self.assertTrue(out['completed']);self.assertFalse(out['native_mql_verified'])
        closed=self.owner.close();self.assertIs(closed['outcome'],out);self.assertFalse(closed['errors'])
        self.assertFalse(f.active);self.assertEqual(self.calls,['init','shutdown'])
        self.assertTrue(all(x['completed'] for x in self.trace.public()))
    def test_unknown_command_stops_session_and_owned_files_close(self):
        r,f,_=self.runtime();r.command('baseline-saved');r.command('arm-disabled');r.command('disabled-done')
        with self.assertRaises(ProbeRejected):r.command('private-secret')
        out=self.owner.close();self.assertTrue(self.s.stopped);self.assertFalse(out['outcome']['completed'])
        self.assertFalse(f.active);self.assertNotIn('private-secret',json.dumps(self.trace.public()))
    def test_trace_nested_completion_retains_incomplete_inner_failure(self):
        def fail():raise ValueError('secret')
        with self.assertRaises(ValueError):self.trace.run('deployment',lambda:self.trace.run('helper_chain',fail))
        self.assertEqual(self.trace.current,'helper_chain')
        self.assertEqual([e['completed'] for e in self.trace.public()],[False,False])
    def test_trace_exhaustion_does_not_prevent_owned_cleanup(self):
        self.boot();r,f,_=self.runtime();r.command('baseline-saved');r.command('arm-disabled');r.command('disabled-done')
        while len(self.trace.events)<32:self.trace.run('preflight',lambda:True)
        out=self.owner.close();self.assertFalse(f.active);self.assertTrue(out['sdk_shutdown_called'])
        self.assertIn('cleanup_budget_rejected',out['errors']);self.assertEqual(len(self.trace.events),32)
    def test_expired_clock_still_releases_files_base_and_sdk(self):
        self.boot();r,f,_=self.runtime();r.command('baseline-saved');r.command('arm-disabled');r.command('disabled-done')
        events=[];self.owner.base=NS(finish=lambda:events.append('base') or dict(PROOF));self.clock.advance(900000)
        out=self.owner.close();self.assertFalse(f.active);self.assertEqual(events,['base'])
        self.assertTrue(out['sdk_shutdown_called']);self.assertIn('post_cleanup_clock_rejected',out['errors'])
    def test_missing_owned_cleanup_proof_cannot_pass(self):
        self.boot();self.owner.base=NS(finish=lambda:None)
        out=self.owner.close();self.assertIn('owned_cleanup_unconfirmed',out['errors']);self.assertTrue(out['sdk_shutdown_called'])
    def test_malformed_proof_does_not_prevent_sdk_shutdown(self):
        self.boot();self.owner.base=NS(finish=lambda:dict(PROOF,unconfirmed_handles=False))
        out=self.owner.close();self.assertIn('owned_cleanup_unconfirmed',out['errors']);self.assertTrue(out['sdk_shutdown_called'])
    def test_cleanup_exception_still_attempts_other_resources(self):
        self.boot()
        def fail():raise RuntimeError('private SID')
        self.owner.files=NS(finish=fail);self.owner.base=NS(finish=lambda:dict(PROOF))
        out=self.owner.close();self.assertIn('file_cleanup_unconfirmed',out['errors'])
        self.assertEqual(out['bootstrap_cleanup'],PROOF);self.assertTrue(out['sdk_shutdown_called'])
        self.assertNotIn('private',json.dumps(out))
    def test_unexpected_resource_close_is_fixed_outcome(self):
        def fail():raise RuntimeError('private SID')
        out=close_owned069(NS(close=fail));self.assertEqual(out['errors'],['resource_cleanup_unconfirmed'])
        self.assertNotIn('private',json.dumps(out))
    def test_reservation_raw_hash_has_no_assumed_sidecar_and_cannot_restart(self):
        raw=(self.root/'reservation').read_bytes();value=json.loads(raw)
        self.assertEqual(value['phase'],PHASE);self.assertEqual(value['bindings'],self.bindings)
        self.assertEqual(len(hashlib.sha256(raw).hexdigest()),64);self.assertFalse((self.root/'reservation.sha256').exists())
        with self.assertRaises(ProbeRejected):Reservation069(self.root/'reservation',self.bindings,Meter069(Clock()))
    def test_profile_binding_required_and_arm_order_latches(self):
        with self.assertRaises(ProbeRejected):Reservation069(self.root/'x',{k:v for k,v in self.bindings.items() if k!='helper_profile'},self.m)
        with self.assertRaises(ProbeRejected):self.s.arm('enabled')
        with self.assertRaises(ProbeRejected):self.s.arm('disabled')
    def test_authorization_binds_profile_and_rejects_boolean_zero(self):
        a=dict(version='sharing_native_070_v1',preparation_sha256='a'*64,policy_sha256='b'*64,helper_profile_sha256='c'*64,
            phase=PHASE,date=DATE,maximum_sdk_connections=1,maximum_launches=2,maximum_log_reads=1,maximum_log_bytes=65536,
            maximum_market_reads=0,maximum_orders=0,maximum_receipt_permissions=0)
        entry.authorization(a,'a'*64,'b'*64,'c'*64)
        for changes in ({'maximum_orders':False},{'helper_profile_sha256':'d'*64},{'date':'2026-10-08'},{'extra':0}):
            with self.assertRaises(ProbeRejected):entry.authorization({**a,**changes},'a'*64,'b'*64,'c'*64)
    def test_deployment_is_new_owned_folder_counted_and_no_overwrite(self):
        src=self.root/'build.ex5';src.write_bytes(b'compiled');scripts=self.root/'Scripts';scripts.mkdir()
        sha=hashlib.sha256(src.read_bytes()).hexdigest();reader=NS(hash_file=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest())
        name='ForexDemoLab069-'+'a'*32;out=deploy_owned069(src,scripts,name,sha,reader,lambda:True,self.m)
        self.assertEqual(out.read_bytes(),b'compiled');self.assertGreater(self.m.counts['startup_path_stats'],0)
        with self.assertRaises(Exception):deploy_owned069(src,scripts,name,sha,reader,lambda:True,Meter069(Clock()))
        self.assertEqual(out.read_bytes(),b'compiled')
    def test_path_stat_budget_rejects_without_deployment(self):
        self.m.counts['startup_path_stats']=64
        with self.assertRaises(ProbeRejected):no_reparse069(self.root,self.m)
        self.assertEqual(self.m.counts['deployment_writes'],0)
    def test_symlink_parent_rejected_before_copy(self):
        target=self.root/'dir';target.mkdir();link=self.root/'link';link.symlink_to(target,target_is_directory=True)
        with self.assertRaises(ProbeRejected):no_reparse069(link,self.m)
    def test_early_preflight_failure_writes_fixed_outcome_without_native_work(self):
        auth=dict(version='sharing_native_070_v1',preparation_sha256='a'*64,policy_sha256='a'*64,helper_profile_sha256='a'*64,
            phase=PHASE,date=DATE,maximum_sdk_connections=1,maximum_launches=2,maximum_log_reads=1,maximum_log_bytes=65536,
            maximum_market_reads=0,maximum_orders=0,maximum_receipt_permissions=0)
        writes=[]
        def fail():raise RuntimeError('secret SID account')
        api=dict(sha=lambda p:'a'*64,sealed=lambda p:auth,write=lambda p,v:writes.append((p.name,v)),bound=lambda p:p,verify=fail)
        with patch.object(entry,'os',NS(name='nt')),patch.object(entry,'sys',NS(stdin=NS(isatty=lambda:True))),patch.object(entry.runpy,'run_path',return_value=api):
            entry.run()
        self.assertEqual([n for n,v in writes],['native-sharing-069-dispatch-started.json','native-sharing-069-runtime.json'])
        out=writes[-1][1];self.assertFalse(out['completed']);self.assertEqual(out['stopped_stage'],'preflight')
        self.assertIsNone(out['counts']);self.assertIsNone(out['reservation_sha256']);self.assertFalse(out['sdk_shutdown_called'])
        self.assertNotIn('secret',json.dumps(out));self.assertEqual(out['quote_reads'],0)
    def test_noninteractive_entry_refuses_before_any_dispatch(self):
        with patch.object(entry,'os',NS(name='nt')),patch.object(entry,'sys',NS(stdin=NS(isatty=lambda:False))),patch.object(entry.runpy,'run_path') as run:
            with self.assertRaises(ProbeRejected):entry.run()
            run.assert_not_called()
