"""Receipt-time pivot candidates, bounce contacts and setup explanations."""
from collections import deque
from fractions import Fraction
from pathlib import Path
import shutil
import tempfile
import unittest

from forex_demo_lab.trendline import breaks, fills, pivots, replay_viewer
from test_trendline_bounce_177 import fixture
from test_trendline_data_163 import files, rows_for
from test_trendline_entries_174 import opening_hour
from test_trendline_pivots_166 import bars_for
from test_trendline_viewer_187 import browser_states, create_reports, evidence, load


def project_candidates(source, indexed_bars):
    detector = pivots.PivotStream(source)
    window = deque(maxlen=2 * pivots.RADIUS)
    active, groups = {}, []
    for index, bar in indexed_bars:
        items = []

        def add(at, kind, value):
            if at != bar.available:
                raise AssertionError("candidate did not use its H4 receipt")
            items.append({"kind": kind, "value": value})

        points = detector.observe(bar)
        for point in points:
            add(point.confirmed_at, "PIVOT", point.record())
        active = replay_viewer._pivot_frontier(window, active, index, bar, points, add)
        groups.append({"at": bar.available, "items": items})
    return {"groups": groups}


def bounce_files(folder):
    source, bars = fixture(end=61, approaches={50: (".1", "1"), 51: ("0", "0"),
                                              55: (".1", "1"), 56: ("0", "0"), 61: (".1", "1")})
    value = source.record()
    rows = rows_for(value)[:len(bars) * 4]
    for index, row in enumerate(rows):
        bar = bars[index // 4].record()
        row.update({key: fills.text(Fraction("1.1") + (Fraction(bar[key]) - 100) / 1000)
                    for key in ("open", "high", "low", "close")})
        row["available_at"] = row["end"]
    opening = opening_hour(fills.PriceModel(source).entry_window(bars[-1].end), "1.102")
    descriptor, hours, _ = files(folder, value, rows + [opening.record()])
    return descriptor, hours, opening.available_at


class ProvisionalPivotTests(unittest.TestCase):
    def test_candidate_countdown_agrees_with_confirmation_and_saved_prefix(self):
        rows = [["100", "105", "95", "100"] for _ in range(7)]
        rows[3][1] = "110"
        source, bars = bars_for(rows)
        complete = project_candidates(source, enumerate(bars))
        for size in (4, 5, 6):
            self.assertEqual(complete["groups"][:size], project_candidates(source, enumerate(bars[:size]))["groups"])
        updates = evidence(complete, "PIVOT_CANDIDATES")
        self.assertEqual([3, 2, 1], [value["active"][0]["right_bars_needed"] for _, _, value in updates[:-1]])
        [(_, confirmed_at, point)] = evidence(complete, "PIVOT")
        self.assertEqual(bars[6].available, confirmed_at)
        self.assertEqual(point["id"], updates[0][2]["active"][0]["id"])
        self.assertEqual([], updates[-1][2]["active"])
        self.assertEqual("CONFIRMED", updates[-1][2]["resolved"][0]["reason"])

    def test_tie_gap_and_dual_extreme_clear_only_on_new_evidence(self):
        for change, indices, hit_at, expected in (
                ((5, 1, "110"), range(7), 5, ["RIGHT_EXTREME_OR_TIE"]),
                (None, (0, 1, 2, 3, 4, 6), 6, ["DATA_GAP"]),
                ((3, 2, "90"), range(7), 6, ["DUAL_EXTREME", "DUAL_EXTREME"])):
            with self.subTest(expected=expected):
                rows = [["100", "105", "95", "100"] for _ in range(7)]
                rows[3][1] = "110"
                if change is not None:
                    index, field, value = change
                    rows[index][field] = value
                source, bars = bars_for(rows)
                view = project_candidates(source, ((i, bars[i]) for i in indices))
                self.assertFalse(evidence(view, "PIVOT"))
                [(_, at, update)] = evidence(view, "PIVOT_CANDIDATES", lambda value: bool(value["resolved"]))
                self.assertEqual(bars[hit_at].available, at)
                self.assertEqual(expected, [value["reason"] for value in update["resolved"]])


class BounceViewerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        temp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(temp.cleanup)
        root = Path(temp.name)
        descriptor, hours, cls.receipt = bounce_files(root)
        directory = root / "saved"
        create_reports(descriptor, hours, directory, "--profile", breaks.BNC_PROFILE, "--as-of", str(cls.receipt))
        cls.inputs = load(descriptor, directory)
        cls.view = replay_viewer.viewer_data(*cls.inputs)

    @unittest.skipUnless(shutil.which("node"), "Node required for executable cursor verification")
    def test_contacts_appear_at_h4_receipt_with_their_line_and_wick(self):
        outcomes = evidence(self.view, "CONTACT")
        self.assertEqual([(50, "FORMATION_BAR_CONTACT"), (55, "CONTACT_TOO_CLOSE"), (61, "CONTACT")],
                         [(value["bar_index"], value["reason"]) for _, _, value in outcomes])
        idx, at, contact = outcomes[-1]
        before, arrived = browser_states(self.view, [idx - 1, idx])
        self.assertEqual([50, 55], [entry["item"]["value"]["bar_index"] for entry in before["contacts"]])
        evidence_row = arrived["contacts"][-1]
        self.assertEqual(contact["line_id"], evidence_row["line"]["line_id"])
        joined = arrived["setupEvidence"][contact["h4_frame_id"]]
        self.assertEqual(joined["action"], evidence_row["line"])
        self.assertEqual(arrived["candles"][-1]["low"], evidence_row["wick"])
        self.assertEqual(at, arrived["candles"][-1]["available"])

    def test_setup_search_and_skipped_opening_keep_their_own_evidence(self):
        cases = evidence(self.view, "SETUP", lambda decision: decision["bar_index"] == 55)
        [(_, _, blocked)] = cases
        self.assertEqual("CONTACT_TOO_CLOSE", blocked["reason"])
        self.assertEqual(1, blocked["line_search"]["action"]["action_lines"])
        frame = self.inputs[1]["action_replay"]["frames"][55]
        self.assertEqual(frame["snapshot_reasons"], blocked["line_search"]["action"]["snapshot_reasons"])
        [(_, reserved_at, reserved), (_, skipped_at, skipped)] = evidence(self.view, "ADMISSION")
        self.assertEqual("AWAITING_ENTRY_BAR", reserved["reason"])
        self.assertEqual(self.receipt, skipped_at)
        self.assertGreater(skipped_at, reserved_at)
        self.assertEqual("STOP_ALREADY_CROSSED", skipped["reason"])
        self.assertEqual(reserved["request"], skipped["request"])
        self.assertEqual(reserved["h4_frame_id"], skipped["h4_frame_id"])
        self.assertFalse(evidence(self.view, "ACCOUNT", lambda value: value["event"]["kind"] == "ENTRY_FILL"))
