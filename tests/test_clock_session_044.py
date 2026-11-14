import copy
from datetime import datetime,timezone
from pathlib import Path
from types import SimpleNamespace
import unittest
from forex_demo_lab.clock_session_044 import *
ROOT=Path(__file__).resolve().parents[1]
def signatures():
    return dict(files=[dict(name=n,signature_status='Valid',signer_subject=SUBJECT,signer_thumbprint=THUMBPRINT,file_version='5.0.0.6241')
        for n in ('metaeditor64.exe','terminal64.exe')])
def event():
    g=int(datetime(2026,10,6,18,40,tzinfo=timezone.utc).timestamp());s=g+10800
    return dict(version=VERSION,accepted=True,reason_code=0,quote_reads=1,guard_checks=5,
        time_current_before_s=s,time_current_after_s=s,calculated_server_before_s=s,calculated_server_after_s=s,
        gmt_before_s=g,gmt_after_s=g,local_before_s=g+7200,local_after_s=g+7200,
        tick_time_s=s,tick_time_msc=s*1000,bid=1.1,ask=1.10001,tick_flags=1158,elapsed_us=100)

class ClockSession044Tests(unittest.TestCase):
    def test_only_two_exact_rollovers_permitted(self):
        self.assertEqual(len(ROLLOVER),2)
        for n,(old,new) in ROLLOVER.items():self.assertTrue(allowed_rollover(n,old,new))
    def test_arbitrary_or_missing_new_bytes_rejected(self):
        for n,(old,new) in ROLLOVER.items():
            self.assertFalse(allowed_rollover(n,old,'other'));self.assertFalse(allowed_rollover(n,'other',new))
            self.assertFalse(allowed_rollover(n,old,None));self.assertFalse(allowed_rollover(n,new,old))
    def test_other_dependencies_cannot_be_rebound(self):
        old,new=next(iter(ROLLOVER.values()))
        for n in ('/mnt/c/Windows/powershell.exe','scripts/clock-runtime-043.py','/mnt/c/Other/metaeditor64.exe'):
            self.assertFalse(allowed_rollover(n,old,new))
    def test_exact_publisher_version_and_signature(self):self.assertTrue(validate_signatures(signatures()))
    def test_untrusted_changed_or_incomplete_signature_set(self):
        for key,value in (('signature_status','NotSigned'),('signer_subject','other'),('signer_thumbprint','other'),('file_version','5.0.0.6242')):
            report=signatures();report['files'][0][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):validate_signatures(report)
        report=signatures();report['files'].pop()
        with self.assertRaises(ValueError):validate_signatures(report)
    def test_interactive_guard_precedes_all_runtime_side_effects(self):
        with self.assertRaises(ValueError):require_interactive(SimpleNamespace(isatty=lambda:False))
        text=(ROOT/'scripts/clock-runtime-044.py').read_text()
        self.assertLess(text.index('require_interactive(sys.stdin)'),text.index('write(RESERVATION,'))
        self.assertLess(text.index('require_interactive(sys.stdin)'),text.index('api.initialize('))
    def test_no_compiler_copy_sdk_quotes_orders_or_identity_output(self):
        text=(ROOT/'scripts/clock-runtime-044.py').read_text()
        for forbidden in ('[IO.File]::Copy','New-Item','hidden_process','symbol_info_tick','copy_ticks','copy_rates','order_send','json.dumps(identity)','account.login','account.server'):
            self.assertNotIn(forbidden,text)
        self.assertIn('runtime_guard(api,identity)',text);self.assertIn('api.shutdown()',text)
        self.assertIn('not RESERVATION.exists()',text)
    def test_complete_critical_source_freeze(self):
        text=(ROOT/'scripts/clock-session-044.py').read_text()
        for name in ('scripts/clock-runtime-044.py','scripts/check-clock-runtime-044.py','scripts/finalize-clock-session-044.py','tests/test_clock_session_044.py'):
            self.assertIn(name,text)
        self.assertIn('assert required<=set(bindings)',text)
    def test_unexpected_disabled_quote_is_preserved_and_blocks_enabled(self):
        s=RuntimeSequence044();s.arm(False);r=event()
        with self.assertRaises(ValueError):s.collect([r])
        self.assertEqual(s.records,[r]);self.assertEqual(sum(x['quote_reads'] for x in s.records),1)
        with self.assertRaises(ValueError):s.arm(True)
    def test_normal_disabled_enabled_sequence_and_no_repeated_arms(self):
        s=RuntimeSequence044();s.arm(False);s.collect([dict(version=VERSION,accepted=False,reason_code=17,quote_reads=0)])
        s.arm(True);s.collect([event()]);self.assertEqual(s.arms,[False,True])
        self.assertEqual(sum(x['quote_reads'] for x in s.records),1)
        with self.assertRaises(ValueError):s.arm(True)
