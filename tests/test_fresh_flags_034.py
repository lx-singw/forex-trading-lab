import ast
import csv
import hashlib
import io
import json
from pathlib import Path
import runpy
import tempfile
import unittest

from test_fresh_ticks_032 import Response,row
from forex_demo_lab.fresh_flags_034 import START,END,FIELDS,FLAGS,DEFINITIONS,analyze,original

ROOT=Path(__file__).resolve().parents[1]
CHECK=runpy.run_path(str(ROOT/'scripts/check-fresh-flags-034.py'))


def tick(ms=START,bid=1.1,ask=1.1001,flags=6):return {**row(ms),'bid':bid,'ask':ask,'flags':flags}
def bar(volume=1):return dict(time=START//1000,open=1.1,high=1.1,low=1.1,close=1.1,tick_volume=volume,spread=0,real_volume=0)


def fixture(path,rows):
    response=Response(rows);binary=response.tobytes()
    text=io.StringIO();writer=csv.DictWriter(text,fieldnames=FIELDS,lineterminator='\n');writer.writeheader();writer.writerows(rows)
    encoded=text.getvalue().encode();(path/'ticks.bin').write_bytes(binary);(path/'ticks.csv').write_bytes(encoded)
    return dict(binary_sha256=hashlib.sha256(binary).hexdigest(),response_sha256=hashlib.sha256(binary).hexdigest(),
        csv_sha256=hashlib.sha256(encoded).hexdigest(),csv_bytes=len(encoded),returned_rows=len(rows),response_bytes=len(binary),
        binary_layout=dict(itemsize=60,fields={k:dict(format=d.str,offset=o,size=d.itemsize) for k,(d,o) in response.dtype.fields.items()},padding_offsets=[]))


class OfflineFlagsTests(unittest.TestCase):
    def test_fixed_masks_and_categories(self):
        r=analyze([tick(START+i,flags=f) for i,f in enumerate((2,4,6,0))],[bar(2)],[])
        self.assertEqual(FLAGS,dict(BID=2,ASK=4,LAST=8,VOLUME=16,BUY=32,SELL=64))
        self.assertEqual(r['category_counts'],dict(bid_flags=2,ask_flags=2,both_flags=1,neither_flag=1))
        self.assertEqual(tuple(c['definition'] for c in r['fixed_definition_comparisons']),DEFINITIONS)

    def test_unknown_mask_retained_uninterpreted(self):
        r=analyze([tick(flags=1026),tick(START+1,flags=1030),tick(START+2,flags=128)],[bar()],[])
        self.assertEqual(r['known_mask_histogram'],{0:1,2:1,6:1})
        self.assertEqual(r['remaining_mask_histogram'],{128:1,1024:2});self.assertFalse(r['unknown_bits_interpreted'])

    def test_first_row_has_no_invented_predecessor(self):
        r=analyze([tick(flags=0)],[bar()],[])
        self.assertEqual(r['first_row_without_predecessor_indices'],[0]);self.assertEqual(r['disagreement_rows'],0)
        self.assertEqual(r['bid_value_change_transitions'],0)
        c={x['definition']:x for x in r['fixed_definition_comparisons']}
        self.assertEqual(c['bid_value_change_with_first']['events'],1)

    def test_flag_without_value_change_records_all_identities(self):
        rows=[tick(),tick(START+1)]
        r=analyze(rows,[bar(2)],rows)
        self.assertEqual(r['bid_disagreement_rows'],1);self.assertEqual(r['ask_disagreement_rows'],1)
        d=r['flag_value_disagreements'][0]
        self.assertEqual(d['original_row_index'],1);self.assertEqual(d['predecessor_original_row_index'],0)
        self.assertEqual(d['original_record'],rows[1]);self.assertEqual(d['predecessor_record'],rows[0])

    def test_value_change_without_flag_is_also_reported(self):
        r=analyze([tick(),tick(START+1,bid=1.11,ask=1.12,flags=0)],[bar()],[])
        self.assertEqual(r['flag_value_disagreements'][0]['mismatched_fields'],['bid','ask'])
        self.assertTrue(r['flag_value_disagreements'][0]['bid_value_changed'])
        self.assertFalse(r['flag_value_disagreements'][0]['bid_flag'])

    def test_same_millisecond_order_is_not_collapsed(self):
        rows=[tick(),tick(bid=1.09,flags=2),tick(flags=0)]
        r=analyze(rows,[bar()],[])
        self.assertEqual(r['source_rows'],3);self.assertEqual(r['same_millisecond_disagreement_rows'],1)
        self.assertEqual(r['fixed_definition_comparisons'][0]['original_row_indices'],[0,1,2])

    def test_exact_duplicates_report_ambiguous_witness_not_selection(self):
        r=analyze([tick(),tick()],[bar()],[tick()])
        self.assertEqual(r['ambiguous_witnesses'],1);self.assertEqual(r['witnesses_matched'],0)
        self.assertEqual(r['witnesses'][0]['matching_original_row_indices'],[0,1])

    def test_witness_compares_every_field(self):
        for field,value in (('flags',2),('last',1.),('volume',1),('volume_real',1.)):
            r=analyze([tick()],[bar()],[{**tick(),field:value}]);self.assertEqual(r['missing_witnesses'],1)

    def test_upper_boundary_excluded_and_outside_identified(self):
        rows=[tick(START-1),tick(START),tick(END),tick(END+1)]
        r=analyze(rows,[bar()],[])
        self.assertEqual(r['half_open_hour_rows'],1);self.assertEqual(r['upper_boundary_row_indices'],[2])
        self.assertEqual(r['outside_inclusive_request_row_indices'],[0,3])
        self.assertEqual(r['first_row_without_predecessor_indices'],[])
        self.assertEqual(r['fixed_definition_comparisons'][0]['original_row_indices'],[1])

    def test_fixed_subset_ohlc_and_volume_differences(self):
        rows=[tick(flags=2),tick(START+1,bid=1.09,flags=4),tick(START+2,bid=1.08,flags=2)]
        r=analyze(rows,[bar(2)],[]);c={x['definition']:x for x in r['fixed_definition_comparisons']}
        self.assertEqual(c['all']['volume_difference'],1);self.assertEqual(c['bid_flag']['volume_difference'],0)
        self.assertEqual(c['bid_flag']['bid_ohlc'],dict(open=1.1,high=1.1,low=1.08,close=1.08))
        self.assertEqual({x['field'] for x in c['bid_flag']['bar_price_differences']},{'low','close'})

    def test_empty_and_unavailable_bar_comparisons_are_explicit(self):
        r=analyze([],[],[]);self.assertEqual(r['source_rows'],0)
        self.assertTrue(all(c['bid_ohlc'] is None and c['bar_price_differences']==[dict(field='comparison_unavailable')] for c in r['fixed_definition_comparisons']))

    def test_invalid_schema_prices_flags_and_chronology_rejected(self):
        cases=([{**tick(),'bid':float('nan')}],[{**tick(),'flags':True}],
               [{**tick(),'flags':-1}],[{**tick(),'time':0}],[tick(START+1),tick(START)])
        for rows in cases:
            with self.assertRaises(ValueError):analyze(rows,[bar()],[])
        with self.assertRaises(ValueError):analyze([tick()],[bar()],[],START-1,END)

    def test_original_all_field_fidelity_and_read_only_inputs(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp);rows=[tick(),tick(START+1,flags=1028)];meta=fixture(path,rows)
            before={p.name:p.read_bytes() for p in path.iterdir()}
            self.assertEqual(original(path,'ticks',meta),rows)
            self.assertEqual({p.name:p.read_bytes() for p in path.iterdir()},before)
            changed={**meta,'binary_layout':{**meta['binary_layout'],'itemsize':64}}
            with self.assertRaises(ValueError):original(path,'ticks',changed)

    def test_mutation_detected_even_with_rehashed_csv(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp);meta=fixture(path,[tick()]);p=path/'ticks.csv'
            p.write_text(p.read_text().replace('1.1001','1.1002'))
            with self.assertRaises(ValueError):original(path,'ticks',meta)
            meta.update(csv_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),csv_bytes=p.stat().st_size)
            with self.assertRaises(ValueError):original(path,'ticks',meta)

    def test_independent_reconstruction_agrees_on_synthetic_cases(self):
        cases=([],[tick()],[tick(),tick(),tick(END)],
               [tick(START-1,flags=1024),tick(START,flags=1026),tick(START+1,bid=1.09,flags=4),tick(END,flags=6)])
        for rows in cases:
            self.assertEqual(analyze(rows,[bar()],rows[:2]),CHECK['reconstruct'](rows,[bar()],rows[:2]))

    def test_no_market_api_calls_or_execution_imports_in_new_sources(self):
        forbidden={'initialize','copy_ticks_range','copy_rates_range','symbol_info_tick','order_send','symbol_select','shutdown'}
        paths=[ROOT/'src/forex_demo_lab/fresh_flags_034.py',ROOT/'scripts/fresh-flags-034.py',ROOT/'scripts/check-fresh-flags-034.py']
        for p in paths:
            tree=ast.parse(p.read_text())
            for node in ast.walk(tree):
                if isinstance(node,(ast.Import,ast.ImportFrom)):
                    self.assertNotIn('MetaTrader5',ast.unparse(node))
                if isinstance(node,ast.Call):
                    name=node.func.attr if isinstance(node.func,ast.Attribute) else node.func.id if isinstance(node.func,ast.Name) else ''
                    self.assertNotIn(name,forbidden)
