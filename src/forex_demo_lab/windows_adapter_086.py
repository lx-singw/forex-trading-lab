"""Concrete Win64 syscall acquisition source, callable-table tests only.

No DLL loader or native entry authority exists in this phase. Tables must be
explicitly model-only. A later separately frozen adapter/entry must bind actual
DLLs, full metadata/image/SDK/source guards and an independently reviewed boot
proof. No native boot fingerprint is fabricated or returned from cached bindings.
"""
import ctypes as C
from dataclasses import replace
from pathlib import PureWindowsPath

from .native_files_065 import D,B,H,P,FILETIME,FILEINFO,SECURITY
from .synchronization_084 import Peer084,Security084,Ace084,Metadata084,Ancestor084,Spec084
from .synchronization_086 import (Bindings086,Pipe086,Composite086,Read086,Write086,
    Guard083,READ,WRITE,META,SHARE_ALL,NO_REPARSE,FIRST_INSTANCE,REJECT_REMOTE,
    require,integer,same_record,check_metadata086,identity086,Meter083)
from .sharing_probe_062 import ProbeRejected

_RETAINED086=[]
NATIVE_CAPS=dict(calls=16384,peak_handles=16,close_attempts=4096,allocations=4096,token_bytes=65536)
ABI={
 'CreateFileW':('k',[C.c_wchar_p,D,D,P,D,D,H],H),
 'CreateDirectoryW':('k',[C.c_wchar_p,P],B),
 'CreateNamedPipeW':('k',[C.c_wchar_p,D,D,D,D,D,D,P],H),
 'ConnectNamedPipe':('k',[H,P],B),
 'ReadFile':('k',[H,P,D,C.POINTER(D),P],B),
 'WriteFile':('k',[H,P,D,C.POINTER(D),P],B),
 'CloseHandle':('k',[H],B),
 'GetFileInformationByHandle':('k',[H,C.POINTER(FILEINFO)],B),
 'GetFinalPathNameByHandleW':('k',[H,C.c_wchar_p,D,D],D),
 'GetNamedPipeInfo':('k',[H,*[C.POINTER(D)]*4],B),
 'GetNamedPipeHandleStateW':('k',[H,*[C.POINTER(D)]*4,P,D],B),
 'GetNamedPipeClientProcessId':('k',[H,C.POINTER(D)],B),
 'OpenProcess':('k',[D,B,D],H),
 'GetProcessTimes':('k',[H,*[C.POINTER(FILETIME)]*4],B),
 'ProcessIdToSessionId':('k',[D,C.POINTER(D)],B),
 'OpenProcessToken':('a',[H,D,C.POINTER(H)],B),
 'GetTokenInformation':('a',[H,D,P,D,C.POINTER(D)],B),
 'GetSecurityInfo':('a',[H,D,D,C.POINTER(P),P,C.POINTER(P),P,C.POINTER(P)],D),
 'GetSecurityDescriptorControl':('a',[P,C.POINTER(C.c_uint16),C.POINTER(D)],B),
 'GetSecurityDescriptorLength':('a',[P],D),
 'ConvertStringSecurityDescriptorToSecurityDescriptorW':('a',[C.c_wchar_p,D,C.POINTER(P),P],B),
 'ConvertSidToStringSidW':('a',[P,C.POINTER(P)],B),
 'LocalFree':('k',[P],P),
}


def native_entry086(*args,**kwargs):
    raise ProbeRejected('native086_entry_unavailable')


def sid086(raw):
    require(type(raw) is bytes and 8<=len(raw)<=68 and raw[0]==1 and raw[1]<=15)
    require(len(raw)==8+4*raw[1]);return raw


def security086(owner,control,acl):
    """Parse bounded raw binary ACL; never turn a capability boolean into facts."""
    sid086(owner);integer(control,0,65535)
    require(type(acl) is bytes and 20<=len(acl)<=1024 and acl[0] in (2,4))
    require(acl[1]==0 and int.from_bytes(acl[2:4],'little')==len(acl))
    require(int.from_bytes(acl[4:6],'little')==1 and acl[6:8]==b'\0\0')
    size=int.from_bytes(acl[10:12],'little');require(size==len(acl)-8)
    ace=Ace084(acl[8],acl[9],int.from_bytes(acl[12:16],'little'),sid086(acl[16:]))
    return Security084(owner,control,(ace,))


