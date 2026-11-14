"""Private uncached guards. No SDK import/initialize, market or order methods.
The caller supplies an already-connected metadata-only SDK and frozen bindings.
"""
import ctypes as C
from dataclasses import dataclass, field
import hashlib
import os
import re
import stat
from pathlib import Path, PureWindowsPath
from .clock_observer_042 import runtime_guard
from .native_files_065 import D, H, P, B, FILETIME
from .sharing_probe_062 import ProbeRejected


@dataclass(frozen=True)
class Identity065:
    pid: int = field(repr=False)
    creation: int = field(repr=False)
    image: str = field(repr=False)
    digest: str = field(repr=False)
    session: int = field(repr=False)
    logon: str = field(repr=False)


class PROCESS_ENTRY(C.Structure):
    _fields_=[('size',D),('usage',D),('pid',D),('heap',C.c_size_t),('module',D),
              ('threads',D),('parent',D),('priority',C.c_int32),('flags',D),('exe',C.c_uint16*260)]
class SID_ATTRIBUTE(C.Structure):
    _fields_=[('sid',P),('attributes',D)]


class NativeIdentity065:
    def __init__(self,files):
        self.f=files;self.meter=files.meter;b=files.bind;k=files.k;a=files.a
        self.process=b(k,'OpenProcess',[D,B,D],H)
        self.image=b(k,'QueryFullProcessImageNameW',[H,D,C.c_wchar_p,C.POINTER(D)],B)
        self.times=b(k,'GetProcessTimes',[H,*[C.POINTER(FILETIME)]*4],B)
        self.session=b(k,'ProcessIdToSessionId',[D,C.POINTER(D)],B)
        self.snapshot=b(k,'CreateToolhelp32Snapshot',[D,D],H)
        self.first=b(k,'Process32FirstW',[H,C.POINTER(PROCESS_ENTRY)],B)
        self.next=b(k,'Process32NextW',[H,C.POINTER(PROCESS_ENTRY)],B)
    def registered(self,handle,role):
        if handle and handle!=self.f.invalid:self.f.active[handle]=role
    def unique_pid(self):
        self.meter.consume('process_snapshots');h=H()
        def remember(value):h.value=value;self.registered(value,'process_snapshot')
        try:
            value,_=self.f._call(self.snapshot,2,0,register=remember)
            if not value or value==self.f.invalid:raise ProbeRejected('private_identity_rejected')
            entry=PROCESS_ENTRY();entry.size=C.sizeof(entry);pids=[]
            ok,error=self.f._call(self.first,h,C.byref(entry))
            for _ in range(513):
                if not ok:
                    if error!=18:raise ProbeRejected('private_identity_rejected')
                    break
                self.meter.consume('process_entries')
                name=bytes(entry.exe).decode('utf-16-le').split('\0',1)[0]
                if name.casefold()=='terminal64.exe':pids.append(int(entry.pid))
                ok,error=self.f._call(self.next,h,C.byref(entry))
            else:raise ProbeRejected('private_identity_rejected')
            if len(pids)!=1:raise ProbeRejected('private_identity_rejected')
            return pids[0]
        finally:
            if h.value and h.value!=self.f.invalid and self.f.close(h.value) is not True:
                raise ProbeRejected('handle_close_unconfirmed')
    def hash_file(self,path):
        self.meter.consume('hash_reads');path=Path(path)
        try:
            for p in (path,*path.parents):
                self.meter.consume('hash_path_stats');s=p.lstat()
                if getattr(s,'st_file_attributes',0)&0x400 or stat.S_ISLNK(s.st_mode):raise ValueError()
            self.meter.consume('hash_path_stats');before=path.stat();total=0;digest=hashlib.sha256()
            if not 0<before.st_size<=134217728:raise ValueError()
            with path.open('rb') as stream:
                while True:
                    self.meter.check();raw=stream.read(1048576)
                    if not raw:break
                    total+=len(raw)
                    if total>134217728:raise ValueError()
                    self.meter.consume('hash_bytes',len(raw));digest.update(raw)
            self.meter.consume('hash_path_stats');after=path.stat()
            if total!=before.st_size or (before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns)!=(after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns):
                raise ValueError()
            self.meter.check();return digest.hexdigest()
        except Exception:raise ProbeRejected('private_hash_rejected') from None
    def identity(self,pid):
        if type(pid) is not int or pid<=0:raise ProbeRejected('private_identity_rejected')
        p=H();token=H();closed=True
        def remember_proc(value):p.value=value;self.registered(value,'identity_process')
        def remember_token(ok):
            if ok:self.registered(token.value,'identity_token')
        try:
            self.meter.consume('process_opens')
            if not self.f._call(self.process,0x1000,False,pid,register=remember_proc)[0]:raise ValueError()
            image=C.create_unicode_buffer(32768);n=D(len(image));times=[FILETIME() for _ in range(4)];session=D()
            if not self.f._call(self.image,p,0,image,C.byref(n))[0]:raise ValueError()
            if not self.f._call(self.times,p,*[C.byref(t) for t in times])[0]:raise ValueError()
            if not self.f._call(self.session,pid,C.byref(session))[0]:raise ValueError()
            self.meter.consume('identity_tokens')
            if not self.f._call(self.f.token,p,8,C.byref(token),register=remember_token)[0]:raise ValueError()
            needed=D();ok,error=self.f._call(self.f.token_info,token,2,None,0,C.byref(needed))
            if ok or error!=122 or not 8<=needed.value<=65536:raise ValueError()
            buf=C.create_string_buffer(needed.value)
            if not self.f._call(self.f.token_info,token,2,buf,len(buf),C.byref(needed))[0]:raise ValueError()
            count=C.cast(buf,C.POINTER(D))[0]
            if count>256 or 8+count*C.sizeof(SID_ATTRIBUTE)>len(buf):raise ValueError()
            groups=(SID_ATTRIBUTE*count).from_address(C.addressof(buf)+8)
            logon=[g for g in groups if g.attributes&0xC0000000==0xC0000000]
            if len(logon)!=1:raise ValueError()
            sid=P()
            try:
                if not self.f._call(self.f.sid_string,logon[0].sid,C.byref(sid))[0]:raise ValueError()
                private_sid=C.wstring_at(sid)
            finally:self.f._release(sid)
            path=Path(image.value);digest=self.hash_file(path)
            creation=(int(times[0].high)<<32)|int(times[0].low)
            return Identity065(pid,creation,str(path).casefold(),digest,int(session.value),private_sid)
        except Exception:raise ProbeRejected('private_identity_rejected') from None
        finally:
            for h in (token.value,p.value):
                if h and self.f.close(h) is not True:closed=False
            if not closed:raise ProbeRejected('handle_close_unconfirmed')


