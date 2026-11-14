"""Local fixture-only Win32 pipe operations. No MT5, SDK or market APIs."""
import ctypes as C
from ctypes import wintypes as W
import hashlib
import os
from pathlib import Path
import time

class PipeRejected(RuntimeError):pass
_PENDING=[] # Retain native IO memory on an unproven cancellation; never reuse it.

class OVERLAPPED(C.Structure):
    _fields_=[('Internal',C.c_size_t),('InternalHigh',C.c_size_t),('Offset',W.DWORD),('OffsetHigh',W.DWORD),('hEvent',W.HANDLE)]
class SECURITY(C.Structure):
    _fields_=[('length',W.DWORD),('descriptor',W.LPVOID),('inherit',W.BOOL)]
class SID_ATTRIBUTE(C.Structure):
    _fields_=[('sid',W.LPVOID),('attributes',W.DWORD)]

class WindowsPipe:
    def __init__(self):
        if os.name!='nt' or C.sizeof(C.c_void_p)!=8:raise PipeRejected('windows_x64_required')
        self.k=C.WinDLL('kernel32',use_last_error=True);self.a=C.WinDLL('advapi32',use_last_error=True)
        def api(dll,name,args,result):
            f=getattr(dll,name);f.argtypes=args;f.restype=result;return f
        H,P,D,B=W.HANDLE,W.LPVOID,W.DWORD,W.BOOL
        self.create=api(self.k,'CreateNamedPipeW',[W.LPCWSTR,D,D,D,D,D,D,P],H)
        self.file=api(self.k,'CreateFileW',[W.LPCWSTR,D,D,P,D,D,H],H)
        self.event=api(self.k,'CreateEventW',[P,B,B,W.LPCWSTR],H)
        self.close=api(self.k,'CloseHandle',[H],B)
        self.connect=api(self.k,'ConnectNamedPipe',[H,P],B)
        self.read=api(self.k,'ReadFile',[H,P,D,P,P],B);self.write=api(self.k,'WriteFile',[H,P,D,P,P],B)
        self.result=api(self.k,'GetOverlappedResult',[H,P,C.POINTER(D),B],B)
        self.wait=api(self.k,'WaitForSingleObject',[H,D],D);self.cancel=api(self.k,'CancelIoEx',[H,P],B)
        self.client_pid=api(self.k,'GetNamedPipeClientProcessId',[H,C.POINTER(D)],B)
        self.server_pid=api(self.k,'GetNamedPipeServerProcessId',[H,C.POINTER(D)],B)
        self.process=api(self.k,'OpenProcess',[D,B,D],H)
        self.image=api(self.k,'QueryFullProcessImageNameW',[H,D,W.LPWSTR,C.POINTER(D)],B)
        self.times=api(self.k,'GetProcessTimes',[H,P,P,P,P],B)
        self.session=api(self.k,'ProcessIdToSessionId',[D,C.POINTER(D)],B)
        self.token=api(self.a,'OpenProcessToken',[H,D,C.POINTER(H)],B)
        self.token_info=api(self.a,'GetTokenInformation',[H,D,P,D,C.POINTER(D)],B)
        self.sid_string=api(self.a,'ConvertSidToStringSidW',[P,C.POINTER(W.LPWSTR)],B)
        self.sddl=api(self.a,'ConvertStringSecurityDescriptorToSecurityDescriptorW',[W.LPCWSTR,D,C.POINTER(P),P],B)
        self.free=api(self.k,'LocalFree',[P],P)
        self.boot=api(self.k,'GetTickCount64',[],C.c_ulonglong)
        self.invalid=C.c_void_p(-1).value

    def identity(self,pid):
        p=self.process(0x1000,False,pid)
        if not p:raise PipeRejected('peer_process_rejected')
        token=W.HANDLE()
        try:
            text=C.create_unicode_buffer(32768);n=W.DWORD(len(text));creation=C.c_ulonglong();other=[C.c_ulonglong() for _ in range(3)]
            session=W.DWORD()
            if not self.image(p,0,text,C.byref(n)) or not self.times(p,C.byref(creation),*[C.byref(x) for x in other]) or not self.session(pid,C.byref(session)):
                raise PipeRejected('peer_metadata_rejected')
            if not self.token(p,8,C.byref(token)):raise PipeRejected('peer_token_rejected')
            needed=W.DWORD();self.token_info(token,2,None,0,C.byref(needed))
            if not 8<=needed.value<=65536:raise PipeRejected('peer_groups_rejected')
            buf=C.create_string_buffer(needed.value)
            if not self.token_info(token,2,buf,len(buf),C.byref(needed)):raise PipeRejected('peer_groups_rejected')
            count=C.cast(buf,C.POINTER(W.DWORD))[0]
            if count>256 or 8+count*C.sizeof(SID_ATTRIBUTE)>len(buf):raise PipeRejected('peer_groups_rejected')
            groups=(SID_ATTRIBUTE*count).from_address(C.addressof(buf)+8)
            values=[g for g in groups if g.attributes&0xC0000000==0xC0000000]
            if len(values)!=1:raise PipeRejected('peer_logon_rejected')
            sid=W.LPWSTR()
            if not self.sid_string(values[0].sid,C.byref(sid)):raise PipeRejected('peer_logon_rejected')
            try:private_sid=sid.value
            finally:self.free(C.cast(sid,W.LPVOID))
            path=Path(text.value)
            return (pid,creation.value,str(path).casefold(),hashlib.sha256(path.read_bytes()).hexdigest(),session.value,private_sid)
        finally:
            if token:self.close(token)
            self.close(p)

    def peer(self,handle,side,expected):
        pid=W.DWORD();function=self.client_pid if side=='client' else self.server_pid
        if not function(handle,C.byref(pid)) or pid.value!=expected[0] or self.identity(pid.value)!=expected:
            raise PipeRejected('peer_binding_rejected')

    def server(self,name,identity):
        if not name.startswith('\\\\.\\pipe\\ForexDemoFixture047-') or '\\' in name[9:]:raise PipeRejected('pipe_name_rejected')
        descriptor=W.LPVOID()
        # Minimum mapped generic-read/write rights required by MQL FileOpen.
        sddl='D:P(A;;0x12019f;;;'+identity[-1]+')'
        if not self.sddl(sddl,1,C.byref(descriptor),None):raise PipeRejected('pipe_security_rejected')
        try:
            security=SECURITY(C.sizeof(SECURITY),descriptor,False)
            handle=self.create(name,3|0x40000000|0x80000,4|2|8,1,128,128,2000,C.byref(security))
        finally:self.free(descriptor)
        if handle==self.invalid:raise PipeRejected('pipe_create_rejected')
        return handle

    def client(self,name):
        h=self.file(name,0xC0000000,0,None,3,0x40000000,None)
        if h==self.invalid:raise PipeRejected('pipe_open_rejected')
        return h

    def io(self,handle,kind,data=None,size=0,timeout_ms=2000):
        if type(timeout_ms) is not int or not 1<=timeout_ms<=2000:raise PipeRejected('io_deadline_rejected')
        event=self.event(None,True,False,None)
        if not event:raise PipeRejected('event_create_rejected')
        overlap=OVERLAPPED();overlap.hEvent=event
        buffer=C.create_string_buffer(data,len(data)) if kind=='write' else C.create_string_buffer(max(size,1))
        count=W.DWORD();retain=False
        try:
            if kind=='connect':ok=self.connect(handle,C.byref(overlap))
            elif kind=='read':ok=self.read(handle,buffer,size,None,C.byref(overlap))
            elif kind=='write':ok=self.write(handle,buffer,len(data),None,C.byref(overlap))
            else:raise PipeRejected('io_kind_rejected')
            error=C.get_last_error()
            if kind=='connect' and (ok or error==535):return b''
            if not ok and error!=997:raise PipeRejected('io_operation_rejected')
            if not ok and self.wait(event,timeout_ms)!=0:
                self.cancel(handle,C.byref(overlap))
                if self.wait(event,1000)!=0:
                    retain=True;_PENDING.append((overlap,event,buffer,handle));raise PipeRejected('cancellation_not_drained')
                # IO may complete normally after cancellation; the deadline still fails.
                self.result(handle,C.byref(overlap),C.byref(count),False)
                raise PipeRejected('io_deadline_exceeded')
            if not self.result(handle,C.byref(overlap),C.byref(count),False):raise PipeRejected('io_completion_rejected')
            if kind=='write' and count.value!=len(data):raise PipeRejected('short_write_rejected')
            return buffer.raw[:count.value] if kind=='read' else b''
        finally:
            if not retain:self.close(event)

    def clock(self):return time.time_ns()//1000000,time.monotonic_ns(),int(self.boot())
