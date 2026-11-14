"""Injected synchronization proposal. No native SDK, MQL launch or order API.

The transport/file/private proofs below are model capabilities, never evidence
of Windows ACLs, native boundaries or a compiled MQL implementation. The old072
reader cannot consume this protocol. Separate source/build/runtime work follows.
"""
from dataclasses import dataclass, field, fields
from datetime import datetime, timezone
import hashlib
import os
from pathlib import Path
import struct

from .sharing_adapter_076 import encoded076, exact076
from .sharing_probe_062 import ProbeRejected

PHASE='83000000000000000000000000000001'
DATE='2026-10-08'
SOURCE_INPUTS=('src/forex_demo_lab/synchronization_083.py',
               'mt5/Scripts/Synchronization083.mqh')
KINDS={'ready':1,'release':2,'holding':3,'closed':4}
WIRE=struct.Struct('<8s16s32s32s16sIB3xQQQQ')
MAX_BOOT=9007199254740991
LIMITS=dict(guards=96,operations=96,polls=64,waits=64,lease_closes=64,
            clock_samples=4096,cleanup_attempts=1,reservation_writes=1)
OUTER_MS=120000
EPISODE_MS=60000


def require(ok):
    if not ok:raise ValueError()


def integer(v,lo=0,hi=MAX_BOOT):
    require(type(v) is int and lo<=v<=hi);return v


def digest(v):
    require(type(v) is str and len(v)==64 and all(c in '0123456789abcdef' for c in v));return v


def same_record(value,expected):
    return type(value) is type(expected) and all(exact076(getattr(value,f.name),getattr(expected,f.name))
        for f in fields(expected))


def source_contract083(bindings):
    try:
        require(type(bindings) is dict and set(bindings)==set(SOURCE_INPUTS))
        for h in bindings.values():digest(h)
        return dict(version='synchronization_source_proposal_083_v1',phase=PHASE,date=DATE,
            input_bindings=dict(bindings),wire_bytes=WIRE.size,compiled=False,
            native_protocol_implemented=False,execution_authorized=False,orders_available=False)
    except Exception:raise ProbeRejected('sync_source_rejected') from None


@dataclass(frozen=True)
class Bindings083:
    source_sha256:str
    retained_build_reference_sha256:str
    helper_profile_sha256:str
    policy_sha256:str
    file_identity:tuple=field(repr=False)
    signal_identity:tuple=field(repr=False)
    def __post_init__(self):
        try:
            for k in ('source_sha256','retained_build_reference_sha256','helper_profile_sha256','policy_sha256'):
                digest(getattr(self,k))
            for ident in (self.file_identity,self.signal_identity):
                require(type(ident) is tuple and len(ident)==3)
                for x in ident:integer(x)
                require(ident[0]>0 and ident[1: ]!=(0,0))
        except Exception:raise ProbeRejected('sync_bindings_rejected') from None


def window_reason083(kind,issued,deadline,hold_start,hold_end,now,expected_deadline,release):
    try:
        for v in (kind,issued,deadline,hold_start,hold_end,now,expected_deadline,release):integer(v)
        require(kind in KINDS.values())
    except Exception:return 1
    if issued>now or now-issued>2000:return 2
    if deadline!=expected_deadline or issued>=deadline or now>=deadline:return 3
    if kind in (1,2):return 0 if hold_start==hold_end==0 else 4
    if not 0<release<=hold_start<=release+10000 or hold_start>issued:return 4
    if kind==3:return 0 if hold_end==0 and now<hold_start+29750 else 5
    return 0 if hold_start+30000<=hold_end<=hold_start+31000 and hold_end<=issued else 6


def control_reason083(start,end,guard_end,hold_start):
    try:
        for v in (start,end,guard_end,hold_start):integer(v)
    except Exception:return 1
    return 0 if 0<hold_start and hold_start+250<start<=end<=guard_end<hold_start+29750 else 5


