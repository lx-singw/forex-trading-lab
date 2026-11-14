# Exness archive metadata 023 — 2026-10-06

Both observed diagnostic archive links returned HTTP 200 to one HEAD each.
No quote body was read. This establishes successful metadata access, not valid
ZIP contents or eligible market data.

| EURUSD month | HTTP | Content type | Advertised bytes | Approximate MiB |
| --- | --- | --- | ---: | ---: |
| March 2023 | 200 | application/zip | 9,762,677 | 9.31 |
| July 2023 | 200 | application/zip | 8,182,992 | 7.80 |

Total advertised size is 17,945,669 bytes. Both Last-Modified headers reported
5 June 2024, 16:24:58 UTC. This modification date is not a quote timestamp or
proof that the underlying data is unchanged since 2023.

The [frozen plan](SOURCE-METADATA-023-PLAN.md) preceded all archive requests.
Observed URLs were matched to the preserved 022 DOM notes. Windows .NET
HttpClient made the two requests sequentially at 04:31:00–04:31:02 UTC on
6 October 2026, with a 30-second timeout per request, redirects/cookies disabled,
no credentials or custom identity and response headers only. No redirect,
access/rate-limit error, GET fallback or network retry occurred. The stop rule
was not triggered. FXCM/Dukascopy archives were not accessed.

The initial local command failed before outcome reservation or HTTP dispatch:
PowerShell's provider-qualified location was unsuitable for .NET filesystem
methods. A native workspace UNC path fixed it without changing request scope.
This zero-network failure is preserved in
`reports/source-metadata-023-local-preflight-failure.json`. It is not a failed
provider response or an archive retry. Exclusive outcome files existed before
HTTP dispatch and prohibit repeating this stage into the same paths.

Original outcomes are `data/source-metadata-023/exness-2023-03-head.json` and
`exness-2023-07-head.json`. Only the declared public metadata fields are saved;
no cookie/auth headers or identifiers. Review/seals and completed source snapshot
are `reports/source-metadata-023-*`. Verification checks plan hash, observed
URLs, request sequence/bounds, metadata arithmetic, no-body flags and previous
022 source/report/input/archive bindings. Existing 020 migration verify passes.
No application code or software test suite changed; latest recorded suite stays
299 passing tests. Integrity checks do not approve the market data.

The provider's public download links remain attributable to its page from 022;
this probe does not certify upstream independence. Old UTC labels, complete
coverage, historical sessions/outages, permitted redistribution and executable
spreads/fees/carry remain unverified. Existing annual gates remain rejected.
No market returns, account creation, payments, contact or orders.

Next: [bounded diagnostic acquisition plan 024](DATA-SAMPLE-024-PLAN.md), declared
after these HEAD results and before any GET. Download only these two observed
monthly ZIPs with fixed size/time/request limits, preserve originals and audit
complete months before targeted clock/coverage comparisons. A successful
download cannot by itself approve annual data or establish profitability.
