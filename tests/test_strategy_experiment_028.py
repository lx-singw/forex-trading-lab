from datetime import datetime, timedelta, timezone
import json
import unittest

from forex_demo_lab.execution_metrics import ExecutableEquityResearchTickSimulator
from forex_demo_lab.model import Bar, Config
from forex_demo_lab.strategies import decide
from forex_demo_lab.strategy_experiment_028 import decision, Experiment028Simulator

BASE = datetime(2024, 1, 1, tzinfo=timezone.utc)


def bars(closes):
    return [Bar(BASE+timedelta(hours=i), c, c, c, c, 1) for i, c in enumerate(closes)]


def quote(i, price, ms=None):
    return dict(sequence=i, time_msc=int(BASE.timestamp()*1000)+i*3600000 if ms is None else ms,
                bid=price, ask=price+.0001)


class ChallengerTests(unittest.TestCase):
    def test_controls_are_exact_original_decisions(self):
        history = bars([1.125]*200+[1.25])
        for c in ('C00', 'C02', 'C04'):
            self.assertEqual(decision(c, history, Config()), decide(c, history, Config()))

    def test_trend_only_agrees_with_existing_trend_branch(self):
        history = bars([1.125]*200+[1.25])
        old = decide('C04', history, Config())
        new = decision('C05', history, Config())
        self.assertEqual(old.features['selected_mode'], 'trend')
        self.assertEqual((new.side, new.stop_distance, new.features), (old.side, old.stop_distance, old.features))
        self.assertEqual(new.side, 1)

    def test_range_and_zero_path_abstain(self):
        for history in (bars([1.125]*201), bars([1.125]*180+[1.125+(i%2)*.01 for i in range(21)])):
            result = decision('C05', history, Config())
            self.assertEqual(result.side, 0)
            self.assertTrue(result.reason.startswith('trend_only_abstain'))

    def test_common_warmup_and_unknown_candidate(self):
        for c in ('C05', 'C06'):
            self.assertEqual(decision(c, bars([1.125]*200), Config()).reason, 'warmup')
        with self.assertRaises(ValueError):
            decision('C07', bars([1.125]*201), Config())

    def test_confirmed_long_and_short(self):
        for closes, side in (([1.125]*200+[1.25], 1), ([1.125]*200+[1.0], -1)):
            result = decision('C06', bars(closes), Config())
            self.assertEqual(result.side, side)
            self.assertEqual(result.reason, 'confirmed_breakout')

    def test_breakout_direction_disagreement(self):
        history = bars([1.25]*151+[1.125]*49+[1.1875])
        self.assertEqual(decide('C02', history, Config()).side, 1)
        result = decision('C06', history, Config())
        self.assertEqual(result.side, 0)
        self.assertEqual(result.features['slow_direction'], -1)

    def test_sma_equality_abstains_on_valid_breakout(self):
        history = bars([1.0]+[1.125]*3+[1.0]*147+[1.0]*49+[1.125])
        self.assertEqual(decide('C02', history, Config()).side, 1)
        result = decision('C06', history, Config())
        self.assertEqual(result.features['sma50'], result.features['sma200'])
        self.assertEqual(result.side, 0)

    def test_reversed_closed_history_rejected(self):
        for c in ('C05', 'C06'):
            with self.assertRaises(ValueError):
                decision(c, list(reversed(bars([1.125]*201))), Config())

    def test_future_quotes_cannot_change_earlier_decisions(self):
        prefix = [quote(i, 1.125 if i < 200 else 1.25) for i in range(202)]
        for candidate in ('C05', 'C06'):
            a = Experiment028Simulator(Config(), candidate)
            b = Experiment028Simulator(Config(), candidate)
            for t in prefix:
                a.step_tick(t)
                b.step_tick(t)
            earlier = list(a.decision_log)
            b.step_tick(quote(202, 1.0))
            boundary = prefix[-1]['time_msc']//3600000*3600000
            self.assertEqual(earlier, [d for d in b.decision_log if d['hour_start_ms'] <= boundary])

    def test_restart_duplicate_and_fill_lineage(self):
        config = Config()
        ticks = [quote(i, 1.125 if i < 200 else 1.25 if i == 200 else 1.25 if i == 201 else 1.0) for i in range(203)]
        for candidate in ('C05', 'C06'):
            a = Experiment028Simulator(config, candidate)
            for t in ticks[:202]:
                a.step_tick(t)
            b = Experiment028Simulator.restore(a.checkpoint(), config, candidate=candidate, evaluation_start_ms=0)
            self.assertFalse(b.step_tick(ticks[201]))
            for obj in (a, b):
                obj.step_tick(ticks[202])
                obj.finish()
            self.assertEqual(a.trades, b.trades)
            self.assertEqual(a.fill_lineage, b.fill_lineage)
            self.assertEqual(a.metrics(), b.metrics())
            self.assertEqual(a.fill_lineage[0]['entry_sequence'], 201)
            self.assertEqual(a.fill_lineage[0]['exit_sequence'], 202)

    def test_legacy_and_wrong_candidate_checkpoint_rejected(self):
        config = Config()
        legacy = ExecutableEquityResearchTickSimulator(config).checkpoint()
        with self.assertRaises(ValueError):
            Experiment028Simulator.restore(legacy, config, candidate='C00', evaluation_start_ms=0)
        fresh = Experiment028Simulator(config, 'C05').checkpoint()
        with self.assertRaises(ValueError):
            Experiment028Simulator.restore(fresh, config, candidate='C06', evaluation_start_ms=0)
        payload = json.loads(fresh)
        payload['payload']['state']['execution_metric_version'] = 'legacy'
        with self.assertRaises(ValueError):
            Experiment028Simulator.restore(json.dumps(payload), config, candidate='C05', evaluation_start_ms=0)

    def open_manually(self, side=1, distance=.01, spread=1):
        sim = Experiment028Simulator(Config(), 'C06')
        sim.processing_tick = quote(0, 1.1)
        sim._open(Bar(BASE, 1.1, 1.1, 1.1, 1.1, spread), side, distance)
        sim.processing_tick = None
        return sim

    def test_position_limit_sizing_and_spread_guard(self):
        sim = self.open_manually()
        old = sim.position
        sim.processing_tick = quote(1, 1.1)
        sim._open(Bar(BASE, 1.1, 1.1, 1.1, 1.1, 1), -1, .01)
        self.assertIs(sim.position, old)
        budget = old.lots*(.01*100000+Config().slippage_pips*.0001*100000+7)
        self.assertLessEqual(budget, 25)
        self.assertIsNone(self.open_manually(spread=3).position)

    def test_target_overshoot_does_not_create_phantom_peak(self):
        sim = self.open_manually()
        sim.step_tick(quote(0, 1.2))
        self.assertEqual(sim.trades[0]['reason'], 'target_tick')
        self.assertAlmostEqual(sim.peak_tick_equity, sim.balance)
        self.assertAlmostEqual(sim.max_tick_drawdown, 0)

    def test_gap_loss_and_daily_entry_pause(self):
        sim = self.open_manually(distance=.001)
        sim.step_tick(quote(0, 1.0))
        self.assertEqual(sim.trades[0]['reason'], 'stop_tick')
        self.assertLess(sim.trades[0]['net_pnl'], -25)
        self.assertTrue(sim.paused)
        sim.processing_tick = quote(1, 1.0)
        sim._open(Bar(BASE, 1.0, 1.0, 1.0, 1.0, 1), 1, .001)
        self.assertIsNone(sim.position)
