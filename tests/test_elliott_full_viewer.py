"""UI data acceptance: executions after the final bar must remain reachable."""
import unittest
from forex_demo_lab.elliott_full.report import viewer_data,render


class ViewerTests(unittest.TestCase):
    def test_pattern_scope_is_visible_in_detail(self):
        report=self.report();report["snapshots"][0]["pattern_window"]={"left_truncated":True,"discarded_pivots":10}
        row=viewer_data(report)["snapshots"][0]
        self.assertTrue(row["pattern_window"]["left_truncated"])
    def report(self):
        return {"bars":[],"snapshots":[{"time":1000,"frame":"H1","reason":"signal","context":{},"counts":[]}],
                "ledger":{"events":[{"kind":"entry","time":"2000","entry":"1.1","stop":"1.09","target":"1.12"},
                                     {"kind":"exit","time":3000,"exit":"1.08","reason":"stop"}]}}

    def test_trade_events_extend_cursor_beyond_last_candle(self):
        view=viewer_data(self.report())
        self.assertEqual([1000,2000,3000],[r["time"] for r in view["snapshots"]])
        self.assertEqual("exit: stop",view["snapshots"][-1]["reason"])

    def test_equal_time_executions_keep_order(self):
        report=self.report();report["ledger"]["events"][-1]["time"]=2000
        rows=viewer_data(report)["snapshots"]
        self.assertEqual([0,1],[r["event_index"] for r in rows[1:]])
        self.assertIn("slice(0,s.event_index+1)",render(report))

    def test_no_future_count_snapshot_borrowed_for_execution(self):
        report=self.report();report["snapshots"].append({"time":4000,"frame":"H1","reason":"future","counts":[]})
        rows=viewer_data(report)["snapshots"]
        self.assertEqual("signal",rows[0]["reason"])
        self.assertEqual("entry",rows[1]["reason"])
        self.assertEqual("future",rows[-1]["reason"])

    def test_execution_without_bars_remains_visible(self):
        report=self.report();report["snapshots"]=[]
        self.assertEqual(2,len(viewer_data(report)["snapshots"]))


if __name__=="__main__":
    unittest.main()
