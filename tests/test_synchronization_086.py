from dataclasses import replace
from datetime import datetime, timezone
import json
from pathlib import Path, PureWindowsPath
import subprocess
from tempfile import TemporaryDirectory
import unittest

from forex_demo_lab.synchronization_086 import *
from forex_demo_lab.synchronization_084 import Ace084

ROOT=Path(__file__).resolve().parents[1]


class Clock086:
    def __init__(self):
        self.boot=100000;self.elapsed=0;self.calls=0
        self.utc=int(datetime(2026,10,8,12,tzinfo=timezone.utc).timestamp()*1000)
    def advance(self,ms):self.boot+=ms;self.elapsed+=ms
    def __call__(self):
        self.calls+=1;return self.utc+self.elapsed,self.elapsed*1000000,self.boot


def bindings086():
    ep=b'private-episode!'
    ep=(ep+b'x')[:16]
    root='C:\\lab\\ForexDemoSynchronization086-'+PHASE+'-'+ep.hex()
    return Bindings086('a'*64,'b'*64,'c'*64,ep,b'private-user-sid',root,(4,5,6),(8,9,10),
        Peer084(500123987,700789321,2,b'private-logon',b'private-boot'),
        tuple((1,2,3) for p in PureWindowsPath(root).parents))


class BackendModel086:
    model_only=True
    def __init__(self,b,c,cfg):
        self.b,self.c,self.cfg=b,c,cfg;self.live={};self.closed=[];self.finishes=0
        self.inspections=0;self.writes=[];self.reads=0;self.waits=[];self.request=None
        self.hold_start=0;self.hold_end=0
        self.security=Security084(b.owner_sid,0x1004,(Ace084(0,0,0x1f01ff,b.owner_sid),))
    def register(self,owner,h,spec):
        self.live[h]=spec;owner.register(h,spec)
    def setup(self,owner):
        owner.install(self)
        self.register(owner,101,Spec084('pipe',self.b.pipe,READ|WRITE,0,1,FIRST_INSTANCE))
        self.register(owner,102,Spec084('root',self.b.root,META,7,3,NO_REPARSE|0x2000000))
        self.register(owner,103,Spec084('metadata',self.b.root+'\\synthetic.bin',META,7,3,NO_REPARSE))
        if self.cfg.get('helper_blocker'):
            self.register(owner,104,Spec084('metadata',self.b.root+'\\synthetic.bin',READ,1,3))
        if self.cfg.get('factory_interrupt'):raise KeyboardInterrupt('private-factory')
        return self,101
    def metadata(self,root=False):
        path=self.b.root if root else self.b.root+'\\synthetic.bin'
        parents=tuple(Ancestor084(str(p),0x10,self.b.root_identity if str(p)==self.b.root else (1,2,3))
            for p in PureWindowsPath(path).parents)
        return Metadata084(self.b.root_identity if root else self.b.file_identity,path,0x10 if root else 0,
            1,0 if root else 84,-1,self.security,parents)
    def inspect(self,h):
        self.inspections+=1
        require(h in self.live)
        pipe=Pipe086(self.b.pipe,self.security,self.b.peer)
        root,file=self.metadata(True),self.metadata()
        p=Composite086(Guard083(),pipe,root,root,file,file)
        if self.inspections==self.cfg.get('change_at',2):
            if 'pipe_change' in self.cfg:p=replace(p,pipe=replace(pipe,**self.cfg['pipe_change']))
            if 'file_change' in self.cfg:p=replace(p,file_path=replace(file,**self.cfg['file_change']))
            if 'root_change' in self.cfg:p=replace(p,root_path=replace(root,**self.cfg['root_change']))
            if 'composite_account' in self.cfg:p=replace(p,account=replace(Guard083(),**self.cfg['composite_account']))
        return p
    def write(self,h,raw):
        self.writes.append(raw);self.c.advance(self.cfg.get('write_ms',1))
        _,_,_,_,_,seq,k,issued,deadline,_,_=WIRE.unpack(raw)
        kind={1:'ready',2:'release',3:'holding',4:'closed'}[k]
        decode086(raw,kind,seq,self.b,self.c.boot,deadline,request=True)
        self.request=(kind,seq,deadline)
        if kind=='release':
            self.c.advance(self.cfg.get('launch_ms',5));self.hold_start=self.c.boot
        if self.cfg.get('write_interrupt'):raise KeyboardInterrupt('private-write')
        return Write086(**self.cfg.get('write_result',dict(succeeded=True,error=0,count=144)))
    def read(self,h,count):
        self.reads+=1
        if self.reads<=self.cfg.get('no_data',0):return Read086(False,232,0,b'')
        kind,seq,deadline=self.request
        if kind=='closed' and self.c.boot>=self.hold_start+30000:self.hold_end=self.hold_start+30000
        reply='pending' if kind=='closed' and not self.hold_end else kind
        start=self.hold_start if reply in ('holding','closed') else 0
        end=self.hold_end if reply=='closed' else 0
        raw=encode086(reply,seq,self.b,self.c.boot-self.cfg.get('stale_ms',0),deadline,start,end)
        if 'tamper' in self.cfg:
            v=bytearray(raw);v[self.cfg['tamper']]^=1;raw=bytes(v)
        self.c.advance(self.cfg.get('read_ms',1))
        return replace(Read086(True,0,len(raw),raw,count),**self.cfg.get('read_change',{}))
    def wait(self,ms):self.waits.append(ms);self.c.advance(ms+self.cfg.get('wait_extra',0))
    def close(self,h):
        self.closed.append(h);self.live.pop(h)
        if self.cfg.get('close_interrupt'):raise KeyboardInterrupt('private-close')
        return not self.cfg.get('close_uncertain',False)
    def finish(self):self.finishes+=1;return not self.cfg.get('finish_fail',False)
    def path_metadata(self):return self.metadata()
    def open_control(self,spec,owner):
        if self.hold_start and not self.hold_end:
            return None,self.cfg.get('control_error',32)
        h=200+len(self.writes)+len(self.closed);self.register(owner,h,spec);return h,0
    def control_metadata(self,h):return self.metadata()


