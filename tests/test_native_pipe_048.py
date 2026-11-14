import io
import json
import unittest
from forex_demo_lab.native_pipe_048 import Session048, PREFIX, parse_record, records_from_log, require_interactive, date_guard

def record(reason=17,requests=0,valid=False):
    return dict(version='pipe_fixture_047_v1',reason_code=reason,requests=requests,receipt_valid=valid,quote_reads=0,orders=0)

class NativePipe048Tests(unittest.TestCase):
    def setUp(self):self.now=0.;self.s=Session048(lambda:self.now)
    def test_complete_sequence(self):
        for step,r in zip(('disabled','enabled','repeat'),(record(),record(0,1,True),record(20))):
            self.s.arm(step);self.s.collect([r])
        with self.assertRaises(ValueError):self.s.arm('repeat')
    def test_enabled_needs_disabled_proof(self):
        with self.assertRaises(ValueError):self.s.arm('enabled')
    def test_pending_arm_cannot_repeat(self):
        self.s.arm('disabled')
        with self.assertRaises(ValueError):self.s.arm('disabled')
    def test_collect_requires_arm(self):
        with self.assertRaises(ValueError):self.s.collect([record()])
    def test_extra_records_stop(self):
        self.s.arm('disabled')
        with self.assertRaises(ValueError):self.s.collect([record(),record()])
    def test_missing_record_stop(self):
        self.s.arm('disabled')
        with self.assertRaises(ValueError):self.s.collect([])
    def test_unexpected_success_retained(self):
        self.s.arm('disabled')
        with self.assertRaises(ValueError):self.s.collect([record(0,1,True)])
        self.assertEqual(self.s.records,[record(0,1,True)])
    def test_whole_deadline(self):
        self.now=899.9;self.assertLessEqual(self.s.remaining_ms(),100)
        self.now=900
        with self.assertRaises(ValueError):self.s.arm('disabled')
    def test_clock_reversal(self):
        self.now=10;self.s.remaining_ms();self.now=9
        with self.assertRaises(ValueError):self.s.remaining_ms()
    def test_noninteractive_preflight(self):
        with self.assertRaises(ValueError):require_interactive(io.StringIO())
    def test_closed_schema_and_types(self):
        for key,value in [('orders',1),('quote_reads',1),('requests',True),('reason_code',True),('receipt_valid',1),('version','other')]:
            r=record();r[key]=value
            with self.assertRaises(ValueError):parse_record(PREFIX+json.dumps(r))
        r=record();r['login']='private'
        with self.assertRaises(ValueError):parse_record(PREFIX+json.dumps(r))
    def test_duplicate_keys_reject(self):
        s=PREFIX+json.dumps(record()).replace('"orders": 0','"orders": 0, "orders": 0')
        with self.assertRaises(ValueError):parse_record(s)
    def test_filtered_log(self):
        raw=('unrelated private content\r\n12:00 '+PREFIX+json.dumps(record())+'\r\n').encode('utf-16-le')
        self.assertEqual(records_from_log(raw),[record()])
    def test_partial_and_oversize_log(self):
        for raw in (b'x',b'\0'*1048578):
            with self.assertRaises(ValueError):records_from_log(raw)
    def test_ambiguous_log(self):
        with self.assertRaises(ValueError):records_from_log((PREFIX+PREFIX+json.dumps(record())).encode('utf-16-le'))
    def test_fixed_date(self):
        date_guard(1791331200000)
        with self.assertRaises(ValueError):date_guard(1791244800000)
