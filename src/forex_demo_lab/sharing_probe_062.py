"""Synthetic local Win32 file-sharing experiment. No SDK, MT5 or permissions."""
import ctypes as C
from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import os
from pathlib import Path
import time
import uuid

DATE = '2026-10-07'
PHASE = '62000000000000000000000000000001'
DATA = bytes((i*37+11)%256 for i in range(84))  # Not a receipt or request.
_RETAINED = []  # Unconfirmed closes: keep ownership until process teardown.


class ProbeRejected(ValueError): pass


class Meter:
    def __init__(self, clock):
        self.clock=clock;self.first=self.last=None
        self.opens=self.writes=self.reads=self.directories=0
        self.elapsed_us=0;self.overrun=False
        self.check()
    def check(self):
        value=self.clock()
        if type(value) is not tuple or len(value)!=2 or any(type(x) is not int or x<0 for x in value):
            raise ProbeRejected('clock_invalid')
        if datetime.fromtimestamp(value[0]/1000,timezone.utc).date().isoformat()!=DATE:
            raise ProbeRejected('declared_date_expired')
        if self.first is None:self.first=self.last=value
        if any(a<b for a,b in zip(value,self.last)):raise ProbeRejected('clock_reversed')
        wall,mono=value[0]-self.first[0],value[1]-self.first[1]
        self.elapsed_us=mono//1000;self.last=value
        if abs(wall-mono//1000000)>1000:raise ProbeRejected('clock_discontinuity')
        if wall>=60000 or mono>=60000000000:
            self.overrun=True;raise ProbeRejected('measured_deadline_exceeded')
    def consume(self, kind):
        limits={'opens':16,'writes':1,'reads':2,'directories':1}
        self.check()
        if kind not in limits or getattr(self,kind)>=limits[kind]:raise ProbeRejected('operation_budget_exhausted')
        setattr(self,kind,getattr(self,kind)+1)


@dataclass(frozen=True)
class Open:
    handle: object = field(repr=False)
    category: str = 'none'


@dataclass(frozen=True)
class Stamp:
    identity: tuple = field(repr=False)
    size: int
    position: int
    directory: bool = False
    security_verified: bool = False
    path_verified: bool = False
    reparse: bool = True
    links: int = 1


def validate_stamp(s, size, position, directory=False):
    if (type(s) is not Stamp or type(s.identity) is not tuple or len(s.identity)!=3 or
            any(type(x) is not int or x<=0 for x in s.identity) or
            type(s.size) is not int or s.size!=size or type(s.position) is not int or s.position!=position or
            type(s.directory) is not bool or s.directory!=directory or
            s.security_verified is not True or s.path_verified is not True or s.reparse is not False or
            type(s.links) is not int or s.links!=1):
        raise ProbeRejected('private_file_binding_rejected')
    return s.identity


def run_probe(api, meter):
    """Injected tests use the same sequence; native backend retains all handles."""
    result=dict(version='sharing_probe_062_v1',phase=PHASE,declared_date=DATE,
        passed=False,stop_reason=None,observations=[],read_counts=[],same_file_verified=False,
        security_path_verified=False,synthetic_sha256=hashlib.sha256(DATA).hexdigest(),
        sdk_connections=0,mt5_invocations=0,receipt_permissions=0,quote_reads=0,history_reads=0,
        orders=0,orders_available=False,fresh_performance_eligible=False,annual_eligible=False,
        native_mql_verified=False,blocking_preemption_verified=False)
    def call(fn,*args):
        meter.check();value=fn(*args);meter.check();return value
    def opened(role, expected='none'):
        r=call(api.open,role)
        if type(r) is not Open:raise ProbeRejected('open_schema_rejected')
        result['observations'].append(dict(role=role,category=r.category if r.category in
            ('none','sharing_violation','access_denied','invalid_handle','already_exists','not_found','other') else 'other'))
        if r.category!=expected or (r.handle is None)!=(expected!='none'):
            raise ProbeRejected('expected_sharing_outcome_rejected')
        return r.handle
    try:
        call(api.setup)
        directory=opened('directory')
        # Directory sizes/link counts are not regular-file EOF evidence.
        ds=call(api.stamp,directory,True)
        if (type(ds) is not Stamp or ds.directory is not True or ds.security_verified is not True or
                ds.path_verified is not True or ds.reparse is not False):
            raise ProbeRejected('private_directory_binding_rejected')
        writer=opened('writer')
        initial=validate_stamp(call(api.stamp,writer),0,0)
        count=call(api.write,writer,DATA)
        if type(count) is not int or count!=84:raise ProbeRejected('short_write_rejected')
        if validate_stamp(call(api.stamp,writer),84,84)!=initial:raise ProbeRejected('file_identity_changed')
        opened('seal_while_writer','sharing_violation')
        if call(api.close,writer) is not True:raise ProbeRejected('handle_close_unconfirmed')
        seal=opened('seal');peer=opened('reader')
        for h in (seal,peer):
            if validate_stamp(call(api.stamp,h),84,0)!=initial:raise ProbeRejected('file_identity_changed')
        opened('writer_while_sealed','sharing_violation')
        opened('delete_while_sealed','sharing_violation')
        for h in (seal,peer):
            raw,count=call(api.read,h,85)
            if type(raw) is not bytes or type(count) is not int or count!=84 or raw!=DATA:
                raise ProbeRejected('synthetic_read_rejected')
            result['read_counts'].append(count)
            if validate_stamp(call(api.stamp,h),84,84)!=initial:raise ProbeRejected('file_identity_changed')
        result['same_file_verified']=result['security_path_verified']=True
        result['passed']=True
    except Exception as exc:
        allowed={'clock_invalid','clock_reversed','clock_discontinuity','declared_date_expired',
            'measured_deadline_exceeded','operation_budget_exhausted','open_schema_rejected',
            'expected_sharing_outcome_rejected','private_directory_binding_rejected',
            'private_file_binding_rejected','short_write_rejected','file_identity_changed',
            'handle_close_unconfirmed','synthetic_read_rejected','native_setup_rejected',
            'native_metadata_rejected','native_io_rejected','local_path_rejected'}
        result['stop_reason']=str(exc) if str(exc) in allowed else 'probe_failed_details_redacted'
    finally:
        try:
            cleanup=api.finish()
            keys={'all_handles_closed','unconfirmed_handles','allocations_released','synthetic_directory_retained'}
            if (type(cleanup) is not dict or set(cleanup)!=keys or
                    any(type(cleanup[k]) is not bool for k in keys-{'unconfirmed_handles'}) or
                    type(cleanup['unconfirmed_handles']) is not int or not 0<=cleanup['unconfirmed_handles']<=16):
                raise ValueError()
            result['cleanup']=cleanup
            if not cleanup['all_handles_closed'] or cleanup['unconfirmed_handles'] or not cleanup['allocations_released']:
                result['passed']=False;result['stop_reason']='cleanup_unconfirmed'
        except Exception:
            result['passed']=False;result['stop_reason']='cleanup_failed_details_redacted'
            result['cleanup']=None
        try:meter.check()
        except Exception:
            result['passed']=False
            if result['stop_reason'] is None:result['stop_reason']='post_cleanup_clock_rejected'
        result.update(handle_open_attempts=meter.opens,write_attempts=meter.writes,
            read_attempts=meter.reads,directory_attempts=meter.directories,
            elapsed_us=meter.elapsed_us,measured_overrun=meter.overrun)
    return result


# Fixed-width ctypes ABI, also inspectable in Linux pure tests.
D=C.c_uint32;B=C.c_int32;H=C.c_void_p;P=C.c_void_p
class FILETIME(C.Structure):_fields_=[('low',D),('high',D)]
class FILEINFO(C.Structure):
    _fields_=[('attributes',D),('created',FILETIME),('accessed',FILETIME),('written',FILETIME),
              ('volume',D),('size_high',D),('size_low',D),('links',D),('index_high',D),('index_low',D)]
class SECURITY(C.Structure):_fields_=[('length',D),('descriptor',P),('inherit',B)]
class ACLINFO(C.Structure):_fields_=[('count',D),('used',D),('free',D)]


class NativeFiles062:
    """Direct local synchronous Win32 only. No events or asynchronous IO.

    Timer checks cannot interrupt a native call. No speculative retries, file
    deletes, rename, recursive cleanup or unrelated directory operations.
    """
    def __init__(self,meter):
        if os.name!='nt' or C.sizeof(P)!=8:raise ProbeRejected('windows_x64_required')
        self.meter=meter;self.active={};self.unconfirmed=[];self.closes=[]
        self.allocations_released=True;self.descriptor=P();self.created=False
        self.k=C.WinDLL('kernel32',use_last_error=True);self.a=C.WinDLL('advapi32',use_last_error=True)
        def bind(dll,name,args,result):
            f=getattr(dll,name);f.argtypes=args;f.restype=result;return f
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
        self.invalid=C.c_void_p(-1).value
        raw_parent=os.environ.get('TEMP')
        if type(raw_parent) is not str or not raw_parent or not Path(raw_parent).is_absolute():
            raise ProbeRejected('local_path_rejected')
        parent=Path(raw_parent)
        if not parent.drive or str(parent).startswith('\\\\') or len(str(parent))>140:
            raise ProbeRejected('local_path_rejected')
        self.parent=parent
        self.root=parent/('ForexDemoSharing062-'+PHASE+'-'+uuid.uuid4().hex)
        self.fixture=self.root/'synthetic.bin'
    def _call(self,fn,*args,register=None):
        self.meter.check();C.set_last_error(0)
        result=fn(*args);error=C.get_last_error()
        if register is not None:register(result)
        self.meter.check()
        return result,error
    def _release(self,p):
        if p:
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
        if not 0<length<len(long_name) or length>140:raise ProbeRejected('local_path_rejected')
        self.parent=Path(long_name.value);self.root=self.parent/self.root.name
        self.fixture=self.root/'synthetic.bin';self._check_parents()
        token=H();self.meter.consume('opens')
        def remember(ok):
            if ok and token.value:self.active[token.value]='token'
        ok,_=self._call(self.token,self.current_process(),8,C.byref(token),register=remember)
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
        roles={'directory':(0x20080,3,3,0x02200000,self.root),
            'writer':(0xC0000000,3,1,0x00200080,self.fixture),
            'seal_while_writer':(0x80000000,1,3,0x00200080,self.fixture),
            'seal':(0x80000000,1,3,0x00200080,self.fixture),
            'reader':(0x80000000,1,3,0x00200080,self.fixture),
            'writer_while_sealed':(0x40000000,3,3,0x00200080,self.fixture),
            'delete_while_sealed':(0x10000,7,3,0x00200080,self.fixture)}
        if role not in roles:raise ProbeRejected('local_path_rejected')
        self._check_parents();access,share,creation,flags,path=roles[role]
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
        info=FILEINFO();position=C.c_int64()
        if not self._call(self.info,h,C.byref(info))[0]:raise ProbeRejected('native_metadata_rejected')
        if not directory and not self._call(self.position,h,0,C.byref(position),1)[0]:raise ProbeRejected('native_metadata_rejected')
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
        if type(n) is not int or n!=85:raise ProbeRejected('native_io_rejected')
        self.meter.consume('reads');buf=C.create_string_buffer(85);count=D()
        if not self._call(self.read_file,h,buf,85,C.byref(count),None)[0] or count.value>85:raise ProbeRejected('native_io_rejected')
        return buf.raw[:count.value],int(count.value)
    def close(self,h):
        if h not in self.active:return False
        role=self.active.pop(h)
        # Always attempt cleanup even after the measured deadline; no retries.
        C.set_last_error(0);ok=bool(self.close_handle(h));error=C.get_last_error()
        self.closes.append(dict(role=role,closed=ok,category='none' if ok else
                           {6:'invalid_handle',5:'access_denied'}.get(error,'other')))
        if not ok:self.unconfirmed.append(h);_RETAINED.append((self,h))
        return ok
    def finish(self):
        for h in list(self.active)[::-1]:self.close(h)
        self._release(self.descriptor);self.descriptor=P()
        return dict(all_handles_closed=not self.active and not self.unconfirmed,
                    unconfirmed_handles=len(self.unconfirmed),allocations_released=self.allocations_released,
                    synthetic_directory_retained=self.created)
