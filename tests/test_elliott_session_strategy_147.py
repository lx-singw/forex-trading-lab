"""Invented schedule integration; declared counts are labelled component checks."""
from copy import deepcopy
from dataclasses import replace
from dataclasses import asdict
import importlib.util
from itertools import groupby
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from forex_demo_lab import elliott_session_strategy_147 as s
from forex_demo_lab import elliott_sessions_146 as observations
from forex_demo_lab.elliott_full.contracts import Bar, D, digest
from forex_demo_lab.elliott_full.strategy import Strategy
from forex_demo_lab.elliott_full.setups import Policy
from forex_demo_lab.elliott_full.interpretations import context_state
from test_elliott_sessions_146 import schedule, hour, filled
from test_elliott_full_policy import counts, history, mirrored


def mapped(count,calendar,frame="H1",extra=8):
    """Declared-count component fixture; does not claim automatic discovery."""
    windows=calendar.frame(frame)
    def node(n):
        return replace(n,anchors=tuple(replace(p,time=windows[p.index].end,
                       available=windows[p.index+p.radius].end+calendar.delay) for p in n.anchors),
                       children=tuple(node(child) for child in n.children))
    c=replace(count,legs=tuple(node(n) for n in count.legs))
    rows=[replace(b,timeframe=frame,start=w.start,end=w.end,available=w.end+calendar.delay,
                  lineage=digest(["invented_mapped",frame,i]))
          for i,(b,w) in enumerate(zip(history(count,extra),windows))]
    return c,rows


def closed_calendar(days=8):
    return observations.Calendar.from_record(schedule((24,)*days,(0,0,0,48)))


