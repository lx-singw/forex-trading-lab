from dataclasses import replace
from datetime import datetime, timedelta, timezone
import unittest

from forex_demo_lab.model import Bar, Config, signal, size_lots, timestamp

START = datetime(2024, 1, 1, tzinfo=timezone.utc)


def candle(hour=0, opening=1.1, high=1.1005, low=1.0995, close=1.1, spread=1.0):
    return Bar(START + timedelta(hours=hour), opening, high, low, close, spread)


class ModelTests(unittest.TestCase):
    def test_reject_invalid_risk_and_specification(self):
        for setting in ({"risk_fraction": .01}, {"daily_loss_fraction": .02}, {"symbol": "GBPUSD"},
                        {"account_currency": "EUR"}, {"lot_step": 0}, {"slippage_pips": -1},
                        {"initial_equity": float("nan")}, {"fast": 1.5}, {"slow": True},
                        {"leverage": 0}, {"commission_per_lot_round_turn": -1}, {"swap_long_per_lot": 3}):
            with self.subTest(setting=setting), self.assertRaises(ValueError):
                Config(**setting)

    def test_invalid_bars_fail(self):
        for setting in ({"high": 1}, {"low": 2}, {"spread": -1}, {"close": float("inf")}, {"opening": 0}):
            with self.subTest(setting=setting), self.assertRaises(ValueError):
                candle(**setting)
        with self.assertRaises(ValueError):
            replace(candle(), time=START.replace(tzinfo=None))
        with self.assertRaises(ValueError):
            replace(candle(), time=START + timedelta(minutes=1))

    def test_timestamp_requires_offset_and_normalizes(self):
        self.assertEqual(timestamp("2024-01-01T02:00:00+02:00"), START)
        with self.assertRaises(ValueError):
            timestamp("2024-01-01T00:00:00")

    def test_closed_candle_cross_and_atr(self):
        config = Config(fast=2, slow=3, atr_period=2)
        bars = [candle(i, close=v, high=1.12, low=1.08) for i, v in enumerate([1.10, 1.09, 1.09, 1.11])]
        self.assertEqual(signal(bars[:3], config), (0, 0))
        side, distance = signal(bars, config)
        self.assertEqual(side, 1)
        self.assertAlmostEqual(distance, .08)
        inverse = [replace(b, close=2.2-b.close) for b in bars]
        self.assertEqual(signal(inverse, config)[0], -1)
        self.assertEqual(signal([candle(i) for i in range(51)], Config())[0], 0)

    def test_sizing_floors_includes_costs_and_never_rounds_up(self):
        c = Config()
        for equity in (10, 100, 1000, 10000, 100000):
            for distance in (.0001, .001, .01, .1):
                lots = size_lots(equity, 1.1, distance, c)
                with self.subTest(equity=equity, distance=distance):
                    self.assertLessEqual(lots, c.lot_max)
                    self.assertLessEqual(lots * ((distance+.00002)*100000+7), equity*.0025+1e-9)
                    self.assertAlmostEqual(lots / c.lot_step, round(lots / c.lot_step))
                    self.assertTrue(lots == 0 or lots >= c.lot_min)

    def test_no_minimum_lot_override_or_invalid_sizing(self):
        for equity, entry, distance in [(1, 1.1, .01), (0, 1.1, .001), (10000, 1.1, 0),
                                       (10000, float("nan"), .001), (-100, 1.1, .001)]:
            self.assertEqual(size_lots(equity, entry, distance, Config()), 0)

    def test_margin_cap_and_no_loss_recovery_multiplier(self):
        c = Config(leverage=1)
        lots = size_lots(10000, 1.1, .0001, c)
        self.assertLessEqual(lots * (110000 + 3.5), 10000)
        self.assertLessEqual(size_lots(9000, 1.1, .001, c), size_lots(10000, 1.1, .001, c))


if __name__ == "__main__":
    unittest.main()
