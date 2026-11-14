from dataclasses import replace
import hashlib
import importlib.util
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch

from forex_demo_lab.native_timing_078 import *
from test_timing_profile_077 import Clock077,Base077,Reader077,build077
from test_fresh_data_031 import API as AccountAPI

ROOT=Path(__file__).resolve().parents[1]
loader=importlib.util.spec_from_file_location('timing_entry078',ROOT/'scripts/runtime-native-timing-078.py')
entry=importlib.util.module_from_spec(loader);loader.loader.exec_module(entry)
SDK_PAIRS=(('sdkinit','6'*64),('sdkcore','7'*64),('shell','8'*64),('security','9'*64),('management','0'*64))


def fixture078(root,cost=0):
    clock=Clock077();build=build077();calls=[];state=NS(reader=None,base=None,trust=True)
    chain=HelperChain068(('launcher','1'*64),('config','2'*64),
        (('package/python3.13.exe','4'*64),),('library','3'*64),'private-alias')
    sdk=AccountAPI();sdk.__version__='5.0.6231'
    sdk.terminal.path=r'C:\Program Files\MetaTrader 5';sdk.terminal.data_path=str(root);sdk.terminal.build=6244
    sdk.initialize=lambda *a,**k:calls.append('initialize') or True
    sdk.shutdown=lambda:calls.append('shutdown')
    def forbidden(*a,**k): raise AssertionError('market/order forbidden')
    sdk.symbol_info_tick=sdk.copy_ticks_range=sdk.copy_rates_range=sdk.order_send=forbidden
    spec=Spec078(build,'e'*64,'f'*64,'5'*64,chain,(r'c:\program files\metatrader 5\terminal64.exe','d'*64),('editor','c'*64),('artifact','b'*64),
        tuple(zip(SOURCE_INPUTS,('source0','source1','source2','source3'))),SDK_PAIRS)
    def backend(meter):
        calls.append('backend');state.base=Base077(meter);return state.base
    def reader(base):
        r=Reader077(base.meter,clock,base,cost);r.values['terminal']='d'*64;r.values.update(SDK_PAIRS)
        state.reader=r;return r
    def trust(meter): meter.consume('trust_queries');calls.append('signature');return state.trust
    def importer(): calls.append('import');return sdk
    hooks=Hooks078(clock,backend,reader,trust,importer,lambda base:'library',9,'launcher','private-alias','3.13.14')
    auth=authorization078(spec.preparation,spec.policy,spec.profile,'a'*64,'b'*64,build.sha256,spec.component_sha256)
    raw=encoded076(auth);ash=hashlib.sha256(raw).hexdigest()
    dispatch=reserve_dispatch078(root/'dispatch',auth,ash)
    return NS(root=root,clock=clock,build=build,spec=spec,hooks=hooks,auth=auth,raw=raw,ash=ash,
        dispatch=dispatch,sdk=sdk,state=state,calls=calls)


def run078(f,**changes):
    args=dict(spec=f.spec,hooks=f.hooks,authorization_raw=f.raw,expected_authorization=f.auth,
        authorization_sha=f.ash,dispatch=f.dispatch,reservation_path=f.root/'reservation')
    return run_entry078(**{**args,**changes})


