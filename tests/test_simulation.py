from dataclasses import replace
import json
import unittest
from unittest.mock import patch

from forex_demo_lab.model import Config
from forex_demo_lab.simulation import Simulator
from test_model import candle


class SimulationTests(unittest.TestCase):
    def setUp(self):
        self.sim = Simulator(Config())

    def open_position(self, side=1, distance=.001):
        self.sim.step(candle())
        self.sim._open(candle(1), side, distance)
        self.assertIsNotNone(self.sim.position)
        return self.sim.position

    def test_single_position_ignores_new_entry(self):
        original = self.open_position()
        balance = self.sim.balance
        self.sim._open(candle(1), -1, .001)
        self.assertIs(self.sim.position, original)
        self.assertEqual(self.sim.balance, balance)

    def test_spread_and_stop_geometry_reject_entry(self):
        for bar, distance in [(candle(spread=2), .001), (candle(), .0001), (candle(), 1)]:
            self.sim._open(bar, 1, distance)
            self.assertIsNone(self.sim.position)

    def test_long_both_boundaries_touched_uses_stop_and_costs(self):
        p = self.open_position()
        self.sim.step(candle(1, high=1.11, low=1.09))
        trade = self.sim.trades[0]
        self.assertEqual(trade["reason"], "stop")
        self.assertAlmostEqual(trade["exit"], p.stop - .00002)
        self.assertAlmostEqual(trade["net_pnl"], -(0.00102*100000+7)*p.lots)
        self.assertLessEqual(-trade["net_pnl"], 25)
        self.assertAlmostEqual(self.sim.balance, 10000 + trade["net_pnl"])

    def test_short_stop_uses_ask_and_adverse_slippage(self):
        p = self.open_position(-1)
        # Bid never reaches stop, ask does.
        self.sim.step(candle(1, high=p.stop-.00005, low=1.0998))
        self.assertEqual(self.sim.trades[0]["reason"], "stop")
        self.assertAlmostEqual(self.sim.trades[0]["exit"], p.stop+.00002)

    def test_gap_stop_can_exceed_budget_and_pause_day(self):
        p = self.open_position()
        self.sim.step(candle(72, opening=1.09, high=1.091, low=1.089, close=1.09))
        trade = self.sim.trades[0]
        self.assertEqual(trade["reason"], "stop_gap")
        self.assertAlmostEqual(trade["exit"], 1.08998)
        self.assertGreater(-trade["net_pnl"], 25)
        self.assertTrue(self.sim.paused)
        self.assertEqual(trade["lots"], p.lots)

    def test_short_gap_stop(self):
        self.open_position(-1)
        self.sim.step(candle(72, opening=1.12, high=1.121, low=1.119, close=1.12))
        self.assertEqual(self.sim.trades[0]["reason"], "stop_gap")
        self.assertAlmostEqual(self.sim.trades[0]["exit"], 1.12012)

    def test_gap_target_does_not_credit_improvement(self):
        p = self.open_position()
        self.sim.step(candle(72, opening=1.12, high=1.121, low=1.119, close=1.12))
        self.assertEqual(self.sim.trades[0]["reason"], "target_gap")
        self.assertEqual(self.sim.trades[0]["exit"], p.target)

    def test_short_target_requires_ask_to_reach_it(self):
        p = self.open_position(-1)
        self.sim.step(candle(1, high=1.1001, low=p.target-.00005))
        self.assertIsNotNone(self.sim.position)
        self.sim.step(candle(2, high=1.1001, low=p.target-.0002))
        self.assertEqual(self.sim.trades[0]["reason"], "target")

    def test_duplicate_and_reordered_bars(self):
        self.sim.step(candle())
        original = self.sim.checkpoint()
        self.assertFalse(self.sim.step(candle()))
        self.assertEqual(self.sim.checkpoint(), original)
        with self.assertRaises(ValueError):
            self.sim.step(candle(close=1.1001))
        with self.assertRaises(ValueError):
            self.sim.step(candle(-1))

    def test_pause_latches_across_recovery_and_restart(self):
        self.sim.step(candle())
        self.sim.observe_loss(9900)
        self.sim.observe_loss(10010)
        restored = Simulator.restore(self.sim.checkpoint(), self.sim.config)
        self.assertTrue(restored.paused)
        restored._open(candle(1), 1, .001)
        self.assertIsNone(restored.position)
        restored.step(candle(24))
        self.assertFalse(restored.paused)

    def test_open_loss_latches_daily_pause_even_after_recovery(self):
        self.sim = Simulator(Config(daily_loss_fraction=.001))
        self.open_position(distance=.01)
        self.sim.step(candle(1, low=1.094, high=1.1005))
        self.assertIsNotNone(self.sim.position)
        self.assertTrue(self.sim.paused)
        self.assertGreater(self.sim.last_equity, 9990)

    def test_daily_boundary_uses_configured_timezone(self):
        self.sim = Simulator(Config(broker_timezone="Africa/Johannesburg"))
        self.sim.step(candle(20))
        self.sim.observe_loss(9899)
        self.sim.step(candle(21))
        self.assertTrue(self.sim.paused)
        self.sim.step(candle(22))
        self.assertFalse(self.sim.paused)

    def test_rollover_triple_and_weekend(self):
        p = self.open_position(distance=.01)
        self.sim.step(candle(24))
        self.assertAlmostEqual(p.swap, -3*p.lots)
        self.sim.step(candle(72))  # Monday+Tuesday+Wednesday triple = 5
        self.assertAlmostEqual(p.swap, -3*p.lots*5)
        self.sim.step(candle(168))  # 7 charges, none on Sat/Sun
        self.assertAlmostEqual(p.swap, -3*p.lots*7)

    def test_checkpoint_open_position_resume_matches_uninterrupted(self):
        self.open_position(distance=.01)
        self.sim.step(candle(1))
        restored = Simulator.restore(self.sim.checkpoint(), self.sim.config)
        self.assertFalse(restored.step(candle(1)))
        for hour in (2, 24, 48, 72):
            bar = candle(hour)
            self.sim.step(bar)
            restored.step(bar)
        self.sim.finish()
        restored.finish()
        self.assertEqual(self.sim.checkpoint(), restored.checkpoint())
        self.assertAlmostEqual(sum(t["net_pnl"] for t in self.sim.trades), self.sim.balance-10000)

    def test_corrupt_or_wrong_config_checkpoint_fails_closed(self):
        state = self.sim.checkpoint()
        with self.assertRaises(ValueError):
            Simulator.restore("broken", self.sim.config)
        corrupt = json.loads(state)
        corrupt["payload"]["state"]["balance"] = 20000
        with self.assertRaises(ValueError):
            Simulator.restore(json.dumps(corrupt), self.sim.config)
        with self.assertRaises(ValueError):
            Simulator.restore(state, replace(self.sim.config, slippage_pips=.5))

    def test_signal_uses_previous_bars_and_skips_gap(self):
        self.sim.step(candle())
        seen = []
        def decision(history, config):
            seen.extend(history)
            return 1, .01
        with patch("forex_demo_lab.simulation.signal", side_effect=decision):
            self.sim.step(candle(1))
            self.assertEqual(len(seen), 1)
            self.assertEqual(seen[0].time, candle().time)
            self.assertIsNotNone(self.sim.position)
        other = Simulator(Config())
        other.step(candle())
        with patch("forex_demo_lab.simulation.signal", return_value=(1, .01)) as decision:
            other.step(candle(72))
            decision.assert_not_called()
            self.assertIsNone(other.position)

    def test_repeated_signals_never_stack_or_reenter_exit_bar(self):
        self.sim.step(candle())
        with patch("forex_demo_lab.simulation.signal", return_value=(1, .001)) as decision:
            self.sim.step(candle(1))
            p = self.sim.position
            self.sim.step(candle(2))
            self.assertIs(self.sim.position, p)
            self.sim.step(candle(3, low=1.09))
            self.assertEqual(len(self.sim.trades), 1)
            self.assertIsNone(self.sim.position)
            self.assertEqual(decision.call_count, 1)

    def test_repeated_losses_pause_entries_and_reduce_size(self):
        self.sim.step(candle())
        with patch("forex_demo_lab.simulation.signal", return_value=(1, .001)):
            for hour in range(1, 20):
                self.sim.step(candle(hour, low=1.098))
        self.assertTrue(self.sim.paused)
        self.assertGreaterEqual(len(self.sim.trades), 4)
        lots = [t["lots"] for t in self.sim.trades]
        self.assertEqual(lots, sorted(lots, reverse=True))
        self.assertLess(len(lots), 19)

    def test_finish_is_idempotent_and_costs_liquidation(self):
        self.open_position()
        self.sim.finish()
        self.assertEqual(self.sim.trades[0]["reason"], "end_of_sample")
        self.assertLess(self.sim.balance, 10000)
        state = self.sim.checkpoint()
        self.sim.finish()
        self.assertEqual(state, self.sim.checkpoint())
        with self.assertRaises(ValueError):
            self.sim.step(candle(2))


if __name__ == "__main__":
    unittest.main()
