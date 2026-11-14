import json
from pathlib import Path
import re
import subprocess
from tempfile import TemporaryDirectory
import unittest
from forex_demo_lab.capture_budget_047 import *
from forex_demo_lab.capture_wire_047 import *

ROOT=Path(__file__).resolve().parents[1]
PHASE='47000000000000000000000000000001';DIGEST='47'*32
UTC=1791352800000;BOOT=100000
def policy():return Policy(PHASE,DIGEST)
def receipt():return dict(version=VERSION,phase=PHASE,policy_sha256=DIGEST,permission=1,
    issued_boot_ms=BOOT,expires_boot_ms=BOOT+2000,expires_utc_ms=UTC+2000)

class CaptureTransport047Tests(unittest.TestCase):
    def test_exact_new_date_derivation_preserves_046(self):
        old=(ROOT/'src/forex_demo_lab/capture_budget_046.py').read_text()
        self.assertEqual((ROOT/'src/forex_demo_lab/capture_budget_047.py').read_text(),
            old.replace("'2026-10-06'","'2026-10-07'").replace('capture_permission_046_v1','capture_permission_047_v1'))
    def test_exact_request_bytes_and_bindings(self):
        raw=encode_request(policy());self.assertEqual(len(raw),56)
        self.assertEqual(raw[:8],b'FXDL047Q');self.assertEqual(decode_request(raw,policy()),(PHASE,DIGEST))
    def test_request_short_long_extra_or_nonbytes_rejected(self):
        raw=encode_request(policy())
        for bad in (raw[:-1],raw+b'x',b'',bytearray(raw),True):
            with self.subTest(bad=type(bad)),self.assertRaises(PermitRejected):decode_request(bad,policy())
    def test_every_request_byte_mutation_rejected(self):
        raw=encode_request(policy())
        for i in range(56):
            bad=bytearray(raw);bad[i]^=1
            with self.subTest(index=i),self.assertRaises(PermitRejected):decode_request(bytes(bad),policy())
    def test_exact_reply_roundtrip(self):
        r=receipt();raw=encode_response(r);self.assertEqual(len(raw),84)
        self.assertEqual(decode_response(raw,policy(),UTC,BOOT),r)
    def test_reply_schema_duplicate_extra_boolean_or_overflow_rejected(self):
        for r in (dict(receipt(),extra=1),dict(receipt(),permission=True),dict(receipt(),version='other'),dict(receipt(),expires_boot_ms=2**64)):
            with self.subTest(r=r),self.assertRaises(PermitRejected):encode_response(r)
    def test_reply_partial_extra_bad_magic_rejected(self):
        raw=encode_response(receipt())
        for bad in (raw[:-1],raw+b'x',b'X'+raw[1:],bytearray(raw)):
            with self.assertRaises(PermitRejected):decode_response(bad,policy(),UTC,BOOT)
    def test_wrong_policy_phase_stale_or_restart_receipt(self):
        raw=encode_response(receipt())
        for p,u,b in ((Policy('a'*32,DIGEST),UTC,BOOT),(Policy(PHASE,'b'*64),UTC,BOOT),(policy(),UTC+2000,BOOT+2000),(policy(),UTC,BOOT-1)):
            with self.assertRaises(PermitRejected):decode_response(raw,p,u,b)
    def test_previous_date_does_not_authorize_047(self):
        with self.assertRaises(PermitRejected):clock_sample(lambda:(UTC-86400000,1,1))
    def test_fixture_disabled_before_ipc_and_no_market_api(self):
        s=(ROOT/'mt5/Scripts/ForexDemoPipeFixture047.mq5').read_text()
        self.assertLess(s.index('if(!ExerciseTransport)'),s.index('FileOpen('))
        self.assertIn('input bool ExerciseTransport=false;',s)
        self.assertNotRegex(s,r'\b(SymbolInfoTick|OrderSend|CopyTicks|CopyRates|SymbolSelect|OnTick|OnTimer|#import)\b')
        for line in s.splitlines():
            if 'PrintFormat(' in line:self.assertNotRegex(line,r'login|server|PHASE047|POLICY047')
    def test_native_guard_and_conservative_gmt_bound_present(self):
        s=(ROOT/'mt5/Scripts/ForexDemoPipeFixture047.mq5').read_text()
        self.assertEqual(len(re.findall(r'AccountReason042\(',s)),3)
        self.assertIn('SymbolReason042(',s);self.assertIn('TimeGMT()*1000+999',s)
        self.assertIn('FileReadArray(h,reply,0,85)',s)
    def test_shared_mql_codec_matches_python_for_100_frames(self):
        cases=[encode_response(receipt())]
        for i in range(84):
            changed=bytearray(cases[0]);changed[i]^=1;cases.append(bytes(changed))
        cases += [cases[0][:i] for i in range(0,13)] + [cases[0]+b'x',cases[0]+b'xx']
        self.assertEqual(len(cases),100)
        expected=[]
        for raw in cases:
            try:decode_response(raw,policy(),UTC,BOOT);expected.append(1)
            except PermitRejected:expected.append(0)
        with TemporaryDirectory() as directory:
            exe=Path(directory)/'wire'
            subprocess.run(['g++','-std=c++17','-Wall','-Wextra','-Werror',str(ROOT/'mt5/Tests/CaptureWire047.cpp'),
                '-o',str(exe)],check=True,capture_output=True,text=True,timeout=30)
            rows='\n'.join(f'{UTC} {BOOT} '+(r.hex() if r else '-') for r in cases)+'\n'
            result=subprocess.run([str(exe)],input=rows,capture_output=True,text=True,check=True,timeout=5)
            self.assertEqual([int(x) for x in result.stdout.splitlines()],expected)

if __name__=='__main__':unittest.main()
