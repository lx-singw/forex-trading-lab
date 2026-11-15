"""Invented sources, account checks and health; temporary journals, no native calls."""
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from forex_demo_lab import recorder_boundary_155 as r
from forex_demo_lab.acquisition_lifecycle_138 import AccountMode, Checks, Lifecycle, Policy, State, HOUR_US
from forex_demo_lab.segment_journal_138 import Journal, DiskStore, StorageFailure, MAX_JOB
from forex_demo_lab.supervision_140 import Supervisor, SyntheticHelper, Ledger, Observation, MAX_STATUS_AGE_US, MAX_FRAME, MAX_FRAMES
from forex_demo_lab.helper_health_142 import HealthDecoder
from forex_demo_lab.paired_replay_133 import canonical
from test_acquisition_138 import GOOD, blobs

JOB='a'*32
CONTEXT=dict(epoch=1,digits=5,contract_units=100000,cost_state='unknown')
QUOTE=dict(source_label=10,bid_points=110000,ask_points=110010,flags=6)
ROOT=Path(__file__).resolve().parents[1]


def snap(at, *, checks=GOOD, job=JOB, health=None, owner=True):
    return r.Snapshot(at,checks,health or Observation(job,at,create_ack=True,set_ack=True,ready_signal=True),owner)


def source(kind='triple',at=10, *, job=JOB, label=10):
    if kind=='context':return r.InventedSource([r.Read('context',snap(at,job=job),snap(at+1,job=job),dict(CONTEXT))]),snap(at+2,job=job)
    return r.InventedSource([
        r.Read('clock_before',snap(at,job=job),snap(at+1,job=job),at),
        r.Read('quote',snap(at+2,job=job),snap(at+3,job=job),dict(QUOTE,source_label=label)),
        r.Read('clock_after',snap(at+4,job=job),snap(at+5,job=job),at+5)]),snap(at+6,job=job)


def rewrite(raw, change):
    rows=[json.loads(line.rsplit(b'\t',1)[0]) for line in raw.splitlines()]
    change(rows);result=[];head='0'*64
    for i,row in enumerate(rows,1):
        row['sequence']=i;row['previous']=head;body=canonical(row);head=hashlib.sha256(body).hexdigest()
        result.append(body+b'\t'+head.encode()+b'\n')
    return b''.join(result)


