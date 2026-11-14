import copy
from datetime import datetime,timezone
import json
from pathlib import Path
import re
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from forex_demo_lab.clock_observer_042 import *
from forex_demo_lab.native_compiler_042 import SOURCE,HEADER,staging_command,native_command
ROOT=Path(__file__).resolve().parents[1]

def disabled():return dict(version=VERSION,accepted=False,reason_code=17,quote_reads=0)
def success():
    g=int(datetime(2026,10,6,17,50,tzinfo=timezone.utc).timestamp());s=g+10800
    return dict(version=VERSION,accepted=True,reason_code=0,quote_reads=1,guard_checks=5,
        time_current_before_s=s,time_current_after_s=s,calculated_server_before_s=s,calculated_server_after_s=s,
        gmt_before_s=g,gmt_after_s=g,local_before_s=g+7200,local_after_s=g+7200,
        tick_time_s=s,tick_time_msc=s*1000+500,bid=1.1,ask=1.10001,tick_flags=1158,elapsed_us=100)
def encode(r):return PREFIX+json.dumps(r)
def fake():
    class API:
        ACCOUNT_TRADE_MODE_DEMO=0
        terminal=SimpleNamespace(connected=True,trade_allowed=False)
        account=SimpleNamespace(trade_mode=0,currency='USD',login=123,server='PRIVATE')
        symbol=SimpleNamespace(visible=True,currency_base='EUR',currency_profit='USD')
        def terminal_info(self):return self.terminal
        def account_info(self):return self.account
        def symbol_info(self,name):return self.symbol
    return API()

