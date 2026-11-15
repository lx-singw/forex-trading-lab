"""Invented closed diagnostics and replay checks; no native helper/account activity."""
from dataclasses import replace
import contextlib
import hashlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from forex_demo_lab.diagnostic_bridge_159 import Bridge
from forex_demo_lab.diagnostic_source_159 import capture
from forex_demo_lab.diagnostic_audit_159 import inspect
from forex_demo_lab.diagnostic_fixture_159 import make_source,snapshot,sync_fault,life_commit_fault,abandon,main
from forex_demo_lab.acquisition_lifecycle_138 import AccountMode
from forex_demo_lab.segment_journal_138 import StorageFailure
from forex_demo_lab.recorder_files_157 import write_file
from forex_demo_lab.relay_audit_158 import inspect_job
from forex_demo_lab.paired_replay_133 import canonical

SOURCE_JOB='a'*32
REPLAY='b'*32
ROOT=Path(__file__).resolve().parents[1]


def rehash_binding(output,change):
    path=output/'Binding159.journal';rows=[];old_heads=[]
    for line in path.read_bytes().splitlines():
        body,head=line.rsplit(b'\t',1);rows.append(json.loads(body));old_heads.append(head.decode())
    original_context=next((h for r,h in zip(rows,old_heads) if r['event']=='context'),None)
    change(rows);result=[];head='0'*64;mapping={};new_context=None
    for index,row in enumerate(rows,1):
        row['sequence']=index;row['previous']=head
        if row['context_binding']==original_context and new_context is not None:row['context_binding']=new_context
        body=canonical(row);head=hashlib.sha256(body).hexdigest();result.append(body+b'\t'+head.encode()+b'\n')
        if index<=len(old_heads):mapping[old_heads[index-1]]=head
        if row['event']=='context':new_context=head
    path.write_bytes(b''.join(result))
    receipt=json.loads((output/'Receipt159.json').read_bytes());receipt['binding_ack_head']=mapping.get(receipt['binding_ack_head'],receipt['binding_ack_head'])
    (output/'Receipt159.json').write_bytes(canonical(receipt)+b'\n')


