"""Injected OS facts and portable byte-codec comparisons; no native execution."""
from dataclasses import replace
from datetime import datetime, timezone
import json
from pathlib import Path, PureWindowsPath
import subprocess
from tempfile import TemporaryDirectory
import unittest

from forex_demo_lab.synchronization_084 import *

ROOT = Path(__file__).resolve().parents[1]
class Clock084:
    def __init__(self):
        self.utc = int(datetime(2026,10,8,tzinfo=timezone.utc).timestamp()*1000)
        self.boot = 100000; self.ns = 0
    def __call__(self): return self.utc, self.ns, self.boot
    def advance(self, ms): self.utc += ms; self.boot += ms; self.ns += ms*1000000


def bindings084():
    ep = b'private-episode!'
    return Bindings084('a'*64,'b'*64,'c'*64,ep,(500123987,2,3),b'private-user-sid',
        'C:\\lab\\ForexDemoSynchronization084-'+PHASE+'-'+ep.hex(),
        Peer084(700789321,987654321,1,b'private-logon-sid',b'private-boot-id'))


class BackendModel084:
    model_only = True
    def __init__(self, b, c, cfg):
        self.b, self.c, self.cfg = b, c, cfg
        self.files = {}; self.handles = {}; self.h = 0; self.closed = []
        self.finish_calls = 0; self.created = False; self.releases = 0
        self.hold_start = self.hold_end = 0; self.requests = []; self.publications = []
        self.security = Security084(b.owner_sid,0x1004,(Ace084(0,0,0x1f01ff,b.owner_sid),))
    def handle(self, spec, owner):
        self.h += 1; h = self.h; self.handles[h] = [spec,0]
        owner.register(h,spec)
        if self.cfg.get('interrupt_open') == spec.role: raise KeyboardInterrupt('private-exception')
        return h
    def bootstrap(self,b,owner):
        if self.created: raise ValueError('private-root-exists')
        self.created = True
        root = Spec084('root',b.root,META,7,3,NO_REPARSE|0x2000000)
        h = self.handle(root,owner)
        self.files[b.root] = [b'',(4,5,6)]
        self.files[b.root+'\\synthetic.bin'] = [DATA084,b.file_identity]
        parents = tuple(Metadata084((1,2,3),str(p),0x10,1,0,-1,self.security)
            for p in PureWindowsPath(b.root).parents)
        if self.cfg.get('reparse_parent'): parents = (replace(parents[0],attributes=0x410),)+parents[1:]
        return Setup084(h,not self.cfg.get('not_new'),parents,DATA084 if not self.cfg.get('bad_pattern') else b'x'*84)
    def open(self,spec,owner):
        if spec.creation == CREATE_NEW:
            if spec.path in self.files: return Open084(None,80)
            self.files[spec.path] = [b'',(8,100+self.h,9)]
            self.publications.append(spec.path)
        elif spec.path not in self.files: return Open084(None,2)
        if spec.role.startswith('control_') and self.hold_start and not self.hold_end:
            self.c.advance(self.cfg.get('blocked_ms',0))
            return Open084(None,self.cfg.get('control_error',32))
        h = self.handle(spec,owner)
        return Open084(h,0)
    def metadata(self,h):
        spec,pos = self.handles[h]; data,ident = self.files[spec.path]
        ancestors = tuple(Ancestor084(str(p),0x10,(4,5,6) if str(p)==self.b.root else (1,2,3))
            for p in PureWindowsPath(spec.path).parents)
        if self.cfg.get('reparse_after_setup') and spec.role=='signal_reader':
            ancestors=(replace(ancestors[0],attributes=0x410),)+ancestors[1:]
        if self.cfg.get('root_replaced') and spec.role=='signal_reader':
            ancestors=(replace(ancestors[0],identity=(4,555,6)),)+ancestors[1:]
        m = Metadata084(ident,spec.path,0x10 if spec.role=='root' else 0,1,len(data),
            -1 if spec.role in ('root','metadata','control_write','control_delete') else pos,self.security,ancestors)
        if self.cfg.get('bad_metadata_role') == spec.role: m = replace(m,**self.cfg['bad_metadata'])
        return m
    def write(self,h,raw):
        spec,pos = self.handles[h]; self.files[spec.path][0] = raw; self.handles[h][1] = len(raw)
        return self.cfg.get('write_count',len(raw))
    def read(self,h,count):
        spec,pos = self.handles[h]
        if self.cfg.get('replace_signal'): self.files[spec.path][1] = (8,999,9)
        raw = self.files[spec.path][0][:count]; self.handles[h][1] += len(raw)
        if self.cfg.get('short_read'): return raw[:-1]
        return raw
    def close(self,h):
        self.closed.append(h); self.handles.pop(h)
        if self.cfg.get('close_fail'): return False
        return True
    def transfer(self,raw):
        magic,phase,source,artifact,ep,seq,k,issued,deadline,start,end = WIRE.unpack(raw)
        kind = {1:'ready',3:'holding',4:'closed'}[k]
        decode084(raw,kind,seq,self.b,self.c.boot,deadline,request=True)
        self.requests.append(raw); self.c.advance(1); completed = self.c.boot
        if kind=='closed' and self.c.boot>=self.hold_start+30000:
            self.hold_end = self.c.boot
        hs = self.hold_start if kind in ('holding','closed') else 0
        he = self.hold_end if kind=='closed' else 0
        reply_kind = 'pending' if kind=='closed' and not he else kind
        response = encode084(reply_kind,seq,self.b,self.c.boot-self.cfg.get('stale_ms',0),deadline,
            0 if reply_kind=='pending' else hs,he)
        if 'tamper' in self.cfg:
            v=bytearray(response);v[self.cfg['tamper']]^=1;response=bytes(v)
        self.c.advance(1)
        security = replace(self.security,control=0) if self.cfg.get('pipe_acl') else self.security
        peer = replace(self.b.peer,created=self.b.peer.created+1) if self.cfg.get('pipe_pid') else self.b.peer
        transfer = Transfer084(response,completed,self.c.boot,security,peer,4,2,144,145,144,0)
        return replace(transfer,**self.cfg.get('bad_transfer',{}))
    def release(self,raw):
        self.releases += 1
        _,_,_,_,_,seq,_,_,deadline,_,_ = WIRE.unpack(raw)
        decode084(raw,'release',seq,self.b,self.c.boot,deadline,request=True)
        self.c.advance(self.cfg.get('launch_ms',5)); self.hold_start = self.c.boot
        if self.cfg.get('release_fail'): raise ValueError('private-send-failed')
        return 144
    def wait(self,ms): self.c.advance(ms+self.cfg.get('wait_extra',0))
    def finish(self): self.finish_calls += 1; return not self.cfg.get('finish_fail',False)


