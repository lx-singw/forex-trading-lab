"""Saved-report causality and export acceptance; no trading rules changed."""
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from forex_demo_lab import elliott_session_viewer_151 as v

ROOT = Path(__file__).resolve().parents[1]


def fixture():
    bars = [{"timeframe": f, "start": 1000, "end": 2000, "available": 3000,
             "open": "1.1", "high": "1.2", "low": "1.0", "close": "1.1", "lineage": f} for f in ("H4", "H1")]
    snapshots = [{"time": 3000, "frame": f, "reason": "warmup" if f == "H4" else "signal",
                  "counts": [], "interpretations": [], "signals": [] if f == "H4" else [{"formed": 3000, "kind": "EW3"}],
                  "context": {"D1": 1, "H4": 1}, "session_coverage": {"ready": True, "session_open": True}}
                 for f in ("H4", "H1")]
    entry = {"kind": "entry", "time": "3000", "side": "1", "entry": "1.11", "stop": "1.09", "target": "1.15", "lots": "0.01"}
    ledger = [entry, {"kind": "quote", "time": 3000, "sequence": 0, "result": "entered", "cash": "9999.9"},
              {"kind": "financing", "time": 0, "debit": "0.1"},
              {"kind": "exit", "time": 4000, "exit": "1.08", "reason": "stop"},
              {"kind": "quote", "time": 4000, "sequence": 1, "result": "held", "cash": "9996.8"},
              {"kind": "finish", "time": 4000, "sequence": 1, "cash": "9996.8"}]
    quotes = [{"time": t, "source": t, "sequence": i, "bid": "1.1", "ask": "1.1001", "session_open": True}
              for i, t in enumerate((3000, 4000))]
    paper = {"kind": "invented_session_paper_148", "orders_available": False, "market_cells_run": 0,
             "market_returns": None, "profile": "base", "time": 4000,
             "decisions": {"kind": "invented_session_strategy_decisions_147", "orders_available": False, "snapshots": snapshots},
             "ledger": {"finished": True, "events": ledger}, "quote_gates": [
                 {"time": q["time"], "sequence": q["sequence"], "effective_open": True} for q in quotes], "cancellations": []}
    account = {"kind": "invented_session_account149", "candidate": "EW_FULL_V1", "orders_available": False,
               "market_status": "UNAVAILABLE", "market_returns": None, "profile": "base",
               "partition": {"name": "development"}, "original_report": paper}
    journal = [{"kind": "bars", "value": bars}, {"kind": "quote", "value": quotes[0]},
               {"kind": "quote", "value": quotes[1]}, {"kind": "finish", "value": quotes[1]}]
    return account, bars, journal


