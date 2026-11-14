from dataclasses import replace
import ctypes as C
import json
import unittest

from forex_demo_lab.readiness_adapter_061 import sharing_compatible
from forex_demo_lab.sharing_probe_062 import *


class Clock:
    def __init__(self):self.utc=1791352800000;self.ns=0
    def __call__(self):return self.utc,self.ns
    def advance(self,ms):self.utc+=ms;self.ns+=ms*1000000


class Files:
    """Injected sharing contract. No files, tokens, SDK or Win32 calls."""
    def __init__(self,meter):
        self.meter=meter;self.active={};self.serial=10;self.data=b'';self.unconfirmed=[]
        self.pos={};self.calls=[];self.close_fail=None;self.permission_error=None
        self.on_open=self.on_read=self.on_stamp=None
        self.stamp_mutate=lambda s:s;self.raw_mutate=lambda b:b
        self.retained=False;self.allocations_released=True
    def setup(self):
        self.meter.consume('opens');self.meter.consume('directories')
        self.retained=True;self.calls.append('setup')
    def open(self,role):
        self.meter.consume('opens');self.calls.append(role)
        if self.on_open:self.on_open(role)
        modes={'directory':(0,7),'writer':(3,3),'seal_while_writer':(1,1),
            'seal':(1,1),'reader':(1,1),'writer_while_sealed':(2,3),'delete_while_sealed':(4,7)}
        access,share=modes[role]
        if role!='directory':
            for oldrole,oldaccess,oldshare in self.active.values():
                if oldrole!='directory' and not sharing_compatible(oldaccess,oldshare,access,share):
                    return Open(None,self.permission_error or 'sharing_violation')
        self.serial+=1;h=self.serial;self.active[h]=(role,access,share);self.pos[h]=0
        return Open(h)
    def stamp(self,h,directory=False):
        if self.on_stamp:self.on_stamp(h,directory)
        return self.stamp_mutate(Stamp((1,2,3),len(self.data) if not directory else 0,
                            self.pos[h],directory,True,True,False))
    def write(self,h,data):
        self.meter.consume('writes');self.data=data;self.pos[h]=len(data)
        return len(data)
    def read(self,h,n):
        self.meter.consume('reads');self.calls.append(('read',n))
        raw=self.raw_mutate(self.data[:n]);self.pos[h]=len(raw)
        if self.on_read:self.on_read(h)
        return raw,len(raw)
    def close(self,h):
        role=self.active.pop(h)[0];self.calls.append(('close',role))
        if role==self.close_fail:self.unconfirmed.append(h);return False
        return True
    def finish(self):
        for h in list(self.active)[::-1]:self.close(h)
        return dict(all_handles_closed=not self.active and not self.unconfirmed,
                    unconfirmed_handles=len(self.unconfirmed),allocations_released=self.allocations_released,
                    synthetic_directory_retained=self.retained)


