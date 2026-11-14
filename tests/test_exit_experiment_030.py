from dataclasses import replace
from datetime import datetime, timezone
import unittest

from forex_demo_lab.model import Bar, Config
from forex_demo_lab.exit_experiment_030 import Experiment030Simulator, protection
from forex_demo_lab.strategy_experiment_028 import Experiment028Simulator

BASE = 1704067200000


def tick(seq, bid, ask=None, ms=None):
    return dict(sequence=seq, time_msc=BASE if ms is None else ms,
                bid=bid, ask=bid+.0001 if ask is None else ask)


class ProtectiveStopTests(unittest.TestCase):
    def opened(self, side=1, config=None, distance=.01):
        sim = Experiment030Simulator(config or Config(), 'C07')
        sim.processing_tick = tick(0, 1.125)
        sim._open(Bar(datetime.fromtimestamp(BASE/1000, timezone.utc), 1.125, 1.125, 1.125, 1.125, 1), side, distance)
        sim.processing_tick = None
        return sim

    def trigger(self, sim, seq=0, ms=None):
        p = sim.position
        price = p.entry+p.side*.007
        q = tick(seq, price if p.side == 1 else price-.0001,
                 price+.0001 if p.side == 1 else price, ms)
        sim.step_tick(q)
        return q

    def test_exact_long_and_short_threshold_equality(self):
        cfg = replace(Config(), commission_per_lot_round_turn=0, slippage_pips=0)
        for side in (1, -1):
            quote = 1.125+side*.125
            self.assertEqual(protection(1.125, 250, .01, side, 0, quote, quote, cfg), (1.125, 125))
            self.assertIsNone(protection(1.125, 250.0001, .01, side, 0, quote, quote, cfg))

    def test_bid_ask_full_cost_and_financing(self):
        cfg = Config()
        for side in (1, -1):
            level, net = protection(1.125, 1, .01, side, -.25, 1.14 if side==1 else 1.10, 1.15 if side==1 else 1.11, cfg)
            close = 1.14 if side==1 else 1.11
            self.assertAlmostEqual(net, side*(close-side*cfg.slippage_pips*.0001-1.125)*1000-.07-.25)
            self.assertAlmostEqual(side*(level-side*cfg.slippage_pips*.0001-1.125)*1000-.07-.25, 0)

    def test_no_early_arm(self):
        sim = self.opened()
        sim.step_tick(tick(0, sim.position.entry+.003))
        self.assertIsNone(sim.pending_protection['arm'])

    def test_long_and_short_monotonic_one_move(self):
        for side in (1, -1):
            sim = self.opened(side)
            original = sim.position.stop
            self.trigger(sim)
            moved = sim.position.stop
            self.assertGreater(side*(moved-original), 0)
            record = dict(sim.pending_protection['arm'])
            self.trigger(sim, 1)
            self.assertEqual(sim.position.stop, moved)
            self.assertEqual(sim.pending_protection['arm'], record)

    def test_targets_fill_before_arming_and_peak_caps(self):
        for side in (1, -1):
            sim = self.opened(side)
            target = sim.position.target
            price = target+side*.1
            sim.step_tick(tick(0, price if side==1 else price-.0001, price+.0001 if side==1 else price))
            self.assertEqual(sim.trades[0]['exit'], target)
            self.assertIsNone(sim.protection_lineage[0]['arm'])
            self.assertAlmostEqual(sim.peak_tick_equity, sim.balance)

    def test_original_stops_fill_before_arming(self):
        sim = self.opened()
        sim.step_tick(tick(0, 1.0))
        self.assertIsNone(sim.protection_lineage[0]['arm'])
        self.assertEqual(sim.trades[0]['reason'], 'stop_tick')

    def test_next_sequence_and_tied_timestamp(self):
        sim = self.opened()
        self.trigger(sim)
        self.assertIsNotNone(sim.position)
        stop = sim.position.stop
        sim.step_tick(tick(1, stop))
        self.assertIsNone(sim.position)
        self.assertEqual(sim.fill_lineage[0]['exit_sequence'], 1)
        self.assertEqual(sim.protection_lineage[0]['arm']['sequence'], 0)
        self.assertAlmostEqual(sim.trades[0]['net_pnl'], 0)

    def test_gap_after_protection_can_exceed_original_risk(self):
        sim = self.opened(distance=.001)
        p = sim.position
        sim.step_tick(tick(0, p.entry+.0008))
        self.assertIsNotNone(sim.pending_protection['arm'])
        risk = sim.pending_protection['initial_risk']
        sim.step_tick(tick(1, 1.0))
        self.assertLess(sim.trades[0]['net_pnl'], -risk)
        self.assertTrue(sim.paused)

    def test_financing_after_arming_does_not_move_stop(self):
        sim = self.opened()
        self.trigger(sim)
        level = sim.position.stop
        self.trigger(sim, 1, BASE+86400000)
        self.assertEqual(sim.position.stop, level)
        self.assertLess(sim.position.swap, 0)
        sim.step_tick(tick(2, level, ms=BASE+86400000))
        self.assertLess(sim.trades[0]['net_pnl'], 0)

    def test_financing_before_arming_is_in_level(self):
        sim = self.opened()
        sim.step_tick(tick(0, sim.position.entry+.001))
        self.trigger(sim, 1, BASE+86400000)
        self.assertLess(sim.pending_protection['arm']['accrued_swap'], 0)
        p = sim.position
        self.assertAlmostEqual(p.stop, p.entry+(-p.swap+p.lots*sim.config.commission_per_lot_round_turn)/(p.lots*sim.config.contract_size)+sim.config.slippage_pips*.0001)

    def test_restart_before_and_after_arm_and_duplicate(self):
        for armed in (False, True):
            a = self.opened()
            q = self.trigger(a) if armed else tick(0, 1.125)
            if not armed:
                a.step_tick(q)
            b = Experiment030Simulator.restore(a.checkpoint(), a.config, candidate='C07', evaluation_start_ms=0)
            self.assertFalse(b.step_tick(q))
            for sim in (a,b):
                if not armed:
                    self.trigger(sim, 1)
                sim.step_tick(tick(1 if armed else 2, 1.0))
                sim.finish()
            self.assertEqual(a.checkpoint(), b.checkpoint())

    def test_checkpoint_rejects_legacy_candidate_and_cost(self):
        cfg = Config()
        for value, candidate, config in ((Experiment028Simulator(cfg).checkpoint(), 'C00', cfg),
                (Experiment030Simulator(cfg,'C07').checkpoint(), 'C08', cfg),
                (Experiment030Simulator(cfg,'C07').checkpoint(), 'C07', replace(cfg,slippage_pips=1))):
            with self.assertRaises(ValueError):
                Experiment030Simulator.restore(value, config, candidate=candidate, evaluation_start_ms=0)

    def test_position_limit_and_original_sizing_budget(self):
        sim = self.opened()
        old, risk = sim.position, sim.pending_protection['initial_risk']
        self.trigger(sim)
        sim.processing_tick = tick(1, 1.1)
        sim._open(Bar(datetime.fromtimestamp(BASE/1000,timezone.utc),1.1,1.1,1.1,1.1,1), -1, .01)
        self.assertIs(sim.position,old)
        self.assertEqual(risk,sim.pending_protection['initial_risk'])
        self.assertLessEqual(risk+old.lots*(7+sim.config.slippage_pips*.0001*100000),25)

    def test_pause_blocks_new_position_after_restart(self):
        sim = self.opened(distance=.001)
        sim.step_tick(tick(0,1.0))
        sim = Experiment030Simulator.restore(sim.checkpoint(),sim.config,candidate='C07',evaluation_start_ms=0)
        sim.processing_tick = tick(1,1.0)
        sim._open(Bar(datetime.fromtimestamp(BASE/1000,timezone.utc),1,1,1,1,1),1,.001)
        self.assertIsNone(sim.position)

    def test_all_controls_exact_full_replay(self):
        for candidate in ('C00','C05','C06'):
            a,b = Experiment028Simulator(Config(),candidate),Experiment030Simulator(Config(),candidate)
            for i in range(204):
                q=tick(i,1.125 if i<200 else 1.25 if i<203 else 1.0,ms=BASE+i*3600000)
                a.step_tick(q); b.step_tick(q)
            a.finish(); b.finish()
            for key in ('trades','curve','fill_lineage','decision_log'):
                self.assertEqual(getattr(a,key),getattr(b,key))
            self.assertEqual(a.metrics(),b.metrics())

    def test_future_quotes_cannot_change_arm_record(self):
        a=self.opened()
        self.trigger(a)
        record=dict(a.pending_protection['arm'])
        a.step_tick(tick(1,1.0))
        self.assertEqual(a.protection_lineage[0]['arm'],record)
