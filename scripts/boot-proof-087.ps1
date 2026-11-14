$ErrorActionPreference = 'Stop'
try {
    # Local, read-only query. Never accept a supplied/cached boot timestamp.
    $rows = @(Get-WmiObject -Namespace 'root\cimv2' -Query 'SELECT LastBootUpTime FROM Win32_OperatingSystem' -ErrorAction Stop)
    if ($rows.Count -ne 1 -or $rows[0].LastBootUpTime -isnot [string] -or
        $rows[0].LastBootUpTime -cnotmatch '^[0-9]{14}\.[0-9]{6}[+-][0-9]{3}$') {
        exit 1
    }
    [Console]::Write($rows[0].LastBootUpTime)
    exit 0
} catch {
    # No machine names, paths, usernames or exception text in output.
    exit 1
}
