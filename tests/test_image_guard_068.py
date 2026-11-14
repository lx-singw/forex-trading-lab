from dataclasses import replace
import hashlib
import json
from pathlib import Path
import stat
from types import SimpleNamespace as NS
import unittest

from forex_demo_lab.image_guard_068 import *
from forex_demo_lab.sharing_runtime_066 import Meter066
from test_transport_lifecycle_060 import Clock


class Stream:
    def __init__(self,fs):self.fs=fs;self.position=0;self.closed=False
    def __enter__(self):return self
    def __exit__(self,*args):self.closed=True
    def fileno(self):return 7
    def read(self,n):
        self.fs.requests.append(n);self.fs.hook(self)
        remaining=max(0,self.fs.actual-self.position);n=min(n,remaining)
        self.position+=n;return b'x'*n


class FakePath:
    def __init__(self,fs,parent=False):self.fs=fs;self.parent=parent
    @property
    def parents(self):return (FakePath(self.fs,True),)
    def lstat(self):
        self.fs.stats+=1
        return self.fs.parent if self.parent else self.fs.info
    def open(self,mode):self.fs.opens+=1;self.fs.stream=Stream(self.fs);return self.fs.stream


class FS:
    def __init__(self,size=9):
        self.info=NS(st_mode=stat.S_IFREG,st_file_attributes=32,st_size=size,st_dev=1,st_ino=2,st_mtime_ns=3)
        self.parent=NS(st_mode=stat.S_IFDIR,st_file_attributes=16)
        self.actual=size;self.opens=0;self.requests=[];self.stats=0;self.stream=None
        self.hook=lambda s:None;self.fd_hook=lambda:None
    def path(self,value):return FakePath(self)
    def fstat(self,fd):self.fd_hook();return self.info