class Api086:
    """Fixed-width ABI with bounded calls and before-error acquisition ownership.

    get_error/set_error are ctypes last-error equivalents from the injected
    table. All HANDLE/LocalAlloc acquisitions register BEFORE clock validation.
    Model fixtures use real ctypes buffers, never load a system DLL.
    """
    def __init__(self,kernel,advapi,clock,boot_reader,get_error,set_error):
        require(getattr(kernel,'model_only',None) is True and getattr(advapi,'model_only',None) is True)
        require(C.sizeof(P)==8 and C.sizeof(D)==4 and C.sizeof(B)==4)
        self.model_only=True;self.meter=Meter083(clock);self.clock,self.boot_reader=self.meter.check,boot_reader
        self.get_error,self.set_error=get_error,set_error
        self.functions={};self.handles={};self.allocations={};self.calls=0;self.close_attempts=0
        self.unconfirmed=0;self.frees_unconfirmed=0;self.invalid=C.c_void_p(-1).value
        self.allocation_attempts=0
        for n,(dll,args,result) in ABI.items():
            fn=getattr(kernel if dll=='k' else advapi,n);fn.argtypes=args;fn.restype=result;self.functions[n]=fn
    def call(self,n,*args,remember=None):
        require(self.calls<NATIVE_CAPS['calls']);self.clock();self.calls+=1;self.set_error(0)
        result=self.functions[n](*args);error=self.get_error()
        if remember is not None:remember(result)
        self.clock();return result,error
    def remember(self,h,role):
        if h and h!=self.invalid:
            require(h not in self.handles)
            self.handles[h]=role
            require(len(self.handles)<=NATIVE_CAPS['peak_handles'])
    def acquire(self,n,args,role,owner=None,spec=None):
        def remember(h):
            self.remember(h,role)
            if h and h!=self.invalid and owner is not None:owner.register(h,spec)
        h,error=self.call(n,*args,remember=remember)
        return (None,error) if not h or h==self.invalid else (h,0)
    def close(self,h):
        require(h in self.handles and self.close_attempts<NATIVE_CAPS['close_attempts'])
        self.handles.pop(h);self.close_attempts+=1
        # Owned cleanup must run even after clock/account rejection; do not retry.
        try:ok=bool(self.functions['CloseHandle'](h))
        except (Exception,KeyboardInterrupt):ok=False
        if not ok:self.unconfirmed+=1;_RETAINED086.append((self,h))
        return ok
    def remember_allocation(self,p):
        if p.value:
            require(p.value not in self.allocations)
            self.allocations[p.value]=p
            self.allocation_attempts+=1
            require(len(self.allocations)<=16 and self.allocation_attempts<=NATIVE_CAPS['allocations'])
    def release(self,p):
        if p.value and p.value in self.allocations:
            self.allocations.pop(p.value)
            try:ok=not self.functions['LocalFree'](p)
            except (Exception,KeyboardInterrupt):ok=False
            if not ok:self.frees_unconfirmed+=1;_RETAINED086.append((self,p))
            return ok
        return not p.value
    def ptr_bytes(self,p,lo,hi,n):
        require(type(n) is int and 0<n<=65536 and lo<=p<=hi and p+n<=hi)
        return C.string_at(p,n)
    def raw_sid(self,p,lo,hi):
        head=self.ptr_bytes(p,lo,hi,8);n=8+4*head[1]
        return sid086(self.ptr_bytes(p,lo,hi,n))
    def security(self,h):
        owner,acl,sd=P(),P(),P()
        try:
            result,_=self.call('GetSecurityInfo',h,1,5,C.byref(owner),None,C.byref(acl),None,C.byref(sd),
                remember=lambda r:self.remember_allocation(sd))
            require(result==0 and owner.value and acl.value and sd.value)
            size,_=self.call('GetSecurityDescriptorLength',sd);require(20<=size<=65536)
            lo,hi=sd.value,sd.value+size;raw_owner=self.raw_sid(owner.value,lo,hi)
            head=self.ptr_bytes(acl.value,lo,hi,8);acl_size=int.from_bytes(head[2:4],'little')
            control=C.c_uint16();revision=D()
            require(self.call('GetSecurityDescriptorControl',sd,C.byref(control),C.byref(revision))[0])
            return security086(raw_owner,int(control.value),self.ptr_bytes(acl.value,lo,hi,acl_size))
        finally:require(self.release(sd))
    def token_data(self,token,kind):
        needed=D();ok,error=self.call('GetTokenInformation',token,kind,None,0,C.byref(needed))
        require(not ok and error==122 and 16<=needed.value<=NATIVE_CAPS['token_bytes'])
        buf=C.create_string_buffer(needed.value)
        require(self.call('GetTokenInformation',token,kind,buf,len(buf),C.byref(needed))[0])
        require(16<=needed.value<=len(buf));return buf,int(needed.value)
    def peer(self,pipe):
        pid=D();require(self.call('GetNamedPipeClientProcessId',pipe,C.byref(pid))[0] and pid.value>0)
        proc,_=self.acquire('OpenProcess',(0x1000,False,pid.value),'peer_process');require(proc is not None)
        token=H()
        try:
            times=[FILETIME() for _ in range(4)];session=D()
            require(self.call('GetProcessTimes',proc,*[C.byref(x) for x in times])[0])
            require(self.call('ProcessIdToSessionId',pid.value,C.byref(session))[0])
            require(self.call('OpenProcessToken',proc,8,C.byref(token),
                remember=lambda ok:self.remember(token.value,'peer_token') if ok else None)[0])
            buf,size=self.token_data(token,2);base=C.addressof(buf)
            count=int.from_bytes(buf.raw[:4],'little');require(count<=256 and 8+count*16<=size)
            logons=[]
            for i in range(count):
                raw=buf.raw[8+i*16:24+i*16];pointer=int.from_bytes(raw[:8],'little')
                flags=int.from_bytes(raw[8:12],'little')
                if flags&0xC0000000==0xC0000000:logons.append(self.raw_sid(pointer,base,base+size))
            require(len(logons)==1)
            # No assumed/cached boot bytes: a separate reviewed fresh proof is mandatory.
            boot=self.boot_reader();require(type(boot) is bytes and 8<=len(boot)<=256)
            return Peer084(int(pid.value),(int(times[0].high)<<32)|int(times[0].low),int(session.value),logons[0],boot)
        finally:
            ok=True
            for h in (token.value,proc):
                if h in self.handles:ok=self.close(h) and ok
            require(ok)
    def file_facts(self,h):
        info=FILEINFO();require(self.call('GetFileInformationByHandle',h,C.byref(info))[0])
        buf=C.create_unicode_buffer(512);n,_=self.call('GetFinalPathNameByHandleW',h,buf,len(buf),0)
        require(0<n<len(buf));path=buf.value
        require(path.startswith('\\\\?\\') and not path.startswith('\\\\?\\UNC\\'));path=path[4:]
        return ((int(info.volume),(int(info.index_high)<<32)|int(info.index_low),
            (int(info.created.high)<<32)|int(info.created.low)),path,int(info.attributes),int(info.links),
            (int(info.size_high)<<32)|int(info.size_low))
    def metadata(self,h,path,root=False):
        ident,final,attrs,links,size=self.file_facts(h);ancestors=[]
        for p in PureWindowsPath(path).parents:
            temp,_=self.acquire('CreateFileW',(str(p),META,7,None,3,NO_REPARSE|0x2000000,None),'ancestor')
            require(temp is not None)
            try:
                aid,ap,aa,al,az=self.file_facts(temp)
                ancestors.append(Ancestor084(ap,aa,aid))
            finally:require(self.close(temp))
        return Metadata084(ident,final,attrs,links,size,-1,self.security(h),tuple(ancestors))
    def path_metadata(self,path,root=False):
        h,_=self.acquire('CreateFileW',(path,META,7,None,3,NO_REPARSE|(0x2000000 if root else 0),None),'path_metadata')
        require(h is not None)
        try:return self.metadata(h,path,root)
        finally:require(self.close(h))
    def pipe_facts(self,h,b):
        flags,outbuf,inbuf,maximum,state,instances=(D() for _ in range(6))
        require(self.call('GetNamedPipeInfo',h,C.byref(flags),C.byref(outbuf),C.byref(inbuf),C.byref(maximum))[0])
        require(self.call('GetNamedPipeHandleStateW',h,C.byref(state),C.byref(instances),None,None,None,0)[0])
        require(flags.value==5 and state.value==3 and maximum.value==instances.value==1)
        return Pipe086(b.pipe,self.security(h),self.peer(h),int(flags.value&4),int(state.value&2),
            int(state.value&1),int(maximum.value),FIRST_INSTANCE,4|2|1|REJECT_REMOTE)
    def read(self,h,n):
        require(type(n) is int and n==145);buf=C.create_string_buffer(n);count=D()
        ok,error=self.call('ReadFile',h,buf,n,C.byref(count),None);require(count.value<=n)
        return Read086(bool(ok),0 if ok else int(error),int(count.value),buf.raw[:count.value],n)
    def write(self,h,raw):
        require(type(raw) is bytes and len(raw) in (84,144));buf=C.create_string_buffer(raw,len(raw));count=D()
        ok,error=self.call('WriteFile',h,buf,len(raw),C.byref(count),None)
        return Write086(bool(ok),0 if ok else int(error),int(count.value))
    def private_descriptor(self,sid):
        sid086(sid);binary=C.create_string_buffer(sid,len(sid));text=P();sd=P()
        try:
            require(self.call('ConvertSidToStringSidW',binary,C.byref(text),
                remember=lambda r:self.remember_allocation(text))[0])
            value=C.wstring_at(text);require(value.startswith('S-1-') and len(value)<=184)
            require(self.call('ConvertStringSecurityDescriptorToSecurityDescriptorW',
                'O:'+value+'D:P(A;OICI;FA;;;'+value+')',1,C.byref(sd),None,
                remember=lambda r:self.remember_allocation(sd))[0])
            return sd
        finally:require(self.release(text))
    def finish(self):
        ok=True
        for h in list(self.handles):ok=self.close(h) and ok
        for p in list(self.allocations.values()):ok=self.release(p) and ok
        return ok and self.unconfirmed==self.frees_unconfirmed==0


