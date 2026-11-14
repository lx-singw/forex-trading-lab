from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
import runpy
import tempfile
import unittest
from unittest.mock import patch

from forex_demo_lab import challenger_chronology_093 as wf
from forex_demo_lab import challenger_selection_093 as selection
from forex_demo_lab import selection as original_selection
from forex_demo_lab import walk_forward_metrics as original_runner
from forex_demo_lab.exit_experiment_030 import Experiment030Simulator
from forex_demo_lab.model import Bar, Config
from forex_demo_lab.strategy_experiment_028 import Experiment028Simulator

checker = runpy.run_path(str(wf.ROOT / 'scripts/check-challenger-chronology-093.py'))


def training_rows(fold='A', pnl=100):
    start, end = selection.FOLDS[fold]
    rows = []
    for c in selection.CANDIDATES:
        for k in selection.COSTS:
            rows.append(dict(candidate=c, cost=k, training_start=f'{start}-01-01T00:00:00+00:00',
                training_end_exclusive=f'{end}-01-01T00:00:00+00:00',
                years={str(start): dict(starting_equity=10000, net_pnl=pnl, closed_trades=30),
                       str(start+1): dict(starting_equity=10000+pnl, net_pnl=pnl, closed_trades=30)},
                quarters={f'{y}-Q{q}': pnl/4 for y in range(start, end) for q in range(1, 5)},
                closed_trades=60, net_winning_trade_sum=400 if pnl > 0 else 200,
                net_losing_trade_sum=2*pnl-(400 if pnl > 0 else 200), max_tick_drawdown=.05))
    return rows


