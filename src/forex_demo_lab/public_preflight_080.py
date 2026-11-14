"""Bounded public-file reader with exact LF/CRLF checksum grammar; no SDK.

The078 reader remains frozen. Its raw/clock/file checks are retained here;
only record-sidecar cap and verification change. No whitespace stripping or
JSON/source normalization is allowed. Native identity is not modeled as proof.
"""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import stat
import time

DATE080='2026-10-08'
SIDECAR_CAP080=66


class PublicInputRejected080(Exception):
    pass


def unique_pairs080(pairs):
    out={}
    for key,value in pairs:
        if key in out:raise ValueError('duplicate_public_key')
        out[key]=value
    return out


def verify_sidecar080(raw, content):
    if type(raw) is not bytes or type(content) is not bytes:
        raise PublicInputRejected080('timing_public_digest_rejected')
    digest=hashlib.sha256(content).hexdigest().encode('ascii')
    if raw==digest+b'\n':return 'lf'
    if raw==digest+b'\r\n':return 'crlf'
    raise PublicInputRejected080('timing_public_digest_rejected')


class PublicInputs080:
    """078 caps retained; sidecar cap66 explicitly admits one CR before LF.

    16 public reads/2MiB/128 stats;64 source/launcher reads/16MiB/1024
    stats;30s, stable regular single-link files, no reparse parents, exact
    descriptor/path identity and size. Clock/date behavior is unchanged.
    """
    def __init__(self,clock=lambda:(time.time_ns()//1000000,time.monotonic_ns())):
        self.clock=clock;self.first=clock();self.last=self.first
        self.reads=self.bytes=self.stats=0
        self.source_reads=self.source_bytes=self.source_stats=0
    def check(self):
        now=self.clock()
        if (type(now) is not tuple or len(now)!=2 or any(type(x) is not int or x<0 for x in now) or
            datetime.fromtimestamp(now[0]//1000,timezone.utc).date().isoformat()!=DATE080 or
            any(a<b for a,b in zip(now,self.last)) or now[1]-self.first[1]>=30000000000 or
            abs(now[0]-self.first[0]-(now[1]-self.first[1])//1000000)>1000):
            raise PublicInputRejected080('timing_public_clock_rejected')
        self.last=now
    def properties(self,path,source=False):
        self.check()
        key='source_stats' if source else 'stats';setattr(self,key,getattr(self,key)+1)
        if getattr(self,key)>(1024 if source else 128): raise PublicInputRejected080('timing_public_budget_rejected')
        s=Path(path).lstat()
        if stat.S_ISLNK(s.st_mode) or getattr(s,'st_file_attributes',0)&0x400:
            raise PublicInputRejected080('timing_public_file_rejected')
        return s
    def raw(self,path,cap=524288,source=False):
        self.check()
        reads='source_reads' if source else 'reads';total='source_bytes' if source else 'bytes'
        stats='source_stats' if source else 'stats'
        setattr(self,reads,getattr(self,reads)+1)
        if getattr(self,reads)>(64 if source else 16): raise PublicInputRejected080('timing_public_budget_rejected')
        path=Path(path)
        for p in path.parents: self.properties(p,source)
        before=self.properties(path,source)
        if not stat.S_ISREG(before.st_mode) or before.st_nlink!=1 or not 0<before.st_size<=cap:
            raise PublicInputRejected080('timing_public_file_rejected')
        setattr(self,total,getattr(self,total)+before.st_size)
        if getattr(self,total)>(16777216 if source else 2097152): raise PublicInputRejected080('timing_public_budget_rejected')
        key=lambda s:(s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_nlink)
        with path.open('rb') as stream:
            setattr(self,stats,getattr(self,stats)+2)
            if getattr(self,stats)>(1024 if source else 128) or key(os.fstat(stream.fileno()))!=key(before): raise PublicInputRejected080('timing_public_file_rejected')
            raw=stream.read(before.st_size)
            if key(os.fstat(stream.fileno()))!=key(before): raise PublicInputRejected080('timing_public_file_rejected')
        if key(self.properties(path,source))!=key(before) or len(raw)!=before.st_size:
            raise PublicInputRejected080('timing_public_file_rejected')
        self.check();return raw
    def record(self,path):
        raw=self.raw(path);side=self.raw(Path(path).with_suffix('.sha256'),SIDECAR_CAP080)
        verify_sidecar080(side,raw)
        try:return json.loads(raw.decode('ascii'),object_pairs_hook=unique_pairs080),hashlib.sha256(raw).hexdigest()
        except Exception:raise PublicInputRejected080('timing_public_schema_rejected') from None
