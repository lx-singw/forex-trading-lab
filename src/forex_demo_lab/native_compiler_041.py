"""Native compiler arguments and isolated staging; no terminal capability."""
import os
from pathlib import Path, PureWindowsPath
import re
import subprocess
from forex_demo_lab.compiler_launch_039 import staging_command as previous_staging, parse_compile_log

SOURCE='ForexDemoClockObserver038.mq5'
HEADER='ClockGuard038.mqh'
ECHO='ArgumentEcho041.py'
VERSION='direct_native_compiler_041_v1'

def windows_path(value):
    value=str(value)
    p=PureWindowsPath(value)
    if not p.is_absolute() or len(p.drive)!=2 or p.drive[1]!=':':
        raise ValueError('absolute_windows_drive_required')
    if any(c in value for c in ('"','\0','\r','\n')):
        raise ValueError('invalid_native_path')
    return str(p)

def native_command(executable,source,log,echo=None):
    """Explicit executable and quoted option values, with shell=False at launch."""
    exe=windows_path(executable);source=windows_path(source);log=windows_path(log)
    prefix=[exe] if echo is None else [exe,windows_path(echo)]
    return subprocess.list2cmdline(prefix)+' /compile:"'+source+'" /log:"'+log+'"'

def module_environment(shell,environ=None):
    env=dict(os.environ if environ is None else environ)
    env['PSModulePath']=str(Path(shell).parent/'Modules')
    return env

def staging_command(root,token,files,fixture=False):
    allowed={ECHO} if fixture else {SOURCE,HEADER}
    if set(files)!=allowed:raise ValueError('undeclared_stage_files')
    # Reuse the immutable exclusive native-copy/reparse checks, substituting
    # only its declared filenames and this stage's directory prefix.
    if fixture:
        old={'ArgumentFixture039.ps1':files[ECHO],'ArgumentEcho039.py':files[ECHO]}
        text=previous_staging(root,token,old,True)
        first=text.index('[IO.File]::Copy(')
        last=text.index('\n$hashes=@{}',first)
        from forex_demo_lab.compiler_launch_039 import ps_quote
        text=text[:first]+'[IO.File]::Copy('+ps_quote(str(files[ECHO]))+', (Join-Path $b '+ps_quote(ECHO)+'), $false)'+text[last:]
    else:
        old={**files,'CompileClock039.ps1':files[SOURCE]}
        text=previous_staging(root,token,old,False)
        text='\n'.join(line for line in text.split('\n') if "(Join-Path $b 'CompileClock039.ps1')" not in line)
    return text.replace("'compiler039-","'compiler041-").replace('Get-Item -LiteralPath $cursor)', 'Get-Item -LiteralPath $cursor -Force)')

def fixture_expected(directory):
    p=PureWindowsPath(directory)
    return ['/compile:'+str(p/'source with spaces & $ ;.mq5'),'/log:'+str(p/'log with spaces & $ ;.log')]

def compile_evidence(completed,log_text,ex5_bytes):
    counts=parse_compile_log(log_text)
    return dict(errors=None if counts is None else counts['errors'],
                warnings=None if counts is None else counts['warnings'],
                compiled=bool(completed and counts==dict(errors=0,warnings=0) and ex5_bytes>0))

def owned_directory(value,root,fixture=False):
    p=PureWindowsPath(windows_path(value));r=PureWindowsPath(windows_path(root))
    pattern='compiler041-'+('fixture-' if fixture else '')+'[0-9a-f]{32}'
    if p.parent!=r or re.fullmatch(pattern,p.name) is None:raise ValueError('unowned_stage_directory')
    return p
