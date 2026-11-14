"""Owned staging and sanitized subprocess evidence; no terminal/SDK capability."""
import json
from pathlib import Path
import re
import shutil

VERSION='isolated_compiler_launch_039_v1'
SOURCE='ForexDemoClockObserver038.mq5'
HEADER='ClockGuard038.mqh'
INVOKER='CompileClock039.ps1'
FIXTURE='ArgumentFixture039.ps1'
ECHO='ArgumentEcho039.py'


def identifier(token):
    if not isinstance(token,str) or re.fullmatch('[0-9a-f]{32}',token) is None:
        raise ValueError('invalid_stage_identifier')
    return token


def owned_path(root,token,fixture=False):
    root=Path(root)
    if not root.is_absolute():raise ValueError('absolute_owned_root_required')
    for path in (root,*root.parents):
        if path.is_symlink() or getattr(path,'is_junction',lambda:False)():
            raise ValueError('reparse_stage_root_rejected')
    return root/('compiler039-'+('fixture-' if fixture else '')+identifier(token))


def copy_exclusive(root,token,files,fixture=False):
    """Synthetic/filesystem helper: existing stage/files are never overwritten."""
    build=owned_path(root,token,fixture)
    allowed={FIXTURE,ECHO} if fixture else {SOURCE,HEADER,INVOKER}
    if set(files)!=allowed:raise ValueError('undeclared_stage_files')
    build.mkdir(parents=True,exist_ok=False)
    for name,source in files.items():
        with Path(source).open('rb') as src, (build/name).open('xb') as dst:shutil.copyfileobj(src,dst)
    return build


def ps_quote(value):
    if not isinstance(value,str) or '\0' in value or '\n' in value or '\r' in value:
        raise ValueError('invalid_powershell_literal')
    return "'"+value.replace("'","''")+"'"


def staging_command(root,token,files,fixture=False):
    """Native PowerShell staging avoids packaged-Python AppData write redirection."""
    identifier(token)
    allowed={FIXTURE,ECHO} if fixture else {SOURCE,HEADER,INVOKER}
    if set(files)!=allowed:raise ValueError('undeclared_stage_files')
    name='compiler039-'+('fixture-' if fixture else '')+token
    copies='\n'.join('[IO.File]::Copy('+ps_quote(str(src))+', (Join-Path $b '+ps_quote(dst)+'), $false)' for dst,src in files.items())
    return '''$ErrorActionPreference='Stop'
$expected = [IO.Path]::GetFullPath('''+ps_quote(str(root))+''')
$actual = Join-Path ([Environment]::GetFolderPath('LocalApplicationData')) 'ForexDemoLab\\builds'
if(-not $expected.Equals([IO.Path]::GetFullPath($actual),[StringComparison]::OrdinalIgnoreCase)) { throw 'stage_root_rejected' }
$cursor=$actual
while($cursor) {
 if(Test-Path -LiteralPath $cursor) {
  if((Get-Item -LiteralPath $cursor).Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'reparse_root_rejected' }
 }
 $cursor=Split-Path -Parent $cursor
}
if(-not (Test-Path -LiteralPath $actual)) { New-Item -ItemType Directory -Path $actual -Force | Out-Null }
$b=Join-Path $actual '''+ps_quote(name)+'''
New-Item -ItemType Directory -Path $b | Out-Null
'''+copies+'''
$hashes=@{}
Get-ChildItem -LiteralPath $b -File | ForEach-Object { $hashes[$_.Name]=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLower() }
ConvertTo-Json -Compress @{outcome='staged';directory=$b;hashes=$hashes}
'''


def invoke_args(powershell,script,**parameters):
    if not str(script).lower().endswith('.ps1'):raise ValueError('powershell_script_required')
    args=[str(powershell),'-NoProfile','-NonInteractive','-File',str(script)]
    for key,value in parameters.items():
        if key not in ('BuildDirectory','MetaEditor','PythonExe'):raise ValueError('undeclared_script_parameter')
        args.extend(['-'+key,str(value)])
    return args


def sanitized_process(result):
    # Never expose the command, stdout/stderr text or exception text.
    text=result.stderr or ''
    return dict(return_code=result.returncode,unauthorized_access='UnauthorizedAccess' in text,
                security_exception='PSSecurityException' in text,access_denied='Access is denied' in text,
                authorization_manager_failure='AuthorizationManager' in text,missing_path='Cannot find path' in text)


def parse_compile_log(text):
    values=re.findall(r'(\d+) errors, (\d+) warnings',text)
    return dict(errors=int(values[-1][0]),warnings=int(values[-1][1])) if values else None


def validated_result(text,kind):
    value=json.loads(text)
    if not isinstance(value,dict):raise ValueError('invalid_native_result')
    if kind=='compile':
        keys={'outcome','compiled','native_compiler_attempts','native_compiler_started','process_completed',
              'exit_code','errors','warnings','owned_timeout_cleanup'}
        outcomes={'compiled','compile_failed','compiler_timeout','preflight_rejected','compiler_launch_failed'}
    elif kind=='fixture':
        keys={'outcome','fixture_passed','child_exit_code','process_completed'}
        outcomes={'fixture_passed','fixture_failed'}
    else:raise ValueError('invalid_result_kind')
    if set(value)!=keys or value['outcome'] not in outcomes:raise ValueError('native_result_schema_changed')
    if kind=='compile':
        if type(value['native_compiler_attempts']) is not int or not 0<=value['native_compiler_attempts']<=1:
            raise ValueError('compiler_budget_exceeded')
        for key in ('compiled','native_compiler_started','process_completed','owned_timeout_cleanup'):
            if type(value[key]) is not bool:raise ValueError('invalid_native_boolean')
        for key in ('exit_code','errors','warnings'):
            if value[key] is not None and type(value[key]) is not int:raise ValueError('invalid_native_integer')
        if value['compiled'] and (value['outcome']!='compiled' or value['errors']!=0 or value['warnings']!=0 or
                value['native_compiler_attempts']!=1 or not value['native_compiler_started'] or not value['process_completed']):
            raise ValueError('unsupported_compile_success')
    elif type(value['fixture_passed']) is not bool or type(value['process_completed']) is not bool or \
            value['child_exit_code'] is not None and type(value['child_exit_code']) is not int:
        raise ValueError('invalid_fixture_result')
    return value
