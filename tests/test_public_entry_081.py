from contextlib import contextmanager,redirect_stdout
from datetime import datetime,timezone
import hashlib
import io
import json
from pathlib import Path,PureWindowsPath
from tempfile import TemporaryDirectory
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch
from forex_demo_lab import public_trace_081 as trace_module
from forex_demo_lab import public_preflight_080 as reader_module

from forex_demo_lab.public_preflight_080 import PublicInputs080,PublicInputRejected080
from forex_demo_lab.public_trace_081 import *
from forex_demo_lab.native_timing_081 import *
from forex_demo_lab.native_timing_078 import authorization078
from forex_demo_lab.sharing_build_075 import build_record075
from forex_demo_lab.sharing_integration_072 import source_contract072
from forex_demo_lab.public_model_080 import DATE_CLOCK080,WINDOWS_ROOT080,model_paths080
from test_native_timing_081 import entry,fixture081,run081


def sealed_fixture081(root,auth_crlf=True):
    root=Path(root);(root/'reports').mkdir()
    def put(name,raw):
        path=root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
        return hashlib.sha256(raw).hexdigest()
    def report(name,value,crlf=False):
        raw=(json.dumps(value,sort_keys=True)+'\n').encode('ascii');digest=put(name,raw)
        put(str(Path(name).with_suffix('.sha256')),digest.encode()+ (b'\r\n' if crlf else b'\n'))
        return digest
    source_bindings={n:put(n,('synthetic source'+str(i)).encode()) for i,n in enumerate(SOURCE_INPUTS)}
    build=VerifiedBuild076(encoded076(build_record075(source_contract072(source_bindings),1,
        'Result: 0 errors, 0 warnings, injected\n',dict(sha256='b'*64,size=100,raw=None),'c'*64,'d'*64)))
    sources=['scripts/runtime-native-timing-081.py','src/forex_demo_lab/synthetic.py']
    bindings={n:put(n,('synthetic binding'+str(i)).encode()) for i,n in enumerate(sources)}
    launcher=put('launcher',b'synthetic pinned launcher')
    bindings.update(launcher=launcher,config='2'*64,library='3'*64,
        **{'package/python3.13.exe':'4'*64},terminal='d'*64,editor='c'*64,artifact='b'*64)
    sdk=['sdk_init','sdk_core','shell','security','management']
    bindings.update(dict.fromkeys(sdk,'6'*64))
    profile=report('reports/helper-profile-068.json',dict(profile_verified=True,native_signature_checks_passed=True),True)
    policy='f'*64
    ledger=dict(helper_profile_sha256=profile,policy_sha256=policy,runtime_bindings=bindings,
        runtime_sources=sources,helper_chain=dict(launcher='launcher',config='config',
            library='library',images=['package/python3.13.exe'],base_alias='private-alias'),
        build_record=build.record(),terminal_name='terminal',editor_name='editor',
        artifact_name='artifact',sdk_bindings=sdk,shell_name='shell')
    lsha=report('reports/native-timing-081-ledger.json',ledger)
    final=report('reports/native-timing-081-final-source.json',dict(source_and_evidence_bindings={
        **{n:bindings[n] for n in sources},'docs/NATIVE-TIMING-081-POLICY.md':policy}))
    report('reports/native-timing-081-checks.json',dict(checker_passed=True,ledger_sha256=lsha))
    report('reports/native-timing-081-completion-review.json',dict(review_passed=True,
        final_source_sha256=final,frozen_input_coverage_complete=True))
    chain=HelperChain068((str(root/'launcher'),launcher),(str(root/'config'),'2'*64),
        ((str(root/'package/python3.13.exe'),'4'*64),),(str(root/'library'),'3'*64),'private-alias')
    spec=Spec081(build,final,policy,profile,chain,(str(root/'terminal'),'d'*64),
        (str(root/'editor'),'c'*64),(str(root/'artifact'),'b'*64),
        tuple((n,str(root/n)) for n in SOURCE_INPUTS),tuple((str(root/n),'6'*64) for n in sdk))
    auth=authorization081(final,policy,profile,lsha,bindings[sources[0]],build.sha256,spec.component_sha256)
    raw=encoded076(auth);put('reports/native-timing-081-authorization.json',raw)
    put('reports/native-timing-081-authorization.sha256',hashlib.sha256(raw).hexdigest().encode()+ (b'\r\n' if auth_crlf else b'\n'))
    return NS(root=root,ledger=ledger,auth=auth,report=report,put=put,sources=sources)


