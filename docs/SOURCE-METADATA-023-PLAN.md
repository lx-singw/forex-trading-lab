# Exness archive HEAD feasibility 023 — 2026-10-06

Declared before archive requests. Inventory 022 observed both exact links on
the provider-operated public page. Check metadata only, in the sequence below:

1. https://ticks.ex2archive.com/ticks/EURUSD/2023/03/Exness_EURUSD_2023_03.zip
2. https://ticks.ex2archive.com/ticks/EURUSD/2023/07/Exness_EURUSD_2023_07.zip

At most one ordinary HTTPS HEAD per URL, sequentially, timeout 30 seconds each.
Use Windows .NET HttpClient with redirects and cookies disabled, no credentials
or custom identity/user-agent. Read headers only, never body bytes. No GET
fallback, range requests, retries, alternative hosts, proxy/identity changes,
authentication or provider contact. Stop all remaining Exness archive requests
on HTTP 403/429; mark later URLs unrequested. A transport failure, redirect or
other status is preserved without a retry and does not establish file absence.
No requests to previously stopped FXCM or Dukascopy archives.

Preserve URL, method, UTC start/end, HTTP status, content type/length,
last-modified and location (public URLs only) or error type in exclusive JSON
outcomes under data/source-metadata-023. Do not log cookies, auth headers,
credentials or account identifiers. Reserve each outcome file before its
request; an existing outcome prohibits a repeat. Review/seal the responses
and verify the plan hash and earlier 022 snapshot/report/input/archive bindings.
Only editable handoff documents may change. No application code changes or
software suite rerun are needed for this metadata-only stage.

HTTP 200 with ZIP metadata establishes only a successful HEAD response and
advertised size. It does not prove a ZIP can be downloaded or parsed, complete
monthly coverage, correct old UTC labels, historical sessions, independent
upstream prices, licensing or executable costs. Keep existing annual gates
failed, no strategy tuning, market returns or order activation.

If metadata permits, separately declare a bounded diagnostic acquisition of
these same months before any GET. Include fixed requests/byte caps, original
ZIP preservation, strict symbol/bid/ask/timestamp parsing, full-month chronology
and gap audit, then independent comparisons at existing March/July questions.
No four-year download, interpolation or provider blending. This stage creates
no account, uses no paid service and consumes no 2025/reserved 2026 quotes.
