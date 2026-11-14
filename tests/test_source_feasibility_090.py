from dataclasses import replace
import hashlib
import io
from pathlib import Path, PureWindowsPath
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch

from forex_demo_lab.source_feasibility_090 import *
from forex_demo_lab.private_guard_065 import NativeIdentity065
import forex_demo_lab.private_guard_065 as private065
from test_native_bindings_087 import fixture087, Reader
from test_compound_acquisition_089 import combined089, SOURCE as COMPOUND_SOURCE, ROOT


def profiles090(reader):
    # Public canonical file sizes/depths; private Windows roles have explicitly
    # SYNTHETIC1-byte profiles. These are not measurements of installed images.
    return {p: Profile090(Path(p).stat().st_size, len(Path(p).parents)+1) if Path(p).is_file()
        else Profile090(1, len(PureWindowsPath(p).parents)+1) for p in reader.hashes}


def coupled090(**cfg):
    captured = {}
    def counted_fixture():
        owner, guard, runner, clock = fixture087()
        source = str(ROOT/COMPOUND_SOURCE)
        owner.reader.hashes[source] = hashlib.sha256((ROOT/COMPOUND_SOURCE).read_bytes()).hexdigest()
        accounting = ReaderAccounting090(owner.reader, profiles090(owner.reader))
        captured['accounting'] = accounting
        return owner, guard, runner, clock
    with patch('test_compound_acquisition_089.fixture087', counted_fixture):
        row = combined089(**cfg)
    a = captured['accounting']
    row.update(reader_count_scope='065_original_numeric_predicates_with_injected_acquisitions',
        reader_counts=dict(a.meter.counts),reader_first_exhausted=a.meter.first_exhausted,
        reader_identity_hashes=a.identity_hashes,reader_model_owned_remaining=len(a.owned),
        reader_model_close_attempts=a.close_attempts,reader_model_free_attempts=a.free_attempts,
        reader_cleanup_exceeded=a.meter.cleanup_exceeded,
        native_reader_verified=False,native_date_admission=False,new_reader_implemented=False)
    return row


def accounting_fixture():
    owner,g,r,c=fixture087()
    a=ReaderAccounting090(owner.reader,profiles090(owner.reader))
    return owner,a


def inventory090():
    owner,g,r,c=fixture087()
    try:
        source=str(ROOT/COMPOUND_SOURCE)
        owner.reader.hashes[source]=hashlib.sha256((ROOT/COMPOUND_SOURCE).read_bytes()).hexdigest()
        profiles=profiles090(owner.reader); rows=[]
        for name,(path,digest) in sorted(owner.pins.hashes.items()):
            repeats=76 + (76 if name in ('terminal','helper') else 0) + (150 if name in ('boot_script','boot_shell') else 0)
            rows.append(dict(name='role:'+name,reads=repeats,size=profiles[path].size,path_nodes=profiles[path].path_nodes))
        for name,(path,digest) in sorted(owner.pins.sources.items()):
            rows.append(dict(name=name,reads=76,size=profiles[path].size,path_nodes=profiles[path].path_nodes))
        rows.append(dict(name=COMPOUND_SOURCE,reads=76,size=profiles[source].size,path_nodes=profiles[source].path_nodes))
        projection=projection090(tuple((Profile090(x['size'],x['path_nodes']),x['reads']) for x in rows))
        return dict(proofs=rows,feasibility=feasibility090(),projection=projection,
            individual_proof_paths=50,source_proof_paths=41,image_helper_sdk_proof_roles=9,
            native_acquisitions_verified=False)
    finally:owner.close()


