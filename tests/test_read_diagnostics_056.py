import ctypes as C
from ctypes import wintypes as W
import json
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
import unittest

from forex_demo_lab.windows_pipe_047 import PipeRejected, _PENDING, WindowsPipe
from forex_demo_lab.windows_pipe_diagnostics_056 import DiagnosticWindowsPipe056, error_category, duration
from forex_demo_lab.read_diagnostics_056 import *
from forex_demo_lab.capture_budget_047 import Policy, VERSION, PermitRejected
from forex_demo_lab.capture_wire_047 import encode_response

ROOT=Path(__file__).resolve().parents[1]
UTC=1791352800000; BOOT=100000
POLICY=Policy('56000000000000000000000000000001','56'*32) # Synthetic, never reserved/issued.
FRAME=encode_response(dict(version=VERSION,phase=POLICY.phase,policy_sha256=POLICY.digest,
    permission=1,issued_boot_ms=BOOT,expires_boot_ms=BOOT+2000,expires_utc_ms=UTC+2000))

class Kernel:
    """Injected ctypes-shaped calls only; never touches Win32 or MT5."""
    def __init__(self):
        self.error=0;self.submit_error=None;self.completion_error=None
        self.event_error=None;self.close_error=None;self.cancel_error=None
        self.waits=[];self.wait_calls=[];self.cancel_calls=0;self.closed=[]
        self.payload=b'x'*84;self.count=84;self.throw_wait=False
    def get_error(self): return self.error
    def event(self,*a):
        self.error=self.event_error or 0
        return 0 if self.event_error is not None else 123
    def submit(self):
        self.error=self.submit_error or 0
        return self.submit_error is None
    def connect(self,*a): return self.submit()
    def read(self,h,b,n,*a): C.memmove(b,self.payload,min(len(self.payload),n));return self.submit()
    def write(self,*a): return self.submit()
    def result(self,h,o,n,wait):
        C.cast(n,C.POINTER(W.DWORD))[0]=self.count
        self.error=self.completion_error or 0
        return self.completion_error is None
    def wait(self,e,ms):
        self.wait_calls.append(ms)
        if self.throw_wait: raise RuntimeError('private account secret')
        result=self.waits.pop(0) if self.waits else 0
        self.error=6 if result==0xffffffff else 998 # Deliberately overwrite previous error.
        return result
    def cancel(self,*a):
        self.cancel_calls+=1;self.error=self.cancel_error or 0
        return self.cancel_error is None
    def close(self,e):
        self.closed.append(e);self.error=self.close_error or 998
        return self.close_error is None

