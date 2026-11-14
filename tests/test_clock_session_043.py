import copy
from pathlib import Path,PureWindowsPath
from types import SimpleNamespace
import unittest
from forex_demo_lab.clock_session_043 import require_interactive,reuse_path
from forex_demo_lab.clock_observer_042 import RuntimeSequence,VERSION
ROOT=Path(__file__).resolve().parents[1]
FOLDER='ForexDemoLab042-'+'a'*32
def deployment(root='C:/Terminal'):
    p=PureWindowsPath(root)/'MQL5'/'Scripts'/FOLDER/'ForexDemoClockObserver042.ex5'
    return dict(folder=FOLDER,artifact_binding={'/mnt/'+p.drive[0].lower()+p.as_posix()[2:]:'sha'})

class ClockSession043Tests(unittest.TestCase):
    def test_noninteractive_rejected_before_connection_or_reservation(self):
        for stream in (object(),SimpleNamespace(isatty=lambda:False)):
            with self.assertRaises(ValueError):require_interactive(stream)
        text=(ROOT/'scripts/clock-runtime-043.py').read_text()
        self.assertLess(text.index('require_interactive(sys.stdin)'),text.index('write(RESERVATION,'))
        self.assertLess(text.index('require_interactive(sys.stdin)'),text.index('api.initialize('))
    def test_interactive_stream_accepted(self):
        self.assertIsNone(require_interactive(SimpleNamespace(isatty=lambda:True)))
    def test_reuse_exact_owned_artifact(self):
        p=reuse_path('C:/Terminal',deployment(),'sha')
        self.assertEqual(p,PureWindowsPath('C:/Terminal')/'MQL5'/'Scripts'/FOLDER/'ForexDemoClockObserver042.ex5')
    def test_wrong_root_and_changed_hash_rejected(self):
        for root,h in (('C:/Other','sha'),('C:/Terminal','changed'),('relative','sha'),('//host/share','sha')):
            with self.subTest(root=root,h=h),self.assertRaises(ValueError):reuse_path(root,deployment(),h)
    def test_reuse_closed_ownership_and_schema(self):
        for key,value in (('folder','ForexDemoLab043-'+'a'*32),('folder','../other'),('extra','private')):
            d=deployment();d[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):reuse_path('C:/Terminal',d,'sha')
        d=deployment();d['artifact_binding']['/mnt/c/Other.exe']='sha'
        with self.assertRaises(ValueError):reuse_path('C:/Terminal',d,'sha')
    def test_no_compilation_copy_quote_or_order_code(self):
        text=(ROOT/'scripts/clock-runtime-043.py').read_text()
        for forbidden in ('[IO.File]::Copy','New-Item','hidden_process','symbol_info_tick','copy_rates','copy_ticks','order_send','positions_get'):
            self.assertNotIn(forbidden,text)
        self.assertIn('reuse_deployment(shell,data_root,artifact)',text)
        self.assertIn("sha(path)!=sha(artifact)",text);self.assertIn('is_junction',text)
        self.assertIn('runtime_guard(api,identity)',text);self.assertIn('api.shutdown()',text)
    def test_restart_and_native_arm_budget(self):
        text=(ROOT/'scripts/clock-runtime-043.py').read_text();self.assertIn('not RESERVATION.exists()',text)
        self.assertIn('maximum_script_arms=2,maximum_quote_reads=1',text)
        s=RuntimeSequence()
        with self.assertRaises(ValueError):s.arm(True)
        s.arm(False)
        with self.assertRaises(ValueError):s.arm(False)
        s.collect([dict(version=VERSION,accepted=False,reason_code=17,quote_reads=0)])
        s.arm(True)
        with self.assertRaises(ValueError):s.arm(True)
    def test_correct_source_freeze_and_no_identity_serialization(self):
        driver=(ROOT/'scripts/clock-session-043.py').read_text()
        for name in ('scripts/clock-runtime-043.py','scripts/check-clock-runtime-043.py','scripts/finalize-clock-session-043.py','tests/test_clock_session_043.py'):
            self.assertIn(name,driver)
        self.assertIn('assert required<=set(bindings)',driver)
        worker=(ROOT/'scripts/clock-runtime-043.py').read_text()
        for forbidden in ('account.login','account.server','str(identity)','json.dumps(identity)'):
            self.assertNotIn(forbidden,worker)