def fixture086(**cfg):
    b,c=bindings086(),Clock086();p=BackendModel086(b,c,cfg);state={'guards':0,'factories':0}
    def guard():
        state['guards']+=1;c.advance(cfg.get('guard_ms',0))
        if state['guards']==cfg.get('bad_guard_at',-1):return replace(Guard083(),**cfg.get('bad_guard',{'same_account':False}))
        return Guard083()
    def factory(owner,b):state['factories']+=1;return p.setup(owner)
    return Transport086(b,c,guard,factory),p,c,state


def transport_case086(**cfg):
    t,p,c,state=fixture086(**cfg);ok=False;failure=None;fingerprint=None;age=None
    try:
        if t.start(cfg.get('enabled',True)):
            lease=t.transaction('ready',c.boot+60000);raw=lease.snapshot()
            fingerprint=__import__('hashlib').sha256(raw).hexdigest();age=c.boot-lease.frame.issued
            lease.close();ok=True
    except (Exception,KeyboardInterrupt) as e:
        failure='episode_deadline' if isinstance(e,ProbeRejected) and str(e)=='sync086_episode_clock_rejected' else 'rejected'
    finally:
        if t.m is not None and t.counts['cleanup']==0:ok=t.finish() and ok
    return dict(modeled_completed=ok,first_failure=failure,summary=t.summary(),
        original_message_sha256=fingerprint,message_age_after_guard_ms=age,
        full_guards=state['guards'],valid_guard_spans=len(t.trace),private_inspections=p.inspections,
        message_writes=len(p.writes),read_attempts=p.reads,poll_waits=len(p.waits),
        handles_remaining=len(p.live),backend_finish_calls=p.finishes,
        modeled_elapsed_ms=c.elapsed,episode_scope='isolated_ready_transaction',
        guard_spans=[dict(start=a-100000,end=z-100000) for a,z in t.trace])


