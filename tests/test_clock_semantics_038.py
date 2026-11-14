import copy
import json
from pathlib import Path
import re
import runpy
import shutil
import struct
import subprocess
import tempfile
import unittest

from forex_demo_lab.clock_semantics_038 import VERSION,TARGETS,PATTERNS,native_clocks,receipt_intervals,research_valid

ROOT=Path(__file__).resolve().parents[1]


def tick(second,ms):return struct.pack('<qdddQqId',second,1.1,1.2,0,0,ms,1026,0)
def declaration():return dict(version=VERSION,targets=list(TARGETS),find_patterns=list(PATTERNS),budgets=dict(search=0,open=8,find=6))
def research():
    actions=[dict(index=i,kind='open',url=url,retrieved_utc='2026-10-06T15:00:00+00:00',status='retrieved') for i,url in enumerate(TARGETS)]
    return dict(version=VERSION,actions=actions,findings=[dict(id='one',url=TARGETS[0],summary='Summary.',limitation='Limited.')],
                market_requests=0,orders_available=False)
def clean_mql():
    text=(ROOT/'mt5/Scripts/ForexDemoClockObserver038.mq5').read_text()
    text=re.sub(r'//[^\n]*|/\*.*?\*/','',text,flags=re.S)
    return re.sub(r'"(?:\\.|[^"\\])*"','""',text)


