"""Calendar/paper safety components plus a separate automatic discovery replay."""
from copy import deepcopy
from dataclasses import replace
from fractions import Fraction as F
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

from forex_demo_lab import elliott_session_paper_148 as p
from forex_demo_lab import elliott_sessions_146 as o
from forex_demo_lab.elliott_full.contracts import Bar, Quote, D, digest
from forex_demo_lab.elliott_full.execution import Setup
from forex_demo_lab.elliott_full.strategy import Strategy
from test_elliott_sessions_146 import schedule, hour

ROOT=Path(__file__).resolve().parents[1]


def event(kind,value):return {"kind":kind,"value":value.record() if isinstance(value,Quote) else value}


def publish(replay,bars):
    for _,group in groupby(bars,key=lambda b:b.available):
        replay.step(event("bars",[b.record() for b in group]))


class PaperComponents148Tests(unittest.TestCase):
    """Declared pending setups/parents isolate quote gates, not wave discovery."""
    def setUp(self):
        self.side=1
        def declared_contexts(strategy,decision_time=None):strategy.contexts={"D1":self.side,"H4":self.side}
        self.patch=patch.object(Strategy,"_contexts",declared_contexts)
        self.patch.start();self.addCleanup(self.patch.stop)

    def component(self,side=1,profile="base",hours=30,closure=False,kind="EW3"):
        self.side=side
        c=o.Calendar.from_record(schedule((24,)*8,tuple([0]*(int(closure)-1)+[48]) if closure else ()))
        raw=o.Observations(c)
        for i,w in enumerate(c.frame("H1")[:hours]):raw.observe(hour(w,0))
        replay=p.PaperReplay(c,profile);publish(replay,raw.bars())
        replay.pending=Setup("invented_component_"+kind,side,kind,replay.time,replay.time+60000,
                             "1.1001","1.0990" if side==1 else "1.1012",None,"1.0992" if side==1 else "1.1010")
        return replay,c

    def quote(self,replay,offset=2000,bid="1.1001",sequence=0,source=None,open=True):
        now=replay.time+offset
        return Quote(now,now if source is None else source,sequence,bid,D(bid)+D(".0001"),open)

    def test_entry_uses_calendar_and_existing_latency_under_both_costs(self):
        for profile,latency in (("base",250),("adverse",1000)):
            replay,_=self.component(profile=profile);formed=replay.time
            first=self.quote(replay,offset=latency)
            self.assertEqual("signal_timing",replay.step(event("quote",first)))
            self.assertIsNotNone(replay.pending)
            nextq=Quote(formed+latency+1,formed+latency+1,1,"1.1001","1.1002")
            self.assertEqual("entered",replay.step(event("quote",nextq)))
            self.assertIsNone(replay.pending);self.assertIsNotNone(replay.ledger.position)

    def test_expiry_equality_is_allowed_but_one_millisecond_late_cancels(self):
        for delta,expected in ((60000,"entered"),(60001,"no_signal")):
            replay,_=self.component();quote=self.quote(replay,offset=delta)
            self.assertEqual(expected,replay.step(event("quote",quote)))
            if delta==60001:self.assertEqual("expired",replay.cancellations[-1]["reason"])

    def test_clock_expiry_cannot_be_revived_by_duplicate_or_later_quote(self):
        replay,_=self.component();expiry=replay.pending.expires
        replay.step(event("clock",expiry+1));self.assertIsNone(replay.pending)
        self.assertEqual("expired",replay.cancellations[-1]["reason"])
        q=self.quote(replay);replay.step(event("quote",q));before=replay.state()
        self.assertEqual("duplicate",replay.step(event("quote",q)));self.assertEqual(before,replay.state())

    def test_new_pending_is_cancelled_when_required_parent_context_is_lost(self):
        replay,_=self.component();self.side=-1
        self.assertEqual("no_signal",replay.step(event("quote",self.quote(replay))))
        self.assertEqual("parent_context_lost",replay.cancellations[-1]["reason"])
        self.assertIsNone(replay.ledger.position)

    def test_pending_cancels_at_exact_missing_h1_deadline(self):
        replay,c=self.component();w=c.frame("H1")[30]
        # A deliberately longer declared component signal isolates the coverage gate.
        replay.pending=replace(replay.pending,expires=w.end+c.delay+60000,formed=w.end+c.delay-1000)
        replay.step(event("clock",w.end+c.delay))
        self.assertIsNone(replay.pending)
        self.assertEqual("scheduled_coverage_missing",replay.cancellations[-1]["reason"])

    def test_pending_cancels_when_calendar_closes(self):
        replay,c=self.component(hours=23,closure=True);close=c.frame("D1")[0].end
        replay.pending=replace(replay.pending,formed=close-1000,expires=close+60000)
        replay.step(event("clock",close))
        self.assertEqual("calendar_closed",replay.cancellations[-1]["reason"])

    def test_raw_closed_flag_inside_open_session_keeps_signal_for_retry(self):
        replay,_=self.component();q=self.quote(replay,open=False)
        self.assertEqual("unavailable_quote",replay.step(event("quote",q)))
        self.assertIsNotNone(replay.pending)
        fresh=self.quote(replay,offset=1,sequence=1)
        self.assertEqual("entered",replay.step(event("quote",fresh)))

    def test_wide_quote_does_not_consume_pending_and_fresh_narrow_quote_can_enter(self):
        replay,_=self.component();q=self.quote(replay);q=replace(q,ask=q.bid+D(".0003"))
        self.assertEqual("entry_spread",replay.step(event("quote",q)))
        self.assertIsNotNone(replay.pending)
        self.assertEqual("entered",replay.step(event("quote",self.quote(replay,offset=1,sequence=1))))

    def test_stale_and_repeated_source_quotes_cannot_enter(self):
        replay,_=self.component();q=self.quote(replay,offset=4000,source=replay.time+1)
        self.assertEqual("unavailable_quote",replay.step(event("quote",q)))
        repeated=self.quote(replay,offset=1,sequence=1,source=q.source)
        self.assertEqual("unavailable_quote",replay.step(event("quote",repeated)))
        self.assertIsNotNone(replay.pending)
        self.assertEqual("entered",replay.step(event("quote",self.quote(replay,offset=1,sequence=2))))

    def test_raw_duplicate_after_clock_event_never_reapplies_or_resurrects_signal(self):
        replay,_=self.component();q=self.quote(replay);replay.step(event("quote",q))
        replay.step(event("clock",q.time+1));before=replay.state();length=len(replay.events)
        self.assertEqual("duplicate",replay.step(event("quote",q)))
        self.assertEqual(before,replay.state());self.assertEqual(length,len(replay.events))
        with self.assertRaises(ValueError):replay.step(event("quote",replace(q,ask=q.ask+D(".00001"))))
        self.assertEqual(before,replay.state())

    def test_quote_receipt_or_source_reversal_rolls_back_all_state(self):
        replay,_=self.component();q=self.quote(replay);replay.step(event("quote",q));before=replay.state()
        for bad in (replace(q,sequence=1,time=q.time-1,source=q.source-1),
                    replace(q,sequence=1,time=q.time+1,source=q.source-1)):
            with self.subTest(quote=bad),self.assertRaises(ValueError):replay.step(event("quote",bad))
            self.assertEqual(before,replay.state())

    def test_ledger_exit_failure_rolls_back_decision_clock_and_account(self):
        replay,_=self.component();replay.step(event("quote",self.quote(replay)));before=replay.state()
        q=self.quote(replay,offset=2*o.HOUR,bid=".00001",sequence=1)
        with self.assertRaisesRegex(ValueError,"nonpositive executable exit"):replay.step(event("quote",q))
        self.assertEqual(before,replay.state())

    def test_new_h1_publication_cancels_old_signal_without_refreshing_it(self):
        replay,c=self.component();w=c.frame("H1")[30]
        replay.step(event("bars",[hour(w).record()]))
        self.assertIsNone(replay.pending);self.assertEqual("new_h1_decision",replay.cancellations[-1]["reason"])

    def test_duplicate_publication_after_clock_or_quote_never_cancels_pending(self):
        replay,_=self.component();last=deepcopy(replay.events[-1])
        replay.step(event("clock",replay.time+1));before=replay.state();length=len(replay.events)
        self.assertEqual("duplicate",replay.step(last));self.assertEqual(before,replay.state())
        self.assertEqual(length,len(replay.events));self.assertIsNotNone(replay.pending)
        h1=[row for row in last["value"] if row["timeframe"]=="H1"]
        self.assertEqual("duplicate",replay.step(event("bars",h1)))
        q=self.quote(replay,offset=1,open=False);replay.step(event("quote",q));before=replay.state()
        self.assertEqual("duplicate",replay.step(last));self.assertEqual(before,replay.state())
        self.assertIsNotNone(replay.pending)

    def test_conflicting_publication_after_clock_rejects_without_cancelling_pending(self):
        replay,_=self.component();last=deepcopy(replay.events[-1]);replay.step(event("clock",replay.time+1))
        last["value"][-1]["close"]=str(D(last["value"][-1]["close"])+D(".00001"));before=replay.state()
        with self.assertRaises(ValueError):replay.step(last)
        self.assertEqual(before,replay.state());self.assertIsNotNone(replay.pending)

    def test_minimum_lot_rejection_consumes_pending_instead_of_increasing_stakes(self):
        replay,_=self.component();replay.pending=replace(replay.pending,stop=D(".5"),invalidation=D(".51"))
        self.assertEqual("minimum_volume",replay.step(event("quote",self.quote(replay))))
        self.assertIsNone(replay.pending);self.assertIsNone(replay.ledger.position)
        self.assertIn("invented_component_EW3",replay.ledger.used)

    def test_held_protection_survives_missing_bars_and_quote_gaps_both_sides(self):
        for side in (1,-1):
            replay,_=self.component(side=side);entry=self.quote(replay);replay.step(event("quote",entry))
            position=dict(replay.ledger.position)
            when=entry.time+2*o.HOUR
            bid=entry.bid-side*D(".02")
            q=Quote(when,when,1,bid,bid+D(".0001"))
            self.assertEqual("held",replay.step(event("quote",q)))
            self.assertIsNone(replay.ledger.position);self.assertEqual("stop",replay.ledger.trades[0]["reason"])
            self.assertGreater(-D(replay.ledger.trades[0]["net"]),position["risk"])
            self.assertTrue(replay.ledger.paused)
            self.assertFalse(replay.decisions.coverage.ready(replay.decisions.strategy.bars,q.time))

    def test_calendar_closed_quote_never_fills_even_if_raw_flag_claims_open(self):
        replay,c=self.component(hours=47,closure=2)
        self.assertEqual("entered",replay.step(event("quote",self.quote(replay))))
        close=c.frame("D1")[1].end
        closed=Quote(close+1000,close+1000,1,"1.08","1.0801",True)
        self.assertEqual("unavailable_quote",replay.step(event("quote",closed)))
        self.assertIsNotNone(replay.ledger.position)
        self.assertFalse(replay.quote_gates[-1]["effective_open"])
        self.assertTrue(replay.quote_gates[-1]["declared_open"])
        before=replay.state()
        with self.assertRaises(ValueError):replay.step(event("finish",closed))
        self.assertEqual(before,replay.state())
        reopened=c.frame("D1")[2].start+1000
        q=Quote(reopened,reopened,2,"1.08","1.0801")
        self.assertEqual("held",replay.step(event("quote",q)))
        self.assertEqual("stop",replay.ledger.trades[0]["reason"])

    def test_receipt_after_session_close_is_unavailable_even_with_open_source(self):
        replay,c=self.component(hours=23,closure=True);close=c.frame("D1")[0].end
        q=Quote(close+1,close-1,0,"1.1","1.1001")
        self.assertEqual("unavailable_quote",replay.step(event("quote",q)))
        self.assertTrue(replay.quote_gates[-1]["calendar_source_open"])
        self.assertFalse(replay.quote_gates[-1]["calendar_receipt_open"])

    def test_source_during_closure_is_unavailable_when_received_after_reopen(self):
        replay,c=self.component(hours=23,closure=True);reopen=c.frame("D1")[1].start
        q=Quote(reopen+1,reopen-1,0,"1.1","1.1001")
        self.assertEqual("unavailable_quote",replay.step(event("quote",q)))
        self.assertFalse(replay.quote_gates[-1]["calendar_source_open"])
        self.assertTrue(replay.quote_gates[-1]["calendar_receipt_open"])

    def test_time_exit_uses_first_executable_quote_after_72_elapsed_hours(self):
        replay,_=self.component();entry=self.quote(replay);replay.step(event("quote",entry))
        when=entry.time+72*o.HOUR
        q=Quote(when,when,1,entry.bid,entry.ask)
        replay.step(event("quote",q));self.assertEqual("time",replay.ledger.trades[0]["reason"])
        self.assertIsNone(replay.ledger.position)

    def test_utc_rollover_financing_and_conservative_pause_are_preserved(self):
        replay,_=self.component();entry=self.quote(replay);replay.step(event("quote",entry));lots=replay.ledger.position["lots"]
        when=(entry.time//86400000+1)*86400000+1000
        q=Quote(when,when,1,entry.bid,entry.ask);replay.step(event("quote",q))
        self.assertEqual(3*lots,replay.ledger.position["financing"])
        self.assertTrue(replay.ledger.paused)
        self.assertEqual("financing",next(e for e in replay.ledger.events if e["kind"]=="financing")["kind"])

    def test_position_limit_prevents_same_quote_reentry_after_protective_exit(self):
        replay,_=self.component();replay.step(event("quote",self.quote(replay)))
        replay.pending=Setup("second_component",1,"EW5",replay.time,replay.time+60000,"1.1001","1.0990")
        q=self.quote(replay,bid="1.12",sequence=1)
        self.assertEqual("position_limit",replay.step(event("quote",q)))
        self.assertEqual(1,len(replay.ledger.trades));self.assertIsNone(replay.ledger.position)
        self.assertIn("second_component",replay.ledger.used)

    def test_loss_pause_blocks_recovery_position(self):
        replay,_=self.component();replay.step(event("quote",self.quote(replay)))
        replay.step(event("quote",self.quote(replay,bid="1.08",sequence=1)))
        replay.pending=Setup("recovery_blocked",1,"EW3",replay.time,replay.time+60000,"1.0801","1.0790")
        self.assertEqual("daily_pause",replay.step(event("quote",self.quote(replay,bid="1.0801",sequence=2))))
        self.assertIsNone(replay.ledger.position);self.assertIsNone(replay.pending)

    def test_boundary_requires_exact_latest_executable_quote_and_is_idempotent(self):
        replay,_=self.component();q=self.quote(replay);replay.step(event("quote",q))
        before=replay.state()
        with self.assertRaises(ValueError):replay.step(event("finish",replace(q,bid=q.bid-D(".00001"))))
        self.assertEqual(before,replay.state())
        self.assertEqual("finished",replay.step(event("finish",q)))
        self.assertEqual("boundary",replay.ledger.trades[-1]["reason"])
        self.assertEqual("duplicate_finish",replay.step(event("finish",q)))
        with self.assertRaises(ValueError):replay.step(event("quote",q))

    def test_flat_boundary_still_rejects_stale_repeated_or_closed_latest_quote(self):
        for bad in ("stale","repeated","closed"):
            replay,_=self.component();replay.pending=None;q=self.quote(replay);replay.step(event("quote",q))
            later=self.quote(replay,offset=4000,sequence=1,source=q.source if bad!="closed" else None,open=bad!="closed")
            if bad=="stale":later=replace(later,source=later.time-2001)
            replay.step(event("quote",later));before=replay.state()
            with self.subTest(bad=bad),self.assertRaises(ValueError):replay.step(event("finish",later))
            self.assertEqual(before,replay.state())


class PaperJournal148Tests(unittest.TestCase):
    def small(self):
        c=o.Calendar.from_record(schedule((24,)*3));replay=p.PaperReplay(c)
        w=c.frame("H1")[0];replay.step(event("bars",[hour(w).record()]))
        return replay,c

    def test_real_small_pipeline_checkpoint_and_clock_restart(self):
        replay,_=self.small();replay.step(event("clock",replay.time+10))
        self.assertEqual(replay.state(),p.PaperReplay.restore(replay.checkpoint()).state())

    def test_checkpoint_mutation_cannot_alter_running_state_or_bindings(self):
        replay,_=self.small();before=replay.checkpoint();changed=replay.checkpoint()
        changed["payload"]["bindings"].clear();changed["payload"]["events"].clear();changed["payload"]["state"].clear()
        self.assertEqual(before,replay.checkpoint())

    def test_changed_source_calendar_state_or_journal_rejects_restore(self):
        replay,_=self.small();saved=replay.checkpoint()
        for change in ("calendar","state","duplicate","kind","profile","source"):
            c=deepcopy(saved);payload=c["payload"]
            if change=="calendar":payload["calendar"]["finalization_delay_ms"]+=1
            if change=="state":payload["state"]["time"]+=1
            if change=="duplicate":payload["events"].append(payload["events"][-1])
            if change=="kind":payload["events"][0]["kind"]="order"
            if change=="profile":payload["profile"]="adverse"
            if change=="source":payload["bindings"]={}
            c["digest"]=digest(payload)
            with self.subTest(change=change),self.assertRaises(ValueError):p.PaperReplay.restore(c)

    def test_source_change_during_run_rejects_checkpoint(self):
        replay,_=self.small()
        with patch.object(p,"source_bindings",return_value={}):
            with self.assertRaises(ValueError):replay.checkpoint()

    def test_atomic_invalid_batch_cannot_cancel_existing_pending_or_mutate_cash(self):
        replay,c=self.small()
        replay.pending=Setup("declared_atomic_component",1,"EW3",replay.time,replay.time+60000,"1.1001","1.0990")
        before=replay.state();w=c.frame("H1")[1]
        with self.assertRaises(ValueError):replay.step(event("bars",[hour(w).record(),hour(w).record()]))
        self.assertEqual(before,replay.state())

    def test_boundaries_types_fields_and_no_order_event(self):
        replay,c=self.small();before=replay.state()
        for invalid in (event("clock",True),event("clock",c.end+60001),event("clock",replay.time-1),
                        event("bars",[]),event("order",{}),{"kind":"quote","value":{},"account":"blocked"}):
            with self.subTest(event=invalid),self.assertRaises(ValueError):replay.step(invalid)
            self.assertEqual(before,replay.state())

    def test_journal_limit_blocks_mutation_and_preserves_restorability(self):
        replay,_=self.small();saved=replay.checkpoint()
        with patch.object(p,"MAX_EVENTS",1):
            with self.assertRaises(ValueError):replay.step(event("clock",replay.time+1))
            self.assertEqual(saved,replay.checkpoint())
            self.assertEqual(replay.state(),p.PaperReplay.restore(saved).state())

    def test_market_and_native_submission_gates_remain_closed(self):
        from forex_demo_lab.elliott_full.admission import study_status,DemoBoundary
        self.assertTrue(all(row["status"]=="UNAVAILABLE" and row["returns"] is None for row in study_status()["cells"]))
        self.assertFalse(DemoBoundary().submission_status()["available"])


class PaperAutomatic148Tests(unittest.TestCase):
    """No declared counts, contexts or signals are supplied to these replays."""
    @classmethod
    def setUpClass(cls):
        spec=importlib.util.spec_from_file_location("paper_example148",ROOT/"scripts/elliott-session-paper-148.py")
        cls.example=importlib.util.module_from_spec(spec);spec.loader.exec_module(cls.example)
        cls.calendar,cls.bars,cls.quotes,cls.freeze=cls.example.fixture("target")
        cls.prefix={}
        for profile in ("base","adverse"):
            replay=p.PaperReplay(cls.calendar,profile);publish(replay,cls.bars)
            if replay.pending is None:raise AssertionError("automatic setup missing")
            cls.prefix[profile]=replay

    def test_automatic_entry_targets_and_gaps_independently_reconcile_both_costs(self):
        results=[]
        for profile in ("base","adverse"):
            prefix=self.prefix[profile]
            self.assertEqual((1,"EW3"),(prefix.pending.side,prefix.pending.kind))
            self.assertEqual({"D1":1,"H4":1},prefix.decisions.strategy.contexts)
            self.assertTrue(all(len(h)>=253 for h in prefix.decisions.strategy.bars.values()))
            self.assertTrue(prefix.decisions.coverage.ready(prefix.decisions.strategy.bars,prefix.time))
            for outcome in ("target","gap"):
                replay=prefix.fork();signal=p.setup_record(replay.pending);q0,q1=self.quotes
                if outcome=="gap":q1=replace(q1,bid=q1.bid-D(".04"),ask=q1.ask-D(".04"))
                self.assertEqual("entered",replay.step(event("quote",q0)))
                position=dict(replay.ledger.position)
                fee,slip,floor=(F(7),F(".00002"),F(0)) if profile=="base" else (F(10),F(".00005"),F(".00012"))
                entry=max(F(q0.ask),F(q0.bid)+floor)+slip
                unrounded=F(signal["stop"])/F(".00001")
                stop=F(unrounded.numerator//unrounded.denominator)*F(".00001")
                distance=entry-stop;per_lot=(distance+slip)*100000+fee
                raw=min(F(25)/per_lot,F(10000)/(entry*100000/30+fee/2),F(1))
                lots=F((raw*100).numerator//(raw*100).denominator,100)
                scaled=(entry+2*distance)/F(".00001");target=F(scaled.numerator//scaled.denominator)*F(".00001")
                self.assertEqual((entry,stop,target,lots),tuple(F(position[k]) for k in ("entry","stop","target","lots")))
                self.assertLessEqual(per_lot*lots,25)
                replay.step(event("quote",q1));replay.step(event("finish",q1))
                trade=replay.ledger.trades[0];fill=target if outcome=="target" else F(q1.bid)-slip
                gross=(fill-entry)*lots*100000;net=gross-fee*lots
                self.assertEqual((fill,gross,net,per_lot*lots),tuple(F(trade[k]) for k in ("exit","gross","net","estimated_risk")))
                self.assertEqual(F(10000)+net,F(replay.ledger.cash));self.assertTrue(replay.ledger.finished)
                self.assertEqual("target" if outcome=="target" else "stop",trade["reason"])
                if outcome=="gap":self.assertGreater(-net,per_lot*lots);self.assertTrue(replay.ledger.paused)
                results.append({"profile":profile,"case":"EW3_long_"+outcome,"trades":1,"fraction_reconciled":True,
                                "bar_counts":{f:len(h) for f,h in prefix.decisions.strategy.bars.items()},
                                "exit":trade["reason"],"market_cells_run":0,"orders_available":False})
        configured=os.environ.get("ELLIOTT_PAPER_EVIDENCE_DIR")
        if configured:
            with (Path(configured)/"automatic-accounts.json").open("x") as out:
                json.dump({"kind":"invented_session_paper_acceptance_148","freeze":self.freeze,"accounts":results},out,indent=2);out.write("\n")

    def test_adverse_pending_restart_matches_continuous_gap_exit(self):
        replay=self.prefix["adverse"].fork();checkpoint=replay.checkpoint();restored=p.PaperReplay.restore(checkpoint)
        q0,q1=self.quotes;q1=replace(q1,bid=q1.bid-D(".04"),ask=q1.ask-D(".04"))
        for current in (replay,restored):
            current.step(event("quote",q0));current.step(event("quote",q1));current.step(event("finish",q1))
        self.assertEqual(replay.state(),restored.state())
        self._record("pending-adverse",checkpoint,replay)

    def test_base_held_restart_matches_continuous_target_exit(self):
        replay=self.prefix["base"].fork();q0,q1=self.quotes;replay.step(event("quote",q0))
        checkpoint=replay.checkpoint();restored=p.PaperReplay.restore(checkpoint)
        for current in (replay,restored):current.step(event("quote",q1));current.step(event("finish",q1))
        self.assertEqual(replay.state(),restored.state());self._record("held-base",checkpoint,replay)

    def _record(self,name,checkpoint,replay):
        configured=os.environ.get("ELLIOTT_PAPER_EVIDENCE_DIR")
        if configured:
            import gzip
            with gzip.open(Path(configured)/(name+".json.gz"),"wt") as out:json.dump(checkpoint,out)
            with (Path(configured)/(name+"-result.json")).open("x") as out:
                json.dump({"case":name,"whole_state_restart_equal":True,"ledger":replay.ledger.state(),
                           "orders_available":False,"market_cells_run":0},out,indent=2);out.write("\n")

    def test_future_exit_price_does_not_change_pending_snapshot_history(self):
        before=self.prefix["base"].state();a=self.prefix["base"].fork();b=self.prefix["base"].fork();q0,q1=self.quotes
        a.step(event("quote",q0));b.step(event("quote",q0))
        a.step(event("quote",q1));b.step(event("quote",replace(q1,bid=q1.bid-D(".04"),ask=q1.ask-D(".04"))))
        self.assertEqual(before["decisions"]["snapshots"],a.state()["decisions"]["snapshots"])
        self.assertEqual(a.state()["decisions"]["snapshots"],b.state()["decisions"]["snapshots"])
        self.assertEqual(before,self.prefix["base"].state())

    def test_public_cli_automatic_gap_case_and_exclusive_output(self):
        configured=os.environ.get("ELLIOTT_PAPER_EVIDENCE_DIR")
        with tempfile.TemporaryDirectory() as temp:
            out=(Path(configured) if configured else Path(temp))/"public-cli"
            args=[sys.executable,str(ROOT/"scripts/elliott-session-paper-148.py"),str(out),"--outcome","gap"]
            done=subprocess.run(args,capture_output=True,text=True)
            self.assertEqual(0,done.returncode,done.stderr)
            report=json.loads((out/"report.json").read_text())
            self.assertEqual("stop",report["report"]["ledger"]["trades"][0]["reason"])
            self.assertTrue(report["report"]["ledger"]["paused"])
            self.assertTrue(report["report"]["ledger"]["finished"])
            self.assertFalse(report["orders_available"])
            self.assertIsNotNone(json.loads((out/"pending.json").read_text())["payload"]["state"]["pending"])
            self.assertIsNotNone(json.loads((out/"held.json").read_text())["payload"]["state"]["ledger"]["position"])
            self.assertNotEqual(0,subprocess.run(args,capture_output=True).returncode)
            self.assertNotEqual(0,subprocess.run(args+["--source","reserved"],capture_output=True).returncode)


if __name__=="__main__":unittest.main()
