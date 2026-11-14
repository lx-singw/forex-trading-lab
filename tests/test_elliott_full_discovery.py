"""Public bar/quote discovery, signal-pending restart and independent cash check."""
import importlib.util
from pathlib import Path
import unittest
from fractions import Fraction
from forex_demo_lab.elliott_full.engine import Engine
from forex_demo_lab.elliott_full.contracts import validate_bundle, D


class DiscoveryTests(unittest.TestCase):
    def test_bar_only_discovery_pending_restart_and_gap_accounting(self):
        self.check_discovery("EW3",1,True)

    def test_short_ew3_automatic_discovery(self):
        self.check_discovery("EW3",-1)

    def test_long_ew5_automatic_discovery(self):
        self.check_discovery("EW5",1)

    def test_short_ew5_automatic_discovery(self):
        self.check_discovery("EW5",-1)

    def check_discovery(self,kind,side,restart=False):
        path=Path(__file__).resolve().parents[1]/"scripts"/"elliott-full-bar-demo.py"
        spec=importlib.util.spec_from_file_location("invented_bar_demo",path)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        bars,quotes=validate_bundle(module.fixture(kind,side))
        engine=Engine()
        for bar in bars:
            engine.step({"kind":"bar","value":bar.record()})
        self.assertIsNotNone(engine.pending)
        self.assertEqual(kind,engine.pending.kind)
        self.assertEqual({"D1":side,"H4":side},engine.strategy.contexts)
        self.assertEqual(1,sum(len(s["signals"]) for s in engine.strategy.snapshots))
        restored=Engine.restore(engine.checkpoint()) if restart else None
        if restored:
            self.assertEqual(engine.state(),restored.state())
        for q in quotes:
            event={"kind":"quote","value":q.record()}
            result=engine.step(event)
            if restored:
                self.assertEqual(result,restored.step(event))
        if restored:
            self.assertEqual(engine.state(),restored.state())
        ledger=engine.ledger
        self.assertEqual(1,len(ledger.trades))
        self.assertIsNone(ledger.position)
        entries=[e for e in ledger.events if e["kind"]=="entry"]
        self.assertEqual(1,len(entries))
        entry=entries[0];trade=ledger.trades[0]
        gross=side*(Fraction(trade["exit"])-Fraction(entry["entry"]))*100000*Fraction(entry["lots"])
        net=gross-7*Fraction(entry["lots"])
        self.assertEqual(net,Fraction(trade["net"]))
        self.assertEqual(Fraction(10000)+net,Fraction(ledger.cash))
        self.assertLess(D(trade["net"]),-D(trade["estimated_risk"]))


if __name__=="__main__":
    unittest.main()