def fixture084(**cfg):
    b,c = bindings084(),Clock084(); backend = BackendModel084(b,c,cfg)
    state = {'guards':0,'factories':0}
    def guard():
        state['guards'] += 1; c.advance(cfg.get('guard_ms',0))
        if state['guards']==cfg.get('bad_guard_at',-1): return replace(Guard083(),**cfg.get('bad_guard',{'actual_account_type':2}))
        return Guard083()
    def factory(owner):
        state['factories'] += 1; owner.install(backend)
        if cfg.get('factory_interrupt'): raise KeyboardInterrupt('private-factory-error')
        return backend
    return Companion084(b,c,guard,factory),backend,c,state


def record084(reason=17,seq=0,start=0,end=0):
    return dict(version='synchronization_reader_084_v1',phase=PHASE,reason=reason,
        requests=seq,responses=max(0,seq-1),opens=2 if reason==0 else 0,reads=1 if reason==0 else 0,
        closes=2 if reason==0 else 0,hold_start=start,hold_end=end,quote_reads=0,history_reads=0,orders=0,receipt_permissions=0)


def run084_case(**cfg):
    client,backend,clock,state = fixture084(**cfg)
    enabled = cfg.get('enabled',True); completed = False; match = None; failure = None
    try:
        if not client.start(enabled): return client,backend,clock,state,False,None,None
        for access in ('write','delete'): client.control('pre',access)
        client.wait_until(clock.boot+300)
        deadline = clock.boot+60000
        lease = client.exchange('ready',deadline); lease.close()
        client.release()
        lease = client.exchange('holding',deadline); lease.close()
        client.wait_until(client.hold_start+251)
        for access in ('write','delete'): client.control('independent',access)
        client.wait_until(client.hold_start+30251)
        lease = client.exchange('closed',deadline); lease.close()
        client.wait_until(client.hold_end+251)
        for access in ('write','delete'): client.control('post',access)
        completed = True
    except (Exception,KeyboardInterrupt) as e:
        failure = 'interrupted' if isinstance(e,KeyboardInterrupt) else 'rejected'
    finally:
        if enabled and client.counts['cleanup']==0: client.finish()
    if completed:
        try:
            match = match084(record084(),record084(0,client.sequence,client.hold_start,client.hold_end),client)
        except Exception: completed=False; failure='match_rejected'
    return client,backend,clock,state,completed,match,failure


