import json
from pathlib import Path
import runpy
import subprocess
from tempfile import TemporaryDirectory
from threading import Event
import unittest
import test_transport_diagnostics_053 as fake
from forex_demo_lab.native_pipe_054 import *
from forex_demo_lab.capture_budget_047 import Policy,VERSION,start_authority
from forex_demo_lab.capture_wire_047 import encode_request,encode_response,decode_response

ROOT=Path(__file__).resolve().parents[1]
POLICY=Policy('54000000000000000000000000000001','54'*32)
def record(step='disabled'):
    code,req,valid,n,why={'disabled':(17,0,False,0,-1),'enabled':(0,1,True,84,0),'repeat':(20,0,False,0,-1)}[step]
    return dict(version='pipe_fixture_054_v1',reason_code=code,requests=req,receipt_valid=valid,
                reply_bytes=n,decode_reason=why,quote_reads=0,orders=0)
def text_record(r):return PREFIX+json.dumps(r)

class Native054Tests(unittest.TestCase):
    def state(self):s=Session054();s.save_baseline();return s
    def collect(self,s,step):s.arm(step);s.save_pending(step);return s.collect([record(step)])
    def test_new_default_proof_required_before_enabled(self):
        s=self.state()
        with self.assertRaises(ValueError):s.arm('enabled')
        self.assertEqual(s.arms,[])
    def test_all_three_native_outcomes_and_fourth_rejected(self):
        s=self.state()
        for step in STEPS:self.collect(s,step)
        with self.assertRaises(ValueError):s.arm('repeat')
        self.assertEqual(len(s.records),3)
    def test_baseline_required_and_cannot_be_repeated(self):
        s=Session054()
        with self.assertRaises(ValueError):s.arm('disabled')
        s.save_baseline()
        with self.assertRaises(ValueError):s.save_baseline()
    def test_matching_log_save_required_before_collection(self):
        s=self.state();s.arm('disabled')
        with self.assertRaises(ValueError):s.collect([record()])
        with self.assertRaises(ValueError):s.save_pending('enabled')
        s.save_pending('disabled')
        with self.assertRaises(ValueError):s.save_pending('disabled')
        s.collect([record()])
    def test_missing_extra_records_rejected(self):
        for rows in ([],[record(),record()]):
            s=self.state();s.arm('disabled');s.save_pending('disabled')
            with self.assertRaises(ValueError):s.collect(rows)
    def test_valid_unexpected_outcome_preserved(self):
        s=self.state();s.arm('disabled');s.save_pending('disabled')
        with self.assertRaises(ValueError):s.collect([record('enabled')])
        self.assertEqual(s.records,[record('enabled')])
    def test_no_next_arm_before_prior_collection(self):
        s=self.state();s.arm('disabled')
        with self.assertRaises(ValueError):s.arm('enabled')
    def test_session_deadline_and_reversal(self):
        for times in ((0,900),(10,9)):
            it=iter(times);s=Session054(clock=lambda:next(it))
            with self.assertRaises(ValueError):s.save_baseline()
    def test_closed_schema_rejects_boolean_counts_extra_private_fields(self):
        for r in (dict(record(),requests=True),dict(record(),account='private'),dict(record(),decode_reason=False),dict(record(),orders=1)):
            with self.assertRaises(ValueError):parse_record(text_record(r))
    def test_disabled_count_and_decoder_must_be_unattempted(self):
        for r in (dict(record(),reply_bytes=1),dict(record(),decode_reason=0)):
            with self.assertRaises(ValueError):parse_record(text_record(r))
    def test_valid_reply_length_and_code_correlate(self):
        self.assertEqual(parse_record(text_record(record('enabled'))),record('enabled'))
        for r in (dict(record('enabled'),reply_bytes=83),dict(record('enabled'),decode_reason=1)):
            with self.assertRaises(ValueError):parse_record(text_record(r))
    def test_invalid_native_reply_categories_remain_failure(self):
        for n,why in ((0,1),(83,1),(85,1),(84,3),(84,10),(84,13)):
            r=dict(record('enabled'),reason_code=23,receipt_valid=False,reply_bytes=n,decode_reason=why)
            self.assertEqual(parse_record(text_record(r)),r)
    def test_guard_failure_after_read_can_preserve_count(self):
        r=dict(record('enabled'),reason_code=4,receipt_valid=False,decode_reason=-1)
        self.assertEqual(parse_record(text_record(r)),r)
    def test_old_phase_and_duplicate_json_fields_rejected(self):
        self.assertEqual(records_from_log(('FXDL_PIPE051 '+json.dumps(record())).encode('utf-16-le')),[])
        with self.assertRaises(ValueError):parse_record(text_record(record()).replace('"requests": 0','"requests": 0,"requests": 0'))
    def test_parser_content_and_text_bounds(self):
        self.assertEqual(records_from_log(b'\0'*1048576),[])
        for raw in (b'x',b'\0'*1048578):
            with self.assertRaises(ValueError):records_from_log(raw)
        with self.assertRaises(ValueError):parse_record(text_record(record())+' '*2048)
    def test_log_save_then_single_visible_append(self):
        with TemporaryDirectory() as d:
            p=Path(d)/'log';p.write_bytes(b'');s=self.state();s.arm('disabled')
            with self.assertRaises(ValueError):s.require_saved('disabled')
            p.write_bytes(text_record(record()).encode('utf-16-le'));s.save_pending('disabled')
            self.assertEqual(s.collect(records_from_log(p.read_bytes())),record())
    def test_stopped_read_once_no_second_attempt(self):
        with TemporaryDirectory() as d:
            p=Path(d)/'log';p.write_bytes(text_record(record()).encode('utf-16-le'));attempted=set();out=[]
            self.assertTrue(collect_stopped_record(p,0,'disabled',attempted,out.append))
            self.assertFalse(collect_stopped_record(p,0,'disabled',attempted,out.append))
            self.assertEqual(out[0]['sdk_connections'],0)
    def test_stopped_read_does_not_retry_attempted_collection(self):
        self.assertFalse(collect_stopped_record(Path('absent'),0,'enabled',{'enabled'},lambda r:self.fail()))
    def test_io_stop_is_separate_from_session_guard(self):
        with TemporaryDirectory() as d:
            clock=fake.Clock();pipe=fake.Duplex();pipe.raw=encode_request(POLICY);whole_stop=Event();io_stop=Event()
            def guard():return not whole_stop.is_set()
            authority=start_authority(Path(d)/'p',POLICY,clock.authority,guard,lambda r:True)
            r=serve_diagnostic(pipe,1,'private',authority,POLICY,guard,900,io_stop,lambda h:False)
            self.assertTrue(io_stop.is_set());self.assertFalse(whole_stop.is_set());self.assertTrue(guard())
            self.assertTrue(r['reply_written'] and r['closed']);self.assertEqual(r['permissions_consumed'],1)
    def test_integrated_write_failure_identifies_stage(self):
        with TemporaryDirectory() as d:
            clock=fake.Clock();pipe=fake.Duplex();pipe.raw=encode_request(POLICY);pipe.fail='reply_write'
            authority=start_authority(Path(d)/'p',POLICY,clock.authority,lambda:True,lambda r:True)
            r=serve_diagnostic(pipe,1,'private',authority,POLICY,lambda:True,900,Event(),lambda h:False)
            self.assertEqual(r['events'][-3]['stage'],'reply_write');self.assertEqual(r['stop_reason'],'io_operation_rejected')
            self.assertEqual(r['permissions_consumed'],1);self.assertTrue(r['closed'])
    def test_integrated_pending_handle_not_closed(self):
        with TemporaryDirectory() as d:
            clock=fake.Clock();pipe=fake.Duplex();pipe.fail='request_read'
            authority=start_authority(Path(d)/'p',POLICY,clock.authority,lambda:True,lambda r:True)
            r=serve_diagnostic(pipe,1,'private',authority,POLICY,lambda:True,900,Event(),lambda h:True)
            self.assertTrue(r['pending_retained']);self.assertFalse(r['closed']);self.assertNotIn('pipe_close',pipe.calls)
    def test_actual_mql_default_and_account_guards_unchanged(self):
        source=(ROOT/'mt5/Scripts/ForexDemoPipeFixture054.mq5').read_text()
        self.assertLess(source.index('if(!ExerciseTransport)'),source.index('FileOpen('))
        self.assertIn('input bool ExerciseTransport=false;',source);self.assertEqual(source.count('AccountReason042('),3)
        self.assertIn('2026.10.07',source)
        self.assertNotRegex(source,r'\b(SymbolInfoTick|OrderSend|CopyTicks|CopyRates|SymbolSelect|OnTick|OnTimer|#import)\b')
    def test_native_logging_has_counts_no_private_identifiers(self):
        source=(ROOT/'mt5/Scripts/ForexDemoPipeFixture054.mq5').read_text()
        for line in source.splitlines():
            if 'PrintFormat(' in line:self.assertNotRegex(line,r'login|server|PHASE054|POLICY054')
        self.assertIn('DecodeReason053(wire,PHASE054,POLICY054,utc,boot,date_ok)',source)
        self.assertIn('Decode047(wire,PHASE054,POLICY054,utc,boot,date_ok)',source)
    def test_shared_native_decoder_87_new_phase_frames(self):
        receipt=dict(version=VERSION,phase=POLICY.phase,policy_sha256=POLICY.digest,permission=1,
                     issued_boot_ms=100000,expires_boot_ms=102000,expires_utc_ms=1791352802000)
        raw=encode_response(receipt);cases=[raw,raw[:-1],raw+b'x']
        for i in range(84):b=bytearray(raw);b[i]^=1;cases.append(bytes(b))
        expected=[]
        for b in cases:
            try:decode_response(b,POLICY,1791352800000,100000);expected.append('1')
            except ValueError:expected.append('0')
        with TemporaryDirectory() as d:
            exe=Path(d)/'wire'
            subprocess.run(['g++','-std=c++17','-Wall','-Wextra','-Werror',str(ROOT/'mt5/Tests/CaptureWire054.cpp'),'-o',str(exe)],check=True,capture_output=True,timeout=30)
            out=subprocess.run([str(exe)],input=''.join('1791352800000 100000 '+b.hex()+'\n' for b in cases),text=True,capture_output=True,check=True,timeout=5)
        self.assertEqual(out.stdout.splitlines(),expected);self.assertEqual(len(cases),87)
    def test_original_051_source_and_failed_evidence_stay_sealed(self):
        api=runpy.run_path(str(ROOT/'scripts/native-pipe-051.py'))
        prior=api['sealed'](ROOT/'reports/transport-diagnostics-053-final-source.json')['source_and_evidence_bindings']
        for n in ('scripts/runtime-native-pipe-051.py','mt5/Scripts/ForexDemoPipeFixture051.mq5','reports/native-pipe-051-runtime.json'):
            self.assertEqual(api['sha'](ROOT/n),prior[n])
    def test_runtime_has_interactive_guard_and_no_market_facade(self):
        source=(ROOT/'scripts/runtime-native-pipe-054.py').read_text()
        self.assertLess(source.index('require_interactive(sys.stdin)'),source.index('write(RESERVATION'))
        self.assertIn('io_stop=Event()',source);self.assertIn('serve_diagnostic(',source)
        self.assertNotRegex(source,r'\b(order_send|symbol_info_tick|copy_ticks|copy_rates|login)\s*\(')

if __name__=='__main__':unittest.main()
