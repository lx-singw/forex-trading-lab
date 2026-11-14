import csv
import json
import runpy
from pathlib import Path
import struct
import tempfile
from types import SimpleNamespace as NS
import unittest

from test_fresh_data_031 import API as BaseAPI, Clock
from test_fresh_ticks_032 import Response, row
from forex_demo_lab.fresh_replication_035 import START,END,BAR_FIELDS,MAX_TICKS,MAX_BARS,MAX_BYTES,capture,reserve_output


def bar():
    return dict(time=START//1000,open=1.1,high=1.1,low=1.1,close=1.1,tick_volume=2,spread=10,real_volume=0)


class Bars(Response):
    def __init__(self,rows):
        self.rows=rows
        formats=('<i8','<f8','<f8','<f8','<f8','<u8','<i4','<u8')
        offsets=(0,8,16,24,32,40,48,52)
        self.dtype=NS(names=BAR_FIELDS,hasobject=False,itemsize=60,
            fields={k:(NS(str=f,kind=f[1],itemsize=int(f[2:])),o) for k,f,o in zip(BAR_FIELDS,formats,offsets)},
            descr=list(zip(BAR_FIELDS,formats)))
        self.shape=(len(rows),); self.nbytes=60*len(rows)
    def tobytes(self):return b''.join(struct.pack('<qddddQiQ',*(r[k] for k in BAR_FIELDS)) for r in self.rows)


class API(BaseAPI):
    COPY_TICKS_ALL=0
    TIMEFRAME_H1=16385
    def __init__(self):
        super().__init__(); self.tick.time_msc=END+1
        self.ticks=Response([row(START),row(END-1),row(END)])
        self.bars=Bars([{**bar(),'time':START//1000+3600*i} for i in range(4)]); self.arguments=[]; self.error=(1,'success')
    def got(self,kind,result,args):
        self.arguments.append((kind,*args)); self.calls+=1
        if self.on_read:self.on_read(self)
        return result
    def symbol_info_tick(self,name):return self.got('horizon',self.tick,(name,))
    def copy_ticks_range(self,symbol,start,end,flags):
        return self.got('ticks',self.ticks,(symbol,int(start.timestamp()*1000),int(end.timestamp()*1000),flags))
    def copy_rates_range(self,symbol,tf,start,end):
        return self.got('bars',self.bars,(symbol,tf,int(start.timestamp()),int(end.timestamp())))
    def last_error(self):return self.error


class ReplicationCollectorTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.output=Path(self.temp.name)/'capture'
    def run_capture(self,api=None,clock=None):return capture(api or API(),self.output,clock or Clock())

    def test_exact_three_requests_preserve_every_tick_and_bar_field(self):
        api=API();meta=self.run_capture(api)
        self.assertEqual(meta['status'],'four_source_hours_originals_preserved_and_rows_valid')
        self.assertEqual(api.arguments,[('horizon','EURUSD'),('ticks','EURUSD',START,END,0),
                                       ('bars','EURUSD',16385,START//1000,END//1000-1)])
        for kind,response in (('ticks',api.ticks),('bars',api.bars)):
            self.assertEqual((self.output/(kind+'.bin')).read_bytes(),response.tobytes())
            with (self.output/(kind+'.csv')).open() as f:
                reader=csv.DictReader(f)
                self.assertEqual(tuple(reader.fieldnames),tuple(response.dtype.names))
                rows=list(reader)
            self.assertEqual(len(rows),len(response))
            for raw,written in zip(response.rows,rows):
                for k,v in raw.items():self.assertEqual(float(written[k]),v)
        for key in ('orders_available','annual_eligible','fresh_performance_eligible','source_clock_interpreted_as_utc'):
            self.assertFalse(meta[key])

    def test_real_contest_unknown_boolean_make_no_requests(self):
        for i,mode in enumerate((1,2,7,True)):
            api=API();api.account.trade_mode=mode
            meta=capture(api,self.output/str(i),Clock())
            self.assertEqual(api.calls,0);self.assertEqual(meta['stop_reason'],'actual_account_not_demo')

    def test_algo_disconnect_currency_and_symbol_guards(self):
        changes=(lambda a:setattr(a.terminal,'trade_allowed',True),lambda a:setattr(a.terminal,'connected',False),
                 lambda a:setattr(a.account,'currency','EUR'),lambda a:setattr(a.symbol,'visible',False))
        for i,change in enumerate(changes):
            api=API();change(api);capture(api,self.output/str(i),Clock());self.assertEqual(api.calls,0)

    def test_identity_or_mode_switch_at_each_read_stops_later_calls(self):
        for stage in (1,2,3):
            for field,value in (('login',123),('server','changed'),('trade_mode',1)):
                api=API();api.on_read=lambda a:setattr(a.account,field,value) if a.calls==stage else None
                path=self.output/(str(stage)+field)
                meta=capture(api,path,Clock());self.assertEqual(api.calls,stage)
                self.assertNotEqual(meta['status'],'four_source_hours_originals_preserved_and_rows_valid')
                if stage==2:self.assertFalse((path/'ticks.bin').exists())
                if stage==3:self.assertTrue((path/'ticks.bin').exists());self.assertFalse((path/'bars.bin').exists())

    def test_expired_or_reserved_date_and_wrong_bounds_no_call(self):
        api=API();clock=Clock();clock.ms=1793491200000
        meta=self.run_capture(api,clock);self.assertEqual(api.calls,0)
        self.assertEqual(meta['stop_reason'],'receipt_outside_declared_date')
        with self.assertRaises(ValueError):capture(api,self.output/'wrong',Clock(),START-1,END)

    def test_horizon_must_be_strictly_after_hour_and_recent(self):
        for i,stamp in enumerate((END,END-1,END+86400000)):
            api=API();api.tick.time_msc=stamp
            meta=capture(api,self.output/str(i),Clock());self.assertEqual(api.calls,1)
            self.assertNotEqual(meta['status'],'four_source_hours_originals_preserved_and_rows_valid')

    def test_invalid_horizon_prices_and_none_stop_history(self):
        for i,quote in enumerate((None,NS(time_msc=END+1,bid=float('nan'),ask=1.2))):
            api=API();api.tick=quote;capture(api,self.output/str(i),Clock());self.assertEqual(api.calls,1)

    def test_sdk_error_at_each_stage_never_retries(self):
        for stage in (1,2,3):
            api=API();api.on_read=lambda a:setattr(a,'error',(-1,'private password')) if a.calls==stage else None
            meta=capture(api,self.output/str(stage),Clock());self.assertEqual(api.calls,stage)
            self.assertNotIn('password',json.dumps(meta))
            if stage>1:self.assertTrue(meta['reads'][-1]['complete_original_preserved'])

    def test_none_and_empty_history_stop_at_affected_read(self):
        for stage,kind in ((2,'ticks'),(3,'bars')):
            for i,response in enumerate((None,Response([]) if kind=='ticks' else Bars([]))):
                api=API();setattr(api,kind,response)
                meta=capture(api,self.output/(kind+str(i)),Clock());self.assertEqual(api.calls,stage)
                self.assertEqual(meta['stop_reason'],'api_returned_none' if response is None else 'empty_response')

    def test_soft_timeout_preserves_ticks_and_prevents_bar_request(self):
        api=API();clock=Clock()
        api.on_read=lambda a:setattr(clock,'ms',clock.ms+61000) if a.calls==2 else None
        meta=self.run_capture(api,clock);self.assertEqual(api.calls,2)
        self.assertEqual(meta['stop_reason'],'soft_timeout_with_preserved_response')
        self.assertTrue((self.output/'ticks.bin').exists());self.assertFalse((self.output/'bars.bin').exists())

    def test_two_history_calls_allow_exact_combined_120_second_limit(self):
        api=API();clock=Clock()
        api.on_read=lambda a:setattr(clock,'ms',clock.ms+59999) if a.calls>1 else None
        meta=self.run_capture(api,clock)
        self.assertEqual(meta['history_elapsed_ns'],120000000000)
        self.assertEqual(meta['status'],'four_source_hours_originals_preserved_and_rows_valid')

    def test_clock_reversal_and_date_change_stop_later_reads(self):
        for i,delta in enumerate((-1000,86400000)):
            api=API();clock=Clock();api.on_read=lambda a:setattr(clock,'ms',clock.ms+delta) if a.calls==2 else None
            meta=capture(api,self.output/str(i),clock);self.assertEqual(api.calls,2)
            self.assertFalse(meta['reads'][-1]['complete_original_preserved'])

    def test_size_limits_export_no_prefix(self):
        for kind,limit in (('ticks',MAX_TICKS),('bars',MAX_BARS)):
            api=API();response=Response([row(START)]*(limit+1)) if kind=='ticks' else Bars([bar()]*(limit+1))
            setattr(api,kind,response);path=self.output/kind
            meta=capture(api,path,Clock());self.assertEqual(meta['stop_reason'],'row_budget_exceeded')
            self.assertFalse((path/(kind+'.bin')).exists())
        api=API();api.ticks.nbytes=MAX_BYTES+1
        meta=capture(api,self.output/'bytes',Clock());self.assertEqual(meta['stop_reason'],'response_byte_budget_exceeded')

    def test_schema_objects_and_nonzero_padding_reject_export(self):
        for i,kind in enumerate(('ticks','bars')):
            api=API();response=getattr(api,kind);response.dtype.names=('secret',)+response.dtype.names[1:]
            meta=capture(api,self.output/str(i),Clock());self.assertEqual(meta['stop_reason'],'unsupported_response_schema')
            self.assertFalse((self.output/str(i)/(kind+'.csv')).exists())
        api=API();api.ticks.dtype.hasobject=True
        self.assertEqual(capture(api,self.output/'object',Clock())['stop_reason'],'unsupported_response_schema')
        api=API();api.bars=Bars([bar()]);r=api.bars;r.dtype.itemsize=64;r.dtype.fields['real_volume']=(r.dtype.fields['real_volume'][0],56);r.nbytes=64
        r.tobytes=lambda:struct.pack('<qddddQi4sQ',*(bar()[k] for k in BAR_FIELDS[:-1]),b'xxxx',0)
        self.assertEqual(capture(api,self.output/'padding',Clock())['stop_reason'],'nonzero_response_padding_not_exported')

    def test_invalid_bounded_ticks_all_preserved_in_order(self):
        api=API();api.ticks=Response([row(START+1),row(START),row(END+1),{**row(START),'bid':float('nan')}])
        meta=self.run_capture(api);self.assertEqual(api.calls,2)
        self.assertEqual(meta['stop_reason'],'original_row_validation_failed')
        self.assertEqual(meta['reads'][1]['returned_rows'],4);self.assertTrue((self.output/'ticks.bin').exists())

    def test_boundary_ties_and_duplicates_preserved(self):
        api=API();api.ticks=Response([row(START),row(START),row(END-1),row(END)])
        meta=self.run_capture(api);audit=meta['reads'][1]['audit']
        self.assertEqual(audit['rows'],4);self.assertEqual(audit['same_millisecond_transitions'],1)
        self.assertEqual(audit['exact_duplicate_transitions'],1);self.assertEqual(audit['last_raw_time_msc'],END)

    def test_wrong_bar_label_count_or_prices_preserved_as_failures(self):
        for i,rows in enumerate(([{**bar(),'time':START//1000+1}],[bar(),bar()],[{**bar(),'time':START//1000+3600*j,'low':2.} for j in range(4)])):
            api=API();api.bars=Bars(rows);path=self.output/str(i)
            meta=capture(api,path,Clock());self.assertEqual(api.calls,3)
            self.assertEqual(meta['stop_reason'],'original_row_validation_failed');self.assertTrue((path/'bars.bin').exists())

    def test_immutable_outputs_and_owned_reservation(self):
        api=API();self.run_capture(api);before=(self.output/'capture.json').read_bytes()
        with self.assertRaises(FileExistsError):self.run_capture(api)
        self.assertEqual(api.calls,3);self.assertEqual((self.output/'capture.json').read_bytes(),before)
        path=self.output/'prepared';reserve_output(path);(path/'foreign').write_text('preserve')
        with self.assertRaises(ValueError):capture(api,path,Clock(),prepared=True)
        self.assertEqual(api.calls,3)

    def test_exceptions_redacted_and_preserved_prior_tick_original(self):
        api=API()
        def fail(a):
            if a.calls==3:raise RuntimeError('private password')
        api.on_read=fail;meta=self.run_capture(api)
        self.assertEqual(api.calls,3);self.assertTrue((self.output/'ticks.bin').exists())
        self.assertNotIn('password',json.dumps(meta));self.assertEqual(meta['stop_reason'],'api_or_runtime_failure_details_redacted')

    def test_completion_identity_failure_keeps_guarded_originals(self):
        api=API()
        def change(a):
            if a.guards==11:a.account.server='changed'
        api.on_guard=change;meta=self.run_capture(api)
        self.assertEqual(api.calls,3);self.assertTrue((self.output/'bars.bin').exists())
        self.assertNotEqual(meta['status'],'four_source_hours_originals_preserved_and_rows_valid')

    def test_between_read_clock_reversal_prevents_next_native_call(self):
        api=API();clock=Clock();clock.ms+=10000;count=0
        def reversing():
            nonlocal count
            count+=1
            if count==5:clock.ms-=1000
            return clock()
        meta=self.run_capture(api,reversing)
        self.assertEqual(api.calls,1)
        self.assertEqual(meta['stop_reason'],'receipt_clock_reversed_between_reads')


CHECK=runpy.run_path(str(Path(__file__).resolve().parents[1]/'scripts/check-fresh-replication-035.py'))
from forex_demo_lab.replication_analysis_035 import analyze


class ReplicationAnalysisTests(unittest.TestCase):
    def test_cross_hour_predecessor_is_retained_not_invented(self):
        rows=[row(START),row(START+3600000)]
        bars=[{**bar(),'time':START//1000+3600*i,'tick_volume':1} for i in range(4)]
        result=analyze(rows,bars,rows)
        self.assertEqual(result['hours'][0]['first_row_without_predecessor_indices'],[0])
        self.assertEqual(result['hours'][1]['first_row_without_predecessor_indices'],[])
        self.assertEqual(result['hours'][1]['bid_value_change_transitions'],0)
        self.assertEqual(result['hours'][1]['fixed_definition_comparisons'][5]['events'],0)
        self.assertEqual(result['flag_value_disagreements'][0]['predecessor_original_row_index'],0)

    def test_all_fixed_definitions_boundaries_and_independent_reconstruction(self):
        rows=[row(START),row(START),{**row(START+3600000),'bid':1.09},row(END)]
        bars=[{**bar(),'time':START//1000+3600*i} for i in range(4)]
        result=analyze(rows,bars,[row(START)])
        self.assertEqual(result,CHECK['reconstruct'](rows,bars,[row(START)]))
        self.assertEqual(result['ambiguous_witnesses'],1)
        self.assertEqual(result['upper_boundary_row_indices'],[3])
        self.assertEqual(result['hours'][0]['exact_close_boundary_row_indices'],[2])
        self.assertEqual(result['hours'][1]['exact_open_boundary_row_indices'],[2])
        self.assertEqual(result['hours'][0]['hour_event_rows'],2)
        self.assertEqual(len(result['hours'][0]['fixed_definition_comparisons']),7)

    def test_four_hour_relative_hypothesis_can_pass_or_fail_without_mask_search(self):
        rows=[row(START+3600000*i) for i in range(4)]
        bars=[{**bar(),'time':START//1000+3600*i,'tick_volume':1} for i in range(4)]
        result=analyze(rows,bars,rows)
        self.assertTrue(result['all_four_relative_hypotheses_passed'])
        self.assertEqual(result['witnesses_matched'],4)
        bars[1]['tick_volume']=2
        result=analyze(rows,bars,rows)
        self.assertFalse(result['all_four_relative_hypotheses_passed'])
        self.assertEqual([h['relative_bid_price_count_hypothesis_passed'] for h in result['hours']],[True,False,True,True])
        self.assertFalse(result['prior_033_diagnostic_passed']);self.assertFalse(result['fresh_performance_eligible'])

    def test_independent_binary_csv_mutation_detection_and_four_bar_order(self):
        from test_fresh_flags_034 import fixture
        from forex_demo_lab.replication_analysis_035 import original
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp);meta=fixture(path,[row(START)])
            self.assertEqual(len(CHECK['decode'](path,'ticks',meta)),1)
            self.assertEqual(original(path,'ticks',meta),[row(START)])
            text=(path/'ticks.csv').read_text().replace('1.1001','1.1002');(path/'ticks.csv').write_text(text)
            import hashlib
            meta.update(csv_sha256=hashlib.sha256((path/'ticks.csv').read_bytes()).hexdigest())
            with self.assertRaises(AssertionError):CHECK['decode'](path,'ticks',meta)
            with self.assertRaises(ValueError):original(path,'ticks',meta)
            meta=fixture(path,[{**row(START),'bid':float('nan')}])
            self.assertEqual(len(original(path,'ticks',meta)),1)
            self.assertEqual(len(CHECK['decode'](path,'ticks',meta)),1)
        bars=[{**bar(),'time':START//1000+3600*i} for i in range(4)]
        self.assertFalse(CHECK['bars_audit'](bars)['errors'])
        self.assertIn('unexpected_bar_open_labels_or_order',CHECK['bars_audit'](list(reversed(bars)))['errors'])
