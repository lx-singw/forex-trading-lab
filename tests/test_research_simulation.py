from dataclasses import replace
from datetime import datetime, timezone
import unittest

from forex_demo_lab.model import Config
from forex_demo_lab.research_simulation import ResearchTickSimulator

START = int(datetime(2024, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
EVALUATION = START + 201 * 3600000


def ticks():
    values = [1.1] * 200 + [1.101, 1.101, 1.101, 1.101]
    return [{"sequence": i, "time_msc": START + i * 3600000, "bid": bid, "ask": bid + .0001}
            for i, bid in enumerate(values)]


class ResearchSimulationTests(unittest.TestCase):
    def sim(self, **kw):
        return ResearchTickSimulator(replace(Config(), leverage=10), **{"candidate": "C02", "evaluation_start_ms": EVALUATION, **kw})

    def test_common_warmup_prevents_orders_until_closed_history_available(self):
        s = self.sim()
        for tick in ticks()[:201]:
            s.step_tick(tick)
            self.assertIsNone(s.position)
        s.step_tick(ticks()[201])
        self.assertIsNotNone(s.position)
        p = s.position
        estimated = ((abs(p.entry - p.stop) + .00002) * 100000 + 7) * p.lots
        self.assertLessEqual(estimated, 25 + 1e-9)
        self.assertGreaterEqual(s.decision_log[0]["hour_start_ms"], EVALUATION)

    def test_future_evaluation_boundary_blocks_an_otherwise_valid_signal(self):
        s = self.sim(evaluation_start_ms=EVALUATION + 2 * 3600000)
        for tick in ticks()[:202]:
            s.step_tick(tick)
        self.assertIsNone(s.position)
        self.assertEqual(s.decision_log, [])

    def test_current_opening_quote_cannot_change_closed_history_decision(self):
        normal, shocked = self.sim(), self.sim()
        for tick in ticks()[:201]:
            normal.step_tick(tick)
            shocked.step_tick(tick)
        normal.step_tick(ticks()[201])
        shocked.step_tick({**ticks()[201], "bid": 1.5, "ask": 1.5001})
        self.assertEqual(normal.decision_log, shocked.decision_log)
        self.assertNotEqual(normal.position.entry, shocked.position.entry)

    def test_restart_with_open_position_matches_uninterrupted_run(self):
        s = self.sim()
        for tick in ticks()[:202]:
            s.step_tick(tick)
        self.assertIsNotNone(s.position)
        restored = ResearchTickSimulator.restore(s.checkpoint(), s.config, candidate="C02", evaluation_start_ms=EVALUATION)
        self.assertFalse(restored.step_tick(ticks()[201]))
        for tick in ticks()[202:]:
            s.step_tick(tick)
            restored.step_tick(tick)
        s.finish()
        restored.finish()
        self.assertEqual(s.checkpoint(), restored.checkpoint())
        self.assertEqual(s.metrics()["warmup_hours"], 201)
        self.assertEqual(s.metrics()["evaluation_hours"], 3)

    def test_checkpoint_rejects_different_candidate_or_window(self):
        s = self.sim()
        for candidate, boundary in (("C03", EVALUATION), ("C02", EVALUATION + 3600000)):
            with self.assertRaisesRegex(ValueError, "mismatch"):
                ResearchTickSimulator.restore(s.checkpoint(), s.config, candidate=candidate, evaluation_start_ms=boundary)

    def test_gap_loss_latches_pause_and_cannot_stack_another_position(self):
        s = self.sim()
        for tick in ticks()[:202]:
            s.step_tick(tick)
        position = s.position
        s.step_tick({"sequence": 202, "time_msc": EVALUATION + 1, "bid": 1.101, "ask": 1.1011})
        self.assertIs(s.position, position)
        s.step_tick({"sequence": 203, "time_msc": EVALUATION + 2, "bid": 1.0, "ask": 1.0001})
        self.assertIsNone(s.position)
        self.assertTrue(s.paused)
        self.assertLess(s.trades[0]["net_pnl"], -100)