class Fixture078(unittest.TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
    def f(self,**kw): return fixture078(self.root,**kw)


class Authority078Tests(Fixture078):
    def test_exact_finite_metadata_authorization_and_no_sharing_permission(self):
        f=self.f();self.assertEqual(validate_authorization078(f.raw,f.auth,f.ash),f.auth)
        self.assertEqual(f.auth['phase'],PHASE);self.assertEqual(f.auth['limits'],LIMITS077)
        for k in ('maximum_script_launches','maximum_deployments','maximum_terminal_log_reads',
            'maximum_market_reads','maximum_orders','maximum_receipt_permissions'):self.assertEqual(f.auth[k],0)
        self.assertFalse(f.auth['sharing_launch_authorized']);self.assertFalse(f.auth['latency_guaranteed'])
    def test_bool_missing_extra_phase_date_and_larger_grants_rejected(self):
        f=self.f()
        changes=[{'maximum_sdk_connections':True},{'fixed_samples':5},{'maximum_orders':1},
            {'phase':'0'*32},{'date':'2026-10-09'},{'execution_authorized':False},{'extra':0}]
        rows=[{**f.auth,**c} for c in changes]+[{k:v for k,v in f.auth.items() if k!='entry_sha256'}]
        for r in rows:
            raw=encoded076(r)
            with self.assertRaises(ProbeRejected):validate_authorization078(raw,f.auth,hashlib.sha256(raw).hexdigest())
    def test_raw_digest_duplicate_keys_and_noncanonical_authority_rejected(self):
        f=self.f()
        for raw in (f.raw+b' ',f.raw.replace(b'"fixed_samples":4',b'"fixed_samples":4,"fixed_samples":4'),b'x'*8193):
            with self.assertRaises(ProbeRejected):validate_authorization078(raw,f.auth,hashlib.sha256(raw).hexdigest())
        with self.assertRaises(ProbeRejected):validate_authorization078(f.raw,f.auth,'0'*64)
    def test_native_dispatch_phase_and_component_binding_are_fresh_and_exact(self):
        f=self.f();r=json.loads((self.root/'dispatch').read_bytes())
        self.assertEqual(r['phase'],PHASE);self.assertEqual(r['component_contract_sha256'],f.spec.component_sha256)
        self.assertNotEqual(r['phase'],json.loads(f.spec.component_raw)['phase'])
        self.assertFalse((self.root/'dispatch.sha256').exists())
    def test_exclusive_dispatch_and_same_process_claim_are_once_only(self):
        f=self.f();expected=dispatch_value078(f.auth,f.ash);f.dispatch.claim(expected)
        with self.assertRaises(ProbeRejected):f.dispatch.claim(expected)
        with self.assertRaises(FileExistsError):reserve_dispatch078(self.root/'dispatch',f.auth,f.ash)
    def test_bad_authorization_prevents_backend_and_sdk_actions(self):
        f=self.f()
        with self.assertRaises(ProbeRejected):run078(f,authorization_sha='0'*64)
        self.assertFalse(f.calls);self.assertFalse((self.root/'reservation').exists())
    def test_build_policy_and_component_mismatch_prevents_native_actions(self):
        f=self.f();changed=replace(f.spec,policy='0'*64)
        with self.assertRaises(ProbeRejected):run078(f,spec=changed)
        self.assertFalse(f.calls)
    def test_spec_rejects_wrong_build_pins_and_source_or_sdk_sets(self):
        f=self.f()
        for change in ({'terminal':('terminal','0'*64)},{'source_paths':f.spec.source_paths[:-1]},
            {'sdk_bindings':SDK_PAIRS[:-1]},{'preparation':False},{'artifact':['artifact','b'*64]}):
            with self.assertRaises(ProbeRejected):replace(f.spec,**change)


class Entry078Tests(Fixture078):
    def test_metadata_entry_eight_guards_four_samples_and_once_owned_cleanup(self):
        f=self.f();r=run078(f);self.assertTrue(r['entry_completed'])
        self.assertEqual(r['counts']['guards'],8);self.assertEqual(r['counts']['sdk_queries'],89)
        self.assertEqual(r['observation']['samples_completed'],4);self.assertEqual(f.state.base.closed,1)
        self.assertEqual(f.calls,['backend','signature','import','initialize','shutdown'])
        self.assertEqual((r['counts']['sdk_connections'],r['counts']['sdk_shutdowns']),(1,1))
        self.assertFalse(r['native_launch_ready']);self.assertFalse(r['latency_guaranteed'])
    def test_sdk_inputs_rehashed_before_import_after_signature_and_each_sample(self):
        f=self.f();r=run078(f);self.assertTrue(r['entry_completed'])
        for path,h in SDK_PAIRS:self.assertEqual(f.state.reader.hashes.count(path),6)
        for name in ('source0','source1','source2','source3'):self.assertEqual(f.state.reader.hashes.count(name),5)
    def test_current_terminal_and_helper_sessions_must_match(self):
        f=self.f();old=f.hooks.reader
        def reader(base):
            r=old(base);r.helper=replace(r.helper,session=2);return r
        r=run078(f,hooks=replace(f.hooks,reader=reader));self.assertFalse(r['entry_completed'])
        self.assertNotIn('import',f.calls);self.assertEqual(f.state.base.closed,1)
    def test_bad_installed_sdk_file_stops_before_import(self):
        f=self.f();old=f.hooks.reader
        def reader(base):r=old(base);r.values['sdkcore']='0'*64;return r
        r=run078(f,hooks=replace(f.hooks,reader=reader))
        self.assertEqual(r['stopped_stage'],'preflight');self.assertNotIn('import',f.calls)
        self.assertFalse(r['cleanup']['sdk_shutdown_called']);self.assertEqual(f.state.base.closed,1)
    def test_sdk_input_changes_during_signature_rejected_before_import(self):
        f=self.f()
        def trust(m):m.consume('trust_queries');f.state.reader.values['sdkinit']='0'*64;return True
        r=run078(f,hooks=replace(f.hooks,trust=trust));self.assertEqual(r['stopped_stage'],'signature')
        self.assertNotIn('import',f.calls)
    def test_false_signature_never_imports_or_attaches(self):
        f=self.f();f.state.trust=False;r=run078(f)
        self.assertFalse(r['entry_completed']);self.assertNotIn('import',f.calls);self.assertEqual(f.state.base.closed,1)
    def test_wrong_helper_version_never_imports_sdk(self):
        f=self.f();r=run078(f,hooks=replace(f.hooks,python_version='3.13.15'))
        self.assertEqual(r['stopped_stage'],'helper_chain');self.assertNotIn('import',f.calls)
    def test_wrong_sdk_version_never_initializes(self):
        f=self.f();f.sdk.__version__='changed';r=run078(f)
        self.assertEqual(r['stopped_stage'],'sdk_attach');self.assertNotIn('initialize',f.calls)
        self.assertNotIn('shutdown',f.calls)
    def test_failed_initialize_attempt_still_shuts_down_once(self):
        f=self.f();f.sdk.initialize=lambda *a,**k:f.calls.append('initialize') or False
        r=run078(f);self.assertFalse(r['entry_completed'])
        self.assertTrue(r['cleanup']['sdk_shutdown_called']);self.assertEqual(f.calls[-2:],['initialize','shutdown'])
    def test_interrupt_during_initialize_is_owned_and_spent(self):
        f=self.f()
        def initialize(*a,**k):f.calls.append('initialize');raise KeyboardInterrupt('private')
        f.sdk.initialize=initialize;r=run078(f)
        self.assertTrue(r['cleanup']['sdk_shutdown_called']);self.assertEqual(r['stopped_stage'],'sdk_attach')
        self.assertNotIn('private',json.dumps(r))
    def test_real_and_contest_modes_rejected_before_sample(self):
        for mode in (1,2):
            with TemporaryDirectory() as d:
                f=fixture078(Path(d));f.sdk.account.trade_mode=mode;f.sdk.account.server='Demo'
                r=run078(f);self.assertFalse(r['entry_completed']);self.assertEqual(r['observation']['samples_completed'],0)
                self.assertEqual(f.calls.count('shutdown'),1)
    def test_algo_on_disconnected_and_currency_change_reject(self):
        for obj,key,value in (('terminal','trade_allowed',True),('terminal','connected',False),('account','currency','EUR')):
            with TemporaryDirectory() as d:
                f=fixture078(Path(d));setattr(getattr(f.sdk,obj),key,value);self.assertFalse(run078(f)['entry_completed'])
    def test_sdk_input_replacement_mid_profile_stops_with_owned_cleanup(self):
        f=self.f();old=f.hooks.loaded_library;calls=[0]
        def library(base):
            calls[0]+=1
            if calls[0]==2:f.state.reader.values['sdkcore']='0'*64
            return old(base)
        r=run078(f,hooks=replace(f.hooks,loaded_library=library))
        self.assertFalse(r['entry_completed']);self.assertEqual(r['stopped_stage'],'profile_samples')
        self.assertEqual(f.calls.count('shutdown'),1)
    def test_wrong_backend_meter_stops_and_closes_owned_backend(self):
        f=self.f();old=f.hooks.reader
        def reader(base):r=old(base);r.meter=Meter077(Clock077());return r
        r=run078(f,hooks=replace(f.hooks,reader=reader));self.assertEqual(r['stopped_stage'],'preflight')
        self.assertEqual(f.state.base.closed,1);self.assertNotIn('import',f.calls)
    def test_metadata_build_rejects_without_fixture_creation(self):
        f=self.f();f.sdk.terminal.build=6245;r=run078(f)
        self.assertEqual(r['stopped_stage'],'account_metadata');self.assertEqual(r['counts']['directories'],0)
    def test_clock_expiry_during_setup_still_releases_owned_backend(self):
        f=self.f(cost=600000);r=run078(f)
        self.assertFalse(r['entry_completed']);self.assertEqual(f.state.base.closed,1);self.assertNotIn('import',f.calls)
    def test_shutdown_failure_invalidates_complete_samples_without_retry(self):
        f=self.f()
        def shutdown():f.calls.append('shutdown');raise RuntimeError('private')
        f.sdk.shutdown=shutdown;r=run078(f)
        self.assertFalse(r['entry_completed']);self.assertEqual(r['observation']['samples_completed'],4)
        self.assertEqual(f.calls.count('shutdown'),1);self.assertNotIn('private',json.dumps(r))
    def test_restart_and_duplicate_entry_never_connect_again(self):
        f=self.f();self.assertTrue(run078(f)['entry_completed'])
        with self.assertRaises(ProbeRejected):run078(f)
        self.assertEqual(f.calls.count('initialize'),1);self.assertEqual(f.calls.count('shutdown'),1)
    def test_partial_component_marker_failure_does_not_reset_dispatch(self):
        f=self.f();(self.root/'reservation').write_bytes(b'partial')
        r=run078(f);self.assertFalse(r['entry_completed']);self.assertFalse(f.calls)
        with self.assertRaises(ProbeRejected):run078(f)
        self.assertEqual((self.root/'reservation').read_bytes(),b'partial')
    def test_reports_do_not_export_account_ids_private_paths_pids_or_logons(self):
        f=self.f();text=json.dumps(run078(f))
        for secret in (str(f.sdk.account.login),f.sdk.account.server,str(self.root),'private-logon','package/python3.13.exe'):
            self.assertNotIn(secret,text)


class Boundary078Tests(Fixture078):
    def public(self):
        c=Clock077();return c,entry.PublicInputs078(lambda:(c.utc,c.mono))
    def record(self,raw=b'{"ok":true}\n'):
        path=self.root/'record.json';path.write_bytes(raw)
        path.with_suffix('.sha256').write_text(hashlib.sha256(raw).hexdigest()+'\n')
        return path
    def test_public_record_requires_bounded_matching_sidecar(self):
        c,p=self.public();path=self.record();r,h=p.record(path)
        self.assertEqual(r,dict(ok=True));self.assertEqual(p.reads,2)
        path.with_suffix('.sha256').write_text('0'*64+'\n')
        with self.assertRaises(ProbeRejected):p.record(path)
    def test_duplicate_json_keys_and_oversized_public_record_rejected(self):
        c,p=self.public();path=self.record(b'{"ok":true,"ok":true}\n')
        with self.assertRaises(ProbeRejected):p.record(path)
        path.write_bytes(b'x'*524289)
        with self.assertRaises(ProbeRejected):entry.PublicInputs078(lambda:(c.utc,c.mono)).raw(path)
    def test_reparse_and_hardlinked_public_files_rejected(self):
        c,p=self.public();path=self.record();link=self.root/'link';link.symlink_to(path)
        with self.assertRaises(ProbeRejected):p.raw(link)
        hard=self.root/'hard';entry.os.link(path,hard)
        with self.assertRaises(ProbeRejected):p.raw(path)
    def test_public_read_byte_and_stat_budgets_are_finite(self):
        c,p=self.public();path=self.record()
        p.reads=16
        with self.assertRaises(ProbeRejected):p.raw(path)
        c,p=self.public();p.bytes=2097152
        with self.assertRaises(ProbeRejected):p.raw(path)
        c,p=self.public();p.stats=128
        with self.assertRaises(ProbeRejected):p.raw(path)
    def test_source_and_launcher_reads_have_separate_finite_budget(self):
        c,p=self.public();path=self.record();p.source_reads=64
        with self.assertRaises(ProbeRejected):p.raw(path,source=True)
        c,p=self.public();p.source_bytes=16777216
        with self.assertRaises(ProbeRejected):p.raw(path,source=True)
    def test_public_clock_expiry_reversal_skew_and_date_fail(self):
        for mode in ('expiry','reversal','skew','date'):
            c,p=self.public()
            if mode=='expiry':c.advance(30000)
            elif mode=='reversal':c.mono-=1
            elif mode=='skew':c.utc+=1001
            else:c.utc-=86400000
            with self.assertRaises(ProbeRejected):p.check()
    def test_windows_entry_requires_windows_before_any_authority_file(self):
        with patch.object(entry.os,'name','posix'):
            with self.assertRaisesRegex(ProbeRejected,'^timing_windows_required$'):entry.run()
    def test_dependency_closure_includes_every_local_guard_and_excludes_data_logs(self):
        paths=entry.dependency_files078(ROOT)
        for n in ('native_timing_078','timing_profile_077','sharing_adapter_076','image_guard_068','private_guard_065'):
            self.assertIn(f'src/forex_demo_lab/{n}.py',paths)
        self.assertLess(len(paths),64);self.assertTrue(all(n.endswith('.py') for n in paths))
    def test_signature_metadata_exact_schema_and_no_execution_policy_change(self):
        c=Clock077();m=Meter077(c);calls=[]
        result=NS(returncode=0,stdout=json.dumps(dict(valid=True,count=5,policy='Restricted',terminal_build=6244,editor_build=6244)),stderr='')
        def invoke(args,**kwargs):calls.append((args,kwargs));return result
        self.assertTrue(entry.signature078(Path('/shell'),m,invoke))
        self.assertEqual(calls[0][1]['timeout'],15);self.assertNotIn('-ExecutionPolicy',calls[0][0])
        self.assertEqual(m.counts['trust_queries'],1)
    def test_bad_signature_bool_build_policy_stdout_stderr_rejected(self):
        good=dict(valid=True,count=5,policy='Restricted',terminal_build=6244,editor_build=6244)
        for change in ({'valid':1},{'count':True},{'terminal_build':6245},{'policy':'RemoteSigned'}):
            m=Meter077(Clock077());result=NS(returncode=0,stdout=json.dumps({**good,**change}),stderr='')
            with self.assertRaises(ProbeRejected):entry.signature078(Path('/shell'),m,lambda *a,**k:result)
    def test_native_result_output_is_exclusive_and_fsynchronized(self):
        path=self.root/'out.json';entry.write_result078(path,dict(completed=False))
        self.assertEqual(path.with_suffix('.sha256').read_text().strip(),hashlib.sha256(path.read_bytes()).hexdigest())
        with self.assertRaises(FileExistsError):entry.write_result078(path,dict(completed=True))


if __name__=='__main__':unittest.main()