class SharingProbe062Tests(unittest.TestCase):
    def setUp(self):
        self.clock=Clock();self.meter=Meter(self.clock);self.files=Files(self.meter)
    def run_model(self):return run_probe(self.files,self.meter)
    def rejected(self,reason=None):
        r=self.run_model();self.assertFalse(r['passed'])
        if reason:self.assertEqual(r['stop_reason'],reason)
        return r
    def test_complete_sharing_sequence_and_exact_budgets(self):
        r=self.run_model();self.assertTrue(r['passed'])
        self.assertEqual((r['handle_open_attempts'],r['write_attempts'],r['read_attempts'],r['directory_attempts']),(8,1,2,1))
        self.assertEqual(r['read_counts'],[84,84]);self.assertTrue(r['cleanup']['all_handles_closed'])
        self.assertEqual([x['category'] for x in r['observations']],['none','none','sharing_violation','none','none','sharing_violation','sharing_violation'])
    def test_existing_writer_prevents_seal(self):
        r=self.run_model();self.assertEqual(r['observations'][2]['role'],'seal_while_writer')
        self.assertEqual(r['observations'][2]['category'],'sharing_violation')
    def test_two_readers_share_same_file_without_new_writer(self):
        r=self.run_model();self.assertTrue(r['same_file_verified'])
        self.assertEqual(sum(isinstance(x,tuple) and x[0]=='read' for x in self.files.calls),2)
    def test_delete_access_test_does_not_delete_or_rename(self):
        r=self.run_model();self.assertTrue(r['passed'])
        self.assertIn('delete_while_sealed',self.files.calls);self.assertEqual(self.files.data,DATA)
    def test_access_denied_is_not_sharing_proof(self):
        self.files.permission_error='access_denied'
        self.rejected('expected_sharing_outcome_rejected')
    def test_unexpected_compatible_seal_rejected(self):
        old=self.files.open
        def opened(role):
            if role=='seal_while_writer':
                for h in list(self.files.active):
                    if self.files.active[h][0]=='writer':self.files.active[h]=('writer',1,1)
            return old(role)
        self.files.open=opened;self.rejected('expected_sharing_outcome_rejected')
    def test_short_write_rejected_without_retry(self):
        def write(h,data):self.meter.consume('writes');return 83
        self.files.write=write;r=self.rejected('short_write_rejected')
        self.assertEqual(r['write_attempts'],1);self.assertEqual(r['read_attempts'],0)
    def test_zero_read_rejected_without_retry(self):
        self.files.raw_mutate=lambda b:b''
        r=self.rejected('synthetic_read_rejected');self.assertEqual(r['read_attempts'],1)
    def test_partial_read_rejected(self):
        self.files.raw_mutate=lambda b:b[:83];self.rejected('synthetic_read_rejected')
    def test_extra_read_rejected(self):
        self.files.raw_mutate=lambda b:b+b'x';self.rejected('synthetic_read_rejected')
    def test_wrong_content_rejected(self):
        self.files.raw_mutate=lambda b:bytes([b[0]^1])+b[1:];self.rejected('synthetic_read_rejected')
    def test_private_error_redacted_and_cleanup_attempted(self):
        def fail(h,n):raise RuntimeError('private SID account identifier')
        self.files.read=fail;r=self.rejected('probe_failed_details_redacted')
        self.assertTrue(r['cleanup']['all_handles_closed']);self.assertNotIn('identifier',json.dumps(r))
    def test_file_identity_changed_after_read_rejected(self):
        def changed(h):self.files.stamp_mutate=lambda s:replace(s,identity=(1,22,3))
        self.files.on_read=changed;self.rejected('file_identity_changed')
    def test_size_change_rejected(self):
        def changed(h):self.files.stamp_mutate=lambda s:replace(s,size=85)
        self.files.on_read=changed;self.rejected('private_file_binding_rejected')
    def test_missing_owner_or_path_or_reparse_evidence_rejected(self):
        for key,value in (('security_verified',False),('path_verified',False),('reparse',True)):
            clock=Clock();meter=Meter(clock);files=Files(meter)
            files.stamp_mutate=lambda s,k=key,v=value:replace(s,**{k:v})
            self.assertFalse(run_probe(files,meter)['passed'])
    def test_hard_link_count_rejected(self):
        self.files.stamp_mutate=lambda s:s if s.directory else replace(s,links=2)
        self.rejected('private_file_binding_rejected')
    def test_wrong_file_pointer_rejected(self):
        self.files.on_read=lambda h:self.files.pos.__setitem__(h,83)
        self.rejected('private_file_binding_rejected')
    def test_writer_close_failure_retained_and_stops(self):
        self.files.close_fail='writer';r=self.rejected('cleanup_unconfirmed')
        self.assertEqual(r['cleanup']['unconfirmed_handles'],1);self.assertNotIn('seal',self.files.calls)
    def test_final_reader_close_failure_invalidates_success(self):
        self.files.close_fail='reader';self.rejected('cleanup_unconfirmed')
    def test_native_allocation_release_failure_invalidates_success(self):
        self.files.allocations_released=False;self.rejected('cleanup_unconfirmed')
    def test_cleanup_exception_redacted(self):
        def fail():raise RuntimeError('private handle values')
        self.files.finish=fail;self.rejected('cleanup_failed_details_redacted')
    def test_deadline_after_blocking_read_is_detected_only_after_return(self):
        self.files.on_read=lambda h:self.clock.advance(60000)
        r=self.rejected('measured_deadline_exceeded');self.assertTrue(r['measured_overrun'])
        self.assertTrue(r['cleanup']['all_handles_closed'])
    def test_clock_reversal_during_native_operation_rejected(self):
        self.clock.advance(1)
        self.files.on_open=lambda role:setattr(self.clock,'ns',self.clock.ns-1)
        self.rejected('clock_reversed')
    def test_wall_monotonic_discontinuity_rejected(self):
        self.clock.utc+=1001;self.rejected('clock_discontinuity')
    def test_fixed_date_expiry_rejected_before_probe(self):
        self.clock.utc+=86400000;self.rejected('declared_date_expired')
        self.assertEqual(self.files.calls,[])
    def test_open_write_read_directory_budgets_burn_before_calls(self):
        for kind,limit in (('opens',16),('writes',1),('reads',2),('directories',1)):
            meter=Meter(Clock())
            for _ in range(limit):meter.consume(kind)
            with self.assertRaisesRegex(ProbeRejected,'^operation_budget_exhausted$'):meter.consume(kind)
            self.assertEqual(getattr(meter,kind),limit)
    def test_bool_or_invalid_clock_rejected(self):
        for sample in ((True,0),(-1,0),(1791352800000,False),[1791352800000,0]):
            with self.assertRaises(ProbeRejected):Meter(lambda s=sample:s)
    def test_bool_count_cannot_be_success(self):
        self.files.write=lambda h,data:True;self.rejected('short_write_rejected')
    def test_no_permission_or_market_capabilities_in_result(self):
        r=self.run_model()
        for name in ('sdk_connections','mt5_invocations','receipt_permissions','quote_reads','history_reads','orders'):
            self.assertEqual(r[name],0)
        self.assertFalse(r['native_mql_verified']);self.assertFalse(r['orders_available'])
        self.assertNotEqual(DATA[:8],b'FXDL047R')
    def test_ctypes_abi_matches_win32_fixed_width_layout(self):
        self.assertEqual(C.sizeof(FILEINFO),52);self.assertEqual(C.sizeof(FILETIME),8)
        self.assertEqual(C.sizeof(ACLINFO),12);self.assertEqual(FILEINFO.volume.offset,28)