class SessionStrategy147Tests(unittest.TestCase):
    def test_strategy_rejects_invalid_coverage_interface(self):
        for bad in (False,0,{},object()):
            with self.subTest(bad=bad), self.assertRaises(ValueError):Strategy(bad)

    def test_coverage_is_immutable_and_forks_share_only_schedule(self):
        coverage=s.Coverage(closed_calendar());strategy=Strategy(coverage);fork=strategy.fork()
        self.assertIs(coverage,fork.coverage);self.assertIs(coverage,fork.policy.coverage)
        with self.assertRaises(AttributeError):coverage.calendar=None
        with self.assertRaises(AttributeError):del coverage.calendar
        with self.assertRaises(TypeError):coverage._indexes["H1"][0]=1
        fork.policy.groups["invented"]={"consumed":True}
        self.assertNotIn("invented",strategy.policy.groups)

    def test_unknown_edges_early_finalization_and_unsupported_frames_reject(self):
        c=closed_calendar();coverage=s.Coverage(c);bar=hour(c.frame("H1")[0])
        for bad in (replace(bar,start=bar.start+1),replace(bar,end=bar.end-1),
                    replace(bar,available=bar.end+1999),replace(bar,lineage=["mutable"])):
            with self.subTest(bar=bad), self.assertRaises(ValueError):coverage.validate(bad)
        with self.assertRaises(ValueError):coverage.validate("bad")

    def test_coverage_due_equality_and_missing_prefix(self):
        c=closed_calendar();coverage=s.Coverage(c);w=c.frame("H1")[0];bar=hour(w)
        self.assertEqual("no_completed_scheduled_bar",coverage.issue("H1",[],bar.available-1))
        self.assertEqual("missing_completed_scheduled_bar",coverage.issue("H1",[],bar.available))
        self.assertIsNone(coverage.issue("H1",[bar],bar.available))
        later=hour(c.frame("H1")[1])
        self.assertEqual("missing_completed_scheduled_bar",coverage.issue("H1",[later],later.available))
        self.assertEqual("missing_or_unavailable_scheduled_bar",coverage.issue("H1",[bar,bar],later.available))
        self.assertEqual("calendar_boundary_unknown",coverage.issue("H1",[],c.start-1))

    def test_closure_clock_needs_no_missing_parent_but_next_deadline_does(self):
        c=observations.Calendar.from_record(schedule((24,)*100,tuple([0]*98+[48])))
        count,rows=mapped(counts(),c,"D1")
        strategy=Strategy(s.Coverage(c));strategy.bars["D1"]=rows
        strategy.counts["D1"]={"interpretations":[count],"nodes":list(count.legs),"incomplete":False}
        with patch("forex_demo_lab.elliott_full.strategy.context_state",wraps=context_state) as compute:
            strategy._contexts(rows[-1].available);self.assertEqual(1,strategy.contexts["D1"])
            strategy._contexts(rows[-1].end+24*observations.HOUR)
            self.assertEqual(1,strategy.contexts["D1"]);self.assertEqual(1,compute.call_count)
            next_window=c.frame("D1")[99]
            strategy._contexts(next_window.end+c.delay)
            self.assertIsNone(strategy.contexts["D1"])
            self.assertEqual("missing_completed_scheduled_bar",strategy.context_details["D1"]["stage"])
            self.assertEqual(1,compute.call_count)

    def test_context_continuity_across_closure_and_permanent_breach_both_sides(self):
        c=observations.Calendar.from_record(schedule((24,)*100,tuple([0]*94+[48])))
        for raw in (counts(),mirrored(counts())):
            count,rows=mapped(raw,c,"D1");coverage=s.Coverage(c)
            self.assertIsNone(context_state([count],rows[-1],history=rows)["side"])
            self.assertEqual(count.side,context_state([count],rows[-1],history=rows,consecutive=coverage.consecutive)["side"])
            altered=list(rows)
            key="low" if count.side==1 else "high"
            altered[95]=replace(altered[95],**{key:count.terminal.price-count.side*D(".0001")})
            self.assertIsNone(context_state([count],altered[-1],history=altered,consecutive=coverage.consecutive)["side"])

    def test_context_still_rejects_an_omitted_scheduled_bar(self):
        c=closed_calendar()
        # Preserve count index references by using a gap in a late extension.
        count,rows=mapped(counts(),c);rows.pop(97)
        self.assertIsNone(context_state([count],rows[-1],history=rows,consecutive=s.Coverage(c).consecutive)["side"])

    def test_ew3_opportunity_survives_declared_closure_and_triggers_both_sides(self):
        c=closed_calendar()
        for raw in (counts(),mirrored(counts())):
            count,rows=mapped(raw,c);rows=rows[:95]
            policy=Policy(s.Coverage(c));baseline=Policy()
            self.assertEqual([],policy.update([count],rows,(count.side,)*2));baseline.update([count],rows,(count.side,)*2)
            self.assertEqual("formed",policy.reason)
            for index in (95,96):
                w=c.frame("H1")[index];value=(count.trigger+count.terminal.price)/2 if index==95 else count.trigger+count.side*D(".0002")
                rows.append(Bar("H1",w.start,w.end,w.end+c.delay,value,value+D(".00001"),value-D(".00001"),value,digest([index])))
                signals=policy.update([count],rows,(count.side,)*2)
                old=baseline.update([count],rows,(count.side,)*2)
            self.assertEqual(1,len(signals));self.assertEqual(count.side,signals[0].side)
            self.assertEqual("signal",policy.reason)
            self.assertEqual([],old);self.assertEqual("coverage_break",baseline.reason)
            self.assertTrue(all(g["consumed"] for g in policy.groups.values()))

    def test_missing_hour_consumes_opportunity_instead_of_treating_it_as_closure(self):
        c=closed_calendar();count,rows=mapped(counts(),c);prefix=rows[:95];policy=Policy(s.Coverage(c))
        policy.update([count],prefix,(1,1));prefix.append(rows[96])
        self.assertEqual([],policy.update([count],prefix,(1,1)))
        self.assertEqual("coverage_break",policy.reason)
        self.assertTrue(all(g["consumed"] for g in policy.groups.values()))

    def test_ew5_expiry_counts_scheduled_bars_without_refreshing_on_closure(self):
        c=observations.Calendar.from_record(schedule((24,)*7+(8,24),tuple([0]*7+[48]),partial=True))
        for raw in (counts("EW5"),mirrored(counts("EW5"))):
            count,rows=mapped(raw,c,extra=18);policy=Policy(s.Coverage(c))
            formation=count.terminal.index+4;prefix=rows[:formation+1]
            policy.update([count],prefix,(count.side,)*2);expiry=next(iter(policy.groups.values()))["expiry_index"]
            self.assertEqual(formation+10,expiry)
            for row in rows[formation+1:expiry+2]:
                prefix.append(row);self.assertEqual([],policy.update([count],prefix,(count.side,)*2))
            self.assertEqual("consumed_or_expired",policy.reason)
            self.assertEqual(expiry,next(iter(policy.groups.values()))["expiry_index"])

    def test_ew5_trigger_crosses_declared_closure_in_both_directions(self):
        c=observations.Calendar.from_record(schedule((24,)*7+(8,24),tuple([0]*7+[48]),partial=True))
        for raw in (counts("EW5"),mirrored(counts("EW5"))):
            count,rows=mapped(raw,c,extra=18);prefix=rows[:175];policy=Policy(s.Coverage(c))
            policy.update([count],prefix,(count.side,)*2)
            for index in (175,176):
                bar=rows[index]
                value=bar.close if index==175 else count.trigger+count.side*D(".0002")
                prefix.append(replace(bar,open=value,close=value,high=value+D(".00001"),low=value-D(".00001")))
                signals=policy.update([count],prefix,(count.side,)*2)
            self.assertEqual(1,len(signals));self.assertEqual((count.side,"EW5"),(signals[0].side,signals[0].kind))
            self.assertEqual([],policy.update([count],prefix,(count.side,)*2))

    def test_closed_session_blocks_new_decision_eligibility(self):
        c=closed_calendar();coverage=s.Coverage(c);close=c.frame("D1")[3].end
        self.assertTrue(coverage.is_open(close-1));self.assertFalse(coverage.is_open(close))
        self.assertFalse(coverage.is_open(close+24*observations.HOUR))
        self.assertTrue(coverage.is_open(c.frame("D1")[4].start))
        self.assertFalse(coverage.ready({f:[] for f in observations.FRAMES},close))

    def test_h1_eligibility_checks_all_timeframe_coverage_after_warmup(self):
        c=observations.Calendar.from_record(schedule((24,)*254));coverage=s.Coverage(c)
        histories={f:[Bar(f,w.start,w.end,w.end+c.delay,"1.1","1.1","1.1","1.1",digest([f,i]))
                      for i,w in enumerate(c.frame(f)) if w.end<=c.frame("D1")[252].end]
                   for f in observations.FRAMES}
        now=c.frame("D1")[252].end+c.delay
        self.assertTrue(coverage.ready(histories,now))
        histories["H4"].pop(20)
        self.assertFalse(coverage.ready(histories,now))
        self.assertEqual("missing_completed_scheduled_bar",coverage.issue("H4",histories["H4"],now))

    def test_raw_observation_pipeline_snapshots_remain_unchanged_at_every_prefix(self):
        c=observations.Calendar.from_record(schedule((23,25),(48,)))
        source=filled(c);replay=s.DecisionReplay(c);prefix=[]
        for bar in source.bars():
            self.assertEqual([],replay.publish(bar))
            self.assertEqual(prefix,replay.strategy.snapshots[:-1])
            prefix=deepcopy(replay.strategy.snapshots)
        self.assertEqual(63,len(prefix))
        self.assertTrue(all("session_coverage" in snap for snap in prefix))
        self.assertFalse(replay.state()["orders_available"])

    def test_strategy_validates_calendar_before_mutating_history(self):
        c=closed_calendar();strategy=Strategy(s.Coverage(c));bar=hour(c.frame("H1")[0])
        with self.assertRaises(ValueError):strategy.on_bar(replace(bar,start=bar.start+1))
        self.assertEqual([],strategy.snapshots);self.assertTrue(all(not rows for rows in strategy.bars.values()))

    def test_replay_invalid_bar_is_atomic_and_exact_duplicate_emits_nothing(self):
        c=closed_calendar();replay=s.DecisionReplay(c);bar=hour(c.frame("H1")[0]);replay.publish(bar)
        before=replay.checkpoint();self.assertEqual([],replay.publish(bar));self.assertEqual(before,replay.checkpoint())
        for bad in (replace(bar,close=bar.close+D(".00001")),replace(bar,start=bar.start+1)):
            with self.subTest(bar=bad),self.assertRaises(ValueError):replay.publish(bad)
            self.assertEqual(before,replay.checkpoint())

    def test_late_source_backfill_rejects_without_sorting_or_partial_state(self):
        c=closed_calendar();replay=s.DecisionReplay(c)
        later=hour(c.frame("H1")[1]);replay.publish(later)
        before=replay.checkpoint()
        late=hour(c.frame("H1")[0],available=later.available+1000)
        with self.assertRaisesRegex(ValueError,"bar chronology"):replay.publish(late)
        self.assertEqual(before,replay.checkpoint())

    def test_same_clock_parent_order_rejects_ambiguous_reordering(self):
        c=closed_calendar();replay=s.DecisionReplay(c);bars=filled(c).bars()
        last=[b for b in bars if b.available==c.frame("D1")[0].end+c.delay]
        self.assertEqual(["D1","H4","H1"],[b.timeframe for b in last])
        replay.publish(last[-1]);before=replay.checkpoint()
        with self.assertRaisesRegex(ValueError,"same-clock"):replay.publish(last[0])
        self.assertEqual(before,replay.checkpoint())

    def test_late_multi_parent_publication_batch_is_atomic(self):
        c=closed_calendar();raw=observations.Observations(c);missing=1
        for i,w in enumerate(c.frame("H1")[:24]):
            if i!=missing:raw.observe(hour(w,i))
        replay=s.DecisionReplay(c);published=raw.bars()
        for _,group in groupby(published,key=lambda b:b.available):replay.publish_batch(tuple(group))
        before=replay.checkpoint();w=c.frame("H1")[missing]
        raw.observe(hour(w,missing,available=c.frame("D1")[0].end+5000))
        known={(b.timeframe,b.start) for b in published}
        batch=tuple(b for b in raw.bars() if (b.timeframe,b.start) not in known)
        self.assertEqual(["D1","H4","H1"],[b.timeframe for b in batch])
        with self.assertRaises(ValueError):replay.publish_batch(batch)
        self.assertEqual(before,replay.checkpoint())
        for bad in ([],list(published[:4]),[published[0],published[1]],"bad"):
            with self.subTest(batch=bad),self.assertRaises(ValueError):replay.publish_batch(bad)

    def test_same_clock_multiple_bars_in_one_frame_are_unavailable(self):
        c=closed_calendar();replay=s.DecisionReplay(c);windows=c.frame("H1")
        later=windows[1].end+c.delay
        replay.publish(hour(windows[0],available=later));before=replay.checkpoint()
        with self.assertRaisesRegex(ValueError,"same-clock"):replay.publish(hour(windows[1],available=later))
        self.assertEqual(before,replay.checkpoint())

    def test_restart_after_each_timeframe_and_clock_boundary_matches(self):
        c=observations.Calendar.from_record(schedule((3.5,),( ),partial=True));bars=filled(c).bars()
        replay=s.DecisionReplay(c)
        for bar in bars:
            replay.publish(bar)
            restored=s.DecisionReplay.restore(replay.checkpoint())
            self.assertEqual(replay.state(),restored.state());replay=restored
        replay.advance(c.end+6000)
        self.assertEqual(replay.state(),s.DecisionReplay.restore(replay.checkpoint()).state())
        with self.assertRaises(ValueError):replay.advance(c.end+60001)

    def test_checkpoint_state_journal_source_and_calendar_tampering_reject(self):
        c=closed_calendar();replay=s.DecisionReplay(c);replay.publish(hour(c.frame("H1")[0]));saved=replay.checkpoint()
        for change in ("digest","state","duplicate","calendar","event"):
            altered=deepcopy(saved);p=altered["payload"]
            if change=="digest":altered["digest"]="0"*64
            if change=="state":p["state"]["time"]+=1
            if change=="duplicate":p["events"].append(deepcopy(p["events"][-1]))
            if change=="calendar":p["calendar"]["finalization_delay_ms"]+=1
            if change=="event":p["events"][0]["kind"]="quote"
            if change!="digest":altered["digest"]=digest(p)
            with self.subTest(change=change),self.assertRaises(ValueError):s.DecisionReplay.restore(altered)
        with patch.object(s,"source_bindings",return_value={}):
            with self.assertRaises(ValueError):s.DecisionReplay.restore(saved)
            with self.assertRaises(ValueError):replay.checkpoint()

    def test_checkpoint_mutation_cannot_modify_running_binding_or_journal(self):
        c=closed_calendar();replay=s.DecisionReplay(c);replay.publish(hour(c.frame("H1")[0]))
        before=replay.checkpoint();altered=replay.checkpoint()
        altered["payload"]["bindings"]["adapter"].clear()
        altered["payload"]["events"].clear();altered["payload"]["state"]["snapshots"].clear()
        self.assertEqual(before,replay.checkpoint())

    def test_journal_limit_blocks_mutation_before_checkpoint_becomes_unrestorable(self):
        c=closed_calendar();replay=s.DecisionReplay(c);bar=hour(c.frame("H1")[0]);replay.publish(bar)
        before=replay.checkpoint()
        with patch.object(s,"MAX_EVENTS",1):
            self.assertEqual([],replay.publish(bar))
            with self.assertRaises(ValueError):replay.advance(bar.available+1)
            with self.assertRaises(ValueError):replay.publish(hour(c.frame("H1")[1]))
            self.assertEqual(before,replay.checkpoint())
            self.assertEqual(replay.state(),s.DecisionReplay.restore(before).state())

    def test_actual_market_and_submission_gates_remain_unavailable(self):
        from forex_demo_lab.elliott_full.admission import study_status,DemoBoundary
        self.assertTrue(all(c["status"]=="UNAVAILABLE" for c in study_status()["cells"]))
        self.assertFalse(DemoBoundary().submission_status()["available"])

    def test_public_cli_embedded_pipeline_and_rejected_backfill(self):
        root=Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as temp:
            out=Path(temp)/"demo"
            args=[sys.executable,str(root/"scripts/elliott-session-strategy-147.py"),str(out)]
            done=subprocess.run(args,text=True,capture_output=True)
            self.assertEqual(0,done.returncode,done.stderr)
            result=json.loads((out/"demonstration.json").read_text())
            self.assertTrue(result["restart_equal"]);self.assertTrue(result["late_backfill"]["rejected"])
            self.assertTrue(result["late_backfill"]["batch_unchanged"])
            self.assertEqual(63,len(result["continuous"]["snapshots"]))
            self.assertFalse(result["orders_available"])
            self.assertNotEqual(0,subprocess.run(args,capture_output=True).returncode)
            self.assertNotEqual(0,subprocess.run(args+["--source","reserved"],capture_output=True).returncode)

    def test_automatic_warmed_common_hourly_ew3_discovery_with_declared_closures(self):
        """All counts/context/signals arise from prices, using the existing template."""
        root=Path(__file__).resolve().parents[1]
        spec=importlib.util.spec_from_file_location("entry147",root/"scripts/elliott-full-shared-entry.py")
        example=importlib.util.module_from_spec(spec);spec.loader.exec_module(example)
        value=example.fixture(1,"target","EW3")
        days=len(value["hours"])//24
        c=observations.Calendar.from_record(schedule((24,)*days,tuple(48 if i%5==4 else 0 for i in range(days-1))))
        calendar_sha=c.sha256
        raw=observations.Observations(c);windows=c.frame("H1")
        cutoff=value["quotes"][0]["time"]
        for i,row in enumerate(value["hours"]):
            if row["available"]>cutoff:break
            w=windows[i]
            raw.observe(Bar("H1",w.start,w.end,w.end+c.delay,row["open"],row["high"],row["low"],row["close"],
                            digest([row["lineage"],calendar_sha,i])))
        replay=s.DecisionReplay(c);signals=[]
        for _,group in groupby(raw.bars(),key=lambda b:b.available):signals.extend(replay.publish_batch(tuple(group)))
        self.assertEqual(1,len(signals));self.assertEqual((1,"EW3"),(signals[0].side,signals[0].kind))
        self.assertEqual({"D1":1,"H4":1},replay.strategy.contexts)
        self.assertTrue(replay.state()["coverage"]["ready"])
        self.assertTrue(all(len(rows)>=253 for rows in replay.strategy.bars.values()))
        self.assertEqual(replay.strategy.bars["H1"][-1].available,signals[0].formed)
        configured=os.environ.get("ELLIOTT_SESSION_STRATEGY_EVIDENCE_DIR")
        if configured:
            result={"kind":"invented_automatic_session_entry_147","calendar":c.record(),"calendar_sha256":calendar_sha,
                    "input_hours_sha256":digest([b.record() for b in raw._hours.values()]),
                    "signals":[asdict(signal) for signal in signals],"contexts":replay.strategy.contexts,
                    "bar_counts":{f:len(rows) for f,rows in replay.strategy.bars.items()},
                    "coverage":replay.state()["coverage"],"sources":s.source_bindings(),
                    "orders_available":False,"market_cells_run":0,"returns_computed":False}
            with (Path(configured)/"automatic-entry.json").open("x",encoding="utf-8") as out:
                json.dump(result,out,indent=2,default=str);out.write("\n")


if __name__=="__main__":unittest.main()
