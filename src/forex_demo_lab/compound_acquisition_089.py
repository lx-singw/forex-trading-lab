"""Historical injected feasibility prototype; no native entry or dated reader.

Every guard owns a new acquisition scope. Proofs may be joined inside that
scope; none are returned as a capability usable by another guard. Frozen086/087
wire, clocks, account checks, ownership and count/time limits remain unchanged.
"""
import ctypes as C
from dataclasses import dataclass, field, replace
from pathlib import PureWindowsPath
import struct

from .windows_adapter_086 import Api086, WindowsAdapter086, security086, sid086
from .native_files_065 import B,D,H,P
from .native_bindings_087 import FullGuard087
from .synchronization_083 import Guard083, require, integer, same_record, control_reason083
from .synchronization_084 import (Metadata084, Ancestor084, Spec084, READ, WRITE,
    DELETE, META, SHARE_ALL, NO_REPARSE, check_security084)
from .synchronization_086 import (Bindings086, Composite086, Pipe086, Transport086,
    FIRST_INSTANCE, check_metadata086)
from .sharing_probe_062 import ProbeRejected

PHASE='89000000000000000000000000000001'
REVIEW_DATE='2026-10-09'
PROTOTYPE_DATE='2026-10-08'
SOURCE='src/forex_demo_lab/compound_acquisition_089.py'
SECURITY_CAP=65536


def native_entry089(*args,**kwargs):
    raise ProbeRejected('native089_entry_unavailable')


def relative_security089(raw):
    """Parse caller-owned copied bytes, never arbitrary native output pointers."""
    try:
        require(type(raw) is bytes and 20<=len(raw)<=SECURITY_CAP)
        revision,sbz,control,owner,group,sacl,dacl=struct.unpack_from('<BBHIIII',raw)
        require(revision==1 and sbz==0 and control&0x8000 and sacl==0)
        intervals=[]
        def part(offset,size):
            require(type(offset) is int and offset>=20 and offset%4==0 and size>0 and offset+size<=len(raw))
            intervals.append((offset,offset+size));return raw[offset:offset+size]
        def sid(offset):
            require(offset>=20 and offset%4==0 and offset+8<=len(raw))
            return sid086(part(offset,8+4*raw[offset+1]))
        owner_sid=sid(owner)
        if group:sid(group)
        require(dacl>=20 and dacl%4==0 and dacl+8<=len(raw))
        acl_size=int.from_bytes(raw[dacl+2:dacl+4],'little')
        acl=part(dacl,acl_size)
        intervals.sort();require(all(a[1]<=b[0] for a,b in zip(intervals,intervals[1:])))
        return security086(owner_sid,control,acl)
    except Exception:raise ProbeRejected('relative_security089_rejected') from None


class Api089(Api086):
    """Same per-call clocks/budgets; bounded file security buffer consolidation."""
    def __init__(self,kernel,advapi,clock,boot_reader,get_error,set_error):
        super().__init__(kernel,advapi,clock,boot_reader,get_error,set_error)
        fn=getattr(advapi,'GetKernelObjectSecurity')
        fn.argtypes=[H,D,P,D,C.POINTER(D)];fn.restype=B
        self.functions['GetKernelObjectSecurity']=fn
    def security(self,h):
        # Named-pipe-specific documentation prescribes GetSecurityInfo. Keep its
        # original three-call bounded acquisition; do not assume generic support.
        if self.handles.get(h)=='pipe':return super().security(h)
        buf=C.create_string_buffer(SECURITY_CAP);needed=D()
        require(C.addressof(buf)%8==0)
        ok,error=self.call('GetKernelObjectSecurity',h,5,buf,len(buf),C.byref(needed))
        require(ok and error==0 and 20<=needed.value<=len(buf))
        return relative_security089(buf.raw[:needed.value])
    def ancestry(self,path):
        result=[]
        for p in PureWindowsPath(path).parents:
            h,_=self.acquire('CreateFileW',(str(p),META,7,None,3,NO_REPARSE|0x2000000,None),'ancestor')
            require(h is not None)
            try:
                identity,final,attributes,links,size=self.file_facts(h)
                result.append(Ancestor084(final,attributes,identity))
            finally:require(self.close(h))
        return tuple(result)
    def core_metadata(self,h):
        identity,final,attributes,links,size=self.file_facts(h)
        return Metadata084(identity,final,attributes,links,size,-1,self.security(h),())
    def core_path(self,path,root=False):
        h,_=self.acquire('CreateFileW',(path,META,7,None,3,NO_REPARSE|(0x2000000 if root else 0),None),'path_metadata')
        require(h is not None)
        try:return self.core_metadata(h)
        finally:require(self.close(h))


