from copy import deepcopy
from datetime import datetime,timezone
import gzip
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

from forex_demo_lab.corrected_clock import Replay
from forex_demo_lab.normalization import MONTHS, completed, coverage, empty_hours, milliseconds, normalize
from forex_demo_lab.tick_audit import sha256
from forex_demo_lab.walk_forward import annual_ticks, review_gate

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('check015',ROOT/'scripts/check-normalization-015.py')
checker=importlib.util.module_from_spec(spec);spec.loader.exec_module(checker)


def tick(i,label,bid=1.1,volume=.5):
    return {'sequence':i,'source_label':datetime.fromisoformat(label),
            'bid':bid,'ask':bid+.0001,'volume':volume}


class NormalizationTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.binding={'archive_sha256':'source-fixture-only','metadata_sha256':'fixture','original_rows':4}

    def repeated(self):
        return [tick(0,'2023-10-29T19:00:00'),tick(1,'2023-10-29T19:59:59',1.11),
                tick(2,'2023-10-29T19:00:00'),tick(3,'2023-10-29T19:59:59',1.11)]

    def normalized(self):
        folder=self.root/'202310'
        meta=normalize(self.repeated(),'202310',folder,self.binding,4,Replay(0,2,2))
        return folder,meta

    def test_exact_replay_lineage_bid_ask_volume_and_original_count(self):
        folder,meta=self.normalized()
        self.assertEqual(meta['original_rows'],4)
        self.assertEqual(meta['candidate_rows'],2)
        self.assertEqual(meta['collapsed_replay_rows'],2)
        self.assertEqual(completed(folder,self.binding),meta)
        with gzip.open(folder/'ticks.csv.gz','rt') as f: lines=f.read().splitlines()
        self.assertEqual(lines[1].split(',')[:3],['0','0','2023-10-29T19:00:00.000'])
        self.assertEqual(lines[2].split(',')[-1],'0.5')
        result=checker.check_month(folder)
        self.assertEqual(result['ticks'],2)
        self.assertFalse(result['market_data_eligibility_verified'])

    def test_source_sequence_after_replay_and_same_ms_order_preserved(self):
        values=self.repeated()+[tick(4,'2023-10-29T20:00:00',1.12),tick(5,'2023-10-29T20:00:00',1.13)]
        folder=self.root/'data'
        normalize(values,'202310',folder,self.binding,6,Replay(0,2,2))
        with gzip.open(folder/'ticks.csv.gz','rt') as f:lines=f.read().splitlines()
        self.assertEqual([line.split(',')[1] for line in lines[1:]],['0','1','4','5'])
        self.assertEqual(checker.check_month(folder)['ticks'],4)
        inventory=json.loads((folder/'inventory.json').read_text())
        self.assertEqual(inventory['same_millisecond_transitions'],1)

    def test_ordinary_identical_quotes_remain_and_spread_is_observed(self):
        values=[tick(0,'2023-07-14T10:00:00'),tick(1,'2023-07-14T10:00:00')]
        folder=self.root/'data'
        normalize(values,'202307',folder,self.binding,2)
        inventory=json.loads((folder/'inventory.json').read_text())
        self.assertEqual(inventory['identical_transition_events_retained'],1)
        self.assertAlmostEqual(inventory['hourly'][0]['entry_spread_pips'],1)
        self.assertEqual(checker.check_month(folder)['ticks'],2)

    def test_real_march_gap_remains_and_no_missing_hour_is_synthesized(self):
        values=[tick(0,'2023-03-26T18:59:56.352'),tick(1,'2023-03-26T20:00:00.010')]
        folder=self.root/'data'
        normalize(values,'202303',folder,self.binding,2)
        inventory=json.loads((folder/'inventory.json').read_text())
        self.assertEqual(len(inventory['hourly']),2)
        self.assertAlmostEqual(inventory['gaps_over_one_hour'][0]['seconds'],3603.658)
        self.assertEqual(checker.check_month(folder)['ticks'],2)

    def test_candidate_next_year_edge_retained(self):
        folder=self.root/'data'
        meta=normalize([tick(0,'2023-12-31T23:59:59.999')],'202312',folder,self.binding,1)
        expected=milliseconds(datetime(2024,1,1,4,59,59,999000,tzinfo=timezone.utc))
        self.assertEqual(meta['last_ms'],expected)
        inventory=json.loads((folder/'inventory.json').read_text())
        self.assertEqual(inventory['candidate_year_tick_counts'],{'2024':1})
        self.assertEqual(checker.check_month(folder)['ticks'],1)

    def test_changed_incomplete_replay_and_unlisted_reversal_publish_no_provenance(self):
        for name,values,replay,count in [('changed',self.repeated(),Replay(0,2,2),4),
                                         ('incomplete',self.repeated()[:3],Replay(0,2,2),4),
                                         ('unlisted',self.repeated(),None,4)]:
            if name=='changed':values[2]['volume']=.7
            folder=self.root/name
            with self.assertRaises(ValueError):normalize(values,'202310',folder,self.binding,count,replay)
            self.assertFalse((folder/'provenance.json').exists())
            self.assertTrue((folder/'ticks.csv.gz.partial').exists())
            with self.assertRaises(ValueError):completed(folder,self.binding)

    def test_wrong_row_count_rejected_before_ready_publication(self):
        folder=self.root/'data'
        with self.assertRaises(ValueError):normalize(self.repeated(),'202310',folder,self.binding,5,Replay(0,2,2))
        self.assertFalse((folder/'provenance.json').exists())
        self.assertTrue((folder/'ticks.csv.gz.partial').exists())

    def test_tampered_completed_data_inventory_provenance_or_binding_rejected(self):
        folder,meta=self.normalized()
        for path in ('ticks.csv.gz','inventory.json','provenance.json'):
            p=folder/path;original=p.read_bytes();p.write_bytes(original+b' ')
            with self.subTest(path=path),self.assertRaises(ValueError):completed(folder,self.binding)
            p.write_bytes(original)
        with self.assertRaises(ValueError):completed(folder,{'archive_sha256':'changed'})
        with self.assertRaises(FileExistsError):normalize(self.repeated(),'202310',folder,self.binding,4,Replay(0,2,2))

    def test_reserved_source_year_and_noninteger_milliseconds_rejected(self):
        with self.assertRaises(ValueError):normalize([],'202511',self.root/'data',self.binding,0)
        with self.assertRaises(ValueError):milliseconds(datetime(2020,1,1,0,0,0,1,tzinfo=timezone.utc))
        with self.assertRaises(ValueError):milliseconds(datetime(2020,1,1))

    def rows(self):
        return [{'source_month':m,'first_ms':i*10000,'last_ms':i*10000+9000,
                 'original_rows':1,'candidate_rows':1,'collapsed_replay_rows':0} for i,m in enumerate(MONTHS)]

    def test_all_month_seams_and_year_seams_reviewed_without_sorting_quotes(self):
        result=coverage(self.rows())
        self.assertEqual(len(result['month_seams']),47)
        self.assertEqual(sum(s['after_source_month'].endswith('12') for s in result['month_seams']),3)
        rows=self.rows();rows[1]['first_ms']=1
        with self.assertRaises(ValueError):coverage(rows)

    def test_missing_duplicate_month_rejected_not_skipped(self):
        with self.assertRaises(ValueError):coverage(self.rows()[:-1])
        rows=self.rows();rows[-1]=deepcopy(rows[0])
        with self.assertRaises(ValueError):coverage(rows)

    def test_quote_free_watchlist_does_not_certify_sessions_or_discard_edges(self):
        h=milliseconds(datetime(2020,1,1,tzinfo=timezone.utc))
        result=empty_hours([h,h-3600000])
        self.assertEqual(result['observed_hours_inside_bounds'],1)
        self.assertEqual(result['observed_hours_outside_bounds'],[h-3600000])
        self.assertFalse(result['session_closures_certified'])
        self.assertIn(h+3600000,result['weekday_quote_free_hours'])

    def test_performance_reader_and_review_reject_diagnostic_output(self):
        folder,meta=self.normalized()
        with self.assertRaises(ValueError):list(annual_ticks({'data':str(folder/'ticks.csv.gz'),
                                                            'provenance':str(folder/'provenance.json')},2023,False))
        with self.assertRaises(ValueError):review_gate(meta,False)

    def test_independent_checker_detects_false_hourly_close_even_when_hash_updated(self):
        folder,meta=self.normalized()
        inventory=json.loads((folder/'inventory.json').read_text())
        inventory['hourly'][0]['bid_close']+=.001
        (folder/'inventory.json').write_text(json.dumps(inventory))
        meta['inventory_sha256']=sha256(folder/'inventory.json')
        (folder/'provenance.json').write_text(json.dumps(meta))
        with self.assertRaisesRegex(ValueError,'hourly aggregate'):checker.check_month(folder)


if __name__=='__main__':unittest.main()
