import ast
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from forex_demo_lab import walk_forward as old
from forex_demo_lab import walk_forward_metrics as wf
from forex_demo_lab.execution_metrics import ExecutableEquityResearchTickSimulator
from forex_demo_lab.runner_migration import generated_runner,compare_controls,challenge,VERSION


def imported(name,path):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module);return module


cli=imported('cli014_metrics_test',old.ROOT/'scripts/walk-forward-014.py')
independent=imported('checker020_test',old.ROOT/'scripts/check-walk-forward-020.py')


class WalkForwardMetricTests(unittest.TestCase):
    def setUp(self):
        folder=tempfile.TemporaryDirectory();self.addCleanup(folder.cleanup);self.root=Path(folder.name)

    def frozen(self):
        data=self.root/'data';cli.synthetic_fixture(data);dest=self.root/'experiment'
        return wf.freeze(data/'bundle.json',dest),dest

    def test_only_declared_functions_change_and_gate_iterator_selector_stay_identical(self):
        original=(old.ROOT/'src/forex_demo_lab/walk_forward.py').read_text()
        generated=(old.ROOT/'src/forex_demo_lab/walk_forward_metrics.py').read_text()
        self.assertEqual(generated,generated_runner(original))
        funcs=lambda s:{node.name:ast.dump(node,include_attributes=False) for node in ast.parse(s).body if isinstance(node,ast.FunctionDef)}
        before,after=funcs(original),funcs(generated)
        self.assertEqual(set(before),set(after))
        changed={name for name in before if before[name]!=after[name]}
        self.assertEqual(changed,{'source_files','freeze','verify','replay_window','run'})

    def test_corrected_constructor_is_used_for_all_ten_accounts(self):
        ledger,dest=self.frozen();constructed=[]
        def factory(*args,**kwargs):
            result=ExecutableEquityResearchTickSimulator(*args,**kwargs);constructed.append(result);return result
        with patch.object(wf,'ResearchTickSimulator',side_effect=factory):rows=wf.replay_window(ledger,ledger['windows']['A-test'])
        self.assertEqual(len(constructed),10)
        self.assertTrue(all(s.execution_metric_version==VERSION for s in constructed))
        self.assertTrue(all(row['metric_contract']==VERSION and row['runner_version']=='020' for row in rows))
        self.assertIn('src/forex_demo_lab/execution_metrics.py',ledger['source_bindings'])

    def test_legacy_and_resealed_wrong_version_ledgers_are_rejected(self):
        with self.assertRaisesRegex(ValueError,'new freeze'):wf.verify(old.ROOT/'reports/walk-forward-014-synthetic')
        ledger,dest=self.frozen()
        for key,value in (('runner_version','014'),('metric_contract','legacy')):
            changed=deepcopy(ledger);changed[key]=value
            (dest/'ledger.json').write_text(json.dumps(changed))
            (dest/'seal.json').write_text(json.dumps({'ledger_sha256':old.sha256(dest/'ledger.json')}))
            with self.assertRaisesRegex(ValueError,'version mismatch'):wf.verify(dest)

    def test_blocked_market_year_or_gap_rejects_before_dataset_iteration(self):
        data=self.root/'data';cli.synthetic_fixture(data);bundle=old.load(data/'bundle.json');bundle['synthetic']=False
        evidence=self.root/'review-evidence.json';evidence.write_text('{}')
        good=dict(kind='chronological_data_review',synthetic=False,performance_evaluation_ready=True,
                  evidence_bindings={str(evidence):old.sha256(evidence)},
                  years={str(y):dict(performance_evaluation_ready=True,clock_verified=True,
                         independent_corroboration_passed=True,source_lineage_reviewed=True,
                         unresolved_open_session_gaps=0,source_months=[f'{y}{m:02}' for m in range(1,13)]) for y in old.YEARS})
        (data/'bundle.json').write_text(json.dumps(bundle))
        for key,value in (('clock_verified',False),('unresolved_open_session_gaps',1),('source_lineage_reviewed',False)):
            review=deepcopy(good);review['years']['2023'][key]=value;(data/'review.json').write_text(json.dumps(review))
            dest=self.root/('rejected-'+key)
            with patch.object(wf,'inventory',side_effect=AssertionError('Data iteration forbidden')) as iterator:
                with self.assertRaisesRegex(ValueError,'lacks clock'):wf.freeze(data/'bundle.json',dest)
                iterator.assert_not_called()
            self.assertFalse(dest.exists())

    def test_choice_locks_before_test_replay_with_corrected_contract(self):
        ledger,dest=self.frozen();original=wf.replay_window;calls=[]
        def observed(l,w):
            calls.append((w['start_year'],w['end_year']))
            fold='A' if w['start_year']==2022 else 'B' if w['start_year']==2023 else None
            if fold:
                lock=wf.load(dest/'run'/f'{fold}-selection.json')
                self.assertEqual(lock['metric_contract'],VERSION);self.assertEqual(len(lock['training_report_bindings']),10)
            return original(l,w)
        with patch.object(wf,'replay_window',side_effect=observed):result=wf.run(dest)
        self.assertEqual(calls,[(2020,2022),(2022,2023),(2021,2023),(2023,2024)])
        self.assertEqual(len(result['scenario_bindings']),40)
        self.assertFalse(result['historical_positive_edge_screen_passed'])
        self.assertEqual(independent.check(dest)['scenarios'],40)

    def test_future_quote_is_rejected_by_new_runner(self):
        ledger,dest=self.frozen();window=ledger['windows']['A-test'];ticks=list(wf.window_ticks(ledger,window))
        ticks.append(dict(sequence=len(ticks),time_msc=wf.bound(2023),bid=1.1,ask=1.1001))
        with patch.object(wf,'window_ticks',return_value=iter(ticks)):
            with self.assertRaisesRegex(ValueError,'future'):wf.replay_window(ledger,window)

    def test_rebound_peak_drawdown_or_trade_corruption_is_rejected(self):
        ledger,dest=self.frozen();wf.run(dest);name='A-test-C04-base.json';path=dest/'run'/name
        original=wf.load(path);summary=wf.load(dest/'run/summary.json')
        self.assertTrue(original['trades'])
        for field in ('peak','drawdown','exit','contract'):
            changed=deepcopy(original)
            if field=='peak':changed['peak_tick_equity']+=1
            elif field=='drawdown':changed['metrics']['max_tick_drawdown']+=.001;changed['max_tick_drawdown']+=.001
            elif field=='exit':changed['trades'][0]['exit']+=.001
            else:changed['metric_contract']='legacy'
            path.write_text(json.dumps(changed));modified=deepcopy(summary);modified['scenario_bindings'][name]=old.sha256(path)
            (dest/'run/summary.json').write_text(json.dumps(modified))
            with self.subTest(field=field),self.assertRaises(ValueError):independent.check(dest)

    def test_scenario_comparison_rejects_cash_changes_and_missing_controls(self):
        root=old.ROOT/'reports/walk-forward-014-synthetic/run';summary=old.load(root/'summary.json')
        rows={n:old.load(root/n) for n in summary['scenario_bindings']};changed=deepcopy(rows)
        next(iter(changed.values()))['metrics']['net_pnl']+=1
        with self.assertRaises(ValueError):compare_controls(rows,changed)
        changed=deepcopy(rows);changed.pop(next(iter(changed)))
        with self.assertRaises(ValueError):compare_controls(rows,changed)

    def test_declared_challenge_bounds_and_target_quotes_are_fixed(self):
        folder=self.root/'challenge';challenge(folder);bundle=old.load(folder/'bundle.json')
        for year in old.YEARS:
            entry={k:str(folder/v) for k,v in bundle['years'][str(year)].items()}
            quotes=list(wf.annual_ticks(entry,year,True));self.assertEqual(len(quotes),522)
            overshoots=[q for q in quotes if q['time_msc']%wf.HOUR==100]
            self.assertEqual([q['bid'] for q in overshoots],[1.111,1.089])
            self.assertEqual(len({q['time_msc']//wf.HOUR for q in quotes}),520)
        self.assertFalse(old.load(folder/'review.json')['performance_evaluation_ready'])


if __name__=='__main__':unittest.main()
