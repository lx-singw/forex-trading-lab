import ctypes as C
from dataclasses import replace
import struct
import unittest

from forex_demo_lab.windows_adapter_086 import *
from forex_demo_lab.synchronization_086 import Transport086,WIRE,encode086
from test_synchronization_086 import bindings086,Clock086

SID=b'\x01\x01'+b'\0'*5+b'\x05'+struct.pack('<I',21)


class Function:
    def __init__(self,fn):self.fn=fn
    def __call__(self,*args):return self.fn(*args)


class Table:
    model_only=True
    def __init__(self,world):self.world=world;self.functions={}
    def __getattr__(self,n):
        if n not in self.functions:self.functions[n]=Function(lambda *a:self.world.call(n,*a))
        return self.functions[n]


class World:
    def __init__(self,**cfg):
        self.c=Clock086();self.cfg=cfg;self.error=0;self.handles={};self.next=100;self.closed=[]
        self.buffers={};self.call_names=[];self.connects=0;self.request=None;self.hold=0
        self.b=replace(bindings086(),owner_sid=SID,peer=Peer084(123,456,2,SID,b'fresh-boot-proof'))
        self.files={str(p):(b'',(4,i+1,5)) for i,p in enumerate(PureWindowsPath(self.b.root).parents)}
    def pointer(self,p,v):p._obj.value=v
    def handle(self,path):self.next+=1;self.handles[self.next]=path;return self.next
    def call(self,n,*a):
        self.call_names.append(n)
        if n=='CreateDirectoryW':
            if self.b.root in self.files:self.error=183;return 0
            self.files[self.b.root]=(b'',(4,100,5));return 1
        if n=='CreateFileW':
            path,access,share,sec,creation,flags,template=a
            if creation==1:
                if path in self.files:self.error=80;return C.c_void_p(-1).value
                self.files[path]=(b'',(4,200,5))
            if path not in self.files:self.error=2;return C.c_void_p(-1).value
            h=self.handle(path)
            if self.cfg.get('expire_open'):self.c.advance(120000)
            return h
        if n=='CreateNamedPipeW':
            self.create_args=a;return self.handle('pipe')
        if n=='ConnectNamedPipe':
            self.connects+=1
            if self.connects==1:return 1
            self.error=536 if self.cfg.get('absent') or self.connects==2 else 535;return 0
        if n=='CloseHandle':
            h=a[0].value if isinstance(a[0],C.c_void_p) else a[0]
            self.closed.append(h);self.handles.pop(h);return 0 if self.cfg.get('close_uncertain') else 1
        if n=='GetFileInformationByHandle':
            path=self.handles[a[0]];data,ident=self.files[path];f=a[1]._obj
            f.attributes=0 if path.endswith('synthetic.bin') else 0x10;f.volume=ident[0]
            f.index_low=ident[1];f.created.low=ident[2];f.links=1;f.size_low=len(data);return 1
        if n=='GetFinalPathNameByHandleW':
            a[1].value='\\\\?\\'+self.handles[a[0]];return len(a[1].value)
        if n=='GetNamedPipeInfo':
            for p,v in zip(a[1:],(5,1024,1024,1)):self.pointer(p,v)
            return 1
        if n=='GetNamedPipeHandleStateW':self.pointer(a[1],3);self.pointer(a[2],1);return 1
        if n=='GetNamedPipeClientProcessId':self.pointer(a[1],123);return 1
        if n=='OpenProcess':return self.handle('process')
        if n=='GetProcessTimes':a[1]._obj.low=456;return 1
        if n=='ProcessIdToSessionId':self.pointer(a[1],2);return 1
        if n=='OpenProcessToken':self.pointer(a[2],self.handle('token'));return 1
        if n=='GetTokenInformation':
            token,kind,buf,size,needed=a;self.pointer(needed,40)
            if buf is None:self.error=122;return 0
            raw=struct.pack('<I',1)+b'\0'*4+struct.pack('<QI',C.addressof(buf)+24,0xC0000000)+b'\0'*4+SID+b'\0'*4
            C.memmove(buf,raw,len(raw));return 1
        if n=='GetSecurityInfo':
            acl=struct.pack('<BBHHH',2,0,16+len(SID),1,0)+struct.pack('<BBHI',0,3,8+len(SID),0x1f01ff)+SID
            buf=C.create_string_buffer(b'\0'*20+SID+acl);base=C.addressof(buf);self.buffers[base]=buf
            self.pointer(a[3],base+20);self.pointer(a[5],base+20+len(SID));self.pointer(a[7],base);return 0
        if n=='GetSecurityDescriptorLength':return 20+len(SID)+16+len(SID)
        if n=='GetSecurityDescriptorControl':self.pointer(a[1],0x9004);self.pointer(a[2],1);return 1
        if n=='ConvertSidToStringSidW':
            buf=C.create_unicode_buffer('S-1-5-21');base=C.addressof(buf);self.buffers[base]=buf;self.pointer(a[1],base);return 1
        if n=='ConvertStringSecurityDescriptorToSecurityDescriptorW':
            buf=C.create_string_buffer(64);base=C.addressof(buf);self.buffers[base]=buf;self.pointer(a[2],base);return 1
        if n=='LocalFree':self.buffers.pop(a[0].value);return None
        if n=='WriteFile':
            h,buf,size,count,overlap=a;raw=C.string_at(buf,size);self.pointer(count,size)
            if self.handles[h]=='pipe':
                self.request=WIRE.unpack(raw)
                if self.request[6]==2:self.hold=self.c.boot+5
            else:self.files[self.handles[h]]=(raw,self.files[self.handles[h]][1])
            return 1
        if n=='ReadFile':
            h,buf,size,count,overlap=a
            if self.cfg.get('no_data'):self.pointer(count,0);self.error=232;return 0
            _,_,_,_,_,seq,kind,issued,deadline,start,end=self.request
            raw=encode086({1:'ready',3:'holding',4:'closed'}[kind],seq,self.bound_b,self.c.boot,deadline,
                self.hold if kind in (3,4) else 0,self.hold+30000 if kind==4 else 0)
            C.memmove(buf,raw,len(raw));self.pointer(count,len(raw));return 1
        raise AssertionError(n)
    def api(self):
        return Api086(Table(self),Table(self),self.c,lambda:b'fresh-boot-proof',lambda:self.error,lambda v:setattr(self,'error',v))


