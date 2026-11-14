import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch

from forex_demo_lab.sharing_build_073 import *
from forex_demo_lab.sharing_integration_072 import validate_build072
from test_transport_lifecycle_060 import Clock

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('build_entry073',ROOT/'scripts/runtime-sharing-build-073.py')
entry=importlib.util.module_from_spec(spec);spec.loader.exec_module(entry)

class Build073Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        self.clock=Clock();self.clock.utc+=86400000;self.b=Budget073(lambda:self.clock()[:2])
        self.inputs={};self.expected={}
        for i,n in enumerate(SOURCE_INPUTS):
            p=self.root/Path(n).name;p.write_bytes(('source-'+str(i)).encode());self.inputs[n]=p
            self.expected[n]=hashlib.sha256(p.read_bytes()).hexdigest()
        self.contract=source_contract072(self.expected);self.directory=self.root/('compiler073-'+'a'*32)
        self.artifact=dict(sha256='b'*64,size=16310,raw=None);self.log="Result: 0 errors, 0 warnings, 1006 ms elapsed, cpu='X64 Regular'\n"
    def record(self,**changes):
        args=dict(contract=self.contract,exit_code=1,log_text=self.log,artifact=self.artifact,
            compiler_sha256='c'*64,terminal_sha256='d'*64)
        return build_record073(**{**args,**changes})
    def test_actual_exit_one_retained_with_clean_log_and_artifact(self):
        r=self.record();self.assertTrue(r['compiled']);self.assertEqual(r['compiler_exit_code'],1)
        self.assertFalse(r['runtime_authorized']);self.assertEqual(r['phase'],PHASE)
    def test_exit_zero_boolean_and_unknown_codes_rejected(self):
        for code in (0,True,None,2,-1):
            with self.assertRaises(BuildRejected):self.record(exit_code=code)
    def test_old_frozen_build_validator_does_not_silently_normalize_exit(self):
        old=dict(version='sharing_build_072_v1',phase=PHASE,date=DATE,input_bindings=self.expected,
            artifact_name=ARTIFACT,artifact_sha256='b'*64,compiler_sha256='c'*64,terminal_sha256='d'*64,
            terminal_build=6244,compiler_invocations=1,exit_code=1,errors=0,warnings=0)
        with self.assertRaises(ValueError):validate_build072(old,self.contract,'c'*64,'d'*64)
    def test_warning_error_missing_and_duplicate_log_summaries_rejected(self):
        for log in ('',self.log.replace('0 errors','1 errors'),self.log.replace('0 warnings','1 warnings'),self.log+self.log):
            with self.assertRaises(BuildRejected):self.record(log_text=log)
    def test_missing_empty_oversized_or_boolean_artifact_rejected(self):
        for artifact in (None,{**self.artifact,'size':0},{**self.artifact,'size':1048577},{**self.artifact,'size':True},
                         {**self.artifact,'sha256':'bad'}):
            with self.assertRaises(BuildRejected):self.record(artifact=artifact)
    def test_changed_contract_or_digest_rejected(self):
        for contract in ({**self.contract,'phase':'64'*16},{**self.contract,'compiled':0},{**self.contract,'input_bindings':{}},
                         {**self.contract,'extra':1}):
            with self.assertRaises(BuildRejected):self.record(contract=contract)
        with self.assertRaises(BuildRejected):self.record(compiler_sha256='private path')
    def test_stage_copies_only_four_declared_source_inputs(self):
        p=stage073(self.inputs,self.expected,self.directory,self.root,self.b)
        self.assertEqual({x.name for x in p.iterdir()},{Path(n).name for n in SOURCE_INPUTS})
        for n,h in self.expected.items():self.assertEqual(read_bound073(p/Path(n).name,self.b)['sha256'],h)
        self.assertEqual(self.b.counts['copies'],4)
    def test_existing_directory_is_not_overwritten(self):
        self.directory.mkdir();p=self.directory/'unrelated';p.write_bytes(b'keep')
        with self.assertRaises(FileExistsError):stage073(self.inputs,self.expected,self.directory,self.root,self.b)
        self.assertEqual(p.read_bytes(),b'keep')
    def test_wrong_owned_name_or_parent_rejected(self):
        for p in (self.root/'compiler065-used',self.root/'child'/self.directory.name):
            with self.assertRaises(BuildRejected):owned073(p,self.root)
    def test_changed_input_stops_before_copy(self):
        n=sorted(self.inputs)[0];self.inputs[n].write_bytes(b'changed')
        with self.assertRaisesRegex(BuildRejected,'^binding_rejected$'):stage073(self.inputs,self.expected,self.directory,self.root,self.b)
        self.assertEqual(self.b.counts['copies'],0)
    def test_missing_or_extra_include_rejected_before_directory_create(self):
        for inputs in ({n:p for n,p in self.inputs.items() if not n.endswith('SharingHold072.mqh')},{**self.inputs,'extra':self.root}):
            with self.assertRaises(BuildRejected):stage073(inputs,self.expected,self.directory,self.root,self.b)
        self.assertFalse(self.directory.exists())
    def test_symlink_input_and_parent_rejected(self):
        p=self.root/'link';p.symlink_to(next(iter(self.inputs.values())))
        with self.assertRaises(BuildRejected):read_bound073(p,self.b)
        target=self.root/'actual';target.mkdir();(target/'file').write_bytes(b'data');link=self.root/'dirlink';link.symlink_to(target,target_is_directory=True)
        with self.assertRaises(BuildRejected):read_bound073(link/'file',self.b)
    def test_hardlink_and_directory_rejected(self):
        p=next(iter(self.inputs.values()));link=self.root/'hard';link.hardlink_to(p)
        with self.assertRaises(BuildRejected):read_bound073(p,self.b)
        with self.assertRaises(BuildRejected):read_bound073(self.root,self.b)
    def test_file_cap_rejects_without_read_bytes(self):
        p=self.root/'large';p.write_bytes(b'x'*101)
        with self.assertRaises(BuildRejected):read_bound073(p,self.b,100)
        self.assertEqual(self.b.counts['hash_bytes'],0)
    def test_aggregate_byte_cap_is_reserved_before_read(self):
        self.b.counts['hash_bytes']=LIMITS['hash_bytes']
        with self.assertRaises(BuildRejected):read_bound073(next(iter(self.inputs.values())),self.b)
        self.assertEqual(self.b.counts['hash_bytes'],LIMITS['hash_bytes'])
    def test_path_stat_and_hash_count_caps_reject(self):
        p=next(iter(self.inputs.values()));self.b.counts['hash_reads']=LIMITS['hash_reads']
        with self.assertRaises(BuildRejected):read_bound073(p,self.b)
        self.b.counts['hash_reads']=0;self.b.counts['path_stats']=LIMITS['path_stats']
        with self.assertRaises(BuildRejected):read_bound073(p,self.b)
    def test_read_bound_returns_exact_digest_and_descriptor_bytes(self):
        p=next(iter(self.inputs.values()));r=read_bound073(p,self.b,collect=True)
        self.assertEqual(r['raw'],p.read_bytes());self.assertEqual(r['sha256'],hashlib.sha256(r['raw']).hexdigest())
    def test_path_replacement_during_open_rejected(self):
        p=next(iter(self.inputs.values()));original=Path.open;other=self.root/'other';other.write_bytes(b'other-xx')
        def opened(this,*args,**kwargs):
            if this==p and args==('rb',):return original(other,*args,**kwargs)
            return original(this,*args,**kwargs)
        with patch.object(Path,'open',opened):
            with self.assertRaises(BuildRejected):read_bound073(p,self.b)
    def test_copy_budget_does_not_refund_prior_copies(self):
        self.b.counts['copies']=4
        with self.assertRaises(BuildRejected):stage073(self.inputs,self.expected,self.directory,self.root,self.b)
        self.assertEqual(self.b.counts['copies'],4)
    def test_single_compiler_call_uses_exact_source_and_timeout(self):
        calls=[]
        def launch(*args):calls.append(args);return NS(returncode=1)
        code=compile_once073(launch,r'C:\MetaTrader\metaeditor64.exe',r'C:\builds\compiler073-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',self.b)
        self.assertEqual(code,1);self.assertEqual(len(calls),1);self.assertEqual(calls[0][2],60)
        self.assertIn('ForexDemoSharing072.mq5',calls[0][0]);self.assertNotIn('ForexDemoSharing064',calls[0][0])
        with self.assertRaises(BuildRejected):compile_once073(launch,r'C:\MetaTrader\metaeditor64.exe',r'C:\builds',self.b)
        self.assertEqual(len(calls),1)
    def test_timeout_consumes_compiler_allowance_without_retry(self):
        calls=[]
        def launch(*args):calls.append(args);raise subprocess.TimeoutExpired('private',60)
        with self.assertRaises(subprocess.TimeoutExpired):compile_once073(launch,r'C:\editor.exe',r'C:\builds',self.b)
        with self.assertRaises(BuildRejected):compile_once073(launch,r'C:\editor.exe',r'C:\builds',self.b)
        self.assertEqual(len(calls),1)
    def test_launch_exception_cannot_refund_budget(self):
        def launch(*args):raise OSError('private')
        with self.assertRaises(OSError):compile_once073(launch,r'C:\editor.exe',r'C:\builds',self.b)
        self.assertEqual(self.b.counts['compiler_invocations'],1)
    def test_metadata_requires_signed_exact_build_no_editor_and_policy(self):
        value=dict(policy='RemoteSigned',editor_processes=0,terminal_build=6244,editor_build=6244,valid_signatures=True)
        self.assertEqual(metadata073(value,'RemoteSigned'),value)
        for changes in ({'policy':'Bypass'},{'editor_processes':1},{'terminal_build':6245},{'editor_build':6245},{'valid_signatures':False},
                        {'editor_processes':False},{'extra':'private'}):
            with self.assertRaises(BuildRejected):metadata073({**value,**changes},'RemoteSigned')
    def test_clock_date_expiry_and_900s_limit(self):
        old=Clock()
        with self.assertRaises(BuildRejected):Budget073(lambda:old()[:2])
        self.clock.advance(900000)
        with self.assertRaises(BuildRejected):self.b.check()
    def test_clock_skew_reversal_and_boolean_shape(self):
        self.clock.advance(1);self.b.check();self.clock.mono-=1
        with self.assertRaises(BuildRejected):self.b.check()
        clock=Clock();clock.utc+=86400000;b=Budget073(lambda:clock()[:2]);clock.utc+=1001
        with self.assertRaises(BuildRejected):b.check()
        with self.assertRaises(BuildRejected):Budget073(lambda:(clock.utc,True))
    def test_clock_sample_and_unknown_budget_rejected(self):
        for key,amount in (('copies',True),('unknown',1),('copies',0)):
            with self.assertRaises(BuildRejected):self.b.consume(key,amount)
        self.b.counts['clock_samples']=10000
        with self.assertRaises(BuildRejected):self.b.check()
    def test_source_record_preserves_full_include_bindings_and_no_market_claim(self):
        r=self.record();self.assertEqual(r['input_bindings'],self.expected)
        self.assertEqual(r['build_phase'],BUILD_PHASE);self.assertFalse(r['orders_available'])
    def test_compile_record_failure_never_exports_private_details(self):
        with self.assertRaises(BuildRejected) as e:self.record(log_text='private account password')
        self.assertEqual(str(e.exception),'evidence_rejected');self.assertNotIn('private',str(e.exception))
    def test_build_reservation_fsyncs_exact_bytes_and_cannot_restart(self):
        p=self.root/'started.json';value=dict(build_reservation_consumed=True,ledger_sha256='a'*64,authorization_sha256='b'*64,
            maximum_compiler_invocations=1,phase=BUILD_PHASE,orders_available=False)
        with patch('forex_demo_lab.sharing_build_073.os.fsync') as sync:
            h=reserve_build073(p,value);self.assertEqual(sync.call_count,2)
        self.assertEqual(h,hashlib.sha256(p.read_bytes()).hexdigest());self.assertEqual(p.with_suffix('.sha256').read_text(),h+'\n')
        raw=p.read_bytes()
        with self.assertRaises(FileExistsError):reserve_build073(p,value)
        self.assertEqual(p.read_bytes(),raw)
    def test_build_reservation_rejects_boolean_budget_before_creation(self):
        p=self.root/'started.json';value=dict(build_reservation_consumed=True,ledger_sha256='a'*64,authorization_sha256='b'*64,
            maximum_compiler_invocations=True,phase=BUILD_PHASE,orders_available=False)
        with self.assertRaises(BuildRejected):reserve_build073(p,value)
        self.assertFalse(p.exists())


