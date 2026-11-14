import copy
import json
from pathlib import Path
import runpy
import subprocess
from tempfile import TemporaryDirectory
from threading import Event
import time
import unittest
import test_transport_diagnostics_053 as fake
from test_read_diagnostics_056 import Kernel
from forex_demo_lab.native_pipe_057 import *
from forex_demo_lab.windows_pipe_047 import _PENDING
from forex_demo_lab.capture_budget_047 import Policy,VERSION,start_authority
from forex_demo_lab.capture_wire_047 import encode_request,encode_response,decode_response

ROOT=Path(__file__).resolve().parents[1]
POLICY=Policy('57000000000000000000000000000001','57'*32)
def record(step='disabled'):
    code,req,valid,n,why={'disabled':(17,0,False,0,-1),'enabled':(0,1,True,84,0),'repeat':(20,0,False,0,-1)}[step]
    return dict(version='pipe_fixture_057_v1',reason_code=code,requests=req,receipt_valid=valid,reply_bytes=n,
        decode_reason=why,read_error_category=0 if step=='enabled' else -1,
        read_elapsed_us=10 if step=='enabled' else -1,read_timing=0 if step=='enabled' else -1,quote_reads=0,orders=0)
def text(r):return PREFIX+json.dumps(r)

class Native057Tests(unittest.TestCase):
    def setUp(self):
        self.kernel=Kernel();self.ns=0
        def now():self.ns+=1000;return self.ns
        self.pipe=ManualWindowsPipe057(injected_api=self.kernel,now=now)
        self.pending_start=len(_PENDING)
        self.addCleanup(lambda:_PENDING.__delitem__(slice(self.pending_start,None)))
    def connect(self, samples=(0,0,0)):
        it=iter(samples);return self.pipe.connect_until(7,5,Event(),clock=lambda:next(it))
    def service(self,guard=None,pending=None):
        self.kernel.payload=encode_request(POLICY);self.kernel.count=56
        def write(*args):self.kernel.count=len(args[1]);return self.kernel.submit()
        self.pipe.write=write
        self.pipe.peer=lambda *args:True
        self.pipe.connect_until=lambda h,d,s:ManualWindowsPipe057.connect_until(self.pipe,h,d,s,clock=lambda:0)
        self.tmp=TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.clock=fake.Clock();self.guard=guard or (lambda:True)
        self.authority=start_authority(Path(self.tmp.name)/'permit',POLICY,self.clock.authority,self.guard,lambda r:True)
        return serve_diagnostic(self.pipe,7,'private identity',self.authority,POLICY,self.guard,5,Event(),
            pending or (lambda h:any(x[3]==h for x in _PENDING)))
    def test_three_steps_with_fresh_disabled_proof(self):
        s=Session057();s.save_baseline()
        for step in STEPS:s.arm(step);s.save_pending(step);s.collect([record(step)])
        with self.assertRaises(ValueError):s.arm('repeat')
    def test_baseline_and_saved_log_required(self):
        s=Session057()
        with self.assertRaises(ValueError):s.arm('disabled')
        s.save_baseline();s.arm('disabled')
        with self.assertRaises(ValueError):s.collect([record()])
    def test_failed_native_result_retained_and_no_next_arm(self):
        s=Session057();s.save_baseline();s.arm('disabled');s.save_pending('disabled');s.collect([record()])
        s.arm('enabled');s.save_pending('enabled');r=dict(record('enabled'),reason_code=23,receipt_valid=False,reply_bytes=0,decode_reason=1,read_error_category=5)
        with self.assertRaises(ValueError):s.collect([r])
        self.assertEqual(s.records[-1],r)
        # Runtime stops on exception; no automatic next arm or permission is issued.
        self.assertEqual(s.arms,['disabled','enabled'])
        with self.assertRaises(ValueError):s.arm('repeat')
    def test_closed_native_schema_privacy_and_boolean_rejection(self):
        for r in (dict(record(),private_account='secret'),dict(record(),read_elapsed_us=True),dict(record(),read_error_category=1),dict(record(),orders=1)):
            with self.assertRaises(ValueError):parse_record(text(r))
    def test_unattempted_read_is_distinct_from_zero_read(self):
        self.assertEqual(parse_record(text(record()))['read_timing'],-1)
        r=dict(record('enabled'),reason_code=23,receipt_valid=False,reply_bytes=0,decode_reason=1,read_error_category=0,read_elapsed_us=0)
        self.assertEqual(parse_record(text(r))['read_timing'],0)
    def test_native_measurement_overrun_and_clock_invalid(self):
        for us,timing in ((-1,1),(900000000,0)):
            r=dict(record('enabled'),reason_code=24,receipt_valid=False,read_elapsed_us=us,read_timing=timing)
            self.assertEqual(parse_record(text(r)),r)
    def test_native_read_error_with_valid_frame_rejects_success(self):
        r=dict(record('enabled'),read_error_category=5)
        with self.assertRaises(ValueError):parse_record(text(r))
        r.update(reason_code=24,receipt_valid=False);self.assertEqual(parse_record(text(r)),r)
    def test_guard_failure_keeps_measured_read_evidence(self):
        r=dict(record('enabled'),reason_code=4,receipt_valid=False,decode_reason=-1)
        self.assertEqual(parse_record(text(r)),r)
    def test_old_prefix_duplicate_and_extra_records(self):
        self.assertEqual(records_from_log(('FXDL_PIPE054 '+json.dumps(record())).encode('utf-16-le')),[])
        with self.assertRaises(ValueError):parse_record(text(record()).replace('"requests": 0','"requests": 0,"requests": 0'))
        self.assertEqual(len(records_from_log((text(record())+'\n'+text(record())).encode('utf-16-le'))),2)
    def test_native_log_bounds(self):
        for raw in (b'x',b'\0'*1048578):
            with self.assertRaises(ValueError):records_from_log(raw)
    def test_manual_immediate_and_already_connected(self):
        for error in (None,535):
            self.kernel.submit_error=error;self.connect();r=validate_operation(self.pipe.last_connect)
            self.assertTrue(r['event_closed']);self.assertEqual(r['submit_category'],'ok' if error is None else 'pipe_connected')
    def test_manual_pending_completion(self):
        self.kernel.submit_error=997;self.connect((0,0,0))
        r=self.pipe.last_connect;self.assertEqual(r['completion_category'],'ok');self.assertEqual(self.kernel.wait_calls,[100])
    def test_manual_immediate_failure_category(self):
        self.kernel.submit_error=109
        with self.assertRaises(PipeRejected):self.connect()
        self.assertEqual(self.pipe.last_connect['submit_category'],'broken_pipe')
    def test_manual_timeout_cancel_drain(self):
        self.kernel.submit_error=997;self.kernel.waits=[0];self.kernel.completion_error=995
        with self.assertRaisesRegex(PipeRejected,'manual_connect_cancelled_or_expired'):self.connect((0,5))
        r=self.pipe.last_connect;self.assertEqual(r['completion_category'],'operation_aborted');self.assertFalse(r['pending_retained'])
    def test_manual_cancel_incomplete_retains_memory(self):
        self.kernel.submit_error=997;self.kernel.waits=[0];self.kernel.completion_error=996
        with self.assertRaisesRegex(PipeRejected,'cancellation_not_drained'):self.connect((0,5))
        self.assertTrue(self.pipe.last_connect['pending_retained']);self.assertEqual(_PENDING[-1][3],7)
    def test_manual_undrained_cancel_retains(self):
        self.kernel.submit_error=997;self.kernel.waits=[258]
        with self.assertRaisesRegex(PipeRejected,'cancellation_not_drained'):self.connect((0,5))
        self.assertFalse(self.pipe.last_connect['event_closed'])
    def test_manual_failed_wait_captured_separately(self):
        self.kernel.submit_error=997;self.kernel.waits=[0xffffffff,0]
        with self.assertRaises(PipeRejected):self.connect((0,0,0))
        r=self.pipe.last_connect;self.assertEqual(r['wait_category'],'invalid_handle');self.assertEqual(r['drain_category'],'ok')
    def test_manual_clock_reversal_rejected_and_drained(self):
        self.kernel.submit_error=997
        with self.assertRaises(PipeRejected):self.connect((1,0))
        self.assertEqual(self.kernel.cancel_calls,1)
    def test_manual_event_cleanup_failure_prevents_success(self):
        self.kernel.close_error=6
        with self.assertRaisesRegex(PipeRejected,'close_result_rejected'):self.connect()
        self.assertFalse(self.pipe.last_connect['event_closed'])
    def test_io_event_cleanup_failure_prevents_success(self):
        self.kernel.close_error=6
        with self.assertRaisesRegex(PipeRejected,'close_result_rejected'):self.pipe.io(7,'read',size=84)
    def test_integrated_success_reports_actual_completed_write(self):
        r=self.service();self.assertTrue(r['reply_written'] and r['closed']);self.assertEqual(r['permissions_consumed'],1)
        self.assertEqual([x['version'] for x in r['windows_operations']],['manual_connect_057_v1','windows_io_056_v1','windows_io_056_v1'])
        self.assertEqual(r['windows_operations'][-1]['transferred_bytes'],84)
    def test_integrated_immediate_write_failure_attempted_not_delivered(self):
        original=self.service
        def write(*args):self.kernel.error=109;return False
        # service sets a successful write function; replace just before request issuance.
        r=original(guard=lambda:setattr(self.pipe,'write',write) or True)
        self.assertFalse(r['reply_written']);self.assertEqual(r['permissions_consumed'],1)
        self.assertEqual(r['windows_operations'][-1]['events'][1]['category'],'broken_pipe')
        self.assertIsNone(r['windows_operations'][-1]['transferred_bytes'])
    def test_integrated_pending_read_keeps_handle(self):
        def guard():self.kernel.submit_error=997;self.kernel.waits=[258,258];return True
        r=self.service(guard=guard);self.assertTrue(r['pending_retained']);self.assertFalse(r['closed'])
        self.assertEqual(r['permissions_consumed'],0)
    def test_integrated_cleanup_failure_blocks_reply_success(self):
        r=self.service(guard=lambda:setattr(self.kernel,'close_error',6) or True)
        self.assertFalse(r['reply_written']);self.assertEqual(r['stop_reason'],'close_result_rejected')
    def test_integrated_delayed_guard_issues_after_delay(self):
        calls=[]
        def guard():
            calls.append(1)
            if len(calls)==2:self.clock.ns+=3197324000
            return True
        # start_authority checks guard before self.clock exists; delay only the later call.
        r=self.service(guard=guard);self.assertTrue(r['reply_written']);self.assertEqual(r['permissions_consumed'],1)
        self.assertGreaterEqual(self.clock.ns,3197324000)
    def test_windows_report_schema_rejects_private_fields_and_unknown_categories(self):
        self.connect();r=self.pipe.last_connect
        for bad in (dict(r,account='secret'),dict(r,submit_category='private server'),dict(r,wait_calls=True),dict(r,elapsed_us=901000001)):
            with self.assertRaises(ValueError):validate_operation(bad)
    def test_native_source_exact_measurement_order_and_85_count(self):
        s=(ROOT/'mt5/Scripts/ForexDemoPipeFixture057.mq5').read_text()
        a=s.index('uchar reply[85]');b=s.index('FileReadArray(h,reply,0,85)');c=s.index('int read_error=GetLastError()',b);d=s.index('FileClose(h)',c)
        self.assertLess(a,b);self.assertLess(b,c);self.assertLess(c,d)
        self.assertNotIn('ReadCandidate056(',s);self.assertNotIn('FileReadInteger(',s)
    def test_native_actual_guards_default_and_no_market_api(self):
        s=(ROOT/'mt5/Scripts/ForexDemoPipeFixture057.mq5').read_text()
        self.assertEqual(s.count('AccountReason042('),3);self.assertIn('input bool ExerciseTransport=false;',s)
        self.assertLess(s.index('if(!ExerciseTransport)'),s.index('FileOpen('))
        self.assertNotRegex(s,r'\b(SymbolInfoTick|OrderSend|CopyTicks|CopyRates|SymbolSelect|#import)\b')
    def test_native_87_fresh_phase_decoder_frames(self):
        raw=encode_response(dict(version=VERSION,phase=POLICY.phase,policy_sha256=POLICY.digest,permission=1,
            issued_boot_ms=100000,expires_boot_ms=102000,expires_utc_ms=1791352802000))
        cases=[raw,raw[:-1],raw+b'x']
        for i in range(84):b=bytearray(raw);b[i]^=1;cases.append(bytes(b))
        expected=[]
        for b in cases:
            try:decode_response(b,POLICY,1791352800000,100000);expected.append('1')
            except ValueError:expected.append('0')
        with TemporaryDirectory() as d:
            exe=Path(d)/'wire';subprocess.run(['g++','-std=c++17','-Wall','-Wextra','-Werror',str(ROOT/'mt5/Tests/CaptureWire057.cpp'),'-o',str(exe)],check=True,capture_output=True,timeout=30)
            out=subprocess.run([str(exe)],input=''.join('1791352800000 100000 '+b.hex()+'\n' for b in cases),text=True,capture_output=True,check=True,timeout=5)
        self.assertEqual(out.stdout.splitlines(),expected)
    def test_frozen_054_and_056_sources_unchanged(self):
        a=runpy.run_path(str(ROOT/'scripts/transport-diagnostics-056.py'));b=a['sealed'](ROOT/'reports/transport-diagnostics-056-final-source.json')['source_and_evidence_bindings']
        for n in ('src/forex_demo_lab/windows_pipe_047.py','src/forex_demo_lab/windows_pipe_diagnostics_056.py','mt5/Scripts/ForexDemoPipeFixture054.mq5','reports/native-pipe-054-runtime.json'):
            self.assertEqual(a['sha'](ROOT/n),b[n])
    def test_readiness_and_identity_checks_not_cached_or_weakened(self):
        from forex_demo_lab.native_pipe_049 import Readiness049
        self.assertIs(Readiness057,Readiness049)
        from forex_demo_lab.windows_pipe_047 import WindowsPipe
        self.assertIs(ManualWindowsPipe057.identity,WindowsPipe.identity)
    def test_runtime_requires_separate_authorization_before_sdk(self):
        s=(ROOT/'scripts/runtime-native-pipe-057.py').read_text()
        self.assertLess(s.index('runtime-authorization.json'),s.index('import MetaTrader5'))
        self.assertIn('io_stop=Event()',s);self.assertNotRegex(s,r'\b(order_send|symbol_info_tick|copy_ticks|copy_rates|login)\s*\(')
        auth=dict(version='native_runtime_057_v1',runtime_authorized=True,preparation_sha256='a'*64,plan_sha256='b'*64,
            phase=POLICY.phase,date='2026-10-07',maximum_sdk_connections=1,maximum_script_arms=3,
            maximum_grants=1,maximum_deployments=1,maximum_session_seconds=900,maximum_io_ms=2000,maximum_drain_ms=1000)
        self.assertEqual(validate_runtime_authorization(auth,'a'*64,'b'*64),auth)
        for bad in ({},dict(auth,maximum_grants=2),dict(auth,maximum_sdk_connections=True),dict(auth,account='secret'),dict(auth,phase='54'*16)):
            with self.assertRaises(ValueError):validate_runtime_authorization(bad,'a'*64,'b'*64)

if __name__=='__main__':unittest.main()