class WindowsDiagnostics056Tests(unittest.TestCase):
    def setUp(self):
        self.kernel=Kernel();self.ns=0
        def now():self.ns+=1000;return self.ns
        self.pipe=DiagnosticWindowsPipe056(injected_api=self.kernel,now=now)
        self.pending_start=len(_PENDING)
        self.addCleanup(lambda:_PENDING.__delitem__(slice(self.pending_start,None)))
    def read(self):return self.pipe.io(7,'read',size=84)
    def rejected(self,reason,fn=None):
        with self.assertRaisesRegex(PipeRejected,'^'+reason+'$'): (fn or self.read)()
        return self.pipe.last_io
    def test_immediate_read_completion(self):
        self.assertEqual(self.read(),b'x'*84);self.assertEqual(self.pipe.last_io['transferred_bytes'],84)
        self.assertTrue(self.pipe.last_io['event_closed']);self.assertFalse(_PENDING[self.pending_start:])
    def test_pending_completion_is_distinct(self):
        self.kernel.submit_error=997;self.assertEqual(len(self.read()),84)
        self.assertEqual(self.pipe.last_io['events'][1]['category'],'io_pending')
        self.assertEqual(self.kernel.wait_calls,[2000])
    def test_immediate_write_failure_captures_error_before_close(self):
        self.kernel.submit_error=109
        r=self.rejected('io_operation_rejected',lambda:self.pipe.io(7,'write',b'x'*84))
        self.assertEqual(r['events'][1]['category'],'broken_pipe');self.assertIsNone(r['transferred_bytes'])
        self.assertEqual(self.kernel.wait_calls,[])
    def test_whitelist_failure_categories(self):
        cases={5:'access_denied',6:'invalid_handle',87:'invalid_parameter',109:'broken_pipe',
               232:'pipe_closing',233:'pipe_not_connected',234:'more_data',535:'pipe_connected',
               995:'operation_aborted',996:'io_incomplete',997:'io_pending'}
        for code,category in cases.items():self.assertEqual(error_category(code),category)
    def test_unknown_codes_and_messages_redacted(self):
        for x in (None,True,-1,'private',2**40):self.assertEqual(error_category(x),'unknown')
        self.kernel.submit_error=123456;self.rejected('io_operation_rejected')
        text=json.dumps(self.pipe.last_io);self.assertNotIn('123456',text);self.assertNotIn('private',text)
        self.assertEqual(error_category(0),'other')
    def test_pending_completion_failure(self):
        self.kernel.submit_error=997;self.kernel.completion_error=109
        r=self.rejected('io_completion_rejected');self.assertEqual(r['events'][-2]['category'],'broken_pipe')
        self.assertFalse(r['pending_retained']);self.assertTrue(r['event_closed'])
    def test_timeout_cancel_aborted_drains(self):
        self.kernel.submit_error=997;self.kernel.waits=[258,0];self.kernel.completion_error=995
        r=self.rejected('io_deadline_exceeded');self.assertFalse(r['pending_retained'])
        self.assertEqual(self.kernel.wait_calls,[2000,1000]);self.assertEqual(self.kernel.cancel_calls,1)
    def test_timeout_racing_success_still_rejected(self):
        self.kernel.submit_error=997;self.kernel.waits=[258,0]
        r=self.rejected('io_deadline_exceeded');self.assertIsNone(r['transferred_bytes'])
    def test_cancel_failure_still_waits_for_completion(self):
        self.kernel.submit_error=997;self.kernel.waits=[258,0];self.kernel.cancel_error=6
        r=self.rejected('io_deadline_exceeded');self.assertEqual(r['events'][3]['category'],'invalid_handle')
        self.assertTrue(r['event_closed'])
    def test_undrained_cancel_retains_all_memory_and_handle(self):
        self.kernel.submit_error=997;self.kernel.waits=[258,258]
        r=self.rejected('cancellation_not_drained');self.assertTrue(r['pending_retained'])
        o,e,b,h=_PENDING[-1];self.assertEqual((e,h),(123,7));self.assertEqual(o.hEvent,123)
        self.assertEqual(len(b),84);self.assertEqual(self.kernel.closed,[])
    def test_wait_failure_categorized_and_drained(self):
        self.kernel.submit_error=997;self.kernel.waits=[0xffffffff,0]
        r=self.rejected('io_wait_rejected');self.assertEqual(r['events'][2]['category'],'invalid_handle')
    def test_wait_failure_undrained_retains(self):
        self.kernel.submit_error=997;self.kernel.waits=[0xffffffff,0xffffffff]
        self.assertTrue(self.rejected('cancellation_not_drained')['pending_retained'])
    def test_incomplete_result_retains(self):
        self.kernel.submit_error=997;self.kernel.completion_error=996
        self.assertTrue(self.rejected('io_completion_rejected')['pending_retained'])
    def test_unknown_completion_does_not_prove_cancellation(self):
        self.kernel.submit_error=997;self.kernel.waits=[258,0];self.kernel.completion_error=12345
        self.assertTrue(self.rejected('cancellation_not_drained')['pending_retained'])
    def test_unexpected_exception_after_pending_retains_and_redacts(self):
        self.kernel.submit_error=997;self.kernel.throw_wait=True
        r=self.rejected('unexpected_failure');self.assertTrue(r['pending_retained'])
        self.assertNotIn('secret',json.dumps(r))
    def test_upstream_pipe_exception_cannot_export_private_reason(self):
        def submit(*args):raise PipeRejected('private account identifier')
        self.kernel.read=submit;self.pipe.read=submit
        r=self.rejected('unexpected_failure');self.assertNotIn('identifier',json.dumps(r))
    def test_event_creation_failure(self):
        self.kernel.event_error=5;r=self.rejected('event_create_rejected')
        self.assertEqual(r['events'],[dict(stage='event_create',category='access_denied')]);self.assertEqual(self.kernel.closed,[])
    def test_close_failure_reported(self):
        self.kernel.close_error=6;self.read();self.assertFalse(self.pipe.last_io['event_closed'])
        self.assertEqual(self.pipe.last_io['events'][-1]['category'],'invalid_handle')
    def test_short_write_rejected(self):
        self.kernel.count=83;self.rejected('short_write_rejected',lambda:self.pipe.io(7,'write',b'x'*84))
    def test_excess_read_count_rejected(self):
        self.kernel.count=85;self.rejected('read_count_rejected')
    def test_connect_already_connected(self):
        self.kernel.submit_error=535;self.assertEqual(self.pipe.io(7,'connect'),b'')
        self.assertEqual(self.pipe.last_io['events'][1]['category'],'pipe_connected')
    def test_limits_reject_before_allocating(self):
        for timeout in (0,2001,True,2.0):
            with self.assertRaises(PipeRejected):self.pipe.io(7,'read',size=84,timeout_ms=timeout)
        for size in (0,129,True):
            with self.assertRaises(PipeRejected):self.pipe.io(7,'read',size=size)
        for data in (b'',b'x'*129,'private'):
            with self.assertRaises(PipeRejected):self.pipe.io(7,'write',data)
        self.assertIsNone(self.pipe.last_io)
    def test_duration_bounds_and_reversal(self):
        self.assertEqual(duration(0,3000000000),(3000000,'measured'))
        self.assertEqual(duration(0,3000001000),(None,'over_bound'))
        for a,b in ((2,1),(-1,0),(True,3)):
            self.assertEqual(duration(a,b),(None,'clock_invalid'))
    def test_security_identity_inherited_without_cache(self):
        for name in ('identity','peer','server','client'):
            self.assertIs(getattr(DiagnosticWindowsPipe056,name),getattr(WindowsPipe,name))

