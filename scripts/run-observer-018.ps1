param([string]$Installation = 'C:\Program Files\MetaTrader 5')
$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
& wsl.exe -d Ubuntu --cd /home/lx_singw/projects/forex-demo-lab -- env PYTHONPATH=src python3 scripts/observer-018.py verify
if ($LASTEXITCODE -ne 0) { throw '018 freeze verification failed.' }
$runId = [guid]::NewGuid().ToString('N')
$root = Join-Path $env:LOCALAPPDATA ('ForexDemoLab\observer018\' + $runId)
$attempt = Join-Path $repo ('reports\observer-018-attempts\' + $runId)
New-Item -ItemType Directory -Path $root,$attempt | Out-Null
function Hash018([string]$path) { return (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant() }
function Json018([string]$path,$value) {
    if (Test-Path -LiteralPath $path) { throw 'Refusing to overwrite attempt evidence.' }
    $value | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $path -Encoding UTF8
}
$expertDir = Join-Path $root 'MQL5\Experts'
$presetDir = Join-Path $root 'MQL5\Profiles\Tester'
New-Item -ItemType Directory -Path $expertDir,$presetDir | Out-Null
Copy-Item -LiteralPath (Join-Path $repo 'mt5\Tests\ForexObserverParity018.mq5') -Destination $expertDir
foreach ($name in @('OriginalObserver018.mqh','Fixtures018.mqh')) {
    Copy-Item -LiteralPath (Join-Path $repo ('mt5\Tests\generated018\' + $name)) -Destination $expertDir
}
# Copy executables only. Never copy account configurations, bases or profiles.
$binaries = @{}
foreach ($name in @('terminal64.exe','metatester64.exe')) {
    $origin = Join-Path $Installation $name
    $destination = Join-Path $root $name
    Copy-Item -LiteralPath $origin -Destination $destination
    if ((Hash018 $origin) -ne (Hash018 $destination)) { throw 'Runtime binary copy differs.' }
    $binaries[$name] = @{ sha256=(Hash018 $destination); version=(Get-Item -LiteralPath $origin).VersionInfo.FileVersion }
}
$source = Join-Path $expertDir 'ForexObserverParity018.mq5'
$log = Join-Path $root 'compile.log'
$editor = Join-Path $Installation 'metaeditor64.exe'
$compiler = Start-Process -FilePath $editor -ArgumentList @("/compile:`"$source`"", "/log:`"$log`"") -WindowStyle Hidden -PassThru
$finished = $compiler.WaitForExit(60000)
$compiled = Join-Path $expertDir 'ForexObserverParity018.ex5'
$logText = if (Test-Path -LiteralPath $log) { Get-Content -LiteralPath $log -Raw } else { '' }
$passed = $finished -and ($logText -match '0 errors, 0 warnings') -and (Test-Path -LiteralPath $compiled)
$logText | Set-Content -LiteralPath (Join-Path $attempt 'compile.log') -Encoding UTF8
$compileEvidence = @{ passed=$passed; finished=$finished; source_sha256=(Hash018 $source); compiler_sha256=(Hash018 $editor) }
if ($passed) { $compileEvidence['ex5_sha256'] = Hash018 $compiled }
Json018 (Join-Path $attempt 'compile.json') $compileEvidence
if (-not $passed) { throw ('018 compilation failed; preserved attempt ' + $runId) }
$commonRelative = 'ForexDemoLab\observer018\' + $runId + '\results.csv'
$commonResult = Join-Path $env:APPDATA ('MetaQuotes\Terminal\Common\Files\' + $commonRelative)
if (Test-Path -LiteralPath $commonResult) { throw 'Result path already exists.' }
$preset = Join-Path $presetDir 'Runtime018.set'
('OutputFile=' + $commonRelative) | Set-Content -LiteralPath $preset -Encoding ASCII
$config = Join-Path $root 'math018.ini'
@'
[Common]
NewsEnable=0
[Experts]
Enabled=0
AllowLiveTrading=0
AllowDllImport=0
[Charts]
ProfileLast=Observer018Empty
[Tester]
Expert=ForexObserverParity018
ExpertParameters=Runtime018.set
Symbol=EURUSD
Period=H1
Model=3
Optimization=0
FromDate=2024.01.02
ToDate=2024.01.01
UseLocal=1
UseRemote=0
UseCloud=0
Visual=0
ShutdownTerminal=1
ReplaceReport=0
'@ | Set-Content -LiteralPath $config -Encoding ASCII
$evidence = @{ status='started'; run_id=$runId; portable_directory=$root; binaries=$binaries;
    ledger_sha256=(Hash018 (Join-Path $repo 'reports\observer-018-ledger.json'));
    config_sha256=(Hash018 $config); preset_sha256=(Hash018 $preset);
    copied_account_configuration=$false; market_data_used=$false; orders_available=$false }
Copy-Item -LiteralPath $config -Destination (Join-Path $attempt 'math018.ini')
Copy-Item -LiteralPath $preset -Destination (Join-Path $attempt 'Runtime018.set')
$terminal = Start-Process -FilePath (Join-Path $root 'terminal64.exe') -ArgumentList @('/portable', "/config:`"$config`"") -WorkingDirectory $root -WindowStyle Hidden -PassThru
# Bound this first-run attempt; stop only the uniquely owned terminal if stuck.
$exited = $terminal.WaitForExit(60000)
if (-not $exited) { Stop-Process -Id $terminal.Id -ErrorAction SilentlyContinue }
if (Test-Path -LiteralPath $commonResult) {
    Copy-Item -LiteralPath $commonResult -Destination (Join-Path $attempt 'results.csv')
    $evidence['result_sha256'] = Hash018 (Join-Path $attempt 'results.csv')
    $evidence['status'] = if ($exited) { 'completed' } else { 'output_present_terminal_timed_out' }
} else { $evidence['status'] = if ($exited) { 'exited_without_output' } else { 'runtime_timed_out_without_output' } }
$evidence['terminal_exited_within_limit'] = $exited
Json018 (Join-Path $attempt 'launch.json') $evidence
Write-Output ('018 attempt ' + $runId + ': ' + $evidence['status'])
if ($evidence['status'] -ne 'completed') { throw 'Runtime unverified; preserve attempt and investigate without broker registration.' }
