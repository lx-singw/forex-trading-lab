import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location("diagnosis", Path(__file__).resolve().parents[1] / "scripts/diagnose-baseline.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class BaselineDiagnosisTests(unittest.TestCase):
    def trade(self, side=1):
        return {"side": side, "lots": .1, "entry": 1.1, "exit": 1.09798 if side == 1 else 1.10202,
                "stop": 1.099 if side == 1 else 1.101, "reason": "stop_tick",
                "gross_pnl": -20.2, "commission": .7, "swap": -.1, "net_pnl": -21,
                "opened": "2024-01-02T00:00:00+00:00", "closed": "2024-01-02T01:00:00+00:00"}

    def run_trade(self, t):
        return module.diagnose({"trades": [t], "metrics": {"closed_trades": 1, "net_pnl": -21}},
                               {"slippage_pips": .2, "contract_size": 100000})

    def test_long_and_short_gap_attribution_separates_assumed_slippage(self):
        for side in (1, -1):
            d = self.run_trade(self.trade(side))
            self.assertAlmostEqual(d["maximum_observed_quote_overshoot_pips"], 10)
            self.assertAlmostEqual(d["stop_overshoot_dollars_including_modeled_exit_slippage"], 10.2)
            self.assertEqual(d["net_pnl"], -21)
            self.assertEqual(d["pnl_before_commission_and_swap_includes_spread_and_slippage"], -20.2)

    def test_nominal_stop_fill_has_no_quote_gap_but_retains_exit_slippage(self):
        t = self.trade()
        t.update(exit=1.09898, gross_pnl=-10.2, net_pnl=-11)
        d = module.diagnose({"trades": [t], "metrics": {"closed_trades": 1, "net_pnl": -11}},
                            {"slippage_pips": .2, "contract_size": 100000})
        self.assertAlmostEqual(d["maximum_observed_quote_overshoot_pips"], 0)
        self.assertAlmostEqual(d["stop_overshoot_dollars_including_modeled_exit_slippage"], .2)

    def test_nonstop_exit_is_not_misclassified_as_a_stop_gap(self):
        t = self.trade()
        t["reason"] = "end_of_sample"
        d = self.run_trade(t)
        self.assertEqual(d["stop_overshoot_dollars_including_modeled_exit_slippage"], 0)
        self.assertEqual(d["exit_reasons"], {"end_of_sample": 1})

    def test_inconsistent_pnl_or_negative_duration_is_rejected(self):
        for updates in ({"net_pnl": -20}, {"closed": "2024-01-01T23:00:00+00:00"}):
            with self.assertRaises(ValueError):
                self.run_trade({**self.trade(), **updates})
