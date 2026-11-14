param([string]$MetaEditor = 'C:\Program Files\MetaTrader 5\metaeditor64.exe')
$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
if (-not (Test-Path -LiteralPath $MetaEditor -PathType Leaf)) {
    throw 'MetaEditor not found; pass -MetaEditor with its installation path.'
}
# Unique, non-terminal staging directory; never deploy or edit terminal settings.
$build = Join-Path $env:LOCALAPPDATA ('ForexDemoLab\builds\' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $build -Force | Out-Null
$source = Join-Path $build 'ForexDemoObserver.mq5'
$log = Join-Path $build 'compile.log'
Copy-Item -LiteralPath (Join-Path $repo 'mt5\Experts\ForexDemoObserver.mq5') -Destination $source
$process = Start-Process -FilePath $MetaEditor -ArgumentList @("/compile:`"$source`"", "/log:`"$log`"") -WindowStyle Hidden -PassThru
if (-not $process.WaitForExit(60000)) { throw 'Compiler timed out; inspect the isolated build directory.' }
if (-not (Test-Path -LiteralPath $log)) { throw 'Compiler did not create a log.' }
$text = Get-Content -LiteralPath $log -Raw
$reports = Join-Path $repo 'reports'
New-Item -ItemType Directory -Path $reports -Force | Out-Null
# Preserve compiler output locally, without staging account data or credentials.
$text | Set-Content -LiteralPath (Join-Path $reports 'observer-compile.log') -Encoding UTF8
if ($text -notmatch '0 errors, 0 warnings' -or -not (Test-Path -LiteralPath (Join-Path $build 'ForexDemoObserver.ex5'))) {
    throw 'Compilation failed or produced warnings; see reports/observer-compile.log.'
}
Write-Output 'Observer compiled: 0 errors, 0 warnings. No terminal deployment performed.'