class Challenger093Tests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory(); self.addCleanup(folder.cleanup)
        self.root = Path(folder.name)

    def frozen(self):
        bundle = wf.synthetic_fixture(self.root / 'data')
        dest = self.root / 'experiment'
        return wf.freeze(bundle, dest), dest

    def rewrite_ledger(self, dest, ledger):
        (dest / 'ledger.json').write_text(json.dumps(ledger))
        (dest / 'seal.json').write_text(json.dumps(dict(ledger_sha256=wf.sha256(dest / 'ledger.json'))))

    def started_sim(self, candidate='C07', side=1):
        base = wf.bound(2020); start = base + 201*wf.HOUR
        cfg = Config(**wf.load(wf.ROOT / 'config/tick-pilot-003.json'))
        sim = wf.simulator(cfg, candidate, start)
        ticks = [dict(sequence=i, time_msc=base+i*wf.HOUR,
            bid=1.125 if i < 200 else 1.125+side*.125,
            ask=(1.125 if i < 200 else 1.125+side*.125)+.0001) for i in range(202)]
        for tick in ticks:
            sim.step_tick(tick)
        self.assertIsNotNone(sim.position)
        self.assertEqual(sim.position.side, side)
        return sim, ticks

    def append(self, sim, ticks, price, ms=None):
        q = dict(sequence=len(ticks), time_msc=ms if ms is not None else ticks[-1]['time_msc']+1,
                 bid=price, ask=price+.0001)
        ticks.append(q); sim.step_tick(q)
        return q

    def test_separate_candidate_inventory_and_original_selector_unchanged(self):
        self.assertEqual(selection.CANDIDATES, ('C00','C05','C06','C07','C08'))
        self.assertEqual(original_selection.CANDIDATES, ('C00','C01','C02','C03','C04'))
        self.assertIs(selection.validate, original_selection.validate)
        wf.specification()

    def test_exact_inventory_duplicates_missing_unknown_cost_reject(self):
        cases = []
        rows = training_rows(); cases.append(rows[:-1])
        rows = training_rows(); rows[-1] = deepcopy(rows[0]); cases.append(rows)
        rows = training_rows(); rows[0]['candidate'] = 'C04'; cases.append(rows)
        rows = training_rows(); rows[0]['cost'] = 'free'; cases.append(rows)
        for rows in cases:
            with self.subTest(rows=rows[0]['candidate']), self.assertRaises(ValueError):
                selection.select_fold(rows, 'A')

    def test_ties_and_input_order_are_deterministic(self):
        rows = training_rows(); a = selection.select_fold(rows, 'A')
        self.assertEqual(a['selected'], 'C00')
        self.assertEqual(a, selection.select_fold(list(reversed(rows)), 'A'))

    def test_both_costs_required_before_adverse_ranking(self):
        rows = training_rows()
        for r in rows:
            if r['candidate'] == 'C00' or r['candidate'] == 'C05' and r['cost'] == 'base':
                r['max_tick_drawdown'] = .11
        self.assertEqual(selection.select_fold(rows, 'A')['selected'], 'C06')

    def test_no_qualified_candidate_selects_cash(self):
        r = selection.select_fold(training_rows(pnl=-100), 'A')
        self.assertEqual(r['selected'], 'CASH')
        self.assertFalse(r['demo_execution_ready']); self.assertFalse(r['orders_available'])

    def test_nonfinite_counts_or_unreconciled_values_reject(self):
        for field, value in [('max_tick_drawdown', float('nan')), ('closed_trades', True),
                             ('net_losing_trade_sum', -1), ('closed_trades', 59)]:
            rows = training_rows(); rows[0][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                selection.select_fold(rows, 'A')

    def test_future_calendar_and_extra_test_statistics_reject(self):
        for change in ('bounds', 'year', 'extra'):
            rows = training_rows()
            if change == 'bounds': rows[0]['training_end_exclusive'] = '2023-01-01T00:00:00+00:00'
            elif change == 'year': rows[0]['years']['2022'] = rows[0]['years']['2021']
            else: rows[0]['test_return'] = 100000
            with self.subTest(change=change), self.assertRaises(ValueError):
                selection.select_fold(rows, 'A')

    def test_fold_b_uses_only_declared_2021_2022_history(self):
        self.assertEqual(selection.select_fold(training_rows('B'), 'B')['test_year'], 2023)
        with self.assertRaises(ValueError): selection.select_fold(training_rows('A'), 'B')

    def test_fixture_is_exactly_reproducible_and_labelled_invented(self):
        bundle = wf.synthetic_fixture(self.root / 'data')
        for y in wf.YEARS:
            self.assertEqual((bundle.parent / f'{y}-ticks.csv.gz').read_bytes(), wf.fixture_bytes(y))
            self.assertEqual(wf.fixture_inventory(y)['ticks'], 3072)
            self.assertEqual(wf.fixture_inventory(y)['observed_hours'], 1024)
            self.assertIn('no market source', wf.provenance(y)['source'])
        with self.assertRaises(ValueError): list(wf.quotes(2025))

    def test_factory_dispatches_original_simulators_without_wrappers(self):
        for c in selection.CANDIDATES:
            expected = Experiment030Simulator if c in ('C07','C08') else Experiment028Simulator
            self.assertIs(type(wf.simulator(Config(), c, 0)), expected)
        with self.assertRaises(ValueError): wf.simulator(Config(), 'C04', 0)

    def test_market_role_rejects_before_iteration_or_output(self):
        bundle = wf.synthetic_fixture(self.root / 'data'); data = wf.load(bundle)
        data['synthetic'] = False; bundle.write_text(json.dumps(data))
        review = wf.load(bundle.parent / 'review.json')
        review['performance_evaluation_ready'] = True
        (bundle.parent / 'review.json').write_text(json.dumps(review))
        dest = self.root / 'blocked'
        with patch.object(wf.base, 'inventory', side_effect=AssertionError('Forbidden iteration')) as inventory:
            with self.assertRaisesRegex(ValueError, 'market input forbidden'): wf.freeze(bundle, dest)
            inventory.assert_not_called()
        self.assertFalse(dest.exists())

    def test_reserved_or_missing_year_rejects_before_iteration(self):
        bundle = wf.synthetic_fixture(self.root / 'data'); original = wf.load(bundle)
        for y in ('2025', '2026'):
            data = deepcopy(original); data['years'][y] = data['years'].pop('2023')
            bundle.write_text(json.dumps(data))
            with patch.object(wf.base, 'inventory', side_effect=AssertionError('Forbidden')) as iterator:
                with self.assertRaises(ValueError): wf.freeze(bundle, self.root / y)
                iterator.assert_not_called()

    def test_relabelled_or_modified_bytes_do_not_become_synthetic(self):
        bundle = wf.synthetic_fixture(self.root / 'data')
        path = bundle.parent / '2020-ticks.csv.gz'; path.write_bytes(b'unrelated provider bytes')
        meta_path = bundle.parent / '2020-provenance.json'; meta = wf.load(meta_path)
        meta['data_sha256'] = wf.sha256(path); meta_path.write_text(json.dumps(meta))
        with patch.object(wf.base, 'inventory', side_effect=AssertionError('Forbidden')) as iterator:
            with self.assertRaisesRegex(ValueError, 'reproducible invented'): wf.freeze(bundle, self.root / 'blocked')
            iterator.assert_not_called()

    def test_ledger_tampering_without_resealing_rejects(self):
        ledger, dest = self.frozen(); ledger['maximum_scenarios'] = 41
        (dest / 'ledger.json').write_text(json.dumps(ledger))
        with self.assertRaises(ValueError): wf.verify(dest)

    def test_resealed_role_approval_cost_and_window_changes_reject(self):
        original, dest = self.frozen()
        for change in ('role', 'approval', 'cost', 'window', 'candidate'):
            ledger = deepcopy(original)
            if change == 'role': ledger['synthetic'] = False
            elif change == 'approval': ledger['annual_eligible'] = True
            elif change == 'cost': ledger['configs']['base']['slippage_pips'] = 0
            elif change == 'window': ledger['windows']['A-test']['end_year'] = 2024
            else: ledger['candidates'][-1] = 'C04'
            self.rewrite_ledger(dest, ledger)
            with self.subTest(change=change), self.assertRaises(ValueError): wf.verify(dest)

    def test_changed_frozen_source_binding_rejects(self):
        ledger, dest = self.frozen()
        ledger['source_bindings']['src/forex_demo_lab/challenger_chronology_093.py'] = '0'*64
        self.rewrite_ledger(dest, ledger)
        with self.assertRaisesRegex(ValueError, 'source changed'): wf.verify(dest)

    def test_changed_input_and_archive_reject(self):
        ledger, dest = self.frozen()
        path = Path(ledger['entries']['2020']['data']); original = path.read_bytes()
        path.write_bytes(original+b'x')
        with self.assertRaisesRegex(ValueError, 'input or source changed'): wf.verify(dest)
        path.write_bytes(original)
        (dest / 'source.zip').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'archive changed'): wf.verify(dest)

    def test_warmup_and_account_initialization_are_common(self):
        ledger, dest = self.frozen(); rows = wf.replay_window(ledger, ledger['windows']['A-test'])
        self.assertEqual(len(rows), 10)
        for r in rows:
            self.assertEqual(r['warmup_hours'], 201)
            self.assertEqual(r['years']['2022']['starting_equity'], 10000)
            self.assertTrue(all(int(datetime.fromisoformat(t['opened']).timestamp()*1000) >= wf.bound(2022) for t in r['trades']))
            self.assertTrue(all(d['hour_start_ms'] >= wf.bound(2022) for d in r['flat_account_decisions']))

    def test_future_quote_is_rejected(self):
        ledger, dest = self.frozen(); window = ledger['windows']['A-test']
        ticks = list(wf.base.window_ticks(ledger, window))
        ticks.append(dict(sequence=len(ticks), time_msc=wf.bound(2023), bid=1.1, ask=1.1001))
        with patch.object(wf.base, 'window_ticks', return_value=iter(ticks)):
            with self.assertRaisesRegex(ValueError, 'future'): wf.replay_window(ledger, window)

    def test_insufficient_warmup_is_rejected(self):
        ledger, dest = self.frozen(); window = ledger['windows']['A-test']
        ticks = list(wf.base.window_ticks(ledger, window))[3:]
        ticks = [{**q, 'sequence': i} for i, q in enumerate(ticks)]
        with patch.object(wf.base, 'window_ticks', return_value=iter(ticks)):
            with self.assertRaisesRegex(ValueError, 'warmup'): wf.replay_window(ledger, window)

    def test_unsupported_window_and_direct_market_replay_reject(self):
        ledger, dest = self.frozen(); window = deepcopy(ledger['windows']['A-test'])
        window['end_year'] = 2024
        with self.assertRaises(ValueError): wf.replay_window(ledger, window)
        ledger['synthetic'] = False
        with patch.object(wf.base, 'window_ticks', side_effect=AssertionError('Forbidden')) as iterator:
            with self.assertRaises(ValueError): wf.replay_window(ledger, ledger['windows']['A-test'])
            iterator.assert_not_called()

    def test_direct_api_rejects_changed_inputs_costs_and_approval_before_iteration(self):
        original, dest = self.frozen()
        for change in ('cost', 'approval', 'bytes'):
            ledger = deepcopy(original)
            if change == 'cost': ledger['configs']['base']['slippage_pips'] = 0
            elif change == 'approval': ledger['annual_eligible'] = True
            else: Path(ledger['entries']['2020']['data']).write_bytes(b'not invented093')
            with patch.object(wf.base, 'window_ticks', side_effect=AssertionError('Forbidden')) as iterator:
                with self.subTest(change=change), self.assertRaises(ValueError):
                    wf.replay_window(ledger, ledger['windows']['A-test'])
                iterator.assert_not_called()

    def test_choice_exists_before_test_and_future_results_cannot_change_it(self):
        ledger, dest = self.frozen(); original = wf.replay_window; choices = {}
        def observed(l, w):
            fold = 'A' if w['start_year'] == 2022 else 'B' if w['start_year'] == 2023 else None
            if fold:
                choice = wf.load(dest / 'run' / (fold+'-selection.json'))
                self.assertEqual(len(choice['training_report_bindings']), 10)
                self.assertTrue(all('-training-' in n for n in choice['training_report_bindings']))
                choices[fold] = deepcopy(choice)
            rows = original(l, w)
            if fold:
                for r in rows: r['metrics']['net_return'] = 1000000
            return rows
        with patch.object(wf, 'replay_window', side_effect=observed): result = wf.run(dest)
        for fold in choices:
            self.assertEqual(wf.load(dest / 'run' / (fold+'-selection.json')), choices[fold])
        self.assertFalse(result['historical_positive_edge_screen_passed'])
        self.assertFalse(result['market_profitability_established'])
        with self.assertRaises((ValueError, AssertionError)): checker['check'](dest)

    def test_changed_choice_is_rejected_and_partial_run_cannot_repeat(self):
        ledger, dest = self.frozen(); original = wf.replay_window
        def observed(l, w):
            if w['start_year'] == 2022:
                path = dest / 'run/A-selection.json'; choice = wf.load(path)
                choice['training_inputs_sha256'] = '0'*64; path.write_text(json.dumps(choice))
            return original(l, w)
        with patch.object(wf, 'replay_window', side_effect=observed):
            with self.assertRaisesRegex(ValueError, 'Locked choice changed'): wf.run(dest)
        self.assertFalse((dest / 'run/summary.json').exists())
        with self.assertRaises(FileExistsError): wf.run(dest)

    def test_full_synthetic_accounting_and_repeat_protection(self):
        ledger, dest = self.frozen(); summary = wf.run(dest); check = checker['check'](dest)
        self.assertEqual(len(summary['scenario_bindings']), 40); self.assertEqual(check['choices'], 2)
        self.assertTrue(check['checks_passed'])
        for k, v in wf.APPROVALS.items(): self.assertIs(summary[k], v)
        with self.assertRaises(FileExistsError): wf.run(dest)

    def test_independent_checker_rejects_rebound_fee_drawdown_or_identity(self):
        ledger, dest = self.frozen(); summary = wf.run(dest)
        name = next(n for n in summary['scenario_bindings'] if wf.load(dest / 'run' / n)['trades'])
        path = dest / 'run' / name; original = wf.load(path)
        for field in ('fee', 'peak', 'identity', 'annual'):
            row = deepcopy(original)
            if field == 'fee': row['trades'][0]['commission'] += 1
            elif field == 'peak': row['peak_tick_equity'] += 1
            elif field == 'identity': row['candidate'] = 'C04'
            else: next(iter(row['years'].values()))['starting_equity'] += 1
            path.write_text(json.dumps(row)); changed = deepcopy(summary)
            changed['scenario_bindings'][name] = wf.sha256(path)
            (dest / 'run/summary.json').write_text(json.dumps(changed))
            with self.subTest(field=field), self.assertRaises((ValueError, AssertionError)): checker['check'](dest)

    def test_independent_first_arm_and_tampered_level(self):
        ledger, dest = self.frozen(); window = ledger['windows']['A-training']
        base = wf.bound(2020)
        ticks = [dict(sequence=i, time_msc=base+i*wf.HOUR, bid=1.125 if i<200 else 1.25,
                      ask=1.1251 if i<200 else 1.2501) for i in range(202)]
        ticks += [dict(sequence=202, time_msc=base+201*wf.HOUR+1, bid=1.27, ask=1.2701),
                  dict(sequence=203, time_msc=base+201*wf.HOUR+2, bid=1.0, ask=1.0001)]
        with patch.object(wf.base, 'window_ticks', return_value=iter(ticks)): rows = wf.replay_window(ledger, window)
        result = checker['check_window'](iter(ticks), rows, ledger['configs'], window)
        self.assertGreaterEqual(result['arms_checked'], 4)
        changed = deepcopy(rows)
        next(r for r in changed if r['candidate']=='C07')['protection_lineage'][0]['arm']['new_stop'] += .0001
        with self.assertRaises(AssertionError): checker['check_window'](iter(ticks), changed, ledger['configs'], window)

    def test_independent_checker_rejects_unmatched_or_duplicate_decisions(self):
        ledger, dest = self.frozen(); window = ledger['windows']['A-test']
        rows = wf.replay_window(ledger, window)
        ticks = list(wf.base.window_ticks(ledger, window))
        for change in ('future', 'duplicate'):
            changed = deepcopy(rows)
            row = next(r for r in changed if r['flat_account_decisions'])
            decision = deepcopy(row['flat_account_decisions'][0])
            if change == 'future': decision['hour_start_ms'] = wf.bound(2023)
            row['flat_account_decisions'].append(decision)
            with self.subTest(change=change), self.assertRaises(AssertionError):
                checker['check_window'](iter(ticks), changed, ledger['configs'], window)

    def test_restart_duplicate_and_gap_parity_for_every_challenger(self):
        for c in ('C05','C06','C07','C08'):
            for side in (1, -1):
                a, ticks = self.started_sim(c, side)
                price = a.position.entry + side*abs(a.position.entry-a.position.stop)*.7
                q = self.append(a, ticks, price if side == 1 else price-.0001)
                b = type(a).restore(a.checkpoint(), a.config, candidate=c, evaluation_start_ms=a.evaluation_start_ms)
                self.assertFalse(b.step_tick(q))
                gap = dict(sequence=len(ticks), time_msc=q['time_msc']+1, bid=.5 if side==1 else 2.0, ask=.5001 if side==1 else 2.0001)
                for sim in (a, b): sim.step_tick(gap); sim.finish()
                self.assertEqual(a.checkpoint(), b.checkpoint())
                self.assertTrue(a.paused); self.assertIsNone(a.position)

    def test_protection_financing_and_gap_are_not_guaranteed_profit(self):
        for c in ('C07','C08'):
            a, ticks = self.started_sim(c)
            price = a.position.entry+abs(a.position.entry-a.position.stop)*.7
            self.append(a, ticks, price); level = a.position.stop
            risk = a.pending_protection['initial_risk']
            self.append(a, ticks, price, ticks[-1]['time_msc']+86400000)
            self.assertEqual(a.position.stop, level); self.assertLess(a.position.swap, 0)
            self.append(a, ticks, .5)
            self.assertLess(a.trades[0]['net_pnl'], -risk)
            self.assertTrue(a.paused)

    def test_aggregate_position_limit_survives_challenger_restart(self):
        for c in ('C05','C06','C07','C08'):
            sim, ticks = self.started_sim(c)
            sim = type(sim).restore(sim.checkpoint(), sim.config, candidate=c, evaluation_start_ms=sim.evaluation_start_ms)
            position = sim.position
            sim.processing_tick = dict(sequence=len(ticks), time_msc=ticks[-1]['time_msc']+1, bid=1.25, ask=1.2501)
            sim._open(Bar(datetime.fromtimestamp(ticks[-1]['time_msc']/1000,timezone.utc),1.25,1.25,1.25,1.25,1), -1, .01)
            self.assertIs(sim.position, position)

    def test_loss_pause_survives_restart_and_blocks_new_entry(self):
        for c in ('C05','C06','C07','C08'):
            sim, ticks = self.started_sim(c); self.append(sim, ticks, .5)
            sim = type(sim).restore(sim.checkpoint(), sim.config, candidate=c, evaluation_start_ms=sim.evaluation_start_ms)
            sim.processing_tick = dict(sequence=len(ticks), time_msc=ticks[-1]['time_msc']+1, bid=1.25, ask=1.2501)
            sim._open(Bar(datetime.fromtimestamp(wf.bound(2020)/1000,timezone.utc),1.25,1.25,1.25,1.25,1), 1, .01)
            self.assertTrue(sim.paused); self.assertIsNone(sim.position)

    def test_c00_matches_original020_on_identical_quotes_and_costs(self):
        ledger, dest = self.frozen(); window = ledger['windows']['A-training']
        new = wf.replay_window(ledger, window); old = original_runner.replay_window(ledger, window)
        for cost in wf.COSTS:
            a = next(r for r in new if r['candidate']=='C00' and r['cost']==cost)
            b = next(r for r in old if r['candidate']=='C00' and r['cost']==cost)
            for key in ('trades','metrics','years','quarters','peak_tick_equity','max_tick_drawdown','period_closing_marks'):
                self.assertEqual(a[key], b[key], key)


if __name__ == '__main__': unittest.main()
