"""Rolling pattern scope must not erase consumed opportunities or held exposure."""
import copy
import importlib.util
from pathlib import Path
import unittest
from dataclasses import replace
from forex_demo_lab.elliott_full.contracts import D,Bar,Quote,validate_bundle
from forex_demo_lab.elliott_full.patterns import Pivot
from forex_demo_lab.elliott_full.windows import select_window
from forex_demo_lab.elliott_full.engine import Engine
from forex_demo_lab.elliott_full.strategy import Strategy
from test_elliott_full_policy import counts,history


class WindowTests(unittest.TestCase):
    def test_missing_completed_parent_cannot_supply_old_context(self):
        # Declared count fixture isolates the context clock gate. It is not a
        # market-session/calendar qualification or automatic-discovery example.
        c=counts();last=history(c)[-1];s=Strategy()
        for frame in ("D1","H4"):
            s.bars[frame]=[replace(b,timeframe=frame) for b in history(c)]
            s.counts[frame]={"nodes":list(c.legs),"interpretations":[c],"incomplete":False}
        s._contexts(last.end)
        self.assertEqual({"D1":1,"H4":1},s.contexts)
        s._contexts(last.end+4*3600000)
        self.assertEqual(1,s.contexts["D1"])
        self.assertIsNone(s.contexts["H4"])
        self.assertEqual("missing_completed_parent_bar",s.context_details["H4"]["stage"])
        s._contexts(last.end+86400000)
        self.assertIsNone(s.contexts["D1"])

    def points(self,n):
        return [Pivot(str(i),i,i*1000,(i+1)*1000,D(10+i%2),"low" if i%2==0 else "high",2) for i in range(n)]

    def test_rollover_retains_latest_256(self):
        window=select_window(self.points(257))
        self.assertEqual(256,len(window.pivots))
        self.assertEqual(1,window.start)
        self.assertEqual(1,window.discarded)
        self.assertTrue(window.record()["left_truncated"])

    def test_future_suffix_does_not_change_retained_pivots(self):
        before=select_window(self.points(256))
        after=select_window(self.points(257))
        self.assertEqual(before.pivots[1:],after.pivots[:-1])

    def test_bad_window_bounds_or_chronology_reject(self):
        for limit in (0,257,True):
            with self.assertRaises(ValueError): select_window(self.points(3),limit)
        with self.assertRaises(ValueError): select_window(list(reversed(self.points(3))))

    def test_empty_window(self):
        self.assertIsNone(select_window([]).start)

    def test_public_long_history_preserves_position_until_executable_quote(self):
        path=Path(__file__).resolve().parents[1]/"scripts"/"elliott-full-bar-demo.py"
        spec=importlib.util.spec_from_file_location("long_history_fixture",path)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        bars,quotes=validate_bundle(module.fixture())
        engine=Engine()
        for b in bars:
            engine.step({"kind":"bar","value":b.record()})
        engine.step({"kind":"quote","value":quotes[0].record()})
        position=copy.deepcopy(engine.ledger.position)
        self.assertIsNotNone(position)
        key=position["key"]
        snapshot_index=len(engine.strategy.snapshots)-1
        published=copy.deepcopy(engine.strategy.snapshots[snapshot_index])
        start=engine.strategy.bars["H1"][-1].end
        waveform=tuple(map(D,("1.1000","1.1004","1.1008","1.1012","1.1008","1.1004")))
        for i in range(805):
            value=waveform[i%6];end=start+(i+1)*3600000
            bar=Bar("H1",end-3600000,end,end,value,value+D(".000001"),value-D(".000001"),value,f"long-history-{i}")
            engine.step({"kind":"bar","value":bar.record()})
        window=engine.strategy.snapshots[-1]["pattern_window"]
        self.assertEqual(256,window["pivot_count"])
        self.assertGreater(window["discarded_pivots"],0)
        self.assertEqual(position,engine.ledger.position)
        self.assertFalse(engine.ledger.trades)  # OHLC is not a fabricated stop fill.
        self.assertIn(key,engine.strategy.policy.emitted)
        self.assertTrue(engine.strategy.policy.groups[key]["consumed"])
        self.assertEqual(published,engine.strategy.snapshots[snapshot_index])
        t=end+2000
        engine.step({"kind":"quote","value":Quote(t,t,2,D("1.1000"),D("1.1001")).record()})
        self.assertIsNone(engine.ledger.position)
        self.assertEqual(1,len(engine.ledger.trades))
        self.assertEqual("stop",engine.ledger.trades[0]["reason"])


if __name__=="__main__":
    unittest.main()
