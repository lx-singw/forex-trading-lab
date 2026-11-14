import json
from pathlib import Path
import re
import runpy
import tempfile
from types import SimpleNamespace as N
import unittest

from forex_demo_lab import compiler_launch_039 as c

ROOT=Path(__file__).resolve().parents[1]
TOKEN='abcdef0123456789abcdef0123456789'


def compile_result():
    return dict(outcome='compiled',compiled=True,native_compiler_attempts=1,native_compiler_started=True,
                process_completed=True,exit_code=1,errors=0,warnings=0,owned_timeout_cleanup=False)


class CompilerLaunchTests(unittest.TestCase):
    def test_identifier_rejects_paths_and_commands(self):
        for value in (None,True,'../escape','abc','A'*32,'x'*32,TOKEN+';',TOKEN+'/child'):
            with self.assertRaises(ValueError):c.identifier(value)
        self.assertEqual(c.identifier(TOKEN),TOKEN)
    def test_absolute_root_required(self):
        with self.assertRaises(ValueError):c.owned_path('relative',TOKEN)
    def test_owned_names(self):
        self.assertEqual(c.owned_path(Path('/tmp'),TOKEN).name,'compiler039-'+TOKEN)
        self.assertEqual(c.owned_path(Path('/tmp'),TOKEN,True).name,'compiler039-fixture-'+TOKEN)
    def test_reparse_root_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'actual').mkdir();(root/'link').symlink_to(root/'actual',target_is_directory=True)
            with self.assertRaises(ValueError):c.owned_path(root/'link'/'builds',TOKEN)
    def test_exclusive_exact_file_copies(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);src=root/'source';src.write_bytes(b'original')
            files={name:src for name in (c.SOURCE,c.HEADER,c.INVOKER)}
            stage=c.copy_exclusive(root/'builds',TOKEN,files)
            self.assertEqual({p.name for p in stage.iterdir()},set(files))
            self.assertTrue(all(p.read_bytes()==b'original' for p in stage.iterdir()))
            with self.assertRaises(FileExistsError):c.copy_exclusive(root/'builds',TOKEN,files)
            self.assertEqual((stage/c.SOURCE).read_bytes(),b'original')
    def test_undeclared_file_copies_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):c.copy_exclusive(Path(directory),TOKEN,{'terminal.ini':'somewhere'})
    def test_fixture_file_set(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);p=root/'source';p.write_bytes(b'x')
            stage=c.copy_exclusive(root/'builds',TOKEN,{c.FIXTURE:p,c.ECHO:p},True)
            self.assertEqual({v.name for v in stage.iterdir()},{c.FIXTURE,c.ECHO})
    def test_powershell_literals(self):
        self.assertEqual(c.ps_quote("C:\\O'Brien\\$(name)"),"'C:\\O''Brien\\$(name)'")
        for value in ('bad\ntext','bad\rtext','bad\0text',None):
            with self.assertRaises(ValueError):c.ps_quote(value)
    def test_explicit_native_argv(self):
        args=c.invoke_args('C:\\Windows\\ps.exe','C:\\Build Dir\\Compile.ps1',BuildDirectory='C:\\Build Dir',MetaEditor='C:\\Program Files\\editor.exe')
        self.assertEqual(args,['C:\\Windows\\ps.exe','-NoProfile','-NonInteractive','-File','C:\\Build Dir\\Compile.ps1',
                               '-BuildDirectory','C:\\Build Dir','-MetaEditor','C:\\Program Files\\editor.exe'])
        self.assertNotIn('-ExecutionPolicy',args)
    def test_native_argv_rejects_undeclared_parameters(self):
        with self.assertRaises(ValueError):c.invoke_args('ps','s.ps1',ExecutionPolicy='Bypass')
        with self.assertRaises(ValueError):c.invoke_args('ps','terminal.exe')
    def test_sanitized_errors_keep_no_private_text(self):
        result=c.sanitized_process(N(returncode=1,stderr='PRIVATE_ACCOUNT AuthorizationManager UnauthorizedAccess',stdout='PRIVATE_PASSWORD'))
        self.assertTrue(result['unauthorized_access']);self.assertTrue(result['authorization_manager_failure'])
        self.assertNotIn('PRIVATE',json.dumps(result));self.assertEqual(result['return_code'],1)
    def test_log_counts_last_result(self):
        self.assertEqual(c.parse_compile_log('one 1 errors, 2 warnings\nResult: 0 errors, 0 warnings'),dict(errors=0,warnings=0))
        self.assertIsNone(c.parse_compile_log('missing result'))
    def test_success_not_inferred_from_exit_code(self):
        value=compile_result();self.assertEqual(c.validated_result(json.dumps(value),'compile'),value)
        value.update(compiled=False,outcome='compile_failed',exit_code=0,errors=2)
        self.assertFalse(c.validated_result(json.dumps(value),'compile')['compiled'])
    def test_compile_schema_and_budget(self):
        for change in (dict(native_compiler_attempts=2),dict(errors=1),dict(process_completed=False),dict(native_compiler_started=False),
                       dict(private_identity='secret'),dict(compiled=1),dict(outcome='unknown')):
            value=compile_result();value.update(change)
            with self.assertRaises(ValueError):c.validated_result(json.dumps(value),'compile')
    def test_fixture_schema(self):
        value=dict(outcome='fixture_passed',fixture_passed=True,child_exit_code=0,process_completed=True)
        self.assertEqual(c.validated_result(json.dumps(value),'fixture'),value)
        value['server']='secret'
        with self.assertRaises(ValueError):c.validated_result(json.dumps(value),'fixture')
    def test_native_stage_constraints(self):
        text=c.staging_command('C:\\Build Root',TOKEN,{c.SOURCE:'source',c.HEADER:'header',c.INVOKER:'invoker'})
        self.assertIn("GetFolderPath('LocalApplicationData')",text);self.assertIn('OrdinalIgnoreCase',text)
        self.assertIn('ReparsePoint',text);self.assertIn('New-Item -ItemType Directory -Path $b | Out-Null',text)
        self.assertIn('[IO.File]::Copy',text);self.assertIn('$false)',text)
        self.assertNotIn('-ExecutionPolicy',text)
    def test_invoker_cannot_attach_or_change_policy(self):
        text=(ROOT/'scripts/compile-clock-observer-039.ps1').read_text()
        self.assertIn('-WindowStyle Hidden',text);self.assertIn('WaitForExit(60000)',text)
        self.assertIn('compiler039-[0-9a-f]{32}',text);self.assertIn('existing_editor_rejected',text)
        self.assertIn('$compiler.SafeHandle',text);self.assertIn('$compiler.Kill()',text)
        self.assertNotRegex(text,r'(?i)Set-ExecutionPolicy|Unblock-File|Start-Service|terminal64|OrderSend|SymbolInfoTick|Stop-Process')
    def test_fixture_avoids_python_appdata_writes(self):
        text=(ROOT/'scripts/argument-fixture-039.ps1').read_text()
        self.assertIn('CreateNoWindow=$true',text);self.assertIn('[IO.FileMode]::CreateNew',text)
        self.assertIn("[string]::Join(' ', $arguments)",text)
        echo=(ROOT/'scripts/argument-echo-039.py').read_text()
        self.assertNotRegex(echo,r'\.open\(|write_text\(|write_bytes\(')
        self.assertIn('print(json.dumps',echo)
    def test_observer_matches_preserved_hashes_and_has_no_new_capabilities(self):
        old=json.loads((ROOT/'reports/clock-semantics-038-compile.json').read_text())
        api=runpy.run_path(str(ROOT/'scripts/clock-semantics-038.py'))
        self.assertEqual(api['sha'](ROOT/'mt5/Scripts/ForexDemoClockObserver038.mq5'),old['source_sha256'])
        self.assertEqual(api['sha'](ROOT/'mt5/Scripts/ClockGuard038.mqh'),old['header_sha256'])
        text=(ROOT/'scripts/compiler-launch-039.py').read_text()
        self.assertNotRegex(text,r'import MetaTrader5|\.initialize\(|\.symbol_info_tick\(')
    def test_exclusive_report(self):
        api=runpy.run_path(str(ROOT/'scripts/compiler-launch-039.py'))
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)/'result.json';api['write'](p,dict(a=1));digest=api['sha'](p)
            with self.assertRaises(FileExistsError):api['write'](p,dict(a=2))
            self.assertEqual(api['sha'](p),digest)


if __name__=='__main__':unittest.main()
