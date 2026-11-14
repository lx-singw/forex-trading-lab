from copy import deepcopy
import unittest
from forex_demo_lab.execution_audit import compare,reference,scenarios


class ExecutionAuditTests(unittest.TestCase):
    def setUp(self):self.cases={c['case_id']:c for c in scenarios()}

    def test_gap_costs_and_swaps_reconcile_hand_calculated_money(self):
        for name,loss in (('long',-226.60),('short',-225.61)):
            final=self.cases[name+'_rollover_stop_gap_tick']['expected']['final']
            self.assertAlmostEqual(final['trades'][0]['net_pnl'],loss)
            self.assertAlmostEqual(final['balance'],10000+loss)
            self.assertTrue(final['paused'])
            self.assertGreater(-loss,100)

    def test_target_peak_is_capped_at_executable_fill_not_overshoot(self):
        for name in ('long','short'):
            case=self.cases[name+'_target_overshoot_tick'];final=case['expected']['final']
            self.assertAlmostEqual(final['balance'],10042.46)
            self.assertAlmostEqual(final['peak_tick_equity'],10042.46)
            self.assertAlmostEqual(final['max_tick_drawdown'],.000341)

    def test_swap_alone_relatches_on_reset_and_recovery_does_not_unpause(self):
        for name,swap in (('long',-2.07),('short',-1.035)):
            trace=self.cases[name+'_swap_pause_recovery_tick']['expected']['trace']
            self.assertFalse(trace[1]['paused']);self.assertTrue(trace[2]['paused'])
            self.assertTrue(trace[3]['paused']);self.assertEqual(trace[2]['position']['swap'],swap)
            self.assertGreater(trace[3]['equity'],trace[3]['daily_reference'])

    def test_skipped_rollovers_have_five_charge_units_not_seven(self):
        for name,net in (('long',-.72),('short',-.57)):
            case=self.cases[name+'_skipped_rollovers_tick']
            self.assertEqual(sum(e['rollover_units'] for e in case['events']),5)
            self.assertAlmostEqual(case['expected']['final']['trades'][0]['net_pnl'],net)

    def test_gap_pause_blocks_reentry_until_next_day_and_size_falls(self):
        for name in ('long','short'):
            trace=self.cases[name+'_gap_pause_next_day_tick']['expected']['trace']
            self.assertEqual(trace[1]['position']['lots'],.22)
            self.assertIsNone(trace[3]['position']);self.assertTrue(trace[3]['paused'])
            self.assertFalse(trace[4]['paused']);self.assertEqual(trace[5]['position']['lots'],.21)

    def test_cost_pause_does_not_suppress_exit_or_clear_on_profit(self):
        trace=self.cases['long_entry_cost_pause_target_tick']['expected']['trace']
        self.assertTrue(trace[1]['paused']);self.assertIsNotNone(trace[1]['position'])
        self.assertTrue(trace[2]['paused']);self.assertIsNone(trace[2]['position'])
        self.assertEqual(trace[2]['trades'][0]['reason'],'target_tick')
        self.assertTrue(trace[3]['paused']);self.assertIsNone(trace[3]['position'])

    def test_checker_rejects_changed_cost_direction_volume_pause_and_inventory(self):
        expected=self.cases['long_rollover_stop_gap_tick']['expected']
        for field,value in (('balance',9999),('paused',False),('max_tick_drawdown',0)):
            changed=deepcopy(expected);changed['final'][field]=value
            with self.assertRaises(ValueError):compare(changed,expected)
        for field,value in (('side',-1),('lots',.23),('commission',0),('swap',0)):
            changed=deepcopy(expected);changed['final']['trades'][0][field]=value
            with self.assertRaises(ValueError):compare(changed,expected)
        changed=deepcopy(expected);changed['trace'].pop()
        with self.assertRaises(ValueError):compare(changed,expected)

    def test_future_or_missing_input_bounds_and_bad_annotations_rejected(self):
        original=self.cases['long_rollover_stop_gap_tick']
        for kind in ('future','missing','wrong_pause'):
            changed=deepcopy(original)
            if kind=='future':changed['ticks'][0]['time_msc']+=366*24*3600000
            elif kind=='missing':changed['events'].pop()
            else:changed['events'][2]['paused']=False
            with self.assertRaises(ValueError):reference(changed)


if __name__=='__main__':unittest.main()
