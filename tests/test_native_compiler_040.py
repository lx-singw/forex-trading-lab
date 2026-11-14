import os
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from forex_demo_lab.native_compiler_040 import *

class NativeCompiler040Tests(unittest.TestCase):
    def test_explicit_quote_values_with_spaces(self):
        self.assertEqual(native_command('C:/Program Files/MetaEditor.exe','C:/Owned/source name.mq5','C:/Owned/log name.log'),
            '"C:\\Program Files\\MetaEditor.exe" /compile:"C:\\Owned\\source name.mq5" /log:"C:\\Owned\\log name.log"')
    def test_command_characters_remain_literals(self):
        text=native_command('C:/Python/python.exe','C:/Owned/a & $ ;.mq5','C:/Owned/b & $ ;.log','C:/Owned/echo.py')
        self.assertIn('/compile:"C:\\Owned\\a & $ ;.mq5"',text)
        self.assertIn('/log:"C:\\Owned\\b & $ ;.log"',text)
    def test_quote_and_control_injection_rejected(self):
        for c in ('"','\0','\r','\n'):
            with self.subTest(c=c),self.assertRaises(ValueError):native_command('C:/editor.exe','C:/a'+c+'.mq5','C:/a.log')
    def test_relative_and_unc_executables_rejected(self):
        for p in ('editor.exe','C:editor.exe','//host/share/editor.exe'):
            with self.subTest(p=p),self.assertRaises(ValueError):native_command(p,'C:/a.mq5','C:/a.log')
    def test_wrong_owned_root_rejected(self):
        with self.assertRaises(ValueError):owned_directory('C:/Other/compiler040-'+'a'*32,'C:/Owned')
    def test_invalid_or_wrong_stage_identifier_rejected(self):
        for name in ('compiler039-'+'a'*32,'compiler040-'+'A'*32,'compiler040-fixture-'+'a'*32,'compiler040-../x'):
            with self.subTest(name=name),self.assertRaises(ValueError):owned_directory('C:/Owned/'+name,'C:/Owned')
    def test_exclusive_staging_keeps_reparse_guards(self):
        text=staging_command("C:/Owned's builds",'a'*32,{SOURCE:'C:/a.mq5',HEADER:'C:/b.mqh'})
        self.assertIn('ReparsePoint',text);self.assertIn('OrdinalIgnoreCase',text);self.assertIn('$false)',text)
        self.assertIn("compiler040-"+'a'*32,text);self.assertIn("Owned''s builds",text)
        self.assertEqual(text.count('[IO.File]::Copy('),2);self.assertNotIn('CompileClock039.ps1',text)
    def test_fixture_stages_only_echo(self):
        text=staging_command('C:/Owned','b'*32,{ECHO:'C:/echo.py'},True)
        self.assertEqual(text.count('[IO.File]::Copy('),1);self.assertIn('compiler040-fixture-',text)
        self.assertIn(ECHO,text);self.assertNotIn('.ps1',text)
        with self.assertRaises(ValueError):staging_command('C:/Owned','b'*32,{ECHO:'C:/echo.py',SOURCE:'C:/a.mq5'},True)
    def test_process_environment_does_not_mutate_parent(self):
        parent={'PSModulePath':'original','PATH':'unchanged','TOKEN':'private'}
        updated=module_environment('/native/powershell.exe',parent)
        self.assertEqual(parent['PSModulePath'],'original');self.assertEqual(updated['PSModulePath'],'/native/Modules')
        self.assertEqual(updated['TOKEN'],parent['TOKEN']);self.assertEqual(updated['PATH'],'unchanged')
    def test_exit_alone_is_not_compile_success(self):
        for completed,text,size in ((False,'0 errors, 0 warnings',12),(True,'',12),(True,'0 errors, 0 warnings',0),
                                   (True,'1 errors, 0 warnings',12),(True,'0 errors, 1 warnings',12)):
            with self.subTest(text=text,size=size):self.assertFalse(compile_evidence(completed,text,size)['compiled'])
        self.assertTrue(compile_evidence(True,'0 errors, 0 warnings',12)['compiled'])
    def test_last_numeric_summary_controls_outcome(self):
        value=compile_evidence(True,'0 errors, 0 warnings\n2 errors, 3 warnings',99)
        self.assertEqual(value,dict(compiled=False,errors=2,warnings=3))
    def test_launcher_and_echo_have_no_terminal_capability(self):
        root=Path(__file__).resolve().parents[1];driver=(root/'scripts/native-compiler-040.py').read_text()
        for forbidden in ("'-File'","'-ExecutionPolicy'",'order_send','MetaTrader5','terminal64','Invoke-Expression','shell=True'):
            self.assertNotIn(forbidden,driver)
        self.assertIn('shell=False',driver);self.assertIn('subprocess.CREATE_NO_WINDOW',driver)
        self.assertIn('not STARTED.exists()',driver);self.assertIn('write(STARTED,',driver)
        self.assertLess(driver.index('write(STARTED,'),driver.index('before=metadata(shell)'))
        echo=(root/'scripts/argument-echo-040.py').read_text()
        self.assertNotIn('open(',echo);self.assertNotIn('subprocess',echo)