class Lifecycle159Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sources=tempfile.TemporaryDirectory();cls.source=make_source(Path(cls.sources.name)/'full',SOURCE_JOB)
        cls.failed=make_source(Path(cls.sources.name)/'failed',SOURCE_JOB,True)
    @classmethod
    def tearDownClass(cls):cls.sources.cleanup()
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
    def snap(self,at):return snapshot(at,REPLAY)
    def ready(self,source=None,budget=30_000_000):
        source=source or self.source;bridge=Bridge(self.root/'Replay',REPLAY,enabled=True,budget_us=budget)
        self.assertTrue(bridge.start(source,SOURCE_JOB,self.snap(0)));self.assertTrue(bridge.context(self.snap(10),self.snap(11)))
        self.addCleanup(lambda:abandon(bridge));return bridge
    def prepared(self):
        bridge=self.ready();self.assertTrue(bridge.begin(self.snap(20)));self.assertTrue(bridge.prepare(self.snap(21)));return bridge
    def complete(self):
        bridge=self.prepared();self.assertTrue(bridge.commit(self.snap(22)));self.assertTrue(bridge.finish(self.snap(30)));return bridge
    def audit(self,bridge,source=None):return inspect(bridge.output,source or self.source)

    def test_default_off_never_admits_reads_or_creates_files(self):
        bridge=Bridge(self.root/'absent',REPLAY)
        with patch('forex_demo_lab.diagnostic_bridge_159.capture',side_effect=AssertionError('source access')):
            self.assertFalse(bridge.start('/absent',SOURCE_JOB,self.snap(0)))
        self.assertEqual(list(self.root.iterdir()),[]);self.assertFalse(bridge.begin(self.snap(1)))

    def test_full_context_triple_joins_all_journals(self):
        bridge=self.complete();value=self.audit(bridge)
        self.assertEqual((value['physical_binding_commits'],value['acknowledged_binding_commits'],value['published_diagnostic_triples']),(1,1,1))
        self.assertEqual(value['unpublished_lifecycle_commits'],0);self.assertTrue(value['ended']);self.assertFalse(value['market_eligible'])
        self.assertTrue(value['replay_checks_are_invented']);self.assertFalse(value['caller_acknowledgement_known'])

    def test_failed_metadata_remains_unknown_with_raw_source_binding(self):
        bridge=self.ready(self.failed);self.assertTrue(bridge.begin(self.snap(20)));self.assertTrue(bridge.prepare(self.snap(21)))
        self.assertTrue(bridge.commit(self.snap(22)));self.assertTrue(bridge.finish(self.snap(30)))
        value=self.audit(bridge,self.failed);self.assertEqual(value['profile'],'failed_metadata');self.assertEqual(value['published_diagnostic_triples'],1)
        descriptor=json.loads((bridge.output/'Source159.json').read_bytes());self.assertFalse(descriptor['source_origin_authenticated'])
        self.assertEqual(descriptor['files']['NativePort156.txt'],hashlib.sha256((self.failed/'NativePort156.txt').read_bytes()).hexdigest())

    def test_profile_gate_rejects_otherwise_consistent_changed_native_prices(self):
        source=self.root/('Job156-'+SOURCE_JOB);shutil.copytree(self.source,source)
        path=source/'NativePort156.txt';chain='0'*64;lines=[]
        for line in path.read_bytes().splitlines():
            fields=line.rsplit(b'\t',1)[0].decode().split('\t')
            if fields[0]=='T':fields[15]='3FF0000000000000'
            payload='\t'.join(fields);chain=hashlib.sha256((chain+'\t'+payload+'\n').encode()).hexdigest().upper();lines.append((payload+'\t'+chain+'\n').encode())
        path.write_bytes(b''.join(lines));receipt=json.loads((source/'Relay157.json').read_bytes());receipt['native_sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
        (source/'Relay157.json').write_text(json.dumps(receipt));self.assertTrue(inspect_job(source,SOURCE_JOB)['writer_complete'])
        bridge=Bridge(self.root/'rejected',REPLAY,enabled=True);self.assertFalse(bridge.start(source,SOURCE_JOB,self.snap(0)))
        self.assertFalse(bridge.output.exists())

    def test_incomplete_source_rejected_before_lifecycle_creation(self):
        source=self.root/('Job156-'+SOURCE_JOB);shutil.copytree(self.source,source);(source/'Relay157.json').unlink()
        bridge=Bridge(self.root/'rejected',REPLAY,enabled=True);self.assertFalse(bridge.start(source,SOURCE_JOB,self.snap(0)))
        self.assertFalse(bridge.output.exists())

    def test_real_contest_unknown_or_native_numeric_enum_cannot_start_replay(self):
        for index,mode in enumerate((AccountMode.REAL,AccountMode.CONTEST,None,0,1)):
            bridge=Bridge(self.root/f'case{index}',REPLAY,enabled=True);sample=self.snap(0);sample=replace(sample,checks=replace(sample.checks,actual_mode=mode))
            self.assertFalse(bridge.start(self.source,SOURCE_JOB,sample));self.assertEqual(bridge.supervisor.helper.calls['start'],0)
            self.assertEqual(self.audit(bridge)['published_diagnostic_triples'],0)

    def test_each_context_and_pending_guard_discards_publication(self):
        for stage in ('context_before','context_after','begin','prepare','commit','finish'):
            bridge=Bridge(self.root/stage,REPLAY,enabled=True);self.assertTrue(bridge.start(self.source,SOURCE_JOB,self.snap(0)))
            bad=lambda at:replace(self.snap(at),checks=replace(self.snap(at).checks,identity_unchanged=False))
            if stage.startswith('context'):self.assertFalse(bridge.context(bad(10) if stage=='context_before' else self.snap(10),bad(11) if stage=='context_after' else self.snap(11)))
            else:
                self.assertTrue(bridge.context(self.snap(10),self.snap(11)))
                if stage=='begin':self.assertFalse(bridge.begin(bad(20)))
                else:
                    self.assertTrue(bridge.begin(self.snap(20)))
                    if stage=='prepare':self.assertFalse(bridge.prepare(bad(21)))
                    else:
                        self.assertTrue(bridge.prepare(self.snap(21)))
                        if stage=='commit':self.assertFalse(bridge.commit(bad(22)))
                        else:self.assertTrue(bridge.commit(self.snap(22)));self.assertFalse(bridge.finish(bad(30)))
            self.assertEqual(self.audit(bridge)['published_diagnostic_triples'],0)

    def test_helper_owner_power_stale_and_binding_faults_abort_pending(self):
        for index,kind in enumerate(('owner','power','exit','stale','binding')):
            old=self.root;self.root=old/str(index);self.root.mkdir()
            try:
                bridge=self.prepared();sample=self.snap(22)
                if kind=='owner':sample=replace(sample,owner_alive=False)
                if kind=='power':sample=replace(sample,health=replace(sample.health,mains=False))
                if kind=='exit':sample=replace(sample,health=replace(sample.health,running=False))
                if kind=='stale':sample=replace(sample,at_us=1_000_022,health=replace(sample.health,observed_us=21))
                if kind=='binding':sample=replace(sample,health=replace(sample.health,token=SOURCE_JOB))
                self.assertFalse(bridge.commit(sample));value=self.audit(bridge);self.assertEqual(value['published_diagnostic_triples'],0);self.assertFalse(value['lifecycle_pending'])
            finally:self.root=old

    def test_missing_replay_binding_or_health_clock_is_never_auto_filled(self):
        for index,key in enumerate(('token','observed_us')):
            old=self.root;self.root=old/str(index);self.root.mkdir()
            try:
                bridge=self.prepared();sample=self.snap(22);sample=replace(sample,health=replace(sample.health,**{key:None}))
                self.assertFalse(bridge.commit(sample));self.assertEqual(self.audit(bridge)['published_diagnostic_triples'],0)
            finally:self.root=old

    def test_reversal_and_deadline_equality_fail_closed(self):
        bridge=self.prepared();self.assertFalse(bridge.commit(self.snap(20)));self.assertEqual(self.audit(bridge)['published_diagnostic_triples'],0)
        other=Bridge(self.root/'deadline',REPLAY,enabled=True,budget_us=22);self.assertTrue(other.start(self.source,SOURCE_JOB,self.snap(0)))
        self.assertTrue(other.context(self.snap(10),self.snap(11)));self.assertTrue(other.begin(self.snap(20)));self.assertTrue(other.prepare(self.snap(21)))
        self.assertFalse(other.commit(self.snap(22)));self.assertEqual(self.audit(other)['published_diagnostic_triples'],0)

    def test_duplicates_and_out_of_order_operations_never_duplicate_commits(self):
        bridge=self.ready();self.assertFalse(bridge.commit(self.snap(12)));self.assertFalse(bridge.context(self.snap(12),self.snap(13)))
        self.assertTrue(bridge.begin(self.snap(20)));self.assertFalse(bridge.begin(self.snap(20)));self.assertTrue(bridge.prepare(self.snap(21)))
        self.assertFalse(bridge.prepare(self.snap(21)));self.assertTrue(bridge.commit(self.snap(22)));self.assertFalse(bridge.commit(self.snap(22)))
        self.assertTrue(bridge.finish(self.snap(30)));before=(bridge.output/'Binding159.journal').read_bytes();self.assertFalse(bridge.finish(self.snap(31)))
        self.assertEqual(before,(bridge.output/'Binding159.journal').read_bytes());self.assertEqual(self.audit(bridge)['published_diagnostic_triples'],1)

    def test_abort_from_begin_or_prepared_has_no_commit(self):
        bridge=self.ready();self.assertTrue(bridge.begin(self.snap(20)));self.assertFalse(bridge.abort(self.snap(21)))
        value=self.audit(bridge);self.assertEqual(value['physical_binding_commits'],0);self.assertFalse(value['lifecycle_pending']);self.assertTrue(value['ended'])

    def test_binding_commit_present_without_ack_is_not_published(self):
        bridge=self.prepared();sync_fault(bridge.journal,'commit');self.assertFalse(bridge.commit(self.snap(22)))
        value=self.audit(bridge);self.assertEqual((value['physical_binding_commits'],value['acknowledged_binding_commits'],value['published_diagnostic_triples']),(1,0,0))
        self.assertEqual(value['unpublished_lifecycle_commits'],1)

    def test_lifecycle_commit_present_without_ack_is_not_published(self):
        bridge=self.prepared();life_commit_fault(bridge);self.assertFalse(bridge.commit(self.snap(22)))
        value=self.audit(bridge);self.assertEqual(value['published_diagnostic_triples'],0);self.assertEqual(value['unpublished_lifecycle_commits'],1)

    def test_binding_prepare_ack_failure_retains_unpublished_prefix(self):
        bridge=self.ready();self.assertTrue(bridge.begin(self.snap(20)));sync_fault(bridge.journal,'prepared')
        self.assertFalse(bridge.prepare(self.snap(21)));self.assertEqual(self.audit(bridge)['published_diagnostic_triples'],0)
        before=(bridge.output/'Binding159.journal').read_bytes();self.assertFalse(bridge.prepare(self.snap(22)));self.assertEqual(before,(bridge.output/'Binding159.journal').read_bytes())

    def test_lifecycle_or_supervision_close_storage_fault_prevents_publication(self):
        for index,kind in enumerate(('life','super')):
            old=self.root;self.root=old/str(index);self.root.mkdir()
            try:
                bridge=self.prepared();self.assertTrue(bridge.commit(self.snap(22)))
                if kind=='life':
                    original=bridge.life.journal.store.sync
                    def fail(stream):stream.flush();raise OSError('invented stop failure')
                    bridge.life.journal.store.sync=fail
                else:bridge.supervisor.ledger._sync=lambda: (_ for _ in ()).throw(OSError('invented control storage'))
                self.assertFalse(bridge.finish(self.snap(30)));self.assertEqual(self.audit(bridge)['published_diagnostic_triples'],0)
            finally:self.root=old

    def test_binding_short_write_retains_partial_bytes(self):
        bridge=self.ready();self.assertTrue(bridge.begin(self.snap(20)));stream=bridge.journal.stream
        class Short:
            def write(self,value):return stream.write(value[:len(value)//2])
            def close(self):stream.close()
        bridge.journal.stream=Short();self.assertFalse(bridge.prepare(self.snap(21)))
        value=self.audit(bridge);self.assertGreater(value['binding_partial_bytes'],0);self.assertEqual(value['published_diagnostic_triples'],0)

    def test_capacity_failure_cannot_retry_or_publish(self):
        bridge=self.prepared();bridge.journal.reserved=131072;self.assertFalse(bridge.commit(self.snap(22)))
        self.assertTrue(bridge.journal.poisoned);self.assertEqual(self.audit(bridge)['published_diagnostic_triples'],0)

    def test_crash_prefixes_never_infer_publication_or_resume(self):
        for index,phase in enumerate(('prepared','committed')):
            old=self.root;self.root=old/str(index);self.root.mkdir()
            try:
                bridge=self.prepared()
                if phase=='committed':self.assertTrue(bridge.commit(self.snap(22)))
                abandon(bridge);value=self.audit(bridge)
                self.assertFalse(value['receipt_present']);self.assertIsNone(value['acknowledged_binding_commits']);self.assertEqual(value['published_diagnostic_triples'],0)
                self.assertFalse(value['resume_available']);self.assertTrue(value['supervision_unobserved_lifecycle_suffix'])
            finally:self.root=old

    def test_receipt_ack_uncertainty_is_not_inferred_from_bytes(self):
        bridge=self.prepared();self.assertTrue(bridge.commit(self.snap(22)))
        def uncertain(path,value):
            write_file(path,value)
            if path.name=='Receipt159.json':raise OSError('invented missing receipt acknowledgement')
        with patch('forex_demo_lab.diagnostic_bridge_159.write_file',side_effect=uncertain):self.assertFalse(bridge.finish(self.snap(30)))
        self.assertFalse(bridge.receipt_ack);value=self.audit(bridge);self.assertEqual(value['published_diagnostic_triples'],1);self.assertFalse(value['caller_acknowledgement_known'])

    def test_source_changes_are_detected_before_lifecycle_commit(self):
        source=self.root/('Job156-'+SOURCE_JOB);shutil.copytree(self.source,source);bridge=self.ready(source)
        self.assertTrue(bridge.begin(self.snap(20)));self.assertTrue(bridge.prepare(self.snap(21)))
        original=(source/'Reply0001.txt').read_bytes();(source/'Reply0001.txt').write_bytes(b'changed')
        self.assertFalse(bridge.commit(self.snap(22)));self.assertEqual(bridge.life.journal.committed,0)
        with self.assertRaises(ValueError):self.audit(bridge,source)
        (source/'Reply0001.txt').write_bytes(original);self.assertEqual(self.audit(bridge,source)['published_diagnostic_triples'],0)

    def test_existing_directory_and_nonce_reuse_are_rejected(self):
        bridge=self.complete();before={str(p.relative_to(bridge.output)):p.read_bytes() for p in bridge.output.rglob('*') if p.is_file()}
        other=Bridge(bridge.output,REPLAY,enabled=True);self.assertFalse(other.start(self.source,SOURCE_JOB,self.snap(0)))
        self.assertEqual(before,{str(p.relative_to(bridge.output)):p.read_bytes() for p in bridge.output.rglob('*') if p.is_file()})
        wrong=Bridge(self.root/'same_nonce',SOURCE_JOB,enabled=True);self.assertFalse(wrong.start(self.source,SOURCE_JOB,snapshot(0,SOURCE_JOB)));self.assertFalse(wrong.output.exists())

    def test_fresh_job_restart_keeps_original_failed_prefix(self):
        bridge=self.prepared();bridge.abort(self.snap(22));before=(bridge.output/'Binding159.journal').read_bytes()
        job='c'*32;other=Bridge(self.root/'fresh',job,enabled=True);snap=lambda at:snapshot(at,job)
        self.assertTrue(other.start(self.source,SOURCE_JOB,snap(0)));self.assertTrue(other.context(snap(10),snap(11)));self.assertTrue(other.begin(snap(20)))
        self.assertTrue(other.prepare(snap(21)));self.assertTrue(other.commit(snap(22)));self.assertTrue(other.finish(snap(30)))
        self.assertEqual(self.audit(other)['published_diagnostic_triples'],1);self.assertEqual(before,(bridge.output/'Binding159.journal').read_bytes())

    def test_output_parent_links_reject_before_creation(self):
        target=self.root/'target';target.mkdir();link=self.root/'link';link.symlink_to(target,target_is_directory=True)
        bridge=Bridge(link/'new',REPLAY,enabled=True);self.assertFalse(bridge.start(self.source,SOURCE_JOB,self.snap(0)));self.assertFalse((target/'new').exists())

    def test_rehashed_semantic_binding_corruption_is_rejected(self):
        original=self.complete().output
        for index,change in enumerate((lambda rows:next(r for r in rows if r['event']=='prepared').update(source_ref='f'*64),lambda rows:next(r for r in rows if r['event']=='commit').update(slot=2),lambda rows:next(r for r in rows if r['event']=='commit').update(life_head=next(r['life_head'] for r in rows if r['event']=='context')),lambda rows:next(r for r in rows if r['event']=='prepared').update(context_binding='f'*64))):
            copy=self.root/f'corrupt{index}';shutil.copytree(original,copy);rehash_binding(copy,change)
            with self.assertRaises(ValueError):inspect(copy,self.source)

    def test_receipt_prefix_forgery_types_and_unknown_fields_reject(self):
        bridge=self.complete();path=bridge.output/'Receipt159.json';value=json.loads(path.read_bytes())
        for update in ({'binding_commit_acks':True},{'binding_ack_head':'f'*64},{'life_ack_head':'f'*64},{'publishable':1},{'unknown':'extra'}):
            path.write_bytes(canonical(dict(value,**update))+b'\n')
            with self.assertRaises(ValueError):self.audit(bridge)

    def test_native_input_and_binding_bytes_are_not_silently_repaired(self):
        bridge=self.complete();path=bridge.output/'Binding159.journal';original=path.read_bytes()
        for bad in (original.replace(b'\n',b'\r\n'),original[:-1],original+b'x'*8192,b'bad'):
            path.write_bytes(bad)
            with self.assertRaises(ValueError):self.audit(bridge)
        path.write_bytes(original);self.assertEqual(self.audit(bridge)['published_diagnostic_triples'],1)

    def test_closed_lifecycle_suffix_and_missing_receipt_cannot_self_publish(self):
        bridge=self.complete();segment=next((bridge.output/('InventedJob138-'+REPLAY)).glob('*.journal'));original=segment.read_bytes();segment.write_bytes(original+b'x')
        with self.assertRaises(ValueError):self.audit(bridge)
        segment.write_bytes(original);(bridge.output/'Receipt159.json').unlink()
        value=self.audit(bridge);self.assertEqual(value['published_diagnostic_triples'],0);self.assertIsNone(value['acknowledged_binding_commits'])

    def test_default_off_and_read_only_check_cli(self):
        absent=self.root/'absent'
        with contextlib.redirect_stdout(io.StringIO()) as output:main(['--output',str(absent)])
        self.assertFalse(json.loads(output.getvalue())['enabled']);self.assertFalse(absent.exists())
        bridge=self.complete();command=[sys.executable,str(ROOT/'scripts/check-diagnostic-lifecycle-159.py'),'--output',str(bridge.output),'--source',str(self.source)]
        result=subprocess.run(command,check=True,capture_output=True,text=True);self.assertEqual(json.loads(result.stdout)['published_diagnostic_triples'],1)
        (bridge.output/'Source159.json').write_bytes(b'{}');result=subprocess.run(command,capture_output=True,text=True)
        self.assertEqual(result.returncode,2);self.assertFalse(json.loads(result.stdout)['market_eligible'])


if __name__=='__main__':unittest.main()