def autonomous_case086(guard_ms=0,late_ms=0,uncertain=False):
    c=Clock086();state={'guards':0,'closes':0}
    def guard():state['guards']+=1;c.advance(guard_ms);return Guard083()
    def close():state['closes']+=1;return not uncertain
    gate=AutonomousClose086(c,guard,close);start=c.boot
    gate.start(True,start-5,start)
    c.advance(30000+late_ms);gate.tick()
    return dict(modeled_completed=gate.valid,close_spent=gate.spent,close_confirmed=gate.confirmed,
        close_calls=state['closes'],full_guards=state['guards'],hold_elapsed_at_close_ms=gate.end-start if gate.end else None,
        peer_requests=0,close_depends_on_peer=False,native_protocol_implemented=False,latency_guaranteed=False,
        sdk_connections=0,market_reads=0,orders=0,receipt_permissions=0,runtime_authorized=False)


def record086(reason=17,seq=0,start=0,end=0):
    return dict(version='synchronization_reader_086_v1',phase=PHASE,reason=reason,
        requests=seq,responses=max(0,seq-1),opens=2 if reason==0 else 0,reads=1 if reason==0 else 0,
        closes=2 if reason==0 else 0,hold_start=start,hold_end=end,quote_reads=0,history_reads=0,orders=0,receipt_permissions=0)


def run086_case(**cfg):
    t,p,c,state=fixture086(**cfg);ok=False;failure=None;matched=None
    try:
        if t.start(cfg.get('enabled',True)):
            for access in ('write','delete'):t.control('pre',access)
            t.wait_until(c.boot+300);deadline=c.boot+60000
            t.transaction('ready',deadline).close();t.transaction('release',deadline)
            t.transaction('holding',deadline).close();t.wait_until(t.hold_start+251)
            for access in ('write','delete'):t.control('independent',access)
            t.wait_until(t.hold_start+30251);t.transaction('closed',deadline).close()
            t.wait_until(t.hold_end+251)
            for access in ('write','delete'):t.control('post',access)
            ok=True
    except (Exception,KeyboardInterrupt) as e:
        failure='episode_deadline' if isinstance(e,ProbeRejected) and str(e)=='sync086_episode_clock_rejected' else 'rejected'
    finally:
        if t.m is not None and t.counts['cleanup']==0:ok=t.finish() and ok
    if ok:
        try:matched=match086(record086(),record086(0,t.sequence,t.hold_start,t.hold_end),t)
        except Exception:ok=False;failure='match_rejected'
    return dict(modeled_completed=ok,first_failure=failure,summary=t.summary(),model_match=matched,
        controls=t.probes,frame_kinds=[f.kind for f in t.frames],full_guards=state['guards'],
        valid_guard_spans=len(t.trace),modeled_elapsed_ms=c.elapsed,remaining_handles=len(p.live),
        backend_finish_calls=p.finishes,scope='full_six_control_injected_episode')