class RecorderBoundary155Tests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        self.addCleanup(self.temp.cleanup)

    def make(self, *, enabled=True, retry=False, budget=60_000_000, job=JOB, limit=r.MAX_BYTES, life_limit=32*1024*1024):
        life=Lifecycle(Journal(job,lambda token:DiskStore(self.root,token),file_limit=life_limit,
                              job_limit=MAX_JOB-limit-MAX_FRAME*MAX_FRAMES),Policy(enabled,retry,budget))
        supervisor=Supervisor(life,SyntheticHelper(),Ledger(self.root,job),enabled=enabled)
        recorder=r.Recorder(supervisor,r.PayloadJournal(self.root,job,limit),enabled=enabled)
        self.addCleanup(recorder.journal.poison)
        self.addCleanup(life.journal.poison)
        self.addCleanup(supervisor.ledger.poison)
        return recorder

    def ready(self, **kwargs):
        recorder=self.make(**kwargs);job=recorder.journal.job
        self.assertTrue(recorder.start(snap(0,job=job)))
        port,final=source('context',1,job=job)
        self.assertTrue(recorder.context(port,final))
        return recorder

    def raw(self, recorder):
        return recorder.journal.path.read_bytes() if recorder.journal.path.exists() else b''

    def inspect(self, recorder):
        return r.inspect(self.raw(recorder),blobs(self.root,recorder.journal.job),recorder.supervisor.ledger.path.read_bytes())

    def test_default_off_has_no_reads_files_or_helper_start(self):
        recorder=self.make(enabled=False);port,final=source()
        self.assertFalse(recorder.start(snap(0)));self.assertFalse(recorder.poll(port,final))
        self.assertEqual([],list(self.root.iterdir()));self.assertEqual(0,port.queries)
        self.assertEqual(0,recorder.supervisor.helper.calls['start'])
        self.assertFalse(recorder.snapshot()['orders_available'])

    def test_never_started_or_poisoned_recorder_has_no_start_stop_side_effects(self):
        recorder=self.make();self.assertFalse(recorder.stop(snap(0)));self.assertEqual([],list(self.root.iterdir()))
        recorder.journal.poison();self.assertFalse(recorder.start(snap(0)))
        self.assertEqual([],list(self.root.iterdir()));self.assertEqual(0,recorder.supervisor.helper.calls['start'])

    def test_invalid_port_guard_records_or_callback_sources_reject_before_use(self):
        for value in ([r.Read('quote',None,snap(2),QUOTE)], [r.Read('order',snap(1),snap(2),QUOTE)], [lambda:QUOTE]):
            with self.assertRaises(ValueError):r.InventedSource(value)
        self.assertEqual([],list(self.root.iterdir()))

    def test_clean_context_and_quote_bind_three_journals(self):
        recorder=self.ready();port,final=source()
        self.assertTrue(recorder.poll(port,final));self.assertEqual(3,port.queries)
        recorder.stop(snap(20));audit=self.inspect(recorder)
        self.assertEqual((1,1,0),(audit['context_count'],audit['published_triples'],audit['unpublished_lifecycle_commits']))
        self.assertTrue(audit['ended']);self.assertFalse(audit['resume_available']);self.assertFalse(audit['durability_ack_proven'])
        self.assertEqual(QUOTE,audit['quotes'][0]['quote'])

    def test_invalid_current_account_or_identity_never_reads_before_guard(self):
        for mode in (AccountMode.REAL,AccountMode.CONTEST,None,1):
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as folder:
                old=self.root;self.root=Path(folder)
                try:
                    recorder=self.make();port,final=source()
                    self.assertFalse(recorder.start(snap(0,checks=replace(GOOD,actual_mode=mode))))
                    self.assertFalse(recorder.poll(port,final));self.assertEqual(0,port.queries)
                    self.assertEqual(0,recorder.supervisor.helper.calls['start'])
                finally:self.root=old

    def test_each_before_and_after_query_guard_discards_values(self):
        for index in range(3):
            for phase in ('before','after'):
                with self.subTest(index=index,phase=phase),tempfile.TemporaryDirectory() as folder:
                    old=self.root;self.root=Path(folder)
                    try:
                        recorder=self.ready();port,final=source();items=list(port.reads);item=items[index]
                        items[index]=replace(item,**{phase:replace(getattr(item,phase),checks=replace(GOOD,identity_unchanged=False))})
                        port=r.InventedSource(items)
                        self.assertFalse(recorder.poll(port,final));audit=self.inspect(recorder)
                        self.assertEqual(index+int(phase=='after'),port.queries)
                        self.assertEqual(0,audit['published_triples']);self.assertFalse(audit['pending_payload'])
                        self.assertNotIn(b'bid_points',self.raw(recorder))
                    finally:self.root=old

    def test_final_guard_after_staging_aborts_without_publishing(self):
        recorder=self.ready();port,final=source();final=replace(final,checks=replace(GOOD,actual_mode=AccountMode.CONTEST))
        self.assertFalse(recorder.poll(port,final));audit=self.inspect(recorder)
        self.assertEqual(3,port.queries);self.assertEqual(0,audit['published_triples'])
        self.assertEqual(0,recorder.supervisor.life.journal.committed)
        self.assertTrue(audit['ended']);self.assertIn(b'bid_points',self.raw(recorder))

    def test_helper_loss_or_stale_status_after_pending_aborts(self):
        for kind in ('stale','power','exit','owner','query','clock','algo'):
            with self.subTest(kind=kind),tempfile.TemporaryDirectory() as folder:
                old=self.root;self.root=Path(folder)
                try:
                    recorder=self.ready();port,final=source(at=2_000_000)
                    if kind=='stale':
                        items=[replace(item,before=replace(item.before,health=replace(item.before.health,observed_us=2_000_000)),
                                      after=replace(item.after,health=replace(item.after.health,observed_us=2_000_000))) for item in port.reads]
                        port=r.InventedSource(items)
                        final=replace(final,at_us=3_000_001,health=replace(final.health,observed_us=2_000_000))
                    if kind=='power':final=replace(final,health=replace(final.health,mains=False))
                    if kind=='exit':final=replace(final,health=replace(final.health,running=False))
                    if kind=='owner':final=replace(final,owner_alive=False)
                    if kind=='query':final=replace(final,checks=replace(GOOD,query_ok=False))
                    if kind=='clock':final=replace(final,checks=replace(GOOD,clock_safe=False))
                    if kind=='algo':final=replace(final,checks=replace(GOOD,algo_enabled=True))
                    self.assertFalse(recorder.poll(port,final));self.assertEqual(0,self.inspect(recorder)['published_triples'])
                    if kind=='stale':self.assertEqual('helper_status_stale',recorder.supervisor.cause.value)
                finally:self.root=old

    def test_missing_context_and_poll_spacing_make_no_source_queries(self):
        recorder=self.make();self.assertTrue(recorder.start(snap(0)));port,final=source()
        self.assertFalse(recorder.poll(port,final));self.assertEqual(0,port.queries)
        ctx,end=source('context',20);self.assertTrue(recorder.context(ctx,end))
        port,end=source(at=30);self.assertTrue(recorder.poll(port,end))
        retry,end=source(at=100);self.assertFalse(recorder.poll(retry,end));self.assertEqual(0,retry.queries)
        recorder.stop(snap(110));self.assertEqual(1,self.inspect(recorder)['published_triples'])

    def test_delayed_helper_readiness_waits_without_reading_source(self):
        recorder=self.make();self.assertTrue(recorder.start(snap(0)))
        port,end=source('context',1);item=port.reads[0]
        port=r.InventedSource([replace(item,before=replace(item.before,health=replace(item.before.health,create_ack=False,set_ack=False,ready_signal=False)))])
        self.assertFalse(recorder.context(port,end));self.assertEqual(0,port.queries)
        self.assertEqual('waiting_ready',recorder.supervisor.state);self.assertEqual(b'',self.raw(recorder))
        self.assertTrue(recorder.context(*source('context',10)))
        self.assertTrue(recorder.poll(*source(at=20)));recorder.stop(snap(30))
        self.assertEqual(1,self.inspect(recorder)['published_triples'])

    def test_hourly_context_refresh_and_deadline(self):
        recorder=self.ready(budget=2*HOUR_US)
        port,final=source(at=HOUR_US+3);self.assertFalse(recorder.poll(port,final));self.assertEqual(0,port.queries)
        ctx,end=source('context',HOUR_US+10);self.assertTrue(recorder.context(ctx,end))
        self.assertTrue(recorder.poll(*source(at=HOUR_US+20)))
        late,final=source(at=2*HOUR_US);self.assertFalse(recorder.poll(late,final));self.assertEqual(0,late.queries)
        self.assertEqual(1,self.inspect(recorder)['published_triples'])

    def test_disconnect_retry_defaults_off_and_opt_in_requires_new_context(self):
        recorder=self.ready(retry=True);port,final=source();final=replace(final,checks=replace(GOOD,connected=False))
        self.assertFalse(recorder.poll(port,final));self.assertEqual(State.INTERRUPTED,recorder.supervisor.life.state)
        due=recorder.supervisor.life.wait_until
        self.assertFalse(recorder.retry(snap(due-1)));self.assertTrue(recorder.retry(snap(due)))
        port,end=source(at=due+1);self.assertFalse(recorder.poll(port,end));self.assertEqual(0,port.queries)
        self.assertTrue(recorder.context(*source('context',due+10)))
        self.assertTrue(recorder.poll(*source(at=due+20)))
        recorder.stop(snap(due+30));audit=self.inspect(recorder)
        self.assertEqual((2,1),(audit['context_count'],audit['published_triples']))

    def test_raw_source_repeats_reversals_and_flags_are_preserved(self):
        recorder=self.ready()
        for i,label in enumerate((9,9,8)):
            self.assertTrue(recorder.poll(*source(at=10+i*1_000_000,label=label)))
        recorder.stop(snap(2_000_020));audit=self.inspect(recorder)
        self.assertEqual((1,1),(audit['adjacent_source_repeats'],audit['source_reversals']))
        self.assertEqual([9,9,8],[q['quote']['source_label'] for q in audit['quotes']])
        self.assertTrue(all(q['quote']['flags']==6 for q in audit['quotes']))

    def test_clean_lifecycle_rotation_requires_new_context(self):
        recorder=self.ready(life_limit=20*1024);rotated=False
        for i in range(30):
            at=10+i*1_000_000;segment=recorder.supervisor.life.journal.segment
            port,end=source(at=at)
            if not recorder.poll(port,end):
                self.assertGreater(recorder.supervisor.life.journal.segment,segment)
                self.assertEqual(0,port.queries);self.assertTrue(recorder.context(*source('context',at+10)))
                self.assertTrue(recorder.poll(*source(at=at+20)));rotated=True;break
        self.assertTrue(rotated);recorder.stop(snap(at+30))
        self.assertGreater(self.inspect(recorder)['context_count'],1)

    def test_bad_payload_never_serializes_unknown_private_fields(self):
        recorder=self.ready();port,end=source();items=list(port.reads)
        items[1]=replace(items[1],value={**QUOTE,'account':'invented_sensitive_marker'})
        port=r.InventedSource(items);self.assertFalse(recorder.poll(port,end))
        self.assertNotIn(b'invented_sensitive_marker',self.raw(recorder));self.assertEqual(0,self.inspect(recorder)['published_triples'])

    def test_source_failure_preserves_attempt_and_stops_without_retries(self):
        recorder=self.ready();port,end=source();port.fail_query=2
        self.assertFalse(recorder.poll(port,end));self.assertEqual(2,port.queries)
        self.assertEqual(0,self.inspect(recorder)['published_triples']);self.assertTrue(self.inspect(recorder)['ended'])

    def test_failure_between_lifecycle_commit_and_payload_ack_is_unpublished(self):
        recorder=self.ready();original=recorder.journal.append
        def fail(event,*args,**kwargs):
            if event=='commit':raise StorageFailure('invented155_commit_failure')
            return original(event,*args,**kwargs)
        with patch.object(recorder.journal,'append',side_effect=fail):self.assertFalse(recorder.poll(*source()))
        audit=self.inspect(recorder)
        self.assertEqual(1,audit['unpublished_lifecycle_commits']);self.assertEqual(0,audit['published_triples'])
        self.assertTrue(audit['pending_payload']);self.assertFalse(audit['ended']);self.assertTrue(recorder.journal.poisoned)
        self.assertEqual('storage_error',recorder.fault);self.assertFalse(recorder.stop(snap(30)))
        self.assertEqual('storage_error',recorder.fault)
        raw=self.raw(recorder);port,end=source(at=1_000_020)
        self.assertFalse(recorder.poll(port,end));self.assertEqual(0,port.queries);self.assertEqual(raw,self.raw(recorder))

    def test_complete_ack_bytes_do_not_prove_the_caller_received_success(self):
        recorder=self.ready();append=recorder.journal.append
        def lost_return(event,*args,**kwargs):
            result=append(event,*args,**kwargs)
            if event=='commit':raise StorageFailure('invented_success_return_lost')
            return result
        with patch.object(recorder.journal,'append',side_effect=lost_return):self.assertFalse(recorder.poll(*source()))
        self.assertEqual(0,recorder.published);audit=self.inspect(recorder)
        self.assertEqual(1,audit['published_triples']);self.assertFalse(audit['durability_ack_proven'])
        self.assertFalse(audit['ended']);self.assertFalse(audit['resume_available'])

    def test_payload_write_sync_close_and_capacity_failures_poison(self):
        class Stream:
            def __init__(self, stream, mode):self.stream,self.mode,self.writes=stream,mode,0
            def write(self, data):
                self.writes+=1
                if self.mode=='write':raise OSError('invented_write')
                return self.stream.write(data[:len(data)//2] if self.mode=='short' else data)
            def flush(self):
                if self.mode=='flush':raise OSError('invented_flush')
                self.stream.flush()
            def fileno(self):return self.stream.fileno()
            def close(self):
                self.stream.close()
                if self.mode=='close':raise OSError('invented_close')
        for mode in ('write','short','flush','fsync','close'):
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as folder:
                old=self.root;self.root=Path(folder)
                try:
                    recorder=self.ready();wrapped=Stream(recorder.journal.stream,mode);recorder.journal.stream=wrapped
                    if mode=='fsync':
                        def fail_sync():
                            wrapped.flush();raise OSError('invented_fsync_ack')
                        with patch.object(recorder.journal,'sync',side_effect=fail_sync):self.assertFalse(recorder.poll(*source()))
                    elif mode=='close':recorder.stop(snap(20))
                    else:self.assertFalse(recorder.poll(*source()))
                    self.assertTrue(recorder.journal.poisoned)
                    self.assertEqual(0,self.inspect(recorder)['published_triples'])
                    before=self.raw(recorder);writes=wrapped.writes;port,end=source(at=1_000_020)
                    self.assertFalse(recorder.poll(port,end));self.assertEqual(0,port.queries)
                    self.assertEqual(writes,wrapped.writes);self.assertEqual(before,self.raw(recorder))
                finally:self.root=old

    def test_payload_open_and_byte_cap_fail_before_further_queries(self):
        recorder=self.make();self.assertTrue(recorder.start(snap(0)))
        original=Path.open
        def fail_open(path,*args,**kwargs):
            if path==recorder.journal.path:raise OSError('invented_open_failure')
            return original(path,*args,**kwargs)
        port,end=source('context',1)
        with patch.object(Path,'open',new=fail_open):self.assertFalse(recorder.context(port,end))
        self.assertEqual(0,port.queries);self.assertTrue(recorder.journal.poisoned)
        fresh=self.ready(job='b'*32,limit=4*r.MAX_FRAME)
        for i in range(40):
            port,end=source(at=10+i*1_000_000,job='b'*32)
            if not fresh.poll(port,end):break
        self.assertTrue(fresh.journal.poisoned)
        self.assertLessEqual(fresh.journal.reserved,4*r.MAX_FRAME)
        self.assertFalse(self.inspect(fresh)['resume_available'])

    def test_lifecycle_commit_failure_leaves_an_explicit_control_prefix(self):
        from forex_demo_lab.segment_journal_138 import Event
        recorder=self.ready();append=recorder.supervisor.life.journal.append
        def fail(event,*args,**kwargs):
            if event is Event.COMMIT:raise StorageFailure('invented_lifecycle_failure')
            return append(event,*args,**kwargs)
        with patch.object(recorder.supervisor.life.journal,'append',side_effect=fail):self.assertFalse(recorder.poll(*source()))
        audit=self.inspect(recorder)
        self.assertEqual(0,audit['published_triples']);self.assertTrue(audit['lifecycle_pending'])
        self.assertFalse(audit['lifecycle_final_close_present'])

    def test_same_job_cannot_reopen_and_new_job_has_no_incoming_payload(self):
        recorder=self.ready();self.assertTrue(recorder.poll(*source()));recorder.stop(snap(20))
        with self.assertRaises(StorageFailure):r.PayloadJournal(self.root,JOB)
        fresh=self.ready(job='b'*32);self.assertTrue(fresh.poll(*source(job='b'*32)))
        fresh.stop(snap(20,job='b'*32));self.assertEqual(1,self.inspect(fresh)['published_triples'])

    def test_truncated_prefix_keeps_pending_and_complete_missing_link_rejects(self):
        recorder=self.ready();self.assertTrue(recorder.poll(*source()));recorder.stop(snap(20))
        raw=self.raw(recorder);segments=blobs(self.root);sup=recorder.supervisor.ledger.path.read_bytes()
        rows=raw.splitlines(keepends=True)
        prepared=next(i for i,line in enumerate(rows) if b'"kind":"triple"' in line and b'"event":"prepared"' in line)
        prefix=b''.join(rows[:prepared+1])+b'{partial'
        audit=r.inspect(prefix,segments,sup);self.assertTrue(audit['pending_payload']);self.assertEqual(0,audit['published_triples'])
        self.assertGreater(audit['trailing_partial_bytes'],0)
        with self.assertRaises(ValueError):r.inspect(raw,segments[:-1],sup)

    def test_rehashed_context_slot_lifecycle_and_job_substitution_reject(self):
        recorder=self.ready();self.assertTrue(recorder.poll(*source()));recorder.stop(snap(20))
        raw=self.raw(recorder);segments=blobs(self.root);sup=recorder.supervisor.ledger.path.read_bytes()
        mutations=[lambda rows:rows[4]['payload'].update(context_ref='f'*64),
                   lambda rows:rows[5].update(slot=9),lambda rows:rows[5].update(life_head='0'*64),
                   lambda rows:rows[0].update(job='b'*32)]
        for change in mutations:
            with self.assertRaises(ValueError):r.inspect(rewrite(raw,change),segments,sup)

    def test_hashes_do_not_authenticate_self_consistently_rewritten_values(self):
        recorder=self.ready();self.assertTrue(recorder.poll(*source()));recorder.stop(snap(20))
        changed=rewrite(self.raw(recorder),lambda rows:rows[4]['payload']['quote'].update(bid_points=110001))
        audit=r.inspect(changed,blobs(self.root),recorder.supervisor.ledger.path.read_bytes())
        self.assertEqual(110001,audit['quotes'][0]['quote']['bid_points'])
        self.assertFalse(audit['producer_authenticated']);self.assertFalse(audit['market_data_qualified'])

    def test_helper_health_protocol_replays_keep_old_status_old(self):
        decoder=HealthDecoder(JOB);challenge='c'*32
        wire=dict(schema='native_health142_status_v1',token=JOB,challenge=challenge,operation='POLL',contained=True,
                  running=True,sample_valid=True,sample_sequence=1,sample_tick_ms=100,owner_tick_ms=120,
                  create_ack=True,set_ack=True,ready_signal=True,mains=True,helper_running_marker=True,cancel_ack=False)
        first=r.decoded_snapshot(decoder,canonical(wire),challenge,2_000_000,2_010_000,GOOD)
        second=r.decoded_snapshot(decoder,canonical(dict(wire,owner_tick_ms=1500)),challenge,3_500_000,3_510_000,GOOD)
        self.assertEqual(first.health.observed_us,second.health.observed_us)
        recorder=self.ready();port,end=source(at=3_500_001)
        items=list(port.reads);items[0]=replace(items[0],before=replace(items[0].before,health=second.health))
        port=r.InventedSource(items)
        self.assertFalse(recorder.poll(port,end));self.assertEqual(0,self.inspect(recorder)['published_triples'])
        self.assertEqual(0,port.queries);self.assertEqual('helper_status_stale',recorder.supervisor.cause.value)

    def test_exact_health_age_equality_is_accepted_at_commit(self):
        recorder=self.ready();port,end=source(at=2_000_000)
        items=[replace(item,before=replace(item.before,health=replace(item.before.health,observed_us=2_000_000)),
                       after=replace(item.after,health=replace(item.after.health,observed_us=2_000_000))) for item in port.reads]
        end=replace(end,at_us=3_000_000,health=replace(end.health,observed_us=2_000_000))
        self.assertTrue(recorder.poll(r.InventedSource(items),end));recorder.stop(snap(3_000_001))
        self.assertEqual(1,self.inspect(recorder)['published_triples'])

    def test_combined_journal_allocation_cannot_exceed_inherited_job_cap(self):
        life=Lifecycle(Journal(JOB,lambda token:DiskStore(self.root,token)),Policy(enabled=True))
        supervisor=Supervisor(life,SyntheticHelper(),Ledger(self.root,JOB),enabled=True)
        with self.assertRaises(ValueError):r.Recorder(supervisor,r.PayloadJournal(self.root,JOB),enabled=True)
        self.assertEqual([],list(self.root.iterdir()))

    def test_invented_payload_is_not136_market_input_or_strategy_admission(self):
        from forex_demo_lab.context_recorder_136 import inspect_bytes
        from forex_demo_lab.elliott_full.admission import study_status,DemoBoundary
        recorder=self.ready();self.assertTrue(recorder.poll(*source()));recorder.stop(snap(20))
        with self.assertRaises(ValueError):inspect_bytes(self.raw(recorder))
        self.assertTrue(all(c['status']=='UNAVAILABLE' and c['returns'] is None for c in study_status()['cells']))
        self.assertFalse(DemoBoundary().submission_status()['available'])

    def test_noncausal_clock_and_unbound_health_do_not_publish(self):
        recorder=self.ready();port,end=source();end=replace(end,at_us=1)
        self.assertFalse(recorder.poll(port,end));self.assertEqual(0,self.inspect(recorder)['published_triples'])

    def test_invented_receipt_markers_cannot_escape_the_query_bracket(self):
        recorder=self.ready();port,end=source();items=list(port.reads)
        items[2]=replace(items[2],value=999999999)
        self.assertFalse(recorder.poll(r.InventedSource(items),end))
        self.assertEqual(0,self.inspect(recorder)['published_triples'])

    def test_wrong_or_unspecified_health_cannot_be_treated_as_fresh(self):
        for health in (Observation(),Observation('b'*32,0),Observation(JOB,None)):
            with self.subTest(health=health),tempfile.TemporaryDirectory() as folder:
                old=self.root;self.root=Path(folder)
                try:
                    recorder=self.make()
                    with self.assertRaises(ValueError):recorder.start(snap(0,health=health))
                    self.assertEqual([],list(self.root.iterdir()))
                finally:self.root=old

    def test_public_cli_default_off_and_fixed_invented_scenarios(self):
        script=ROOT/'scripts/recorder-boundary-155.py';out=self.root/'cli'
        done=subprocess.run([sys.executable,str(script),'--output',str(out)],capture_output=True,text=True,check=True)
        self.assertFalse(json.loads(done.stdout)['enabled']);self.assertFalse(out.exists())
        done=subprocess.run([sys.executable,str(script),'--exercise-invented','--output',str(out)],capture_output=True,text=True)
        self.assertEqual(0,done.returncode,done.stderr)
        report=json.loads((out/'exercise.json').read_text());self.assertEqual(9,len(report['cases']))
        records={r['name']:r for r in report['cases']}
        self.assertEqual(3,records['clean_repeats']['inspection']['published_triples'])
        self.assertEqual(1,records['health_protocol']['inspection']['published_triples'])
        self.assertEqual(10,records['clean_repeats']['source_queries'])
        self.assertEqual(4,records['health_protocol']['source_queries'])
        self.assertEqual(8,records['retry_boundary']['source_queries'])
        self.assertEqual(1,records['orphan_commit']['inspection']['unpublished_lifecycle_commits'])
        self.assertFalse(report['actual_quotes_read']);self.assertFalse(report['native_helper_launched'])
        for args in (['--exercise-invented','--output',str(out)],['--live'],['--native-source']):
            self.assertNotEqual(0,subprocess.run([sys.executable,str(script),*args],capture_output=True).returncode)


if __name__=='__main__':unittest.main()
