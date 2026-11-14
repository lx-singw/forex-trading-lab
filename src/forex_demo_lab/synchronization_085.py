"""Offline held-message transport and autonomous-close redesign.

Acquisition of all Windows facts is injected. No native backend, MQL entry
point, account connection, compilation, deployment or trading is provided.
The grouping is the original083/084 pipe transaction guard pair; response-file
publication and its IO/guards are removed because those files no longer exist.
"""
from dataclasses import dataclass, field
import ast
import hashlib
from pathlib import Path, PureWindowsPath

from .synchronization_083 import (WIRE, Guard083, Meter083, integer, digest,
    require, same_record, window_reason083)
from .synchronization_084 import (Peer084, Security084, Metadata084, Ancestor084,
    Spec084, check_security084, READ, WRITE, META, SHARE_ALL, OPEN_EXISTING,
    NO_REPARSE, MQL_INPUTS)
from .sharing_probe_062 import ProbeRejected

PHASE = '85000000000000000000000000000001'
DATE = '2026-10-08'
MAGIC = b'FXDL085S'
KINDS = {'ready': 1, 'release': 2, 'holding': 3, 'closed': 4, 'pending': 5}
CAPS = dict(guards=96, transactions=64, reads=256, writes=64, waits=256,
    cleanup=1, closes=8)
READS_PER_TRANSACTION = 16
POLL_MS = 10
FIRST_INSTANCE = 0x80000
REJECT_REMOTE = 8


@dataclass(frozen=True)
class Bindings085:
    source_sha256: str
    candidate_artifact_sha256: str
    policy_sha256: str
    episode: bytes = field(repr=False)
    owner_sid: bytes = field(repr=False)
    root: str = field(repr=False)
    root_identity: tuple = field(repr=False)
    file_identity: tuple = field(repr=False)
    peer: Peer084 = field(repr=False)
    ancestor_identities: tuple = field(repr=False)

    def __post_init__(self):
        try:
            for v in (self.source_sha256, self.candidate_artifact_sha256, self.policy_sha256): digest(v)
            require(type(self.episode) is bytes and len(self.episode)==16 and any(self.episode))
            require(type(self.owner_sid) is bytes and 8<=len(self.owner_sid)<=256)
            require(type(self.peer) is Peer084)
            for ident in (self.root_identity, self.file_identity): identity085(ident)
            require(self.root_identity != self.file_identity)
            require(type(self.root) is str and len(self.root)<220)
            p=PureWindowsPath(self.root)
            require(p.is_absolute() and len(p.drive)==2 and p.drive[1]==':' and '..' not in p.parts)
            require(str(p)==self.root and p.name=='ForexDemoSynchronization085-'+PHASE+'-'+self.episode.hex())
            require(type(self.ancestor_identities) is tuple and len(self.ancestor_identities)==len(tuple(p.parents))<=16)
            for v in self.ancestor_identities:identity085(v)
        except Exception: raise ProbeRejected('sync085_bindings_rejected') from None

    @property
    def pipe(self): return '\\\\.\\pipe\\ForexDemoSynchronization085-'+PHASE+'-'+self.episode.hex()


def identity085(v):
    require(type(v) is tuple and len(v)==3)
    for x in v: integer(x)
    require(v[0]>0 and v[1:]!=(0,0))


def encode085(kind, seq, b, issued, deadline, start=0, end=0):
    require(type(b) is Bindings085 and kind in KINDS)
    integer(seq,1,64)
    for x in (issued,deadline,start,end): integer(x)
    return WIRE.pack(MAGIC,bytes.fromhex(PHASE),bytes.fromhex(b.source_sha256),
        bytes.fromhex(b.candidate_artifact_sha256),b.episode,seq,KINDS[kind],issued,deadline,start,end)


@dataclass(frozen=True)
class Frame085:
    kind: int
    sequence: int
    issued: int
    deadline: int
    hold_start: int
    hold_end: int
    raw: bytes = field(repr=False)


