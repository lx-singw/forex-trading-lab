from dataclasses import replace
from datetime import datetime,timezone
import hashlib
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from forex_demo_lab.build_bindings_087 import *

ROOT=Path(__file__).resolve().parents[1]
LOG='Result: 0 errors, 0 warnings, model compile\n'
PINS=dict(compiler='a'*64,terminal='b'*64,policy='RemoteSigned')


class Clock:
    def __init__(self):self.ms=int(datetime(2026,10,8,12,tzinfo=timezone.utc).timestamp()*1000);self.ns=0;self.calls=0
    def __call__(self):self.calls+=1;return self.ms,self.ns
    def advance(self,ms):self.ms+=ms;self.ns+=ms*1000000


class CompilerModel:
    model_only=True
    def __init__(self,c,**cfg):self.c=c;self.cfg=cfg;self.compiles=0;self.metas=0;self.image_calls=0
    def images(self):
        self.image_calls+=1
        return dict(compiler='f'*64 if self.cfg.get('changed_image') else PINS['compiler'],terminal=PINS['terminal'])
    def metadata(self):
        self.metas+=1
        value=dict(policy=PINS['policy'],editor_processes=0,terminal_build=6244,editor_build=6244,valid_signatures=True)
        if self.cfg.get('editor_left') and self.metas==3:value['editor_processes']=1
        return value
    def compile(self,directory,source,timeout):
        self.compiles+=1;assert source==SOURCE and timeout==60
        if self.cfg.get('interrupt'):raise KeyboardInterrupt()
        if self.cfg.get('timeout'):self.c.advance(900000);raise TimeoutError()
        (directory/ARTIFACT).write_bytes(b'model-only-ex5')
        (directory/'compile.log').write_bytes(self.cfg.get('log',LOG).encode('utf-16'))
        if self.cfg.get('tamper_source'):(directory/Path(SOURCE).name).write_bytes(b'changed')
        if self.cfg.get('extra'):(directory/'undeclared.bin').write_bytes(b'extra')
        return self.cfg.get('exit_code',1)


def model_build087(**cfg):
    c=Clock();p=CompilerModel(c,**cfg);contract=build_contract087(ROOT)
    with TemporaryDirectory() as d:
        root=Path(d);stage=Stage087(ROOT,contract,PINS,p,c)
        r=stage.run(root/'spent.json',root/('compiler087-'+'1'*32),
            {n:ROOT/n for n in contract['source_contract']['input_bindings']},cfg.get('enabled',True))
        r['backend_compile_calls']=p.compiles;r['backend_metadata_calls']=p.metas
        r['attempt_persisted']=(root/'spent.json').exists()
    return r