class Public081Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        self.reader=PublicInputs080(lambda:DATE_CLOCK080);self.trace=PublicTrace081(self.reader)
    def test_invocation_is_exclusive_raw_canonical_and_has_no_sidecar(self):
        p=self.root/'invocation.json';raw=reserve_invocation081(p)
        self.assertEqual(raw,invocation_bytes081());self.assertEqual(json.loads(raw),invocation_value081())
        self.assertFalse(p.with_suffix('.sha256').exists())
        with self.assertRaises(FileExistsError):reserve_invocation081(p)
        self.assertEqual(p.read_bytes(),raw)
    def test_partial_invocation_is_preserved_without_reset(self):
        p=self.root/'invocation.json';p.write_bytes(b'partial')
        with self.assertRaises(FileExistsError):reserve_invocation081(p)
        self.assertEqual(p.read_bytes(),b'partial')
    def test_authority_binds_fresh_invocation_and_exact_public_limits(self):
        f=fixture081(self.root)
        self.assertEqual(f.auth['maximum_native_entry_invocations'],1)
        self.assertEqual(f.auth['invocation_contract_sha256'],hashlib.sha256(invocation_bytes081()).hexdigest())
        self.assertEqual(f.auth['public_limits'],PUBLIC_LIMITS081)
        self.assertEqual(f.auth['public_limits']['sidecar_bytes'],66)
    def test_old078_authority_cannot_authorize081(self):
        f=fixture081(self.root);a=f.auth
        old=authorization078(a['preparation_sha256'],a['policy_sha256'],a['helper_profile_sha256'],
            a['ledger_sha256'],a['entry_sha256'],a['build_record_sha256'],a['component_contract_sha256'])
        raw=encoded076(old)
        with self.assertRaises(ProbeRejected):validate_authorization081(raw,a,hashlib.sha256(raw).hexdigest())
        self.assertFalse(f.calls)
    def test_public_contract_or_invocation_binding_change_rejects(self):
        f=fixture081(self.root)
        for name in ('public_limits','invocation_contract_sha256','maximum_native_entry_invocations'):
            a=json.loads(f.raw)
            if name=='public_limits':a[name]['sidecar_bytes']=67
            elif name=='maximum_native_entry_invocations':a[name]=True
            else:a[name]='0'*64
            raw=encoded076(a)
            with self.assertRaises(ProbeRejected):validate_authorization081(raw,f.auth,hashlib.sha256(raw).hexdigest())
    def test_inner077_component_has_new_bindings_and_no_execution_authority(self):
        f=fixture081(self.root);v=json.loads(f.spec.component_raw)
        self.assertEqual(v['phase'],'77000000000000000000000000000001')
        self.assertFalse(v['execution_authorized']);self.assertEqual(v['bindings']['preparation'],f.spec.preparation)
    def test_trace_rejects_arbitrary_stage_operation_or_private_index(self):
        for values in (('secret','validate',None),('ledger','secret',None),('source','source_bytes',True),
                       ('source','source_bytes',64),('source','source_bytes',-1)):
            with self.assertRaises(PublicFailure081):self.trace.step(*values)
    def test_trace_limit_latches_and_retains_failure(self):
        self.trace.steps=128
        with self.assertRaises(PublicFailure081) as e:self.trace.step('ledger','validate')
        r=self.trace.outcome(False,e.exception)
        self.assertEqual(r['stop_reason'],'trace_budget_rejected');self.assertTrue(self.trace.stopped)
        with self.assertRaises(PublicFailure081):self.trace.step('checks','validate')
    def test_outcome_requires_authority_source_and_dispatch_before_success(self):
        with self.assertRaises(PublicFailure081):self.trace.outcome(True)
        self.trace.authority_validated=self.trace.source_pins_verified=self.trace.dispatch_reserved=True
        self.assertTrue(self.trace.outcome(True)['completed'])
        with self.assertRaises(PublicFailure081):self.trace.outcome(False,RuntimeError('private'))
    def test_unknown_exception_and_private_message_are_redacted(self):
        self.trace.step('helper_profile','sidecar_bytes')
        r=self.trace.outcome(False,RuntimeError('private-account-path-and-id'))
        self.assertEqual(r['stop_reason'],'unexpected_failure_redacted')
        self.assertNotIn('private-account',json.dumps(r));self.assertFalse(r['account_type_verified'])
        self.assertFalse(r['owned_cleanup_applicable']);self.assertEqual(r['sdk_connections'],0)
    def test_categories_do_not_export_os_messages(self):
        for error,expected in ((FileNotFoundError('secret'),'file_missing'),(PermissionError('secret'),'file_access_rejected'),
            (KeyboardInterrupt('secret'),'interrupted'),(PublicInputRejected080('timing_public_file_rejected'),'file_rejected'),
            (PublicInputRejected080('secret'),'unexpected_failure_redacted')):
            self.assertEqual(category081(error),expected)
    def test_record_rejects_malformed_sidecar_at_specific_substep(self):
        p=self.root/'r.json';p.write_bytes(b'{}');p.with_suffix('.sha256').write_bytes(b'0'*64+b'\r\n')
        with self.assertRaises(PublicInputRejected080) as e:self.trace.record('helper_profile',p)
        r=self.trace.outcome(False,e.exception)
        self.assertEqual((r['stopped_stage'],r['stopped_operation'],r['stop_reason']),
            ('helper_profile','sidecar_digest','digest_rejected'))
    def test_raw_authority_crlf_does_not_normalize_authority_bytes(self):
        p=self.root/'a.json';raw=b'{"a":1}\n';p.write_bytes(raw)
        p.with_suffix('.sha256').write_bytes(hashlib.sha256(raw).hexdigest().encode()+b'\r\n')
        got,digest=self.trace.authority(p)
        self.assertEqual(got,raw);self.assertEqual(digest,hashlib.sha256(raw).hexdigest())
    def test_source_failure_reports_only_fixed_index_and_operation(self):
        p=self.root/'secret';p.write_bytes(b'source')
        with self.assertRaises(PublicFailure081) as e:self.trace.source(p,'0'*64,3)
        r=self.trace.outcome(False,e.exception)
        self.assertEqual((r['stopped_stage'],r['stopped_operation'],r['source_index']),('source','source_digest',3))
        self.assertNotIn(str(p),json.dumps(r))
    def test_source_closure_includes_corrected_reader_trace_and_actual_guards(self):
        sources=entry.dependency_files081(Path(__file__).resolve().parents[1])
        for n in ('native_timing_081','public_preflight_080','public_trace_081','timing_profile_077','private_guard_065'):
            self.assertIn('src/forex_demo_lab/'+n+'.py',sources)
        self.assertNotIn('src/forex_demo_lab/native_timing_078.py',sources)
        self.assertLess(len(sources),64)
    def test_signature_metadata_still_has_exact_policy_builds_and_no_bypass(self):
        from test_timing_profile_077 import Clock077
        m=Meter077(Clock077());seen=[]
        result=NS(returncode=0,stdout=json.dumps(dict(valid=True,count=5,policy='Restricted',terminal_build=6244,editor_build=6244)),stderr='')
        def invoke(args,**kw):seen.append((args,kw));return result
        self.assertTrue(entry.signature081(Path('/shell'),m,invoke));self.assertEqual(seen[0][1]['timeout'],15)
        self.assertNotIn('-ExecutionPolicy',seen[0][0])
    def test_native_result_writer_is_bounded_exclusive_and_digest_returning(self):
        p=self.root/'out.json';digest=entry.write_result081(p,dict(completed=False))
        self.assertEqual(digest,hashlib.sha256(p.read_bytes()).hexdigest())
        self.assertEqual(p.with_suffix('.sha256').read_bytes(),digest.encode()+b'\n')
        with self.assertRaises(FileExistsError):entry.write_result081(p,{})
        with self.assertRaises(PublicFailure081):entry.write_result081(self.root/'large.json',dict(x='x'*65536))


