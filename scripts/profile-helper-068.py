"""One source-bound current-date Windows SELF profile; never touches MT5/SDK."""
import ctypes as C
import json
import os
from pathlib import Path
import runpy
import sys
import time

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from forex_demo_lab.sharing_runtime_066 import Meter066,LIMITS066
from forex_demo_lab.image_guard_068 import NativeIdentity068,HelperChain068,Stage068
from forex_demo_lab.native_files_065 import NativeFiles065,H,D
from forex_demo_lab.sharing_probe_062 import ProbeRejected

SELF_LIMITS={**dict.fromkeys(LIMITS066,0), 'clock_samples':4096,'native_calls':200,
    'closes':4,'local_frees':4,'process_opens':2,'identity_tokens':2,'token_queries':16,
    'hash_reads':5,'hash_bytes':16777216,'hash_path_stats':160,'trust_queries':1}


class SelfMeter(Meter066):
    def check(self):
        now=super().check()
        if self.counts['clock_samples']>SELF_LIMITS['clock_samples']:raise ProbeRejected('profile_budget_rejected')
        return now
    def consume(self,key,amount=1):
        self.check()
        if key not in SELF_LIMITS or type(amount) is not int or amount<1 or self.counts[key]+amount>SELF_LIMITS[key]:
            raise ProbeRejected('profile_budget_rejected')
        self.counts[key]+=amount
    def cleanup(self,key):
        self.counts[key]+=1
        if self.counts[key]>SELF_LIMITS[key]:self.cleanup_exceeded=True


def run():
    if os.name!='nt':raise ProbeRejected('profile_windows_required')
    api=runpy.run_path(str(ROOT/'scripts/image-correction-068.py'))
    sha,sealed,write,bound=(api[k] for k in ('sha','sealed','write','bound'))
    l=api['verify']();checks=sealed(ROOT/'reports/image-correction-068-checks.json')
    assert checks['checker_passed'] and checks['tests_passed']==1158
    assert checks['ledger_sha256']==sha(api['LEDGER']) and sha(Path(sys.executable))==l['python_sha256']
    from datetime import datetime,timezone
    assert datetime.now(timezone.utc).date().isoformat()=='2026-10-07'
    write(ROOT/'reports/helper-profile-068-started.json',dict(profile_consumed=True,
        ledger_sha256=sha(api['LEDGER']),checks_sha256=sha(ROOT/'reports/image-correction-068-checks.json'),
        maximum_self_profiles=1,sdk_connections=0,mt5_invocations=0,orders_available=False))
    files=None;meter=None;stages=Stage068();verified=False;reason=None;cleanup=None
    signature_valid=False;helper_name=None;same_launcher=None;loaded_matches=False
    try:
        kernel=C.WinDLL('kernel32',use_last_error=True);boot=kernel.GetTickCount64;boot.argtypes=[];boot.restype=C.c_uint64
        meter=SelfMeter(lambda:(time.time_ns()//1000000,time.monotonic_ns(),int(boot())))
        files=NativeFiles065(meter,Path(os.environ['TEMP']),'compatibility') # Never setup/create any file.
        reader=NativeIdentity068(files)
        native=runpy.run_path(str(ROOT/'scripts/native-compiler-042.py'))
        settings=sealed(ROOT/'reports/native-compiler-042-ledger.json')
        stages.enter('signature');meter.consume('trust_queries')
        command=r"""$ErrorActionPreference='Stop'
$root='C:\Program Files\WindowsApps\PythonSoftwareFoundation.Python.3.13_3.13.3824.0_x64__qbz5n2kfra8p0'
$s=@('python.exe','python3.13.exe','python313.dll') | ForEach-Object { Get-AuthenticodeSignature -LiteralPath (Join-Path $root $_) }
$ok=@($s | Where-Object { $_.Status.ToString() -ne 'Valid' -or $null -eq $_.SignerCertificate -or $_.SignerCertificate.Subject -notmatch 'Python Software Foundation' }).Count -eq 0
ConvertTo-Json -Compress @{valid=$ok;count=@($s).Count;policy=(Get-ExecutionPolicy).ToString()}
"""
        result=native['command'](bound(settings['powershell_path']),command);meter.check()
        if result.returncode!=0 or json.loads(result.stdout)!=dict(valid=True,count=3,policy='Restricted'):
            raise ProbeRejected('profile_signature_rejected')
        signature_valid=True;stages.complete()
        helper=stages.run('helper_process',reader.identity,os.getpid())
        stages.enter('helper_chain')
        module=files.bind(files.k,'GetModuleHandleW',[C.c_wchar_p],H)
        filename=files.bind(files.k,'GetModuleFileNameW',[H,C.c_wchar_p,D],D)
        handle,error=files._call(module,'python313.dll')
        if not handle or error:raise ProbeRejected('profile_library_rejected')
        buf=C.create_unicode_buffer(32768);n,error=files._call(filename,handle,buf,len(buf))
        if not 0<n<len(buf) or error:raise ProbeRejected('profile_library_rejected')
        p=l['helper_chain']
        def pair(n):return str(bound(n)),l['bindings'][n]
        chain=HelperChain068(pair(p['launcher']),pair(p['config']),tuple(pair(n) for n in p['images']),
            pair(p['library']),p['base_alias'])
        chain.check(reader,helper,sys.executable,sys._base_executable,buf.value)
        if sys.version.split()[0]!='3.13.14':raise ProbeRejected('profile_version_rejected')
        if reader.identity(os.getpid())!=helper:raise ProbeRejected('profile_identity_changed')
        helper_name=Path(helper.image).name
        if helper_name not in ('python.exe','python3.13.exe'):raise ProbeRejected('profile_image_rejected')
        same_launcher=helper.image==str(Path(sys.executable)).casefold()
        loaded_matches=True;stages.complete();verified=True
    except Exception:
        reason='self_profile_failed_details_redacted';verified=False
    finally:
        if files is not None:
            try:
                cleanup=files.finish()
                if not cleanup['all_handles_closed'] or not cleanup['allocations_released'] or cleanup['unconfirmed_handles']:
                    verified=False;reason='profile_cleanup_unconfirmed'
            except Exception:verified=False;reason='profile_cleanup_failed_details_redacted'
        if meter is not None:
            try:meter.check()
            except Exception:verified=False;reason='profile_final_clock_rejected'
            if meter.cleanup_exceeded:verified=False;reason='profile_cleanup_budget_exceeded'
    write(ROOT/'reports/helper-profile-068.json',dict(profile_verified=verified,stop_reason=reason,
        ledger_sha256=sha(api['LEDGER']),source_checks_sha256=sha(ROOT/'reports/image-correction-068-checks.json'),
        native_signature_checks_passed=signature_valid,actual_helper_image_name=helper_name,
        helper_image_equals_sys_executable=same_launcher,loaded_python_library_matches_pin=loaded_matches,
        private_process_creation_logon_session_not_exported=True,stage_trace=stages.public(),
        stopped_stage=stages.current,counts=dict(meter.counts) if meter else None,cleanup=cleanup,
        sdk_connections=0,mt5_invocations=0,terminal_deployments=0,terminal_log_content_reads=0,
        market_reads=0,orders=0,receipt_permissions=0,orders_available=False,
        fresh_performance_eligible=False,annual_eligible=False))
    print(json.dumps(dict(profile_verified=verified,stop_reason=reason,stopped_stage=stages.current,
        helper_image_equals_sys_executable=same_launcher,orders_available=False)))


if __name__=='__main__':
    try:run()
    except Exception:raise SystemExit('profile_preflight_rejected_details_redacted') from None
