"""Invented selection and lifecycle commands; not automatic setup/replay evidence."""
from copy import deepcopy
from dataclasses import FrozenInstanceError, replace
from decimal import Decimal
from fractions import Fraction as F
import json
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from forex_demo_lab.trendline import data as d, geometry as g, lines as l, selection as s, lifecycle as j
from test_trendline_data_163 import files
from test_trendline_geometry_167 import hourly_fixture
from test_trendline_pivots_166 import bars_for, golden, source_for

ROOT = Path(__file__).resolve().parents[1]


def declared_line(indices=(0,6,12),b_index=None,profile="TRL_BRK3_E1",frame="H4",kind="resistance",age=40,distance=0):
    ids = tuple(d.digest(["declared_line_touch",frame,kind,i]) for i in indices)
    b_index = indices[-1] if b_index is None else b_index
    ray = g.Ray(kind,indices[0],110 if kind == "resistance" else 90,b_index,
                F(110)-F(b_index-indices[0],5) if kind == "resistance" else F(90)+F(b_index-indices[0],5),frame)
    a_id,b_id = ids[0],ids[indices.index(b_index)]
    geometry_id = d.digest(["EURUSD",frame,kind,a_id,b_id])
    return s.ValidatedLine(geometry_id,a_id,b_id,profile,ray,ids,tuple(indices),F(distance),age)


def declared_snapshot(source,values=(),index=40,profile="TRL_BRK3_E1",role="full",prices=("100","101","99","100")):
    """Declared metadata/cursor fixture, not discovery from a complete candle path."""
    frame = "D1" if profile == "D1_BRK3" else "H4"
    _,bars = bars_for([list(prices)],frame,source,offset=index)
    values = tuple(replace(v,age=index-v.touch_indices[0]) for v in values)
    record = {"schema":s.VERSION,"kind":"invented_trendline_selection","data_level":"B",
              "declaration_sha256":source.sha256,"source_bindings":s.bindings(),"timeframe":frame,"profile":profile,
              "coverage_state":"CURRENT","search_incomplete":False,"entry_ready":False,"orders_available":False,
              "penetration_role":role,"latest_bar":bars[0].record(),"bar_index":index,
              "publication_ordinal":index+1,"as_of":bars[0].available,
              "selection":{"ranked":[v.record() for v in values]}}
    return s.SelectedSnapshot(d.canonical(record).decode(),values)


def discovered(length=48,role="full",side="LONG",profile="TRL_BRK3_E1"):
    source,bars = bars_for(golden(35,side)["inputs"]["ohlc"])
    return source,s.select(source,bars[:length],role=role,profile=profile),bars


