"""Common invented inputs, unchanged controls, explicit unavailable cells."""
from copy import deepcopy
from decimal import localcontext
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from forex_demo_lab import elliott_session_comparison_149 as s
from forex_demo_lab.elliott_full.contracts import Bar,D,digest
from test_daily_fills_120 import audit_ledger
from test_elliott_execution_125 import audit_account

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("comparison149_examples",ROOT/"scripts/elliott-session-comparison-149.py")
examples=importlib.util.module_from_spec(spec);spec.loader.exec_module(examples)


def rehash(value):
    sha=s.observations.Calendar.from_record(value["calendar"]).sha256
    for row in value["hours"]:row["lineage"]=s.hour_lineage(value["case"],sha,row)
    return value


class Comparison149Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.home=tempfile.TemporaryDirectory();cls.root=Path(cls.home.name);cls.cache={}

    @classmethod
    def tearDownClass(cls):cls.home.cleanup()

    def frozen(self,value=None):
        root=Path(tempfile.mkdtemp(dir=self.root));input=root/"input.json";manifest=root/"freeze.json"
        s.write(input,examples.fixture(warmup_days=1) if value is None else value);s.freeze(input,manifest)
        return root,input,manifest

    def prepared(self,partition="development"):
        if partition not in self.cache:
            root,input,manifest=self.frozen(examples.fixture());s.prepare(input,manifest,partition,root/"prepared")
            self.cache[partition]=root/"prepared"
        return self.cache[partition]

    def test_calendar_converts_explicit_closures_without_inferred_days(self):
        value=examples.fixture(warmup_days=6);calendar=s.observations.Calendar.from_record(value["calendar"])
        converted=s.legacy_calendar(calendar);rows=converted["sessions"]
        self.assertEqual(4,sum(row["status"]=="closure" for row in rows))
        self.assertEqual(calendar.start,rows[0]["start_msc"]);self.assertEqual(calendar.end,rows[-1]["end_msc"])
        self.assertTrue(all(b["start_msc"]==a["end_msc"] for a,b in zip(rows,rows[1:])))

    def test_shifted_short_and_variable_days_are_unsupported_for_controls(self):
        value=examples.fixture("shifted",1)
        with self.assertRaisesRegex(ValueError,"UTC_midnight"):s.legacy_calendar(s.observations.Calendar.from_record(value["calendar"]))
        from test_elliott_sessions_146 import schedule
        for hours in ((23,25),(3.5,)):
            c=s.observations.Calendar.from_record(schedule(hours,partial=True))
            with self.assertRaises(ValueError):s.legacy_calendar(c)

    def test_other_finalization_profile_is_not_silently_changed(self):
        value=examples.fixture(warmup_days=1);value["calendar"]["finalization_delay_ms"]=1000
        with self.assertRaisesRegex(ValueError,"finalization_profile"):s.legacy_calendar(s.observations.Calendar.from_record(value["calendar"]))

    def test_invented_kind_and_private_or_policy_fields_reject(self):
        for field,value in (("kind","qualified_market"),("account","blocked"),("password","blocked"),("orders_available",True)):
            spec=examples.fixture(warmup_days=1);spec[field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):s.validate(spec)

    def test_partitions_are_chronological_disjoint_and_fixed(self):
        for change in ("order","overlap","bounds","name","boolean"):
            value=examples.fixture(warmup_days=1)
            if change=="order":value["partitions"].reverse()
            if change=="overlap":value["partitions"][1]["start_msc"]=value["partitions"][0]["start_msc"]
            if change=="bounds":value["partitions"][0]["end_msc"]=value["partitions"][0]["start_msc"]
            if change=="name":value["partitions"][0]["name"]="holdout_claim"
            if change=="boolean":value["partitions"][0]["start_msc"]=True
            with self.subTest(change=change),self.assertRaises(ValueError):s.validate(value)

    def test_quote_source_and_receipt_cannot_cross_partition(self):
        value=examples.fixture(warmup_days=1);value["quotes"][0]["source"]=value["partitions"][0]["start_msc"]-1
        with self.assertRaisesRegex(ValueError,"outside_partition"):s.validate(value)

    def test_quote_order_conflicting_sources_and_cap_reject(self):
        for change in ("sequence","receipt","source","price"):
            value=examples.fixture(warmup_days=1)
            if change=="sequence":value["quotes"][0]["sequence"]=True
            if change=="receipt":value["quotes"][1]["time"]=value["quotes"][0]["time"]-1;value["quotes"][1]["source"]=value["quotes"][0]["source"]-1
            if change=="source":value["quotes"][1]["source"]=value["quotes"][0]["source"]-1
            if change=="price":value["quotes"][1]["source"]=value["quotes"][0]["source"]
            with self.subTest(change=change),self.assertRaises(ValueError):s.validate(value)
        value=examples.fixture(warmup_days=1);q=value["quotes"][0]
        value["quotes"]=[{**q,"sequence":i,"source":q["source"]+i,"time":q["time"]+i} for i in range(257)]+value["quotes"][2:]
        for i,q in enumerate(value["quotes"]):q["sequence"]=i
        with self.assertRaisesRegex(ValueError,"quote_bound"):s.validate(value)

    def test_hours_require_exact_bounds_lineage_and_receipt_order(self):
        for change in ("lineage","end","observation","duplicate","order","frame"):
            value=examples.fixture(warmup_days=1)
            if change=="lineage":value["hours"][0]["lineage"]="a"*64
            if change=="end":value["hours"][0]["end"]-=1;rehash(value)
            if change=="observation":value["hours"][0]["observation"]=value["hours"][0]["end"];rehash(value)
            if change=="duplicate":value["hours"].insert(1,deepcopy(value["hours"][0]))
            if change=="order":value["hours"][0],value["hours"][1]=value["hours"][1],value["hours"][0]
            if change=="frame":value["hours"][0]["timeframe"]="H4";rehash(value)
            with self.subTest(change=change),self.assertRaises(ValueError):s.validate(value)

    def test_quote_hour_contradiction_is_not_repaired(self):
        value=examples.fixture(warmup_days=1);q=value["quotes"][0]
        row=next(row for row in value["hours"] if row["start"]<=q["source"]<row["end"])
        row["high"]=row["close"];rehash(value)
        with self.assertRaisesRegex(ValueError,"quote_hour_observation_conflict"):s.validate(value)

    def test_decimal_profile_is_bounded_and_independent_of_global_precision(self):
        value=examples.fixture(warmup_days=1)
        with localcontext() as context:context.prec=6;s.validate(value)
        for amount in (1.1,"NaN","1e1000000",".0000000000000000000001","9"*65):
            changed=deepcopy(value);changed["hours"][0]["high"]=amount
            with self.subTest(amount=amount),self.assertRaises(ValueError):s.validate(changed)

    def test_float_roundtrip_limits_only_legacy_bridge(self):
        value=examples.fixture(warmup_days=1);value["hours"][0]["open"]="1.10000000000000001";rehash(value);s.validate(value)
        with self.assertRaisesRegex(ValueError,"legacy_float_roundtrip"):s.legacy_input(value,value["partitions"][0])

    def test_future_legacy_precision_failure_does_not_block_development_bridge(self):
        value=examples.fixture();cut=value["partitions"][1]["start_msc"]
        row=next(row for row in value["hours"] if row["start"]>cut)
        row["open"]=str(D(row["open"])+D(".00000000000000001"));rehash(value);s.validate(value)
        s.legacy_input(value,value["partitions"][0])
        with self.assertRaisesRegex(ValueError,"legacy_float_roundtrip"):s.legacy_input(value,value["partitions"][1])

    def test_explicit_session_disagreement_is_unrepresentable_for_controls(self):
        value=examples.fixture(warmup_days=1);value["quotes"][0]["session_open"]=False;s.validate(value)
        with self.assertRaisesRegex(ValueError,"session_flag_unrepresentable"):s.legacy_input(value,value["partitions"][0])

    def test_source_receipt_session_crossing_cannot_be_hidden_in_control_conversion(self):
        value=examples.fixture(warmup_days=4);part=value["partitions"][0];close=part["end_msc"]
        value["quotes"][1]["time"]=close+1;part["end_msc"]=close+2000;s.validate(value)
        with self.assertRaisesRegex(ValueError,"source_receipt_session_mismatch"):s.legacy_input(value,part)

    def test_freeze_metadata_tampering_and_boolean_zero_reject(self):
        for field,altered in (("orders_available",0),("market_data_qualified",True),("kind","market_approved")):
            root,input,manifest=self.frozen();f=json.loads(manifest.read_text());f[field]=altered;manifest.write_text(json.dumps(f))
            with self.subTest(field=field),self.assertRaises(ValueError):s.prepare(input,manifest,"development",root/"out")
            self.assertFalse((root/"out").exists())

    def test_changed_input_or_source_rejects_before_output(self):
        root,input,manifest=self.frozen();value=json.loads(input.read_text());value["case"]="another_case";rehash(value);input.write_text(json.dumps(value))
        with self.assertRaisesRegex(ValueError,"freeze_binding"):s.prepare(input,manifest,"development",root/"out")
        root,input,manifest=self.frozen()
        with patch.object(s,"source_bindings",return_value={}):
            with self.assertRaises(ValueError):s.prepare(input,manifest,"development",root/"out")
        self.assertFalse((root/"out").exists())

    def test_duplicate_json_nonfinite_and_symlink_inputs_reject(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);input=root/"input.json"
            for raw in ('{"kind":1,"kind":2}','{"kind":NaN}'):
                input.write_text(raw)
                with self.assertRaises(ValueError):s.freeze(input,root/"freeze.json")
            link=root/"link.json";link.symlink_to(input)
            with self.assertRaises(ValueError):s.read(link)

    def test_missing_hours_empty_quotes_and_short_warmup_keep_all_cells_null(self):
        for change in ("hour","quotes","warmup"):
            value=examples.fixture(warmup_days=253 if change!="warmup" else 1)
            if change=="hour":del value["hours"][10]
            if change=="quotes":value["quotes"]=[]
            root,input,manifest=self.frozen(value);result=s.evaluate(input,manifest,root/"run")
            self.assertEqual(16,len(result["cells"]));self.assertEqual(0,result["computed_invented_cells"])
            self.assertTrue(all(cell["summary"] is None and cell["market_returns"] is None for cell in result["cells"]))

    def test_exact_endpoint_stale_repeated_and_late_tail_reject(self):
        for change in ("missing","stale","repeat","tail"):
            value=examples.fixture(warmup_days=253);part=value["partitions"][0]
            if change=="missing":part["endpoint_source_msc"]-=1
            if change=="stale":value["quotes"][1]["time"]+=1000;value["quotes"][1]["source"]-=2000;part["endpoint_source_msc"]-=2000
            if change=="repeat":value["quotes"][1]["source"]=value["quotes"][0]["source"];value["quotes"][1]["bid"]=value["quotes"][0]["bid"];value["quotes"][1]["ask"]=value["quotes"][0]["ask"];part["endpoint_source_msc"]=value["quotes"][0]["source"]
            if change=="tail":
                row=next(row for row in value["hours"] if row["end"]==part["end_msc"]-s.observations.HOUR)
                row["available"]=part["end_msc"]-500;value["hours"].sort(key=lambda row:(row["available"],row["start"]));rehash(value)
            if change=="stale":
                # Keep the receipt inside the declared interval while exceeding freshness.
                value["quotes"][1]["time"]=part["end_msc"]-1
            s.validate(value)
            with self.subTest(change=change),self.assertRaisesRegex(ValueError,"endpoint"):s.scope(value,"development")

    def test_same_clock_publication_ambiguity_is_common_unavailability(self):
        value=examples.fixture();value["hours"][0]["available"]=value["hours"][1]["available"]
        value["hours"].sort(key=lambda row:(row["available"],row["start"]));rehash(value);s.validate(value)
        with self.assertRaisesRegex(ValueError,"ambiguous_same_clock"):s.scope(value,"development")

    def test_old_source_backfill_is_not_sorted_into_history(self):
        value=examples.fixture();value["hours"][0]["available"]=value["hours"][2]["available"]+1
        value["hours"].sort(key=lambda row:(row["available"],row["start"]));rehash(value);s.validate(value)
        with self.assertRaisesRegex(ValueError,"source_order_backfill"):s.scope(value,"development")

    def test_bridge_daily_values_publication_and_quotes_match_exactly(self):
        root=self.prepared();prepared=json.loads((root/"prepared149.json").read_text())
        self.assertEqual({"D1":253,"H4":1518,"H1":6072},prepared["warmup"]);self.assertIsNone(prepared["controls_reason"])
        new=json.loads((root/"derived-bars.json").read_text())["bars"]
        old=json.loads((root/"legacy/derived-bars.json").read_text())["bars"]
        self.assertEqual([s.semantic_bar(Bar(**row)) for row in new],[s.semantic_bar(Bar(**row)) for row in old])
        prefix=json.loads((root/"prefix.json").read_text());expected=[(q["source"],q["time"],D(q["bid"]),D(q["ask"])) for q in prefix["quotes"]]
        for name in ("fills-input.json","compiled-input.json"):
            v=json.loads((root/"legacy"/name).read_text())
            self.assertEqual(expected,[(q["source_msc"],q["receipt_msc"],D(str(q["bid"])),D(str(q["ask"]))) for q in v["events"]])

    def test_future_prices_cannot_change_development_inputs(self):
        value=examples.fixture();cut=value["partitions"][1]["start_msc"]//s.observations.HOUR*s.observations.HOUR
        for row in value["hours"]:
            if row["start"]>=cut:
                for key in ("open","high","low","close"):row[key]=str(D(row[key])+D(".0002"))
        for q in value["quotes"]:
            if q["source"]>=cut:q["bid"]=str(D(q["bid"])+D(".0002"));q["ask"]=str(D(q["ask"])+D(".0002"))
        rehash(value);root,input,manifest=self.frozen(value);s.prepare(input,manifest,"development",root/"prepared")
        for name in ("paper-events.json","derived-bars.json","legacy/daily-input.json","legacy/fills-input.json"):
            self.assertEqual(json.loads((self.prepared()/name).read_text()),json.loads((root/"prepared"/name).read_text()))

    def test_unknown_candidate_profile_unfinished_report_and_conflicting_event_reject(self):
        for candidate,profile in (("MIX50_D","base"),("CASH","live")):
            with self.assertRaises(ValueError):s.ComparisonReplay(self.root,candidate,profile)
        replay=s.ComparisonReplay(self.prepared(),"CASH")
        with self.assertRaises(ValueError):replay.report()
        replay.step();before=replay.checkpoint();bad=deepcopy(replay.events[0]);bad["bid"]+=.00001
        with self.assertRaises(ValueError):replay.step(bad)
        self.assertEqual(before,replay.checkpoint())

    def test_control_held_and_finished_checkpoints_restore(self):
        root=self.prepared()
        for candidate in ("T12_D","CASH","EWPB_D124"):
            replay=s.ComparisonReplay(root,candidate);replay.step()
            if candidate=="T12_D":self.assertIsNotNone(replay.engine.engine.state["held"])
            checkpoint=replay.checkpoint();restored=s.ComparisonReplay.restore(root,checkpoint)
            self.assertEqual(checkpoint,restored.checkpoint());self.assertEqual(replay.run(),restored.run())
            final=replay.checkpoint();self.assertEqual(final,s.ComparisonReplay.restore(root,final).checkpoint())

    def test_paper_checkpoint_prefix_and_final_identity_are_bound(self):
        root=self.prepared();replay=s.ComparisonReplay(root,"EW_FULL_V1")
        for _ in range(12):replay.step()
        checkpoint=replay.checkpoint();self.assertEqual(checkpoint,s.ComparisonReplay.restore(root,checkpoint).checkpoint())
        changed=deepcopy(checkpoint);changed["payload"]["inner"]["payload"]["events"][0]["value"][0]["lineage"]="f"*64
        inner=changed["payload"]["inner"];inner["digest"]=digest(inner["payload"]);changed["digest"]=digest(changed["payload"])
        with self.assertRaisesRegex(ValueError,"checkpoint_prefix"):s.ComparisonReplay.restore(root,changed)

    def test_rehashed_outer_profile_or_candidate_cannot_relabel_inner_account(self):
        root=self.prepared()
        for candidate in ("CASH","EW_FULL_V1"):
            checkpoint=s.ComparisonReplay(root,candidate).checkpoint()
            changed=deepcopy(checkpoint);changed["payload"]["profile"]="adverse";changed["digest"]=digest(changed["payload"])
            with self.assertRaisesRegex(ValueError,"checkpoint_identity"):s.ComparisonReplay.restore(root,changed)
        checkpoint=s.ComparisonReplay(root,"T12_D").checkpoint();checkpoint["payload"]["candidate"]="CASH";checkpoint["digest"]=digest(checkpoint["payload"])
        with self.assertRaisesRegex(ValueError,"checkpoint_identity"):s.ComparisonReplay.restore(root,checkpoint)

    def test_self_consistent_foreign_calendar_checkpoint_cannot_replace_prepared_calendar(self):
        root=self.prepared();replay=s.ComparisonReplay(root,"EW_FULL_V1")
        for _ in range(12):replay.step()
        checkpoint=replay.checkpoint();calendar=replay.engine.decisions.coverage.calendar.record()
        closure=next(row for row in calendar["segments"] if row["kind"]=="closure");closure["reason"]="holiday"
        foreign=s.paper.PaperReplay(s.observations.Calendar.from_record(calendar))
        for event in replay.events[:replay.cursor]:foreign.step(event)
        checkpoint["payload"]["inner"]=foreign.checkpoint();checkpoint["digest"]=digest(checkpoint["payload"])
        with self.assertRaisesRegex(ValueError,"checkpoint_calendar"):s.ComparisonReplay.restore(root,checkpoint)

    def test_cross_partition_cursor_and_finish_forgery_reject(self):
        root=self.prepared();checkpoint=s.ComparisonReplay(root,"CASH").checkpoint()
        with self.assertRaisesRegex(ValueError,"checkpoint_partition"):s.ComparisonReplay.restore(self.prepared("later_validation"),checkpoint)
        for field,val in (("cursor",True),("cursor",100000),("finished",True)):
            changed=deepcopy(checkpoint);changed["payload"][field]=val;changed["digest"]=digest(changed["payload"])
            with self.subTest(field=field),self.assertRaises(ValueError):s.ComparisonReplay.restore(root,changed)

    def test_changed_prepared_source_or_extra_file_cannot_be_checkpointed(self):
        root=self.prepared();replay=s.ComparisonReplay(root,"CASH")
        with patch.object(s,"source_bindings",return_value={}):
            with self.assertRaises(ValueError):replay.checkpoint()
        stray=root/"unowned.txt";stray.write_text("unowned")
        try:
            with self.assertRaises(ValueError):replay.checkpoint()
        finally:stray.unlink()

    def test_prepared_hash_path_tampering_rejects_without_following_paths(self):
        root,input,manifest=self.frozen(examples.fixture());s.prepare(input,manifest,"development",root/"prepared")
        prepared=root/"prepared/prepared149.json";record=json.loads(prepared.read_text());record["files"]["../../foreign.txt"]="a"*64;prepared.write_text(json.dumps(record))
        with self.assertRaises(ValueError):s.ComparisonReplay(root/"prepared","CASH")

    def test_source_change_before_final_status_aborts_publication(self):
        root,input,manifest=self.frozen();original=s.source_bindings();changed=[False]
        def unavailable(*args):changed[0]=True;raise ValueError("deliberate_preparation_failure")
        with patch.object(s,"source_bindings",side_effect=lambda:{} if changed[0] else original),patch.object(s,"prepare",side_effect=unavailable):
            with self.assertRaises(ValueError):s.evaluate(input,manifest,root/"run")
        self.assertFalse((root/"run/comparison-status.json").exists())

    def test_artifact_corruption_before_final_status_aborts_publication(self):
        root,input,manifest=self.frozen(examples.fixture());changed=[False]
        def fake_run(replay):
            if not changed[0]:
                with (replay.root/"prefix.json").open("a") as out:out.write("\n")
                changed[0]=True
            return {"summary":{}}
        with patch.object(s.ComparisonReplay,"run",fake_run):
            with self.assertRaisesRegex(ValueError,"artifacts_changed_during_run"):s.evaluate(input,manifest,root/"run")
        self.assertFalse((root/"run/comparison-status.json").exists())

    def test_output_report_corruption_before_status_aborts_publication(self):
        root,input,manifest=self.frozen(examples.fixture());first=[None]
        def fake_run(replay):
            if first[0] is None:first[0]=replay.root/"EW_FULL_V1-base.json"
            elif first[0].exists():
                with first[0].open("a") as out:out.write("\n")
            return {"summary":{}}
        with patch.object(s.ComparisonReplay,"run",fake_run):
            with self.assertRaisesRegex(ValueError,"reports_changed_during_run"):s.evaluate(input,manifest,root/"run")
        self.assertFalse((root/"run/comparison-status.json").exists())

    def test_public_utc_matrix_keeps_all16_and_reconciles_original_controls(self):
        configured=os.environ.get("ELLIOTT_COMPARISON_EVIDENCE_DIR")
        root=Path(configured)/"utc-trend" if configured else self.root/"utc-trend";root.mkdir(exist_ok=False)
        input,manifest,run=root/"input.json",root/"freeze.json",root/"run"
        script=str(ROOT/"scripts/elliott-session-comparison-149.py")
        for args in (("fixture",str(input)),("freeze",str(input),str(manifest)),("replay",str(input),str(manifest),str(run))):
            done=subprocess.run([sys.executable,script,*args],capture_output=True,text=True)
            self.assertEqual(0,done.returncode,done.stderr)
        status=json.loads((run/"comparison-status.json").read_text());self.assertEqual(16,status["computed_invented_cells"])
        self.assertEqual(16,len(status["cells"]));self.assertTrue(all(row["market_status"]=="UNAVAILABLE" and row["market_returns"] is None for row in status["cells"]))
        for part in s.PARTITIONS:
            for profile in s.PROFILES:
                for candidate in s.CANDIDATES:
                    report=json.loads((run/part/(candidate+"-"+profile+".json")).read_text())
                    self.assertEqual("10000",report["summary"]["initial_cash_usd"])
                    if candidate=="EW_FULL_V1":self.assertEqual(0,report["summary"]["closed_positions"])
                    else:
                        replay=s.ComparisonReplay(run/part,candidate,profile)
                        original=report["original_report"]["original_report"]
                        (audit_account if candidate=="EWPB_D124" else audit_ledger)(replay.engine.engine._fixture,original)
                        self.assertEqual(report["summary"],replay.engine.run()["summary"])

    def test_shifted_calendar_computes_ew_only_and_never_zeroes_unavailable_controls(self):
        configured=os.environ.get("ELLIOTT_COMPARISON_EVIDENCE_DIR")
        root=Path(configured)/"shifted" if configured else self.root/"shifted";root.mkdir(exist_ok=False)
        input,manifest=root/"input.json",root/"freeze.json";s.write(input,examples.fixture("shifted"));s.freeze(input,manifest)
        report=s.evaluate(input,manifest,root/"run")
        self.assertEqual(4,report["computed_invented_cells"])
        for cell in report["cells"]:
            if cell["candidate"]=="EW_FULL_V1":self.assertEqual("computed",cell["invented_status"])
            else:
                self.assertIsNone(cell["summary"]);self.assertEqual("unavailable",cell["invented_status"])
                self.assertEqual("legacy_requires_UTC_midnight_days",cell["reason"])

    def test_automatic_wave_entry_survives_common_adapter_with_closures(self):
        configured=os.environ.get("ELLIOTT_COMPARISON_EVIDENCE_DIR")
        root=Path(configured)/"wave" if configured else self.root/"wave";root.mkdir(exist_ok=False)
        input,manifest=root/"input.json",root/"freeze.json";s.write(input,examples.fixture("wave"));s.freeze(input,manifest)
        s.prepare(input,manifest,"development",root/"prepared")
        replay=s.ComparisonReplay(root/"prepared","EW_FULL_V1");report=replay.run()
        self.assertEqual(1,report["summary"]["closed_positions"])
        trade=replay.engine.ledger.trades[0];self.assertEqual("stop",trade["reason"])
        self.assertGreater(-D(trade["net"]),D(trade["estimated_risk"]))
        self.assertTrue(replay.engine.ledger.paused);s.write(root/"report.json",report)

    def test_market_and_demo_submission_admission_stay_closed(self):
        from forex_demo_lab.elliott_full.admission import study_status,DemoBoundary
        self.assertTrue(all(c["status"]=="UNAVAILABLE" and c["returns"] is None for c in study_status()["cells"]))
        self.assertFalse(DemoBoundary().submission_status()["available"])


if __name__=="__main__":unittest.main()
