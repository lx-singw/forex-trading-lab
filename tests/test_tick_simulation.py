from dataclasses import replace
from datetime import datetime, timezone
import unittest

from forex_demo_lab.model import Config
from forex_demo_lab.simulation import Position
from forex_demo_lab.tick_simulation import TickSimulator

START=int(datetime(2024,1,3,tzinfo=timezone.utc).timestamp()*1000)


def quote(sequence, milliseconds, bid=1.1, ask=None):
    return {"sequence":sequence,"time_msc":START+milliseconds,"bid":bid,"ask":bid+.0001 if ask is None else ask}


class TickSimulationTests(unittest.TestCase):
    def config(self, **kw):
        return replace(Config(),fast=1,slow=3,atr_period=1,leverage=10,**kw)

    def warmup(self, spread=.0001):
        sim=TickSimulator(self.config())
        for i,bid in enumerate([1.1000,1.0999,1.0998,1.1001]):
            sim.step_tick(quote(i,i*3600000,bid,bid+spread))
        return sim

    def position(self, side=1, stop=1.099, target=1.102):
        sim=TickSimulator(self.config())
        sim.step_tick(quote(0,0))
        sim.position=Position(side,.1,1.1,stop,target,datetime.fromtimestamp(START/1000,timezone.utc).isoformat(),0)
        return sim

    def test_closed_hour_signal_actual_entry_and_sizing_cost_cap(self):
        sim=self.warmup()
        self.assertIsNone(sim.position)
        sim.step_tick(quote(4,4*3600000+123,1.1001,1.1002))
        p=sim.position
        self.assertIsNotNone(p)
        self.assertAlmostEqual(p.entry,1.10022)
        self.assertTrue(p.opened.endswith(".123000+00:00"))
        risk=(abs(p.entry-p.stop)+sim.config.slippage_pips*.0001)*p.lots*100000+p.lots*7
        self.assertLessEqual(risk,25+1e-9)
        original=p
        sim.step_tick(quote(5,4*3600000+200,1.1001))
        self.assertIs(sim.position,original)

    def test_wide_opening_spread_never_retried_on_later_narrow_quote(self):
        sim=self.warmup()
        sim.step_tick(quote(4,4*3600000,1.1001,1.1004))
        sim.step_tick(quote(5,4*3600000+1,1.1001,1.10011))
        self.assertIsNone(sim.position)
        self.assertEqual(sim.spread_rejections,1)

    def test_missing_hour_discards_stale_signal(self):
        sim=self.warmup()
        sim.step_tick(quote(4,5*3600000,1.1001))
        self.assertIsNone(sim.position)

    def test_same_millisecond_exit_sequence_target_before_later_stop(self):
        sim=self.position()
        sim.step_tick(quote(1,1,1.1025))
        sim.step_tick(quote(2,1,1.0980))
        self.assertEqual(sim.trades[0]["reason"],"target_tick")
        self.assertEqual(sim.trades[0]["exit"],1.102)
        self.assertEqual(len(sim.trades),1)

    def test_stop_gap_is_actual_quote_plus_adverse_slippage(self):
        sim=self.position()
        sim.step_tick(quote(1,3*3600000,1.09))
        self.assertAlmostEqual(sim.trades[0]["exit"],1.08998)
        self.assertLess(sim.trades[0]["net_pnl"],-100)
        self.assertTrue(sim.paused)

    def test_short_exits_on_ask_not_bid(self):
        sim=self.position(-1,1.101,1.098)
        sim.step_tick(quote(1,1,1.1005,1.1011))
        self.assertEqual(sim.trades[0]["reason"],"stop_tick")
        self.assertAlmostEqual(sim.trades[0]["exit"],1.10112)

    def test_open_loss_pause_survives_price_recovery(self):
        sim=self.position(1,1.08,1.12)
        sim.step_tick(quote(1,1,1.089))
        self.assertTrue(sim.paused)
        sim.step_tick(quote(2,2,1.1))
        self.assertTrue(sim.paused)
        self.assertGreater(sim.metrics()["max_tick_drawdown"],.01)

    def test_restart_mid_hour_position_and_duplicate_replay(self):
        sim=self.warmup()
        sim.step_tick(quote(4,4*3600000+1,1.1001))
        checkpoint=sim.checkpoint()
        restored=TickSimulator.restore(checkpoint,sim.config)
        self.assertFalse(restored.step_tick(quote(4,4*3600000+1,1.1001)))
        for t in [quote(5,4*3600000+2,1.099),quote(6,5*3600000,1.1005)]:
            sim.step_tick(t);restored.step_tick(t)
        sim.finish();restored.finish()
        self.assertEqual(sim.checkpoint(),restored.checkpoint())
        self.assertAlmostEqual(sum(t["net_pnl"] for t in sim.trades),sim.balance-10000)

    def test_conflicting_duplicate_invalid_quotes_and_missing_sequence_rejected(self):
        sim=self.position()
        for t in [quote(0,0,1.101),quote(2,1),quote(1,-1),quote(1,1,1.2,1.1),quote(1,1,float("nan"))]:
            with self.subTest(t=t),self.assertRaises(ValueError):sim.step_tick(t)

    def test_future_prices_cannot_change_prior_entry(self):
        a=self.warmup();b=self.warmup()
        opening=quote(4,4*3600000,1.1001)
        a.step_tick(opening);b.step_tick(opening)
        entry=a.position.entry;size=a.position.lots
        a.step_tick(quote(5,4*3600000+1,1.105))
        b.step_tick(quote(5,4*3600000+1,1.095))
        self.assertEqual(a.trades[0]["entry"],entry)
        self.assertEqual(b.trades[0]["entry"],entry)
        self.assertEqual(a.trades[0]["lots"],size)
        self.assertEqual(b.trades[0]["lots"],size)

    def test_rollover_and_final_short_liquidation_use_actual_quote(self):
        sim=self.position(-1,1.2,1.0)
        sim.step_tick(quote(1,24*3600000,1.1,1.1004))
        self.assertAlmostEqual(sim.position.swap,-.45) # Wednesday tripled
        sim.finish()
        self.assertAlmostEqual(sim.trades[0]["exit"],1.10042)
        self.assertAlmostEqual(sim.balance,10000+sim.trades[0]["net_pnl"])
        before=sim.checkpoint();sim.finish();self.assertEqual(before,sim.checkpoint())
