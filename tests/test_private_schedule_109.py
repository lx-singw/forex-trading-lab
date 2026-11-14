import json
from pathlib import Path
import re
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]

class PrivateSchedule109Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory()
        cls.exe=Path(cls.temp.name)/'schedule'
        try:
            subprocess.run(['g++','-std=c++17','-Wall','-Wextra','-Werror',
                str(ROOT/'mt5/Tests/PrivateSchedule109.cpp'),'-o',str(cls.exe)],
                capture_output=True,check=True,timeout=30)
            cls.result=json.loads(subprocess.run([str(cls.exe)],capture_output=True,
                text=True,check=True,timeout=5).stdout)
        except BaseException:
            cls.temp.cleanup()
            raise
    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()
    def test_actual_shared_boundary_checks(self):
        self.assertTrue(self.result['passed'])
        self.assertEqual(self.result['boundary_checks'],15)
    def test_ideal_capture_preserves_spacing_and_budget(self):
        r=self.result['ideal']
        self.assertEqual((r['observed'],r['reason']),(120,0))
        self.assertGreaterEqual(r['min_gap_us'],500000)
        self.assertLessEqual(r['elapsed_us'],60000000)
    def test_coarse_wait_fails_under_invented_oversleep(self):
        r=self.result['coarse_wait']
        self.assertLess(r['observed'],120);self.assertEqual(r['reason'],13)
    def test_adaptive_wait_handles_same_invented_delay_without_catchup(self):
        r=self.result['adaptive_wait']
        self.assertEqual((r['observed'],r['reason']),(120,0))
        self.assertGreaterEqual(r['min_gap_us'],500000)
        self.assertLessEqual(r['elapsed_us'],60000000)
    def test_long_stall_still_stops(self):
        r=self.result['long_stall']
        self.assertLess(r['observed'],120);self.assertEqual(r['reason'],13)
        self.assertGreaterEqual(r['min_gap_us'],500000)
    def test_large_sleep_delay_cannot_bypass_budget(self):
        r=self.result['unbounded_sleep_delay']
        self.assertLess(r['observed'],120);self.assertEqual(r['reason'],13)
    def test_only_wait_and_public_script_labels_changed(self):
        old=(ROOT/'mt5/Scripts/ForexDemoPrivateRecorder107.mq5').read_text()
        new=(ROOT/'mt5/Scripts/ForexDemoPrivateRecorder109.mq5').read_text()
        def without_wait(s):
            start=s.index('      if(last_read_us!=0) {')
            end=s.index('      reason=ReadGuard107(true,login,server);',start)
            return s[:start]+s[end:]
        normalized=new.replace('#include "PrivateSchedule109.mqh"\n','')
        normalized=normalized.replace('FXDL109','FXDL107').replace('ForexDemoLab109','ForexDemoLab107').replace('Snapshot109-','Snapshot107-')
        normalized=normalized.replace('Private demo snapshot diagnostics with adaptive waiting. No order capability.',
            'Private demo snapshot diagnostics. No order capability.')
        self.assertEqual(without_wait(old),without_wait(normalized))
    def test_default_off_and_no_trading_network_or_sdk(self):
        s=(ROOT/'mt5/Scripts/ForexDemoPrivateRecorder109.mq5').read_text()
        self.assertIn('input bool RecordDiagnosticSnapshots = false;',s)
        self.assertNotRegex(s,r'\b(OrderSend|OrderSendAsync|CTrade|WebRequest|SymbolSelect|initialize|login|FILE_COMMON)\s*\(')
        self.assertNotIn('#import',s)
        self.assertIn('FXDL107_V1',s)
    def test_wait_checks_stop_clock_deadline_and_adaptive_pause(self):
        s=(ROOT/'mt5/Scripts/ForexDemoPrivateRecorder109.mq5').read_text()
        block=s[s.index('      if(last_read_us!=0) {'):s.index('      reason=ReadGuard107(true,login,server);',s.index('      if(last_read_us!=0) {'))]
        self.assertIn('IsStopped()',block);self.assertIn('Clock107(origin_s,origin_us)',block)
        self.assertIn('Schedule109(origin_us,last_read_us,GetMicrosecondCount()',block)
        self.assertIn('if(ready) break;',block)
        self.assertIn('if(pause_ms>0) Sleep(pause_ms);',block)
        self.assertNotIn('Sleep(20)',block)

if __name__=='__main__':unittest.main()