@dataclass(frozen=True)
class Composite089:
    facts: Composite086 = field(repr=False)
    controls: tuple = field(repr=False)


class Adapter089(WindowsAdapter086):
    def __init__(self,api,b,guard,wait):
        require(type(api) is Api089 and api.model_only is True and type(b) is Bindings086)
        require(type(guard) is Bridge089 and api.boot_reader is guard.boot)
        require(api.meter.clock is guard.owner.meter.clock and same_record(b.peer,guard.pins.peer))
        self.api,self.b,self.guard,self.wait_fn=api,b,guard,wait
        self.model_only=True;self.root_handle=self.file_handle=self.pipe_handle=None
        self.specs={};self.finished=False
    def inspect(self,h):
        # Only Transport089's guard-owned callback may inspect. This method does
        # not call a second bridge or keep an ancestry cache on the adapter.
        require(self.guard.active and h==self.pipe_handle and h in self.api.handles)
        path=self.b.root+'\\synthetic.bin'
        before=self.api.ancestry(path)
        pipe=self.api.pipe_facts(h,self.b)
        root_descriptor=self.api.core_metadata(self.root_handle)
        root_path=self.api.core_path(self.b.root,True)
        file_descriptor=self.api.core_metadata(self.file_handle)
        file_path=self.api.core_path(path)
        controls=[]
        for handle,spec in self.owner.live.items():
            if spec.role.startswith('control_'):
                # DELETE-only handles need not grant READ_CONTROL. Query their
                # identity/path/size on the actual control handle; security and
                # complete ancestry come from the same freshly proved object
                # through the already-owned metadata handle in this scope.
                identity,final,attributes,links,size=self.api.file_facts(handle)
                controls.append((handle,Metadata084(identity,final,attributes,links,size,-1,
                    file_descriptor.security,())))
        after=self.api.ancestry(path)
        require(before==after)
        def parents(m,root=False):return replace(m,ancestors=after[1:] if root else after)
        facts=Composite086(Guard083(),pipe,parents(root_descriptor,True),parents(root_path,True),
            parents(file_descriptor),parents(file_path))
        require(set(self.api.handles)==set(self.owner.live))
        return Composite089(facts,tuple((h,parents(m)) for h,m in controls))


class Bridge089(FullGuard087):
    """Fresh SDK/image/source proofs surround each single raw acquisition."""
    def __init__(self,owner,boot,source_binding):
        super().__init__(owner,boot)
        require(type(source_binding) is tuple and len(source_binding)==2)
        from .synchronization_083 import digest
        require(type(source_binding[0]) is str and bool(source_binding[0]));digest(source_binding[1])
        self.source_binding=source_binding;self.fixed_source=source_binding;self.active=False
    def sources_now(self):
        require(self.source_binding==self.fixed_source)
        for path,sha in (*self.pins.hashes.values(),*self.pins.sources.values(),self.source_binding):
            require(self.reader.hash_file(path)==sha)
    def acquire(self,raw,validate):
        try:
            require(not self.stopped and not self.active and self.calls<96);self.calls+=1;self.active=True
            self.owner.meter.check();self.graph();self.identity();self.account_metadata()
            require(self.boot()==self.pins.peer.boot);self.sources_now()
            value=raw();validate(value)
            self.sources_now();self.identity();self.account_metadata();self.graph();self.owner.meter.check()
            return value
        except (Exception,KeyboardInterrupt):
            self.stopped=True;raise ProbeRejected('compound089_guard_rejected') from None
        finally:self.active=False
    def __call__(self):
        raise ProbeRejected('compound089_scope_required')


