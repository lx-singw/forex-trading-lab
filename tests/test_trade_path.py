from dataclasses import asdict
from datetime import datetime, timezone
import copy
import unittest

from forex_demo_lab.model import Config
from forex_demo_lab.trade_path import TradePath


def iso(ms):
    return datetime.fromtimestamp(ms/1000, timezone.utc).isoformat()


def example(side=1, reason='stop_tick', start=1704067200000, end=None, swap=0):
    end = start+1000 if end is None else end
    c = asdict(Config())
    entry = 1.10012 if side == 1 else 1.09998
    stop, target = entry-side*.001, entry+side*.002
    raw = stop-side*.00002 if reason == 'stop_tick' else target+side*.01 if reason == 'target_tick' else entry+side*.0004
    price = target if reason == 'target_tick' else raw-side*.00002
    t = dict(opened=iso(start), closed=iso(end), entry=entry, stop=stop, target=target,
        side=side, lots=.1, exit=price, reason=reason, commission=.7, entry_commission=.35,
        swap=swap, gross_pnl=side*(price-entry)*10000)
    t['net_pnl'] = t['gross_pnl']-.7+swap
    ticks = [dict(sequence=0, time_msc=start, bid=1.1, ask=1.1001),
             dict(sequence=1, time_msc=end, bid=raw if side == 1 else raw-.0001,
                  ask=raw+.0001 if side == 1 else raw)]
    return t, dict(trade_index=0, entry_sequence=0, exit_sequence=1), c, ticks


def extract(args):
    t, f, c, ticks = args
    p = TradePath(t, f, c)
    for tick in ticks:
        p.step(tick)
    return p.finish()


class TradePathTests(unittest.TestCase):
    def test_long_short_include_spread_slippage_and_fees_once(self):
        for side in (-1, 1):
            r = extract(example(side))
            self.assertAlmostEqual(r['witnesses']['maximum']['net_pnl'], -2.1)
            self.assertAlmostEqual(r['witnesses']['endpoint']['net_pnl'], -11.1)
            self.assertLess(r['maximum_net_r'], 0)

    def test_target_overshoot_is_capped(self):
        for side in (-1, 1):
            r = extract(example(side, 'target_tick'))
            self.assertAlmostEqual(r['maximum_net_r'], 1.93)
            self.assertFalse(r['prior_one_r'])
            self.assertEqual(r['witnesses']['maximum']['sequence'], 1)

    def test_stop_gap_can_exceed_nominal_risk(self):
        t, f, c, ticks = example()
        ticks[-1].update(bid=1.09, ask=1.0901)
        t['exit'] = 1.08998
        t['gross_pnl'] = (t['exit']-t['entry'])*10000
        t['net_pnl'] = t['gross_pnl']-.7
        r = extract((t, f, c, ticks))
        self.assertLess(r['minimum_net_r'], -10)

    def test_wednesday_triple_financing_both_sides(self):
        start = int(datetime(2024, 1, 3, 22, tzinfo=timezone.utc).timestamp()*1000)
        for side, swap in ((1, -.9), (-1, -.45)):
            r = extract(example(side, 'end_of_sample', start, start+86400000, swap))
            self.assertAlmostEqual(r['witnesses']['endpoint']['accrued_swap'], swap)

    def test_weekend_and_gap_rollover(self):
        start = int(datetime(2024, 1, 5, 22, tzinfo=timezone.utc).timestamp()*1000)
        r = extract(example(1, 'end_of_sample', start, start+4*86400000, -.6))
        self.assertAlmostEqual(r['witnesses']['endpoint']['accrued_swap'], -.6)

    def test_tied_milliseconds_use_sequence_order(self):
        t, f, c, ticks = example()
        ticks[1]['time_msc'] = ticks[0]['time_msc']
        t['closed'] = t['opened']
        r = extract((t, f, c, ticks))
        self.assertEqual(r['quote_count'], 2)
        self.assertEqual(r['duration_hours'], 0)

    def test_missing_sequence_and_backward_timestamp_rejected(self):
        for kind in ('sequence', 'time_msc'):
            t, f, c, ticks = example()
            ticks[1][kind] = 3 if kind == 'sequence' else ticks[0][kind]-1
            with self.assertRaises(ValueError):
                extract((t, f, c, ticks))

    def test_missing_endpoint_rejected(self):
        t, f, c, ticks = example()
        p = TradePath(t, f, c)
        p.step(ticks[0])
        with self.assertRaises(ValueError):
            p.finish()

    def test_source_time_price_or_cost_mismatch_rejected(self):
        for key in ('entry', 'exit', 'commission', 'net_pnl', 'swap'):
            args = example()
            args[0][key] += .01
            with self.assertRaises(ValueError):
                extract(args)

    def test_invalid_risk_and_direction_rejected(self):
        for change in ({'stop': 1.10012}, {'side': 0}, {'lots': 0}):
            args = example()
            args[0].update(change)
            with self.assertRaises(ValueError):
                extract(args)

    def test_threshold_equality_and_first_extreme_tie(self):
        c = asdict(Config())
        c.update(contract_size=8, commission_per_lot_round_turn=0, slippage_pips=0)
        base = 1704067200000
        t = dict(opened=iso(base), closed=iso(base+4), entry=1.125, stop=1.0,
            target=1.375, exit=1.0, side=1, lots=1, reason='stop_tick', commission=0,
            entry_commission=0, swap=0, gross_pnl=-1, net_pnl=-1)
        f = dict(trade_index=0, entry_sequence=0, exit_sequence=4)
        ticks = [dict(sequence=i, time_msc=base+i, bid=p, ask=p) for i, p in enumerate((1.125, 1.1875, 1.25, 1.25, 1.0))]
        r = extract((t, f, c, ticks))
        self.assertEqual(r['witnesses']['half_r']['sequence'], 1)
        self.assertEqual(r['witnesses']['one_r']['sequence'], 2)
        self.assertEqual(r['witnesses']['maximum']['sequence'], 2)
        self.assertTrue(r['prior_one_r'])

    def test_trade_cannot_persist_past_target(self):
        t, f, c, ticks = example(reason='target_tick')
        f['exit_sequence'] = 2
        t['closed'] = iso(ticks[1]['time_msc']+1)
        ticks.append({**ticks[1], 'sequence': 2, 'time_msc': ticks[1]['time_msc']+1})
        with self.assertRaises(ValueError):
            extract((t, f, c, ticks))
