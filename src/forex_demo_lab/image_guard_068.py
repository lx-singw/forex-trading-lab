"""Separate bounded image hash correction and helper-chain decisions.

No SDK import/attachment, quotes, history or orders. Native identity ABI and
ownership stay with065; old source and consumed066 reservation are unchanged.
"""
from dataclasses import dataclass, field
import hashlib
import json
import os
from pathlib import Path, PureWindowsPath
import stat

from .private_guard_065 import NativeIdentity065,Identity065
from .sharing_probe_062 import ProbeRejected

MAX_IMAGE_BYTES=136314880  #130MiB, NOT an unbounded image read.
CHUNK=1048576
STAGES=('preflight','terminal_image','editor_image','signature','terminal_process',
    'helper_process','helper_chain','sdk_import','sdk_attach','account_metadata',
    'deployment','file_prepare','disabled_arm','enabled_arm','independent_controls',
    'post_controls','saved_log','file_cleanup','sdk_cleanup','final_audit')


def bounded_hash(meter,path,path_factory=Path,fstat=os.fstat):
    meter.consume('hash_reads')
    try:
        path=path_factory(path)
        def properties(p):
            meter.consume('hash_path_stats');s=p.lstat()
            if getattr(s,'st_file_attributes',0)&0x400 or stat.S_ISLNK(s.st_mode):raise ValueError()
            return s
        def stable(s):return s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns
        for p in path.parents:properties(p)
        before=properties(path)
        if not stat.S_ISREG(before.st_mode) or not 0<before.st_size<=MAX_IMAGE_BYTES:raise ValueError()
        before_key=stable(before);remaining=before.st_size;digest=hashlib.sha256()
        with path.open('rb') as stream:
            meter.consume('hash_path_stats');opened=fstat(stream.fileno())
            if stable(opened)!=before_key:raise ValueError()
            while remaining:
                meter.check();n=min(CHUNK,remaining)
                # Reserve every requested byte BEFORE the stream call. A short
                # read/failure never refunds this aggregate allowance.
                meter.consume('hash_bytes',n);raw=stream.read(n)
                if type(raw) is not bytes or not raw or len(raw)>n:raise ValueError()
                digest.update(raw);remaining-=len(raw)
            meter.consume('hash_path_stats');closed=fstat(stream.fileno())
            if stable(closed)!=before_key:raise ValueError()
            meter.check()
        for p in path.parents:properties(p)
        after=properties(path)
        if stable(after)!=before_key:raise ValueError()
        meter.check();return digest.hexdigest()
    except Exception:raise ProbeRejected('image_hash_rejected_details_redacted') from None


class NativeIdentity068(NativeIdentity065):
    def hash_file(self,path):return bounded_hash(self.meter,path)


class Stage068:
    """Fixed names/counters only; never export an exception/path/identity."""
    def __init__(self):self.current=None;self.events=[]
    def enter(self,name):
        if name not in STAGES or len(self.events)>=24:raise ProbeRejected('stage_budget_rejected')
        self.current=name;self.events.append(dict(stage=name,started=True,completed=False))
    def complete(self):
        if not self.events or self.events[-1]['completed']:raise ProbeRejected('stage_order_rejected')
        self.events[-1]['completed']=True
    def run(self,name,operation,*args):
        self.enter(name);result=operation(*args);self.complete();return result
    def public(self):return [dict(e) for e in self.events]


@dataclass(frozen=True)
class HelperChain068:
    launcher: tuple = field(repr=False)
    config: tuple = field(repr=False)
    images: tuple = field(repr=False)
    library: tuple = field(repr=False)
    base_alias: str = field(repr=False)
    def __post_init__(self):
        import re
        if not self.images or len(self.images)>2:raise ProbeRejected('helper_chain_rejected')
        for path,digest in (self.launcher,self.config,self.library,*self.images):
            if type(path) is not str or not path or type(digest) is not str or re.fullmatch('[0-9a-f]{64}',digest) is None:
                raise ProbeRejected('helper_chain_rejected')
        if type(self.base_alias) is not str or not self.base_alias:raise ProbeRejected('helper_chain_rejected')
    def check(self,reader,helper,executable,base_alias,loaded_library):
        # The WindowsApps alias is a DECLARED launch input, never a native
        # identity or a path to hash through a reparse point. Actual image/DLL
        # must match pinned regular files in the measured installed package.
        if (type(helper) is not Identity065 or str(executable).casefold()!=self.launcher[0].casefold() or
            str(base_alias).casefold()!=self.base_alias.casefold() or
            str(loaded_library).casefold()!=self.library[0].casefold() or
            (helper.image,helper.digest) not in tuple((p.casefold(),h) for p,h in self.images)):
            raise ProbeRejected('helper_chain_rejected')
        for path,expected in (self.launcher,self.config,self.library):
            if reader.hash_file(path)!=expected:raise ProbeRejected('helper_chain_rejected')
        return True


def reservation_bytes(raw,expected_sha,bindings,phase):
    """Audit exact exclusive reservation bytes, not an assumed sidecar."""
    from .clock_observer_042 import unique_pairs
    try:
        if type(raw) is not bytes or len(raw)>4096 or hashlib.sha256(raw).hexdigest()!=expected_sha:raise ValueError()
        r=json.loads(raw.decode('ascii'),object_pairs_hook=unique_pairs)
        if r['bindings']!=bindings or r['phase']!=phase or r['orders_available'] is not False:raise ValueError()
        return r
    except Exception:raise ProbeRejected('reservation_bytes_rejected') from None
