param([string]$MetaEditor = 'C:\Program Files\MetaTrader 5\metaeditor64.exe')
$ErrorActionPreference = 'Stop'
$taskRepo = Split-Path -Parent $PSScriptRoot
if (-not (Test-Path -LiteralPath $MetaEditor -PathType Leaf)) {
    ConvertTo-Json -Compress @{outcome='compiler_unavailable'; compiled=$false}
    exit 0
}
# Unique staging under an owned build root; no terminal directory or EA deployment.
$taskBuildRoot = Join-Path $env:LOCALAPPDATA 'ForexDemoLab\builds'
$taskBuild = Join-Path $taskBuildRoot ('clock038-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $taskBuild | Out-Null
$taskSource = Join-Path $taskBuild 'ForexDemoClockObserver038.mq5'
$taskHeader = Join-Path $taskBuild 'ClockGuard038.mqh'
$taskLog = Join-Path $taskBuild 'compile.log'
Copy-Item -LiteralPath (Join-Path $taskRepo 'mt5\Scripts\ForexDemoClockObserver038.mq5') -Destination $taskSource
Copy-Item -LiteralPath (Join-Path $taskRepo 'mt5\Scripts\ClockGuard038.mqh') -Destination $taskHeader
$taskArguments = @('/compile:"' + $taskSource + '"', '/log:"' + $taskLog + '"')
$taskProcess = Start-Process -FilePath $MetaEditor -ArgumentList $taskArguments -WindowStyle Hidden -PassThru
$taskExited = $taskProcess.WaitForExit(60000)
$taskEx5 = Join-Path $taskBuild 'ForexDemoClockObserver038.ex5'
$taskResult = @{outcome='compile_failed'; compiled=$false; errors=$null; warnings=$null; build_directory=$taskBuild;
    source=$taskSource; header=$taskHeader; log=$taskLog; executable=$taskEx5; process_completed=$taskExited}
if (-not $taskExited) {
    # Clean up only this newly launched owned compiler process.
    Stop-Process -Id $taskProcess.Id -ErrorAction SilentlyContinue
    $taskResult.outcome = 'compiler_timeout'
} elseif (Test-Path -LiteralPath $taskLog -PathType Leaf) {
    $taskText = Get-Content -LiteralPath $taskLog -Raw
    if ($taskText -match '(\d+) errors, (\d+) warnings') {
        $taskResult.errors = [int]$Matches[1]
        $taskResult.warnings = [int]$Matches[2]
        if ($taskResult.errors -eq 0 -and $taskResult.warnings -eq 0 -and (Test-Path -LiteralPath $taskEx5 -PathType Leaf)) {
            $taskResult.outcome = 'compiled'
            $taskResult.compiled = $true
        }
    }
}
ConvertTo-Json -Compress $taskResult
