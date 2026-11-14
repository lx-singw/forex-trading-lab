import json
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
import unittest
from forex_demo_lab.capture_budget_047 import Policy,VERSION
from forex_demo_lab.capture_wire_047 import encode_response,decode_response
ROOT=Path(__file__).resolve().parents[1]
PHASE='49000000000000000000000000000001';DIGEST='49'*32

class Fixture049Tests(unittest.TestCase):
    def test_native_exact_declared_derivation(self):
        old=(ROOT/'mt5/Scripts/ForexDemoPipeFixture047.mq5').read_text()
        for a,b in (('PHASE047','PHASE049'),('POLICY047','POLICY049'),('Stop047','Stop049'),('Account047','Account049'),
            ('FXDL_PIPE047','FXDL_PIPE049'),('pipe_fixture_047_v1','pipe_fixture_049_v1'),
            ('47000000000000000000000000000001',PHASE),('47'*32,DIGEST)):
            old=old.replace(a,b)
        self.assertEqual((ROOT/'mt5/Scripts/ForexDemoPipeFixture049.mq5').read_text(),old)
    def test_no_price_execution_or_dll_api_and_default_disabled(self):
        s=(ROOT/'mt5/Scripts/ForexDemoPipeFixture049.mq5').read_text()
        self.assertIn('input bool ExerciseTransport=false;',s)
        self.assertLess(s.index('if(!ExerciseTransport)'),s.index('FileOpen('))
        self.assertNotRegex(s,r'\b(SymbolInfoTick|OrderSend|CopyTicks|CopyRates|SymbolSelect|OnTick|OnTimer|#import)\b')
        self.assertEqual(s.count('AccountReason042('),3)
        self.assertIn('2026.10.07',s)
    def test_new_phase_cannot_accept_old_receipt(self):
        r=dict(version=VERSION,phase='47000000000000000000000000000001',policy_sha256='47'*32,permission=1,
            issued_boot_ms=100000,expires_boot_ms=102000,expires_utc_ms=1791352802000)
        with self.assertRaises(ValueError):decode_response(encode_response(r),Policy(PHASE,DIGEST),1791352800000,100000)
    def test_exact_shared_mql_decoder_new_phase(self):
        r=dict(version=VERSION,phase=PHASE,policy_sha256=DIGEST,permission=1,
            issued_boot_ms=100000,expires_boot_ms=102000,expires_utc_ms=1791352802000)
        good=encode_response(r);cases=[good,good[:-1],good+b'x']
        for i in range(84):
            bad=bytearray(good);bad[i]^=1;cases.append(bytes(bad))
        expected=[]
        for raw in cases:
            try:decode_response(raw,Policy(PHASE,DIGEST),1791352800000,100000);expected.append('1')
            except ValueError:expected.append('0')
        with TemporaryDirectory() as d:
            exe=Path(d)/'wire';subprocess.run(['g++','-std=c++17',str(ROOT/'mt5/Tests/CaptureWire049.cpp'),'-o',str(exe)],check=True,capture_output=True)
            out=subprocess.run([str(exe)],input=''.join('1791352800000 100000 '+raw.hex()+'\n' for raw in cases),
                text=True,capture_output=True,check=True)
        self.assertEqual(out.stdout.splitlines(),expected)
