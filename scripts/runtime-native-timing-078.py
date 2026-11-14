"""Future one-use Windows metadata profile. Requires separate exact authorization.

Importing this file performs no Windows operation, SDK import or attachment.
The offline078 controller never executes run(). No user commands or UI needed.
"""
import ast
import ctypes as C
from datetime import datetime,timezone
import hashlib
import importlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from forex_demo_lab.native_timing_078 import (Spec078,Hooks078,authorization078,
    validate_authorization078,reserve_dispatch078,run_entry078)
from forex_demo_lab.sharing_adapter_076 import VerifiedBuild076,encoded076,exact076
from forex_demo_lab.sharing_integration_072 import SOURCE_INPUTS
from forex_demo_lab.image_guard_068 import NativeIdentity068,HelperChain068
from forex_demo_lab.native_files_065 import NativeFiles065,H,D
from forex_demo_lab.native_compiler_042 import module_environment
from forex_demo_lab.clock_observer_042 import unique_pairs
from forex_demo_lab.sharing_probe_062 import ProbeRejected
from forex_demo_lab.timing_profile_077 import DATE


def dependency_files078(root):
    """Static closure of local Python imports; excludes historic data/log files."""
    root=Path(root);todo=['native_timing_078','native_compiler_042'];seen=set()
    while todo:
        name=todo.pop()
        if name in seen: continue
        path=root/'src/forex_demo_lab'/f'{name}.py'
        if not path.is_file(): raise ProbeRejected('timing_source_rejected')
        seen.add(name)
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node,ast.ImportFrom):
                if node.level==1 and node.module: todo.append(node.module.split('.')[0])
                elif node.module and node.module.startswith('forex_demo_lab.'):
                    todo.append(node.module.split('.')[1])
    return tuple(sorted(['scripts/runtime-native-timing-078.py','src/forex_demo_lab/__init__.py',
        *(f'src/forex_demo_lab/{n}.py' for n in seen)]))


