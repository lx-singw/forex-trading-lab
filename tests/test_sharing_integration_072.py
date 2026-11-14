from dataclasses import replace
import hashlib
import json
from pathlib import Path,PureWindowsPath
import subprocess
from tempfile import TemporaryDirectory
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch

from forex_demo_lab.mql_sharing_072 import *
from forex_demo_lab.sharing_integration_072 import *
from forex_demo_lab.sharing_runtime_069 import ObservedCompanion069,Resources069,LIMITS069
from forex_demo_lab.private_guard_065 import Identity065
from forex_demo_lab.sharing_probe_062 import ProbeRejected
from test_sharing_runtime_066 import ExternalFiles
from test_transport_lifecycle_060 import Clock
from test_sharing_companion_065 import Reader
from test_fresh_data_031 import API as AccountAPI
from test_mql_sharing_064 import record as old_record,text as old_text

ROOT=Path(__file__).resolve().parents[1]


def record072(enabled=False):
    return {**old_record(enabled),'version':'sharing_fixture_072_v1','phase':PHASE}
def text072(r):return PREFIX+json.dumps(r)


class Integration072Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        self.clock=Clock();self.clock.utc+=86400000;self.clock.boot=99000
        self.m=Meter072(self.clock);self.trace=Trace069()
        self.bindings=dict.fromkeys(BINDING_KEYS,'a'*64)
        self.s=Reservation072(self.root/'reservation',self.bindings,self.m)
        self.guard=lambda:True;self.f=ExternalFiles(self.m,self.clock)
        self.c=ObservedCompanion069(Companion072(self.f,self.m,lambda:self.guard()),self.trace)
        self.log=self.root/'log';self.log.write_bytes('old\r\n'.encode('utf-16-le'))
        self.r=Runtime072(self.c,self.s,self.m,lambda:self.guard(),self.log,self.clock.advance,trace=self.trace)
    def prepared(self):
        for cmd in COMMANDS[:3]:self.r.command(cmd)
    def armed(self):self.prepared();self.clock.advance(1000);self.r.command('arm-enabled')
    def probed(self):self.armed();self.r.command('probe')
    def saved(self,rows=None):
        with self.log.open('ab') as f:f.write(('\r\n'.join(text072(x) for x in (rows or [record072(),record072(True)]))+'\r\n').encode('utf-16-le'))
        self.r.command('logs-saved')
    def reject(self,cmd,reason):
        with self.assertRaisesRegex(ProbeRejected,'^'+reason+'$'):self.r.command(cmd)
        out=self.r.finish();self.assertFalse(out['completed']);self.assertFalse(self.f.active)
        self.assertEqual(out['stop_reason'],reason);return out
    def account_guard(self):
        a=AccountAPI();a.terminal.path=r'C:\Program Files\MetaTrader 5';a.terminal.data_path=r'C:\private-demo';a.terminal.build=6244
        peer=Identity065(7,11,r'c:\program files\metatrader 5\terminal64.exe','a'*64,1,'private-logon')
        reader=Reader(peer,self.m)
        g=FullGuard072(a,reader,peer,a.terminal.data_path,6244,('editor','a'*64),('artifact','a'*64),self.m)
        return a,reader,g
    def contract(self):return source_contract072(dict.fromkeys(SOURCE_INPUTS,'a'*64))
    def build(self):
        return dict(version='sharing_build_072_v1',phase=PHASE,date=DATE,input_bindings=self.contract()['input_bindings'],
            artifact_name='ForexDemoSharing072.ex5',artifact_sha256='b'*64,compiler_sha256='c'*64,
            terminal_sha256='d'*64,terminal_build=6244,compiler_invocations=1,exit_code=0,errors=0,warnings=0)
    def test_fresh_injected_sequence_matches_new_phase_and_date(self):
        self.probed();self.saved();out=self.r.finish();self.assertTrue(out['completed'])
        self.assertEqual((out['phase'],out['date'],out['diagnostics']['phase']),(PHASE,DATE,PHASE))
        self.assertEqual([p.stage for p in self.c.probes],['pre','pre','independent','independent','post','post'])
        self.assertFalse(out['native_mql_verified']);self.assertFalse(out['orders_available'])
    def test_old_phase_and_version_are_rejected(self):
        for changes in ({'phase':old_record()['phase']},{'version':old_record()['version']}):
            with self.assertRaises(ValueError):parse_record(text072({**record072(True),**changes}))
    def test_old_prefix_never_yields_fresh_record(self):
        self.assertEqual(records_from_log(old_text(old_record(True)).encode('utf-16-le')),[])
        with self.assertRaises(ValueError):parse_record(old_text(old_record(True)))
    def test_duplicate_keys_and_unknown_private_fields_rejected(self):
        bad=text072(record072(True)).replace('"opens": 1','"opens": 1, "opens": 1')
        with self.assertRaises(ValueError):parse_record(bad)
        with self.assertRaisesRegex(ValueError,'^sharing_record_rejected$') as e:
            parse_record(text072({**record072(True),'account':'private'}))
        self.assertNotIn('private',str(e.exception))
    def test_integer_booleans_and_nonzero_financial_counts_rejected(self):
        for k in KEYS-{'version','phase','pattern_ok'}:
            with self.assertRaises(ValueError):parse_record(text072({**record072(True),k:True}))
        for k in ('quote_reads','history_reads','orders','receipt_permissions'):
            with self.assertRaises(ValueError):parse_record(text072({**record072(True),k:1}))
    def test_wrong_bytes_and_hold_duration_rejected(self):
        for changes in ({'read_bytes':83},{'pattern_ok':False},{'hold_end_boot_ms':129999,'hold_elapsed_us':29999000},
                        {'hold_end_boot_ms':131001,'hold_elapsed_us':31001000}):
            with self.assertRaises(ValueError):parse_record(text072({**record072(True),**changes}))
    def test_disabled_has_no_file_activity(self):
        self.assertEqual(parse_record(text072(record072())),record072())
        with self.assertRaises(ValueError):parse_record(text072({**record072(),'opens':1}))
    def test_log_bounds_encoding_and_ambiguous_prefix(self):
        for raw in (b'x',b'\0'*65538,b'\x00\xd8',(PREFIX+text072(record072())).encode('utf-16-le')):
            with self.assertRaises(ValueError):records_from_log(raw)
    def test_fresh_matcher_requires_new_date(self):
        self.probed();self.saved();proof=PrivateProof(True,True,True,True,True,True,True,True,'2026-10-07')
        with self.assertRaises(ValueError):match_evidence(self.r.rows,self.c.probes,proof)
    def test_control_masking_and_wrong_error_cannot_match(self):
        self.probed();self.saved();proof=PrivateProof(True,True,True,True,True,True,True,True,DATE)
        for changes in ({'blocking_companion_handles':1},{'error':5},{'opened':True}):
            probes=list(self.c.probes);probes[2]=replace(probes[2],**changes)
            with self.assertRaises(ValueError):match_evidence(self.r.rows,probes,proof)
    def test_missing_private_proof_and_boundary_margin_rejected(self):
        self.probed();self.saved();proof=PrivateProof(True,True,True,True,True,True,True,True,DATE)
        with self.assertRaises(ValueError):match_evidence(self.r.rows,self.c.probes,replace(proof,full_hashes_rechecked=False))
        probes=list(self.c.probes);probes[2]=replace(probes[2],start_boot_ms=100250,end_boot_ms=100251)
        with self.assertRaises(ValueError):match_evidence(self.r.rows,probes,proof)
    def test_wrong_date_rejected_at_meter_construction(self):
        for delta in (-86400000,86400000):
            clock=Clock();clock.utc+=86400000+delta
            with self.assertRaisesRegex(ProbeRejected,'^fresh_date_rejected$'):Meter072(clock)
    def test_midnight_expiry_still_closes_files(self):
        self.prepared();self.clock.utc+=86400000
        # Coherent clocks can cross midnight as well as the total session bound.
        self.clock.mono+=86400000000000;self.clock.boot+=86400000
        out=self.r.finish();self.assertFalse(out['completed']);self.assertFalse(self.f.active)
        self.assertTrue(out['cleanup']['all_handles_closed'])
    def test_coherent_midnight_within_session_rejected(self):
        clock=Clock();clock.utc=1791503999000;meter=Meter072(clock);clock.advance(1000)
        with self.assertRaisesRegex(ProbeRejected,'^fresh_date_rejected$'):meter.check()
    def test_clock_reversal_during_probe_rejected(self):
        self.armed();self.clock.mono-=1;self.reject('probe','command_order:clock_rejected')
    def test_reservation_has_exact_fresh_schema_and_no_sidecar(self):
        raw=(self.root/'reservation').read_bytes();r=json.loads(raw)
        self.assertEqual((r['version'],r['phase'],r['mql_phase'],r['date']),('sharing_reservation_072_v1',PHASE,PHASE,DATE))
        self.assertEqual(r['bindings'],self.bindings);self.assertFalse((self.root/'reservation.sha256').exists())
        self.assertEqual(len(hashlib.sha256(raw).hexdigest()),64)
    def test_restart_cannot_reuse_reservation(self):
        raw=(self.root/'reservation').read_bytes()
        with self.assertRaises(ProbeRejected):Reservation072(self.root/'reservation',self.bindings,Meter072(self.clock))
        self.assertEqual((self.root/'reservation').read_bytes(),raw)
    def test_missing_hold_binding_or_unknown_binding_rejected(self):
        for changes in ({k:v for k,v in self.bindings.items() if k!='hold'},{**self.bindings,'extra':'a'*64}):
            with self.assertRaises(ProbeRejected):Reservation072(self.root/'new',changes,self.m)
        self.assertFalse((self.root/'new').exists())
    def test_sdk_attempt_and_arm_are_not_refunded(self):
        self.s.sdk_attempt()
        with self.assertRaises(ProbeRejected):self.s.sdk_attempt()
        self.s.arm('disabled');self.s.arm('enabled')
        with self.assertRaises(ProbeRejected):self.s.arm('enabled')
        self.assertEqual(self.m.counts['sdk_connections'],1);self.assertEqual(self.s.arms,['disabled','enabled'])
    def test_duplicate_command_cannot_arm_again(self):
        self.r.command('baseline-saved');self.r.command('arm-disabled')
        self.reject('arm-disabled','command_order:order_rejected');self.assertEqual(self.s.arms,['disabled'])
    def test_late_probe_has_relative_diagnostics_without_widened_gate(self):
        self.armed();self.clock.advance(10001);out=self.reject('probe','probe_launch_window:window_rejected')
        self.assertEqual(out['diagnostics']['metrics']['arm_to_window_check_ms'],10001)
        self.assertEqual(out['counts']['schedule_waits'],0)
    def test_post_arm_and_probe_guard_time_both_count(self):
        self.prepared();self.clock.advance(1000)
        def guard():
            self.clock.advance(5000 if self.s.arms==['disabled','enabled'] else 0);return True
        self.guard=guard;self.r.command('arm-enabled')
        self.guard=lambda:self.clock.advance(6000) or True
        out=self.reject('probe','probe_launch_window:window_rejected');d=out['diagnostics']['metrics']
        self.assertEqual((d['arm_to_ready_ms'],d['arm_to_probe_receipt_ms'],d['arm_to_window_check_ms']),(5000,5000,11000))
    def test_wrong_independent_error_stops_before_post_controls(self):
        self.armed();self.f.error='access_denied';out=self.reject('probe','independent_controls:controls_failed')
        self.assertEqual(out['counts']['schedule_waits'],1)
    def test_post_control_failure_is_not_hidden(self):
        self.armed();original=self.c.controls
        def controls(stage):
            if stage=='post':raise ValueError('private')
            return original(stage)
        self.c.controls=controls;self.reject('probe','post_controls:controls_failed')
    def test_frozen_wait_clock_has_finite_budget(self):
        self.armed();calls=[];self.r.wait=lambda ms:calls.append(ms)
        self.reject('probe','wait5_loop:wait_rejected');self.assertEqual(len(calls),36)
    def test_old_log_records_cannot_complete_fresh_runtime(self):
        self.probed()
        with self.log.open('ab') as f:f.write((old_text(old_record())+'\r\n'+old_text(old_record(True))).encode('utf-16-le'))
        self.reject('logs-saved','saved_range_read:saved_log_failed')
    def test_saved_range_replacement_and_repeat_read_rejected(self):
        saved=SavedRange072(self.log,self.m);self.log.rename(self.root/'old');self.log.write_bytes(b'\0'*100)
        with self.assertRaises(ProbeRejected):saved.read()
        with self.assertRaises(ProbeRejected):saved.read()
        self.assertEqual(self.m.counts['log_reads'],1)
    def test_first_failure_survives_cleanup_exception(self):
        self.armed();self.clock.advance(10001);original=self.c.finish
        def finish():original();raise ValueError('private account')
        self.c.finish=finish;out=self.reject('probe','probe_launch_window:window_rejected')
        self.assertNotIn('private',json.dumps(out));self.assertEqual(out['diagnostics']['events'][-1]['failure_code'],'cleanup_unconfirmed')
    def test_uncertain_cleanup_cannot_pass(self):
        self.probed();self.saved();original=self.c.finish;self.c.finish=lambda:{**original(),'unconfirmed_handles':False}
        out=self.r.finish();self.assertFalse(out['completed']);self.assertEqual(out['stop_reason'],'cleanup_validate:cleanup_unconfirmed')
    def test_resource_owner_shutdown_once_after_expiry(self):
        self.prepared();self.s.sdk_attempt();calls=[];owner=Resources069(self.s,self.m,self.trace)
        owner.runner=self.r;owner.sdk=NS(shutdown=lambda:calls.append('shutdown'));self.clock.advance(900000)
        out=owner.close();self.assertFalse(self.f.active);self.assertEqual(calls,['shutdown'])
        self.assertFalse(out['outcome']['completed'])
        with self.assertRaises(ProbeRejected):owner.close()
    def test_diagnostic_exhaustion_still_closes_owned_handles(self):
        self.prepared()
        while len(self.r.diagnostics.events)<192:self.r.diagnostics.run('command_order','order_rejected',lambda:True)
        out=self.r.finish();self.assertFalse(out['completed']);self.assertFalse(self.f.active)
        self.assertTrue(out['diagnostics']['diagnostics_exhausted'])
    def test_real_and_contest_rejected_by_actual_type(self):
        for mode in (1,2):
            a,reader,g=self.account_guard();a.account.trade_mode=mode;a.account.server='demo-looking-name'
            with self.assertRaises(ProbeRejected):g()
        self.assertEqual(self.m.counts['directories'],0)
    def test_full_guard_rehashes_both_times(self):
        a,reader,g=self.account_guard();self.assertTrue(g());self.assertTrue(g())
        self.assertEqual(reader.hashes,['editor','artifact']*2);self.assertEqual(reader.identities,4)
    def test_account_or_algo_change_latches_guard(self):
        a,reader,g=self.account_guard();g();a.terminal.trade_allowed=True
        with self.assertRaises(ProbeRejected):g()
        a.terminal.trade_allowed=False
        with self.assertRaises(ProbeRejected):g()
    def test_fresh_backend_paths_are_separate_from_consumed_sandbox(self):
        parent,root,fixture=terminal_paths072(r'C:\private-demo')
        self.assertEqual(root.name,SANDBOX);self.assertEqual(fixture.parent,root)
        self.assertNotIn('Sharing064',str(fixture));self.assertEqual(parent,PureWindowsPath(r'C:\private-demo\MQL5\Files'))
    def test_native_constructor_never_runs_in_offline_tests(self):
        with patch.object(NativeFiles065,'__init__',side_effect=AssertionError('native constructor')) as call:
            with self.assertRaises(ProbeRejected):NativeFiles072(self.m,self.root,'compatibility')
            call.assert_not_called()
        self.assertEqual(self.m.counts['native_calls'],0)
    def test_guard_rejects_old_native_backend_and_wrong_sandbox(self):
        a,reader,g=self.account_guard()
        with self.assertRaises(ProbeRejected):g.bind_files(NS(scope='terminal'))
        files=object.__new__(NativeFiles072);files.scope='terminal'
        files.parent,files.root,files.fixture=terminal_paths072(a.terminal.data_path)
        files.root=files.parent/'ForexDemoSharing064-used'
        with self.assertRaises(ProbeRejected):g.bind_files(files)
        self.assertEqual(reader.identities,0)
    def test_runtime_rejects_old_meter_or_session(self):
        with self.assertRaises(ProbeRejected):Runtime072(self.c,self.s,Meter069(Clock()),self.guard,self.log,self.clock.advance,trace=self.trace)
        with self.assertRaises(ProbeRejected):Runtime072(self.c,NS(meter=self.m),self.m,self.guard,self.log,self.clock.advance,trace=self.trace)
        old=ObservedCompanion069(Companion065(self.f,self.m,self.guard),self.trace)
        with self.assertRaises(ProbeRejected):Runtime072(old,self.s,self.m,self.guard,self.log,self.clock.advance,trace=self.trace)
    def test_build_contract_is_exact_and_does_not_authorize_runtime(self):
        out=validate_build072(self.build(),self.contract(),'c'*64,'d'*64)
        self.assertTrue(out['build_contract_matched']);self.assertFalse(out['orders_available'])
        self.assertFalse(self.contract()['compiled']);self.assertEqual(self.contract()['maximum_native_sessions'],0)
    def test_build_rejects_old_phase_wrong_input_or_compiler(self):
        for changes in ({'phase':'64'*16},{'input_bindings':{}},{'compiler_sha256':'e'*64},{'artifact_name':'ForexDemoSharing064.ex5'},
                        {'terminal_sha256':'e'*64},{'extra':0}):
            with self.assertRaises(ProbeRejected):validate_build072({**self.build(),**changes},self.contract(),'c'*64,'d'*64)
    def test_build_rejects_warnings_errors_bool_exit_and_bad_digest(self):
        for changes in ({'warnings':1},{'errors':1},{'exit_code':False},{'compiler_invocations':True},{'artifact_sha256':'bad'}):
            with self.assertRaises(ProbeRejected):validate_build072({**self.build(),**changes},self.contract(),'c'*64,'d'*64)
        with self.assertRaises(ProbeRejected):validate_build072(self.build(),{**self.contract(),'compiled':0},'c'*64,'d'*64)
    def test_source_contract_requires_exact_include_closure(self):
        b=self.contract()['input_bindings'];b.pop('mt5/Scripts/SharingHold072.mqh')
        with self.assertRaises(ProbeRejected):source_contract072(b)
    def test_source_is_default_off_read_only_and_fresh_dated(self):
        s=(ROOT/SOURCE_INPUTS[0]).read_text();start=s[s.index('void OnStart()'):]
        self.assertLess(start.index('if(!ReadSyntheticEvidence)'),start.index('GetTickCount64()'))
        self.assertIn('input bool ReadSyntheticEvidence=false;',s);self.assertIn('2026.10.08',s)
        self.assertIn(PHASE,s);self.assertIn('ForexDemoSharing072-',s);self.assertIn('FILE_READ|FILE_BIN|FILE_SHARE_READ',s)
        self.assertIn('AccountReason042(s,p.identified,p.login,p.server)',s)
        for token in ('2026.10.07','ForexDemoSharing064','FILE_WRITE','FILE_COMMON','SymbolInfoTick','CopyTicks','CopyRates','OrderSend','CTrade','#import'):
            self.assertNotIn(token,s)
        self.assertEqual((s.count('FileOpen('),s.count('FileReadArray('),s.count('FileClose(')),(1,1,1))
    def test_pure_new_hold_header_matches_reviewed_decisions(self):
        cases=[(100000,100000+d,d*1000,i,False,True) for d in (29999,30000,30500,31000,31001) for i in (0,1,601,602)]
        cases += [(0,30000,30000000,600,False,True),(100001,100000,0,1,False,True),
            (100000,130000,-1,600,False,True),(100000,130000,30000000,600,True,True),
            (100000,130000,30000000,600,False,False),
            (9007199254740990,9007199254770990,30000000,600,False,True),
            (100000,131000,30000000,600,False,True),(100000,130000,31000000,600,False,True)]
        with TemporaryDirectory() as tmp:
            exe=Path(tmp)/'hold072'
            subprocess.run(['g++','-std=c++17','-Wall','-Wextra','-Werror',str(ROOT/'mt5/Tests/SharingHold072.cpp'),'-o',str(exe)],check=True,capture_output=True,timeout=30)
            inp=''.join(' '.join(str(int(x)) for x in c)+'\n' for c in cases)
            out=subprocess.run([str(exe)],input=inp,capture_output=True,text=True,check=True,timeout=5)
        expected=[hold_reason(*c) for c in cases]+[-1,*DATA,-1]
        self.assertEqual(list(map(int,out.stdout.split())),expected);self.assertEqual(len(expected),114)
    def test_injected_success_exports_no_native_or_market_claim(self):
        self.probed();self.saved();out=self.r.finish()
        for k in ('native_mql_verified','native_publication_verified','fresh_performance_eligible','annual_eligible','orders_available'):
            self.assertFalse(out[k])
        for k in ('sdk_connections','native_calls','deployment_writes'):self.assertEqual(out['counts'][k],0)
        self.assertEqual(LIMITS069['hash_bytes'],103079215104)
    def test_fresh_clock_rejects_shape_boolean_float_and_negative(self):
        now=self.clock()
        for sample in ([*now],now[:2],(now[0],True,now[2]),(now[0],float(now[1]),now[2]),(now[0],-1,now[2])):
            with self.assertRaisesRegex(ProbeRejected,'^fresh_clock_rejected$'):Meter072(lambda:sample)
    def test_fresh_clock_discontinuity_and_all_three_reversals(self):
        for index in (0,1,2):
            clock=Clock();clock.utc+=86400000;meter=Meter072(clock);clock.advance(1)
            meter.check();values=list(clock());values[index]-=1;meter.clock=lambda:tuple(values)
            with self.assertRaisesRegex(ProbeRejected,'^clock_reversed$'):meter.check()
        clock=Clock();clock.utc+=86400000;meter=Meter072(clock);clock.utc+=1001
        with self.assertRaisesRegex(ProbeRejected,'^clock_discontinuity$'):meter.check()
    def test_session_and_clock_sample_budgets_not_extended(self):
        clock=Clock();clock.utc+=86400000;meter=Meter072(clock);clock.advance(900000)
        with self.assertRaisesRegex(ProbeRejected,'^session_expired$'):meter.check()
        clock=Clock();clock.utc+=86400000;meter=Meter072(clock);meter.counts['clock_samples']=LIMITS069['clock_samples']
        with self.assertRaisesRegex(ProbeRejected,'^clock_budget_exhausted$'):meter.check()
    def test_new_sampler_does_not_change_old_oct7_sampler(self):
        from forex_demo_lab.capture_budget_047 import clock_sample,PermitRejected
        self.assertEqual(clock_sample(Clock()),Clock()())
        with self.assertRaises(PermitRejected):clock_sample(self.clock)
    def test_fresh_native_constructor_changes_paths_before_any_file_io(self):
        def metadata_only(this,meter,parent,scope):
            this.parent=Path(parent);this.scope=scope;this.meter=meter
            this.root=this.parent/'ForexDemoSharing064-used';this.fixture=this.root/'synthetic.bin'
        with patch.object(NativeFiles065,'__init__',metadata_only),patch.object(NativeFiles065,'setup',side_effect=AssertionError('IO')):
            files=NativeFiles072(self.m,self.root,'terminal')
        self.assertEqual(files.root,self.root/SANDBOX);self.assertEqual(files.fixture,files.root/'synthetic.bin')
        self.assertEqual(self.m.counts['native_calls'],0)
    def test_fresh_matcher_rejects_duplicate_and_reversed_rows(self):
        self.probed();self.saved();proof=PrivateProof(True,True,True,True,True,True,True,True,DATE)
        for rows in (self.r.rows+[record072(True)],list(reversed(self.r.rows))):
            with self.assertRaises(ValueError):match_evidence(rows,self.c.probes,proof)
    def test_fresh_matcher_rejects_overlapping_or_late_controls(self):
        self.probed();self.saved();proof=PrivateProof(True,True,True,True,True,True,True,True,DATE)
        for changes in ({'start_boot_ms':140000,'end_boot_ms':140050},{'start_boot_ms':99999}):
            probes=list(self.c.probes);probes[2]=replace(probes[2],**changes)
            with self.assertRaises(ValueError):match_evidence(self.r.rows,probes,proof)
