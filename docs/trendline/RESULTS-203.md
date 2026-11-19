# Sprint 203 · Independent Exness archive diagnostic

19 November 2026. The user directed the lab to research the archive using
public evidence without contacting Exness. The provider explicitly offers
anonymous downloads and describes using the files with local scripts for
backtesting. That supports a private, temporary source diagnostic. The general
website copying provision and longer-term retention of raw data and derived
bars remain relevant to the eventual study. [Archive guide](https://www.exness.com/blog/product/exness-tick-history-bid-ask-prices/) · [Public backtesting guidance](https://www.exness.com/order-execution/) · [Earlier terms review](RESULTS-199.md)

## Scope declared before the sample request

Inspect one exact public [January 2022 EURUSD ZIP](https://ticks.ex2archive.com/ticks/EURUSD/2022/01/Exness_EURUSD_2022_01.zip)
for schema, bid/ask validity and timing. January 2022 has a contemporaneous
provider schedule and belongs to the 2021–2022 development candidate. Its
market dates had prior diagnostic exposure in the lab through HistData. The
2018–2019 validation candidate and other protected periods are outside this
diagnostic. [Exact header receipt](RESULTS-196.md) · [Prior exposure](RESULTS-202.md)

Use one ordinary HTTPS GET, with no redirects, retries, credentials or alternate
identity. Require HTTP 200, ZIP media type and the documented 5,412,286-byte
length. Bound the response to 8 MiB and use the prior audit’s 256 MiB total
uncompressed cap. Keep the ZIP in memory and retain hashes and sanitized
diagnostic aggregates. Reuse the frozen 024B parser and independent checker for
complete row and CRC checks. Compare the file’s labels as written with the
published Sunday 22:05 open and Friday 21:59 close minute in GMT+0. Compare
the last Friday and first Sunday observations for January 7/9, 14/16, 21/23
and 28/30. An observation in the stated minute supports consistency for that
boundary. Any other observed time remains a discrepancy to investigate.
Count first timestamps in observed UTC-labeled H1 bins with zero, positive
subsecond and at least one second of lag. These bins diagnose source labels
and do not assign a strategy opening price or an exchange session. [January schedule](https://web.archive.org/web/20220118223244/https://www.exness.com/forex/) · [Audit contract](../EXNESS-AUDIT-024B-PLAN.md)

The work is source qualification in Phase 10. Market signal counts and returns
require admitted inputs and the separate study scope in the frozen protocol.

## Sample results

The public URL returned the expected ZIP length. Both parsers checked every
row and agreed on record counts, source endpoints, hourly counts, order, ties,
and gaps. CRC checks passed. The archive contained one CSV member. All
**748,560** rows matched the exact EURUSD schema used in the 2023 audit,
including paired bid/ask prices and millisecond `Z` timestamps. In the
labeled month, 506 of 744 hourly bins contained quotes. Four consecutive-quote
gaps exceeded one hour. Time labels do not distinguish expected closures
from missing data on their own.

| Weekend | Last Friday label | First Sunday label | Matches published Friday and Sunday minutes |
| --- | --- | --- | --- |
| 7–9 January | 21:58:54.802 | 22:05:41.705 | Friday no, Sunday yes |
| 14–16 January | 21:58:59.302 | 22:05:17.540 | Friday no, Sunday yes |
| 21–23 January | 21:58:55.051 | 22:09:28.088 | Friday no, Sunday no |
| 28–30 January | 21:58:38.075 | 22:06:45.422 | Friday no, Sunday no |

All four Friday labels precede 21:59 by less than 22 seconds. That is
consistent with an exclusive 21:59 cutoff as well as a gap near closing.
The declared minute comparison remains as recorded. Two Sunday first
observations are later than the published opening minute. This is useful
clock corroboration for one month. Absolute UTC, the meaning of these
boundary differences, and date-specific sessions across the wider archive
still need evidence.

Of 506 observed hourly bins, **zero** began with a quote exactly on the hour,
**303** had their first quote within the following second, and **203** took
at least a second. This measures the archive’s source times. The Level B
opening availability assumption still needs to be explicit and independently
reviewed before entry-eligible signals can be counted. [Frozen opening rule](PROTOCOL.md)

## Status and verification

Separate source diagnostics from admission for strategy evaluation. Public
documentation and a scoped diagnostic supplied real format and timing evidence
without a provider message. The diagnostic leaves source-wide session and
coverage evidence, the applicable retention terms for a full study and
admission open. The exact January 2022 Exness source has now been inspected
for Phase 10 qualification. The older 2018–2019 proposal remains outside it.

All 43 targeted audit and preflight tests passed. The local receipt binds
the original header and pre-request scope and records the archive hash.
The ZIP existed in process memory. The ignored report contains the receipt,
dates and aggregates. Canonical Phase 10 still reports `UNAVAILABLE` with
null actual counts. [Prior source evidence](RESULTS-202.md)
