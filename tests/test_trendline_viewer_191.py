"""Manual annotation visibility and the Phase 8 fixed-target acceptance case."""
from copy import deepcopy
from fractions import Fraction
import json
import shutil
import subprocess
import unittest

from forex_demo_lab.trendline import breaks, quote_replay, quotes, replay_viewer
from test_trendline_levels_180 import target_hours
from test_trendline_quotes_185 import document, history, midpoint
from test_trendline_viewer_187 import browser_states, evidence


def winning_tape():
    value, hours = target_hours("LONG")
    at = hours[-1]["start"]
    tail = [midpoint(at + step, price, at + 700 + step)
            for step, price in ((1, "102.2"), (2, "108"), (3, "99"))]
    return document(value, history(hours[:-1]) + tail), at


def annotation_results(document, chart, candles, queries):
    template = replay_viewer.TEMPLATE.read_text(encoding="utf-8")
    js = template.split("// ANNOTATION_PROJECTION\n")[1].split("// END_ANNOTATION_PROJECTION")[0]
    program = js + """
const fs=require('fs');
const {document,chart,candles,queries}=JSON.parse(fs.readFileSync(0,'utf8'));
try{
  const lines=parseAnnotations(document,chart,candles);
  process.stdout.write(JSON.stringify(queries.map(q=>annotationSegments(lines,...q))));
}catch(error){process.stdout.write(JSON.stringify({error:error.message}));}
"""
    result = subprocess.run(["node", "-e", program], check=True, capture_output=True, text=True,
                            input=json.dumps({"document": document, "chart": chart, "candles": candles,
                                              "queries": queries}))
    return json.loads(result.stdout)


@unittest.skipUnless(shutil.which("node"), "Node required for executable annotation and viewer verification")
class ManualLineViewerTests(unittest.TestCase):
    def setUp(self):
        self.chart = {"source_sha256": "1" * 64, "symbol": "EURUSD", "timeframe": "H4",
                      "data_level": "B", "geometry_basis": "bid_only", "partition": "development"}
        self.candles = [{"start": 1000, "available": 2000, "index": 2},
                        {"start": 3000, "available": 4000, "index": 4}]
        self.line = {"label": "Manual support", "a": {"bar_start_ms": 3000, "price": "1.25"},
                     "b": {"bar_start_ms": 1000, "price": "1.125"},
                     "available_at_ms": 4500, "extend_right": True}
        self.document = {"schema": replay_viewer.ANNOTATION_SCHEMA, "chart": deepcopy(self.chart),
                         "lines": [deepcopy(self.line)]}

    def test_drawn_lines_follow_anchor_receipts_authored_receipt_and_chart_window(self):
        self.document["lines"].append({**self.line, "label": "After review", "available_at_ms": None,
                                       "extend_right": False})
        query = [(3999, True, 0, 7), (4499, False, 0, 7), (4500, False, 3, 6),
                 (4500, True, 0, 7), (4500, True, 6, 7)]
        before_anchors, before_authorship, arrived, retrospective, later_window = annotation_results(
            self.document, self.chart, self.candles, query)
        self.assertEqual(([], []), (before_anchors, before_authorship))
        self.assertEqual([{"label": "Manual support", "from": 3, "to": 6, "start": 1.1875, "end": 1.375}], arrived)
        self.assertEqual(["Manual support", "After review"], [segment["label"] for segment in retrospective])
        self.assertEqual((2, 4, 1.125, 1.25), tuple(retrospective[-1][k] for k in ("from", "to", "start", "end")))
        self.assertEqual(["Manual support"], [segment["label"] for segment in later_window])

    def test_wrong_chart_invalid_anchor_or_backdated_drawing_is_rejected(self):
        for change, expected in (
                (lambda d: d["chart"].update(source_sha256="2" * 64), "different chart"),
                (lambda d: d["chart"].update(geometry_basis="mid_sync"), "different chart"),
                (lambda d: d["lines"][0]["a"].update(bar_start_ms=2000), "saved H4 opening"),
                (lambda d: d["lines"][0]["a"].update(bar_start_ms=1000), "different H4 candles"),
                (lambda d: d["lines"][0]["a"].update(price="0"), "positive decimal price"),
                (lambda d: d["lines"][0].update(available_at_ms=3999), "after both anchor receipts")):
            candidate = deepcopy(self.document)
            change(candidate)
            self.assertIn(expected, annotation_results(candidate, self.chart, self.candles, [])["error"])

    def test_target_trade_inspects_original_action_and_safety_at_recorded_receipts(self):
        raw, at = winning_tape()
        tape = quotes.Tape(raw)
        saved = quote_replay.evaluate(tape, as_of=at + 703, tick="0.0001", profile=breaks.FXR_PROFILE)
        view = replay_viewer.quote_viewer_data(tape, saved)
        events = evidence(view, "ACCOUNT", lambda item: item["event"]["kind"] in ("ENTRY_FILL", "EXIT_FILL"))
        [(entry_index, entry_receipt, entry), (exit_index, exit_receipt, exit_)] = events
        before, opened, closed = browser_states(view, [entry_index - 1, entry_index, exit_index])
        frame = entry["h4_frame_id"]
        link = opened["setupEvidence"][frame]
        self.assertEqual([], before["fills"])
        self.assertEqual((at + 701, at + 702), (entry_receipt, exit_receipt))
        self.assertEqual((at + 1, at + 2), (entry["quote"]["source"], exit_["quote"]["source"]))
        self.assertEqual(("1.1068", "TARGET_QUOTE"), (opened["held"]["target"], exit_["trade"]["reason"]))
        self.assertGreater(Fraction(exit_["trade"]["net_usd"]), 0)
        self.assertEqual(link, closed["setupEvidence"][frame])
        self.assertEqual(("action", "safety"), (link["action"]["role"], link["safety"]["role"]))
        self.assertTrue(all(link[role]["available_at"] <= link["item"]["value"]["available_at"]
                            for role in ("action", "safety")))
