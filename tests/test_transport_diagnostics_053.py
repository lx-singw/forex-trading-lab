import copy
import json
from pathlib import Path
import struct
import subprocess
from tempfile import TemporaryDirectory
from threading import Event
import unittest

from forex_demo_lab.capture_budget_047 import Policy,PermitRejected,start_authority,VERSION
from forex_demo_lab.capture_wire_047 import encode_request,encode_response,decode_response
from forex_demo_lab.transport_diagnostics_053 import *

ROOT=Path(__file__).resolve().parents[1]
UTC=1791352800000;BOOT=100000
POLICY=Policy('53000000000000000000000000000001','53'*32)

def receipt(**updates):
    r=dict(version=VERSION,phase=POLICY.phase,policy_sha256=POLICY.digest,permission=1,
        issued_boot_ms=BOOT,expires_boot_ms=BOOT+2000,expires_utc_ms=UTC+2000)
    r.update(updates);return r

class Clock:
    def __init__(self):self.ns=0
    def now(self):self.ns+=1000000;return self.ns
    def authority(self):return UTC+self.ns//1000000,self.ns,BOOT+self.ns//1000000

class Duplex:
    """Injected peer consumes the complete reply; never opens a native pipe."""
    def __init__(self):
        self.fail=None;self.raw=encode_request(POLICY);self.delivered=b'';self.calls=[];self.close_result=True
    def check(self,stage):
        self.calls.append(stage)
        if self.fail==stage:raise PipeRejected('io_operation_rejected')
    def connect_until(self,h,deadline,stop):self.check('connect')
    def peer(self,h,side,expected):self.check('peer')
    def io(self,h,kind,data=None,size=0):
        self.check('request_read' if kind=='read' else 'reply_write')
        if kind=='read':return self.raw
        self.delivered=data
        return b''
    def close(self,h):self.check('pipe_close');return self.close_result