class Selection169Tests(unittest.TestCase):
    def test_g35_prefers_existing_earliest_latest_pair_on_both_sides(self):
        for side in ("LONG","SHORT"):
            _,snapshot,_ = discovered(side=side)
            self.assertEqual(1,len(snapshot.selected))
            value = snapshot.selected[0]
            self.assertEqual((17,29),(value.ray.a_index,value.ray.b_index))
            self.assertEqual((17,23,29),value.touch_indices)
            report = snapshot.record()
            self.assertEqual(2,len(report["profile_valid_ids"]))
            self.assertEqual("DUPLICATE_TOUCH_SET",report["selection"]["discarded"][0]["reason"])

    def test_g30_does_not_invent_invalid_earliest_latest_geometry(self):
        value = declared_line(b_index=6)
        reduction = s.reduce_lines((value,))
        self.assertEqual((value,),reduction.kept)
        self.assertEqual(6,reduction.kept[0].ray.b_index)

    def test_earliest_latest_preference_precedes_distance_and_id(self):
        preferred = declared_line(distance="0.4")
        alternate = declared_line(b_index=6,distance=0)
        self.assertEqual((preferred,),s.reduce_lines((alternate,preferred)).kept)

    def test_fallback_uses_exact_distance_then_canonical_id(self):
        first = declared_line(indices=(0,6,12,18),b_index=6,distance=F(1,10))
        other = declared_line(indices=(0,6,12,18),b_index=12,distance=F(1,10)+F(1,10**30))
        self.assertEqual((first,),s.reduce_lines((other,first)).kept)
        tied = replace(other,summed_distance=first.summed_distance)
        self.assertEqual(min(first.geometry_id,tied.geometry_id),s.reduce_lines((first,tied)).kept[0].geometry_id)

    def test_strict_subsets_removed_only_inside_same_profile(self):
        subset = declared_line()
        superset = declared_line(indices=(0,6,12,18))
        brk2 = declared_line(indices=(0,6),profile="TRL_BRK2_E1")
        result = s.reduce_lines((subset,superset,brk2))
        self.assertEqual({superset.geometry_id,brk2.geometry_id},{v.geometry_id for v in result.kept})
        self.assertEqual(((subset.profile,"H4",subset.geometry_id,"STRICT_TOUCH_SUBSET",(superset.geometry_id,)),),result.discarded)

    def test_deduplication_is_permutation_independent_and_duplicate_idempotent(self):
        values = [declared_line(indices=(0,6,12,18),b_index=b) for b in (6,12,18)]+[declared_line(indices=(6,12,18),age=34)]
        expected = s.reduce_lines(values)
        rng = random.Random(169)
        for _ in range(30):
            rng.shuffle(values)
            self.assertEqual(expected,s.reduce_lines(values+[values[0]]))

    def test_conflicting_same_geometry_and_invalid_typed_metadata_refused(self):
        value = declared_line()
        with self.assertRaises(ValueError):s.reduce_lines((value,replace(value,age=41)))
        with self.assertRaises(ValueError):s.reduce_lines([{}])
        for kwargs in ({"age":29},{"touch_ids":(value.touch_ids[0],)*3},{"summed_distance":-1},
                       {"geometry_id":"0"*64},{"touch_indices":(0,5,12)}):
            with self.assertRaises(ValueError):replace(value,**kwargs)

    def test_frozen_profiles_cannot_be_smuggled_as_valid_metadata(self):
        with self.assertRaises(ValueError):declared_line(indices=(0,6))
        with self.assertRaises(ValueError):declared_line(profile="TRL_BRK2_E1")
        with self.assertRaises(ValueError):declared_line(profile="TRL_FXR_M")

    def test_rank_tuple_is_total_and_transitive(self):
        values = [declared_line(indices=(i,i+6,i+12),age=60-i) for i in range(12)]
        keys = [v.display_key for v in values]
        ordered = sorted(keys)
        self.assertEqual(len(keys),len(set(keys)))
        for a,b,c in zip(ordered,ordered[1:],ordered[2:]):self.assertTrue(a < b < c and a < c)
        self.assertEqual(tuple(sorted(values,key=lambda v:v.display_key)),s.reduce_lines(values).kept)

    def test_rank_dimensions_and_economic_key_excludes_canonical_id(self):
        three = declared_line()
        four = declared_line(indices=(0,6,12,18),age=31)
        older = replace(three,age=41)
        recent = declared_line(indices=(0,6,18))
        self.assertLess(four.economic_key,three.economic_key)
        self.assertLess(older.economic_key,three.economic_key)
        self.assertLess(recent.economic_key,three.economic_key)
        # Same first/last touch and count, different interior touch/geometry.
        left = declared_line(indices=(0,6,18),b_index=6)
        right = declared_line(indices=(0,12,18),b_index=12)
        self.assertEqual(left.economic_key,right.economic_key)
        self.assertNotEqual(left.display_key,right.display_key)
        report = s.reduce_lines((left,right)).record()
        self.assertEqual(1,len(report["economic_ties"]))
        self.assertFalse(report["trade_selection_available"])

    def test_normalized_record_roundtrip_is_immutable_and_exact(self):
        value = declared_line(distance=F(1,3))
        self.assertEqual(value,s.ValidatedLine.from_record(value.record()))
        record = value.record();record["touch_ids"].clear()
        self.assertEqual(3,len(value.touch_ids))
        with self.assertRaises(FrozenInstanceError):value.age = 1
        with self.assertRaises(ValueError):s.fraction({"numerator":True,"denominator":1})

    def test_mixed_frontiers_cannot_be_ranked_as_one_snapshot(self):
        with self.assertRaises(ValueError):s.reduce_lines((declared_line(),declared_line(indices=(6,12,18),age=40)))

    def test_duplicate_geometry_ids_in_different_profiles_keep_scope_in_diagnostics(self):
        brk3 = declared_line(b_index=6)
        brk2 = declared_line(indices=(0,6),profile="TRL_BRK2_E1")
        superset = declared_line(indices=(0,6,12,18),b_index=18)
        self.assertEqual(brk3.geometry_id,brk2.geometry_id)
        report = s.reduce_lines((brk3,brk2,superset)).record()
        self.assertEqual("TRL_BRK3_E1",report["discarded"][0]["profile"])
        self.assertTrue(any(v["profile"] == "TRL_BRK2_E1" for v in report["ranked"]))

    def test_selection_snapshot_is_repeatable_defensive_and_has_no_entry(self):
        source,snapshot,bars = discovered()
        self.assertEqual(snapshot,s.select(source,bars[:48]))
        before = snapshot.record();changed = snapshot.record();changed["selection"]["ranked"].clear()
        self.assertEqual(before,snapshot.record())
        for field in ("entry_ready","orders_available","trade_selection_available","lifecycle_integrated"):
            self.assertFalse(before[field])
        self.assertEqual(48,before["publication_ordinal"])
        self.assertEqual(snapshot,s.select(source,bars[:48]+[bars[47]]))

    def test_invalid_candidate_cannot_enter_reduction_or_restore_geometry(self):
        _,snapshot,_ = discovered(length=49)
        self.assertEqual((),snapshot.selected)
        raw = snapshot.record()["candidates"][1]
        self.assertFalse(raw["profile_valid"])
        with self.assertRaises(ValueError):s.ValidatedLine.from_candidate(raw,"TRL_BRK3_E1","H4")

    def test_future_suffix_never_mutates_a_selected_prefix(self):
        source,snapshot,bars = discovered()
        before = snapshot.record()
        s.select(source,bars,role="action_break")
        self.assertEqual(before,snapshot.record())
        self.assertEqual(before,s.select(source,bars[:48]).record())

    def test_source_binding_change_rejects_snapshot_before_publication(self):
        source,_,bars = discovered()
        bound = s.bindings()
        with patch.object(s,"bindings",side_effect=[bound,{}]):
            with self.assertRaises(ValueError):s.select(source,bars[:48])

    def test_cli_selection_and_single_snapshot_journal_export(self):
        with tempfile.TemporaryDirectory() as directory:
            value,rows = hourly_fixture();meta,hours,_ = files(directory,value,rows[:192])
            output = Path(directory)/"out"
            command = [sys.executable,str(ROOT/"scripts/trendline-lines-169.py"),str(meta),str(hours),str(output),"--journal"]
            run = subprocess.run(command,capture_output=True,text=True)
            self.assertEqual(0,run.returncode,run.stderr)
            report = json.loads((output/"selection.json").read_text())
            journal = json.loads((output/"journal.json").read_text())
            self.assertEqual(1,len(report["selection"]["ranked"]))
            self.assertEqual(["REGISTER","VALID"],[e["command"]["op"] for e in journal["events"]])
            before = (output/"selection.json").read_bytes()
            self.assertNotEqual(0,subprocess.run(command,capture_output=True).returncode)
            self.assertEqual(before,(output/"selection.json").read_bytes())

    def test_cli_action_exception_cannot_seed_journal_or_bypass_market_loader(self):
        with tempfile.TemporaryDirectory() as directory:
            value,rows = hourly_fixture();meta,hours,value = files(directory,value,rows)
            for index,extra in enumerate((("--role","action_break","--journal"),())):
                if index:value["kind"] = "market_trendline_source";meta.write_text(json.dumps(value))
                output = Path(directory)/str(index)
                run = subprocess.run([sys.executable,str(ROOT/"scripts/trendline-lines-169.py"),str(meta),str(hours),str(output),*extra],capture_output=True)
                self.assertNotEqual(0,run.returncode);self.assertFalse(output.exists())


