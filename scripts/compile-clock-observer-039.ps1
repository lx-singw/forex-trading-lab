param([Parameter(Mandatory=$true)][string]$BuildDirectory,
      [Parameter(Mandatory=$true)][string]$MetaEditor)
$ErrorActionPreference='Stop'
$result=@{outcome='preflight_rejected';compiled=$false;native_compiler_attempts=0;native_compiler_started=$false;
          process_completed=$false;exit_code=$null;errors=$null;warnings=$null;owned_timeout_cleanup=$false}
try {
    $root=Join-Path ([Environment]::GetFolderPath('LocalApplicationData')) 'ForexDemoLab\builds'
    $build=[IO.Path]::GetFullPath($BuildDirectory)
    if(-not ([IO.Path]::GetDirectoryName($build)).Equals([IO.Path]::GetFullPath($root),[StringComparison]::OrdinalIgnoreCase)) { throw 'outside_owned_root' }
    if([IO.Path]::GetFileName($build) -notmatch '^compiler039-[0-9a-f]{32}$') { throw 'unowned_build' }
    if(-not ([IO.Path]::GetFullPath($MetaEditor)).Equals('C:\Program Files\MetaTrader 5\metaeditor64.exe',[StringComparison]::OrdinalIgnoreCase)) { throw 'compiler_path_rejected' }
    if(-not (Test-Path -LiteralPath $MetaEditor -PathType Leaf)) { throw 'compiler_unavailable' }
    if(@(Get-Process metaeditor64 -ErrorAction SilentlyContinue).Count -ne 0) { throw 'existing_editor_rejected' }
    $source=Join-Path $build 'ForexDemoClockObserver038.mq5'
    $header=Join-Path $build 'ClockGuard038.mqh'
    $log=Join-Path $build 'compile.log'
    $ex5=Join-Path $build 'ForexDemoClockObserver038.ex5'
    if(-not (Test-Path -LiteralPath $source -PathType Leaf) -or -not (Test-Path -LiteralPath $header -PathType Leaf)) { throw 'missing_frozen_source' }
    if((Test-Path -LiteralPath $log) -or (Test-Path -LiteralPath $ex5)) { throw 'existing_output_rejected' }
    $cursor=$build
    while($cursor) {
        if((Get-Item -LiteralPath $cursor).Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'reparse_path_rejected' }
        $cursor=Split-Path -Parent $cursor
    }
    $arguments=@(
        ('/compile:"'+$source+'"')
        ('/log:"'+$log+'"')
    )
    $result.native_compiler_attempts=1
    $result.outcome='compiler_launch_failed'
    $compiler=Start-Process -FilePath $MetaEditor -ArgumentList $arguments -WindowStyle Hidden -PassThru
    $result.native_compiler_started=$true
    $ownedHandle=$compiler.SafeHandle
    $done=$compiler.WaitForExit(60000)
    $result.process_completed=$done
    if(-not $done) {
        if(-not $compiler.HasExited) { $compiler.Kill(); $null=$compiler.WaitForExit(5000); $result.owned_timeout_cleanup=$true }
        $result.outcome='compiler_timeout'
    } else {
        $result.exit_code=$compiler.ExitCode
        $result.outcome='compile_failed'
        if(Test-Path -LiteralPath $log) {
            $text=Get-Content -LiteralPath $log -Raw
            if($text -match '(\d+) errors, (\d+) warnings') {
                $result.errors=[int]$Matches[1];$result.warnings=[int]$Matches[2]
                if($result.errors -eq 0 -and $result.warnings -eq 0 -and (Test-Path -LiteralPath $ex5 -PathType Leaf)) {
                    $result.compiled=$true;$result.outcome='compiled'
                }
            }
        }
    }
} catch { }
ConvertTo-Json -Compress $result
