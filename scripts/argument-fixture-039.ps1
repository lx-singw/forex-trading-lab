param([Parameter(Mandatory=$true)][string]$BuildDirectory,
      [Parameter(Mandatory=$true)][string]$PythonExe)
$ErrorActionPreference='Stop'
$result=@{outcome='fixture_failed';fixture_passed=$false;child_exit_code=$null;process_completed=$false}
try {
    $root=Join-Path ([Environment]::GetFolderPath('LocalApplicationData')) 'ForexDemoLab\builds'
    $build=[IO.Path]::GetFullPath($BuildDirectory)
    if(-not ([IO.Path]::GetDirectoryName($build)).Equals([IO.Path]::GetFullPath($root),[StringComparison]::OrdinalIgnoreCase)) { throw 'outside_owned_root' }
    if([IO.Path]::GetFileName($build) -notmatch '^compiler039-fixture-[0-9a-f]{32}$') { throw 'unowned_fixture' }
    $echo=Join-Path $build 'ArgumentEcho039.py'
    $output=Join-Path $build 'fixture-argv.json'
    if(Test-Path -LiteralPath $output) { throw 'existing_fixture_output' }
    $source=Join-Path $build 'source with spaces.mq5'
    $log=Join-Path $build 'log with spaces.log'
    $arguments=@(
        ('"'+$echo+'"')
        ('/compile:"'+$source+'"')
        ('/log:"'+$log+'"')
    )
    $startInfo=New-Object Diagnostics.ProcessStartInfo
    $startInfo.FileName=$PythonExe
    $startInfo.Arguments=[string]::Join(' ', $arguments)
    $startInfo.UseShellExecute=$false
    $startInfo.CreateNoWindow=$true
    $startInfo.RedirectStandardOutput=$true
    $child=New-Object Diagnostics.Process
    $child.StartInfo=$startInfo
    $null=$child.Start()
    $ownedHandle=$child.SafeHandle
    $done=$child.WaitForExit(10000)
    $result.process_completed=$done
    if(-not $done) { $child.Kill(); $null=$child.WaitForExit(5000) }
    if($done) {
        $result.child_exit_code=$child.ExitCode
        if($child.ExitCode -eq 0) {
            $text=$child.StandardOutput.ReadToEnd()
            $value=$text | ConvertFrom-Json
            if($value.arguments_equal -eq $true -and $value.argv[0] -ceq ('/compile:'+$source) -and $value.argv[1] -ceq ('/log:'+$log)) {
                $result.outcome='fixture_passed';$result.fixture_passed=$true
                $stream=[IO.FileStream]::new($output,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None)
                try { $bytes=[Text.Encoding]::UTF8.GetBytes($text); $stream.Write($bytes,0,$bytes.Length) } finally { $stream.Dispose() }
            }
        }
    }
} catch { }
ConvertTo-Json -Compress $result