class Metadata065:
    def __init__(self,api,meter):
        if type(api.ACCOUNT_TRADE_MODE_DEMO) is not int or api.ACCOUNT_TRADE_MODE_DEMO!=0:
            raise ProbeRejected('private_guard_rejected')
        self.ACCOUNT_TRADE_MODE_DEMO=0;self._api=api;self._meter=meter
    def _call(self,name,*args):
        self._meter.consume('sdk_queries');value=getattr(self._api,name)(*args);self._meter.check();return value
    def account_info(self):return self._call('account_info')
    def terminal_info(self):return self._call('terminal_info')
    def symbol_info(self,name):return self._call('symbol_info',name)


class FullGuard065:
    def __init__(self,api,reader,peer,data_root,build,editor_binding,artifact_binding,meter):
        self.reader,self.peer,self.data_root,self.build=reader,peer,str(data_root),build
        self.editor,self.artifact=editor_binding,artifact_binding
        self.meter=meter;self.api=Metadata065(api,meter);self.account=None;self.stopped=False
        if (type(peer) is not Identity065 or type(build) is not int or build<=0 or
                any(type(x) is not int or x<=0 for x in (peer.pid,peer.creation)) or
                type(peer.session) is not int or peer.session<0 or
                any(type(x) is not str or not x for x in (peer.image,peer.logon,self.data_root)) or
                type(peer.digest) is not str or re.fullmatch('[0-9a-f]{64}',peer.digest) is None):raise ProbeRejected('private_guard_rejected')
        for binding in (self.editor,self.artifact):
            if type(binding) is not tuple or len(binding)!=2 or type(binding[1]) is not str or re.fullmatch('[0-9a-f]{64}',binding[1]) is None:
                raise ProbeRejected('private_guard_rejected')
        self.terminal_dir=str(PureWindowsPath(peer.image).parent).casefold()
    def __call__(self):
        try:
            if self.stopped:raise ValueError()
            self.meter.consume('guards')
            if self.reader.unique_pid()!=self.peer.pid or self.reader.identity(self.peer.pid)!=self.peer:raise ValueError()
            self.account=runtime_guard(self.api,self.account)
            info=self.api.terminal_info()
            if (info is None or type(info.build) is not int or info.build!=self.build or
                    type(info.path) is not str or info.path.casefold()!=self.terminal_dir or
                    type(info.data_path) is not str or info.data_path.casefold()!=self.data_root.casefold()):raise ValueError()
            # Full byte hashes on EVERY guard, with per-read/byte caps. No cache.
            for path,digest in (self.editor,self.artifact):
                if self.reader.hash_file(path)!=digest:raise ValueError()
            if self.reader.unique_pid()!=self.peer.pid or self.reader.identity(self.peer.pid)!=self.peer:raise ValueError()
            runtime_guard(self.api,self.account);self.meter.check();return True
        except Exception:
            self.stopped=True;raise ProbeRejected('private_guard_rejected') from None
    def bind_files(self,files):
        expected=PureWindowsPath(self.data_root)/'MQL5'/'Files'
        if files.scope!='terminal' or str(files.parent).casefold()!=str(expected).casefold():
            raise ProbeRejected('private_guard_rejected')
        return self()