class Source090Tests(unittest.TestCase):
    def test_source_only_lower_bound_cannot_fit(self):
        r=feasibility090();self.assertEqual(r['source_reads'],3116)
        self.assertFalse(r['source_only_fits']);self.assertFalse(r['contract_fits'])
    def test_identity_internal_hashes_increase_old_explicit_total(self):
        r=feasibility090();self.assertEqual((r['explicit_reads'],r['identity_image_reads'],r['reader_reads']),(4100,152,4252))
        self.assertEqual(r['hash_read_cap'],768)
    def test_each_individual_source_and_image_role_has_fresh_multiplicity(self):
        r=inventory090();rows=r['proofs']
        self.assertEqual(len(rows),50);self.assertEqual(sum(x['reads'] for x in rows),4252)
        self.assertEqual(sum(x['reads'] for x in rows if not x['name'].startswith('role:')),3116)
        self.assertEqual({x['reads'] for x in rows if not x['name'].startswith('role:')},{76})
    def test_projected_reader_process_and_hash_limits_are_separate_from_actual_runtime(self):
        r=inventory090()['projection'];c=r['projected_counts']
        self.assertEqual((c['hash_reads'],c['process_opens'],c['process_snapshots'],c['native_calls']),(4252,152,76,1520))
        self.assertEqual((c['token_queries'],c['closes'],c['local_frees']),(456,380,152))
        self.assertEqual(set(r['exceeded']),{'hash_reads','hash_path_stats'})
        self.assertFalse(r['native_cost_proven']);self.assertFalse(r['sdk_raw_api_and_runner_costs_included'])
    def test_single_hash_projection_matches_actual_counted_hash(self):
        p=Profile090(CHUNK+1,8);m=Counts090();hash_cost090(m,p)
        c=projection090(((p,1),))['projected_counts']
        for key in ('hash_reads','hash_bytes','hash_path_stats'):
            self.assertEqual(c[key],m.counts[key])
    def test_projection_cannot_accept_zero_byte_or_bool_read_discount(self):
        for p,n in ((Profile090(0,1),1),(Profile090(1,0),1),(Profile090(1,1),False)):
            with self.assertRaises(Exception):projection090(((p,n),))
    def test_even_one_pass_is_impossible_and_is_not_admitted(self):
        r=feasibility090(passes=1);self.assertEqual(r['source_reads'],1558)
        self.assertFalse(r['source_only_fits']);self.assertFalse(r['native_experiment_can_proceed'])
    def test_cost_review_module_would_increase_runnable_source_floor(self):
        self.assertEqual(feasibility090(sources=42)['source_reads'],3192)
        self.assertFalse(feasibility090()['counted_current_090_source'])
    def test_malformed_counts_reject_instead_of_negative_or_bool_discount(self):
        for value in (True,False,0,-1,1.0,None):
            with self.assertRaises(Exception):feasibility090(sources=value)
    def test_caps_immutable_and_equal_to_frozen_original(self):
        self.assertEqual(dict(CAPS),LIMITS)
        with self.assertRaises(TypeError):CAPS['hash_reads']=4252
    def test_batch_archive_manifest_cache_and_single_pass_rejected(self):
        for kind in ('archive','manifest','cached','batch_as_one','single_pass',None):
            with self.assertRaises(Exception):representation090(kind)
        self.assertFalse(representation090('individual_fresh_before_after')['contract_fits'])
    def test_archive_hash_cannot_detect_separate_execution_file_change(self):
        archive=b'frozen source archive';paths={'helper.py':b'old'}
        archive_pin=hashlib.sha256(archive).hexdigest();path_pin=hashlib.sha256(paths['helper.py']).hexdigest()
        paths['helper.py']=b'changed execution source'
        self.assertEqual(hashlib.sha256(archive).hexdigest(),archive_pin)
        self.assertNotEqual(hashlib.sha256(paths['helper.py']).hexdigest(),path_pin)
    def test_original_predicate_accepts_exact_cap_then_rejects_without_increment(self):
        m=Counts090()
        for _ in range(768):m.consume('hash_reads')
        with self.assertRaises(Exception):m.consume('hash_reads')
        self.assertEqual(m.counts['hash_reads'],768);self.assertEqual(m.first_exhausted,'hash_reads')
        with self.assertRaises(Exception):m.consume('hash_bytes')
        self.assertEqual(m.counts['hash_bytes'],0)
    def test_cleanup_still_counted_after_exhaustion_and_flags_overflow(self):
        m=Counts090();m.counts['hash_reads']=768
        with self.assertRaises(Exception):m.consume('hash_reads')
        m.counts['closes']=1600;m.cleanup('closes')
        self.assertEqual(m.counts['closes'],1601);self.assertTrue(m.cleanup_exceeded)
    def test_hash_chunks_bytes_ancestry_and_clocks_match_actual065_method(self):
        for size,nodes in ((1,1),(CHUNK,4),(CHUNK+1,3)):
            raw=b'x'*size
            class FakePath:
                parents=tuple(range(nodes-1))
                def lstat(self):return NS(st_file_attributes=0,st_mode=0)
                def stat(self):return NS(st_size=size,st_dev=1,st_ino=2,st_mtime_ns=3)
                def open(self,mode):self.assert_mode=mode;return io.BytesIO(raw)
            p=FakePath();p.parents=tuple(FakePath() for _ in range(nodes-1))
            real=Counts090();model=Counts090()
            with patch.object(private065,'Path',lambda value:p):
                digest=NativeIdentity065.hash_file(NS(meter=real),'injected')
            hash_cost090(model,Profile090(size,nodes))
            self.assertEqual(digest,hashlib.sha256(raw).hexdigest());self.assertEqual(real.counts,model.counts)
    def test_hash_rejects_zero_oversize_and_bool_sizes(self):
        for size in (0,FILE_CAP+1,True):
            with self.assertRaises(Exception):hash_cost090(Counts090(),Profile090(size,2))
    def test_complete_ancestry_is_charged_for_each_fresh_read(self):
        m=Counts090();p=Profile090(10,7)
        hash_cost090(m,p);hash_cost090(m,p)
        self.assertEqual((m.counts['hash_reads'],m.counts['hash_path_stats'],m.counts['hash_bytes']),(2,18,20))
    def test_path_and_byte_caps_reject_before_extra_io(self):
        for key in ('hash_path_stats','hash_bytes'):
            m=Counts090();m.counts[key]=CAPS[key]
            with self.assertRaises(Exception):hash_cost090(m,Profile090(1,1))
            self.assertEqual(m.counts[key],CAPS[key]);self.assertEqual(m.first_exhausted,key)
    def test_identity_hash_process_token_native_and_cleanup_counts(self):
        owner,a=accounting_fixture()
        try:
            before=a.meter.counts['clock_samples'];value=owner.reader.identity(owner.pins.terminal.pid)
            self.assertEqual(value,owner.pins.terminal)
            c=a.meter.counts
            self.assertEqual((c['process_opens'],c['identity_tokens'],c['token_queries'],c['native_calls']),(1,1,3,8))
            self.assertEqual((c['hash_reads'],c['closes'],c['local_frees']),(1,2,1));self.assertEqual(a.identity_hashes,1)
            self.assertEqual(c['clock_samples']-before,31);self.assertEqual(a.owned,[])
        finally:owner.close()
    def test_identity_hash_failure_still_attempts_each_registered_close_once(self):
        owner,a=accounting_fixture();a.meter.counts['hash_reads']=768
        try:
            with self.assertRaises(Exception):owner.reader.identity(owner.pins.terminal.pid)
            self.assertEqual(a.owned,[]);self.assertEqual((a.close_attempts,a.free_attempts),(2,1))
            self.assertEqual(a.meter.counts['hash_reads'],768)
        finally:owner.close()
    def test_unique_process_snapshot_entries_and_close_are_charged(self):
        owner,a=accounting_fixture()
        try:
            self.assertEqual(owner.reader.unique_pid(),owner.pins.terminal.pid)
            c=a.meter.counts;self.assertEqual((c['process_snapshots'],c['process_entries'],c['native_calls'],c['closes']),(1,2,4,1))
            self.assertEqual(c['clock_samples'],12);self.assertEqual(a.owned,[])
        finally:owner.close()
    def test_post_native_clock_failure_registers_and_cleans_snapshot(self):
        owner,a=accounting_fixture();a.meter.counts['clock_samples']=CAPS['clock_samples']-2
        try:
            with self.assertRaises(Exception):owner.reader.unique_pid()
            self.assertEqual(a.close_attempts,1);self.assertEqual(a.owned,[])
        finally:owner.close()
    def test_full_six_control_target_rejects_under_all_reader_predicates(self):
        r=coupled090();self.assertFalse(r['modeled_completed'],r)
        self.assertEqual(r['reader_first_exhausted'],'hash_reads');self.assertEqual(r['reader_counts']['hash_reads'],768)
        self.assertLess(len(r['controls']),6);self.assertEqual(r['reader_model_owned_remaining'],0)
        self.assertEqual((r['remaining_handles'],r['remaining_allocations'],r['sdk_shutdown_attempts']),(0,0,1))
        self.assertTrue(r['summary']['cleanup_confirmed']);self.assertTrue(r['sdk_cleanup_confirmed'])
    def test_source_change_detected_with_fresh_counted_reader(self):
        r=coupled090(mutation='source_change',new_source_only=True)
        self.assertFalse(r['modeled_completed']);self.assertTrue(r['mutation_injected'])
        self.assertIsNone(r['reader_first_exhausted']);self.assertEqual(r['summary']['valid_guard_spans'],1)
    def test_image_hash_change_is_visible_inside_identity(self):
        owner,a=accounting_fixture()
        try:
            owner.reader.hashes[owner.pins.terminal.image]='0'*64
            self.assertNotEqual(owner.reader.identity(owner.pins.terminal.pid),owner.pins.terminal)
        finally:owner.close()
    def test_default_off_performs_zero_reader_acquisitions(self):
        r=coupled090(enabled=False);self.assertEqual(r['reader_counts']['hash_reads'],0)
        self.assertEqual(r['reader_counts']['native_calls'],0);self.assertEqual(r['api_calls'],0)
    def test_expired_native_gate_is_unmodified_and_entry_unavailable(self):
        from test_synchronization_086 import Clock086
        with self.assertRaises(Exception):Meter065(Clock086())
        with self.assertRaises(Exception):native_entry090()
        self.assertFalse(coupled090(enabled=False)['native_date_admission'])


if __name__=='__main__':unittest.main()
