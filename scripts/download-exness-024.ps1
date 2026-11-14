# One-shot diagnostic acquisition. Never rerun after a receipt has been reserved.
$ErrorActionPreference = 'Stop'
$root024 = '\\wsl.localhost\Ubuntu\home\lx_singw\projects\forex-demo-lab'
$out024 = Join-Path $root024 'data/exness-024'
$preflight024 = Get-Content -LiteralPath (Join-Path $root024 'reports/exness-024-acquisition-preflight.json') -Raw | ConvertFrom-Json
if ($preflight024.passed -ne $true) { throw 'PreflightNotPassed' }
foreach ($binding024 in $preflight024.bindings.PSObject.Properties) {
    if ((Get-FileHash -LiteralPath (Join-Path $root024 $binding024.Name) -Algorithm SHA256).Hash.ToLower() -ne $binding024.Value) { throw 'PreflightBindingChanged' }
}
$months024 = @('03', '07')
$lengths024 = @(9762677L, 8182992L)
$receipts024 = @()
[System.IO.Directory]::CreateDirectory($out024) | Out-Null
# Reserve every receipt and partial before the first request. Any existing file aborts.
foreach ($month024 in $months024) {
    foreach ($name024 in @("exness-2023-$month024-get.json", "Exness_EURUSD_2023_$month024.zip.partial")) {
        $handle024 = [System.IO.File]::Open((Join-Path $out024 $name024), [System.IO.FileMode]::CreateNew, [System.IO.FileAccess]::Write)
        $handle024.Dispose()
    }
    if (Test-Path -LiteralPath (Join-Path $out024 "Exness_EURUSD_2023_$month024.zip")) { throw 'OriginalAlreadyExists' }
    $receipts024 += [ordered]@{
        kind='bounded_public_archive_get_024'; month="2023-$month024";
        url="https://ticks.ex2archive.com/ticks/EURUSD/2023/$month024/Exness_EURUSD_2023_$month024.zip";
        method='GET'; plan_sha256=$preflight024.bindings.'docs/DATA-SAMPLE-024-PLAN.md';
        requested=$false; outcome='reserved_unrequested'; started_utc=$null; ended_utc=$null;
        status=$null; content_type=$null; content_length=$null; advertised_head_length=$lengths024[$receipts024.Count];
        length_differs_from_head=$null; timeout_seconds=60; per_file_cap=26214400; total_cap=52428800;
        redirects_allowed=$false; cookies_enabled=$false; credentials_used=$false; custom_identity=$false;
        retries=0; body_bytes_read=0L; stored_bytes=0L; sha256=$null; original_path=$null;
        error_type=$null; provider_stop=$false
    }
}
function Save-Receipt024($index024) {
    $receipts024[$index024] | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $out024 "exness-2023-$($months024[$index024])-get.json") -Encoding utf8
}
Save-Receipt024 0
Save-Receipt024 1
$handler024 = [System.Net.Http.HttpClientHandler]::new()
$handler024.AllowAutoRedirect=$false
$handler024.UseCookies=$false
$handler024.UseDefaultCredentials=$false
$client024=[System.Net.Http.HttpClient]::new($handler024)
$client024.Timeout=[System.Threading.Timeout]::InfiniteTimeSpan
$total024=0L
$stop024=$false
try {
    for ($index024=0; $index024 -lt 2; $index024++) {
        $receipt024=$receipts024[$index024]
        if ($stop024) { $receipt024.outcome='unrequested_provider_stop'; Save-Receipt024 $index024; continue }
        $partial024=Join-Path $out024 "Exness_EURUSD_2023_$($months024[$index024]).zip.partial"
        $final024=Join-Path $out024 "Exness_EURUSD_2023_$($months024[$index024]).zip"
        $cts024=[System.Threading.CancellationTokenSource]::new([TimeSpan]::FromSeconds(60))
        $request024=[System.Net.Http.HttpRequestMessage]::new([System.Net.Http.HttpMethod]::Get, $receipt024.url)
        $response024=$null; $stream024=$null; $file024=$null
        try {
            $receipt024.requested=$true
            $receipt024.started_utc=[DateTimeOffset]::UtcNow.ToString('o')
            $receipt024.outcome='request_started'
            Save-Receipt024 $index024
            $response024=$client024.SendAsync($request024,[System.Net.Http.HttpCompletionOption]::ResponseHeadersRead,$cts024.Token).GetAwaiter().GetResult()
            $receipt024.status=[int]$response024.StatusCode
            $receipt024.content_type=[string]$response024.Content.Headers.ContentType
            $receipt024.content_length=$response024.Content.Headers.ContentLength
            if ($null -ne $receipt024.content_length) { $receipt024.length_differs_from_head=($receipt024.content_length -ne $receipt024.advertised_head_length) }
            if ($receipt024.status -in @(403,429)) { $stop024=$true; $receipt024.provider_stop=$true }
            if ($receipt024.status -ne 200) { $receipt024.outcome='http_status_failure'; continue }
            if ($null -ne $receipt024.content_length -and ($receipt024.content_length -gt 26214400 -or $total024+$receipt024.content_length -gt 52428800)) { $receipt024.outcome='advertised_size_failure'; continue }
            $stream024=$response024.Content.ReadAsStreamAsync($cts024.Token).GetAwaiter().GetResult()
            $file024=[System.IO.File]::Open($partial024,[System.IO.FileMode]::Open,[System.IO.FileAccess]::Write)
            $buffer024=[byte[]]::new(65536)
            while ($true) {
                $remaining024=[Math]::Min(26214400L-$receipt024.body_bytes_read,52428800L-$total024)
                if ($remaining024 -eq 0) {
                    if ($receipt024.content_length -eq $receipt024.body_bytes_read) { break }
                    throw 'BodyCapReachedWithoutProvenEnd'
                }
                $count024=$stream024.ReadAsync($buffer024,0,[int][Math]::Min(65536L,$remaining024),$cts024.Token).GetAwaiter().GetResult()
                if ($count024 -eq 0) { break }
                $receipt024.body_bytes_read += $count024
                $total024 += $count024
                $file024.Write($buffer024,0,$count024)
                $receipt024.stored_bytes += $count024
            }
            if ($cts024.IsCancellationRequested) { throw 'CompleteStreamTimeout' }
            if ($null -ne $receipt024.content_length -and $receipt024.content_length -ne $receipt024.body_bytes_read) { throw 'ContentLengthMismatch' }
            $file024.Dispose(); $file024=$null
            [System.IO.File]::Move($partial024,$final024)
            $receipt024.original_path="data/exness-024/Exness_EURUSD_2023_$($months024[$index024]).zip"
            $receipt024.sha256=(Get-FileHash -LiteralPath $final024 -Algorithm SHA256).Hash.ToLower()
            $receipt024.outcome='complete_original_preserved'
        } catch {
            $receipt024.error_type=$_.Exception.GetType().FullName
            $receipt024.outcome='transport_or_body_failure'
        } finally {
            if ($null -ne $file024) { $file024.Dispose() }
            if ($null -ne $stream024) { $stream024.Dispose() }
            if ($null -ne $response024) { $response024.Dispose() }
            $request024.Dispose(); $cts024.Dispose()
            $receipt024.ended_utc=[DateTimeOffset]::UtcNow.ToString('o')
            if ($null -eq $receipt024.sha256) { $receipt024.sha256=(Get-FileHash -LiteralPath $partial024 -Algorithm SHA256).Hash.ToLower() }
            Save-Receipt024 $index024
            $receipt024 | ConvertTo-Json -Depth 8
        }
    }
} finally { $client024.Dispose(); $handler024.Dispose() }