def decode085(raw,kind,seq,b,now,deadline,release=0,request_completed=None,request=False):
    try:
        require(type(b) is Bindings085 and kind in KINDS and type(request) is bool)
        integer(seq,1,64)
        for x in (now,deadline,release): integer(x)
        require(type(raw) is bytes and len(raw)==144 and raw[109:112]==b'\0'*3)
        magic,phase,source,artifact,ep,s,k,issued,expiry,start,end=WIRE.unpack(raw)
        require((magic,phase,source,artifact,ep,s)==(MAGIC,bytes.fromhex(PHASE),
            bytes.fromhex(b.source_sha256),bytes.fromhex(b.candidate_artifact_sha256),b.episode,seq))
        require(k==KINDS[kind] or not request and k==5 and kind in ('holding','closed'))
        require(not request or k in (1,2,3,4))
        require(window_reason083(1 if request or k==5 else k,issued,expiry,start,end,now,deadline,release)==0)
        if request_completed is not None:
            integer(request_completed);require(request_completed<=issued<=now)
        return Frame085(k,s,issued,expiry,start,end,raw)
    except Exception: raise ProbeRejected('sync085_frame_rejected') from None


@dataclass(frozen=True)
class Pipe085:
    name: str = field(repr=False)
    security: Security084 = field(repr=False)
    client: Peer084 = field(repr=False)
    pipe_type: int = 4
    read_mode: int = 2
    wait_mode: int = 1
    maximum_instances: int = 1
    creation_flags: int = FIRST_INSTANCE
    pipe_mode_flags: int = 4|2|1|REJECT_REMOTE


@dataclass(frozen=True)
class Composite085:
    account: Guard083
    pipe: Pipe085 = field(repr=False)
    root_descriptor: Metadata084 = field(repr=False)
    root_path: Metadata084 = field(repr=False)
    file_descriptor: Metadata084 = field(repr=False)
    file_path: Metadata084 = field(repr=False)


@dataclass(frozen=True)
class Read085:
    succeeded: bool
    error: int
    count: int
    raw: bytes = field(repr=False)
    buffer_bytes: int = 145


@dataclass(frozen=True)
class Write085:
    succeeded: bool
    error: int
    count: int


def check_metadata085(m,b,root=False):
    require(type(m) is Metadata084)
    path=b.root if root else b.root+'\\synthetic.bin'
    expected=b.root_identity if root else b.file_identity
    identity085(m.identity);require(m.identity==expected)
    require(type(m.final_path) is str and m.final_path.casefold()==path.casefold())
    for v in (m.attributes,m.links,m.size): integer(v)
    integer(m.position,-1)
    require(m.attributes&0x400==0 and bool(m.attributes&0x10)==root)
    require(m.links==1 and m.size==(0 if root else 84) and m.position==-1)
    check_security084(m.security,b.owner_sid)
    parents=tuple(str(p) for p in PureWindowsPath(path).parents)
    require(type(m.ancestors) is tuple and len(m.ancestors)==len(parents)<=16)
    for a,p in zip(m.ancestors,parents):
        require(type(a) is Ancestor084 and type(a.final_path) is str and a.final_path.casefold()==p.casefold())
        integer(a.attributes);identity085(a.identity)
        require(a.attributes&0x400==0 and a.attributes&0x10!=0)
    expected=b.ancestor_identities if root else (b.root_identity,)+b.ancestor_identities
    require(tuple(a.identity for a in m.ancestors)==expected)


class Owner085:
    """Install before factory IO; register each acquired handle before raising."""
    def __init__(self):
        self.backend=None;self.live={};self.finished=False;self.attempts=0;self.unconfirmed=0
    def install(self,p):
        require(self.backend is None and getattr(p,'model_only',None) is True)
        self.backend=p;return p
    def register(self,h,spec):
        require(not self.finished and self.backend is not None and h is not None and type(spec) is Spec084)
        require(h not in self.live and len(self.live)<CAPS['closes'])
        self.live[h]=spec
    def finish(self):
        require(not self.finished);self.finished=True
        for h in list(self.live):
            self.live.pop(h);self.attempts+=1
            try: ok=self.backend.close(h) is True
            except (Exception,KeyboardInterrupt): ok=False
            if not ok:self.unconfirmed+=1
        try: released=self.backend is None or self.backend.finish() is True
        except (Exception,KeyboardInterrupt):released=False
        return not self.live and self.unconfirmed==0 and released