class Sync086Tests(unittest.TestCase):
    def rejects(self,**cfg):
        r=transport_case086(**cfg);self.assertFalse(r['modeled_completed'])
        self.assertEqual(r['handles_remaining'],0);self.assertEqual(r['backend_finish_calls'],1)
        return r
    def test_default_off_no_dependencies(self):
        t,p,c,s=fixture086();self.assertFalse(t.start())
        self.assertEqual((c.calls,s['guards'],s['factories'],len(p.live)),(0,0,0,0))
    def test_complete_ready_has_four_guards_no_response_file(self):
        r=transport_case086();self.assertTrue(r['modeled_completed']);self.assertEqual(r['full_guards'],4)
        self.assertEqual(r['private_inspections'],3);self.assertEqual(r['summary']['response_files_created'],0)
        self.assertEqual(r['message_writes'],1);self.assertEqual(r['summary']['physical_close_attempts'],3)
    def test_1611_ms_isolated_ready_original_fresh_after_guard(self):
        r=transport_case086(guard_ms=1611);self.assertTrue(r['modeled_completed'])
        self.assertEqual(r['message_age_after_guard_ms'],1612);self.assertEqual(r['modeled_elapsed_ms'],6446)
    def test_slow_trailing_guard_rejects_freshness(self):self.rejects(guard_ms=2000)
    def test_all_account_facts_exact_and_initial_real_contest_reject(self):
        for change in ({'actual_account_type':1},{'actual_account_type':2},{'actual_account_type':False},
            {'algo_allowed':True},{'currency':'EUR'},{'connected':False},{'uncached_images_sdk_sources':False}):
            t,p,c,s=fixture086(bad_guard_at=1,bad_guard=change)
            with self.assertRaises(Exception):t.start(True)
            self.assertEqual(s['factories'],0);self.assertFalse(p.live)
    def test_account_changes_in_trailing_full_guard(self):self.rejects(bad_guard_at=4)
    def test_raw_composite_account_must_also_be_valid(self):self.rejects(composite_account={'same_owned_sdk':False})
    def test_factory_interrupt_owned_before_io_cleanup_once(self):self.rejects(factory_interrupt=True)
    def test_response_pipe_peer_creation_cannot_change(self):
        self.rejects(pipe_change={'client':replace(bindings086().peer,created=1)})
    def test_pipe_mode_flags_remote_firstinstance_and_types_exact(self):
        for k,v in (('pipe_type',0),('read_mode',0),('wait_mode',0),('maximum_instances',2),
            ('creation_flags',0),('pipe_mode_flags',7),('wait_mode',True),('name','remote-pipe')):
            self.rejects(pipe_change={k:v})
    def test_private_acl_owner_and_extra_ace_reject(self):
        b=bindings086();sec=Security084(b.owner_sid,0x1004,(Ace084(0,0,0x1f01ff,b.owner_sid),))
        for changed in (replace(sec,owner=b'other-user'),replace(sec,control=0),replace(sec,aces=sec.aces*2)):
            self.rejects(pipe_change={'security':changed})
    def test_path_descriptor_replacement_and_reparse_reject(self):
        for change in ({'identity':(8,20,10)},{'attributes':0x400},{'links':2},{'links':True},
            {'final_path':'C:\\different'},{'position':0},{'size':85}):self.rejects(file_change=change)
        self.rejects(root_change={'identity':(4,20,6)})
    def test_reparse_ancestor_and_replaced_root_ancestor_reject(self):
        t,p,c,s=fixture086();m=p.metadata()
        for a in (replace(m.ancestors[0],attributes=0x410),replace(m.ancestors[0],identity=(4,8,6))):
            self.rejects(file_change={'ancestors':(a,)+m.ancestors[1:]})
    def test_helper_share_blocker_rejected(self):self.rejects(helper_blocker=True)
    def test_no_data_polls_do_not_resend_request(self):
        r=transport_case086(no_data=3);self.assertTrue(r['modeled_completed'])
        self.assertEqual((r['message_writes'],r['read_attempts'],r['poll_waits']),(1,4,3))
    def test_no_data_exhaustion_is_finite(self):
        r=self.rejects(no_data=1000)
        self.assertEqual((r['message_writes'],r['read_attempts'],r['poll_waits']),(1,16,15))
    def test_backpressure_zero_write_and_partial_write_never_resend(self):
        for count in (0,143,145,True):
            r=self.rejects(write_result=dict(succeeded=True,error=0,count=count))
            self.assertEqual(r['message_writes'],1);self.assertEqual(r['read_attempts'],0)
    def test_read_partial_oversize_moredata_bytearray_and_wrong_error_reject(self):
        for change in ({'count':143},{'count':145},{'error':234},{'succeeded':False,'error':234},
            {'raw':bytearray(144)},{'buffer_bytes':144},{'count':True},
            {'succeeded':False,'error':5,'count':0,'raw':b''}):self.rejects(read_change=change)
    def test_message_received_before_request_completion_rejects(self):self.rejects(stale_ms=1)
    def test_bindings_magic_sequence_and_padding_tamper_reject(self):
        for offset in (0,8,24,56,88,104,108,109):self.rejects(tamper=offset)
    def test_lease_held_across_trailing_guard_physical_pipe_until_finish(self):
        t,p,c,s=fixture086();t.start(True);l=t.transaction('ready',c.boot+60000)
        raw=l.raw;self.assertEqual(l.snapshot(),raw);self.assertIn(t.pipe_handle,t.owner.live)
        l.close();self.assertIn(t.pipe_handle,t.owner.live);self.assertEqual(len(p.closed),0)
        with self.assertRaises(Exception):l.snapshot()
        self.assertTrue(t.finish());self.assertEqual(len(p.closed),3)
    def test_lease_blocks_next_transaction(self):
        t,p,c,s=fixture086();t.start(True);l=t.transaction('ready',c.boot+60000)
        with self.assertRaises(Exception):t.transaction('release',t.deadline)
        self.assertEqual(len(p.writes),1);self.assertTrue(t.finish());self.assertTrue(l.closed)
    def test_expired_lease_latches_failure_and_cannot_resume(self):
        t,p,c,s=fixture086();t.start(True);l=t.transaction('ready',c.boot+60000);c.advance(2001)
        with self.assertRaises(Exception):l.snapshot()
        l.close();self.assertTrue(t.stopped)
        with self.assertRaises(Exception):t.transaction('release',t.deadline)
        self.assertEqual(len(p.writes),1);t.finish()
    def test_release_spent_before_failed_write_no_retry(self):
        t,p,c,s=fixture086();t.start(True);t.transaction('ready',c.boot+60000).close()
        p.cfg['write_result']=dict(succeeded=True,error=0,count=0)
        with self.assertRaises(Exception):t.transaction('release',t.deadline)
        self.assertTrue(t.release_spent)
        with self.assertRaises(Exception):t.transaction('release',t.deadline)
        self.assertEqual(len(p.writes),2);t.finish()
    def test_ready_release_holding_closed_states_and_same_hold(self):
        t,p,c,s=fixture086();t.start(True);d=c.boot+60000;t.transaction('ready',d).close()
        t.transaction('release',d);l=t.transaction('holding',d)
        start=l.frame.hold_start;l.close();c.advance(30251);l=t.transaction('closed',d)
        self.assertEqual(l.frame.hold_start,start);self.assertEqual(l.frame.hold_end-start,30000)
        l.close();self.assertEqual(t.expected,'done');self.assertTrue(t.finish())
    def test_pending_close_keeps_state_and_requires_fresh_new_challenge(self):
        t,p,c,s=fixture086();t.start(True);d=c.boot+60000;t.transaction('ready',d).close()
        t.transaction('release',d);t.transaction('holding',d).close();l=t.transaction('closed',d)
        self.assertEqual(l.frame.kind,5);self.assertEqual(t.expected,'closed');l.close()
        c.advance(30251);l=t.transaction('closed',d);self.assertEqual(l.frame.sequence,5);l.close();t.finish()
    def test_failed_close_not_retried_and_all_handles_attempted(self):
        for cfg in ({'close_uncertain':True},{'close_interrupt':True},{'finish_fail':True}):
            r=self.rejects(**cfg);self.assertEqual(r['summary']['physical_close_attempts'],3)
    def test_clock_overrun_and_date_expiry_still_owned_cleanup(self):
        self.rejects(read_ms=120000);self.rejects(no_data=1,wait_extra=86400000)
    def test_episode_expiry_does_not_extend_sixty_seconds(self):
        self.rejects(read_ms=60000)
    def test_guard_budget_is_finite_and_cleanup_unconditional(self):
        t,p,c,s=fixture086();t.start(True);t.counts['guards']=CAPS['guards']
        with self.assertRaises(Exception):t.transaction('ready',c.boot+60000)
        self.assertEqual(len(p.writes),0);self.assertTrue(t.finish());self.assertFalse(p.live)
    def test_bound_ancestor_change_rejects_even_without_reparse(self):
        t,p,c,s=fixture086();m=p.metadata();a=replace(m.ancestors[-1],identity=(1,99,3))
        self.rejects(file_change={'ancestors':m.ancestors[:-1]+(a,)})
    def test_budget_and_same_instance_are_one_use(self):
        t,p,c,s=fixture086();t.start(True)
        with self.assertRaises(Exception):t.start(True)
        t.counts['reads']=CAPS['reads']
        with self.assertRaises(Exception):t.transaction('ready',c.boot+60000)
        self.assertTrue(t.finish())
        with self.assertRaises(Exception):t.finish()
    def test_private_reprs_and_summaries_redacted(self):
        t,p,c,s=fixture086();t.start(True);t.transaction('ready',c.boot+60000).close();t.finish()
        text=json.dumps(t.summary())+repr(t.b)+repr(t.b.peer)
        for private in ('500123987','700789321','private-user','private-episode','C:\\lab'):self.assertNotIn(private,text)
    def test_close_policy_every_boundary_and_type_rejects(self):
        release,start=99995,100000
        self.assertEqual([close_action086(start+n,release,start) for n in (0,29999,30000,31000,31001)], [0,0,1,1,2])
        for args in ((True,release,start),(start,0,start),(start,release,start+1),(start,release,start+10001)):
            self.assertEqual(close_action086(*args),3)
    def test_autonomous_no_peer_closes_at_thirty_seconds(self):
        r=autonomous_case086();self.assertTrue(r['modeled_completed']);self.assertEqual(r['peer_requests'],0)
        self.assertEqual((r['close_calls'],r['hold_elapsed_at_close_ms']),(1,30000))
    def test_autonomous_slow_guard_and_scheduler_late_close_invalid(self):
        for cfg in ({'guard_ms':1611},{'late_ms':1001}):
            r=autonomous_case086(**cfg);self.assertFalse(r['modeled_completed']);self.assertTrue(r['close_spent'])
            self.assertEqual(r['close_calls'],1)
    def test_autonomous_uncertain_close_spent_without_retry(self):
        r=autonomous_case086(uncertain=True);self.assertFalse(r['modeled_completed']);self.assertEqual(r['close_calls'],1)
    def test_autonomous_default_off_no_clock_guard_or_close(self):
        c=Clock086()
        def forbidden():raise AssertionError()
        g=AutonomousClose086(c,forbidden,forbidden);self.assertFalse(g.start());self.assertEqual(c.calls,0)
    def test_autonomous_account_rejection_and_expiry_close_once(self):
        for expired in (False,True):
            c=Clock086();closes=[];g=AutonomousClose086(c,lambda:replace(Guard083(),actual_account_type=2),lambda:closes.append(1))
            g.start(True,c.boot-5,c.boot);c.advance(86400000 if expired else 30000)
            self.assertTrue(g.tick());self.assertFalse(g.valid);self.assertEqual(len(closes),1)
            with self.assertRaises(Exception):g.tick()
    def test_pure_mql_close_policy_portable_parity(self):
        vectors=[(100000+n,99995,100000) for n in (0,29999,30000,31000,31001)]
        vectors += [(99999,99995,100000),(100000,0,100000),(100000,1,100000),
            (-1,1,1),(9007199254740992,1,1),(100000,99996,100000)]
        source='#include <iostream>\n#include "'+str(ROOT/'mt5/Scripts/Synchronization085.mqh')+'"\nint main(){\n'
        for args in vectors:source+='std::cout<<CloseAction085('+','.join(str(x)+'LL' for x in args)+')<<"\\n";\n'
        source+='}\n'
        with TemporaryDirectory() as d:
            p=Path(d);(p/'policy.cpp').write_text(source)
            subprocess.run(['g++','-std=c++17',str(p/'policy.cpp'),'-o',str(p/'policy')],capture_output=True,check=True)
            result=subprocess.run([str(p/'policy')],capture_output=True,check=True,text=True)
        self.assertEqual(list(map(int,result.stdout.splitlines())),[close_action086(*args) for args in vectors])
        self.assertEqual(len(vectors),11)
    def test_source_contract_explicit_grouping_no_native_mql_admission(self):
        r=source_contract086(ROOT);self.assertEqual(r['full_guard_group'],'one_bounded_pipe_transaction')
        self.assertIn('src/forex_demo_lab/synchronization_086.py',r['input_bindings'])
        self.assertTrue(r['new_mql_entrypoint_prepared']);self.assertFalse(r['native_runtime_authorized'])
        self.assertEqual((r['freshness_ms'],r['close_max_ms'],r['whole_limit_ms']),(2000,31000,120000))
    def test_complete_six_controls_match_original_frame_sequence(self):
        r=run086_case();self.assertTrue(r['modeled_completed'],r)
        self.assertEqual([x['error'] for x in r['controls']],[0,0,32,32,0,0])
        self.assertEqual(r['frame_kinds'],[1,2,3,4]);self.assertEqual(r['summary']['physical_close_attempts'],7)
    def test_slow_full_episode_guards_reject_without_extension(self):
        r=run086_case(guard_ms=1611);self.assertFalse(r['modeled_completed']);self.assertEqual(r['remaining_handles'],0)
        self.assertGreaterEqual(r['summary']['episode_elapsed_ms'],60000)
        self.assertEqual(r['first_failure'],'episode_deadline')
    def test_control_error_access_denied_does_not_prove_sharing(self):
        for error in (5,6,0,2):self.assertFalse(run086_case(control_error=error)['modeled_completed'])
    def test_native_entry_unavailable_before_any_dll_load(self):
        from forex_demo_lab.windows_adapter_086 import native_entry086
        with self.assertRaises(ProbeRejected):native_entry086()
    def test_reader_source_nonwaiting_close_before_read_and_no_pipe_fileopen(self):
        s=(ROOT/MQL_INPUTS[0]).read_text()
        self.assertIn('pipe=kernel32::CreateFileW',s);self.assertNotIn('pipe=FileOpen',s)
        self.assertLess(s.index('CloseAction085(now'),s.index('r.reason=Receive086(pipe'))
        self.assertNotIn('FileFlush',s);self.assertNotIn('FileSeek',s)
        self.assertIn('kernel32::GetLastError()',s);self.assertIn('::GetLastError()',s)
        self.assertLess(s.index('if(!ReadSyntheticEvidence086)'),s.index('p.first_boot=GetTickCount64()'))
    def test_exact_redacted_record_and_duplicates_reject(self):
        d=record086();self.assertEqual(parse086(PREFIX+json.dumps(d)),d)
        for changed in ({'orders':1},{'requests':True},{'phase':'changed'},{'extra':0}):
            with self.assertRaises(ProbeRejected):parse086(PREFIX+json.dumps({**d,**changed}))
        with self.assertRaises(ProbeRejected):parse086(PREFIX+json.dumps(d)[:-1]+',"orders":0}')
    def test_fresh_protocol_does_not_accept_old_phase_bytes(self):
        from test_synchronization_085 import bindings085
        from forex_demo_lab.synchronization_085 import encode085
        with self.assertRaises(ProbeRejected):decode086(encode085('ready',1,bindings085(),100100,160000),
            'ready',1,bindings086(),100100,160000)
    def test_ported_actual_reader_absent_peer_backpressure_real_and_disabled(self):
        import re
        prelude=(ROOT/'tests/fixtures/reader_086.cpp').read_text();source=(ROOT/MQL_INPUTS[0]).read_text()
        source=re.sub(r'^#property.*\n','',source,flags=re.M).replace('input ','')
        source=source.replace('#include "WindowsPipe086.mqh"','')
        source=re.sub(r'uchar &(\w+)\[\]',r'uchar *\1',source)
        for header in ('ClockGuard042.mqh','SynchronizationWire084.mqh','Synchronization085.mqh'):
            source=source.replace('"'+header+'"','"'+str(ROOT/'mt5/Scripts'/header)+'"')
        port=prelude.replace('// FXDL086_INSERT',source)
        with TemporaryDirectory() as d:
            p=Path(d);(p/'reader.cpp').write_text(port)
            subprocess.run(['g++','-std=c++17',str(p/'reader.cpp'),'-o',str(p/'reader')],capture_output=True,check=True)
            rows=[]
            for config in range(6):
                lines=subprocess.run([str(p/'reader'),str(config)],capture_output=True,check=True,text=True).stdout.splitlines()
                rows.append((list(map(int,lines[0].split())),list(map(int,lines[1].split()[1:]))))
        self.assertEqual(rows[0][0][:6],[0,4,3,2,1,2])
        self.assertEqual(rows[0][1][2:4],[1,1])
        self.assertEqual(rows[1][0][0],21);self.assertEqual(rows[1][1][2:4],[1,1])
        self.assertTrue(30000<=rows[1][1][5]-rows[1][1][4]<=31000)
        self.assertEqual(rows[2][0][0],24);self.assertEqual(rows[2][0][1:3],[1,1])
        self.assertEqual(rows[3][0][0],4);self.assertEqual(rows[3][1][0],0)
        self.assertEqual(rows[4][0][0],25);self.assertEqual(rows[4][1][2],1)
        self.assertEqual(rows[5][0][0],17);self.assertEqual(rows[5][1][:2],[0,0])


if __name__=='__main__':unittest.main()
