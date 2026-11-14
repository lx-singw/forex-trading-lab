"""Separate065 native files backend. No SDK, process attachment or market API.
Only an explicit prepared caller may instantiate this Windows-only adapter.
"""
import ctypes as C
import os
from pathlib import Path
import uuid
from .sharing_companion_065 import Meter065, PHASE, ROLE_SPECS
from .mql_sharing_064 import DATA, PHASE as MQL_PHASE
from .sharing_probe_062 import ProbeRejected, Open, Stamp
_RETAINED=[]

# Fixed-width ctypes ABI, also inspectable in Linux pure tests.
D=C.c_uint32;B=C.c_int32;H=C.c_void_p;P=C.c_void_p
class FILETIME(C.Structure):_fields_=[('low',D),('high',D)]
class FILEINFO(C.Structure):
    _fields_=[('attributes',D),('created',FILETIME),('accessed',FILETIME),('written',FILETIME),
              ('volume',D),('size_high',D),('size_low',D),('links',D),('index_high',D),('index_low',D)]
class SECURITY(C.Structure):_fields_=[('length',D),('descriptor',P),('inherit',B)]
class ACLINFO(C.Structure):_fields_=[('count',D),('used',D),('free',D)]


class NativeFiles065:
    """Direct local synchronous Win32 only. No events or asynchronous IO.

    Timer checks cannot interrupt a native call. No speculative retries, file
    deletes, rename, recursive cleanup or unrelated directory operations.
    """
    def __init__(self,meter,parent,scope):
        if os.name!='nt' or C.sizeof(P)!=8:raise ProbeRejected('windows_x64_required')
        self.meter=meter;self.active={};self.unconfirmed=[];self.closes=[]
        self.allocations_released=True;self.descriptor=P();self.created=False
        self.k=C.WinDLL('kernel32',use_last_error=True);self.a=C.WinDLL('advapi32',use_last_error=True)
        def bind(dll,name,args,result):
            f=getattr(dll,name);f.argtypes=args;f.restype=result;f._fxdl_name=name;return f
        self.file=bind(self.k,'CreateFileW',[C.c_wchar_p,D,D,P,D,D,H],H)
        self.mkdir=bind(self.k,'CreateDirectoryW',[C.c_wchar_p,P],B)
        self.close_handle=bind(self.k,'CloseHandle',[H],B)
        self.write_file=bind(self.k,'WriteFile',[H,P,D,C.POINTER(D),P],B)
        self.read_file=bind(self.k,'ReadFile',[H,P,D,C.POINTER(D),P],B)
        self.info=bind(self.k,'GetFileInformationByHandle',[H,C.POINTER(FILEINFO)],B)
        self.position=bind(self.k,'SetFilePointerEx',[H,C.c_int64,C.POINTER(C.c_int64),D],B)
        self.final_path=bind(self.k,'GetFinalPathNameByHandleW',[H,C.c_wchar_p,D,D],D)
        self.attributes=bind(self.k,'GetFileAttributesW',[C.c_wchar_p],D)
        self.long_path=bind(self.k,'GetLongPathNameW',[C.c_wchar_p,C.c_wchar_p,D],D)
        self.current_process=bind(self.k,'GetCurrentProcess',[],H)
        self.token=bind(self.a,'OpenProcessToken',[H,D,C.POINTER(H)],B)
        self.token_info=bind(self.a,'GetTokenInformation',[H,D,P,D,C.POINTER(D)],B)
        self.sid_length=bind(self.a,'GetLengthSid',[P],D)
        self.copy_sid=bind(self.a,'CopySid',[D,P,P],B)
        self.sid_string=bind(self.a,'ConvertSidToStringSidW',[P,C.POINTER(P)],B)
        self.sddl=bind(self.a,'ConvertStringSecurityDescriptorToSecurityDescriptorW',[C.c_wchar_p,D,C.POINTER(P),P],B)
        self.security_info=bind(self.a,'GetSecurityInfo',[H,D,D,C.POINTER(P),P,C.POINTER(P),P,C.POINTER(P)],D)
        self.control=bind(self.a,'GetSecurityDescriptorControl',[P,C.POINTER(C.c_uint16),C.POINTER(D)],B)
        self.acl_info=bind(self.a,'GetAclInformation',[P,P,D,D],B)
        self.ace=bind(self.a,'GetAce',[P,D,C.POINTER(P)],B)
        self.equal_sid=bind(self.a,'EqualSid',[P,P],B)
        self.free=bind(self.k,'LocalFree',[P],P)
        self.bind=bind
        self.invalid=C.c_void_p(-1).value
        if scope not in ('compatibility','terminal'):
            raise ProbeRejected('local_path_rejected')
        raw_parent=str(parent)
        parent=Path(raw_parent)
        if not parent.is_absolute() or not parent.drive or raw_parent.startswith('\\\\') or len(raw_parent)>180:
            raise ProbeRejected('local_path_rejected')
        self.parent=parent;self.scope=scope
        name=('ForexDemoMetadata065-'+PHASE+'-'+uuid.uuid4().hex if scope=='compatibility'
              else 'ForexDemoSharing064-'+MQL_PHASE)
        self.root=parent/name;self.fixture=self.root/'synthetic.bin'
        if len(str(self.fixture))>=248:raise ProbeRejected('local_path_rejected')
    def _call(self,fn,*args,register=None):
        name=getattr(fn,'_fxdl_name','')
        bucket=('security_queries' if name in ('GetSecurityInfo','GetSecurityDescriptorControl','GetAclInformation','GetAce','EqualSid')
                else 'file_properties' if name in ('GetFileInformationByHandle','SetFilePointerEx','GetFinalPathNameByHandleW')
                else 'parent_queries' if name in ('GetFileAttributesW','GetLongPathNameW')
                else 'token_queries' if name in ('GetTokenInformation','GetLengthSid','CopySid','ConvertSidToStringSidW','ConvertStringSecurityDescriptorToSecurityDescriptorW')
                else None)
        if bucket:self.meter.consume(bucket)
        self.meter.consume('native_calls');C.set_last_error(0)
        result=fn(*args);error=C.get_last_error()
        if register is not None:register(result)
        self.meter.check()
        return result,error
    def _release(self,p):
        if p:
            self.meter.cleanup('local_frees')
            if self.free(p):self.allocations_released=False;_RETAINED.append((self,p))
    def _check_parents(self):
        for path in (self.parent,*self.parent.parents):
            flags,_=self._call(self.attributes,str(path))
            if flags==0xffffffff or flags&0x400 or not flags&0x10:raise ProbeRejected('local_path_rejected')
        if self.root.parent!=self.parent or self.fixture.parent!=self.root:raise ProbeRejected('local_path_rejected')
    def setup(self):
        self._check_parents()
        long_name=C.create_unicode_buffer(32768)
        length,_=self._call(self.long_path,str(self.parent),long_name,len(long_name))
        if not 0<length<len(long_name) or length>180:raise ProbeRejected('local_path_rejected')
        self.parent=Path(long_name.value);self.root=self.parent/self.root.name
        self.fixture=self.root/'synthetic.bin';self._check_parents()
        token=H();self.meter.consume('opens')
        def remember(ok):
            if ok and token.value:self.active[token.value]='token'
        ok,_=self._call(self.token,self._call(self.current_process)[0],8,C.byref(token),register=remember)
        if not ok:raise ProbeRejected('native_setup_rejected')
        needed=D();ok,error=self._call(self.token_info,token,1,None,0,C.byref(needed))
        if ok or error!=122 or not 16<=needed.value<=65536:raise ProbeRejected('native_setup_rejected')
        buf=C.create_string_buffer(needed.value)
        if not self._call(self.token_info,token,1,buf,len(buf),C.byref(needed))[0]:raise ProbeRejected('native_setup_rejected')
        sid=C.cast(buf,C.POINTER(P))[0]
        length,_=self._call(self.sid_length,sid)
        if not 8<=length<=256:raise ProbeRejected('native_setup_rejected')
        self.sid=C.create_string_buffer(length)
        if not self._call(self.copy_sid,length,self.sid,sid)[0]:raise ProbeRejected('native_setup_rejected')
        text=P()
        try:
            if not self._call(self.sid_string,self.sid,C.byref(text))[0]:raise ProbeRejected('native_setup_rejected')
            private_sid=C.wstring_at(text)
        finally:self._release(text)
        if self.close(token.value) is not True:raise ProbeRejected('handle_close_unconfirmed')
        if not self._call(self.sddl,'O:'+private_sid+'D:P(A;OICI;FA;;;'+private_sid+')',1,C.byref(self.descriptor),None)[0]:
            raise ProbeRejected('native_setup_rejected')
        self.security=SECURITY(C.sizeof(SECURITY),self.descriptor,False)
        self.meter.consume('directories')
        def directory_created(ok):self.created=bool(ok)
        ok,_=self._call(self.mkdir,str(self.root),C.byref(self.security),register=directory_created)
        if not ok:raise ProbeRejected('native_setup_rejected')
    def open(self,role):
        roles=ROLE_SPECS
        if role not in roles:raise ProbeRejected('local_path_rejected')
        self._check_parents();access,share,creation,flags=roles[role];path=self.root if role=='directory' else self.fixture
        self.meter.consume('opens')
        def remember(h):
            if h and h!=self.invalid:self.active[h]=role
        h,error=self._call(self.file,str(path),access,share,C.byref(self.security) if creation==1 else None,
                           creation,flags,None,register=remember)
        if not h or h==self.invalid:
            return Open(None,{32:'sharing_violation',5:'access_denied',6:'invalid_handle',
                2:'not_found',80:'already_exists',183:'already_exists'}.get(error,'other'))
        return Open(h)
    def _security_verified(self,h):
        owner=P();acl=P();sd=P()
        try:
            result,_=self._call(self.security_info,h,1,5,C.byref(owner),None,C.byref(acl),None,C.byref(sd))
            if result or not owner or not acl or not sd:return False
            control=C.c_uint16();revision=D();ai=ACLINFO();ace=P()
            if not self._call(self.control,sd,C.byref(control),C.byref(revision))[0] or not control.value&0x1000:return False
            if not self._call(self.equal_sid,owner,self.sid)[0]:return False
            if not self._call(self.acl_info,acl,C.byref(ai),C.sizeof(ai),2)[0] or ai.count!=1:return False
            if not self._call(self.ace,acl,0,C.byref(ace))[0] or not ace:return False
            head=C.string_at(ace,8)
            if head[0]!=0 or head[1]&~3 or not 12<=int.from_bytes(head[2:4],'little')<=1024:return False
            if int.from_bytes(head[4:8],'little')!=0x1f01ff:return False
            return bool(self._call(self.equal_sid,P(ace.value+8),self.sid)[0])
        finally:self._release(sd)
    def stamp(self,h,directory=False):
        self._check_parents()
        self.meter.consume('stamps')
        info=FILEINFO();position=C.c_int64()
        if not self._call(self.info,h,C.byref(info))[0]:raise ProbeRejected('native_metadata_rejected')
        metadata=self.active.get(h) in ('metadata','control_write','control_delete')
        if metadata:position.value=-1
        if not directory and not metadata and not self._call(self.position,h,0,C.byref(position),1)[0]:raise ProbeRejected('native_metadata_rejected')
        buf=C.create_unicode_buffer(32768)
        size,_=self._call(self.final_path,h,buf,len(buf),0)
        if not 0<size<len(buf):raise ProbeRejected('native_metadata_rejected')
        text=buf.value
        if text.startswith('\\\\?\\'):text=text[4:]
        expected=self.root if directory else self.fixture
        identity=(int(info.volume),(int(info.index_high)<<32)|int(info.index_low),
                  (int(info.created.high)<<32)|int(info.created.low))
        return Stamp(identity,(int(info.size_high)<<32)|int(info.size_low),position.value,
            bool(info.attributes&0x10),self._security_verified(h),text.casefold()==str(expected).casefold(),
            bool(info.attributes&0x400),int(info.links))
    def write(self,h,data):
        if type(data) is not bytes or data!=DATA:raise ProbeRejected('native_io_rejected')
        self.meter.consume('writes');buf=C.create_string_buffer(data,len(data));count=D()
        if not self._call(self.write_file,h,buf,len(data),C.byref(count),None)[0]:raise ProbeRejected('native_io_rejected')
        return int(count.value)
    def read(self,h,n):
        if type(n) is not int or n!=84:raise ProbeRejected('native_io_rejected')
        self.meter.consume('reads');buf=C.create_string_buffer(84);count=D()
        if not self._call(self.read_file,h,buf,84,C.byref(count),None)[0] or count.value>84:raise ProbeRejected('native_io_rejected')
        return buf.raw[:count.value],int(count.value)
    def close(self,h):
        if h not in self.active:return False
        role=self.active.pop(h)
        # Always attempt cleanup even after the measured deadline; no retries.
        self.meter.cleanup('closes');C.set_last_error(0);ok=bool(self.close_handle(h));error=C.get_last_error()
        self.closes.append(dict(role=role,closed=ok,category='none' if ok else
                           {6:'invalid_handle',5:'access_denied'}.get(error,'other')))
        if not ok:self.unconfirmed.append(h);_RETAINED.append((self,h))
        return ok
    def blocking_readers(self):
        return sum(role in ('seal','reader') for role in self.active.values())
    def finish(self):
        for h in list(self.active)[::-1]:self.close(h)
        self._release(self.descriptor);self.descriptor=P()
        return dict(all_handles_closed=not self.active and not self.unconfirmed,
                    unconfirmed_handles=len(self.unconfirmed),allocations_released=self.allocations_released,
                    synthetic_directory_retained=self.created)