class Pipeline081Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        self.f=sealed_fixture081(self.root);self.trace=PublicTrace081(PublicInputs080(lambda:DATE_CLOCK080))
    def prepare(self):
        with patch.object(entry,'ROOT',self.root):return entry.prepare081(self.trace,str(self.root/'launcher'))
    def capture_failure(self):
        try:self.prepare()
        except (Exception,KeyboardInterrupt) as e:return self.trace.outcome(False,e)
        self.fail('expected rejection')
    def test_full_public_pipeline_accepts_profile_and_authority_crlf(self):
        r=self.prepare();self.assertTrue(self.trace.authority_validated);self.assertTrue(self.trace.source_pins_verified)
        self.assertEqual(r['auth'],self.f.auth);self.assertEqual(self.trace.public.reads,12)
        self.assertEqual(self.trace.public.source_reads,3)
    def test_full_public_pipeline_accepts_lf_authority_unchanged(self):
        p=self.root/'reports/native-timing-081-authorization.sha256';p.write_bytes(p.read_bytes().replace(b'\r\n',b'\n'))
        self.assertEqual(self.prepare()['auth'],self.f.auth)
    def test_helper_profile_sidecar_oversize_identifies_record_substep(self):
        p=self.root/'reports/helper-profile-068.sha256';p.write_bytes(p.read_bytes()+b' ')
        r=self.capture_failure();self.assertEqual((r['stopped_stage'],r['stopped_operation'],r['stop_reason']),
            ('helper_profile','sidecar_bytes','file_rejected'))
    def test_missing_record_identifies_the_specific_public_stage(self):
        (self.root/'reports/native-timing-081-checks.json').unlink()
        r=self.capture_failure();self.assertEqual((r['stopped_stage'],r['stopped_operation'],r['stop_reason']),
            ('checks','record_bytes','file_missing'))
    def test_false_or_integer_preparation_boolean_rejects(self):
        p='reports/native-timing-081-completion-review.json';v=json.loads((self.root/p).read_bytes());v['review_passed']=1
        self.f.report(p,v);r=self.capture_failure();self.assertEqual(r['stopped_stage'],'preparation')
        self.assertFalse(r['authority_validated'])
    def test_stale_authority_and_matching_sidecar_reject_at_authority_validation(self):
        p='reports/native-timing-081-authorization.json';v=dict(self.f.auth);v['policy_sha256']='0'*64
        raw=encoded076(v);self.f.put(p,raw);self.f.put(str(Path(p).with_suffix('.sha256')),hashlib.sha256(raw).hexdigest().encode()+b'\r\n')
        r=self.capture_failure();self.assertEqual((r['stopped_stage'],r['stopped_operation'],r['stop_reason']),
            ('authorization','validate','authorization_rejected'))
    def test_source_content_change_rejects_before_dispatch(self):
        (self.root/self.f.sources[1]).write_bytes(b'changed')
        r=self.capture_failure();self.assertEqual(r['stopped_stage'],'source');self.assertEqual(r['stop_reason'],'binding_rejected')
        self.assertFalse(r['dispatch_reserved']);self.assertTrue(r['authority_validated'])
    def test_launcher_change_rejects_at_launcher_digest(self):
        (self.root/'launcher').write_bytes(b'helper image')
        r=self.capture_failure();self.assertEqual((r['stopped_stage'],r['stopped_operation']),('launcher','source_digest'))
        self.assertFalse(r['source_pins_verified'])
    def test_early_public_failure_spends_invocation_without_native_hooks(self):
        (self.root/'reports/helper-profile-068.sha256').write_bytes(b'x'*67);calls=[];output=io.StringIO()
        fixed_datetime=NS(now=lambda *a:datetime(2026,10,8,tzinfo=timezone.utc))
        with (patch.object(entry,'ROOT',self.root),patch.object(entry,'os',NS(name='nt',fsync=entry.os.fsync)),patch.object(entry,'datetime',fixed_datetime),
            patch.object(entry,'PublicInputs080',lambda:PublicInputs080(lambda:DATE_CLOCK080)),
            patch.object(entry,'hooks081',lambda *a:calls.append('hooks')),redirect_stdout(output)):
            self.assertFalse(entry.run())
        self.assertFalse(calls);self.assertTrue((self.root/'reports/native-timing-081-invocation-started.json').exists())
        self.assertFalse((self.root/'reports/native-timing-081-dispatch-started.json').exists())
        r=json.loads((self.root/'reports/native-timing-081-public-outcome.json').read_bytes())
        self.assertEqual(r['stopped_operation'],'sidecar_bytes');self.assertEqual(r['sdk_connections'],0)
    def test_restart_does_not_read_authority_or_call_native_hooks(self):
        reserve_invocation081(self.root/'reports/native-timing-081-invocation-started.json');calls=[]
        fixed_datetime=NS(now=lambda *a:datetime(2026,10,8,tzinfo=timezone.utc))
        with (patch.object(entry,'ROOT',self.root),patch.object(entry,'os',NS(name='nt')),patch.object(entry,'datetime',fixed_datetime),
            patch.object(entry,'prepare081',lambda *a:calls.append('prepare')),redirect_stdout(io.StringIO())):
            self.assertFalse(entry.run())
        self.assertFalse(calls);self.assertFalse((self.root/'reports/native-timing-081-public-outcome.json').exists())
    def test_nonwindows_entry_rejects_without_any_marker(self):
        with patch.object(entry,'ROOT',self.root),patch.object(entry,'os',NS(name='posix')),redirect_stdout(io.StringIO()):
            self.assertFalse(entry.run())
        self.assertFalse((self.root/'reports/native-timing-081-invocation-started.json').exists())
    def test_expired_date_rejects_without_any_marker(self):
        future=NS(now=lambda *a:datetime(2026,10,9,tzinfo=timezone.utc))
        with patch.object(entry,'ROOT',self.root),patch.object(entry,'os',NS(name='nt')),patch.object(entry,'datetime',future),redirect_stdout(io.StringIO()):
            self.assertFalse(entry.run())
        self.assertFalse((self.root/'reports/native-timing-081-invocation-started.json').exists())
    def test_full_pipeline_with_explicit_windows_unc_parent_model(self):
        mapping={str(WINDOWS_ROOT080/p.relative_to(self.root).as_posix()):p
            for p in self.root.rglob('*') if p.is_file()}
        model=model_paths080(mapping,self.root)
        with (patch.object(entry,'ROOT',WINDOWS_ROOT080),patch.object(entry,'Path',PureWindowsPath),
              patch.object(trace_module,'Path',PureWindowsPath),patch.object(reader_module,'Path',model)):
            r=entry.prepare081(self.trace,str(WINDOWS_ROOT080/'launcher'))
        self.assertEqual(r['auth'],self.f.auth)
        self.assertEqual(self.trace.public.stats,120);self.assertEqual(self.trace.public.reads,12)
        self.assertLess(self.trace.steps,128)
    def test_duplicate_traversal_and_invalid_source_schema_reject(self):
        for names in ([self.f.sources[0]]*2,[self.f.sources[0],'../private.py'],[self.f.sources[0],True]):
            with TemporaryDirectory() as d:
                f=sealed_fixture081(Path(d));f.ledger['runtime_sources']=names
                ledger_sha=f.report('reports/native-timing-081-ledger.json',f.ledger)
                f.report('reports/native-timing-081-checks.json',dict(checker_passed=True,ledger_sha256=ledger_sha))
                f.auth['ledger_sha256']=ledger_sha;raw=encoded076(f.auth)
                f.put('reports/native-timing-081-authorization.json',raw)
                f.put('reports/native-timing-081-authorization.sha256',hashlib.sha256(raw).hexdigest().encode()+b'\n')
                trace=PublicTrace081(PublicInputs080(lambda:DATE_CLOCK080))
                with patch.object(entry,'ROOT',Path(d)):
                    with self.assertRaises(PublicFailure081):entry.prepare081(trace,str(Path(d)/'launcher'))
                self.assertEqual(trace.stage,'source_schema')
    def test_public_clock_failure_is_recorded_before_any_dispatch(self):
        clock=list(DATE_CLOCK080);trace=PublicTrace081(PublicInputs080(lambda:tuple(clock)))
        clock[0]+=1001
        with patch.object(entry,'ROOT',self.root):
            with self.assertRaises(PublicInputRejected080) as e:entry.prepare081(trace,str(self.root/'launcher'))
        result=trace.outcome(False,e.exception)
        self.assertEqual((result['stopped_stage'],result['stopped_operation'],result['stop_reason']),
            ('ledger','record_bytes','clock_rejected'))
