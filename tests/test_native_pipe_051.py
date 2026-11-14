import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
import runpy
from forex_demo_lab.native_pipe_051 import Session051,PREFIX,records_from_log,parse_record,collect_stopped_record

def record(reason=0,requests=1,valid=True):
    return dict(version='pipe_fixture_051_v1',reason_code=reason,requests=requests,receipt_valid=valid,quote_reads=0,orders=0)

class NativePipe051Tests(unittest.TestCase):
    def setUp(self):self.now=0.;self.s=Session051(True,clock=lambda:self.now)
    def ready(self):self.s.save_baseline();self.s.arm('enabled')
    def test_external_disabled_proof_required(self):
        for bad in (False,None,1):
            with self.assertRaises(ValueError):Session051(bad)
    def test_no_synthetic_disabled_record(self):self.assertEqual(self.s.records,[]);self.assertEqual(self.s.arms,[])
    def test_baseline_save_required(self):
        with self.assertRaises(ValueError):self.s.arm('enabled')
    def test_baseline_ack_once_only(self):
        self.s.save_baseline()
        with self.assertRaises(ValueError):self.s.save_baseline()
    def test_disabled_native_arm_not_allowed(self):
        self.s.save_baseline()
        with self.assertRaises(ValueError):self.s.arm('disabled')
    def test_repeat_cannot_precede_enabled(self):
        self.s.save_baseline()
        with self.assertRaises(ValueError):self.s.arm('repeat')
    def test_collect_requires_log_save(self):
        self.ready()
        with self.assertRaises(ValueError):self.s.collect([record()])
    def test_save_ack_requires_matching_pending_step(self):
        self.ready()
        with self.assertRaises(ValueError):self.s.save_pending('repeat')
    def test_save_ack_cannot_repeat(self):
        self.ready();self.s.save_pending('enabled')
        with self.assertRaises(ValueError):self.s.save_pending('enabled')
    def test_two_native_runs_complete(self):
        self.ready();self.s.save_pending('enabled');self.s.collect([record()])
        self.s.arm('repeat');self.s.save_pending('repeat');self.s.collect([record(20,0,False)])
        self.assertEqual(len(self.s.records),2)
        with self.assertRaises(ValueError):self.s.arm('enabled')
    def test_repeat_rejection_not_second_success(self):
        self.ready();self.s.save_pending('enabled');self.s.collect([record()]);self.s.arm('repeat');self.s.save_pending('repeat')
        with self.assertRaises(ValueError):self.s.collect([record()])
        self.assertEqual(self.s.records[-1],record())
    def test_missing_or_extra_records_stop(self):
        for rows in ([],[record(),record()]):
            s=Session051(True);s.save_baseline();s.arm('enabled');s.save_pending('enabled')
            with self.assertRaises(ValueError):s.collect(rows)
    def test_whole_session_deadline(self):
        self.ready();self.now=900
        with self.assertRaises(ValueError):self.s.save_pending('enabled')
    def test_delayed_file_visibility_and_save_order(self):
        with TemporaryDirectory() as d:
            p=Path(d)/'log';p.write_bytes(b'');self.ready()
            self.assertEqual(records_from_log(p.read_bytes()),[])
            with self.assertRaises(ValueError):self.s.require_saved('enabled')
            p.write_bytes((PREFIX+json.dumps(record())).encode('utf-16-le'));self.s.save_pending('enabled')
            self.assertEqual(self.s.collect(records_from_log(p.read_bytes())),record())
    def test_exact_mebibyte_bound(self):
        self.assertEqual(records_from_log(b'\0'*1048576),[])
        with self.assertRaises(ValueError):records_from_log(b'\0'*1048578)
        root=Path(__file__).resolve().parents[1]
        read=runpy.run_path(str(root/'scripts/runtime-native-pipe-051.py'))['read_append']
        with TemporaryDirectory() as d:
            p=Path(d)/'log';p.write_bytes(b'\0'*1048576)
            self.assertEqual(read(p,0),([],1048576,1048576))
            p.write_bytes(b'\0'*1048578)
            with self.assertRaises(ValueError):read(p,0)
    def test_exact_text_bound(self):
        valid=PREFIX+json.dumps(record());self.assertEqual(parse_record(valid),record())
        with self.assertRaises(ValueError):parse_record(valid+' '*2048)
    def test_closed_schema_types_and_no_identifiers(self):
        for key,value in (('orders',1),('quote_reads',1),('requests',True),('receipt_valid',1),('login',1)):
            r=record();r[key]=value
            with self.assertRaises(ValueError):parse_record(PREFIX+json.dumps(r))
    def test_old_prefix_cannot_count_as_new_phase(self):
        r=record();r['version']='pipe_fixture_049_v1'
        self.assertEqual(records_from_log(('FXDL_PIPE049 '+json.dumps(r)).encode('utf-16-le')),[])
    def test_stopped_read_once_only_no_sdk(self):
        with TemporaryDirectory() as d:
            p=Path(d)/'log';p.write_bytes((PREFIX+json.dumps(record())).encode('utf-16-le'));out=[];attempted=set()
            self.assertTrue(collect_stopped_record(p,0,'enabled',attempted,out.append))
            self.assertFalse(collect_stopped_record(p,0,'enabled',attempted,out.append))
            self.assertEqual(out[0]['records'],[record()]);self.assertEqual(out[0]['sdk_connections'],0)
    def test_clock_reversal(self):
        self.now=2.;self.s.remaining_ms();self.now=1.
        with self.assertRaises(ValueError):self.s.remaining_ms()