class Transport089(Transport086):
    """Historical wire with compound observational proofs, not a new reader."""
    def __init__(self,b,clock,guard,factory):
        require(type(guard) is Bridge089)
        super().__init__(b,clock,guard,factory)
    def validate(self,result):
        if self.pipe_handle is None:require(result is None);return
        backend=self.owner.backend
        require(backend.guard is self.guard and type(backend.api) is Api089)
        require(backend.api.boot_reader is self.guard.boot and backend.api.clock==backend.api.meter.check)
        require(backend.api.meter.clock is self.clock and self.guard.owner.meter.clock is self.clock)
        require(type(result) is Composite089);p=result.facts
        require(type(p) is Composite086 and same_record(p.account,Guard083()))
        pipe=p.pipe;require(type(pipe) is Pipe086 and pipe.name==self.b.pipe)
        check_security084(pipe.security,self.b.owner_sid);require(same_record(pipe.client,self.b.peer))
        for k in ('pipe_type','read_mode','wait_mode','maximum_instances','creation_flags','pipe_mode_flags'):
            integer(getattr(pipe,k));require(getattr(pipe,k)==getattr(Pipe086(pipe.name,pipe.security,pipe.client),k))
        for root,desc,path in ((True,p.root_descriptor,p.root_path),(False,p.file_descriptor,p.file_path)):
            check_metadata086(desc,self.b,root);check_metadata086(path,self.b,root);require(same_record(desc,path))
        for spec in self.owner.live.values():
            require(spec.role in ('root','metadata','pipe','control_write','control_delete'))
            if spec.role=='pipe':expected=Spec084('pipe',self.b.pipe,READ|WRITE,0,1,FIRST_INSTANCE)
            elif spec.role.startswith('control_'):
                expected=Spec084(spec.role,self.b.root+'\\synthetic.bin',WRITE if spec.role=='control_write' else DELETE,7,3,NO_REPARSE)
            else:
                expected=Spec084(spec.role,self.b.root if spec.role=='root' else self.b.root+'\\synthetic.bin',META,SHARE_ALL,3,
                    NO_REPARSE|(0x2000000 if spec.role=='root' else 0))
            require(same_record(spec,expected))
        roles=sorted(s.role for s in self.owner.live.values())
        require(all(roles.count(x)==1 for x in ('metadata','pipe','root')) and len(roles)<=4)
        require(self.owner.live[self.pipe_handle].role=='pipe')
        require(type(result.controls) is tuple)
        required={h for h,s in self.owner.live.items() if s.role.startswith('control_')}
        require(len(result.controls)==len(required) and {h for h,m in result.controls}==required)
        for h,m in result.controls:
            check_metadata086(m,self.b);require(same_record(m,p.file_descriptor))
    def full_guard(self):
        self.bump('guards');start=self.m.check()[2]
        require(self.guard.owner.meter.clock is self.clock)
        self.guard.acquire(lambda:self.owner.backend.inspect(self.pipe_handle) if self.pipe_handle is not None else None,
            self.validate)
        end=self.m.check()[2];self.trace.append((start,end));return end
    def control(self,stage,access):
        try:
            expected=[(s,a) for s in ('pre','independent','post') for a in ('write','delete')]
            require(len(self.probes)<6 and expected[len(self.probes)]==(stage,access) and self.lease is None)
            backend=self.owner.backend
            spec=Spec084('control_'+access,self.b.root+'\\synthetic.bin',WRITE if access=='write' else DELETE,7,3,NO_REPARSE)
            # Each open still has full before/after proofs. Its trailing guard
            # stamps any acquired control handle against the same current file.
            opened,start,end,after=self.control_call(lambda:backend.open_control(spec,self.owner))
            require(type(opened) is tuple and len(opened)==2 and type(opened[1]) is int)
            h,error=opened
            if stage=='independent':
                require(h is None and error==32 and control_reason083(start,end,after,self.hold_start)==0)
            else:
                require(error==0 and self.owner.live.get(h)==spec)
                def close():
                    self.owner.live.pop(h);self.owner.attempts+=1
                    try:ok=backend.close(h) is True
                    except (Exception,KeyboardInterrupt):ok=False
                    if not ok:self.owner.unconfirmed+=1
                    require(ok)
                # Before-close guard stamps the live control again; after-close
                # guard freshly proves path/descriptor/ACL/ancestry/account.
                self.control_call(close)
            final=self.m.check()[2]
            if stage=='independent':require(final<self.hold_start+29750)
            if stage=='post':require(start>self.hold_end+250)
            self.probes.append(dict(stage=stage,access=access,error=error,start=start,end=end,guard_end=after,
                final_guard_end=final,same_file_before_after=True,companion_blockers=0))
        except (Exception,KeyboardInterrupt):self.stopped=True;raise
    def summary(self):
        result=super().summary();result.update(version='compound_acquisition_model_089_v1',
            guard_group='one_fresh_bridge_around_raw_acquisition',historical_fixture_date=PROTOTYPE_DATE,
            new_reader_implemented=False,new_runtime_admission=False)
        return result