class ClockObserver042Tests(unittest.TestCase):
    def test_exact_new_mql_derivation(self):
        for old,new in (('Scripts/ForexDemoClockObserver038.mq5','Scripts/ForexDemoClockObserver042.mq5'),
                        ('Scripts/ClockGuard038.mqh','Scripts/ClockGuard042.mqh'),('Tests/ClockGuard038.cpp','Tests/ClockGuard042.cpp')):
            expected=(ROOT/'mt5'/old).read_text().replace('038','042')
            if new.endswith('.mq5'):expected=expected.replace('#property strict\n','#property strict\n#property script_show_inputs\n')
            self.assertEqual((ROOT/'mt5'/new).read_text(),expected)
    def test_exact_shared_guard_header(self):
        with tempfile.TemporaryDirectory() as d:
            exe=Path(d)/'guards'
            subprocess.run(['g++','-std=c++17','-Wall','-Wextra','-Werror',str(ROOT/'mt5/Tests/ClockGuard042.cpp'),'-o',str(exe)],
                capture_output=True,text=True,check=True,timeout=30)
            result=subprocess.run([str(exe)],capture_output=True,text=True,check=True,timeout=5)
            self.assertEqual(json.loads(result.stdout),dict(guard_checks=73,passed=True))
    def test_disabled_one_shot_call_and_privacy_guards(self):
        text=(ROOT/'mt5/Scripts/ForexDemoClockObserver042.mq5').read_text()
        self.assertIn('input bool CollectClockEvidence = false;',text);self.assertIn('#property script_show_inputs',text)
        self.assertEqual(len(re.findall(r'\bSymbolInfoTick\s*\(',text)),1)
        self.assertEqual(len(re.findall(r'\bAccountReason042\s*\(',text)),5)
        self.assertIn('if(!CollectClockEvidence) { StopClock042(17, 0); return; }',text)
        self.assertNotRegex(text,r'\b(OnTick|OnTimer|FileOpen|SymbolSelect|OrderSend|CopyTicks|CopyRates)\s*\(')
        for line in text.splitlines():
            if 'PrintFormat(' in line:self.assertNotRegex(line,r'identity_login|identity_server|state\.login|state\.server')
    def test_valid_payload_and_uncertainty_intervals(self):
        r=success();self.assertEqual(parse_record(encode(r)),r)
        result=comparison(r)
        self.assertEqual(result['raw_tick_minus_gmt_interval_ms'],[10799501,10800500])
        self.assertEqual(result['time_current_minus_gmt_interval_ms'],[10799001,10800999])
        self.assertEqual(result['local_minus_gmt_interval_ms'],[7199001,7200999])
        self.assertFalse(result['historical_clock_certified']);self.assertFalse(result['offset_correction_authorized'])
    def test_extra_private_keys_and_wrong_versions_rejected(self):
        for key,value in (('login',123),('server','PRIVATE'),('version','clock_observer_038_v1')):
            r=success();r[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):parse_record(encode(r))
    def test_duplicate_keys_and_invalid_prefix(self):
        text=encode(disabled()).replace('"quote_reads": 0','"quote_reads": 0, "quote_reads": 1')
        for bad in (text,'FXDL_CLOCK038 '+json.dumps(disabled()),'prefix '+encode(disabled()),encode(disabled())+' trailing'):
            with self.subTest(bad=bad),self.assertRaises(ValueError):parse_record(bad)
    def test_strict_types_and_counter_budgets(self):
        for key,value in (('accepted',1),('reason_code',False),('quote_reads',True),('quote_reads',2),('guard_checks',4),('elapsed_us',1.0),('tick_flags',True)):
            r=success();r[key]=value
            with self.subTest(key=key,value=value),self.assertRaises(ValueError):parse_record(encode(r))
    def test_tick_floor_overflow_and_nonpositive(self):
        for key,value in (('tick_time_msc',1),('tick_time_msc',32535216000000),('tick_time_s',0),('time_current_before_s',0)):
            r=success();r[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):parse_record(encode(r))
    def test_stale_and_future_quote_age(self):
        for delta in (-60001,2001):
            r=success();r['tick_time_msc']=r['time_current_after_s']*1000+delta;r['tick_time_s']=r['tick_time_msc']//1000
            with self.subTest(delta=delta),self.assertRaises(ValueError):parse_record(encode(r))
    def test_native_clock_reversal(self):
        for field in ('time_current','calculated_server','gmt','local'):
            r=success();r[field+'_after_s']-=1
            with self.subTest(field=field),self.assertRaises(ValueError):parse_record(encode(r))
    def test_expired_native_date(self):
        r=success();r['gmt_before_s']-=86400;r['gmt_after_s']-=86400
        with self.assertRaises(ValueError):parse_record(encode(r))
    def test_timeout_and_wall_discontinuity(self):
        for key,value in (('elapsed_us',15000001),('elapsed_us',-1),('elapsed_us',3000000)):
            r=success();r[key]=value
            with self.subTest(value=value),self.assertRaises(ValueError):parse_record(encode(r))
    def test_price_and_unsigned_flag_validation(self):
        for key,value in (('bid',0),('bid',2),('ask',float('nan')),('bid',float('inf')),('ask',True),('tick_flags',-1),('tick_flags',4294967296)):
            r=success();r[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):parse_record(encode(r))
    def test_failure_schema_disabled_reads_and_codes(self):
        self.assertEqual(parse_record(encode(disabled())),disabled())
        for key,value in (('quote_reads',1),('reason_code',0),('reason_code',20),('accepted','false')):
            r=disabled();r[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):parse_record(encode(r))
    def test_logs_filter_unrelated_private_lines_and_ambiguity(self):
        raw=('PRIVATE account 123\n10:00 script '+encode(disabled())+'\nPRIVATE server\n').encode('utf-16-le')
        self.assertEqual(records_from_log(raw),[disabled()])
        with self.assertRaises(ValueError):records_from_log((encode(disabled())+encode(disabled())).encode('utf-16-le'))
        with self.assertRaises(ValueError):records_from_log(b'x')
        with self.assertRaises(ValueError):records_from_log(b'\0'*1048578)
    def test_disabled_proof_required_before_capture(self):
        s=RuntimeSequence()
        with self.assertRaises(ValueError):s.arm(True)
        s.arm(False);s.collect([disabled()]);s.arm(True);s.collect([success()])
        self.assertEqual(s.arms,[False,True]);self.assertEqual(sum(r['quote_reads'] for r in s.records),1)
    def test_repeated_arms_and_duplicate_records_rejected(self):
        s=RuntimeSequence();s.arm(False)
        with self.assertRaises(ValueError):s.arm(False)
        with self.assertRaises(ValueError):s.collect([disabled(),disabled()])
        s.collect([disabled()])
        with self.assertRaises(ValueError):s.arm(False)
        s.arm(True);s.collect([success()])
        with self.assertRaises(ValueError):s.arm(True)
        with self.assertRaises(ValueError):s.collect([success()])
    def test_native_enabled_rejection_is_preserved(self):
        s=RuntimeSequence();s.arm(False);s.collect([disabled()]);s.arm(True)
        bad=dict(version=VERSION,accepted=False,reason_code=8,quote_reads=1)
        with self.assertRaises(ValueError):s.collect([bad])
        self.assertEqual(s.records[-1],bad);self.assertEqual(sum(r['quote_reads'] for r in s.records),1)
    def test_actual_account_and_identity_guards(self):
        a=fake();identity=runtime_guard(a);self.assertEqual(identity,(123,'PRIVATE'))
        for field,value in (('trade_mode',1),('trade_mode',2),('trade_mode',True),('currency','EUR'),('login',0),('server','')):
            a=fake();setattr(a.account,field,value)
            with self.subTest(field=field,value=value),self.assertRaises(ValueError):runtime_guard(a)
        for field,value in (('connected',False),('trade_allowed',True)):
            a=fake();setattr(a.terminal,field,value)
            with self.subTest(field=field),self.assertRaises(ValueError):runtime_guard(a)
        a=fake();a.account.login=124
        with self.assertRaises(ValueError):runtime_guard(a,identity)
        a=fake();a.symbol.visible=False
        with self.assertRaises(ValueError):runtime_guard(a)
    def test_frozen_source_coverage_and_no_sdk_quotes_or_execution(self):
        driver=(ROOT/'scripts/native-compiler-042.py').read_text();worker=(ROOT/'scripts/clock-runtime-042.py').read_text()
        for name in ('scripts/native-compiler-042.py','scripts/check-native-compiler-042.py','scripts/clock-runtime-042.py',
                     'scripts/check-clock-runtime-042.py','scripts/finalize-clock-observer-042.py','tests/test_clock_observer_042.py'):
            self.assertIn(name,driver)
        self.assertIn('assert required<=set(bindings)',driver)
        self.assertIn('not RESERVATION.exists()',worker)
        for name in ('symbol_info_tick','copy_ticks','copy_rates','order_send','positions_get','launch_app','terminal64.exe /'):
            self.assertNotIn(name,worker)
        command=staging_command('C:/Owned','a'*32,{SOURCE:'C:/042.mq5',HEADER:'C:/042.mqh'})
        self.assertIn('Get-Item -LiteralPath $cursor -Force',command);self.assertIn('ReparsePoint',command)
        self.assertIn(SOURCE,command);self.assertIn(HEADER,command);self.assertNotIn('038.mq5',command)
        self.assertIn('/compile:"C:\\a & $ ;.mq5"',native_command('C:/editor.exe','C:/a & $ ;.mq5','C:/a.log'))