class BuildEntry073Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        (self.root/'reports').mkdir();self.build_root=self.root/'builds';self.build_root.mkdir()
        self.clock=Clock();self.clock.utc+=86400000;self.inputs={}
        for n in SOURCE_INPUTS:
            p=self.root/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(n.encode());self.inputs[n]=hashlib.sha256(p.read_bytes()).hexdigest()
        self.sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
        self.ledger=dict(source_contract=source_contract072(self.inputs),build_root=str(self.build_root),execution_policy='RemoteSigned')
        for key in ('terminal','editor','shell','python'):
            p=self.root/(key+'.exe');p.write_bytes(key.encode());self.ledger[key+'_path']=str(p);self.ledger[key+'_sha256']=self.sha(p)
        self.ledger_path=self.root/'reports/ledger';self.ledger_path.write_bytes(b'ledger')
        self.auth_path=self.root/'reports/auth';self.auth_path.write_bytes(b'auth')
        self.calls=[];self.behavior='success';self.outputs=[]
        auth=dict(allowed=True)
        self.api=dict(verify=lambda:self.ledger,sha=self.sha,bound=Path,
            sealed=lambda p:auth if p==self.auth_path else dict(checker_passed=True,ledger_sha256=self.sha(self.ledger_path)),
            write=self.write,AUTH=self.auth_path,CHECKS=self.root/'reports/checks',LEDGER=self.ledger_path,
            authorization_value=lambda l:auth,external_name=lambda p:str(p))
    def write(self,p,value):
        with Path(p).open('x') as f:json.dump(value,f)
        self.outputs.append(value)
    def metadata(self,shell,budget,policy,cleanup=False):
        if cleanup:budget.counts['metadata_calls']+=1
        else:budget.consume('metadata_calls')
        self.calls.append('metadata-cleanup' if cleanup else 'metadata')
        return dict(policy=policy,editor_processes=0,terminal_build=6244,editor_build=6244,valid_signatures=True)
    def compile(self,launch,editor,directory,budget):
        budget.consume('compiler_invocations');self.calls.append('compiler')
        if self.behavior=='timeout':raise subprocess.TimeoutExpired('private account',60)
        if self.behavior=='failure':raise OSError('private password')
        (directory/'compile.log').write_text('Result: 0 errors, 0 warnings, 123 ms elapsed\n',encoding='utf-16')
        (directory/ARTIFACT).write_bytes(b'compiled artifact')
        if self.behavior=='warning':(directory/'compile.log').write_text('Result: 0 errors, 1 warnings, 123 ms elapsed\n',encoding='utf-16')
        if self.behavior=='extra':(directory/'unexpected').write_bytes(b'no')
        if self.behavior=='expired':self.clock.advance(900000)
        return 1
    def run_entry(self):
        with patch.object(entry,'ROOT',self.root),patch.object(entry,'os',NS(name='nt')),patch.object(entry,'sys',NS(executable=self.ledger['python_path'])),\
             patch.object(entry.runpy,'run_path',return_value=self.api),patch.object(entry,'Budget073',lambda clock:Budget073(lambda:self.clock()[:2])),\
             patch.object(entry,'datetime',NS(now=lambda tz:datetime.fromtimestamp(self.clock.utc//1000,timezone.utc))),\
             patch.object(entry,'metadata',self.metadata),patch.object(entry,'compile_once073',self.compile):
            entry.run()
        return self.outputs[-1]
    def test_complete_entry_retains_exit_hashes_and_zero_runtime_calls(self):
        r=self.run_entry();self.assertTrue(r['completed']);self.assertEqual(r['compiler_exit_code'],1)
        self.assertEqual(r['counts']['compiler_invocations'],1);self.assertEqual(r['counts']['metadata_calls'],3)
        self.assertEqual(len(r['output_bindings']),6);self.assertTrue(all(e['completed'] for e in r['stage_trace']))
        self.assertEqual(r['mt5_runtime_invocations'],0);self.assertEqual(r['sdk_connections'],0);self.assertFalse(r['orders_available'])
    def test_timeout_spends_attempt_and_preserves_owned_cleanup_query(self):
        self.behavior='timeout';r=self.run_entry();self.assertFalse(r['completed'])
        self.assertEqual(r['stop_reason'],'compiler_timeout');self.assertTrue(r['timeout_owned_process_waited'])
        self.assertEqual(self.calls.count('compiler'),1);self.assertEqual(self.calls[-1],'metadata-cleanup')
    def test_launch_failure_is_redacted_and_cleanup_runs(self):
        self.behavior='failure';r=self.run_entry();self.assertEqual(r['stop_reason'],'unexpected_failure')
        self.assertNotIn('private',json.dumps(r));self.assertEqual(self.calls[-1],'metadata-cleanup')
    def test_warning_output_fails_without_salvage(self):
        self.behavior='warning';r=self.run_entry();self.assertFalse(r['compiled']);self.assertEqual(r['stop_reason'],'evidence_rejected')
    def test_unexpected_output_rejected_with_bounded_inventory(self):
        self.behavior='extra';r=self.run_entry();self.assertFalse(r['compiled']);self.assertEqual(r['stop_reason'],'evidence_rejected')
        self.assertEqual(r['stopped_stage'],'outputs');self.assertEqual(r['output_bindings'],{})
    def test_expiry_still_queries_owned_process_and_never_passes(self):
        self.behavior='expired';r=self.run_entry();self.assertFalse(r['compiled'])
        self.assertEqual(r['stop_reason'],'date_or_clock_rejected');self.assertEqual(self.calls[-1],'metadata-cleanup')
        self.assertTrue(r['owned_compiler_absent_after']);self.assertEqual(r['counts']['compiler_invocations'],1)
    def test_repeat_entry_cannot_compile_twice(self):
        self.run_entry()
        with self.assertRaises(AssertionError):self.run_entry()
        self.assertEqual(self.calls.count('compiler'),1)
    def test_changed_native_image_rejected_before_staging_or_launch(self):
        Path(self.ledger['editor_path']).write_bytes(b'changed')
        r=self.run_entry();self.assertEqual(r['stop_reason'],'binding_rejected');self.assertEqual(r['stopped_stage'],'preflight')
        self.assertEqual(r['counts']['compiler_invocations'],0);self.assertFalse(list(self.build_root.iterdir()))
