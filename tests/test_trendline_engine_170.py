"""Invented automatic lifecycle; supplied triggers are not detected trade signals."""
from copy import deepcopy
from dataclasses import replace
from decimal import Decimal
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from forex_demo_lab.trendline import data as d, engine as e, lines as l, lifecycle as j, selection as s
from test_trendline_data_163 import calendar, descriptor, files
from test_trendline_geometry_167 import hourly_fixture
from test_trendline_pivots_166 import bars_for, golden, source_for
from test_trendline_lines_168 import support_rows
from test_trendline_selection_169 import declared_line

ROOT = Path(__file__).resolve().parents[1]


def run_rows(rows,profile="TRL_BRK3_E1",frame="H4",source=None):
    source,bars = bars_for(rows,frame,source)
    replay = e.Engine(source,profile,frame)
    for bar in bars:replay.observe(bar)
    return replay,source,bars


def latest(replay):return replay.report()["frames"][-1]


class Engine170Tests(unittest.TestCase):
    def test_g35_mirrors_form_at47_then_poke_at48(self):
        for side in ("LONG","SHORT"):
            replay,_,_ = run_rows(golden(35,side)["inputs"]["ohlc"])
            report = replay.report()
            self.assertFalse(report["frames"][46]["eligible_line_ids"])
            self.assertEqual(1,len(report["frames"][47]["eligible_line_ids"]))
            self.assertFalse(report["frames"][48]["eligible_line_ids"])
            self.assertEqual(["REGISTER","VALID","POKE"],[v["command"]["op"] for v in report["journal"]["events"]])
            line = report["journal"]["lines"][0]
            self.assertEqual("POKED",line["status"])
            self.assertEqual((17,29),(line["line"]["ray"]["a_index"],line["line"]["ray"]["b_index"]))
            self.assertFalse(report["entry_ready"]);self.assertFalse(report["trigger_detection_available"])

    def test_declared_trigger_consumes_before_current_poke_and_restarts(self):
        source,bars = bars_for(golden(35)["inputs"]["ohlc"])
        replay = e.Engine(source)
        for bar in bars[:48]:replay.observe(bar)
        line_id = latest(replay)["eligible_line_ids"][0]
        frame = replay.observe(bars[48],declared_triggers=[line_id])
        state = replay.report()["journal"]["lines"][0]
        self.assertEqual("TRIGGERED",state["status"]);self.assertTrue(state["group_consumed"])
        self.assertEqual(["REGISTER","VALID","TRIGGER"],[v["command"]["op"] for v in replay.report()["journal"]["events"]])
        restored = e.Engine.restore(source,replay.checkpoint())
        self.assertEqual(replay.report(),restored.report())
        self.assertEqual(frame,restored.observe(bars[48],declared_triggers=[line_id]))

    def test_same_formation_bar_trigger_is_rejected_atomically(self):
        source,bars = bars_for(golden(35)["inputs"]["ohlc"])
        replay = e.Engine(source)
        for bar in bars[:47]:replay.observe(bar)
        expected = s.select(source,bars[:48]).selected[0]
        before = replay.report()
        with self.assertRaises(ValueError):replay.observe(bars[47],declared_triggers=[e.instance_id(expected)])
        self.assertEqual(before,replay.report())
        replay.observe(bars[47]);self.assertEqual(1,len(latest(replay)["eligible_line_ids"]))

    def test_incremental_inspection_matches_batch_at_handwritten_boundaries(self):
        source,bars = bars_for(golden(35)["inputs"]["ohlc"])
        replay = e.Engine(source)
        for index,bar in enumerate(bars):
            frame = replay.observe(bar)
            if index in (20,26,32,46,47,48):
                batch = s.select(source,bars[:index+1]).record()
                self.assertEqual(batch["candidates"],frame["candidates"])
                self.assertEqual(batch["selection"],frame["selection"])

    def test_incremental_forks_do_not_mutate_original_frontiers(self):
        source,bars = bars_for(golden(35)["inputs"]["ohlc"])
        inspector = l.Inspector(source)
        for bar in bars[:33]:inspector.observe(bar)
        before = inspector.snapshot()
        staged = inspector.fork();staged.observe(bars[33])
        self.assertEqual(before,inspector.snapshot())
        self.assertEqual(33,len(inspector.publications));self.assertEqual(34,len(staged.publications))

    def test_valid_pivot_superset_retires_old_and_creates_fresh_group(self):
        replay,_,_ = run_rows(support_rows(count=62,centres=(20,32,44,56)))
        report = replay.report()
        self.assertEqual(["RETIRED","VALID"],sorted(v["status"] for v in report["journal"]["lines"]))
        self.assertEqual(2,len(report["journal"]["groups"]))
        self.assertTrue(all(not g["consumed"] for g in report["journal"]["groups"]))
        self.assertEqual(1,len(report["frames"][58]["eligible_line_ids"]))
        self.assertNotEqual(report["frames"][58]["eligible_line_ids"],report["frames"][59]["eligible_line_ids"])
        self.assertEqual(["REGISTER","VALID","REGISTER","VALID","RETIRE"],[v["command"]["op"] for v in report["journal"]["events"]])

    def test_new_touch_group_does_not_reset_an_old_consumed_group(self):
        source,bars = bars_for(support_rows(count=62,centres=(20,32,44,56)))
        replay = e.Engine(source)
        for bar in bars[:58]:replay.observe(bar)
        old = latest(replay)["eligible_line_ids"][0]
        replay.observe(bars[58],declared_triggers=[old])
        for bar in bars[59:]:replay.observe(bar)
        groups = replay.report()["journal"]["groups"]
        self.assertEqual([False,True],sorted(g["consumed"] for g in groups))
        self.assertEqual(1,len(latest(replay)["eligible_line_ids"]))

    def test_alias_policy_merges_only_exact_union_of_prior_groups(self):
        source = source_for(100)
        book = j.Journal(source)
        # Declared group metadata, not a complete candle-discovery fixture.
        from test_trendline_selection_169 import declared_snapshot
        a,b = declared_line(),declared_line(indices=(0,6,18))
        snap = declared_snapshot(source,(a,b))
        ids = [book.register(snap,v.geometry_id) for v in snap.selected]
        for value in ids:book.validate(snap,value)
        book.trigger_many(declared_snapshot(source,index=41),[ids[0]])
        combined = declared_line(indices=(0,6,12,18),age=42)
        prior = book.states
        groups = e.alias_groups(combined,prior)
        self.assertEqual(2,len(groups))
        snap = declared_snapshot(source,(combined,),index=42)
        new_id = book.register(snap,combined.geometry_id);book.validate(snap,new_id)
        new_group = next(v.group_id for v in book.states if v.line_id == new_id)
        book.merge_groups(snap,(*groups,new_group))
        self.assertTrue(all(v["consumed"] for v in book.report()["groups"]))
        novel = declared_line(indices=(0,6,12,18,24),age=42)
        self.assertEqual((),e.alias_groups(novel,prior))

    def test_search_cap_blocks_eligibility_then_recovers_without_new_group(self):
        source,bars = bars_for(support_rows(count=55))
        replay = e.Engine(source)
        for bar in bars[:51]:replay.observe(bar)
        line = latest(replay)["eligible_line_ids"][0]
        with patch.object(l,"enumerate_pairs",return_value=l.PairSearch((),(),(),257,0,True)):
            blocked = replay.observe(bars[51])
        self.assertTrue(blocked["search_incomplete"]);self.assertFalse(blocked["eligible_line_ids"])
        self.assertEqual("VALID",replay.report()["journal"]["lines"][0]["status"])
        replay.observe(bars[52])
        self.assertEqual([line],latest(replay)["eligible_line_ids"])
        self.assertEqual(2,len(replay.report()["journal"]["events"]))

    def test_search_cap_does_not_suppress_observable_poke(self):
        source,bars = bars_for(support_rows(count=55))
        replay = e.Engine(source)
        for bar in bars[:51]:replay.observe(bar)
        poked = replace(bars[51],low=Decimal("105.0"))
        with patch.object(l,"enumerate_pairs",return_value=l.PairSearch((),(),(),257,0,True)):
            frame = replay.observe(poked)
        self.assertTrue(frame["search_incomplete"])
        self.assertEqual("POKED",replay.report()["journal"]["lines"][0]["status"])

    def test_unknown_gap_blocks_old_line_without_inventing_a_poke(self):
        source,bars = bars_for(support_rows(count=60))
        replay = e.Engine(source)
        for bar in bars[:51]+bars[52:]:replay.observe(bar)
        report = replay.report()
        self.assertEqual("VALID",report["journal"]["lines"][0]["status"])
        self.assertFalse(report["frames"][-1]["eligible_line_ids"])
        self.assertIn("LINE_COVERAGE_INCOMPLETE",report["latest_views"][0]["view"]["reasons"])
        self.assertEqual(report,e.Engine.restore(source,replay.checkpoint()).report())

    def test_declared_calendar_closure_preserves_line_adjacency(self):
        lengths = (24,)*10
        closures = (0,0,0,0,0,0,0,0,48)
        source = d.Declaration.from_record(descriptor(calendar(lengths,closures)))
        replay,_,_ = run_rows(support_rows(count=60),source=source)
        self.assertTrue(latest(replay)["eligible_line_ids"])
        self.assertNotIn("LINE_COVERAGE_INCOMPLETE",replay.report()["latest_views"][0]["view"]["reasons"])

    def test_age501_retirement_and_poke_precedence_even_during_search_cap(self):
        rows = []
        for i in range(552):
            low = Decimal(100)+Decimal(i)/100+(0 if i in (20,32,44) else 2)
            rows.append(["130","150",str(low),"130"])
        source,bars = bars_for(rows)
        replay = e.Engine(source)
        for bar in bars[:551]:replay.observe(bar)
        self.assertEqual("VALID",replay.report()["journal"]["lines"][0]["status"])
        checkpoint = replay.checkpoint()
        with patch.object(l,"enumerate_pairs",return_value=l.PairSearch((),(),(),257,0,True)):
            replay.observe(bars[551])
        self.assertEqual("RETIRED",replay.report()["journal"]["lines"][0]["status"])
        second = e.Engine.restore(source,checkpoint)
        with patch.object(l,"enumerate_pairs",return_value=l.PairSearch((),(),(),257,0,True)):
            second.observe(replace(bars[551],low=Decimal("105.0")))
        self.assertEqual("POKED",second.report()["journal"]["lines"][0]["status"])

    def test_clock_advance_marks_due_missing_bar_without_fake_retirement(self):
        source,bars = bars_for(support_rows(count=55))
        replay = e.Engine(source)
        for bar in bars[:51]:replay.observe(bar)
        before_events = replay.report()["journal"]["events"]
        frame = replay.advance(bars[51].available)
        self.assertEqual("MISSING_COMPLETED_BAR",frame["coverage_state"])
        self.assertFalse(frame["eligible_line_ids"])
        self.assertEqual(before_events,replay.report()["journal"]["events"])
        self.assertEqual(replay.report(),e.Engine.restore(source,replay.checkpoint()).report())

    def test_duplicate_latest_is_noop_and_conflicting_trigger_retry_rejects(self):
        replay,_,bars = run_rows(golden(35)["inputs"]["ohlc"])
        before = replay.report()
        replay.observe(bars[-1]);self.assertEqual(before,replay.report())
        with self.assertRaises(ValueError):replay.observe(bars[-1],declared_triggers=["0"*64])
        self.assertEqual(before,replay.report())

    def test_invalid_bar_or_declared_trigger_cannot_partially_publish(self):
        source,bars = bars_for(golden(35)["inputs"]["ohlc"])
        replay = e.Engine(source)
        for bar in bars[:48]:replay.observe(bar)
        before = replay.report()
        for bar,extra in ((replace(bars[48],available=bars[48].end),()),
                          (replace(bars[48],lineage=bars[0].lineage),()),(bars[46],()),(bars[48],("0"*64,))):
            with self.assertRaises(ValueError):replay.observe(bar,declared_triggers=extra)
            self.assertEqual(before,replay.report())
        replay.observe(bars[48]);self.assertEqual(49,len(replay.publications))

    def test_trace_and_command_bounds_abort_whole_publication(self):
        source,bars = bars_for(golden(35)["inputs"]["ohlc"])
        replay = e.Engine(source);before = replay.report()
        for name,value in (("MAX_TRACE_BYTES",1),("MAX_COMMANDS",0)):
            with patch.object(e,name,value):
                with self.assertRaises(ValueError):replay.observe(bars[0])
            self.assertEqual(before,replay.report())

    def test_report_and_prior_revisions_are_defensive_and_append_only(self):
        source,bars = bars_for(golden(35)["inputs"]["ohlc"])
        replay = e.Engine(source)
        for bar in bars[:48]:replay.observe(bar)
        before = replay.report();tampered = replay.report()
        tampered["latest_views"][0]["view"]["status"] = "BROKEN"
        tampered["frames"][0].clear()
        self.assertEqual(before,replay.report())
        replay.observe(bars[48])
        self.assertEqual(before["frames"],replay.report()["frames"][:48])
        self.assertEqual(before["journal"]["events"],replay.report()["journal"]["events"][:2])

    def test_future_suffix_and_file_binding_do_not_rename_published_frames(self):
        source,bars = bars_for(golden(35)["inputs"]["ohlc"])
        left = e.Engine(source)
        for bar in bars[:48]:left.observe(bar)
        value = source.record();value["input_sha256"] = "1"*64
        other = d.Declaration.from_record(value);right = e.Engine(other)
        for bar in bars[:48]:right.observe(bar)
        self.assertEqual(left.report()["frames"],right.report()["frames"])
        left.observe(bars[48])
        self.assertEqual(right.report()["frames"],left.report()["frames"][:48])
        with self.assertRaises(ValueError):e.Engine.restore(other,left.checkpoint())

    def test_checkpoint_duplicate_reorder_edit_code_and_state_tampering_refused(self):
        replay,source,bars = run_rows(golden()["inputs"]["ohlc"])
        original = replay.checkpoint()
        for change in ("duplicate","reorder","edit","code","state"):
            record = deepcopy(original)
            if change == "duplicate":record["commands"].append(deepcopy(record["commands"][-1]))
            if change == "reorder":record["commands"].reverse()
            if change == "edit":record["commands"][0]["bar"]["lineage"] = "1"*64
            if change == "code":record["source_bindings"] = {}
            if change == "state":record["state_sha256"] = "0"*64
            with self.assertRaises(ValueError):e.Engine.restore(source,record)

    def test_empty_clock_checkpoint_and_code_source_scope_guards(self):
        source = source_for()
        replay = e.Engine(source);replay.advance(source.calendar.start+1000)
        self.assertEqual(replay.report(),e.Engine.restore(source,replay.checkpoint()).report())
        before = replay.report()
        with patch.object(e,"bindings",return_value={}):
            with self.assertRaises(ValueError):replay.advance(replay.clock+1)
        self.assertEqual(before,replay.report())
        replay.profile = "TRL_BRK2_E1"
        with self.assertRaises(ValueError):replay.checkpoint()

    def test_d1_and_bounce_profiles_have_no_action_break_exception(self):
        replay,_,_ = run_rows(support_rows(count=40,centres=(16,22,28)),profile="D1_BRK3",frame="D1")
        self.assertTrue(latest(replay)["eligible_line_ids"])
        self.assertFalse(latest(replay)["action_line_ids"])
        replay,_,_ = run_rows(support_rows(count=55),profile="TRL_BNC_E1")
        self.assertTrue(latest(replay)["eligible_line_ids"])
        self.assertEqual("full",replay.report()["latest_inspection"]["penetration_role"])

    def test_cli_prefix_checkpoint_resume_matches_uninterrupted_and_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            value,rows = hourly_fixture();meta,hours,_ = files(directory,value,rows)
            def run(name,extra=()):
                output = Path(directory)/name
                proc = subprocess.run([sys.executable,str(ROOT/"scripts/trendline-replay-170.py"),str(meta),str(hours),str(output),*extra],capture_output=True,text=True)
                self.assertEqual(0,proc.returncode,proc.stderr)
                return output
            prefix = run("prefix",("--as-of",str(rows[191]["available_at"])))
            full = run("full")
            resumed = run("resumed",("--restore-checkpoint",str(prefix/"checkpoint.json")))
            self.assertEqual((full/"replay.json").read_bytes(),(resumed/"replay.json").read_bytes())
            before = (full/"replay.json").read_bytes()
            proc = subprocess.run([sys.executable,str(ROOT/"scripts/trendline-replay-170.py"),str(meta),str(hours),str(full)],capture_output=True)
            self.assertNotEqual(0,proc.returncode);self.assertEqual(before,(full/"replay.json").read_bytes())

    def test_cli_validation_and_market_kinds_cannot_bypass_loader(self):
        with tempfile.TemporaryDirectory() as directory:
            value,rows = hourly_fixture();meta,hours,value = files(directory,value,rows)
            for index,change in enumerate(({"partition":"validation"},{"kind":"market_trendline_source"})):
                record = deepcopy(value);record.update(change);meta.write_text(json.dumps(record))
                output = Path(directory)/str(index)
                run = subprocess.run([sys.executable,str(ROOT/"scripts/trendline-replay-170.py"),str(meta),str(hours),str(output)],capture_output=True)
                self.assertNotEqual(0,run.returncode);self.assertFalse(output.exists())


if __name__ == "__main__":unittest.main()