class Lease085:
    """Immutable consumed message plus a still-owned physical pipe instance.

    Closing a logical lease discards no physical pipe handle. The same owned
    handle stays registered until once-only session cleanup; no files publish
    the response. A peer cannot edit bytes already consumed and copied.
    """
    def __init__(self,c,raw,frame,kind,completed):
        self.client=c;self.raw=raw;self.frame=frame;self.kind=kind;self.completed=completed;self.closed=False
    def snapshot(self):
        c=self.client
        try:
            require(not self.closed and c.lease is self and not c.owner.finished)
            require(c.pipe_handle in c.owner.live and not c.stopped)
            decode085(self.raw,self.kind,self.frame.sequence,c.b,c.m.check()[2],c.deadline,c.release,self.completed)
            return self.raw
        except (Exception,KeyboardInterrupt):c.stopped=True;raise
    def close(self):
        require(not self.closed and self.client.lease is self)
        self.closed=True;self.client.lease=None


class Transport085:
    """Injected message contract; no default native backend.

    factory(owner,b) returns an installed peer plus an owned private server
    handle. Fresh inspect() facts are acquired INSIDE every full guard, never
    cached. Only root/metadata share-all and private pipe handles may be owned.
    Backend write/read/wait calls are nonwaiting/bounded contract obligations;
    time checks after return do not interrupt a stalled native function.
    """
    def __init__(self,b,clock,guard,factory):
        require(type(b) is Bindings085)
        self.b,self.clock,self.guard,self.factory=b,clock,guard,factory
        self.owner=Owner085();self.m=None;self.used=False;self.stopped=False
        self.pipe_handle=None;self.lease=None;self.sequence=0;self.deadline=0;self.release=0
        self.expected='ready';self.hold_start=0
        self.release_spent=False;self.counts=dict.fromkeys(CAPS,0);self.trace=[];self.cleanup_ok=None
    def bump(self,k):
        require(not self.stopped and self.counts[k]<CAPS[k]);self.counts[k]+=1
    def full_guard(self):
        self.bump('guards');start=self.m.check()[2]
        require(same_record(self.guard(),Guard083()))
        if self.pipe_handle is not None:
            p=self.owner.backend.inspect(self.pipe_handle)
            require(type(p) is Composite085 and same_record(p.account,Guard083()))
            pipe=p.pipe;require(type(pipe) is Pipe085 and type(pipe.name) is str and pipe.name==self.b.pipe)
            check_security084(pipe.security,self.b.owner_sid)
            require(same_record(pipe.client,self.b.peer))
            for k in ('pipe_type','read_mode','wait_mode','maximum_instances','creation_flags','pipe_mode_flags'):
                integer(getattr(pipe,k));require(getattr(pipe,k)==getattr(Pipe085(pipe.name,pipe.security,pipe.client),k))
            for root,desc,path in ((True,p.root_descriptor,p.root_path),(False,p.file_descriptor,p.file_path)):
                check_metadata085(desc,self.b,root);check_metadata085(path,self.b,root)
                require(same_record(desc,path))
            for spec in self.owner.live.values():
                require(spec.role in ('root','metadata','pipe'))
                if spec.role=='pipe':require(same_record(spec,Spec084('pipe',self.b.pipe,READ|WRITE,0,1,FIRST_INSTANCE)))
                else:
                    expected=Spec084(spec.role,self.b.root if spec.role=='root' else self.b.root+'\\synthetic.bin',
                        META,SHARE_ALL,OPEN_EXISTING,NO_REPARSE|(0x2000000 if spec.role=='root' else 0))
                    require(same_record(spec,expected))
            require(sorted(s.role for s in self.owner.live.values())==['metadata','pipe','root'])
            require(self.owner.live[self.pipe_handle].role=='pipe')
        end=self.m.check()[2];self.trace.append((start,end));return end
    def start(self,enabled=False):
        require(type(enabled) is bool and not self.used);self.used=True
        if not enabled:return False
        self.m=Meter083(self.clock)
        try:
            self.full_guard();p,h=self.factory(self.owner,self.b)
            require(p is self.owner.backend and h in self.owner.live)
            self.pipe_handle=h;self.full_guard();return True
        except (Exception,KeyboardInterrupt):
            self.stopped=True;self.finish();raise
    def episode_check(self):
        now=self.m.check()[2]
        if self.deadline:require(now<self.deadline)
        return now
    def transaction(self,kind,deadline):
        try:
            require(self.m is not None and not self.owner.finished and self.lease is None)
            require(kind in ('ready','release','holding','closed'))
            require(kind==self.expected)
            integer(deadline);now=self.episode_check()
            if not self.deadline:
                require(kind=='ready' and now<deadline<=now+60000);self.deadline=deadline
            require(deadline==self.deadline)
            if kind=='release':
                require(not self.release_spent);self.release_spent=True
            self.bump('transactions');self.full_guard();self.episode_check()
            self.sequence+=1;integer(self.sequence,1,64)
            issued=self.m.check()[2]
            raw=encode085(kind,self.sequence,self.b,issued,deadline)
            self.bump('writes');w=self.owner.backend.write(self.pipe_handle,raw)
            completed=self.episode_check()
            require(type(w) is Write085 and w.succeeded is True and type(w.error) is int and w.error==0)
            require(type(w.count) is int and w.count==144)
            if kind=='release':
                self.release=issued;self.full_guard();now=self.episode_check()
                decode085(raw,kind,self.sequence,self.b,now,deadline,request=True)
                self.expected='holding';return None
            response=None
            for i in range(READS_PER_TRANSACTION):
                self.bump('reads');r=self.owner.backend.read(self.pipe_handle,145);received=self.episode_check()
                require(type(r) is Read085 and type(r.succeeded) is bool and type(r.error) is int and type(r.count) is int)
                require(type(r.buffer_bytes) is int and r.buffer_bytes==145 and type(r.raw) is bytes)
                if r.succeeded:
                    require(r.error==0 and r.count==len(r.raw)==144);response=r.raw;break
                require(r.error==232 and r.count==0 and r.raw==b'')
                if i+1<READS_PER_TRANSACTION:
                    self.bump('waits');require(self.owner.backend.wait(POLL_MS) is None);self.episode_check()
            require(response is not None)
            frame=decode085(response,kind,self.sequence,self.b,received,deadline,self.release,completed)
            if frame.kind==3:self.hold_start=frame.hold_start
            if frame.kind==4:require(frame.hold_start==self.hold_start)
            lease=Lease085(self,response,frame,kind,completed);self.lease=lease
            self.full_guard();self.episode_check();lease.snapshot()
            if frame.kind!=5:self.expected={'ready':'release','holding':'closed','closed':'done'}[kind]
            return lease
        except (Exception,KeyboardInterrupt):self.stopped=True;raise
    def finish(self):
        require(self.counts['cleanup']==0);self.counts['cleanup']=1
        if self.lease is not None:self.lease.close()
        ok=self.owner.finish()
        self.counts['closes']=self.owner.attempts
        try:
            if self.m is not None:self.m.check()
        except (Exception,KeyboardInterrupt):ok=False
        self.cleanup_ok=ok;return ok
    def summary(self):
        return dict(version='held_message_transport_085_v1',counts=dict(self.counts),
            valid_guard_spans=len(self.trace),release_spent=self.release_spent,cleanup_confirmed=self.cleanup_ok,
            unconfirmed_closes=self.owner.unconfirmed,physical_close_attempts=self.owner.attempts,
            response_files_created=0,full_guards_uncached=True,guard_group='one_bounded_pipe_transaction',
            sdk_connections=0,market_reads=0,orders=0,receipt_permissions=0,
            native_protocol_implemented=False,native_mql_verified=False,runtime_authorized=False,latency_guaranteed=False)


