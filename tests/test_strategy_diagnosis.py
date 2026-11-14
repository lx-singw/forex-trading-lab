import copy
import unittest

from forex_demo_lab.strategy_diagnosis import diagnose, paired_paths

CONFIG = dict(contract_size=100000, commission_per_lot_round_turn=7,
              reward_risk=2, initial_equity=10000, slippage_pips=.2)


def fixture(side=1, reason='stop_tick'):
    t = dict(opened='2024-01-01T01:00:00+00:00', closed='2024-01-01T01:30:00+00:00',
        side=side, entry=1.1, stop=1.1-side*.001, target=1.1+side*.002,
        exit=1.1-side*.0012 if reason == 'stop_tick' else 1.1+side*.002,
        lots=.1, commission=.7, entry_commission=.35, swap=-.3, reason=reason)
    t['gross_pnl'] = side*(t['exit']-t['entry'])*10000
    t['net_pnl'] = t['gross_pnl']-1
    d = dict(hour_start_ms=1704070800000, side=side, stop_distance=.001,
             reason='selector_range:range_reentry',
             features=dict(efficiency_ratio=.1, selected_mode='range'))
    return dict(scenario='test', trades=[t], flat_account_decisions=[d],
        metrics=dict(closed_trades=1, signals_observed=1, spread_rejections=0,
                     commission=.7, swap=-.3, net_pnl=t['net_pnl'], net_return=t['net_pnl']/10000),
        equity=[dict(equity=10000+t['net_pnl'], paused=False)])


class DiagnosisTests(unittest.TestCase):
    def run_diagnosis(self, r):
        return diagnose(r, CONFIG, 'C04', 1704070800000)

    def test_long_short_risk_costs_and_quote_overshoot(self):
        for side in (-1, 1):
            row = self.run_diagnosis(fixture(side))['trades_detail'][0]
            self.assertEqual(row['match_status'], 'matched')
            self.assertAlmostEqual(row['initial_cash_risk'], 10)
            self.assertAlmostEqual(row['net_r'], -1.3)
            self.assertAlmostEqual(row['commission_r'], .07)
            self.assertAlmostEqual(row['financing_debit_r'], .03)
            self.assertAlmostEqual(row['observed_quote_overshoot_pips'], 1.8)

    def test_target_has_no_stop_overshoot(self):
        row = self.run_diagnosis(fixture(reason='target_tick'))['trades_detail'][0]
        self.assertAlmostEqual(row['net_r'], 1.9)
        self.assertEqual(row['stop_fill_overshoot_dollars'], 0)

    def test_missing_and_wrong_side_decisions_remain_unattributed(self):
        for wrong in ('missing', 'side'):
            r = fixture()
            if wrong == 'missing':
                r['flat_account_decisions'] = []
                r['metrics']['signals_observed'] = 0
            else:
                r['flat_account_decisions'][0]['side'] = -1
            d = self.run_diagnosis(r)
            self.assertEqual(d['match_counts'], {'missing': 1})
            self.assertEqual(d['trades_detail'][0]['branch'], 'unattributed')

    def test_duplicate_matching_decisions_are_ambiguous(self):
        r = fixture()
        r['flat_account_decisions'] *= 2
        r['metrics']['signals_observed'] = 2
        self.assertEqual(self.run_diagnosis(r)['match_counts'], {'ambiguous': 1})

    def test_accounting_commission_and_geometry_reject(self):
        for key in ('net_pnl', 'commission', 'target', 'gross_pnl'):
            r = fixture()
            r['trades'][0][key] += .1
            with self.assertRaises(ValueError):
                self.run_diagnosis(r)

    def test_zero_or_wrong_side_risk_rejects(self):
        for stop in (1.1, 1.101):
            r = fixture()
            r['trades'][0]['stop'] = stop
            with self.assertRaises(ValueError):
                self.run_diagnosis(r)

    def test_branch_boundary_and_neutral_signal_reject(self):
        r = fixture()
        r['flat_account_decisions'][0]['features']['efficiency_ratio'] = .35
        with self.assertRaises(ValueError):
            self.run_diagnosis(r)
        r = fixture()
        d = r['flat_account_decisions'][0]
        d['features'] = dict(efficiency_ratio=.3, selected_mode='neutral')
        d['reason'] = 'selector_neutral'
        with self.assertRaises(ValueError):
            self.run_diagnosis(r)

    def test_future_log_withholding_does_not_change_entry_attribution(self):
        r = fixture()
        original = self.run_diagnosis(r)['trades_detail']
        later = copy.deepcopy(r['flat_account_decisions'][0])
        later.update(hour_start_ms=1704074400000, side=0)
        r['flat_account_decisions'].append(later)
        self.assertEqual(self.run_diagnosis(r)['trades_detail'], original)

    def test_reentry_streak_and_changed_cost_path(self):
        r = fixture()
        t = copy.deepcopy(r['trades'][0])
        t.update(opened='2024-01-01T02:00:00+00:00', closed='2024-01-01T02:30:00+00:00')
        r['trades'].append(t)
        d = copy.deepcopy(r['flat_account_decisions'][0])
        d['hour_start_ms'] += 3600000
        r['flat_account_decisions'].append(d)
        for key in ('closed_trades', 'signals_observed', 'commission', 'swap', 'net_pnl', 'net_return'):
            r['metrics'][key] *= 2
        r['equity'][-1]['equity'] = 10000 + r['metrics']['net_pnl']
        result = self.run_diagnosis(r)
        self.assertEqual(result['longest_loss_streak'], 2)
        self.assertEqual(result['rapid_after_losses'], 1)
        self.assertEqual(result['rapid_same_side'], 1)
        pair = paired_paths(self.run_diagnosis(fixture()), result)
        self.assertEqual((pair['shared_entries'], pair['base_only_entries'], pair['adverse_only_entries']), (1, 0, 1))

    def test_no_trades_and_zero_signal(self):
        r = fixture()
        r['trades'] = []
        r['flat_account_decisions'] = []
        for key in r['metrics']:
            r['metrics'][key] = 0
        r['equity'][0]['equity'] = 10000
        self.assertIsNone(self.run_diagnosis(r)['mean_net_r'])

    def test_overlapping_trades_reject(self):
        r = fixture()
        r['trades'] *= 2
        with self.assertRaises(ValueError):
            self.run_diagnosis(r)

    def test_trade_cannot_reuse_a_decision(self):
        r = fixture()
        t = copy.deepcopy(r['trades'][0])
        t.update(opened='2024-01-01T01:40:00+00:00', closed='2024-01-01T01:50:00+00:00')
        r['trades'].append(t)
        with self.assertRaises(ValueError):
            self.run_diagnosis(r)