class Cursor151Tests(unittest.TestCase):
    def setUp(self):
        self.account, self.bars, self.journal = fixture()

    def view(self):
        return v.viewer_data(self.account, self.bars, self.journal)

    def test_same_clock_does_not_reveal_later_frame_signal_or_fill(self):
        view = self.view()
        early = v.state_at(view, 0)
        self.assertIsNone(early["snapshot"])
        self.assertEqual([], early["bars"])
        self.assertEqual([], early["actions"])
        self.assertIsNone(early["cash"])
        signal = v.state_at(view, 1)
        self.assertEqual("signal", signal["snapshot"]["reason"])
        self.assertEqual([], signal["actions"])
        self.assertEqual("entry", v.state_at(view, 2)["position"]["kind"])

    def test_financing_appears_at_receipt_not_effective_date(self):
        rows = self.view()["rows"]
        self.assertEqual([3000, 3000, 3000, 4000, 4000], [r["time"] for r in rows])
        self.assertFalse(any(e["kind"] == "financing" for r in rows[:3] for e in r.get("effects", [])))
        self.assertEqual("financing", rows[3]["effects"][0]["kind"])
        self.assertEqual(0, rows[3]["effects"][0]["time"])

    def test_future_exit_and_later_bar_changes_leave_earlier_projection_identical(self):
        before = v.state_at(self.view(), 2)
        self.account["original_report"]["ledger"]["events"][3]["exit"] = "0.9"
        bar = dict(self.bars[-1], start=2000, end=3000, available=3500)
        self.bars.append(bar)
        snapshot = deepcopy(self.account["original_report"]["decisions"]["snapshots"][-1])
        snapshot["time"] = 3500
        snapshot["signals"] = []
        self.account["original_report"]["decisions"]["snapshots"].append(snapshot)
        self.journal[0]["value"] = self.bars[:2]
        self.journal.insert(2, {"kind": "bars", "value": [bar]})
        after = v.state_at(self.view(), 2)
        self.assertEqual(before, after)

    def test_exit_clears_position_and_final_cash_is_not_backfilled(self):
        view = self.view()
        self.assertEqual("9999.9", v.state_at(view, 2)["cash"])
        state = v.state_at(view, 3)
        self.assertIsNone(state["position"])
        self.assertEqual("9996.8", state["cash"])

    def test_cancellation_tie_is_conservatively_delayed(self):
        self.account["original_report"]["cancellations"] = [{"time": 3000, "key": "anonymous", "reason": "superseded"}]
        view = self.view()
        self.assertEqual("quote", view["rows"][2]["kind"])
        self.assertEqual([], v.state_at(view, 2)["cancellations"])
        self.assertEqual("cancellation", view["rows"][3]["kind"])

    def test_recorded_count_ranking_is_preserved(self):
        snapshot = self.account["original_report"]["decisions"]["snapshots"][-1]
        snapshot["interpretations"] = [{"id": "economic_first", "available": 2000}, {"id": "newer_second", "available": 3000}]
        self.assertEqual(["economic_first", "newer_second"], [c["id"] for c in self.view()["rows"][1]["snapshot"]["interpretations"]])

    def test_nested_future_pivot_is_rejected(self):
        self.account["original_report"]["decisions"]["snapshots"][0]["counts"] = [
            {"children": [{"pivot_records": [{"available": 3001, "time": 1000}]}]}]
        with self.assertRaisesRegex(ValueError, "future_pivot"):
            self.view()

    def test_future_interpretation_and_signal_are_rejected(self):
        for field, value in (("interpretations", [{"available": 3001}]), ("signals", [{"formed": 3001}])):
            account, bars, journal = fixture()
            account["original_report"]["decisions"]["snapshots"][0][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                v.viewer_data(account, bars, journal)

    def test_wrong_publication_order_and_quote_sequence_are_rejected(self):
        self.bars.reverse()
        with self.assertRaisesRegex(ValueError, "snapshot_order"):
            self.view()
        self.account, self.bars, self.journal = fixture()
        self.account["original_report"]["quote_gates"][0]["sequence"] = 8
        with self.assertRaisesRegex(ValueError, "gate_order"):
            self.view()

    def test_missing_quote_finish_and_extra_ledger_effect_are_rejected(self):
        for mutation in (lambda a, b, j: j.pop(), lambda a, b, j: a["original_report"]["ledger"]["events"].append({"kind": "quote"})):
            a, b, j = fixture()
            mutation(a, b, j)
            with self.assertRaises(ValueError):
                v.viewer_data(a, b, j)

    def test_market_live_control_and_unfinished_reports_are_rejected(self):
        for key, value in (("orders_available", True), ("candidate", "CASH"), ("market_status", "COMPUTED"), ("market_returns", "1")):
            account, bars, journal = fixture()
            account[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                v.viewer_data(account, bars, journal)
        self.account["original_report"]["ledger"]["finished"] = False
        with self.assertRaises(ValueError):
            self.view()

    def test_export_data_is_detached_from_input(self):
        view = self.view()
        self.bars[0]["close"] = "9"
        self.account["original_report"]["ledger"]["events"][0]["entry"] = "9"
        self.assertEqual("1.1", view["bars"][0]["close"])
        self.assertEqual("1.11", view["rows"][2]["effects"][0]["entry"])

    def test_html_escapes_script_content_and_forbids_network(self):
        view = self.view()
        view["limitations"].append("</script><script>alert('bad')</script>&")
        html = v.render(view)
        self.assertNotIn("</script><script>", html)
        self.assertIn("\\u003c/script>", html)
        self.assertIn("connect-src 'none'", html)
        self.assertNotIn("/*VIEW_DATA*/", html)

    def test_browser_projection_matches_reference_for_every_cursor_and_frame(self):
        view = self.view()
        code = v.TEMPLATE.read_text().split("// Pure cursor projection;")[1].split("// END_CURSOR_PROJECTION")[0]
        code = code[code.index("function stateAt"):]
        requests = [(i, frame) for i in range(len(view["rows"])) for frame in ("H1", "H4", "D1")]
        program = code + "\nconst view=" + json.dumps(view) + ";\nconsole.log(JSON.stringify(" + json.dumps(requests) + ".map(([i,f])=>stateAt(view,i,f))));"
        done = subprocess.run(["node", "-e", program], capture_output=True, text=True, check=True)
        self.assertEqual([v.state_at(view, i, frame) for i, frame in requests], json.loads(done.stdout))

    def test_javascript_controls_and_svg_render_without_future_cash(self):
        # Minimal DOM harness checks the shipped script, not browser layout.
        html = v.render(self.view())
        script = html.split("<script>")[1].split("</script>")[0]
        harness = """
class Element {
 constructor(){this.children=[];this.value='';this.textContent='';this.handlers={};}
 appendChild(child){this.children.push(child);if(this.value==='')this.value=child.value;return child;}
 replaceChildren(){this.children=[];this.value='';}
 setAttribute(key,value){this[key]=value;}
 addEventListener(name,handler){this.handlers[name]=handler;}
}
const elements=new Map();
const document={getElementById(id){if(!elements.has(id))elements.set(id,new Element());return elements.get(id);},createElement(){return new Element();},createElementNS(){return new Element();}};
document.getElementById('cursor').value='0';document.getElementById('frame').value='H1';document.getElementById('filter').value='all';
"""
        assertions = """
const result={initialCash:byId('cash').textContent,initialEvidence:byId('evidence').textContent};
byId('filter').value='signals';byId('next').onclick();result.signal=byId('stamp').textContent;result.signalCash=byId('cash').textContent;
byId('filter').value='fills';byId('next').onclick();result.entry=byId('position').textContent;
byId('next').onclick();result.exit=byId('position').textContent;result.exitCash=byId('cash').textContent;result.svgNodes=byId('chart').children.length;
byId('first').onclick();result.rewoundCash=byId('cash').textContent;
console.log(JSON.stringify(result));
"""
        done = subprocess.run(["node", "-"], input=harness + script + assertions, capture_output=True, text=True, check=True)
        result = json.loads(done.stdout)
        self.assertEqual("Not yet observed", result["initialCash"])
        self.assertNotIn("9996.8", result["initialEvidence"])
        self.assertIn("H1: signal", result["signal"])
        self.assertEqual("Not yet observed", result["signalCash"])
        self.assertIn("Long", result["entry"])
        self.assertEqual("Flat", result["exit"])
        self.assertEqual("9996.80", result["exitCash"])
        self.assertGreater(result["svgNodes"], 10)
        self.assertEqual("Not yet observed", result["rewoundCash"])


class Export151Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.temp.name)
        cls.prepared = cls.root / "prepared"
        spec = importlib.util.spec_from_file_location("fixture151", ROOT / "scripts/elliott-session-comparison-149.py")
        generator = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(generator)
        source, freeze = cls.root / "input.json", cls.root / "freeze.json"
        v.comparison.write(source, generator.fixture("trend"))
        v.comparison.freeze(source, freeze)
        v.comparison.prepare(source, freeze, "development", cls.prepared)
        prepared = json.loads((cls.prepared / "prepared149.json").read_text())
        bars = json.loads((cls.prepared / "derived-bars.json").read_text())["bars"]
        journal = json.loads((cls.prepared / "paper-events.json").read_text())["events"]
        account, _, _ = fixture()
        paper = account["original_report"]
        account["partition"] = prepared["partition"]
        paper["time"] = journal[-1]["value"]["time"]
        paper["decisions"]["snapshots"] = [{"time": b["available"], "frame": b["timeframe"], "reason": "warmup",
                                            "counts": [], "interpretations": [], "signals": [], "context": {}} for b in bars]
        quote_events = [{"kind": e["kind"], "time": e["value"]["time"], "sequence": e["value"]["sequence"],
                         "result": "no_signal", "cash": "10000"} for e in journal if e["kind"] in ("quote", "finish")]
        paper["ledger"]["events"] = quote_events
        paper["quote_gates"] = [{"time": e["time"], "sequence": e["sequence"]} for e in quote_events if e["kind"] == "quote"]
        cls.report = cls.prepared / "EW_FULL_V1-base.json"
        cls.report.write_text(json.dumps(account))

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_export_binds_artifacts_and_does_not_modify_prepared_files(self):
        before = v.comparison.collect(self.prepared)
        destination = self.root / "export"
        result = v.export(self.prepared, destination)
        self.assertEqual(before, v.comparison.collect(self.prepared))
        self.assertEqual(hashlib.sha256((destination / "replay.html").read_bytes()).hexdigest(), result["html_sha256"])
        self.assertEqual(v.comparison.report_hash(self.report), result["report_sha256"])
        self.assertFalse(result["orders_available"])
        with self.assertRaises(FileExistsError):
            v.export(self.prepared, destination)

    def test_export_rejects_output_inside_prepared_and_modified_derived_data(self):
        with self.assertRaisesRegex(ValueError, "outside_prepared"):
            v.export(self.prepared, self.prepared / "viewer")
        path = self.prepared / "derived-bars.json"
        raw = path.read_bytes()
        try:
            path.write_bytes(raw + b" ")
            with self.assertRaisesRegex(ValueError, "prepared_binding"):
                v.export(self.prepared, self.root / "bad-export")
            self.assertFalse((self.root / "bad-export").exists())
        finally:
            path.write_bytes(raw)

    def test_public_cli_and_no_live_option(self):
        script = ROOT / "scripts/elliott-session-viewer-151.py"
        done = subprocess.run([sys.executable, str(script), str(self.prepared), str(self.root / "cli-export")], capture_output=True, text=True)
        self.assertEqual(0, done.returncode, done.stderr)
        self.assertFalse(json.loads(done.stdout)["orders_available"])
        done = subprocess.run([sys.executable, str(script), "--live"], capture_output=True, text=True)
        self.assertNotEqual(0, done.returncode)


if __name__ == "__main__":
    unittest.main()