class Diagnostics053Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.clock=Clock();self.pipe=Duplex();self.stop=Event();self.guard_failure=None;self.journal_failure=False
        def guard():
            if self.guard_failure is not None:raise ValueError(self.guard_failure)
            return True
        def journal(r):
            if self.journal_failure:raise RuntimeError('private journal content must never appear')
            return True
        self.guard=guard
        self.authority=start_authority(Path(self.tmp.name)/'reservation',POLICY,self.clock.authority,guard,journal)
    def run_service(self,**kwargs):
        return serve(self.pipe,1,'private peer identity',self.authority,POLICY,self.guard,900,self.stop,
                     clock=kwargs.pop('clock',self.clock.now),**kwargs)
    def test_complete_duplex_reply_and_closed_authority(self):
        r=self.run_service()
        self.assertIsNone(r['stop_reason']);self.assertIsNone(r['cleanup_reason'])
        self.assertTrue(r['reply_written'] and r['closed'] and self.stop.is_set())
        self.assertEqual(r['permissions_consumed'],1);self.assertEqual(len(self.pipe.delivered),84)
        self.assertEqual(decode_reason(self.pipe.delivered,POLICY,UTC+100,BOOT+100),0)
        self.assertEqual([e['stage'] for e in r['events']],list(STAGES))
    def test_connection_failure_cleanup_no_permission(self):
        self.pipe.fail='connect';r=self.run_service()
        self.assertEqual(r['events'][0]['reason'],'io_operation_rejected');self.assertEqual(r['permissions_consumed'],0)
        self.assertTrue(r['closed']);self.assertTrue(self.authority.summary()['closed'])
    def test_peer_failure_blocks_guard_and_issue(self):
        self.pipe.fail='peer';r=self.run_service()
        self.assertEqual(r['events'][-3]['stage'],'peer');self.assertEqual(r['permissions_consumed'],0)
    def test_disconnection_fixed_guard_reason(self):
        self.guard_failure='disconnected';r=self.run_service()
        self.assertEqual(r['stop_reason'],'disconnected');self.assertEqual(r['events'][-3]['stage'],'guard')
        self.assertEqual(r['permissions_consumed'],0)
    def test_request_read_failure_no_issue(self):
        self.pipe.fail='request_read';r=self.run_service()
        self.assertEqual(r['events'][-3]['stage'],'request_read');self.assertEqual(r['permissions_consumed'],0)
    def test_bad_request_burns_single_permission(self):
        self.pipe.raw=b'x'*56;r=self.run_service()
        self.assertEqual(r['stop_reason'],'request_binding_rejected');self.assertEqual(r['permissions_consumed'],1)
        self.assertEqual(r['events'][-3]['stage'],'request_decode')
        with self.assertRaises(PermitRejected):self.authority.issue(POLICY.phase,POLICY.digest)
    def test_short_request_burns_and_no_reply(self):
        self.pipe.raw=self.pipe.raw[:-1];r=self.run_service()
        self.assertEqual(r['stop_reason'],'request_length_rejected');self.assertEqual(r['permissions_consumed'],1)
        self.assertFalse(r['reply_written'])
    def test_extra_request_burns_and_no_reply(self):
        self.pipe.raw+=b'x';r=self.run_service()
        self.assertEqual(r['stop_reason'],'request_length_rejected');self.assertEqual(r['permissions_consumed'],1)
    def test_issue_journal_failure_burns(self):
        self.journal_failure=True;r=self.run_service()
        self.assertEqual(r['stop_reason'],'consumption_journal_rejected');self.assertEqual(r['permissions_consumed'],1)
        self.assertEqual(r['events'][-3]['stage'],'issue')
    def test_second_guard_failure_after_journal_is_identified_as_issue(self):
        self.authority._journal=lambda row:setattr(self,'guard_failure','disconnected') or True
        r=self.run_service();self.assertEqual(r['stop_reason'],'private_account_or_instrument_guard_rejected')
        self.assertEqual(r['permissions_consumed'],1);self.assertFalse(r['reply_written'])
    def test_encode_schema_failure_preserves_burn(self):
        original=self.authority.issue
        def bad(*args):r=original(*args);r['extra']='private';return r
        self.authority.issue=bad;r=self.run_service()
        self.assertEqual(r['stop_reason'],'response_schema_rejected');self.assertEqual(r['events'][-3]['stage'],'encode')
        self.assertEqual(r['permissions_consumed'],1)
    def test_write_failure_identifies_stage_and_burn(self):
        self.pipe.fail='reply_write';r=self.run_service()
        self.assertEqual(r['events'][-3]['stage'],'reply_write');self.assertFalse(r['reply_written'])
        self.assertEqual(r['permissions_consumed'],1);self.assertTrue(r['closed'])
    def test_explicit_two_second_write_timeout(self):
        original=self.pipe.io
        def io(*args,**kw):
            if args[1]=='write':
                self.clock.ns+=2000000000
                raise PipeRejected('io_deadline_exceeded')
            return original(*args,**kw)
        self.pipe.io=io;r=self.run_service();self.assertEqual(r['stop_reason'],'io_deadline_exceeded')
        self.assertTrue(r['closed']);self.assertEqual(r['permissions_consumed'],1)
        self.assertGreaterEqual(r['events'][-3]['elapsed_us'],2000000)
    def test_short_write_is_not_reported_success(self):
        original=self.pipe.io
        def io(*args,**kw):
            if args[1]=='write':raise PipeRejected('short_write_rejected')
            return original(*args,**kw)
        self.pipe.io=io;r=self.run_service();self.assertEqual(r['stop_reason'],'short_write_rejected')
        self.assertFalse(r['reply_written'])
    def test_cancellation_pending_memory_and_handle_retained(self):
        self.pipe.fail='request_read';r=self.run_service(pending=lambda h:True)
        self.assertTrue(r['pending_retained']);self.assertFalse(r['closed'])
        self.assertNotIn('pipe_close',self.pipe.calls);self.assertEqual(r['cleanup_reason'],'cleanup_pending_retained')
        self.assertTrue(self.authority.summary()['closed'])
    def test_cleanup_failures_still_attempt_both_closures(self):
        self.authority.close=lambda:(_ for _ in ()).throw(RuntimeError('private closure'))
        r=self.run_service();self.assertTrue(r['closed']);self.assertEqual(r['cleanup_reason'],'unexpected_failure')
    def test_failed_handle_close_is_explicit(self):
        self.pipe.close_result=False;r=self.run_service()
        self.assertFalse(r['closed']);self.assertEqual(r['cleanup_reason'],'close_result_rejected')
    def test_clock_reversal_closes_without_issue(self):
        samples=iter((10,9));r=self.run_service(clock=lambda:next(samples))
        self.assertEqual(r['stop_reason'],'clock_reversed');self.assertTrue(r['closed'])
        self.assertEqual(r['permissions_consumed'],0)
    def test_invalid_initial_clock_still_closes(self):
        r=self.run_service(clock=lambda:True)
        self.assertEqual(r['stop_reason'],'clock_invalid');self.assertTrue(r['closed'])
    def test_whole_session_expiry_no_extension(self):
        samples=iter((0,LIMIT_NS));r=self.run_service(clock=lambda:next(samples))
        self.assertEqual(r['stop_reason'],'session_deadline_exceeded');self.assertTrue(r['closed'])
    def test_private_exception_text_and_peer_never_exported(self):
        self.guard_failure='private account and password';r=self.run_service();encoded=json.dumps(r)
        self.assertEqual(r['stop_reason'],'unexpected_failure');self.assertNotIn('private',encoded)
        self.assertNotIn('password',encoded);self.assertNotIn(POLICY.phase,encoded)
    def test_summary_failure_is_unknown_not_fabricated_zero(self):
        self.authority.summary=lambda:{'permissions_consumed':True};r=self.run_service()
        self.assertIsNone(r['permissions_consumed']);self.assertEqual(r['cleanup_reason'],'summary_rejected')
    def test_closed_report_rejects_extra_fields_boolean_counts_and_wrong_order(self):
        good=self.run_service()
        changes=[dict(good,account='private'),dict(good,quote_reads=True),dict(good,permissions_consumed=True),
                 dict(good,stop_reason=['private']),dict(good,events=list(reversed(good['events']))),dict(good,reply_written=False)]
        for bad in changes:
            with self.subTest(bad=bad),self.assertRaises(ValueError):validate_report(bad)
    def test_report_bounds_reject_excess_bytes_duration_and_raw_events(self):
        good=self.run_service()
        for key,value in (('byte_count',86),('elapsed_us',900000001),('reason','private')):
            bad=copy.deepcopy(good);bad['events'][3][key]=value
            with self.assertRaises(ValueError):validate_report(bad)
    def test_native_record_byte_length_rejections_are_closed(self):
        for raw in (b'',b'x'*83,b'x'*85):
            r=native_record(raw,POLICY,UTC,BOOT);self.assertEqual(r['decode_reason'],1)
            self.assertEqual(r['reply_bytes'],len(raw));self.assertFalse(r['receipt_valid'])
        with self.assertRaises(ValueError):native_record(b'x'*86,POLICY,UTC,BOOT)
    def test_native_record_schema_and_cross_field_consistency(self):
        good=native_record(encode_response(receipt()),POLICY,UTC,BOOT)
        for bad in (dict(good,reply_bytes=True),dict(good,login='private'),dict(good,decode_reason=1),
                    dict(good,receipt_valid=False),dict(good,orders=1)):
            with self.assertRaises(ValueError):validate_native_record(bad)
    def test_exact_receipt_expiry_and_restart_categories(self):
        raw=encode_response(receipt())
        self.assertEqual(decode_reason(raw,POLICY,UTC+2000,BOOT+2000),10)
        self.assertEqual(decode_reason(raw,POLICY,UTC+2000,BOOT),13)
        self.assertEqual(decode_reason(raw,POLICY,UTC,BOOT-1),9)
        self.assertEqual(decode_reason(raw,POLICY,UTC,BOOT,False),8)
        self.assertEqual(decode_reason(raw,POLICY,UTC+1999,BOOT+1999),0)
    def test_diagnostic_categories_preserve_legacy_acceptance(self):
        good=encode_response(receipt());cases=[good,good[:-1],good+b'x']
        for i in range(84):
            r=bytearray(good);r[i]^=1;cases.append(bytes(r))
        for raw in cases:
            try:decode_response(raw,POLICY,UTC,BOOT);accepted=True
            except PermitRejected:accepted=False
            self.assertEqual(decode_reason(raw,POLICY,UTC,BOOT)==0,accepted)
    def test_shared_actual_mql_header_matches_all_categories(self):
        good=encode_response(receipt());cases=[(good,UTC,BOOT,True)]
        for i in range(84):
            r=bytearray(good);r[i]^=1;cases.append((bytes(r),UTC,BOOT,True))
        cases += [(good[:n],UTC,BOOT,True) for n in (0,1,56,83)] + [(good+b'x',UTC,BOOT,True)]
        cases += [(good,UTC,BOOT,False),(good,UTC,BOOT-1,True),(good,UTC,BOOT+2000,True),
                  (good,0,BOOT,True),(good,UTC+2000,BOOT,True),(good,UTC-1,BOOT,True)]
        cases += [(encode_response(receipt(expires_boot_ms=BOOT+2001)),UTC,BOOT,True),
                  (encode_response(receipt(expires_utc_ms=0)),UTC,BOOT,True),
                  (encode_response(receipt(issued_boot_ms=9007199254740992)),UTC,BOOT,True)]
        expected=[decode_reason(raw,POLICY,u,b,d) for raw,u,b,d in cases]
        self.assertEqual(len(cases),99)
        with TemporaryDirectory() as d:
            exe=Path(d)/'wire'
            subprocess.run(['g++','-std=c++17','-Wall','-Wextra','-Werror',str(ROOT/'mt5/Tests/CaptureWireDiagnostics053.cpp'),'-o',str(exe)],check=True,capture_output=True,timeout=30)
            rows=''.join(f'{u} {b} {int(date)} '+(raw.hex() if raw else '-')+'\n' for raw,u,b,date in cases)
            out=subprocess.run([str(exe)],input=rows,text=True,capture_output=True,check=True,timeout=5)
        observed=[tuple(map(int,line.split())) for line in out.stdout.splitlines()]
        self.assertEqual(observed,[(code,int(code==0)) for code in expected])
    def test_native_header_has_no_market_or_side_effect_api(self):
        source=(ROOT/'mt5/Scripts/CaptureWireDiagnostics053.mqh').read_text()
        self.assertNotRegex(source,r'\b(FileOpen|OrderSend|SymbolInfoTick|CopyRates|CopyTicks|AccountInfoInteger|#import)\b')
    def test_write_return_type_cannot_fake_success(self):
        original=self.pipe.io
        self.pipe.io=lambda *a,**k:bytearray() if a[1]=='write' else original(*a,**k)
        r=self.run_service();self.assertEqual(r['stop_reason'],'write_result_rejected');self.assertFalse(r['reply_written'])
    def test_pending_check_exception_retains_handle_conservatively(self):
        def pending(h):raise RuntimeError('private')
        r=self.run_service(pending=pending)
        self.assertTrue(r['pending_retained']);self.assertFalse(r['closed']);self.assertNotIn('pipe_close',self.pipe.calls)

if __name__=='__main__':unittest.main()