def close_action085(now,release,start):
    """Pure priority policy: hold=0, close=1, late-close=2, invalid=3."""
    try:
        for v in (now,release,start):integer(v)
        require(0<release<=start<=release+10000 and now>=start)
    except Exception:return 3
    if now<start+30000:return 0
    return 1 if now<=start+31000 else 2


class AutonomousClose085:
    """Injected reader close schedule, driven independently of pipe requests.

    close() is spent before invocation, including uncertainty/interruptions.
    guard/close latency or a scheduler stall may still overrun. On any guard or
    clock rejection, cleanup attempts the owned close once and success is false.
    No implementation here opens a reader or guarantees physical preemption.
    """
    def __init__(self,clock,guard,close):
        self.clock,self.guard,self.close=clock,guard,close
        self.m=None;self.used=False;self.spent=False;self.confirmed=False;self.valid=False
        self.release=0;self.start_time=0;self.end=None;self.guards=0
    def start(self,enabled=False,release=0,hold_start=0):
        require(type(enabled) is bool and not self.used);self.used=True
        if not enabled:return False
        self.m=Meter083(self.clock);now=self.m.check()[2]
        require(close_action085(now,release,hold_start)==0)
        self.release,self.start_time=release,hold_start;return True
    def owned_close(self):
        require(not self.spent);self.spent=True
        try:self.confirmed=self.close() is True
        except (Exception,KeyboardInterrupt):self.confirmed=False
    def tick(self):
        require(self.m is not None and not self.spent)
        try:
            action=close_action085(self.m.check()[2],self.release,self.start_time)
            require(action!=3)
            if action==0:return False
            self.guards+=1;require(same_record(self.guard(),Guard083()));self.m.check()
            self.owned_close();self.end=self.m.check()[2]
            self.guards+=1;require(same_record(self.guard(),Guard083()));self.m.check()
            self.valid=self.confirmed and close_action085(self.end,self.release,self.start_time)==1
            return True
        except (Exception,KeyboardInterrupt):
            if not self.spent:self.owned_close()
            self.valid=False;return True