class ImageGuard068Tests(unittest.TestCase):
    def setUp(self):self.clock=Clock();self.m=Meter066(self.clock);self.fs=FS()
    def hash(self):return bounded_hash(self.m,'private',self.fs.path,self.fs.fstat)
    def rejects(self):
        with self.assertRaisesRegex(ProbeRejected,'^image_hash_rejected_details_redacted$'):self.hash()
        if self.fs.stream:self.assertTrue(self.fs.stream.closed)
    def test_current_terminal_size_now_hashes_completely(self):
        self.fs=FS(134439504);value=self.hash()
        expected=hashlib.sha256();remaining=self.fs.actual
        while remaining:n=min(CHUNK,remaining);expected.update(b'x'*n);remaining-=n
        self.assertEqual(value,expected.hexdigest());self.assertEqual(self.m.counts['hash_bytes'],134439504)
        self.assertLessEqual(max(self.fs.requests),CHUNK);self.assertTrue(self.fs.stream.closed)
    def test_exact_130mib_boundary_accepted(self):
        self.fs=FS(MAX_IMAGE_BYTES);self.assertEqual(len(self.hash()),64)
        self.assertEqual(self.m.counts['hash_bytes'],MAX_IMAGE_BYTES)
    def test_130mib_plus_one_rejected_before_open(self):
        self.fs=FS(MAX_IMAGE_BYTES+1);self.rejects();self.assertEqual(self.fs.opens,0)
    def test_empty_file_rejected_before_open(self):self.fs=FS(0);self.rejects();self.assertEqual(self.fs.opens,0)
    def test_nonregular_image_rejected(self):self.fs.info.st_mode=stat.S_IFDIR;self.rejects()
    def test_symlink_image_rejected(self):self.fs.info.st_mode=stat.S_IFLNK;self.rejects()
    def test_parent_reparse_rejected(self):self.fs.parent.st_file_attributes|=0x400;self.rejects()
    def test_file_reparse_rejected(self):self.fs.info.st_file_attributes|=0x400;self.rejects()
    def test_stream_identity_mismatch_rejected(self):
        self.fs.fstat=lambda fd:NS(**{**vars(self.fs.info),'st_ino':22});self.rejects()
    def test_truncated_stream_rejected_and_counted(self):
        self.fs.actual=8;self.rejects();self.assertEqual(self.m.counts['hash_bytes'],10)
    def test_growth_during_read_rejected_without_unbounded_read(self):
        def grow(s):self.fs.info.st_size=CHUNK*100;self.fs.actual=CHUNK*100
        self.fs.hook=grow;self.rejects();self.assertEqual(self.m.counts['hash_bytes'],9)
    def test_final_mtime_change_rejected(self):
        calls=[]
        def change():
            calls.append(1)
            if len(calls)==2:self.fs.info=NS(**{**vars(self.fs.info),'st_mtime_ns':4})
        self.fs.fd_hook=change;self.rejects()
    def test_final_path_replacement_rejected(self):
        old=self.fs.path
        class Replacement(FakePath):
            def lstat(s):
                value=super().lstat()
                if not s.parent and s.fs.stream and s.fs.stream.closed:return NS(**{**vars(value),'st_ino':99})
                return value
        self.fs.path=lambda value:Replacement(self.fs);self.rejects()
    def test_late_parent_reparse_rejected(self):
        self.fs.fd_hook=lambda:setattr(self.fs.parent,'st_file_attributes',0x410) if self.fs.stream.position else None
        self.rejects()
    def test_hash_aggregate_budget_still_rejects(self):
        self.m.counts['hash_bytes']=103079215104-8;self.rejects();self.assertTrue(self.fs.stream.closed)
    def test_attempt_budget_spent_even_rejected_size(self):
        self.fs=FS(MAX_IMAGE_BYTES+1);self.rejects();self.assertEqual(self.m.counts['hash_reads'],1)
    def test_expiry_during_stream_still_closes(self):
        self.fs.hook=lambda s:self.clock.advance(900000);self.rejects()
    def test_hash_exception_details_redacted(self):
        def fail(s):raise RuntimeError('secret SID private account')
        self.fs.hook=fail;self.rejects()
    def test_repeated_hash_is_not_cached(self):
        self.assertEqual(self.hash(),self.hash());self.assertEqual(self.fs.opens,2)
        self.assertEqual(self.m.counts['hash_bytes'],18)
    def test_stage_failure_is_localized_without_exception_text(self):
        s=Stage068()
        def fail():raise RuntimeError('secret')
        with self.assertRaises(RuntimeError):s.run('terminal_image',fail)
        self.assertEqual(s.current,'terminal_image');self.assertNotIn('secret',json.dumps(s.public()))
        self.assertFalse(s.public()[0]['completed'])
    def test_stage_unsupported_name_rejected(self):
        with self.assertRaises(ProbeRejected):Stage068().enter('private account')
    def test_stage_budget_is_finite(self):
        s=Stage068()
        for _ in range(24):s.run('helper_chain',lambda:True)
        with self.assertRaises(ProbeRejected):s.enter('helper_chain')
    def test_stage_completion_cannot_duplicate(self):
        s=Stage068();s.enter('helper_chain');s.complete()
        with self.assertRaises(ProbeRejected):s.complete()
    def chain(self):
        c=HelperChain068(('launcher','a'*64),('config','b'*64),(('base','c'*64),('alternate','c'*64)),('library','d'*64),'alias')
        h=Identity065(7,11,'base','c'*64,1,'hidden')
        expected={'launcher':'a'*64,'config':'b'*64,'library':'d'*64};calls=[]
        r=NS(hash_file=lambda path:calls.append(path) or expected[path]);return c,h,r,calls
    def test_alias_differs_from_native_image_without_removing_pin(self):
        c,h,r,calls=self.chain();self.assertTrue(c.check(r,h,'launcher','alias','library'))
        self.assertEqual(calls,['launcher','config','library']);self.assertNotIn('alias',calls)
        self.assertNotIn('hidden',repr(c));self.assertNotIn('launcher',repr(c))
    def test_unpinned_native_helper_image_or_digest_rejected(self):
        c,h,r,calls=self.chain()
        for change in ({'image':'unknown'},{'digest':'e'*64}):
            with self.assertRaises(ProbeRejected):c.check(r,replace(h,**change),'launcher','alias','library')
        self.assertEqual(calls,[])
    def test_wrong_launcher_alias_or_loaded_library_rejected(self):
        c,h,r,calls=self.chain()
        for args in (('other','alias','library'),('launcher','other','library'),('launcher','alias','other')):
            with self.assertRaises(ProbeRejected):c.check(r,h,*args)
        self.assertEqual(calls,[])
    def test_changed_chain_file_hash_rejected(self):
        c,h,r,calls=self.chain();r.hash_file=lambda path:'e'*64
        with self.assertRaises(ProbeRejected):c.check(r,h,'launcher','alias','library')
    def test_exact_reservation_bytes_bound_without_sidecar(self):
        raw=b'{"bindings":{"source":"pinned"},"phase":"new","orders_available":false}'
        h=hashlib.sha256(raw).hexdigest();self.assertEqual(reservation_bytes(raw,h,{'source':'pinned'},'new')['phase'],'new')
        with self.assertRaises(ProbeRejected):reservation_bytes(raw+b' ',h,{'source':'pinned'},'new')
    def test_duplicate_reservation_keys_rejected(self):
        raw=b'{"bindings":{},"phase":"new","phase":"new","orders_available":false}'
        with self.assertRaises(ProbeRejected):reservation_bytes(raw,hashlib.sha256(raw).hexdigest(),{},'new')
    def test_real_cap_reproduces_old_size_failure(self):
        old=Path(__file__).resolve().parents[1].joinpath('src/forex_demo_lab/private_guard_065.py').read_text()
        self.assertIn('before.st_size<=134217728',old);self.assertGreater(134439504,134217728)
        self.assertEqual(MAX_IMAGE_BYTES,136314880)