class PublicInputs078:
    """Bounded public report/source verification before native backend creation.

    At most16 JSON/sidecar reads/2MiB/128 stats, and64 source/launcher
    reads/16MiB/1024 stats;30s for the whole public boundary.
    This boundary never opens a terminal log or market-data archive.
    """
    def __init__(self,clock=lambda:(time.time_ns()//1000000,time.monotonic_ns())):
        self.clock=clock;self.first=clock();self.last=self.first
        self.reads=self.bytes=self.stats=0
        self.source_reads=self.source_bytes=self.source_stats=0
    def check(self):
        now=self.clock()
        if (type(now) is not tuple or len(now)!=2 or any(type(x) is not int or x<0 for x in now) or
            datetime.fromtimestamp(now[0]//1000,timezone.utc).date().isoformat()!=DATE or
            any(a<b for a,b in zip(now,self.last)) or now[1]-self.first[1]>=30000000000 or
            abs(now[0]-self.first[0]-(now[1]-self.first[1])//1000000)>1000):
            raise ProbeRejected('timing_public_clock_rejected')
        self.last=now
    def properties(self,path,source=False):
        self.check()
        key='source_stats' if source else 'stats';setattr(self,key,getattr(self,key)+1)
        if getattr(self,key)>(1024 if source else 128): raise ProbeRejected('timing_public_budget_rejected')
        s=Path(path).lstat()
        if stat.S_ISLNK(s.st_mode) or getattr(s,'st_file_attributes',0)&0x400:
            raise ProbeRejected('timing_public_file_rejected')
        return s
    def raw(self,path,cap=524288,source=False):
        self.check()
        reads='source_reads' if source else 'reads';total='source_bytes' if source else 'bytes'
        stats='source_stats' if source else 'stats'
        setattr(self,reads,getattr(self,reads)+1)
        if getattr(self,reads)>(64 if source else 16): raise ProbeRejected('timing_public_budget_rejected')
        path=Path(path)
        for p in path.parents: self.properties(p,source)
        before=self.properties(path,source)
        if not stat.S_ISREG(before.st_mode) or before.st_nlink!=1 or not 0<before.st_size<=cap:
            raise ProbeRejected('timing_public_file_rejected')
        setattr(self,total,getattr(self,total)+before.st_size)
        if getattr(self,total)>(16777216 if source else 2097152): raise ProbeRejected('timing_public_budget_rejected')
        key=lambda s:(s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_nlink)
        with path.open('rb') as stream:
            setattr(self,stats,getattr(self,stats)+2)
            if getattr(self,stats)>(1024 if source else 128) or key(os.fstat(stream.fileno()))!=key(before): raise ProbeRejected('timing_public_file_rejected')
            raw=stream.read(before.st_size)
            if key(os.fstat(stream.fileno()))!=key(before): raise ProbeRejected('timing_public_file_rejected')
        if key(self.properties(path,source))!=key(before) or len(raw)!=before.st_size:
            raise ProbeRejected('timing_public_file_rejected')
        self.check();return raw
    def record(self,path):
        raw=self.raw(path);side=self.raw(Path(path).with_suffix('.sha256'),65)
        if side!=hashlib.sha256(raw).hexdigest().encode('ascii')+b'\n': raise ProbeRejected('timing_public_digest_rejected')
        try: return json.loads(raw.decode('ascii'),object_pairs_hook=unique_pairs),hashlib.sha256(raw).hexdigest()
        except Exception: raise ProbeRejected('timing_public_schema_rejected') from None


def bound078(name):
    if name.startswith('/mnt/c/'): return Path('C:/')/name[7:]
    if name.startswith('/') or '..' in Path(name).parts: raise ProbeRejected('timing_path_rejected')
    return ROOT/name


def loaded_library078(files):
    module=files.bind(files.k,'GetModuleHandleW',[C.c_wchar_p],H)
    filename=files.bind(files.k,'GetModuleFileNameW',[H,C.c_wchar_p,D],D)
    handle,error=files._call(module,'python313.dll')
    if not handle or error: raise ProbeRejected('timing_library_rejected')
    buf=C.create_unicode_buffer(32768);n,error=files._call(filename,handle,buf,len(buf))
    if not 0<n<len(buf) or error: raise ProbeRejected('timing_library_rejected')
    return buf.value


SIGNATURE_COMMAND=r"""$ErrorActionPreference='Stop'
$terminal='C:\Program Files\MetaTrader 5\terminal64.exe'
$editor='C:\Program Files\MetaTrader 5\metaeditor64.exe'
$python='C:\Program Files\WindowsApps\PythonSoftwareFoundation.Python.3.13_3.13.3824.0_x64__qbz5n2kfra8p0'
$mt=@(@($terminal,$editor) | ForEach-Object { Get-AuthenticodeSignature -LiteralPath $_ })
$py=@(@('python.exe','python3.13.exe','python313.dll') | ForEach-Object { Get-AuthenticodeSignature -LiteralPath (Join-Path $python $_) })
$valid=@($mt | Where-Object { $_.Status.ToString() -ne 'Valid' -or $null -eq $_.SignerCertificate -or $_.SignerCertificate.Subject -notmatch 'MetaQuotes' }).Count -eq 0
$valid=$valid -and @($py | Where-Object { $_.Status.ToString() -ne 'Valid' -or $null -eq $_.SignerCertificate -or $_.SignerCertificate.Subject -notmatch 'Python Software Foundation' }).Count -eq 0
ConvertTo-Json -Compress @{valid=$valid;count=(@($mt).Count+@($py).Count);policy=(Get-ExecutionPolicy).ToString();terminal_build=(Get-Item -LiteralPath $terminal).VersionInfo.FilePrivatePart;editor_build=(Get-Item -LiteralPath $editor).VersionInfo.FilePrivatePart}
"""


def signature078(shell,meter,invoke=subprocess.run):
    meter.consume('trust_queries')
    kwargs=dict(env=module_environment(shell),capture_output=True,text=True,timeout=15)
    if os.name=='nt':
        startup=subprocess.STARTUPINFO();startup.dwFlags|=subprocess.STARTF_USESHOWWINDOW;startup.wShowWindow=0
        kwargs.update(startupinfo=startup,creationflags=subprocess.CREATE_NO_WINDOW)
    result=invoke([str(shell),'-NoProfile','-NonInteractive','-Command',SIGNATURE_COMMAND],**kwargs)
    meter.check()
    expected=dict(valid=True,count=5,policy='Restricted',terminal_build=6244,editor_build=6244)
    if result.returncode!=0 or len(result.stdout)>4096 or result.stderr or not exact076(json.loads(result.stdout),expected):
        raise ProbeRejected('timing_signature_rejected')
    return True


def write_result078(path,value):
    raw=(json.dumps(value,indent=2,sort_keys=True)+'\n').encode('ascii')
    with Path(path).open('xb') as stream: stream.write(raw);stream.flush();os.fsync(stream.fileno())
    with Path(path).with_suffix('.sha256').open('xb') as stream:
        stream.write(hashlib.sha256(raw).hexdigest().encode('ascii')+b'\n');stream.flush();os.fsync(stream.fileno())


def run():
    if os.name!='nt': raise ProbeRejected('timing_windows_required')
    public=PublicInputs078()
    ledger,lsha=public.record(ROOT/'reports/native-timing-078-ledger.json')
    checks,csha=public.record(ROOT/'reports/native-timing-078-checks.json')
    final,fsha=public.record(ROOT/'reports/native-timing-078-final-source.json')
    review,rsha=public.record(ROOT/'reports/native-timing-078-completion-review.json')
    profile,psha=public.record(ROOT/'reports/helper-profile-068.json')
    # Authorization is the only raw canonical record; its sidecar is mandatory.
    auth_raw=public.raw(ROOT/'reports/native-timing-078-authorization.json',8192)
    auth_sha=hashlib.sha256(auth_raw).hexdigest()
    if public.raw(ROOT/'reports/native-timing-078-authorization.sha256',65)!=auth_sha.encode('ascii')+b'\n':
        raise ProbeRejected('timing_authorization_rejected')
    if (not checks['checker_passed'] or checks['ledger_sha256']!=lsha or
        not review['review_passed'] or review['final_source_sha256']!=fsha or
        not review['frozen_input_coverage_complete'] or not profile['profile_verified'] or
        not profile['native_signature_checks_passed'] or psha!=ledger['helper_profile_sha256']):
        raise ProbeRejected('timing_preparation_rejected')
    policy_sha=ledger['policy_sha256'];bindings=ledger['runtime_bindings']
    if final['source_and_evidence_bindings'].get('docs/NATIVE-TIMING-078-POLICY.md')!=policy_sha:
        raise ProbeRejected('timing_policy_binding_rejected')
    def pair(name): return str(bound078(name)),bindings[name]
    p=ledger['helper_chain']
    chain=HelperChain068(pair(p['launcher']),pair(p['config']),tuple(pair(n) for n in p['images']),pair(p['library']),p['base_alias'])
    build=VerifiedBuild076(encoded076(ledger['build_record']))
    spec=Spec078(build,fsha,policy_sha,psha,chain,pair(ledger['terminal_name']),pair(ledger['editor_name']),
        pair(ledger['artifact_name']),tuple((n,str(ROOT/n)) for n in SOURCE_INPUTS),
        tuple(pair(n) for n in ledger['sdk_bindings']))
    expected=authorization078(fsha,policy_sha,psha,lsha,bindings['scripts/runtime-native-timing-078.py'],
        build.sha256,spec.component_sha256)
    auth=validate_authorization078(auth_raw,expected,auth_sha)
    # Validate every selected source dependency, never old logs/data/archives.
    sources=ledger['runtime_sources']
    if (type(sources) is not list or not 1<len(sources)<64 or len(set(sources))!=len(sources) or
        'scripts/runtime-native-timing-078.py' not in sources or
        any(type(n) is not str or '..' in Path(n).parts or not n.endswith('.py') or
            not (n=='scripts/runtime-native-timing-078.py' or n.startswith('src/forex_demo_lab/')) for n in sources)):
        raise ProbeRejected('timing_source_rejected')
    # The transitive closure was independently computed/frozen/tested offline.
    # Do not parse unverified or potentially oversized source here.
    expected_sources=set(sources)
    for n in sorted(expected_sources):
        if hashlib.sha256(public.raw(ROOT/n,262144,source=True)).hexdigest()!=bindings[n]:
            raise ProbeRejected('timing_source_rejected')
        if final['source_and_evidence_bindings'].get(n)!=bindings[n]: raise ProbeRejected('timing_source_rejected')
        public.check()
    if hashlib.sha256(public.raw(Path(sys.executable),1048576,source=True)).hexdigest()!=bindings[p['launcher']]:
        raise ProbeRejected('timing_launcher_rejected')
    dispatch=reserve_dispatch078(ROOT/'reports/native-timing-078-dispatch-started.json',auth,auth_sha)
    kernel=C.WinDLL('kernel32',use_last_error=True);boot=kernel.GetTickCount64
    boot.argtypes=[];boot.restype=C.c_uint64
    def importer():
        sdk=importlib.import_module('MetaTrader5')
        core=importlib.import_module('MetaTrader5._core')
        if (str(Path(sdk.__file__)).casefold()!=str(bound078(ledger['sdk_bindings'][0])).casefold() or
            str(Path(core.__file__)).casefold()!=str(bound078(ledger['sdk_bindings'][1])).casefold()):
            raise ProbeRejected('timing_sdk_import_rejected')
        return sdk
    hooks=Hooks078(lambda:(time.time_ns()//1000000,time.monotonic_ns(),int(boot())),
        lambda meter:NativeFiles065(meter,Path(os.environ['TEMP']),'compatibility'),NativeIdentity068,
        lambda meter:signature078(bound078(ledger['shell_name']),meter),importer,loaded_library078,
        os.getpid(),sys.executable,sys._base_executable,sys.version.split()[0])
    value=run_entry078(spec,hooks,auth_raw,expected,auth_sha,dispatch,
        ROOT/'reports/native-timing-078-sdk-reservation.json')
    value.update(native_entry_invoked=True,public_record_reads=public.reads,public_record_bytes=public.bytes,
        public_source_reads=public.source_reads,public_source_bytes=public.source_bytes,
        public_record_stats=public.stats,public_source_stats=public.source_stats,
        checks_sha256=csha,completion_review_sha256=rsha)
    write_result078(ROOT/'reports/native-timing-078-runtime.json',value)
    print(json.dumps(dict(entry_completed=value['entry_completed'],stop_reason=value['stop_reason'],
        stopped_stage=value['stopped_stage'],samples_completed=value['observation']['samples_completed']
            if value['observation'] else 0,orders_available=False)),flush=True)


if __name__=='__main__':
    try: run()
    except (Exception,KeyboardInterrupt): raise SystemExit('timing_preflight_rejected_details_redacted') from None