class Build087Tests(unittest.TestCase):
    def test_six_headers_and_full37_source_contract(self):
        c=build_contract087(ROOT);self.assertEqual((len(c['compile_inputs']),len(c['source_contract']['input_bindings'])),(6,37))
        self.assertFalse(c['build_authority']);self.assertFalse(c['runtime_authorized'])
    def test_nested_schema_and_bool_integer_mutations_rejected(self):
        for change in ({'compiler_invocations':True},{'actual_compiler_exit':0},{'build_authority':True},{'extra':0}):
            with self.assertRaises(Exception):validate_contract087({**build_contract087(ROOT),**change})
        c=build_contract087(ROOT);c['source_contract']['freshness_ms']=3000
        with self.assertRaises(Exception):validate_contract087(c)
    def test_build_exact_exit_log_and_artifact_required(self):
        c=build_contract087(ROOT);a=dict(sha256='c'*64,size=12,raw=None)
        for code in (0,True,2,None):
            with self.assertRaises(Exception):build_record087(c,code,LOG,a,PINS['compiler'],PINS['terminal'])
        for log in ('',LOG+LOG,'Result: 0 errors, 1 warnings, x\n',LOG+'source: warning ignored\n'):
            with self.assertRaises(Exception):build_record087(c,1,log,a,PINS['compiler'],PINS['terminal'])
    def test_artifact_zero_oversize_bool_and_bad_digest_reject(self):
        c=build_contract087(ROOT)
        for a in (dict(sha256='c'*64,size=0,raw=None),dict(sha256='c'*64,size=1048577,raw=None),
            dict(sha256='c'*64,size=True,raw=None),dict(sha256='bad',size=12,raw=None)):
            with self.assertRaises(Exception):build_record087(c,1,LOG,a,PINS['compiler'],PINS['terminal'])
    def test_build_bytes_canonical_no_duplicates_extra_or_normalization(self):
        c=build_contract087(ROOT);a=dict(sha256='c'*64,size=12,raw=None)
        value=build_record087(c,1,LOG,a,PINS['compiler'],PINS['terminal']);raw=encoded076(value)
        self.assertEqual(verify_build087(raw,c,LOG,a,PINS['compiler'],PINS['terminal']).record(),value)
        for changed in (raw+b' ',raw[:-2]+b',"errors":0}\n',encoded076({**value,'runtime_authorized':True})):
            with self.assertRaises(Exception):verify_build087(changed,c,LOG,a,PINS['compiler'],PINS['terminal'])
    def test_complete_model_stage_stages_six_and_one_invocation(self):
        r=model_build087();self.assertTrue(r['modeled_completed'],r)
        self.assertEqual((r['counts']['copies'],r['compiler_invocations'],r['backend_compile_calls'],r['backend_metadata_calls']),(6,1,1,3))
        self.assertTrue(r['attempt_persisted']);self.assertEqual(r['native_compiler_invocations'],0)
    def test_default_off_no_marker_clock_or_backend_calls(self):
        r=model_build087(enabled=False);self.assertFalse(r['modeled_completed']);self.assertFalse(r['attempt_persisted'])
        self.assertEqual((r['backend_compile_calls'],r['backend_metadata_calls']),(0,0))
    def test_changed_image_stops_before_compile_and_final_metadata_attempted(self):
        r=model_build087(changed_image=True);self.assertFalse(r['modeled_completed']);self.assertEqual(r['backend_compile_calls'],0)
        self.assertEqual(r['backend_metadata_calls'],1)
    def test_wrong_exit_and_warning_not_native_success(self):
        for cfg in ({'exit_code':0},{'log':'Result: 0 errors, 1 warnings, x\n'}):
            r=model_build087(**cfg);self.assertFalse(r['modeled_completed']);self.assertEqual(r['backend_compile_calls'],1)
    def test_post_compile_source_change_and_extra_file_rejected(self):
        for cfg in ({'tamper_source':True},{'extra':True}):self.assertFalse(model_build087(**cfg)['modeled_completed'])
    def test_editor_remaining_invalidates_clean_output(self):
        r=model_build087(editor_left=True);self.assertFalse(r['modeled_completed']);self.assertTrue(r['metadata_after_attempted'])
    def test_timeout_interrupt_spent_and_after_metadata_attempted(self):
        for cfg in ({'timeout':True},{'interrupt':True}):
            r=model_build087(**cfg);self.assertFalse(r['modeled_completed']);self.assertTrue(r['attempt_persisted'])
            self.assertEqual(r['backend_metadata_calls'],3)
    def test_restart_marker_and_one_instance_reject_repeat(self):
        c=Clock();backend=CompilerModel(c);contract=build_contract087(ROOT)
        with TemporaryDirectory() as d:
            p=Path(d);marker=p/'spent.json';directory=p/('compiler087-'+'2'*32)
            paths={n:ROOT/n for n in contract['source_contract']['input_bindings']}
            s=Stage087(ROOT,contract,PINS,backend,c);self.assertTrue(s.run(marker,directory,paths,True)['modeled_completed'])
            with self.assertRaises(Exception):s.run(marker,directory,paths,True)
            with self.assertRaises(Exception):Stage087(ROOT,contract,PINS,backend,c).run(marker,p/('compiler087-'+'3'*32),paths,True)
            self.assertEqual(backend.compiles,1)
    def test_no_stage_overwrite(self):
        c=Clock();b=CompilerModel(c);contract=build_contract087(ROOT)
        with TemporaryDirectory() as d:
            p=Path(d);directory=p/('compiler087-'+'4'*32);directory.mkdir();(directory/'user.txt').write_text('retain')
            s=Stage087(ROOT,contract,PINS,b,c);r=s.run(p/'spent.json',directory,{n:ROOT/n for n in contract['source_contract']['input_bindings']},True)
            self.assertFalse(r['modeled_completed']);self.assertEqual((directory/'user.txt').read_text(),'retain');self.assertEqual(b.compiles,0)
    def test_native_backend_rejected_before_clock(self):
        b=CompilerModel(Clock());b.model_only=False
        with self.assertRaises(Exception):Stage087(ROOT,build_contract087(ROOT),PINS,b,lambda:1/0)
    def test_date_backwards_and_finite_copy_budget(self):
        c=Clock();b=Budget087(c);c.advance(86400000)
        with self.assertRaises(Exception):b.check()
        c=Clock();b=Budget087(c);b.consume('copies',6)
        with self.assertRaises(Exception):b.consume('copies')

if __name__=='__main__':unittest.main()