def source_contract085(root):
    root=Path(root);names=set(MQL_INPUTS)
    pending=['src/forex_demo_lab/synchronization_085.py','src/forex_demo_lab/__init__.py']
    while pending:
        n=pending.pop()
        if n in names:continue
        names.add(n)
        for node in ast.walk(ast.parse((root/n).read_text())):
            if isinstance(node,ast.ImportFrom) and node.level:
                require(node.level==1 and node.module is not None)
                pending.append('src/forex_demo_lab/'+node.module.replace('.','/')+'.py')
    inputs={n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in sorted(names)}
    for n in ('mt5/Scripts/Synchronization085.mqh','docs/SYNCHRONIZATION-085-DESIGN.md',
              'docs/SYNCHRONIZATION-085-POLICY.md'):
        inputs[n]=hashlib.sha256((root/n).read_bytes()).hexdigest()
    return dict(version='transport_redesign_source_085_v1',phase=PHASE,date=DATE,input_bindings=inputs,
        wire_bytes=144,caps=dict(CAPS),reads_per_transaction=READS_PER_TRANSACTION,poll_ms=POLL_MS,
        original_peer_bytes=True,response_files_created=0,full_guard_group='one_bounded_pipe_transaction',
        full_guard_contents='uncached_account_images_sdk_sources_peer_acl_root_file_path_descriptor',
        close_trigger='own_clock_independent_of_requests',pipe_wait_mode=1,pipe_read_mode=2,pipe_type=4,
        flush_calls=0,whole_limit_ms=120000,episode_limit_ms=60000,freshness_ms=2000,
        start_limit_ms=10000,close_min_ms=30000,close_max_ms=31000,control_margin_ms=250,
        retained_mql_inputs=list(MQL_INPUTS),new_mql_entrypoint_prepared=False,compiled=False,native_backend_prepared=False,
        native_protocol_implemented=False,native_runtime_authorized=False,orders_available=False)
