from copy import deepcopy
import unittest

from forex_demo_lab.selection import select_fold
from forex_demo_lab.strategies import CANDIDATES


def rows():
    return [{'candidate': c, 'cost': cost,
             'training_start': '2020-01-01T00:00:00+00:00',
             'training_end_exclusive': '2022-01-01T00:00:00+00:00',
             'years': {'2020': {'net_pnl': 100, 'starting_equity': 10000, 'closed_trades': 30},
                       '2021': {'net_pnl': 100, 'starting_equity': 10100, 'closed_trades': 30}},
             'quarters': {f'{y}-Q{q}': 25 for y in (2020, 2021) for q in (1, 2, 3, 4)},
             'closed_trades': 60, 'net_winning_trade_sum': 1200,
             'net_losing_trade_sum': -1000, 'max_tick_drawdown': .05}
            for c in CANDIDATES for cost in ('base', 'adverse')]


class SelectionTests(unittest.TestCase):
    def test_tie_break_and_input_order_are_deterministic(self):
        a = select_fold(rows(), 'A')
        self.assertEqual(a['selected'], 'C00')
        self.assertEqual(a, select_fold(list(reversed(rows())), 'A'))
        self.assertFalse(a['demo_execution_ready'])

    def test_all_failed_candidates_select_cash(self):
        r = rows()
        for v in r: v['max_tick_drawdown'] = .10001
        self.assertEqual(select_fold(r, 'A')['selected'], 'CASH')

    def test_rank_uses_weaker_adverse_year_not_largest_total_profit(self):
        r = rows()
        for v in r[:2]:
            v['years']['2020']['net_pnl'] = 1000
            v['years']['2021'].update(net_pnl=50, starting_equity=11000)
            for q in (1, 2, 3, 4):
                v['quarters'][f'2020-Q{q}'] = 250
                v['quarters'][f'2021-Q{q}'] = 12.5
            v['net_winning_trade_sum'] = 2050
        self.assertEqual(select_fold(r, 'A')['selected'], 'C01')

    def test_both_costs_must_pass(self):
        r = rows(); r[0]['max_tick_drawdown'] = .11
        result = select_fold(r, 'A')
        self.assertFalse(result['candidates']['C00']['qualified'])
        self.assertEqual(result['selected'], 'C01')

    def test_insufficient_trades_do_not_win_on_apparent_profit(self):
        r = rows()
        for v in r:
            v['closed_trades'] = 2
            for y in v['years'].values(): y['closed_trades'] = 1
        self.assertEqual(select_fold(r, 'A')['selected'], 'CASH')

    def test_missing_or_duplicate_candidate_is_an_error_not_abstention(self):
        with self.assertRaises(ValueError): select_fold(rows()[:-1], 'A')
        r = rows(); r[-1] = deepcopy(r[0])
        with self.assertRaises(ValueError): select_fold(r, 'A')

    def test_later_year_cannot_enter_earlier_fold(self):
        r = rows(); r[0]['training_end_exclusive'] = '2023-01-01T00:00:00+00:00'
        with self.assertRaisesRegex(ValueError, 'future'): select_fold(r, 'A')
        r = rows(); r[0]['quarters']['2022-Q1'] = 1000
        with self.assertRaisesRegex(ValueError, 'future'): select_fold(r, 'A')
        with self.assertRaises(ValueError): select_fold(rows(), 'B')

    def test_inconsistent_and_nonfinite_statistics_rejected(self):
        for key, value in [('net_winning_trade_sum', 9999), ('closed_trades', 61),
                           ('max_tick_drawdown', float('nan')), ('max_tick_drawdown', True)]:
            r = rows(); r[0][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError): select_fold(r, 'A')
        r = rows(); r[0]['years']['2021']['starting_equity'] = 10000
        with self.assertRaises(ValueError): select_fold(r, 'A')

    def test_quarter_consistency_and_positive_quarter_gate(self):
        r = rows(); r[0]['quarters']['2020-Q1'] = 200
        with self.assertRaises(ValueError): select_fold(r, 'A')
        r = rows()
        for v in r:
            for y in (2020, 2021):
                for q in (1, 2, 3): v['quarters'][f'{y}-Q{q}'] = -10
                v['quarters'][f'{y}-Q4'] = 130
        self.assertEqual(select_fold(r, 'A')['selected'], 'CASH')

    def test_profit_factor_and_drawdown_boundaries(self):
        r = rows()
        for v in r:
            v.update(net_winning_trade_sum=2200, net_losing_trade_sum=-2000, max_tick_drawdown=.10)
        self.assertEqual(select_fold(r, 'A')['selected'], 'C00')
        for v in r: v.update(net_winning_trade_sum=3200, net_losing_trade_sum=-3000)
        self.assertEqual(select_fold(r, 'A')['selected'], 'CASH')

    def test_undefined_profit_factor_does_not_qualify(self):
        r = rows()
        for v in r: v.update(net_winning_trade_sum=200, net_losing_trade_sum=0)
        self.assertEqual(select_fold(r, 'A')['selected'], 'CASH')