class ClockSemanticsTests(unittest.TestCase):
    def test_native_fields_floor_relation(self):
        r=native_clocks(tick(1791291600,1791291600000)+tick(1791291600,1791291600999))
        self.assertEqual(r['rows'],2);self.assertEqual(r['clock_fields_decoded'],4)
        self.assertTrue(r['all_seconds_equal_floor_milliseconds']);self.assertEqual(r['residual_histogram'],{'0':1,'999':1})
    def test_contrary_rows_retained(self):
        r=native_clocks(tick(100,101000)+tick(101,100999))
        self.assertEqual([v['original_row_index'] for v in r['floor_relation_mismatches']],[0,1])
        self.assertEqual(r['floor_relation_mismatches'][1]['residual_ms'],-1)
    def test_invalid_binary(self):
        for value in (b'',b'x',tick(1,1000)+b'x',bytearray(tick(1,1000))):
            with self.assertRaises(ValueError):native_clocks(value)
    def test_nonpositive_native_fields(self):
        for second,ms in ((0,1000),(1,0),(-1,1000),(1,-1)):
            with self.assertRaises(ValueError):native_clocks(tick(second,ms))
    def test_all_reversals_retained(self):
        r=native_clocks(tick(2,2000)+tick(1,1001)+tick(1,1000))
        self.assertEqual(r['seconds_reversals'],[1]);self.assertEqual(r['milliseconds_reversals'],[1,2])
    def test_histogram_duplicates(self):
        r=native_clocks(tick(2,2010)*3)
        self.assertEqual(r['residual_histogram'],{'10':3});self.assertEqual(r['milliseconds_reversals'],[])
    def test_native_integer_precision(self):
        ms=9_007_199_254_740_999;s=ms//1000
        r=native_clocks(tick(s,ms));self.assertTrue(r['all_seconds_equal_floor_milliseconds'])
        self.assertEqual(r['milliseconds_max'],ms)
    def test_receipt_intervals(self):
        r=receipt_intervals([dict(raw_time_msc=10801000,received_before_utc_ms=1000,received_after_utc_ms=1002),
                             dict(raw_time_msc=10801999,received_before_utc_ms=2000,received_after_utc_ms=2001)])
        self.assertEqual(r['envelope_ms'],[10799998,10800000])
        self.assertEqual(r['distance_from_hypothetical_three_hours_ms'],[-2,0]);self.assertFalse(r['offset_correction_authorized'])
    def test_invalid_receipt_types(self):
        for value in (True,0,1.5,'1000'):
            with self.assertRaises(ValueError):receipt_intervals([dict(raw_time_msc=value,received_before_utc_ms=1,received_after_utc_ms=2)])
    def test_reversed_or_absent_receipts(self):
        for rows in ([],[dict(raw_time_msc=100,received_before_utc_ms=2,received_after_utc_ms=1)]):
            with self.assertRaises(ValueError):receipt_intervals(rows)
    def test_research_fixed_targets(self):
        self.assertEqual(research_valid(research(),declaration()),dict(search=0,open=8,find=0,findings=1))
    def test_research_search_and_alternate_url_rejected(self):
        for kind,url in (('search',TARGETS[0]),('open','https://www.mql5.com/en/forum/1'),('open',TARGETS[0]+'?retry=1')):
            r=research();r['actions'][0].update(kind=kind,url=url)
            with self.assertRaises(ValueError):research_valid(r,declaration())
    def test_research_retries(self):
        r=research();r['actions'][1]['url']=TARGETS[0]
        with self.assertRaises(ValueError):research_valid(r,declaration())
        r=research()
        for i in (8,9):r['actions'].append(dict(index=i,kind='find',url=TARGETS[0],pattern=PATTERNS[0],matched=True,retrieved_utc='2026-10-06T15:00:00+00:00'))
        with self.assertRaises(ValueError):research_valid(r,declaration())
    def test_research_find_budget(self):
        r=research()
        for i in range(7):r['actions'].append(dict(index=8+i,kind='find',url=TARGETS[i],pattern=PATTERNS[0],matched=False,retrieved_utc='2026-10-06T15:00:00+00:00'))
        with self.assertRaises(ValueError):research_valid(r,declaration())
    def test_research_declaration_cannot_change(self):
        d=declaration();d['budgets']['open']=9
        with self.assertRaises(ValueError):research_valid(research(),d)
        d=declaration();d['targets'].reverse()
        with self.assertRaises(ValueError):research_valid(research(),d)
    def test_attribution_requires_retrieved_source(self):
        for case in ('unavailable','outside','duplicate','empty'):
            r=research()
            if case=='unavailable':r['actions'][0]['status']='unavailable'
            if case=='outside':r['findings'][0]['url']='https://example.com/'
            if case=='duplicate':r['findings'].append(copy.deepcopy(r['findings'][0]))
            if case=='empty':r['findings'][0]['limitation']=''
            with self.assertRaises(ValueError):research_valid(r,declaration())
    def test_utc_action_receipts_and_privacy_schema(self):
        for field,value in (('retrieved_utc','2026-10-06T12:00:00'),('private_identity','secret')):
            r=research();r['actions'][0][field]=value
            with self.assertRaises(ValueError):research_valid(r,declaration())
        r=research();r['market_requests']=1
        with self.assertRaises(ValueError):research_valid(r,declaration())
    def test_exact_shared_native_guard_predicates(self):
        with tempfile.TemporaryDirectory() as directory:
            exe=Path(directory)/'guards'
            compiler=shutil.which('g++');self.assertIsNotNone(compiler)
            result=subprocess.run([compiler,'-std=c++17','-Wall','-Wextra','-Werror',str(ROOT/'mt5/Tests/ClockGuard038.cpp'),'-o',str(exe)],
                                  capture_output=True,text=True,timeout=30)
            self.assertEqual(result.returncode,0,result.stderr)
            result=subprocess.run([str(exe)],capture_output=True,text=True,timeout=5,check=True)
            self.assertEqual(json.loads(result.stdout),dict(guard_checks=73,passed=True))
    def test_mql_read_only_call_whitelist(self):
        calls=set(re.findall(r'\b([A-Za-z_]\w*)\s*\(',clean_mql()))
        allowed={'if','OnStart','StopClock038','ReadAccount038','ReadClocks038','AccountReason038','SymbolReason038','ReadingReason038',
            'PrintFormat','ResetLastError','GetLastError','TerminalInfoInteger','MQLInfoInteger','AccountInfoInteger','AccountInfoString',
            'SymbolInfoInteger','SymbolInfoString','GetMicrosecondCount','TimeCurrent','TimeTradeServer','TimeGMT','TimeLocal',
            'TimeToString','SymbolInfoTick','MathIsValidNumber'}
        self.assertEqual(calls,allowed)
        self.assertNotRegex(clean_mql(),r'\b(OnTick|OnTimer|FileOpen|SymbolSelect|OrderSend|CopyTicks|CopyRates)\s*\(')
    def test_one_shot_and_disabled_default(self):
        text=(ROOT/'mt5/Scripts/ForexDemoClockObserver038.mq5').read_text()
        self.assertIn('input bool CollectClockEvidence = false;',text)
        self.assertEqual(len(re.findall(r'\bSymbolInfoTick\s*\(',clean_mql())),1)
        self.assertIn('if(!CollectClockEvidence) { StopClock038(17, 0); return; }',text)
    def test_guard_composition_and_api_errors(self):
        text=clean_mql()
        self.assertEqual(len(re.findall(r'\bAccountReason038\s*\(',text)),5)
        for field in ('TERMINAL_CONNECTED','TERMINAL_TRADE_ALLOWED','MQL_TESTER','ACCOUNT_TRADE_MODE','ACCOUNT_CURRENCY','ACCOUNT_LOGIN','ACCOUNT_SERVER'):
            line=next(v for v in text.splitlines() if field in v)
            self.assertIn('ResetLastError()',line);self.assertIn('GetLastError() == 0',line)
        sample=text.index('SymbolInfoTick(')
        self.assertIn('AccountReason038(',text[:sample]);self.assertIn('AccountReason038(',text[sample:])
        self.assertLess(text.rindex('AccountReason038('),text.rindex('PrintFormat('))
    def test_output_whitelist_no_identity(self):
        text=(ROOT/'mt5/Scripts/ForexDemoClockObserver038.mq5').read_text()
        keys=set(re.findall(r'\\"([a-z_]+)\\"\s*:',text))
        expected={'version','accepted','reason_code','quote_reads','guard_checks','time_current_before_s','time_current_after_s',
            'calculated_server_before_s','calculated_server_after_s','gmt_before_s','gmt_after_s','local_before_s','local_after_s',
            'tick_time_s','tick_time_msc','bid','ask','tick_flags','elapsed_us'}
        self.assertEqual(keys,expected)
        for line in text.splitlines():
            if 'PrintFormat(' in line:self.assertNotRegex(line,r'identity_login|identity_server|state\.login|state\.server')
    def test_exclusive_report_seals(self):
        api=runpy.run_path(str(ROOT/'scripts/clock-semantics-038.py'))
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)/'r.json';api['write'](p,dict(a=1));h=api['sha'](p)
            with self.assertRaises(FileExistsError):api['write'](p,dict(a=2))
            self.assertEqual(api['sha'](p),h);self.assertEqual(api['sealed'](p),dict(a=1))
    def test_compiler_isolated_hidden_and_no_deployment(self):
        text=(ROOT/'scripts/compile-clock-observer-038.ps1').read_text()
        self.assertIn('-WindowStyle Hidden',text);self.assertIn('WaitForExit(60000)',text)
        self.assertIn("'ForexDemoLab\\builds'",text);self.assertIn("'clock038-'",text)
        self.assertNotRegex(text,r'terminal64|MQL5\\Experts|MQL5\\Scripts|Start-Service|Set-Service')


if __name__=='__main__':unittest.main()
