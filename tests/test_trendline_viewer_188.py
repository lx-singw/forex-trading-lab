"""Saved Level Q viewer and receipt-bound trade explanations."""
from copy import deepcopy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from forex_demo_lab.trendline import breaks, data, quote_replay, quotes, replay_viewer
from test_trendline_entries_174 import fixture
from test_trendline_exits_181 import suffix
from test_trendline_levels_180 import target_hours
from test_trendline_quotes_185 import document, history, midpoint, row
from test_trendline_viewer_187 import ROOT, browser_states, evidence


def quote_fixture():
    value, hours = fixture()
    trigger = hours[-1]["end"]
    rows = history(hours) + [
        midpoint(trigger + 1, "104.4", trigger + 2002),
        midpoint(trigger + 2, "104.4", trigger + 2002, "0.00016"),
        midpoint(trigger + 3, "104.4", trigger + 2003, "0.00015"),
        midpoint(trigger + 4, "104.5", trigger + 2004),
        midpoint(trigger + 4, "104.5", trigger + 2004),
        midpoint(trigger + 4, "102", trigger + 2004, "0.001"),
    ]
    return document(value, rows), trigger


def ledger(tape, as_of):
    return quote_replay.evaluate(tape, as_of=as_of, tick="0.0001")


class QuoteViewerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document, cls.trigger = quote_fixture()
        cls.tape = quotes.Tape(cls.document)
        cls.report = ledger(cls.tape, cls.trigger + 2004)
        cls.view = replay_viewer.quote_viewer_data(cls.tape, cls.report)

    def test_receipt_prefix_agrees_before_same_receipt_sequence_group(self):
        through = self.trigger + 2003
        short = replay_viewer.quote_viewer_data(self.tape, ledger(self.tape, through))
        expected = [group for group in self.view["groups"] if group["at"] <= through]
        short["groups"][-1]["items"].pop()
        self.assertEqual(expected, short["groups"])
        same_time = [(item["quote"]["sequence"], item["reason"]) for _, at, item in evidence(self.view, "QUOTE")
                     if at == through + 1]
        sequence = len(self.tape.quotes)
        self.assertEqual([(sequence - 2, "EXECUTABLE"), (sequence - 1, "REPEATED_QUOTE"),
                          (sequence, "EXECUTABLE")], same_time)
        _, _, stale = evidence(self.view, "QUOTE", lambda item: item["reason"] == "STALE_QUOTE")[0]
        self.assertEqual(2001, stale["quote"]["time"] - stale["quote"]["source"])
        self.assertNotIn("modeled_bid", stale)

    @unittest.skipUnless(shutil.which("node"), "Node required for executable cursor verification")
    def test_trade_keeps_the_original_action_and_safety_revisions(self):
        [(opening, received, enter), (closing, released, leave)] = evidence(
            self.view, "ACCOUNT", lambda row: row["event"]["kind"] in ("ENTRY_FILL", "EXIT_FILL"))
        prior, held, closed = browser_states(self.view, [opening - 1, opening, closing])
        frame = enter["h4_frame_id"]
        facts = held["setupEvidence"][frame]
        self.assertEqual(facts, closed["setupEvidence"][frame])
        self.assertEqual("PENDING", prior["admission"]["status"])
        self.assertEqual([], prior["fills"])
        self.assertLess(facts["item"]["value"]["available_at"], enter["quote"]["source"])
        self.assertEqual(("action", "safety"), (facts["action"]["role"], facts["safety"]["role"]))
        self.assertEqual(facts["item"]["value"]["selected_line_id"], facts["action"]["line_id"])
        self.assertEqual(facts["item"]["value"]["safety"]["line_id"], facts["safety"]["line_id"])
        self.assertEqual(received, enter["quote"]["time"])
        self.assertEqual(released, leave["quote"]["time"])
        self.assertEqual("STOP_QUOTE", leave["trade"]["reason"])
        self.assertEqual("-37.02", leave["trade"]["net_usd"])
        self.assertEqual("9962.98", closed["account"]["cash_usd"])
        self.assertIsNotNone(held["held"])
        self.assertIsNone(closed["held"])

    def test_skip_is_revealed_by_the_first_eligible_quote_receipt(self):
        value, hours = fixture()
        at = hours[-1]["end"]
        rows = history(hours) + [midpoint(at + 1, "102", at + 501), midpoint(at + 2, "104.4", at + 502)]
        tape = quotes.Tape(document(value, rows))
        view = replay_viewer.quote_viewer_data(tape, ledger(tape, at + 502))
        [(_, pending_at, pending), (_, skip_at, skip)] = evidence(view, "ADMISSION")
        self.assertEqual((at, "AWAITING_ELIGIBLE_QUOTE"), (pending_at, pending["reason"]))
        self.assertNotIn("quote", pending)
        self.assertEqual((at + 501, "STOP_ALREADY_CROSSED", at + 1), (skip_at, skip["reason"], skip["quote"]["source"]))
        self.assertFalse(evidence(view, "ACCOUNT", lambda item: item["event"]["kind"] == "ENTRY_FILL"))

    def test_protection_keeps_h4_decision_and_first_applicable_quote_separate(self):
        value, hours = fixture()
        value["calendar"]["finalization_delay_ms"] = 1000
        trigger = hours[-1]["end"]
        candles = suffix(value, hours, *(("104.4", "104.9", "103.2", "104.4"),) * 8)
        continuation = history(candles)
        continuation.insert(3, midpoint(trigger + 1001, "104.4"))
        at = candles[-1]["end"] + 1000
        continuation += [row(at - 500, "1.10265", "1.10275", at + 1),
                         row(at + 2, "1.10265", "1.10275", at + 20)]
        tape = quotes.Tape(document(value, history(hours) + continuation))
        before = replay_viewer.quote_viewer_data(tape, ledger(tape, at + 1))
        after = replay_viewer.quote_viewer_data(tape, ledger(tape, at + 20))
        self.assertFalse(evidence(before, "PROTECTION"))
        [(_, _, boundary)] = evidence(before, "END")
        [(_, received, change)] = evidence(after, "PROTECTION")
        self.assertEqual(boundary["open_liability"]["stop"], change["stop"])
        self.assertEqual((at + 20, at, at + 2), (received, change["decision_at"]["time"], change["quote"]["source"]))
        before["groups"][-1]["items"].pop()
        self.assertEqual([group for group in after["groups"] if group["at"] <= at + 1], before["groups"])

    def test_fxr_view_preserves_fixed_target_and_exit_quote(self):
        value, hours = target_hours("LONG")
        at = hours[-1]["start"]
        rows = history(hours[:-1]) + [midpoint(at + 1, "102.2"), midpoint(at + 2, "108"), midpoint(at + 3, "99")]
        tape = quotes.Tape(document(value, rows))
        report = quote_replay.evaluate(tape, as_of=at + 3, tick="0.0001", profile=breaks.FXR_PROFILE)
        view = replay_viewer.quote_viewer_data(tape, report)
        [(_, _, entry), (_, _, settled)] = evidence(
            view, "ACCOUNT", lambda item: item["event"]["kind"] in ("ENTRY_FILL", "EXIT_FILL"))
        self.assertEqual("1.1068", entry["held"]["target"])
        self.assertEqual(("TARGET_QUOTE", "1.1068", at + 2),
                         (settled["trade"]["reason"], settled["event"]["price"], settled["quote"]["source"]))
        self.assertFalse(evidence(view, "PROTECTION"))

    def test_saved_export_binds_checkpoint_and_rejects_changed_tape(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            tape_path, saved, view_path = folder / "tape.json", folder / "saved", folder / "view"
            tape_path.write_text(json.dumps(self.document))
            saved.mkdir()
            report_path = saved / "quote-ledger.json"
            data.write_new(report_path, self.report)
            data.write_new(saved / "checkpoint.json", quote_replay.checkpoint(self.report))
            argv = [sys.executable, str(ROOT / "scripts/trendline-viewer-187.py"), str(tape_path), str(saved)]
            proc = subprocess.run([*argv, str(view_path)], capture_output=True, text=True)
            self.assertEqual(0, proc.returncode, proc.stderr)
            manifest = json.loads((view_path / "manifest.json").read_text())
            self.assertEqual(("Q", "mid_sync", self.tape.sha256),
                             (manifest["data_level"], manifest["geometry_basis"], manifest["tape_sha256"]))
            self.assertEqual(set(manifest["reports"]), {"quote-ledger.json", "checkpoint.json"})
            changed = deepcopy(self.document)
            changed["quotes"][-1]["ask"] = "1.103"
            tape_path.write_text(json.dumps(changed))
            rejected = folder / "rejected"
            with self.assertRaisesRegex(ValueError, "matching invented Level Q ledger and tape"):
                replay_viewer.export(tape_path, saved, rejected)
            self.assertFalse(rejected.exists())
            tape_path.write_text(json.dumps(self.document))
            report_path.write_text(json.dumps({**self.report, "status": "OPEN"}))
            with self.assertRaisesRegex(ValueError, "does not match its checkpoint"):
                replay_viewer.export(tape_path, saved, rejected)
            self.assertFalse(rejected.exists())
