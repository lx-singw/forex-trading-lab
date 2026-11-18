"""Saved Level B viewer and executable browser cursor projection."""
from copy import deepcopy
from fractions import Fraction
from hashlib import sha256
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from forex_demo_lab.trendline import data, fills, replay_viewer
from test_trendline_data_163 import files
from test_trendline_entries_174 import fixture
from test_trendline_exits_181 import suffix

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ("setups.json", "entries.json", "exits.json", "ledger.json")


def fixture_files(folder, crossed=False):
    declaration, prefix = fixture()
    gap = ("102",) * 4
    inside = ("104.4", "104.9", "102.75", "104.4")
    candles = (gap,) if crossed else (inside, inside, inside, inside, gap)
    continuation = suffix(declaration, prefix, *candles)
    rows = prefix + continuation
    for row in rows:
        for key in ("open", "high", "low", "close"):
            row[key] = fills.text(Fraction("1.1") + (Fraction(row[key]) - 100) / 1000)
    descriptor, hours, _ = files(folder, declaration, rows)
    return descriptor, hours, continuation[0]["start"]


def create_reports(descriptor, hours, output, *options):
    proc = subprocess.run([sys.executable, str(ROOT / "scripts/trendline-breaks-173.py"), str(descriptor),
                           str(hours), str(output), "--tick-size", "0.0001", "--ledger", *options],
                          capture_output=True, text=True)
    if proc.returncode != 0:
        raise AssertionError(proc.stderr)


def load(descriptor, root):
    source = data.Declaration.from_record(data.read_json(descriptor)[0])
    return (source, *(data.read_json(root / file)[0] for file in REPORTS))


def evidence(view, kind, predicate=lambda _: True):
    return [(i, group["at"], item["value"]) for i, group in enumerate(view["groups"])
            for item in group["items"] if item["kind"] == kind and predicate(item["value"])]


def browser_states(view, indices):
    js = replay_viewer.TEMPLATE.read_text(encoding="utf-8").split("// CURSOR_PROJECTION\n")[1].split(
        "// END_CURSOR_PROJECTION")[0]
    program = js + """
const fs=require('fs');
const {view,indices}=JSON.parse(fs.readFileSync(0,'utf8'));
process.stdout.write(JSON.stringify(indices.map(i=>stateAt(view,i))));
"""
    result = subprocess.run(["node", "-e", program], input=json.dumps({"view": view, "indices": indices}),
                            capture_output=True, text=True, check=True)
    return json.loads(result.stdout)


class ReplayViewerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        workspace = tempfile.TemporaryDirectory()
        cls.addClassCleanup(workspace.cleanup)
        cls.root = Path(workspace.name)
        cls.descriptor, cls.hours, cls.trigger = fixture_files(cls.root)
        cls.reports = cls.root / "full"
        create_reports(cls.descriptor, cls.hours, cls.reports)
        cls.inputs = load(cls.descriptor, cls.reports)
        cls.view = replay_viewer.viewer_data(*cls.inputs)

    @unittest.skipUnless(shutil.which("node"), "Node required for executable cursor verification")
    def test_javascript_reveals_pivot_and_revisions_only_on_receipt(self):
        i, at, pivot = evidence(self.view, "PIVOT")[0]
        prior, arrived = browser_states(self.view, [i - 1, i])
        self.assertLess(pivot["occurred_at"], at)
        self.assertNotIn(pivot["id"], {p["id"] for p in prior["pivots"]})
        self.assertIn(pivot, arrived["pivots"])
        i, _, line = evidence(self.view, "LINE", lambda v: v["revision"] == 1)[0]
        prior, arrived = browser_states(self.view, [i - 1, i])
        key = line["role"] + ":" + line["line_id"]
        self.assertNotIn(key, prior["lines"])
        self.assertEqual(line, arrived["lines"][key])
        i, _, poked = evidence(self.view, "LINE", lambda v: v["view"]["status"] == "POKED")[0]
        prior, arrived = browser_states(self.view, [i - 1, i])
        key = poked["role"] + ":" + poked["line_id"]
        self.assertIsNone(prior["lines"][key]["poke_index"])
        self.assertEqual(poked["poke_index"], arrived["candles"][-1]["index"])
        self.assertEqual("POKED", arrived["lines"][key]["view"]["status"])

    @unittest.skipUnless(shutil.which("node"), "Node required for executable cursor verification")
    def test_javascript_fill_stop_and_cash_follow_receipt(self):
        [(first, receipt, entry), (last, close_receipt, departure)] = evidence(
            self.view, "ACCOUNT", lambda row: row["event"]["kind"] in ("ENTRY_FILL", "EXIT_FILL"))
        self.assertLess(entry["event"]["effective_at"], receipt)
        self.assertLess(departure["event"]["effective_at"], close_receipt)
        prior, held, before_exit, closed = browser_states(self.view, [first - 1, first, last - 1, last])
        self.assertEqual([], prior["fills"])
        self.assertIsNone(prior["held"])
        self.assertEqual(entry["event"]["attempt_id"], prior["reservation"])
        self.assertEqual("10000", prior["account"]["cash_usd"])
        self.assertIsNone(held["reservation"])
        self.assertEqual("1.1026", held["held"]["stop"])
        self.assertEqual(entry["h4_frame_id"], held["held"]["h4_frame_id"])
        self.assertEqual("9999.58", held["account"]["cash_usd"])
        self.assertEqual(1, len(before_exit["fills"]))
        self.assertIsNone(closed["held"])
        self.assertEqual("-31.56", closed["fills"][-1]["trade"]["net_usd"])
        self.assertEqual("9968.44", closed["account"]["cash_usd"])

    def test_earlier_saved_replay_matches_later_receipt_prefix(self):
        earlier = self.root / "prefix"
        create_reports(self.descriptor, self.hours, earlier, "--as-of", str(self.trigger))
        prefix = replay_viewer.viewer_data(*load(self.descriptor, earlier))
        selected = [group for group in self.view["groups"] if group["at"] <= self.trigger]
        index, _, boundary = evidence(prefix, "END")[0]
        self.assertEqual("RESERVED", boundary["status"])
        self.assertEqual(index, len(selected) - 1)
        observed = deepcopy(prefix["groups"])
        observed[index]["items"].pop()
        self.assertEqual(selected, observed)

    def test_skip_reason_is_revealed_at_opening_row_receipt(self):
        folder = self.root / "crossed"
        folder.mkdir()
        descriptor, hours, _ = fixture_files(folder, crossed=True)
        output = folder / "reports"
        create_reports(descriptor, hours, output)
        view = replay_viewer.viewer_data(*load(descriptor, output))
        [(_, reserved_at, _), (_, settled_at, settled)] = evidence(view, "ADMISSION")
        self.assertEqual("STOP_ALREADY_CROSSED", settled["reason"])
        self.assertGreater(settled_at, reserved_at)
        self.assertEqual([], evidence(view, "ACCOUNT", lambda v: v["event"]["kind"] == "ENTRY_FILL"))

    def test_rejects_mixed_reports_and_future_account_evidence(self):
        source, setups, priced, paths, account = self.inputs
        modified = deepcopy(account)
        modified["cost_profile"] = "adverse"
        with self.assertRaisesRegex(ValueError, "costs or scope mismatch"):
            replay_viewer.viewer_data(source, setups, priced, paths, modified)
        modified = deepcopy(account)
        modified["events"][-1]["available_at"] = account["as_of"] + 1
        with self.assertRaisesRegex(ValueError, "receipt scope|released position"):
            replay_viewer.viewer_data(source, setups, priced, paths, modified)

    def test_export_binds_reports_and_refuses_replacing_html(self):
        destination = self.root / "viewer"
        program = [sys.executable, str(ROOT / "scripts/trendline-viewer-187.py"), str(self.descriptor),
                   str(self.reports), str(destination)]
        exported = subprocess.run(program, capture_output=True, text=True)
        self.assertEqual(0, exported.returncode, exported.stderr)
        manifest = json.loads((destination / "manifest.json").read_text())
        self.assertEqual(set(REPORTS), set(manifest["reports"]))
        self.assertEqual("bid_only", manifest["geometry_basis"])
        html = (destination / "replay.html").read_bytes()
        self.assertEqual(manifest["html_sha256"], sha256(html).hexdigest())
        repeated = subprocess.run(program, capture_output=True, text=True)
        self.assertNotEqual(0, repeated.returncode)
        self.assertEqual(html, (destination / "replay.html").read_bytes())

    def test_render_escapes_data_inside_offline_document(self):
        tag = "</script><img src=x onerror=alert(1)>"
        html = replay_viewer.render({"profile": tag})
        self.assertNotIn(tag, html)
        self.assertIn(r"\u003c/script>", html)
        self.assertIn("connect-src 'none'", html)
