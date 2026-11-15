param([string]$MetaEditor = 'C:\Program Files\MetaTrader 5\metaeditor64.exe')
$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
if (-not (Test-Path -LiteralPath $MetaEditor -PathType Leaf)) { throw 'MetaEditor is unavailable.' }
$id = [guid]::NewGuid().ToString('N')
$build = Join-Path $env:LOCALAPPDATA ('ForexDemoLab\builds\native-port-156-' + $id)
$report = Join-Path $repo ('reports\native-port-156-compile-' + $id)
New-Item -ItemType Directory -Path $build,$report | Out-Null
$names = @('ForexDemoNativePort156.mq5','RecorderPort156.mqh','RunPermit156.mqh','PrivateGuard107.mqh','CostBounds128.mqh')
$hashes = [ordered]@{}
foreach ($name in $names) {
    $canonical = Join-Path $repo ('mt5\Scripts\' + $name)
    $hashes[$name] = (Get-FileHash -LiteralPath $canonical -Algorithm SHA256).Hash.ToLowerInvariant()
    Copy-Item -LiteralPath $canonical -Destination (Join-Path $build $name)
}
$source = Join-Path $build $names[0]
$log = Join-Path $build 'compile.log'
$process = Start-Process -FilePath $MetaEditor -ArgumentList @("/compile:`"$source`"", "/log:`"$log`"") -WindowStyle Hidden -PassThru
if (-not $process.WaitForExit(45000)) {
    # Only the compiler process created by this invocation; no terminal interaction.
    if (-not $process.HasExited) { $process.Kill() }
    throw 'Owned compiler timed out. Isolated staging retained; no retry or deployment.'
}
if (-not (Test-Path -LiteralPath $log -PathType Leaf)) { throw 'Compiler produced no log; isolated staging retained.' }
$raw = Get-Content -LiteralPath $log -Raw
$raw | Set-Content -LiteralPath (Join-Path $report 'compile.log') -Encoding UTF8
$result = [regex]::Match($raw, 'Result: [^\r\n]+').Value
$binary = Join-Path $build 'ForexDemoNativePort156.ex5'
$ok = $raw -match '0 errors, 0 warnings' -and (Test-Path -LiteralPath $binary -PathType Leaf)
foreach ($name in $names) {
    $canonical = Join-Path $repo ('mt5\Scripts\' + $name)
    if ((Get-FileHash -LiteralPath $canonical).Hash.ToLowerInvariant() -ne $hashes[$name] -or
        (Get-FileHash -LiteralPath (Join-Path $build $name)).Hash.ToLowerInvariant() -ne $hashes[$name]) {
        $ok = $false
    }
}
$manifest = [ordered]@{
    schema='native_port156_compile_v1'; compiler_version=(Get-Item -LiteralPath $MetaEditor).VersionInfo.FileVersion
    compiler_sha256=(Get-FileHash -LiteralPath $MetaEditor).Hash.ToLowerInvariant()
    sources=$hashes; result=$result; verified=$ok; deployed=$false; terminal_started=$false; run_granted=$false
    ex5_sha256=$(if (Test-Path -LiteralPath $binary) { (Get-FileHash -LiteralPath $binary).Hash.ToLowerInvariant() } else { $null })
}
$manifest | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $report 'manifest.json') -Encoding UTF8
Write-Output (Split-Path -Leaf $report)
Write-Output $result
if (-not $ok) { throw 'Compilation or source binding failed; inspect the retained report.' }
Write-Output 'Closed-entry prototype compiled. No terminal deployment, account query or collection.'
