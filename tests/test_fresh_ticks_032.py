import csv
import json
from pathlib import Path
import struct
import tempfile
from types import SimpleNamespace as NS
import unittest

from test_fresh_data_031 import API as ProbeAPI,Clock
from forex_demo_lab.fresh_ticks_032 import START,END,FIELDS,MAX_BYTES,MAX_ROWS,capture


def row(ms=START):
    return dict(time=ms//1000,bid=1.1,ask=1.1001,last=0.,volume=0,
                time_msc=ms,flags=6,volume_real=0.)


class Response:
    def __init__(self,rows):
        self.rows=rows
        formats=('<i8','<f8','<f8','<f8','<u8','<i8','<u4','<f8')
        offsets=(0,8,16,24,32,40,48,52)
        self.dtype=NS(names=FIELDS,hasobject=False,itemsize=60,
            fields={k:(NS(str=f,kind=f[1],itemsize=int(f[2:])),o) for k,f,o in zip(FIELDS,formats,offsets)},
            descr=list(zip(FIELDS,formats)))
        self.shape=(len(rows),)
        self.nbytes=60*len(rows)

    def __len__(self):return len(self.rows)
    def __iter__(self):return iter(self.rows)
    def tobytes(self):return b''.join(struct.pack('<qdddQqId',*(r[k] for k in FIELDS)) for r in self.rows)


class API(ProbeAPI):
    COPY_TICKS_ALL=0
    def __init__(self,response=None):
        super().__init__()
        self.response=Response([row(),row(START+1),row(END)]) if response is None else response
        self.request_args=None
        self.error=(1,'success')

    def copy_ticks_range(self,symbol,start,end,flags):
        self.calls+=1
        self.request_args=(symbol,int(start.timestamp()*1000),int(end.timestamp()*1000),flags)
        if self.on_read:self.on_read(self)
        return self.response

    def last_error(self):return self.error


class FullSampleTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.output=Path(self.temp.name)/'capture'

    def run_capture(self,api=None,clock=None):
        return capture(api or API(),self.output,clock or Clock())

    def test_one_exact_request_and_full_original(self):
        api=API();meta=self.run_capture(api)
        self.assertEqual(api.calls,1)
        self.assertEqual(api.request_args,('EURUSD',START,END,0))
        self.assertEqual(meta['status'],'sample_preserved_and_rows_valid')
        self.assertEqual(meta['audit']['rows'],3)
        self.assertEqual(meta['audit']['last_raw_time_msc'],END)
        self.assertEqual((self.output/'response.bin').read_bytes(),api.response.tobytes())
        with (self.output/'raw.csv').open() as f:
            reader=csv.DictReader(f);self.assertEqual(tuple(reader.fieldnames),FIELDS)
            self.assertEqual(len(list(reader)),3)
        self.assertFalse(meta['fresh_performance_eligible'])
        self.assertFalse(meta['orders_available'])
        self.assertTrue(meta['complete_original_preserved'])
        padded=Response([row()])
        padded.dtype.itemsize=64
        padded.dtype.fields['volume_real']=(padded.dtype.fields['volume_real'][0],56)
        padded.nbytes=64
        padded.tobytes=lambda:struct.pack('<qdddQqI4xd',*(row()[k] for k in FIELDS))
        meta=capture(API(padded),self.output/'padded',Clock())
        self.assertEqual(meta['status'],'sample_preserved_and_rows_valid')
        self.assertEqual(meta['binary_layout']['padding_offsets'],[52,53,54,55])

    def test_real_contest_unknown_rejected_before_request(self):
        for mode in (1,2,True):
            api=API();api.account.trade_mode=mode
            meta=capture(api,self.output/str(mode),Clock())
            self.assertEqual(api.calls,0)
            self.assertEqual(meta['stop_reason'],'actual_account_not_demo')

    def test_disconnect_algo_currency_symbol_rejections(self):
        changes=(lambda a:setattr(a.terminal,'connected',False),lambda a:setattr(a.terminal,'trade_allowed',True),
                 lambda a:setattr(a.account,'currency','EUR'),lambda a:setattr(a.symbol,'visible',False))
        for i,change in enumerate(changes):
            api=API();change(api)
            meta=capture(api,self.output/str(i),Clock())
            self.assertEqual(api.calls,0)
            self.assertEqual(meta['requests'],0)

    def test_account_server_or_mode_change_after_read_discards_payload(self):
        for i,(field,value) in enumerate((('login',123),('server','other'),('trade_mode',1))):
            api=API();api.on_read=lambda a:setattr(a.account,field,value)
            path=self.output/str(i)
            meta=capture(api,path,Clock())
            self.assertEqual(api.calls,1)
            self.assertFalse(meta['complete_original_preserved'])
            self.assertFalse((path/'raw.csv').exists())

    def test_reserved_date_and_wrong_bounds_make_no_request(self):
        api=API();clock=Clock();clock.ms=1793491200000
        self.assertEqual(self.run_capture(api,clock)['stop_reason'],'receipt_outside_declared_date')
        self.assertEqual(api.calls,0)
        with self.assertRaises(ValueError):capture(api,self.output/'wrong',Clock(),START-1,END)

    def test_existing_output_rejects_before_api_or_overwrite(self):
        api=API();self.run_capture(api)
        before=(self.output/'capture.json').read_bytes()
        with self.assertRaises(FileExistsError):self.run_capture(api)
        self.assertEqual(api.calls,1)
        self.assertEqual((self.output/'capture.json').read_bytes(),before)

    def test_none_and_empty_fail_without_retry(self):
        for i,response in enumerate((None,Response([]))):
            api=API();api.response=response
            meta=capture(api,self.output/str(i),Clock())
            self.assertEqual(api.calls,1)
            self.assertEqual(meta['stop_reason'],'api_returned_none' if response is None else 'empty_response')

    def test_api_error_preserves_bounded_rows_and_redacts_text(self):
        api=API();api.error=(-1,'private login password secret')
        meta=self.run_capture(api)
        self.assertEqual(meta['stop_reason'],'api_error_with_preserved_response')
        self.assertTrue(meta['complete_original_preserved'])
        self.assertNotIn('secret',json.dumps(meta))

    def test_schema_and_object_rejection_exports_no_unknown_values(self):
        for i,object_dtype in enumerate((False,True)):
            response=Response([row()])
            response.dtype.names=('login',)+FIELDS[1:]
            response.dtype.hasobject=object_dtype
            api=API(response);path=self.output/str(i)
            meta=capture(api,path,Clock())
            self.assertEqual(meta['stop_reason'],'unsupported_response_schema')
            self.assertFalse((path/'raw.csv').exists())
            self.assertFalse(meta['complete_original_preserved'])

    def test_size_budgets_never_export_a_prefix(self):
        for i,by_rows in enumerate((True,False)):
            response=Response([row()]*(MAX_ROWS+1) if by_rows else [row()])
            if not by_rows:response.nbytes=MAX_BYTES+1
            path=self.output/str(i)
            meta=capture(API(response),path,Clock())
            self.assertEqual(meta['stop_reason'],'row_budget_exceeded' if by_rows else 'response_byte_budget_exceeded')
            self.assertFalse((path/'raw.csv').exists())
            self.assertFalse((path/'response.bin').exists())

    def test_chronology_and_range_failure_keeps_all_original_rows(self):
        rows=[row(START+2),row(START+1),row(END+1)]
        meta=self.run_capture(API(Response(rows)))
        self.assertEqual(meta['stop_reason'],'original_row_validation_failed')
        self.assertEqual(meta['audit']['error_counts'],dict(decreasing_labels=1,outside_request=1))
        self.assertEqual(meta['audit']['rows'],3)
        self.assertTrue(meta['complete_original_preserved'])

    def test_invalid_prices_volume_and_second_agreement_preserved(self):
        rows=[{**row(),'bid':float('nan')},{**row(),'last':-1},{**row(),'time':0},
              {**row(),'bid':2.0},{**row(),'volume_real':float('inf')}]
        meta=self.run_capture(API(Response(rows)))
        self.assertEqual(meta['stop_reason'],'original_row_validation_failed')
        self.assertEqual(meta['audit']['error_counts'],dict(invalid_prices=2,invalid_auxiliary_fields=2,timestamp_mismatch=1))
        self.assertEqual(meta['audit']['rows'],5)

    def test_ties_duplicates_and_gaps_stay_in_original_order(self):
        rows=[row(),row(),{**row(),'ask':1.1002},row(END)]
        meta=self.run_capture(API(Response(rows)))
        self.assertEqual(meta['audit']['same_millisecond_transitions'],2)
        self.assertEqual(meta['audit']['exact_duplicate_transitions'],1)
        self.assertEqual(meta['audit']['maximum_nonnegative_intertick_gap_ms'],END-START)
        self.assertEqual(meta['audit']['rows'],4)

    def test_soft_timeout_preserves_entire_response(self):
        api=API();clock=Clock()
        api.on_read=lambda a:setattr(clock,'ms',clock.ms+61000)
        meta=self.run_capture(api,clock)
        self.assertEqual(meta['stop_reason'],'soft_timeout_with_preserved_response')
        self.assertTrue(meta['complete_original_preserved'])
        self.assertEqual(api.calls,1)

    def test_exception_details_redacted_no_retry(self):
        api=API()
        def fail(a):raise RuntimeError('password secret private login')
        api.on_read=fail
        meta=self.run_capture(api)
        self.assertEqual(meta['stop_reason'],'api_or_runtime_failure_details_redacted')
        self.assertNotIn('secret',json.dumps(meta))
        self.assertEqual(api.calls,1)

    def test_completion_guard_failure_keeps_previously_guarded_original(self):
        api=API()
        def change(a):
            if a.guards==5:a.terminal.connected=False
        api.on_guard=change
        meta=self.run_capture(api)
        self.assertEqual(meta['stop_reason'],'disconnected')
        self.assertTrue(meta['complete_original_preserved'])
