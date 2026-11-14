from dataclasses import asdict, replace
import json
from pathlib import Path
import tempfile
import unittest

from forex_demo_lab.cli import evaluate, freeze, read_bars, synthetic_data
from forex_demo_lab.model import Config
from forex_demo_lab.simulation import Simulator


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.data = self.root / "synthetic.csv"
        self.config = self.root / "config.json"
        self.manifest = self.root / "frozen.json"
        synthetic_data(self.data, 400)
        self.config.write_text(json.dumps(asdict(Config())), encoding="utf-8")
        self.bars = read_bars(self.data)

    def freeze(self):
        freeze(self.data, self.config, self.bars[280].time.isoformat(), self.manifest,
               "Deterministic synthetic test fixture", "Hypothetical costs", True)

    def test_end_to_end_partitions_and_reproducibility(self):
        self.freeze()
        dev = evaluate(self.data, self.manifest, "development", self.root/"dev.json")
        holdout = evaluate(self.data, self.manifest, "holdout", self.root/"holdout.json")
        again = evaluate(self.data, self.manifest, "holdout", self.root/"again.json")
        self.assertEqual(holdout, again)
        self.assertEqual(dev["rows"], 280)
        self.assertEqual(holdout["rows"], 120)
        self.assertLess(dev["last_bar"], holdout["first_bar"])
        self.assertEqual(holdout["status"], "synthetic_software_check")
        self.assertGreater(dev["metrics"]["closed_trades"], 0)
        for trade in holdout["trades"]:
            self.assertGreaterEqual(trade["opened"], self.bars[280].time.isoformat())
        self.assertAlmostEqual(sum(t["net_pnl"] for t in dev["trades"]), dev["metrics"]["net_pnl"])

    def test_future_prices_do_not_change_prefix_decisions_or_equity(self):
        normal, altered = Simulator(Config()), Simulator(Config())
        for bar in self.bars[:280]:
            normal.step(bar)
            altered.step(bar)
        prefix = normal.checkpoint()
        self.assertEqual(prefix, altered.checkpoint())
        for bar in self.bars[280:]:
            normal.step(bar)
            altered.step(replace(bar, open=bar.open+0.2, high=bar.high+0.2,
                                 low=bar.low+0.2, close=bar.close+0.2))
        self.assertEqual(normal.curve[:280], altered.curve[:280])
        boundary = self.bars[280].time.isoformat()
        self.assertEqual([t for t in normal.trades if t["closed"] < boundary],
                         [t for t in altered.trades if t["closed"] < boundary])

    def test_restart_full_strategy_exactly_matches_uninterrupted(self):
        normal, resumed = Simulator(Config()), Simulator(Config())
        for index, bar in enumerate(self.bars):
            normal.step(bar)
            resumed.step(bar)
            if index % 23 == 0:
                resumed = Simulator.restore(resumed.checkpoint(), resumed.config)
                self.assertFalse(resumed.step(bar))
        normal.finish()
        resumed.finish()
        self.assertEqual(normal.checkpoint(), resumed.checkpoint())

    def test_frozen_data_or_code_change_rejected(self):
        self.freeze()
        with self.data.open("a") as stream:
            stream.write("\n")
        with self.assertRaisesRegex(ValueError, "Dataset changed"):
            evaluate(self.data, self.manifest, "holdout", self.root/"out.json")
        manifest = json.loads(self.manifest.read_text())
        manifest["code_sha256"] = "changed"
        self.manifest.write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ValueError, "code changed"):
            evaluate(self.data, self.manifest, "holdout", self.root/"out.json")

    def test_frozen_config_is_independent_of_editable_config_file(self):
        self.freeze()
        self.config.write_text("{}")
        report = evaluate(self.data, self.manifest, "development", self.root/"out.json")
        self.assertEqual(report["experiment"]["config"], asdict(Config()))

    def test_no_overwrite_of_manifest_or_reports(self):
        self.freeze()
        with self.assertRaises(FileExistsError):
            self.freeze()
        evaluate(self.data, self.manifest, "development", self.root/"out.json")
        with self.assertRaises(FileExistsError):
            evaluate(self.data, self.manifest, "development", self.root/"out.json")

    def test_duplicate_and_unsorted_csv_are_rejected(self):
        lines = self.data.read_text().splitlines()
        for rows in ([lines[0], lines[1], lines[1]], [lines[0], lines[2], lines[1]]):
            self.data.write_text("\n".join(rows))
            with self.assertRaises(ValueError):
                read_bars(self.data)

    def test_split_requires_warmup_and_exact_boundary(self):
        for split in (self.bars[20].time.isoformat(), "2024-01-01T01:30:00Z", self.bars[-1].time.isoformat()):
            with self.assertRaises(ValueError):
                freeze(self.data, self.config, split, self.manifest, "fixture", "costs", True)

    def test_empty_malformed_and_nonfinite_input_rejected(self):
        for content in ("time,open,high,low,close,spread_pips\n", "wrong,header\n",
                        "time,open,high,low,close,spread_pips\n2024-01-01T00:00:00Z,1,2,1,nan,1\n"):
            self.data.write_text(content)
            with self.assertRaises(ValueError):
                read_bars(self.data)


if __name__ == "__main__":
    unittest.main()