class FramingDiagnostics056Tests(unittest.TestCase):
    def test_single_read_sequence_delays_disconnect_and_no_retry(self):
        for requested in (84,85):
            for payload,error,delay in ((FRAME,0,100),(b'',5015,2000000),
                    (FRAME[:20],0,10),(FRAME+b'x',0,10),(FRAME,0,3197324)):
                ticks=iter((0,delay));calls=[]
                def read(n):calls.append(n);return payload[:n],error
                r=modeled_read(read,requested,lambda:next(ticks))
                self.assertEqual(calls,[requested]);self.assertEqual(r['elapsed_us'],delay)
                self.assertEqual(r['frame_accepted'],len(payload[:requested])==84 and error==0)
    def test_modeled_read_exception_redacted(self):
        def read(n):raise RuntimeError('private account identifier')
        with self.assertRaisesRegex(PipeRejected,'^read_failed_details_redacted$'):
            modeled_read(read,84,lambda:0)
    def test_exact_and_oversized_request_models(self):
        for n in (84,85):self.assertEqual(frame_candidate(FRAME,n),FRAME)
    def test_zero_partial_and_extra_rejected_without_retry(self):
        for raw in (b'',FRAME[:1],FRAME[:83],FRAME+b'x',FRAME*2):
            for n in (84,85):
                with self.assertRaises(PipeRejected):frame_candidate(raw,n)
    def test_count_change_cannot_detect_unread_suffix(self):
        self.assertEqual(frame_candidate((FRAME+b'x')[:84],84),FRAME)
        with self.assertRaises(PipeRejected):frame_candidate((FRAME+b'x')[:85],85)
    def test_read_error_even_with_full_frame_rejected(self):
        for error in (5007,5010,5011,5015,12345,-1,None):
            with self.assertRaises(PipeRejected):frame_candidate(FRAME,84,error)
    def test_native_strict_whitelist(self):
        for code,cat in ((0,0),(5007,2),(5010,3),(5011,4),(5015,5),(12345,6),(-1,7),(True,7)):
            self.assertEqual(native_error(code),cat)
    def test_native_read_measurement_before_close_model(self):
        r=native_read_report(0,5015,10,3000010)
        self.assertEqual(r['elapsed_us'],3000000);self.assertEqual(r['error_category'],5)
        self.assertNotIn('5015',json.dumps(r))
    def test_native_duration_bounds_do_not_hide_overrun(self):
        self.assertEqual(native_read_report(84,0,0,900000000)['elapsed_us'],900000000)
        self.assertEqual(native_read_report(0,0,0,900000001)['timing'],'over_bound')
        self.assertEqual(native_read_report(0,0,20,10)['timing'],'clock_invalid')
        with self.assertRaises(PipeRejected):native_read_report(86,0,0,1)
    def test_delayed_valid_reply_within_receipt(self):
        a=consumption_ack(FRAME,POLICY,UTC+1999,BOOT+1999,lambda:True)
        self.assertTrue(validate_ack(a,FRAME,POLICY,UTC+1999,BOOT+1999,lambda:True,0,1999000000))
    def test_delayed_reply_receipt_expired(self):
        with self.assertRaises(PermitRejected):consumption_ack(FRAME,POLICY,UTC+2000,BOOT+2000,lambda:True)
    def test_ack_exact_frame_binding(self):
        a=consumption_ack(FRAME,POLICY,UTC,BOOT,lambda:True)
        for raw in (b'',a[:-1],a+b'x',a[:-1]+bytes([a[-1]^1])):
            with self.assertRaises(PipeRejected):validate_ack(raw,FRAME,POLICY,UTC,BOOT,lambda:True,0,1)
    def test_ack_wrong_phase_and_policy(self):
        for p in (Policy('57'*16,POLICY.digest),Policy(POLICY.phase,'57'*32)):
            with self.assertRaises(PermitRejected):consumption_ack(FRAME,p,UTC,BOOT,lambda:True)
    def test_ack_guard_recheck_and_privacy(self):
        a=consumption_ack(FRAME,POLICY,UTC,BOOT,lambda:True)
        def fail():raise RuntimeError('private login')
        for guard in (lambda:False,fail):
            with self.assertRaisesRegex(PermitRejected,'^private_account_or_instrument_guard_rejected$'):
                validate_ack(a,FRAME,POLICY,UTC,BOOT,guard,0,1)
    def test_ack_deadline_cannot_be_extended(self):
        a=consumption_ack(FRAME,POLICY,UTC,BOOT,lambda:True)
        for n in (-1,2000000000,3000000000,True):
            with self.assertRaises(PipeRejected):validate_ack(a,FRAME,POLICY,UTC,BOOT,lambda:True,0,n)
    def test_no_ack_on_missing_or_disconnected_reply(self):
        for raw in (b'',FRAME[:83]):
            with self.assertRaises(PermitRejected):consumption_ack(raw,POLICY,UTC,BOOT,lambda:True)
    def test_actual_pure_header_python_differential(self):
        codes=(-1,0,5007,5010,5011,5015,9999)
        times=((0,0),(10,11),(20,10),(0,2000000),(0,900000000),(0,900000001))
        cases=[(c,a,b) for c in codes for a,b in times]
        with TemporaryDirectory() as tmp:
            exe=Path(tmp)/'read056'
            subprocess.run(['g++','-std=c++17',str(ROOT/'mt5/Tests/CaptureReadDiagnostics056.cpp'),'-o',str(exe)],check=True,capture_output=True)
            p=subprocess.run([str(exe)],input=''.join(f'{c} {a} {b}\n' for c,a,b in cases),text=True,capture_output=True,check=True)
        rows=[tuple(map(int,line.split())) for line in p.stdout.splitlines()]
        expected=[]
        for c,a,b in cases:
            d=duration(a*1000,b*1000,900000000)[0];expected.append((native_error(c),-1 if d is None else d))
        self.assertEqual(rows,expected);self.assertEqual(len(rows),42)
    def test_wrapper_keeps_read_error_and_timing_before_close(self):
        s=(ROOT/'mt5/Scripts/CaptureReadDiagnostics056.mqh').read_text()
        self.assertLess(s.index('ResetLastError();'),s.index('FileReadArray('))
        self.assertLess(s.index('int error=GetLastError();'),s.index('ulong end=GetMicrosecondCount();'))
        self.assertNotIn('FileClose(',s);self.assertNotIn('FlushFileBuffers',s)