def encode_signal083(kind,seq,b,episode,issued,deadline,hold_start=0,hold_end=0):
    require(type(b) is Bindings083 and type(episode) is bytes and len(episode)==16 and any(episode))
    integer(seq,1,64);integer(issued);integer(deadline,1)
    integer(hold_start);integer(hold_end);require(kind in KINDS)
    return WIRE.pack(b'FXDL083S',bytes.fromhex(PHASE),bytes.fromhex(b.source_sha256),
        bytes.fromhex(b.retained_build_reference_sha256),episode,seq,KINDS[kind],
        issued,deadline,hold_start,hold_end)


def decode_signal083(raw,kind,seq,b,episode,now,deadline,release):
    try:
        require(type(b) is Bindings083 and type(episode) is bytes and len(episode)==16 and any(episode))
        integer(seq,1,64);integer(now);integer(deadline,1);integer(release)
        require(type(raw) is bytes and len(raw)==144 and raw[109:112]==b'\0'*3)
        magic,phase,source,build,ep,s,k,issued,expiry,start,end=WIRE.unpack(raw)
        require((magic,phase,source,build,ep,s,k)==(b'FXDL083S',bytes.fromhex(PHASE),
            bytes.fromhex(b.source_sha256),bytes.fromhex(b.retained_build_reference_sha256),
            episode,seq,KINDS[kind]))
        require(window_reason083(k,issued,expiry,start,end,now,deadline,release)==0)
        return dict(issued=issued,deadline=expiry,hold_start=start,hold_end=end)
    except Exception:raise ProbeRejected('sync_signal_rejected') from None


@dataclass(frozen=True)
class Guard083:
    actual_account_type:int=0
    connected:bool=True
    algo_allowed:bool=False
    currency:str='USD'
    same_account:bool=True
    same_process_creation_logon_boot:bool=True
    uncached_images_sdk_sources:bool=True
    same_owned_sdk:bool=True
    supported_eurusd_metadata:bool=True
    terminal_build:int=6244
    terminal_paths_stable:bool=True
    helper_chain_bound:bool=True
    sdk_version:str='5.0.6231'


@dataclass(frozen=True)
class Private083:
    file_identity:tuple=field(repr=False)
    signal_identity:tuple=field(repr=False)
    private_owner:bool=True
    no_reparse_single_link:bool=True
    metadata_shares_all:bool=True
    same_file:bool=True
    companion_blockers:int=0
    regular_file:bool=True
    synthetic_size:int=84
    metadata_position:int=-1
    synthetic_pattern_verified:bool=True


@dataclass(frozen=True)
class Reply083:
    stage:str
    operation:str
    proof:Private083=field(repr=False)
    error:int=0
    opened:bool=False
    closed:bool=False


@dataclass(frozen=True)
class Snapshot083:
    status:str
    raw:bytes=field(repr=False)
    proof:Private083=field(repr=False)
    boundary:bool=True
    handle_held:bool=True
    write_delete_excluded:bool=True


@dataclass(frozen=True)
class Cleanup083:
    all_handles_closed:bool=True
    allocations_released:bool=True
    unconfirmed_handles:int=0