def adapter_ready086(**cfg):
    w=World(**cfg);api=w.api();p=WindowsAdapter086(api,w.b,lambda:Guard083(),lambda ms:w.c.advance(ms))
    def factory(owner,b):
        made=p.factory(owner,b);w.bound_b=made[2];return made
    t=Transport086(w.b,w.c,lambda:Guard083(),factory);ok=False
    try:
        t.start(True);t.transaction('ready',w.c.boot+60000).close();ok=True
    except (Exception,KeyboardInterrupt):pass
    finally:
        if t.counts['cleanup']==0:ok=t.finish() and ok
    return w,api,p,t,ok


class Adapter086Tests(unittest.TestCase):
    def test_fixed_width_abi_sizes_and_signatures(self):
        self.assertEqual((C.sizeof(D),C.sizeof(B),C.sizeof(P),C.sizeof(SECURITY),C.sizeof(FILEINFO)),(4,4,8,24,52))
        self.assertEqual(len(ABI['CreateNamedPipeW'][1]),8);self.assertEqual(len(ABI['ReadFile'][1]),5)
    def test_raw_binary_acl_parsing_and_private_validation(self):
        acl=struct.pack('<BBHHH',2,0,16+len(SID),1,0)+struct.pack('<BBHI',0,3,8+len(SID),0x1f01ff)+SID
        sec=security086(SID,0x9004,acl);self.assertEqual(sec.owner,SID)
        for offset in (1,2,4,6,10):
            changed=bytearray(acl);changed[offset]^=1
            with self.assertRaises(Exception):security086(SID,0x9004,bytes(changed))
    def test_binary_sid_size_revision_and_subauthority_bound(self):
        self.assertEqual(sid086(SID),SID)
        for raw in (SID[:-1],b'\x02'+SID[1:],bytes([1,16])+b'\0'*6,b''):
            with self.assertRaises(Exception):sid086(raw)
    def test_callable_adapter_acquires_raw_facts_and_ready_transaction(self):
        w,api,p,t,ok=adapter_ready086();self.assertTrue(ok)
        self.assertEqual((t.b.root_identity,t.b.file_identity),((4,100,5),(4,200,5)))
        self.assertFalse(w.handles);self.assertFalse(w.buffers);self.assertFalse(api.allocations)
        for n in ('GetSecurityInfo','GetNamedPipeInfo','GetTokenInformation','GetProcessTimes','GetFinalPathNameByHandleW'):
            self.assertIn(n,w.call_names)
        self.assertEqual(w.create_args[1:4],(3|FIRST_INSTANCE,4|2|1|8,1))
    def test_initial_true_connect_requires_later_pipe_connected(self):
        w,api,p,t,ok=adapter_ready086();self.assertTrue(ok);self.assertEqual(w.connects,3)
        w,api,p,t,ok=adapter_ready086(absent=True);self.assertFalse(ok);self.assertEqual(w.connects,64)
        self.assertFalse(w.handles);self.assertFalse(w.buffers)
    def test_handle_registered_before_post_acquisition_clock_failure(self):
        w=World(expire_open=True);api=w.api();path=str(next(iter(w.files)))
        with self.assertRaises(Exception):api.acquire('CreateFileW',(path,META,7,None,3,NO_REPARSE,None),'metadata')
        self.assertEqual(len(api.handles),1);self.assertTrue(api.finish());self.assertFalse(w.handles)
    def test_peak_budget_registers_overflow_acquisition_for_cleanup(self):
        w=World();api=w.api()
        for i in range(16):api.remember(w.handle(str(i)),'temporary')
        h=w.handle('overflow')
        with self.assertRaises(Exception):api.remember(h,'temporary')
        self.assertIn(h,api.handles);self.assertTrue(api.finish());self.assertFalse(w.handles)
    def test_uncertain_close_attempted_once_and_never_retried(self):
        w=World(close_uncertain=True);api=w.api();h=w.handle('temporary');api.remember(h,'temporary')
        self.assertFalse(api.close(h))
        with self.assertRaises(Exception):api.close(h)
        self.assertEqual(w.closed.count(h),1);self.assertFalse(api.finish())
    def test_read_no_data_returns_raw_typed_result_without_delivery_claim(self):
        w=World(no_data=True);api=w.api();h=w.handle('pipe');api.remember(h,'pipe')
        r=api.read(h,145);self.assertEqual((r.succeeded,r.error,r.count,r.raw),(False,232,0,b''));api.finish()
    def test_native_function_tables_rejected_before_binding(self):
        w=World();k=Table(w);k.model_only=False
        with self.assertRaises(Exception):Api086(k,Table(w),w.c,lambda:b'proof-proof',lambda:0,lambda v:None)
        self.assertFalse(w.call_names)
    def test_pointer_bounds_are_checked_before_dereference(self):
        w=World();api=w.api()
        for args in ((1,10,20,8),(10,10,20,11),(10,10,20,True)):
            with self.assertRaises(Exception):api.ptr_bytes(*args)
    def test_reused_private_root_not_overwritten(self):
        w,api,p,t,ok=adapter_ready086();self.assertTrue(ok);before=dict(w.files)
        other=WindowsAdapter086(w.api(),w.b,lambda:Guard083(),lambda ms:None)
        from forex_demo_lab.synchronization_086 import Owner086
        owner=Owner086()
        with self.assertRaises(Exception):other.factory(owner,w.b)
        owner.finish();self.assertEqual(w.files,before)


if __name__=='__main__':unittest.main()
