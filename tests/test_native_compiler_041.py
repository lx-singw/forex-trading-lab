"""Narrow staging repair preserves exclusivity, reparse and native-launch guards."""
import hashlib
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from forex_demo_lab import native_compiler_040 as old
from forex_demo_lab import native_compiler_041 as new
ROOT=Path(__file__).resolve().parents[1]

class NativeCompiler041Tests(unittest.TestCase):
    def test_exact_hidden_metadata_only_derivation(self):
        for fixture in (False,True):
            files={old.ECHO:'C:/source & $ ;.py'} if fixture else {old.SOURCE:'C:/source.mq5',old.HEADER:'C:/guard.mqh'}
            changed={new.ECHO:v for k,v in files.items()} if fixture else files
            previous=old.staging_command("C:/Owner's path/builds",'a'*32,files,fixture)
            expected=previous.replace('compiler040-','compiler041-').replace(old.ECHO,new.ECHO).replace(
                'Get-Item -LiteralPath $cursor)', 'Get-Item -LiteralPath $cursor -Force)')
            actual=new.staging_command("C:/Owner's path/builds",'a'*32,changed,fixture)
            self.assertEqual(actual,expected);self.assertEqual(actual.count('Get-Item -LiteralPath $cursor -Force'),1)
    def test_force_never_applies_to_creation_or_copy(self):
        text=new.staging_command('C:/Owned','a'*32,{new.SOURCE:'C:/source',new.HEADER:'C:/header'})
        self.assertEqual(text.count('[IO.File]::Copy('),2)
        for line in text.splitlines():
            if '[IO.File]::Copy(' in line:self.assertIn('$false)',line);self.assertNotIn('-Force',line)
            if 'New-Item -ItemType Directory -Path $b' in line:self.assertNotIn('-Force',line)
        self.assertIn('ReparsePoint',text);self.assertIn("throw 'reparse_root_rejected'",text)
        self.assertIn('OrdinalIgnoreCase',text);self.assertIn("throw 'stage_root_rejected'",text)
    def test_file_allowlists_and_identifiers_remain_closed(self):
        for files,fixture in (({new.ECHO:'C:/x',new.SOURCE:'C:/y'},True),({new.SOURCE:'C:/x'},False),({old.ECHO:'C:/x'},True)):
            with self.subTest(files=files),self.assertRaises(ValueError):new.staging_command('C:/Owned','a'*32,files,fixture)
        with self.assertRaises(ValueError):new.staging_command('C:/Owned','A'*32,{new.ECHO:'C:/x'},True)
    def test_previous_or_wrong_root_stage_cannot_be_owned(self):
        for path in ('C:/Other/compiler041-'+'a'*32,'C:/Owned/compiler040-'+'a'*32,'C:/Owned/compiler041-fixture-'+'a'*32):
            with self.subTest(path=path),self.assertRaises(ValueError):new.owned_directory(path,'C:/Owned')
        self.assertEqual(new.owned_directory('C:/Owned/compiler041-'+'a'*32,'C:/Owned').name,'compiler041-'+'a'*32)
        self.assertEqual(new.native_command('C:/editor.exe','C:/a & $ ;.mq5','C:/a.log'),old.native_command('C:/editor.exe','C:/a & $ ;.mq5','C:/a.log'))
    def test_observer_byte_identity_and_disabled_default(self):
        source=ROOT/'mt5/Scripts/ForexDemoClockObserver038.mq5';header=ROOT/'mt5/Scripts/ClockGuard038.mqh'
        self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),'23d06b1a2187285b5dd69a273cb8dbc3ced231e288605994ba368eab44c02455')
        self.assertEqual(hashlib.sha256(header.read_bytes()).hexdigest(),'a0848e412afbeb8be722e3bc811d2d036114a943c5ec11ecca918fae870eca55')
        self.assertIn('input bool CollectClockEvidence = false;',source.read_text())
        self.assertIn('2026.10.06',source.read_text());self.assertNotIn('OrderSend',source.read_text())
    def test_started_receipt_and_owned_timeout_preserved(self):
        text=(ROOT/'scripts/native-compiler-041.py').read_text()
        self.assertIn('not STARTED.exists()',text);self.assertIn('write(STARTED,',text)
        self.assertLess(text.index('write(STARTED,'),text.index('before=metadata(shell)'))
        self.assertIn("build_dir/'compile.log'),editor,60)",text)
        self.assertIn('shell=False',text);self.assertIn('subprocess.CREATE_NO_WINDOW',text)
        for forbidden in ("'-File'","'-ExecutionPolicy'",'terminal64','MetaTrader5','order_send','shell=True','taskkill'):
            self.assertNotIn(forbidden,text)