class Meter083:
    def __init__(self,clock):
        self.clock=clock;self.counts=dict.fromkeys(LIMITS,0);self.first=self.last=None
        self.stopped=False;self.check()
    def check(self):
        if self.stopped:raise ProbeRejected('sync_clock_rejected')
        self.counts['clock_samples']+=1
        try:
            require(self.counts['clock_samples']<=LIMITS['clock_samples'])
            v=self.clock();require(type(v) is tuple and len(v)==3)
            for x in v:integer(x,0,2**63-1)
            require(v[2]<=MAX_BOOT and datetime.fromtimestamp(v[0]//1000,timezone.utc).date().isoformat()==DATE)
            if self.first is None:self.first=self.last=v
            require(all(a>=b for a,b in zip(v,self.last)))
            d=tuple(a-b for a,b in zip(v,self.first))
            require(max(d[0],d[2])<OUTER_MS and d[1]<OUTER_MS*1000000)
            require(abs(d[0]-d[1]//1000000)<=1000 and abs(d[2]-d[1]//1000000)<=1000)
            self.last=v;return v
        except Exception:
            self.stopped=True;raise ProbeRejected('sync_clock_rejected') from None
    def consume(self,k):
        self.check()
        if k not in LIMITS or self.counts[k]>=LIMITS[k]:
            self.stopped=True;raise ProbeRejected('sync_budget_rejected')
        self.counts[k]+=1


class Owner083:
    """Own before factory entry; even an interrupted factory can register cleanup."""
    def __init__(self):self.peer=None;self.closed=False
    def adopt(self,peer):
        require(self.peer is None and getattr(peer,'model_only',None) is True)
        self.peer=peer;return peer
    def finish(self):
        require(not self.closed);self.closed=True
        return self.peer.cleanup_model() if self.peer is not None else Cleanup083()


class Model083:
    def __init__(self,path,bindings,episode,clock,guard,factory,wait):
        require(type(bindings) is Bindings083 and type(episode) is bytes and len(episode)==16 and any(episode))
        self.b,self.episode=bindings,episode;self.m=Meter083(clock)
        self.guard,self.factory,self.wait=guard,factory,wait;self.path=Path(path)
        self.owner=Owner083();self.used=False;self.release_spent=False
        self.trace=[];self.failure=None;self.stage='new';self.origin=self.deadline=None
        self.release=self.hold_start=self.hold_end=self.episode_end=None;self.seq=0;self.probes=[]
    def private(self,p):
        require(type(p) is Private083 and same_record(p,Private083(self.b.file_identity,self.b.signal_identity)))
    def full_guard(self,label):
        self.m.consume('guards');start=self.m.check()[2]
        require(same_record(self.guard(),Guard083()))
        end=self.m.check()[2]
        self.trace.append(dict(operation=label+'_guard',elapsed_ms=end-start,
            start_boot_offset_ms=start-self.m.first[2],end_boot_offset_ms=end-self.m.first[2]))
    def call(self,label,fn,validate=lambda v:v):
        self.stage=label;self.full_guard(label+'_before');self.m.consume('operations')
        start=self.m.check()[2];v=fn();end=self.m.check()[2]
        result=validate(v);self.full_guard(label+'_after')
        self.trace.append(dict(operation=label,elapsed_ms=end-start,
            start_boot_offset_ms=start-self.m.first[2],end_boot_offset_ms=end-self.m.first[2]))
        return result,start,end,self.m.check()[2]
    def reserve(self):
        self.m.consume('reservation_writes')
        raw=encoded076(dict(version='sync_model_reservation_083_v1',phase=PHASE,date=DATE,
            source_sha256=self.b.source_sha256,
            retained_build_reference_sha256=self.b.retained_build_reference_sha256,
            policy_sha256=self.b.policy_sha256,helper_profile_sha256=self.b.helper_profile_sha256,
            episode_sha256=hashlib.sha256(self.episode).hexdigest(),
            private_identity_sha256=hashlib.sha256(encoded076((self.b.file_identity,self.b.signal_identity))).hexdigest(),
            maximum_releases=1,limits=dict(LIMITS),execution_authorized=False,orders_available=False))
        with self.path.open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
    def reply(self,r,stage,op,blocked=False):
        require(type(r) is Reply083 and (r.stage,r.operation)==(stage,op));self.private(r.proof)
        expected=Reply083(stage,op,Private083(self.b.file_identity,self.b.signal_identity),
            32 if blocked else 0,op=='open' and not blocked,op=='close')
        require(same_record(r,expected));return r
    def controls(self,stage):
        for access in ('write','delete'):
            self.call(stage+'_metadata_before_'+access,
                lambda:self.owner.peer.operation(stage,'metadata_before',access),
                lambda r:self.reply(r,stage,'metadata_before'))
            _,start,end,after=self.call(stage+'_open_'+access,
                lambda:self.owner.peer.operation(stage,'open',access),
                lambda r:self.reply(r,stage,'open',stage=='independent'))
            if stage=='independent':
                require(control_reason083(start,end,after,self.hold_start)==0)
            else:
                self.call(stage+'_stamp_'+access,lambda:self.owner.peer.operation(stage,'stamp',access),
                    lambda r:self.reply(r,stage,'stamp'))
                self.call(stage+'_close_'+access,lambda:self.owner.peer.operation(stage,'close',access),
                    lambda r:self.reply(r,stage,'close'))
            self.call(stage+'_metadata_after_'+access,
                lambda:self.owner.peer.operation(stage,'metadata_after',access),
                lambda r:self.reply(r,stage,'metadata_after'))
            final=self.m.check()[2]
            if stage=='independent':require(final<self.hold_start+29750)
            if stage=='post':require(start>self.hold_end+250)
            self.probes.append(dict(stage=stage,access=access,error=32 if stage=='independent' else 0,
                start_boot_offset_ms=start-self.m.first[2],end_boot_offset_ms=end-self.m.first[2],
                full_guards_before_after=True,same_file_before_after=True,companion_blockers=0))
    def episode_check(self):
        require(self.m.check()[2]<self.deadline)
    def exchange(self,kind):
        for _ in range(64):
            self.episode_check();self.m.consume('polls');self.seq+=1;integer(self.seq,1,64)
            lease=None;snapshot=None;parsed=None
            try:
                def observe():
                    nonlocal lease
                    lease=self.owner.peer.exchange(kind,self.seq,self.b,self.episode,self.deadline)
                    return lease.snapshot()
                def validate(s):
                    nonlocal snapshot,parsed
                    require(type(s) is Snapshot083);self.private(s.proof)
                    require(type(s.status) is str and s.status in ('pending','boundary'))
                    require(type(s.raw) is bytes and s.handle_held is True and s.write_delete_excluded is True)
                    if s.status=='pending':require(s.raw==b'' and s.boundary is False)
                    else:
                        require(s.boundary is True)
                        parsed=decode_signal083(s.raw,kind,self.seq,self.b,self.episode,
                            self.m.check()[2],self.deadline,self.release or 0)
                    snapshot=s;return s
                self.call(kind+'_read',observe,validate)
                renewed=lease.snapshot()
                require(same_record(renewed,snapshot));self.private(renewed.proof);self.episode_check()
                if parsed is not None:
                    decode_signal083(snapshot.raw,kind,self.seq,self.b,self.episode,
                        self.m.check()[2],self.deadline,self.release or 0)
                    return parsed
            finally:
                if lease is not None:
                    self.m.counts['lease_closes']+=1
                    require(self.m.counts['lease_closes']<=LIMITS['lease_closes'] and lease.close() is True)
            self.m.consume('waits')
            self.call('poll_wait',lambda:self.wait(50),lambda v:require(v is None))
        raise ProbeRejected('sync_poll_exhausted')
    def run(self,enabled=False):
        if type(enabled) is not bool:raise ProbeRejected('sync_default_rejected')
        if self.used:raise ProbeRejected('sync_model_spent')
        self.used=True;completed=False;cleanup=None;cleanup_ok=False
        if not enabled:return self.report(False,None,None)
        try:
            self.stage='reservation';self.reserve()
            def construct():
                p=self.factory(self.owner);require(p is self.owner.peer);return p
            self.call('bootstrap',construct)
            self.controls('pre')
            pre_target=max(p['end_boot_offset_ms'] for p in self.probes)+self.m.first[2]+251
            if self.m.check()[2]<pre_target:
                self.m.consume('waits')
                self.call('pre_margin_wait',lambda:self.wait(max(0,pre_target-self.m.check()[2])),
                    lambda v:require(v is None))
            self.origin=self.m.check()[2];self.deadline=self.origin+EPISODE_MS
            self.exchange('ready')
            self.episode_check();self.release_spent=True # Spend before any release attempt.
            def release():
                self.seq+=1;integer(self.seq,1,64);self.release=self.m.check()[2]
                raw=encode_signal083('release',self.seq,self.b,self.episode,self.release,self.deadline)
                return self.owner.peer.release(raw,self.b,self.episode,self.seq,self.deadline)
            self.call('release_write',release,lambda r:self.reply(r,'signal','release'))
            self.hold_start=self.exchange('holding')['hold_start']
            require(all(p['end_boot_offset_ms']+self.m.first[2]<self.hold_start-250 for p in self.probes))
            if self.m.check()[2]<=self.hold_start+250:
                self.m.consume('waits')
                self.call('start_margin_wait',lambda:self.wait(max(0,self.hold_start+251-self.m.check()[2])),
                    lambda v:require(v is None))
            self.controls('independent');self.episode_check()
            target=self.hold_start+30251
            def wait_closed():
                for _ in range(64):
                    now=self.m.check()[2]
                    if now>=target:return
                    self.m.consume('waits');require(self.wait(min(1000,target-now)) is None)
                    self.episode_check()
                raise ProbeRejected('sync_poll_exhausted')
            # Preserve the old wait's full before/after guards and bounded clock
            # loop; do not add a full guard to every individual sleep chunk.
            self.call('hold_wait',wait_closed,lambda v:require(v is None))
            closed=self.exchange('closed');require(closed['hold_start']==self.hold_start)
            self.hold_end=closed['hold_end'];self.episode_check();self.episode_end=self.m.check()[2]
            self.controls('post');self.full_guard('final');completed=True
        except (Exception,KeyboardInterrupt) as error:
            self.failure=dict(stage=self.stage,code='interrupted' if isinstance(error,KeyboardInterrupt) else 'rejected')
        finally:
            self.m.counts['cleanup_attempts']+=1
            try:
                cleanup=self.owner.finish();cleanup_ok=same_record(cleanup,Cleanup083())
            except (Exception,KeyboardInterrupt):cleanup_ok=False
            if not cleanup_ok and self.failure is None:self.failure=dict(stage='cleanup',code='unconfirmed')
            try:self.m.check()
            except (Exception,KeyboardInterrupt):
                if self.failure is None:self.failure=dict(stage='cleanup',code='clock_rejected')
        return self.report(completed and cleanup_ok and self.failure is None,cleanup,cleanup_ok)
    def report(self,completed,cleanup,cleanup_ok):
        base=self.m.first[2]
        return dict(version='synchronization_model_083_v1',phase=PHASE,date=DATE,
            modeled_completed=completed,dependencies_injected=True,release_spent=self.release_spent,
            first_failure=self.failure,counts=dict(self.m.counts),trace=list(self.trace),probes=list(self.probes),
            cleanup_confirmed=cleanup_ok,outer_elapsed_ms=self.m.last[2]-base,
            episode_origin_offset_ms=self.origin-base if self.origin is not None else None,
            episode_elapsed_ms=self.episode_end-self.origin if self.episode_end is not None else None,
            release_offset_ms=self.release-base if self.release is not None else None,
            hold_start_offset_ms=self.hold_start-base if self.hold_start is not None else None,
            hold_end_offset_ms=self.hold_end-base if self.hold_end is not None else None,
            native_protocol_implemented=False,native_mql_verified=False,native_publication_verified=False,
            native_launch_ready=False,latency_guaranteed=False,runtime_authorized=False,
            sdk_connections=0,market_reads=0,orders=0,receipt_permissions=0,
            fresh_performance_eligible=False,annual_eligible=False,orders_available=False)