class WindowsAdapter086:
    """Concrete source using Api086; only model-only callable tables accepted."""
    def __init__(self,api,b,account_guard,wait):
        require(type(api) is Api086 and api.model_only is True and type(b) is Bindings086)
        self.api,self.b,self.guard,self.wait_fn=api,b,account_guard,wait
        self.model_only=True;self.root_handle=self.file_handle=self.pipe_handle=None;self.specs={};self.finished=False
    def factory(self,owner,b):
        require(b is self.b);owner.install(self);self.owner=owner;sd=P()
        try:
            sd=self.api.private_descriptor(b.owner_sid);sec=SECURITY(C.sizeof(SECURITY),sd,False)
            ok,error=self.api.call('CreateDirectoryW',b.root,C.byref(sec));require(ok and error==0)
            path=b.root+'\\synthetic.bin'
            creator,_=self.api.acquire('CreateFileW',(path,READ|WRITE,0,C.byref(sec),1,NO_REPARSE,None),'creator')
            require(creator is not None)
            try:
                data=bytes((17*i+29)%256 for i in range(84));w=self.api.write(creator,data)
                require(w.succeeded and w.count==84)
            finally:require(self.api.close(creator))
            for role,p,flags in (('root',b.root,NO_REPARSE|0x2000000),('metadata',path,NO_REPARSE)):
                spec=Spec084(role,p,META,7,3,flags)
                h,_=self.api.acquire('CreateFileW',(p,META,7,None,3,flags,None),role,owner,spec)
                require(h is not None);self.specs[h]=spec
                if role=='root':self.root_handle=h
                else:self.file_handle=h
            spec=Spec084('pipe',b.pipe,READ|WRITE,0,1,FIRST_INSTANCE)
            h,_=self.api.acquire('CreateNamedPipeW',(b.pipe,3|FIRST_INSTANCE,4|2|1|REJECT_REMOTE,1,1024,1024,50,C.byref(sec)),
                'pipe',owner,spec);require(h is not None);self.pipe_handle=h;self.specs[h]=spec
            connected=False
            for _ in range(64):
                ok,error=self.api.call('ConnectNamedPipe',h,None)
                if not ok and error==535:connected=True;break
                # NOWAIT's initial TRUE only changes availability, not connection.
                require(ok and error==0 or not ok and error==536);self.wait_fn(50)
            require(connected)
            root=self.api.metadata(self.root_handle,b.root,True);file=self.api.metadata(self.file_handle,path)
            # Identity of a CREATE_NEW object cannot be predicted before creation.
            prepared=replace(b,root_identity=root.identity,file_identity=file.identity,
                ancestor_identities=tuple(a.identity for a in root.ancestors))
            check_metadata086(root,prepared,True);check_metadata086(file,prepared)
            self.b=prepared;return self,h,prepared
        finally:require(self.api.release(sd))
    def inspect(self,h):
        require(h==self.pipe_handle and h in self.api.handles)
        account=self.guard();require(same_record(account,Guard083()))
        result=Composite086(account,self.api.pipe_facts(h,self.b),
            self.api.metadata(self.root_handle,self.b.root,True),self.api.path_metadata(self.b.root,True),
            self.api.metadata(self.file_handle,self.b.root+'\\synthetic.bin'),self.path_metadata())
        require(set(self.api.handles)==set(self.owner.live))
        return result
    def path_metadata(self):return self.api.path_metadata(self.b.root+'\\synthetic.bin')
    def open_control(self,spec,owner):
        h,error=self.api.acquire('CreateFileW',(spec.path,spec.access,spec.share,None,3,spec.flags,None),spec.role,owner,spec)
        if h is not None:self.specs[h]=spec
        return h,error
    def control_metadata(self,h):return self.api.metadata(h,self.b.root+'\\synthetic.bin')
    def read(self,h,n):return self.api.read(h,n)
    def write(self,h,raw):return self.api.write(h,raw)
    def wait(self,ms):return self.wait_fn(ms)
    def close(self,h):self.specs.pop(h,None);return self.api.close(h)
    def finish(self):
        require(not self.finished);self.finished=True;return self.api.finish()
