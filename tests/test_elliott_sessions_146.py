"""Invented UTC schedules, not a broker timezone/calendar certification."""
from copy import deepcopy
from decimal import Decimal
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from forex_demo_lab import elliott_sessions_146 as s
from forex_demo_lab.elliott_full.contracts import Bar, digest, validate_bundle


def schedule(lengths=(24,), closures=(), partial=False):
    cursor = s.START+22*s.HOUR  # Explicit non-midnight open; no server heuristic.
    start = cursor
    segments = []
    for index, hours in enumerate(lengths):
        end = cursor+int(hours*s.HOUR)
        grid = lambda step: list(range(cursor, end, step))+[end]
        segments.append({"kind": "session", "label": f"session_{index}",
                         "start": cursor, "end": end, "h1": grid(s.HOUR),
                         "h4": grid(4*s.HOUR), "partial": partial})
        cursor = end
        if index < len(closures) and closures[index]:
            end = cursor+int(closures[index]*s.HOUR)
            segments.append({"kind": "closure", "start": cursor, "end": end, "reason": "invented"})
            cursor = end
    return {"kind": "invented_session_calendar_146", "scope": {"start": start, "end": cursor},
            "finalization_delay_ms": 2000, "segments": segments}


def hour(w, index=0, available=None):
    p = Decimal("1.10")+Decimal(index)/10000
    return Bar("H1", w.start, w.end, w.end+2000 if available is None else available,
               p, p+Decimal(".0003"), p-Decimal(".0002"), p+Decimal(".0001"),
               digest(["invented", index, w.start]))


def filled(calendar):
    stream = s.Observations(calendar)
    for i, w in enumerate(calendar.frame("H1")):
        stream.observe(hour(w, i))
    return stream


