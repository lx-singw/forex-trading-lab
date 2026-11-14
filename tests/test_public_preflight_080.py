import hashlib
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from forex_demo_lab import public_preflight_080 as module
from forex_demo_lab.public_model_080 import (original_class080,unchanged_methods080,
    model_paths080,WINDOWS_ROOT080,DATE_CLOCK080)

ROOT=Path(__file__).resolve().parents[1]


class Public080Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.clock=list(DATE_CLOCK080)
        self.reader=module.PublicInputs080(lambda:tuple(self.clock))
    def record(self,raw=b'{"ok":true}\n',newline=b'\n'):
        p=self.root/'r.json';p.write_bytes(raw)
        p.with_suffix('.sha256').write_bytes(hashlib.sha256(raw).hexdigest().encode('ascii')+newline)
        return p
    def rejects(self,callback,reason=None):
        if reason:
            with self.assertRaisesRegex(module.PublicInputRejected080,'^'+reason+'$'):callback()
        else:
            with self.assertRaises(module.PublicInputRejected080):callback()
    def windows(self,path,overrides=None):
        w=WINDOWS_ROOT080/'reports/r.json'
        model=model_paths080({str(w):path,str(w.with_suffix('.sha256')):path.with_suffix('.sha256')},self.root,overrides)
        return w,model

    def test_exact_lf_checksum(self):
        raw=b'{}';side=hashlib.sha256(raw).hexdigest().encode()+b'\n'
        self.assertEqual(module.verify_sidecar080(side,raw),'lf')
    def test_exact_crlf_checksum(self):
        raw=b'{}';side=hashlib.sha256(raw).hexdigest().encode()+b'\r\n'
        self.assertEqual(len(side),66);self.assertEqual(module.verify_sidecar080(side,raw),'crlf')
    def test_other_whitespace_bom_cr_and_missing_newline_reject(self):
        raw=b'{}';h=hashlib.sha256(raw).hexdigest().encode()
        for side in (h,h+b'\r',h+b' \n',h+b'\n\n',h+b'\r\r\n',b' '+h+b'\n',b'\xef\xbb\xbf'+h+b'\n'):
            self.rejects(lambda:module.verify_sidecar080(side,raw),'timing_public_digest_rejected')
    def test_wrong_uppercase_digest_and_nonbytes_reject(self):
        raw=b'{}';h=hashlib.sha256(raw).hexdigest().encode()
        for side in (b'0'*64+b'\n',h.upper()+b'\n',h.decode()+'\n',False,bytearray(h+b'\n')):
            self.rejects(lambda:module.verify_sidecar080(side,raw))
        self.rejects(lambda:module.verify_sidecar080(h+b'\n','{}'))
    def test_lf_record_json_and_original_content_digest(self):
        p=self.record();value,h=self.reader.record(p)
        self.assertEqual(value,dict(ok=True));self.assertEqual(h,hashlib.sha256(p.read_bytes()).hexdigest())
    def test_crlf_record_preserves_json_bytes_and_digest(self):
        raw=b'{"ok":true}\r\n';p=self.record(raw,b'\r\n');before=p.read_bytes()
        value,h=self.reader.record(p);self.assertEqual(value,dict(ok=True))
        self.assertEqual(p.read_bytes(),before);self.assertEqual(h,hashlib.sha256(before).hexdigest())
    def test_bad_digest_rejects_before_json_decode(self):
        p=self.record(b'not json');p.with_suffix('.sha256').write_bytes(b'0'*64+b'\r\n')
        self.rejects(lambda:self.reader.record(p),'timing_public_digest_rejected')
    def test_duplicate_json_keys_reject_with_matching_crlf_digest(self):
        p=self.record(b'{"ok":true,"ok":false}',b'\r\n')
        self.rejects(lambda:self.reader.record(p),'timing_public_schema_rejected')
    def test_nonascii_json_rejects_with_matching_digest(self):
        p=self.record(b'{"x":"\xc3\xa9"}',b'\r\n')
        self.rejects(lambda:self.reader.record(p),'timing_public_schema_rejected')
    def test_empty_and_oversized_public_file_reject(self):
        p=self.record()
        for raw in (b'',b'x'*524289):
            p.write_bytes(raw);self.rejects(lambda:self.reader.raw(p))
    def test_sidecar_larger_than66_rejects_before_read(self):
        p=self.record();p.with_suffix('.sha256').write_bytes(b'0'*64+b'\r\n ')
        self.rejects(lambda:self.reader.record(p),'timing_public_file_rejected')
    def test_hardlink_rejects(self):
        p=self.record();module.os.link(p,self.root/'hard')
        self.rejects(lambda:self.reader.record(p),'timing_public_file_rejected')
    def test_symlink_rejects(self):
        p=self.record();link=self.root/'link';link.symlink_to(p)
        self.rejects(lambda:self.reader.raw(link),'timing_public_file_rejected')
    def test_windows_reparse_parent_rejects(self):
        p=self.record();w=WINDOWS_ROOT080/'reports/r.json'
        w,model=self.windows(p,{str(w.parents[0]):{'st_file_attributes':0x400}})
        with patch.object(module,'Path',model):
            self.rejects(lambda:self.reader.record(str(w)),'timing_public_file_rejected')
    def test_descriptor_identity_changes_at_either_check_reject(self):
        p=self.record();actual=module.os.fstat
        for trigger in (1,2):
            count=[0];reader=module.PublicInputs080(lambda:tuple(self.clock))
            def changed(fd):
                s=actual(fd);count[0]+=1
                fields={k:getattr(s,k) for k in ('st_dev','st_ino','st_size','st_mtime_ns','st_nlink')}
                if count[0]==trigger:fields['st_ino']+=1
                return SimpleNamespace(**fields)
            with patch.object(module.os,'fstat',changed):
                self.rejects(lambda:reader.raw(p),'timing_public_file_rejected')
    def test_final_path_identity_change_rejects(self):
        p=self.record();w,model=self.windows(p);actual=model.lstat;calls=[0]
        def changed(node):
            s=actual(node)
            if str(node)==str(w):
                calls[0]+=1
                if calls[0]==2:s.st_ino+=1
            return s
        with patch.object(module,'Path',model),patch.object(model,'lstat',changed):
            self.rejects(lambda:self.reader.raw(str(w)),'timing_public_file_rejected')
    def test_short_read_rejects_and_closes_stream(self):
        p=self.record();w,model=self.windows(p);actual=model.open;seen=[]
        class Short:
            def __init__(self,stream):self.stream=stream
            def __enter__(self):seen.append(self.stream);return self
            def __exit__(self,*args):self.stream.close()
            def fileno(self):return self.stream.fileno()
            def read(self,n):return self.stream.read(n)[:-1]
        with patch.object(module,'Path',model),patch.object(model,'open',lambda node,mode:Short(actual(node,mode))):
            self.rejects(lambda:self.reader.raw(str(w)))
        self.assertEqual(len(seen),1);self.assertTrue(seen[0].closed)
    def test_public_read_budget_unchanged(self):
        p=self.record();self.reader.reads=16;self.rejects(lambda:self.reader.raw(p))
    def test_public_byte_budget_unchanged(self):
        p=self.record();self.reader.bytes=2097152;self.rejects(lambda:self.reader.record(p))
    def test_public_stat_budget_unchanged(self):
        p=self.record();self.reader.stats=128;self.rejects(lambda:self.reader.raw(p))
    def test_source_read_byte_and_stat_budgets_unchanged(self):
        p=self.record()
        for attr,n in (('source_reads',64),('source_bytes',16777216),('source_stats',1024)):
            reader=module.PublicInputs080(lambda:tuple(self.clock));setattr(reader,attr,n)
            self.rejects(lambda:reader.raw(p,source=True))
    def test_clock_30_second_expiry(self):
        self.clock[0]+=30000;self.clock[1]+=30000000000
        self.rejects(self.reader.check,'timing_public_clock_rejected')
    def test_clock_date_reversal_and_skew_reject(self):
        for kind in ('date','reversal','skew'):
            clock=list(DATE_CLOCK080);reader=module.PublicInputs080(lambda:tuple(clock))
            if kind=='date':clock[0]+=86400000
            elif kind=='reversal':clock[1]-=1
            else:clock[0]+=1001
            self.rejects(reader.check,'timing_public_clock_rejected')
    def test_four_original_integrity_methods_are_ast_equal(self):
        names=unchanged_methods080((ROOT/'scripts/runtime-native-timing-078.py').read_text(),
            (ROOT/'src/forex_demo_lab/public_preflight_080.py').read_text())
        self.assertEqual(names,('__init__','check','properties','raw'))
    def test_ast_comparison_detects_weakened_link_guard(self):
        old=(ROOT/'scripts/runtime-native-timing-078.py').read_text()
        new=(ROOT/'src/forex_demo_lab/public_preflight_080.py').read_text().replace('before.st_nlink!=1','before.st_nlink!=2')
        with self.assertRaisesRegex(ValueError,'^public_integrity_method_changed$'):unchanged_methods080(old,new)
    def test_original_class_rejects_crlf_before_digest_validation(self):
        p=self.record(newline=b'\r\n');cls,namespace=original_class080((ROOT/'scripts/runtime-native-timing-078.py').read_text())
        old=cls(lambda:tuple(self.clock));self.rejects(lambda:old.record(p),'timing_public_file_rejected')
        self.assertEqual(old.reads,2);self.assertNotIn('run',namespace)
        self.assertNotIn('MetaTrader5',namespace)
    def test_explicit_windows_parent_arithmetic(self):
        p=self.record(newline=b'\r\n');w,model=self.windows(p)
        self.assertEqual(len(w.parents),6)
        with patch.object(module,'Path',model):self.reader.record(str(w))
        self.assertEqual((self.reader.reads,self.reader.stats),(2,20))
    def test_extra_crlf_byte_is_charged_to_same_aggregate_budget(self):
        p=self.record(newline=b'\r\n');self.reader.record(p)
        self.assertEqual(self.reader.bytes,p.stat().st_size+66)
        self.assertEqual((self.reader.source_reads,self.reader.source_bytes,self.reader.source_stats),(0,0,0))


if __name__=='__main__':unittest.main()