class Lifecycle169Tests(unittest.TestCase):
    def setUp(self):
        self.source = source_for(100)
        self.line = declared_line()
        self.snapshot = declared_snapshot(self.source,(self.line,))
        self.book = j.Journal(self.source)

    def seed(self):
        line_id = self.book.register(self.snapshot,self.line.geometry_id)
        self.book.validate(self.snapshot,line_id)
        return line_id

    def later(self,index=41,values=(),**kwargs):return declared_snapshot(self.source,values,index=index,**kwargs)

    def test_discovered_g35_register_validate_then_poke_without_restoration(self):
        source,ready,bars = discovered()
        book = j.Journal(source)
        line_id = book.register(ready,ready.selected[0].geometry_id)
        book.validate(ready,line_id)
        poked = s.select(source,bars)
        book.poke(poked,line_id)
        self.assertEqual("POKED",book.report()["lines"][0]["status"])
        self.assertEqual(book.report(),j.Journal.restore(source,book.checkpoint()).report())
        before = book.report()
        self.assertEqual(line_id,book.validate(ready,line_id))  # Old identical retry, not revival.
        self.assertEqual(before,book.report())
        with self.assertRaises(ValueError):book.trigger_many(poked,[line_id])

    def test_candidate_valid_and_trigger_events_preserve_immutable_history(self):
        line_id = self.book.register(self.snapshot,self.line.geometry_id)
        initial = self.book.report()
        self.book.validate(self.snapshot,line_id)
        valid = self.book.report()
        self.book.trigger_many(self.later(),[line_id])
        final = self.book.report()
        self.assertEqual("CANDIDATE",initial["lines"][0]["status"])
        self.assertEqual("VALID",valid["lines"][0]["status"])
        self.assertEqual("TRIGGERED",final["lines"][0]["status"])
        self.assertTrue(final["lines"][0]["group_consumed"])
        self.assertEqual(initial["events"],final["events"][:1])
        self.assertEqual(valid["events"],final["events"][:2])

    def test_same_formation_bar_trigger_is_rejected_atomically(self):
        line_id = self.seed();before = self.book.report()
        with self.assertRaises(ValueError):self.book.trigger_many(self.snapshot,[line_id])
        self.assertEqual(before,self.book.report())

    def test_unknown_or_mixed_trigger_batch_cannot_partially_consume(self):
        line_id = self.seed();before = self.book.report()
        with self.assertRaises(ValueError):self.book.trigger_many(self.later(),[line_id,"0"*64])
        self.assertEqual(before,self.book.report())

    def test_simultaneous_declared_triggers_consume_all_before_later_filters(self):
        other = declared_line(indices=(0,6,18))
        snapshot = declared_snapshot(self.source,(self.line,other))
        ids = [self.book.register(snapshot,v.geometry_id) for v in snapshot.selected]
        for line_id in ids:self.book.validate(snapshot,line_id)
        self.book.trigger_many(self.later(),ids)
        self.assertTrue(all(v["group_consumed"] for v in self.book.report()["lines"]))
        self.assertTrue(all(v["status"] == "TRIGGERED" for v in self.book.report()["lines"]))

    def test_consumed_group_survives_explicit_alias_merge_and_blocks_trigger(self):
        first = self.seed();self.book.trigger_many(self.later(),[first])
        other = declared_line(indices=(0,6,18),age=42)
        snapshot = self.later(42,(other,))
        second = self.book.register(snapshot,other.geometry_id);self.book.validate(snapshot,second)
        groups = [v["group_id"] for v in self.book.report()["lines"]]
        before = self.book.report()["events"]
        self.book.merge_groups(snapshot,groups)
        report = self.book.report()
        self.assertEqual(before,report["events"][:len(before)])
        self.assertTrue(all(v["group_consumed"] for v in report["lines"]))
        with self.assertRaises(ValueError):self.book.trigger_many(self.later(43),[second])

    def test_new_touch_set_gets_new_instance_and_group_without_resetting_old(self):
        first = self.seed();self.book.trigger_many(self.later(),[first])
        new = declared_line(indices=(0,6,12,18),b_index=12,age=42)
        snapshot = self.later(42,(new,))
        second = self.book.register(snapshot,new.geometry_id);self.book.validate(snapshot,second)
        states = {v["line_id"]:v for v in self.book.report()["lines"]}
        self.assertNotEqual(first,second)
        self.assertNotEqual(states[first]["group_id"],states[second]["group_id"])
        self.assertTrue(states[first]["group_consumed"]);self.assertFalse(states[second]["group_consumed"])

    def test_same_touch_aliases_share_group_and_cannot_reconsume_it(self):
        first = self.seed()
        alias = declared_line(b_index=6,age=41)
        snapshot = self.later(41,(alias,))
        second = self.book.register(snapshot,alias.geometry_id);self.book.validate(snapshot,second)
        self.assertEqual(1,len(self.book.report()["groups"]))
        self.book.trigger_many(self.later(42),[first])
        with self.assertRaises(ValueError):self.book.trigger_many(self.later(43),[second])

    def test_opposing_kinds_cannot_be_merged_as_aliases(self):
        self.seed()
        other = declared_line(kind="support",age=41)
        snapshot = self.later(41,(other,))
        self.book.register(snapshot,other.geometry_id)
        before = self.book.report()
        with self.assertRaises(ValueError):self.book.merge_groups(snapshot,[v["id"] for v in before["groups"]])
        self.assertEqual(before,self.book.report())

    def test_retry_is_idempotent_even_after_later_state_and_restart(self):
        line_id = self.seed()
        snapshot = self.later();self.book.trigger_many(snapshot,[line_id])
        before = self.book.report()
        self.book.trigger_many(snapshot,[line_id]);self.book.register(self.snapshot,self.line.geometry_id)
        self.assertEqual(before,self.book.report())
        restored = j.Journal.restore(self.source,self.book.checkpoint())
        restored.trigger_many(snapshot,[line_id])
        self.assertEqual(before,restored.report())

    def test_strict_poke_requires_actual_negative_distance_and_is_terminal(self):
        line_id = self.seed();before = self.book.report()
        equal = self.later(prices=("101","101.8","100","101"))
        with self.assertRaises(ValueError):self.book.poke(equal,line_id)
        self.assertEqual(before,self.book.report())
        poked = self.later(prices=("101","101.800000000000000001","100","101"))
        self.book.poke(poked,line_id)
        with self.assertRaises(ValueError):self.book.validate(self.later(42,(self.line,)),line_id)
        self.assertEqual("POKED",self.book.report()["lines"][0]["status"])

    def test_age_retirement_is500_exclusive_and501_inclusive(self):
        source = source_for(600)
        snapshot = declared_snapshot(source,(self.line,),index=40)
        book = j.Journal(source);line_id = book.register(snapshot,self.line.geometry_id);book.validate(snapshot,line_id)
        before = book.report()
        with self.assertRaises(ValueError):book.retire(declared_snapshot(source,index=540),line_id)
        self.assertEqual(before,book.report())
        book.retire(declared_snapshot(source,index=541),line_id)
        self.assertEqual("RETIRED",book.report()["lines"][0]["status"])
        self.assertEqual(book.report(),j.Journal.restore(source,book.checkpoint()).report())

    def test_strict_superset_retires_old_line_without_implicit_alias_merge(self):
        line_id = self.seed()
        replacement = declared_line(indices=(0,6,12,18),age=41)
        snapshot = self.later(41,(replacement,))
        self.book.retire(snapshot,line_id,replacement_geometry_id=replacement.geometry_id)
        self.assertEqual("RETIRED",self.book.report()["lines"][0]["status"])
        self.assertEqual(self.book.report(),j.Journal.restore(self.source,self.book.checkpoint()).report())
        with self.assertRaises(ValueError):self.book.register(self.later(42,(self.line,)),self.line.geometry_id)

    def test_replacement_with_no_strict_superset_or_other_kind_is_rejected(self):
        line_id = self.seed();before = self.book.report()
        for value in (declared_line(b_index=6,age=41),declared_line(indices=(0,6,12,18),kind="support",age=41)):
            with self.assertRaises(ValueError):self.book.retire(self.later(41,(value,)),line_id,replacement_geometry_id=value.geometry_id)
            self.assertEqual(before,self.book.report())

    def test_registration_rejects_action_exception_wrong_source_and_mutation(self):
        before = self.book.report()
        bad = declared_snapshot(self.source,(self.line,),role="action_break")
        with self.assertRaises(ValueError):self.book.register(bad,self.line.geometry_id)
        record = self.snapshot.record();record["declaration_sha256"] = "0"*64
        altered = s.SelectedSnapshot(d.canonical(record).decode(),self.snapshot.selected)
        with self.assertRaises(ValueError):self.book.register(altered,self.line.geometry_id)
        self.assertEqual(before,self.book.report())

    def test_cursor_reversal_and_event_limit_reject_before_mutation(self):
        self.seed();before = self.book.report()
        early = declared_snapshot(self.source,(self.line,),index=39)
        with self.assertRaises(ValueError):self.book.register(early,self.line.geometry_id)
        with patch.object(j,"MAX_EVENTS",2):
            with self.assertRaises(ValueError):self.book.trigger_many(self.later(),[before["lines"][0]["line_id"]])
        self.assertEqual(before,self.book.report())

    def test_report_and_checkpoint_copies_cannot_mutate_journal(self):
        self.seed();before = self.book.report()
        report = self.book.report();report["events"][0]["command"]["payload"].clear();report["lines"].clear()
        checkpoint = self.book.checkpoint();checkpoint["events"].clear()
        self.assertEqual(before,self.book.report())

    def test_restart_at_each_candidate_valid_terminal_and_merge_state(self):
        line_id = self.book.register(self.snapshot,self.line.geometry_id)
        self.assertEqual(self.book.report(),j.Journal.restore(self.source,self.book.checkpoint()).report())
        self.book.validate(self.snapshot,line_id)
        self.assertEqual(self.book.report(),j.Journal.restore(self.source,self.book.checkpoint()).report())
        self.book.trigger_many(self.later(),[line_id])
        self.assertEqual(self.book.report(),j.Journal.restore(self.source,self.book.checkpoint()).report())
        new = declared_line(indices=(0,6,18),age=42);snapshot = self.later(42,(new,))
        self.book.register(snapshot,new.geometry_id)
        self.book.merge_groups(snapshot,[v["id"] for v in self.book.report()["groups"]])
        self.assertEqual(self.book.report(),j.Journal.restore(self.source,self.book.checkpoint()).report())

    def test_checkpoint_hash_chain_duplicate_reorder_and_bindings_tampering_refused(self):
        self.seed();original = self.book.checkpoint()
        variants = []
        for change in ("hash","duplicate","reorder","command","source","code"):
            value = deepcopy(original)
            if change == "hash":value["state_sha256"] = "0"*64
            if change == "duplicate":value["events"].append(deepcopy(value["events"][-1]))
            if change == "reorder":value["events"].reverse()
            if change == "command":value["events"][0]["command"]["payload"]["line"]["age_bars"] = 41
            if change == "source":value["declaration_sha256"] = "0"*64
            if change == "code":value["source_bindings"] = {}
            variants.append(value)
        for value in variants:
            with self.assertRaises(ValueError):j.Journal.restore(self.source,value)

    def test_changed_code_or_market_source_cannot_continue_journal(self):
        self.seed();before = self.book.report()
        with patch.object(j,"bindings",return_value={}):
            with self.assertRaises(ValueError):self.book.trigger_many(self.later(),[before["lines"][0]["line_id"]])
        self.assertEqual(before,self.book.report())
        value = self.source.record();value["kind"] = "market_trendline_source"
        with self.assertRaises(ValueError):j.Journal(d.Declaration(json.dumps(value)))

    def test_checkpoint_size_bound_rejects_without_replay(self):
        self.seed()
        with patch.object(j,"MAX_CHECKPOINT_BYTES",1):
            with self.assertRaises(ValueError):j.Journal.restore(self.source,self.book.checkpoint())

    def test_file_suffix_binding_does_not_rename_causal_instances_or_groups(self):
        line_id = self.seed()
        value = self.source.record();value["input_sha256"] = "1"*64
        source = d.Declaration.from_record(value)
        other = j.Journal(source)
        snapshot = declared_snapshot(source,(self.line,))
        other_id = other.register(snapshot,self.line.geometry_id)
        self.assertEqual(line_id,other_id)
        self.assertEqual(self.book.report()["groups"],other.report()["groups"])
        with self.assertRaises(ValueError):j.Journal.restore(source,self.book.checkpoint())

    def test_profile_scope_cannot_change_inside_an_existing_journal(self):
        self.seed();before = self.book.report()
        self.book.profile = "TRL_BRK2_E1"
        with self.assertRaises(ValueError):self.book.checkpoint()
        self.book.profile = "TRL_BRK3_E1"
        self.assertEqual(before,self.book.report())


if __name__ == "__main__":unittest.main()