class Sync084Tests(unittest.TestCase):
    def failure(self,**cfg):
        c,b,clock,state,ok,m,f = run084_case(**cfg)
        self.assertFalse(ok);self.assertIsNotNone(f)
        self.assertFalse(b.handles);self.assertEqual(b.finish_calls,1)
        return c,b
    def test_default_off_no_clock_factory_guard_or_files(self):
        c,b,clock,state,ok,m,f=run084_case(enabled=False)
        self.assertEqual(state,dict(guards=0,factories=0));self.assertFalse(b.files)
        self.assertEqual(b.finish_calls,0);self.assertIsNone(c.m)
    def test_full_typed_flow_six_controls_exact_original_bytes(self):
        c,b,clock,state,ok,m,f=run084_case()
        self.assertTrue(ok,f);self.assertTrue(m['modeled_match']);self.assertFalse(b.handles)
        self.assertEqual([p.error for p in c.probes],[0,0,32,32,0,0])
        self.assertEqual(b.releases,1);self.assertEqual(len(b.publications),3)
        self.assertTrue(all(l.raw==b.files[l.spec.path][0] for l in c.leases))
        self.assertEqual(state['guards'],sum(t[0]=='guard' for t in c.trace))
    def test_fifty_ms_guards_concrete_flow_finishes(self):
        c,b,clock,state,ok,m,f=run084_case(guard_ms=50)
        self.assertTrue(ok,f);self.assertLess(clock.boot-c.m.first[2],120000)
        self.assertLess(c.hold_end-c.release_time,60000)
    def test_observed_1611_ms_guards_reject_concrete_publication_freshness(self):
        c,b=self.failure(guard_ms=1611)
        self.assertFalse(c.release_spent);self.assertEqual(b.releases,0)
    def test_real_contest_and_algo_on_reject_before_factory(self):
        for change in ({'actual_account_type':1},{'actual_account_type':2},{'actual_account_type':False},{'algo_allowed':True}):
            c,b,clock,state,ok,m,f=run084_case(bad_guard_at=1,bad_guard=change)
            self.assertFalse(ok);self.assertEqual(state['factories'],0)
    def test_changed_account_or_uncached_graph_rejects(self):
        for change in ({'same_account':False},{'uncached_images_sdk_sources':False},{'same_owned_sdk':False},
                       {'same_process_creation_logon_boot':False},{'terminal_paths_stable':False}):
            self.failure(bad_guard_at=21,bad_guard=change)
    def test_interrupted_factory_owned_before_entry_cleanup_once(self): self.failure(factory_interrupt=True)
    def test_interrupt_after_acquisition_handle_registered_and_closed(self): self.failure(interrupt_open='signal_writer')
    def test_changed_signal_identity_during_read_rejected(self): self.failure(replace_signal=True)
    def test_short_read_and_false_or_short_write_rejected(self):
        self.failure(short_read=True)
        for count in (True,143,145): self.failure(write_count=count)
    def test_create_new_collision_not_overwritten_or_retried(self):
        c,b,clock,state=fixture084();c.start(True)
        path=c.b.root+'\\response-01.bin';b.files[path]=[b'old',(8,9,10)]
        with self.assertRaises(Exception):c.exchange('ready',clock.boot+60000)
        self.assertEqual(b.files[path][0],b'old');self.assertTrue(c.finish())
    def test_same_root_restart_is_rejected(self):
        c,b,clock,state=fixture084();c.start(True);c.finish()
        other=Companion084(c.b,clock,lambda:Guard083(),lambda owner:owner.install(b))
        with self.assertRaises(Exception):other.start(True)
        self.assertEqual(b.finish_calls,2);self.assertFalse(b.handles)
    def test_reparse_ancestor_old_root_and_wrong_synthetic_bytes_rejected(self):
        for cfg in ({'reparse_parent':True},{'not_new':True},{'bad_pattern':True}): self.failure(**cfg)
    def test_reparse_or_directory_replacement_after_setup_rejects(self):
        self.failure(reparse_after_setup=True);self.failure(root_replaced=True)
    def test_owner_acl_links_and_reparse_metadata_reject(self):
        b=bindings084();sec=Security084(b.owner_sid,0x1004,(Ace084(0,0,0x1f01ff,b.owner_sid),))
        changes=({'links':2},{'links':True},{'attributes':0x400},{'attributes':0x10},
            {'final_path':'C:\\wrong'}, {'security':replace(sec,owner=b'changed-user-sid')},
            {'security':replace(sec,control=0)}, {'security':replace(sec,aces=sec.aces*2)},
            {'security':replace(sec,aces=(replace(sec.aces[0],mask=0x1f01fe),))},
            {'security':replace(sec,aces=(replace(sec.aces[0],type=1),))})
        for change in changes: self.failure(bad_metadata_role='signal_reader',bad_metadata=change)
    def test_private_pipe_security_or_client_creation_changed(self):
        self.failure(pipe_acl=True);self.failure(pipe_pid=True)
    def test_pipe_message_mode_exact_counts_and_more_data_reject(self):
        for change in ({'pipe_type':0},{'pipe_read_mode':0},{'request_bytes_written':143},
            {'response_buffer_bytes':144},{'response_bytes_read':145},{'response_error':234},
            {'response_error':False}): self.failure(bad_transfer=change)
    def test_peer_stale_after_request_cannot_be_retimestampped(self):
        self.failure(stale_ms=1);self.failure(stale_ms=2001)
    def test_every_binding_and_padding_tamper_including_zero_rejects(self):
        for offset in (0,8,24,56,88,104,108,109): self.failure(tamper=offset)
    def test_wrong_native_error_does_not_prove_sharing(self):
        for code in (5,6,2,0):self.failure(control_error=code)
    def test_blocked_native_return_after_hold_margin_rejected(self): self.failure(blocked_ms=30000)
    def test_launch_after_ten_seconds_rejected(self): self.failure(launch_ms=10001)
    def test_wait_overshoot_rejected_without_clock_preemption_claim(self): self.failure(wait_extra=120000)
    def test_cleanup_failure_invalidates_match_and_close_never_retried(self):
        c,b=self.failure(close_fail=True);self.assertGreater(c.owner.unconfirmed,0)
        self.assertEqual(len(b.closed),len(set(b.closed)))
        self.failure(finish_fail=True)
    def test_spent_release_even_when_send_fails_no_second_attempt(self):
        c,b=self.failure(release_fail=True);self.assertTrue(c.release_spent)
        with self.assertRaises(Exception):c.release()
        self.assertEqual(b.releases,1)
    def test_owned_cleanup_after_date_expiry(self):
        c,b,clock,state=fixture084();c.start(True);clock.advance(86400000)
        with self.assertRaises(Exception):c.exchange('ready',clock.boot+60000)
        self.assertTrue(c.finish());self.assertFalse(b.handles)
    def test_summary_and_private_reprs_do_not_export_identifiers(self):
        c,b,clock,state,ok,m,f=run084_case()
        text=json.dumps(c.summary())+repr(c.b)+repr(c.b.peer)
        for private in ('500123987','700789321','987654321','private-user','private-episode','C:\\lab'):
            self.assertNotIn(private,text)
        self.assertFalse(c.summary()['runtime_authorized']);self.assertEqual(c.summary()['orders'],0)
    def test_request_and_response_windows_are_distinct(self):
        b=bindings084();raw=encode084('holding',3,b,100100,160000)
        self.assertEqual(decode084(raw,'holding',3,b,100100,160000,100000,request=True).kind,3)
        with self.assertRaises(ProbeRejected):decode084(raw,'holding',3,b,100100,160000,100000)
    def test_pending_closed_is_fresh_and_has_no_fabricated_hold_times(self):
        b=bindings084();raw=encode084('pending',4,b,100100,160000)
        self.assertEqual(decode084(raw,'closed',4,b,100100,160000,100000,100100).kind,5)
        with self.assertRaises(ProbeRejected):decode084(raw,'closed',4,b,100100,160000,100000,request=True)
    def test_truncated_extended_future_wrong_deadline_and_bool_sequence_reject(self):
        b=bindings084();raw=encode084('ready',1,b,100100,160000)
        for value in (raw[:-1],raw+b'x'):
            with self.assertRaises(ProbeRejected):decode084(value,'ready',1,b,100100,160000)
        for seq,now,deadline in ((True,100100,160000),(1,100099,160000),(1,100100,160001)):
            with self.assertRaises(ProbeRejected):decode084(raw,'ready',seq,b,now,deadline)
    def test_record_exact_fields_types_duplicates_and_zero_market_calls(self):
        d=record084();self.assertEqual(parse084(PREFIX+json.dumps(d)),d)
        for change in ({'orders':1},{'requests':True},{'extra':0},{'phase':'changed'}):
            with self.assertRaises(ProbeRejected):parse084(PREFIX+json.dumps({**d,**change}))
        with self.assertRaises(ProbeRejected):parse084(PREFIX+json.dumps(d)[:-1]+',"orders":0}')
    def test_matcher_rejects_forged_success_or_missing_controls(self):
        c,b,clock,state,ok,m,f=run084_case();self.assertTrue(ok)
        good=record084(0,c.sequence,c.hold_start,c.hold_end)
        with self.assertRaises(ProbeRejected):match084(record084(),{**good,'hold_end':good['hold_end']+1},c)
        with self.assertRaises(ProbeRejected):match084(record084(),{**good,'requests':good['requests']+1,'responses':good['responses']+1},c)
        c.probes[2]=replace(c.probes[2],error=5)
        with self.assertRaises(ProbeRejected):match084(record084(),good,c)
    def test_same_instance_budget_and_cleanup_one_use(self):
        c,b,clock,state=fixture084();c.start(True)
        with self.assertRaises(Exception):c.start(True)
        c.counts['exchanges']=CAPS['exchanges']
        with self.assertRaises(Exception):c.exchange('ready',clock.boot+60000)
        self.assertTrue(c.finish())
        with self.assertRaises(Exception):c.finish()
    def test_held_lease_survives_trailing_guard_and_requires_close(self):
        c,b,clock,state=fixture084();c.start(True);deadline=clock.boot+60000
        l=c.exchange('ready',deadline);self.assertEqual(l.snapshot(),l.raw)
        self.assertEqual(c.owner.live[l.h].access,READ);self.assertEqual(c.owner.live[l.h].share,1)
        with self.assertRaises(Exception):c.exchange('holding',deadline)
        self.assertTrue(c.finish())
    def test_source_import_include_graph_exact_no_native_authority(self):
        p=source_contract084(ROOT)
        self.assertTrue(set(MQL_INPUTS)<=set(p['input_bindings']))
        self.assertIn('src/forex_demo_lab/synchronization_083.py',p['input_bindings'])
        self.assertEqual(p['candidate_build_schema']['actual_compiler_exit'],1)
        self.assertFalse(p['compiled']);self.assertFalse(p['execution_authorized'])
        text=(ROOT/MQL_INPUTS[0]).read_text()
        self.assertLess(text.index('if(!ReadSyntheticEvidence084)'),text.index('p.first_boot=GetTickCount64()'))
        for name in ('OrderSend','CTrade','SymbolInfoTick','CopyTicks','CopyRates','#import'):
            self.assertNotIn(name,text)
    def test_python_and_portable_mql_byte_codec_match(self):
        b=bindings084();raw=encode084('ready',1,b,100100,160000);cases=[]
        cases.append((raw,'ready',1,100100,160000,0,100100,False))
        for offset in (0,8,24,56,88,104,108,109):
            v=bytearray(raw);v[offset]^=1;cases.append((bytes(v),'ready',1,100100,160000,0,100100,False))
        for age in (2000,2001):cases.append((raw,'ready',1,100100+age,160000,0,100100,False))
        cases.append((raw,'ready',1,100100,160000,0,100101,False))
        for kind,start,end,req in (('holding',100100,0,False),('closed',100100,130100,False),
            ('holding',0,0,True),('closed',0,0,True)):
            now=130100 if end else 100100
            value=encode084(kind,3,b,now,160000,start,end)
            cases.append((value,kind,3,now,160000,100000,now if not req else -1,req))
        for value in (raw[:-1],raw+b'x'):cases.append((value,'ready',1,100100,160000,0,100100,False))
        source='#include <iostream>\nusing uchar=unsigned char;\n#define FXDL084_CPP\n#include "'+str(ROOT/'mt5/Scripts/SynchronizationWire084.mqh')+'"\nint main(){Wire084 s;\n'
        source+='uchar prefix[104]={'+','.join(map(str,raw[:104]))+'};\n'
        expected=[]
        for i,(value,kind,seq,now,deadline,release,completed,req) in enumerate(cases):
            try:decode084(value,kind,seq,b,now,deadline,release,None if completed<0 else completed,req);expected.append(True)
            except ProbeRejected:expected.append(False)
            source+='uchar r%d[]={%s};std::cout << (DecodeWire084(r%d,%d,prefix,%d,%d,%d,%d,%d,%d,s,%s)==0) << "\\n";\n'%(i,','.join(map(str,value)),i,len(value),KINDS[kind],seq,now,deadline,release,completed,'true' if req else 'false')
        source+='uchar out[144];Wire084 e={1,1,100100,160000,0,0};EncodeWire084(out,prefix,e);for(int i=0;i<144;i++)std::cout << (int)out[i] << " ";}\n'
        with TemporaryDirectory() as d:
            p=Path(d);(p/'codec.cpp').write_text(source)
            subprocess.run(['g++','-std=c++17',str(p/'codec.cpp'),'-o',str(p/'codec')],check=True,capture_output=True)
            lines=subprocess.run([str(p/'codec')],check=True,capture_output=True,text=True).stdout.splitlines()
        self.assertEqual([x=='1' for x in lines[:-1]],expected)
        self.assertEqual(bytes(map(int,lines[-1].split())),raw);self.assertEqual(len(expected),18)