class Sessions146Tests(unittest.TestCase):
    def test_explicit_non_midnight_and_23_25_hour_sessions(self):
        c = s.Calendar.from_record(schedule((23, 25), (48,)))
        days = c.frame("D1")
        self.assertEqual([23*s.HOUR, 25*s.HOUR], [w.end-w.start for w in days])
        self.assertEqual(48, len(c.frame("H1")))
        self.assertEqual([3*s.HOUR, s.HOUR], [c.frame("H4")[5].end-c.frame("H4")[5].start,
                                             c.frame("H4")[-1].end-c.frame("H4")[-1].start])
        self.assertEqual(22*s.HOUR, (days[0].start-s.START) % (24*s.HOUR))

    def test_partial_session_and_terminal_hour_need_explicit_opt_in(self):
        with self.assertRaisesRegex(ValueError, "partial policy"):
            s.Calendar.from_record(schedule((3.5,)))
        c = s.Calendar.from_record(schedule((3.5,), partial=True))
        bars = filled(c).bars()
        self.assertEqual(4, sum(b.timeframe == "H1" for b in bars))
        self.assertEqual(s.HOUR//2, c.frame("H1")[-1].end-c.frame("H1")[-1].start)
        self.assertEqual(1, sum(b.timeframe == "D1" for b in bars))

    def test_twenty_four_hour_day_is_unchanged_by_an_adjacent_short_day(self):
        c = s.Calendar.from_record(schedule((24, 23)))
        stream = filled(c)
        self.assertEqual([24, 23], [len(w.children) for w in c.frame("D1")])
        self.assertEqual(47, sum(b.timeframe == "H1" for b in stream.bars()))
        self.assertEqual(12, sum(b.timeframe == "H4" for b in stream.bars()))
        self.assertEqual("ready", stream.status("D1")["state"])

    def test_calendar_must_cover_scope_without_implicit_gap(self):
        value = schedule((23, 25), (48,));value["segments"].pop(1)
        with self.assertRaisesRegex(ValueError, "gap/overlap"):
            s.Calendar.from_record(value)
        value = schedule();value["scope"]["end"] += 1
        with self.assertRaisesRegex(ValueError, "complete bounded"):
            s.Calendar.from_record(value)

    def test_closure_needs_an_explicit_recognized_reason(self):
        value = schedule((24, 24), (48,));value["segments"][1]["reason"] = "guessed_server_name"
        with self.assertRaises(ValueError):s.Calendar.from_record(value)
        value = schedule((24, 24), (48,));del value["segments"][1]["reason"]
        with self.assertRaises(ValueError):s.Calendar.from_record(value)

    def test_unbounded_sessions_and_non_integer_or_repeated_edges_reject(self):
        for hours in (26, 0, -1):
            with self.subTest(hours=hours), self.assertRaises(ValueError):
                s.Calendar.from_record(schedule((hours,), partial=True))
        for edge in (True, "wrong", 1.5, None):
            value = schedule();value["segments"][0]["h1"][1] = edge
            with self.subTest(edge=edge), self.assertRaises(ValueError):s.Calendar.from_record(value)
        value = schedule();value["segments"][0]["h1"][1] = value["segments"][0]["h1"][0]
        with self.assertRaises(ValueError):s.Calendar.from_record(value)

    def test_calendar_rejects_overlap_reordering_and_duplicate_session(self):
        for change in ("overlap", "order", "label"):
            value = schedule((24, 24))
            if change == "overlap":value["segments"][1]["start"] -= 1
            if change == "order":value["segments"].reverse()
            if change == "label":value["segments"][1]["label"] = "session_0"
            with self.subTest(change=change), self.assertRaises(ValueError):
                s.Calendar.from_record(value)

    def test_parent_child_edges_must_align_and_cover_entire_session(self):
        for change in ("middle", "short", "end", "child"):
            value = schedule()
            if change == "middle":value["segments"][0]["h4"][1] -= 1000
            if change == "short":value["segments"][0]["h1"][1] -= 1000
            if change == "end":value["segments"][0]["h1"][-1] -= 1
            if change == "child":value["segments"][0]["h4"][-2] += s.HOUR//2
            with self.subTest(change=change), self.assertRaises(ValueError):
                s.Calendar.from_record(value)

    def test_strict_kind_types_fields_scope_and_size(self):
        changes = (("kind", "qualified_market"), ("finalization_delay_ms", True),
                   ("finalization_delay_ms", 60001), ("password", "blocked"),
                   ("segments", []))
        for key, value in changes:
            plan = schedule();plan[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                s.Calendar.from_record(plan)
        for key, val in (("partial", 1), ("label", "account_123"), ("end", True)):
            plan = schedule();plan["segments"][0][key] = val
            with self.subTest(key=key), self.assertRaises(ValueError):
                s.Calendar.from_record(plan)
        plan = schedule();plan["scope"]["start"] = s.END
        with self.assertRaises(ValueError):s.Calendar.from_record(plan)

    def test_calendar_and_returned_records_cannot_mutate_declared_grid(self):
        plan = schedule();c = s.Calendar.from_record(plan);sha = c.sha256
        plan["segments"][0]["h1"][1] += 3
        copy = c.record();copy["segments"].clear()
        self.assertEqual(sha, c.sha256)
        self.assertEqual(24, len(c.frame("H1")))
        with self.assertRaises(ValueError):c.frame("M5")

    def test_declared_closure_skipped_but_missing_scheduled_bar_is_not(self):
        c = s.Calendar.from_record(schedule((24, 24), (48,)))
        hours = c.frame("H1");days = c.frame("D1")
        self.assertTrue(c.consecutive("H1", hours[23].start, hours[24].start))
        self.assertTrue(c.consecutive("D1", days[0].start, days[1].start))
        self.assertFalse(c.consecutive("H1", hours[22].start, hours[24].start))
        self.assertFalse(c.consecutive("H1", hours[0].start-1, hours[0].start))
        self.assertFalse(c.consecutive("H1", hours[-1].start, hours[-1].start+s.HOUR))

    def test_unknown_calendar_tail_cannot_be_extended_by_closure_guess(self):
        c = s.Calendar.from_record(schedule())
        stream = filled(c)
        with self.assertRaises(ValueError):stream.advance(c.end+60001)
        w = s.Window("H1", c.end, c.end+s.HOUR, (c.end,), "session_unknown")
        with self.assertRaises(ValueError):stream.observe(hour(w))

    def test_closed_period_adds_no_missing_observations_or_bars(self):
        c = s.Calendar.from_record(schedule((24, 24), (48,)))
        stream = s.Observations(c)
        for i, w in enumerate(c.frame("H1")[:24]):stream.observe(hour(w, i))
        before = stream.bars()
        stream.advance(c.frame("D1")[1].start)
        self.assertEqual(before, stream.bars())
        self.assertEqual("ready", stream.status("D1")["state"])
        self.assertEqual([], stream.status("H1")["missing_starts"])

    def test_before_first_completion_no_bar_is_due(self):
        c = s.Calendar.from_record(schedule());stream = s.Observations(c)
        stream.advance(c.start+s.HOUR+1999)
        self.assertEqual("no_completed_bar", stream.status("H1")["state"])
        stream.advance(c.start+s.HOUR+2000)
        self.assertEqual("missing_completed_bar", stream.status("H1")["state"])

    def test_finalizer_hold_and_receipt_gate_are_both_required(self):
        c = s.Calendar.from_record(schedule());stream = s.Observations(c)
        w = c.frame("H1")[0]
        stream.observe(hour(w, available=w.end))
        self.assertEqual((), stream.bars())
        stream.advance(w.end+1999);self.assertEqual((), stream.bars())
        stream.advance(w.end+2000)
        self.assertEqual(w.end+2000, stream.bars()[0].available)

    def test_missing_child_never_filled_by_later_price_or_nominal_close(self):
        c = s.Calendar.from_record(schedule());stream = s.Observations(c)
        for i, w in enumerate(c.frame("H1")):
            if i != 1:stream.observe(hour(w, i))
        bars = stream.bars()
        self.assertFalse(any(b.timeframe == "D1" for b in bars))
        self.assertEqual(5, sum(b.timeframe == "H4" for b in bars))
        self.assertEqual("missing_completed_bar", stream.status("H1")["state"])
        self.assertFalse(stream.status("H4")["historical_coverage_complete"])
        self.assertEqual([c.start], stream.status("D1")["missing_starts"])

    def test_late_child_publication_is_causal_not_backdated(self):
        c = s.Calendar.from_record(schedule());stream = s.Observations(c)
        windows = c.frame("H1")
        for i, w in enumerate(windows):
            if i != 1:stream.observe(hour(w, i))
        earlier = [b.record() for b in stream.bars()]
        late = c.end+5000;stream.observe(hour(windows[1], 1, available=late))
        new = [b for b in stream.bars() if b.timeframe in ("D1", "H4") and b.start == c.start]
        self.assertEqual([late, late], [b.available for b in new])
        self.assertTrue(all(b.available >= late for b in stream.bars() if b.start == windows[1].start))
        self.assertEqual("ready", stream.status("D1")["state"])
        self.assertFalse(any(b["timeframe"] == "D1" for b in earlier))

    def test_aggregation_uses_source_order_exact_ohlc_and_lineage(self):
        c = s.Calendar.from_record(schedule((23, 25), (48,)));stream = filled(c)
        days = [b for b in stream.bars() if b.timeframe == "D1"]
        self.assertEqual(Decimal("1.10"), days[0].open)
        self.assertEqual(Decimal("1.1025"), days[0].high)
        self.assertEqual(Decimal("1.0998"), days[0].low)
        self.assertEqual(Decimal("1.1023"), days[0].close)
        self.assertEqual(Decimal("1.1023"), days[1].open)
        self.assertEqual(Decimal("1.1048"), days[1].close)
        self.assertNotEqual(days[0].lineage, days[1].lineage)
        self.assertEqual(48, sum(b.timeframe == "H1" for b in stream.bars()))

    def test_same_clock_parent_publication_order_and_last_session_endpoint(self):
        c = s.Calendar.from_record(schedule());stream = filled(c)
        self.assertEqual(["D1", "H4", "H1"], [b.timeframe for b in stream.bars() if b.available == c.end+2000])
        self.assertTrue(all(b.end <= c.end for b in stream.bars()))
        last = [b for b in stream.bars() if b.timeframe == "D1"][0]
        self.assertEqual(c.end, last.end)
        self.assertEqual(c.end+2000, last.available)

    def test_lineage_binds_both_child_identity_and_calendar_policy(self):
        original = schedule();c = s.Calendar.from_record(original);stream = filled(c)
        day = next(b for b in stream.bars() if b.timeframe == "D1")
        changed = deepcopy(original);changed["finalization_delay_ms"] = 1999
        altered = next(b for b in filled(s.Calendar.from_record(changed)).bars() if b.timeframe == "D1")
        self.assertEqual(day.open, altered.open);self.assertNotEqual(day.lineage, altered.lineage)
        replacement = s.Observations(c)
        for i, w in enumerate(c.frame("H1")):
            record = hour(w, i).record()
            if i == 0:record["lineage"] = "f"*64
            replacement.observe(Bar(**record))
        self.assertNotEqual(day.lineage, next(b for b in replacement.bars() if b.timeframe == "D1").lineage)

    def test_mutable_or_unhashed_observation_lineage_rejects(self):
        c = s.Calendar.from_record(schedule());stream = s.Observations(c)
        for lineage in (["mutable"], {"mutable": True}, "unhashed"):
            record = hour(c.frame("H1")[0]).record();record["lineage"] = lineage
            with self.subTest(lineage=lineage), self.assertRaises(ValueError):stream.observe(Bar(**record))
        self.assertEqual((), stream.bars())

    def test_receipt_order_can_differ_from_source_order_without_future_borrow(self):
        c = s.Calendar.from_record(schedule());stream = s.Observations(c)
        windows = c.frame("H1")
        stream.observe(hour(windows[1], 1))
        self.assertEqual(1, len(stream.bars()))
        late = windows[1].end+3000
        stream.observe(hour(windows[0], 0, available=late))
        self.assertEqual(2, len(stream.bars()))
        for i, w in enumerate(windows[2:4], 2):stream.observe(hour(w, i))
        parent = next(b for b in stream.bars() if b.timeframe == "H4")
        self.assertEqual(Decimal("1.10"), parent.open)
        self.assertEqual(Decimal("1.1004"), parent.close)

    def test_every_published_prefix_is_unchanged_by_later_observations(self):
        c = s.Calendar.from_record(schedule((23, 25), (48,)))
        stream = s.Observations(c);prefixes = []
        for i, w in enumerate(c.frame("H1")):
            stream.observe(hour(w, i));prefixes.append((stream.clock, stream.bars()))
        final = stream.bars()
        for clock, prefix in prefixes:
            self.assertEqual(prefix, tuple(b for b in final if b.available <= clock))

    def test_invalid_duplicate_closed_misaligned_or_backward_input_is_atomic(self):
        c = s.Calendar.from_record(schedule((24, 24), (48,)))
        stream = s.Observations(c);w = c.frame("H1")[0];stream.observe(hour(w))
        bad = (hour(w), Bar("H1", w.start+1, w.end, w.end+2000, "1", "1", "1", "1", "x"),
               Bar("H4", w.start, w.end, w.end+2000, "1", "1", "1", "1", "x"),
               hour(s.Window("H1", c.frame("D1")[0].end, c.frame("D1")[0].end+s.HOUR, (), "x")))
        before = stream.checkpoint()
        for bar in bad:
            with self.subTest(bar=bar), self.assertRaises(ValueError):stream.observe(bar)
            self.assertEqual(before, stream.checkpoint())
        with self.assertRaises(ValueError):stream.advance(stream.clock-1)
        stream.advance(c.frame("H1")[1].end+5000);before = stream.checkpoint()
        with self.assertRaises(ValueError):stream.observe(hour(c.frame("H1")[1]))
        self.assertEqual(before, stream.checkpoint())

    def test_restart_at_each_prefix_and_finalizer_pending_preserves_results(self):
        c = s.Calendar.from_record(schedule((3.5, 25), (48,), partial=True))
        stream = s.Observations(c)
        for i, w in enumerate(c.frame("H1")):
            stream.observe(hour(w, i, available=w.end))
            restored = s.Observations.restore(c, stream.checkpoint())
            self.assertEqual(stream.report(), restored.report())
            stream = restored
        stream.advance(c.end+2000)
        self.assertEqual(2, sum(b.timeframe == "D1" for b in stream.bars()))
        self.assertEqual(stream.report(), s.Observations.restore(c, stream.checkpoint()).report())

    def test_checkpoint_mutation_cannot_change_running_journal(self):
        c = s.Calendar.from_record(schedule());stream = filled(c)
        checkpoint = stream.checkpoint();before = stream.checkpoint()
        checkpoint["payload"]["observations"][0]["open"] = "9"
        self.assertEqual(before, stream.checkpoint())

    def test_restore_rejects_tampering_calendar_or_source_change(self):
        c = s.Calendar.from_record(schedule());stream = filled(c);saved = stream.checkpoint()
        wrong = schedule();wrong["finalization_delay_ms"] = 2001
        with self.assertRaises(ValueError):s.Observations.restore(s.Calendar.from_record(wrong), saved)
        changed = deepcopy(saved);changed["payload"]["clock"] -= 1
        with self.assertRaises(ValueError):s.Observations.restore(c, changed)
        with patch.object(s, "source_bindings", return_value={"changed": "x"}):
            with self.assertRaises(ValueError):s.Observations.restore(c, saved)
            with self.assertRaises(ValueError):stream.checkpoint()

    def test_manually_corrupted_calendar_indexes_rejected_before_observation(self):
        c = s.Calendar.from_record(schedule())
        forged = s.Calendar(c._json, c.windows[:-1], c.delay, c.start, c.end)
        with self.assertRaises(ValueError):s.Observations(forged)

    def test_rehashed_invalid_journal_still_rejected(self):
        c = s.Calendar.from_record(schedule());saved = filled(c).checkpoint()
        for change in ("duplicate", "order", "clock", "fields"):
            checkpoint = deepcopy(saved);p = checkpoint["payload"]
            if change == "duplicate":p["observations"].append(p["observations"][-1])
            if change == "order":p["observations"].reverse()
            if change == "clock":p["clock"] = c.start
            if change == "fields":p["observations"][0]["account"] = "blocked"
            checkpoint["sha256"] = digest(p)
            with self.subTest(change=change), self.assertRaises(ValueError):s.Observations.restore(c, checkpoint)

    def test_invented_report_cannot_enter_existing_bundle_or_market_admission(self):
        from forex_demo_lab.elliott_full.admission import study_status, DemoBoundary
        before = study_status();c = s.Calendar.from_record(schedule());report = filled(c).report()
        with self.assertRaises(ValueError):validate_bundle(report)
        self.assertFalse(report["orders_available"]);self.assertFalse(report["returns_computed"])
        self.assertEqual(before, study_status())
        self.assertTrue(all(cell["status"] == "UNAVAILABLE" for cell in before["cells"]))
        self.assertFalse(DemoBoundary().submission_status()["available"])

    def test_public_cli_runs_only_embedded_invented_case_and_exclusive_output(self):
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp)/"demo"
            args = [sys.executable, str(root/"scripts"/"elliott-sessions-146.py"), str(out)]
            result = subprocess.run(args, capture_output=True, text=True)
            self.assertEqual(0, result.returncode, result.stderr)
            report = json.loads((out/"demonstration.json").read_text())
            self.assertEqual("missing_completed_bar", report["before_late_child"]["coverage"]["D1"]["state"])
            self.assertEqual("ready", report["after_late_child"]["coverage"]["D1"]["state"])
            self.assertTrue(report["restart_equal"])
            self.assertFalse(report["orders_available"])
            self.assertNotEqual(0, subprocess.run(args, capture_output=True).returncode)
            self.assertNotEqual(0, subprocess.run(args+["--source", "reserved"], capture_output=True).returncode)


if __name__ == "__main__":unittest.main()
