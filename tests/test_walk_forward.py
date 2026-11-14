from copy import deepcopy
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from forex_demo_lab.cli import write_json
from forex_demo_lab.model import Config
from forex_demo_lab.research_simulation import ResearchTickSimulator
from forex_demo_lab.tick_audit import sha256
from forex_demo_lab import walk_forward as wf

spec = importlib.util.spec_from_file_location('walk014', wf.ROOT/'scripts/walk-forward-014.py')
cli = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cli)
check_spec = importlib.util.spec_from_file_location('check014',wf.ROOT/'scripts/check-walk-forward-014.py')
checker = importlib.util.module_from_spec(check_spec)
check_spec.loader.exec_module(checker)


class WalkForwardTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def fixture(self):
        folder = self.root/'data'
        cli.synthetic_fixture(folder)
        return folder/'bundle.json'

    def frozen(self):
        bundle = self.fixture()
        dest = self.root/'experiment'
        ledger = wf.freeze(bundle,dest)
        return ledger,dest

    def market_review(self):
        evidence = self.root/'evidence.json'
        evidence.write_text('{"claimed_review_test_only":true}')
        return {'kind':'chronological_data_review','synthetic':False,'performance_evaluation_ready':True,
            'evidence_bindings':{str(evidence):sha256(evidence)},
            'years':{str(y):{'performance_evaluation_ready':True,'clock_verified':True,
                'independent_corroboration_passed':True,'source_lineage_reviewed':True,
                'unresolved_open_session_gaps':0,'source_months':[f'{y}{m:02}' for m in range(1,13)]}
                     for y in wf.YEARS}}

    def test_global_pass_cannot_override_a_blocked_year_or_gap(self):
        for key,value in [('clock_verified',False),('performance_evaluation_ready',False),
                          ('source_lineage_reviewed',False),('unresolved_open_session_gaps',1),
                          ('unresolved_open_session_gaps',False),('source_months',['202301'])]:
            review = self.market_review()
            review['years']['2023'][key] = value
            with self.subTest(key=key),self.assertRaises(ValueError):
                wf.review_gate(review)

    def test_synthetic_and_market_roles_cannot_be_swapped(self):
        fixture = {'kind':'synthetic_chronological_fixture','synthetic':True,
            'performance_evaluation_ready':False,'years':{str(y):{} for y in wf.YEARS}}
        wf.review_gate(fixture,True)
        with self.assertRaises(ValueError): wf.review_gate(fixture,False)
        with self.assertRaises(ValueError): wf.review_gate(self.market_review(),True)
        fixture['performance_evaluation_ready']=True
        with self.assertRaises(ValueError): wf.review_gate(fixture,True)

    def test_missing_or_changed_review_evidence_fails(self):
        review = self.market_review()
        wf.review_gate(review)
        Path(next(iter(review['evidence_bindings']))).write_text('changed')
        with self.assertRaisesRegex(ValueError,'evidence changed'): wf.review_gate(review)
        review['evidence_bindings']={}
        with self.assertRaises(ValueError): wf.review_gate(review)

    def test_old_diagnostic_gate_is_rejected_before_output_creation(self):
        bundle = self.fixture()
        review = bundle.parent/'review.json'
        review.write_text(json.dumps({'performance_evaluation_ready':False}))
        dest = self.root/'experiment'
        with self.assertRaisesRegex(ValueError,'Annual data review'): wf.freeze(bundle,dest)
        self.assertFalse(dest.exists())

    def test_missing_year_and_reserved_year_rejected(self):
        bundle = self.fixture()
        value = wf.load(bundle)
        value['years']['2025']=value['years'].pop('2023')
        bundle.write_text(json.dumps(value))
        with self.assertRaises(ValueError): wf.freeze(bundle,self.root/'experiment')

    def test_freeze_binds_all_inputs_and_exact_warmup_before_returns(self):
        ledger,dest = self.frozen()
        self.assertEqual(wf.verify(dest),ledger)
        self.assertFalse((dest/'run').exists())
        self.assertFalse(ledger['performance_evaluation_ready'])
        self.assertEqual(ledger['maximum_scenarios'],40)
        self.assertGreater(ledger['windows']['A-training']['evaluation_start_ms'],wf.bound(2020))
        self.assertEqual(ledger['windows']['B-training']['evaluation_start_ms'],wf.bound(2021))
        for label,window in ledger['windows'].items():
            ticks=list(wf.window_ticks(ledger,window))
            hours={t['time_msc']//wf.HOUR for t in ticks if t['time_msc']<window['evaluation_start_ms']}
            self.assertEqual(len(hours),201,label)
            self.assertEqual([t['sequence'] for t in ticks],list(range(len(ticks))))
            self.assertLess(ticks[-1]['time_msc'],wf.bound(window['end_year']))

    def test_changed_bytes_provenance_and_frozen_ledger_rejected(self):
        ledger,dest = self.frozen()
        path=Path(ledger['entries']['2022']['data'])
        path.write_bytes(path.read_bytes()+b'x')
        with self.assertRaisesRegex(ValueError,'input or evidence changed'): wf.verify(dest)
        with self.assertRaises(ValueError): list(wf.annual_ticks(ledger['entries']['2022'],2022,True))
        value=wf.load(dest/'ledger.json');value['configs']['base']['leverage']=100
        (dest/'ledger.json').write_text(json.dumps(value))
        with self.assertRaisesRegex(ValueError,'ledger changed'): wf.verify(dest)

    def test_annual_counts_and_role_are_checked_to_end_of_stream(self):
        bundle=self.fixture()
        entry={k:str(bundle.parent/p) for k,p in wf.load(bundle)['years']['2020'].items()}
        meta=wf.load(entry['provenance']);meta['ticks']+=1
        Path(entry['provenance']).write_text(json.dumps(meta))
        with self.assertRaisesRegex(ValueError,'coverage differs'): list(wf.annual_ticks(entry,2020,True))
        with self.assertRaises(ValueError): list(wf.annual_ticks(entry,2020,False))

    def test_same_ms_quotes_preserved_and_reordered_annual_rows_rejected(self):
        import csv,gzip
        bundle=self.fixture()
        entry={k:str(bundle.parent/p) for k,p in wf.load(bundle)['years']['2020'].items()}
        with gzip.open(entry['data'],'rt',newline='') as stream:
            reader=csv.DictReader(stream); rows=list(reader)
        rows.insert(1,{**rows[0],'bid':'1.10001','ask':'1.10011'})
        for i,row in enumerate(rows): row['sequence']=i
        def rewrite():
            with gzip.open(entry['data'],'wt',newline='') as stream:
                writer=csv.DictWriter(stream,fieldnames=['sequence','time_msc','bid','ask'])
                writer.writeheader();writer.writerows(rows)
            meta=wf.load(entry['provenance'])
            meta.update(data_sha256=sha256(Path(entry['data'])),ticks=len(rows))
            Path(entry['provenance']).write_text(json.dumps(meta))
        rewrite()
        kept=list(wf.annual_ticks(entry,2020,True))
        self.assertEqual(kept[0]['time_msc'],kept[1]['time_msc'])
        self.assertNotEqual(kept[0]['bid'],kept[1]['bid'])
        rows[3]['time_msc']=rows[0]['time_msc']
        rewrite()
        with self.assertRaisesRegex(ValueError,'sequence, time or quote'):
            list(wf.annual_ticks(entry,2020,True))

    def test_future_quote_and_insufficient_warmup_abort_replay(self):
        ledger,dest=self.frozen()
        window=ledger['windows']['A-test']
        original=list(wf.window_ticks(ledger,window))
        future={'sequence':len(original),'time_msc':wf.bound(2023),'bid':1.1,'ask':1.1001}
        with patch.object(wf,'window_ticks',return_value=iter(original+[future])):
            with self.assertRaisesRegex(ValueError,'future'): wf.replay_window(ledger,window)
        with patch.object(wf,'window_ticks',return_value=iter([{**t,'sequence':i} for i,t in enumerate(original[3:])])):
            with self.assertRaisesRegex(ValueError,'201'): wf.replay_window(ledger,window)

    def test_closed_trades_and_marked_open_equity_cross_year_with_costs(self):
        config=Config(**wf.load(wf.ROOT/'config/tick-pilot-003.json'))
        evaluation=wf.bound(2021)-wf.HOUR
        sim=ResearchTickSimulator(config,'C00',evaluation)
        ticks=[{'sequence':i,'time_msc':evaluation-(201-i)*wf.HOUR,'bid':1.1,'ask':1.1001} for i in range(201)]
        ticks += [{'sequence':201,'time_msc':evaluation,'bid':1.1,'ask':1.1001},
                  {'sequence':202,'time_msc':evaluation+wf.HOUR-1,'bid':1.102,'ask':1.1021},
                  {'sequence':203,'time_msc':wf.bound(2021),'bid':1.103,'ask':1.1031}]
        marks={}
        # Use the real risk/fee/marking engine; force one entry to isolate accounting.
        with patch.object(sim,'_decision',side_effect=lambda: (1,.01)
                          if sim.current['hour']*wf.HOUR >= evaluation and len(sim.history)>=201 else (0,0)):
            for tick in ticks:
                sim.step_tick(tick)
                if tick['time_msc']>=evaluation: marks[wf.period(tick['time_msc'])]=sim.last_equity
        self.assertIsNotNone(sim.position)
        mark2020=marks['2020-Q4']
        row,metrics=wf.reconcile(sim,marks,2020,2022,evaluation)
        self.assertGreater(row['years']['2020']['net_pnl'],0)
        self.assertEqual(row['years']['2020']['closed_trades'],0)
        self.assertEqual(row['years']['2021']['closed_trades'],1)
        self.assertAlmostEqual(row['years']['2021']['starting_equity'],mark2020)
        self.assertGreater(metrics['commission'],0)
        self.assertLess(metrics['swap'],0)
        self.assertAlmostEqual(sum(row['quarters'].values()),metrics['net_pnl'])
        self.assertAlmostEqual(row['net_winning_trade_sum']+row['net_losing_trade_sum'],metrics['net_pnl'])
        self.assertEqual(sim.trades[0]['reason'],'end_of_sample')

    def test_real_replay_has_no_warmup_trades_and_reconciles_all_costs(self):
        ledger,dest=self.frozen()
        window=ledger['windows']['A-training']
        reports=wf.replay_window(ledger,window)
        self.assertEqual(len(reports),10)
        for row in reports:
            self.assertEqual(row['warmup_hours'],201)
            self.assertTrue(row['reconciled'])
            self.assertAlmostEqual(sum(row['quarters'].values()),row['metrics']['net_pnl'])
            for trade in row['trades']:
                self.assertGreaterEqual(int(datetime.fromisoformat(trade['opened']).timestamp()*1000),window['evaluation_start_ms'])
        self.assertEqual(wf.select_fold(wf.selection_rows(reports),'A')['selected'],'CASH')

    def test_choices_lock_before_test_and_all_controls_publish_for_cash(self):
        ledger,dest=self.frozen()
        original=wf.replay_window
        calls=[]
        def observed_replay(l,w):
            calls.append((w['start_year'],w['end_year']))
            fold='A' if w['start_year']==2022 else 'B' if w['start_year']==2023 else None
            if fold:
                lock=dest/'run'/f'{fold}-selection.json'
                self.assertTrue(lock.exists())
                value=wf.load(lock)
                self.assertEqual(len(value['training_report_bindings']),10)
                for name,digest in value['training_report_bindings'].items():
                    self.assertEqual(sha256(dest/'run'/name),digest)
            return original(l,w)
        with patch.object(wf,'replay_window',side_effect=observed_replay): result=wf.run(dest)
        self.assertEqual(calls,[(2020,2022),(2022,2023),(2021,2023),(2023,2024)])
        self.assertEqual(len(result['scenario_bindings']),40)
        self.assertEqual(len(result['selection_bindings']),2)
        self.assertFalse(result['historical_positive_edge_screen_passed'])
        self.assertFalse(result['market_profitability_established'])
        independent=checker.check(dest)
        self.assertEqual(independent['scenarios'],40)
        self.assertFalse(independent['market_data_eligibility_verified'])
        for row in result['selected_tests']:
            self.assertEqual(row['candidate'],'CASH')
            self.assertFalse(row['positive_edge_screen_passed'])
            self.assertEqual(row['metrics']['net_pnl'],0)
        with self.assertRaises(FileExistsError): wf.run(dest)

    def test_independent_checker_rejects_inconsistent_boundary_equity(self):
        ledger,dest=self.frozen()
        wf.run(dest)
        path=dest/'run'/'A-training-C00-base.json'
        row=wf.load(path)
        mark=next(iter(row['period_closing_marks'].values()))
        mark['equity']+=1
        path.write_text(json.dumps(row))
        summary=wf.load(dest/'run'/'summary.json')
        summary['scenario_bindings'][path.name]=sha256(path)
        (dest/'run'/'summary.json').write_text(json.dumps(summary))
        with self.assertRaisesRegex(ValueError,'accounting differs'): checker.check(dest)

    def test_partial_run_is_preserved_and_not_silently_resumed(self):
        ledger,dest=self.frozen()
        with patch.object(wf,'replay_window',side_effect=ValueError('intentional failure')):
            with self.assertRaises(ValueError): wf.run(dest)
        self.assertTrue((dest/'run').exists())
        self.assertFalse((dest/'run'/'summary.json').exists())
        with self.assertRaises(FileExistsError): wf.run(dest)
        with self.assertRaises(FileExistsError): wf.freeze(self.root/'data'/'bundle.json',dest)

    def test_locked_choice_tampering_prevents_test_reports_and_completion(self):
        ledger,dest=self.frozen()
        original=wf.replay_window
        def tamper(l,w):
            result=original(l,w)
            if w['start_year']==2022:
                path=dest/'run'/'A-selection.json'
                value=wf.load(path);value['selected']='C00'
                path.write_text(json.dumps(value))
            return result
        with patch.object(wf,'replay_window',side_effect=tamper):
            with self.assertRaisesRegex(ValueError,'choice changed'): wf.run(dest)
        self.assertFalse((dest/'run'/'summary.json').exists())
        self.assertFalse((dest/'run'/'A-test-C00-base.json').exists())


if __name__=='__main__': unittest.main()
