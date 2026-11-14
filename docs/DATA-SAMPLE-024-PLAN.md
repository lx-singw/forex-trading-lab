# Exness diagnostic acquisition 024 — declared 2026-10-06

Prepared after the successful 023 HEAD probes, before any GET. This plan does
not report an acquisition: no quote payload has yet been requested. Use exact
EURUSD variant and the two provider-page links already observed in 022:

1. https://ticks.ex2archive.com/ticks/EURUSD/2023/03/Exness_EURUSD_2023_03.zip
2. https://ticks.ex2archive.com/ticks/EURUSD/2023/07/Exness_EURUSD_2023_07.zip

At most one ordinary HTTPS GET per URL, sequentially, no HEAD repeat, range
request, retry, redirect, cookies, credentials, identity change or alternative
host. Timeout the complete request/body stream at 60 seconds per file. Limit
each response body to 25 MiB and the combined acquisition to 50 MiB. March's
HEAD advertises 9,762,677 bytes, July 8,182,992. Check GET length when present
and record any difference from HEAD; do not assume byte identity from metadata.
Stop all further Exness archive requests on 403/429. Preserve other transport,
status, oversize, truncation or parsing failures without retries or fabrication.

Reserve exclusive receipts and original/partial files before requests under
data/exness-024. Existing files prohibit a repeated acquisition. Preserve bytes,
URL, retrieval UTC time, exact size and SHA256. Log only public metadata and
sanitized error types. Keep partial failures separate; never overwrite completed
originals. ZIP inspection must cap members at 64, uncompressed bytes at 256 MiB
per archive and 512 MiB total; reject paths, encryption or non-CSV members except
explicitly documented harmless directory entries. No extraction outside the
workspace. Check CRC and schema before any data-quality approval.

Audit all original CSV rows with provenance: exact symbol EURUSD, provider tag,
documented five-column header, ISO timestamp with explicit UTC designation and
milliseconds, finite positive bid/ask with ask >= bid, chronological event order,
original row ordering at tied timestamps and UTC month boundaries. Do not drop
duplicates, sort or repair input to hide failures. Preserve offending rows/counts
and stop dependent comparisons on schema failure; a format change needs a
separately declared supplemental interpretation before rerunning the parser.

Record quote counts, first/last stamps, tied/exact duplicates, observed/empty
UTC hours and long gaps for complete months. Absence is not automatically a
trading closure. Current general sessions are not a historical holiday/outage
calendar. ZIP availability and Z timestamps are not independent UTC certification.
These source ticks are indicative and account-specific, not proven executable
prices for the existing broker. Do not blend variants or providers.

If full-month parsing succeeds, compare only fixed existing data-quality
questions (March transition/empty-hour and July 14 truncation), with separately
bound old-source inputs and their preserved preflights. Declare exact windows,
metrics and acceptance rules before comparisons. Audit first; do not choose
favorable windows or thresholds from outcomes. No strategy/return calculation.

Any new parser/reader needs meaningful tests for boundaries, malformed prices,
bad timestamps/symbols, tied events, ordering/gaps and corrupt/oversized archives,
plus an independent original-row accounting check. Preserve prior frozen code,
plans, source/results and data hashes. New diagnostic review must remain
ineligible for annual performance until all original clock/session/gap/upstream
and cost requirements pass. No annual download by assumption, interpolation,
registration, paid services, contact, orders or live mode. Consumed 2025 and
reserved November–December 2026 quotes remain unused.
