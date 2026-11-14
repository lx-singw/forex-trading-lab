from dataclasses import replace
import json
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
import unittest

from forex_demo_lab.mql_sharing_064 import *

ROOT = Path(__file__).resolve().parents[1]


def record(enabled=False):
    r = dict(version='sharing_fixture_064_v1',phase=PHASE,reason_code=17,
        opens=0,reads=0,closes=0,read_bytes=0,size_before=-1,size_after=-1,
        position_before=-1,position_after=-1,pattern_ok=False,open_category=-1,
        read_category=-1,close_category=-1,hold_start_boot_ms=-1,
        hold_end_boot_ms=-1,hold_elapsed_us=-1,hold_iterations=0,
        quote_reads=0,history_reads=0,orders=0,receipt_permissions=0)
    if enabled:
        r.update(reason_code=0,opens=1,reads=1,closes=1,read_bytes=84,size_before=84,
            size_after=84,position_before=0,position_after=84,pattern_ok=True,
            open_category=0,read_category=0,close_category=0,hold_start_boot_ms=100000,
            hold_end_boot_ms=130000,hold_elapsed_us=30000000,hold_iterations=600)
    return r


def text(r): return PREFIX+json.dumps(r)


class MQLSharing064Tests(unittest.TestCase):
    def setUp(self):
        self.rows = [record(), record(True)]
        self.proof = PrivateProof(True,True,True,True,True,True,True,True,DATE)
        self.probes = [Probe(s,a,t,t+50,32 if s=='independent' else 0,
                            s!='independent',s!='independent',0,True,True,True,True)
                       for s,a,t in [('pre','write',99000),('pre','delete',99200),
                            ('independent','write',102000),('independent','delete',103000),
                            ('post','write',131000),('post','delete',132000)]]

    def reject(self):
        with self.assertRaisesRegex(ValueError,'^sharing_evidence_rejected$'):
            match_evidence(self.rows,self.probes,self.proof)

    def bad_record(self, **changes):
        r=record(True);r.update(changes)
        with self.assertRaisesRegex(ValueError,'^sharing_record_rejected$'):parse_record(text(r))

    def test_matching_controls_and_independent_interval(self):
        r=match_evidence(self.rows,self.probes,self.proof)
        self.assertTrue(r['modeled_match']);self.assertEqual(r['probe_count'],6)
        self.assertFalse(r['native_mql_verified']);self.assertFalse(r['orders_available'])

    def test_disabled_record_has_no_file_or_market_operations(self):
        self.assertEqual(parse_record(text(record())),record())
        for k in ('opens','reads','closes','quote_reads','history_reads','orders','receipt_permissions'):
            r=record();r[k]=1
            with self.assertRaises(ValueError):parse_record(text(r))

    def test_missing_or_duplicate_records_rejected(self):
        for rows in ([],self.rows[:1],self.rows+[record(True)]):
            self.rows=rows;self.reject()

    def test_swapped_disabled_enabled_records_rejected(self):
        self.rows.reverse();self.reject()

    def test_wrong_phase_or_version_rejected(self):
        self.bad_record(phase='65'*16);self.bad_record(version='other')

    def test_record_duplicate_json_keys_rejected(self):
        value=text(record(True)).replace('"opens": 1','"opens": 1, "opens": 1')
        with self.assertRaises(ValueError):parse_record(value)

    def test_unknown_fields_and_private_payload_rejected(self):
        self.bad_record(account='private identifier')
        with self.assertRaisesRegex(ValueError,'^sharing_record_rejected$') as e:
            parse_record(PREFIX+'{"private-path":"secret"}')
        self.assertNotIn('secret',str(e.exception))

    def test_boolean_integer_fields_rejected(self):
        for k in KEYS-{'version','phase','pattern_ok'}:self.bad_record(**{k:True})

    def test_success_requires_exact_bytes_and_pattern(self):
        for n in (0,20,83,85):self.bad_record(read_bytes=n)
        self.bad_record(pattern_ok=False);self.bad_record(pattern_ok=1)

    def test_success_requires_size_and_position_before_after(self):
        for k in ('size_before','size_after','position_before','position_after'):
            self.bad_record(**{k:-1});self.bad_record(**{k:85})

    def test_success_requires_one_open_read_close(self):
        for k in ('opens','reads','closes'):
            self.bad_record(**{k:0});self.bad_record(**{k:2})

    def test_success_rejects_error_or_unknown_category(self):
        for k in ('open_category','read_category','close_category'):
            for v in (-1,6,999):self.bad_record(**{k:v})

    def test_too_short_hold_and_long_overrun_rejected(self):
        self.bad_record(hold_end_boot_ms=129999,hold_elapsed_us=29999000)
        self.bad_record(hold_end_boot_ms=131001,hold_elapsed_us=31001000)

    def test_reversed_or_stale_boot_record_rejected(self):
        self.bad_record(hold_end_boot_ms=99999)
        self.bad_record(hold_start_boot_ms=0,hold_end_boot_ms=30000)

    def test_hold_iteration_frozen_clock_budget(self):
        self.bad_record(hold_iterations=0);self.bad_record(hold_iterations=602)
        self.assertEqual(hold_reason(100000,100000,0,601,False,True),21)

    def test_stopped_and_wrong_date_hold_rejected(self):
        self.assertEqual(hold_reason(100000,130000,30000000,600,True,True),18)
        self.assertEqual(hold_reason(100000,130000,30000000,600,False,False),10)

    def test_missing_private_proofs_or_cached_hashes_rejected(self):
        for k in PrivateProof.__dataclass_fields__:
            if k=='current_date':continue
            original=self.proof
            for v in (False,1):self.proof=replace(original,**{k:v});self.reject()
            self.proof=original

    def test_private_process_boot_or_date_change_rejected(self):
        self.proof=replace(self.proof,current_date='2026-10-08');self.reject()
        self.proof=replace(self.proof,current_date=DATE,same_process_image_account_logon_boot=False);self.reject()

    def test_helper_read_seal_cannot_mask_mql_exclusion(self):
        self.probes[2]=replace(self.probes[2],blocking_companion_handles=1);self.reject()

    def test_metadata_handle_must_share_all_accesses(self):
        self.proof=replace(self.proof,metadata_handle_shares_all=False);self.reject()

    def test_access_denied_never_counts_as_sharing_violation(self):
        self.probes[2]=replace(self.probes[2],error=5);self.reject()

    def test_successful_independent_writer_or_delete_rejected(self):
        for i in (2,3):
            old=self.probes[i];self.probes[i]=replace(old,error=0,opened=True,closed=True)
            self.reject();self.probes[i]=old

    def test_pre_controls_cannot_already_be_blocked(self):
        self.probes[0]=replace(self.probes[0],error=32,opened=False,closed=False);self.reject()

    def test_post_controls_corroborate_mql_release(self):
        self.probes[4]=replace(self.probes[4],error=32,opened=False,closed=False);self.reject()

    def test_unconfirmed_control_close_rejected(self):
        self.probes[5]=replace(self.probes[5],closed=False);self.reject()

    def test_full_guards_and_same_file_both_sides_required(self):
        for key in ('full_guard_before','full_guard_after','same_file_before','same_file_after'):
            old=self.probes[2];self.probes[2]=replace(old,**{key:False});self.reject();self.probes[2]=old

    def test_independent_probe_cannot_straddle_hold_start(self):
        self.probes[2]=replace(self.probes[2],start_boot_ms=99999);self.reject()

    def test_independent_probe_cannot_straddle_hold_end(self):
        self.probes[3]=replace(self.probes[3],end_boot_ms=130001);self.reject()

    def test_resolution_margin_is_strict_at_both_ends(self):
        old=self.probes[2];self.probes[2]=replace(old,start_boot_ms=100250,end_boot_ms=100251);self.reject()
        self.probes[2]=old
        self.probes[3]=replace(self.probes[3],end_boot_ms=129750);self.reject()

    def test_probes_must_be_ordered_and_nonoverlapping(self):
        self.probes[2],self.probes[3]=self.probes[3],self.probes[2];self.reject()
        self.probes[2],self.probes[3]=self.probes[3],self.probes[2]
        self.probes[3]=replace(self.probes[3],start_boot_ms=102025);self.reject()

    def test_missing_duplicate_or_extra_probe_rejected(self):
        old=self.probes
        for value in (old[:5],old+[old[-1]],old[:3]+[old[2]]+old[4:]):
            self.probes=value;self.reject()

    def test_bad_probe_integer_and_handle_booleans_rejected(self):
        old=self.probes[2]
        for key,value in (('error',True),('start_boot_ms',True),('blocking_companion_handles',False),('opened',0),('closed',0)):
            self.probes[2]=replace(old,**{key:value});self.reject()

    def test_delayed_log_arrival_does_not_move_hold_window(self):
        raw=('late log line '+text(record(True))+'\r\n').encode('utf-16-le')
        parsed=records_from_log(raw)
        self.assertEqual(parsed[0]['hold_start_boot_ms'],100000)
        self.rows[1]=parsed[0]
        self.probes[2]=replace(self.probes[2],start_boot_ms=140000,end_boot_ms=140050)
        self.reject()

    def test_saved_log_range_utf16_bound_and_ambiguous_prefix(self):
        raw=('other\r\n'+text(record())+'\r\n'+text(record(True))).encode('utf-16-le')
        self.assertEqual(records_from_log(raw),self.rows)
        for bad in (b'x',b'\0'*65538,(PREFIX+text(record())).encode('utf-16-le'),b'\x00\xd8'):
            with self.assertRaises(ValueError):records_from_log(bad)

    def test_synthetic_bytes_are_not_a_receipt_or_permission(self):
        self.assertEqual(len(DATA),84);self.assertNotEqual(DATA[:8],b'FXDL047R')
        self.assertEqual(match_evidence(self.rows,self.probes,self.proof)['receipt_permissions'],0)

    def test_mql_source_default_off_and_read_only_scope(self):
        s=(ROOT/'mt5/Scripts/ForexDemoSharing064.mq5').read_text()
        self.assertIn('input bool ReadSyntheticEvidence=false;',s)
        start=s[s.index('void OnStart()'):]
        self.assertLess(start.index('if(!ReadSyntheticEvidence)'),start.index('GetTickCount64()'))
        self.assertIn('FILE_READ|FILE_BIN|FILE_SHARE_READ',s)
        for token in ('FILE_WRITE','FILE_SHARE_WRITE','FILE_COMMON','FileWrite','FileFlush',
                      'FileDelete','FileMove','SymbolInfoTick','CopyTicks','CopyRates','OrderSend',
                      'CTrade','TimeCurrent','ReadingReason042','AccountInfoDouble','#import'):
            self.assertNotIn(token,s)
        self.assertEqual(s.count('FileOpen('),1);self.assertEqual(s.count('FileReadArray('),1)
        self.assertEqual(s.count('FileClose('),1)
        self.assertIn('AccountReason042(s,p.identified,p.login,p.server)',s)

    def test_pure_mql_hold_and_byte_decisions_match(self):
        cases=[(100000,100000+d,d*1000,i,False,True)
               for d in (29999,30000,30500,31000,31001) for i in (0,1,601,602)]
        cases += [(0,30000,30000000,600,False,True),(100001,100000,0,1,False,True),
                  (100000,130000,-1,600,False,True),(100000,130000,30000000,600,True,True),
                  (100000,130000,30000000,600,False,False),
                  (9007199254740990,9007199254770990,30000000,600,False,True),
                  (100000,131000,30000000,600,False,True),(100000,130000,31000000,600,False,True)]
        with TemporaryDirectory() as tmp:
            exe=Path(tmp)/'hold064'
            subprocess.run(['g++','-std=c++17','-Wall','-Wextra','-Werror',str(ROOT/'mt5/Tests/SharingHold064.cpp'),'-o',str(exe)],check=True,capture_output=True,timeout=30)
            inp=''.join(' '.join(str(int(x)) for x in c)+'\n' for c in cases)
            out=subprocess.run([str(exe)],input=inp,capture_output=True,text=True,check=True,timeout=5)
        expected=[hold_reason(*c) for c in cases]+[-1,*DATA,-1]
        self.assertEqual(list(map(int,out.stdout.split())),expected)
        self.assertEqual(len(expected),114)

    def test_schema_failure_reports_no_upstream_private_details(self):
        self.rows=[{'private':'account path'},record(True)]
        with self.assertRaisesRegex(ValueError,'^sharing_evidence_rejected$') as e:
            match_evidence(self.rows,self.probes,self.proof)
        self.assertNotIn('account',str(e.exception))
