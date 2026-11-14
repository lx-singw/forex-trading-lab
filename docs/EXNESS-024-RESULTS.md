# Exness diagnostic acquisition and audit 024/024B — 2026-10-06

Both original EURUSD monthly ZIPs downloaded successfully, and a separately
declared format interpretation passed a complete original-row audit. Independent
accounting matched **2,537,026 rows** and all reported endpoints, hours, ties,
duplicates and gaps. This is usable diagnostic evidence; **annual performance
eligibility remains false**. No strategy returns or orders were produced.

## Acquisition and preserved format failure

The frozen [acquisition plan](DATA-SAMPLE-024-PLAN.md) permitted exactly one GET
for March and one for July 2023. Both returned HTTP 200/application ZIP, taking
about 9.6 and 9.7 seconds including body handling. Received sizes exactly match
both GET Content-Length and prior HEAD metadata: 9,762,677 and 8,182,992 bytes,
17,945,669 bytes combined (17.1 MiB). No redirects, retries, credentials, cookies,
custom identity or additional provider requests occurred. Original ZIPs and
receipts are preserved under `data/exness-024`.

Windows initially blocked the unsigned UNC script before execution. That local
zero-request failure is preserved. The same frozen script ran in a child
PowerShell process with ExecutionPolicy Bypass; no persistent policy changed.
The prior 023 snapshot's 201 source, 278 report, 20 synthetic input and eight
access bindings, plus all 507 archived members, passed before acquisition.

Final review initially expected a hash-only seal, while the prior snapshot uses
hash plus filename. That local zero-request failure is preserved. The new
finalizer validates either format, including the exact filename when present;
no previous seal or hash was changed, and no quote audit was rerun.

The original [024 protocol](EXNESS-AUDIT-024-PROTOCOL.md) assumed provider row tag
`Exness` and timestamp separator T. Actual records use `exness` and a space,
such as `2023-03-01 00:00:03.282Z`. All records therefore failed the frozen
provider check. That failure and its independent matching counts remain sealed
in `reports/exness-024-audit.json` and `reports/exness-024-checks.json`. Its zero
accepted-hour counts describe parser rejection, not market inactivity.

The separate [024B plan](EXNESS-AUDIT-024B-PLAN.md) was declared before parsing
again. Separate parser/checker versions permit those exact lowercase/space
forms and canonicalize only the reporting hour key. They preserve original
record strings and price precision. An exact derivation check proves the limited
format changes and separate output names; original code/results stay unchanged.
No price rounding, row sorting, deduplication or quote interpolation occurred.

## Complete-month evidence

Each ZIP contains one CSV member. Bounded CRC inspection passed for all member
bytes, totaling 155,811,918 uncompressed bytes. Exact five-column headers, EURUSD
symbols, provider tags, millisecond Z timestamps, named-month boundaries, finite
positive bid/ask prices and Ask >= Bid all pass under 024B. Event order passes.

| Stated UTC month | Original quotes | Hours with quotes | Empty hours | Gaps >1h | Tied transitions | Exact duplicate records |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| March 2023 | 1,385,093 | 550 | 194 | 4 | 2 | 0 |
| July 2023 | 1,151,933 | 507 | 237 | 4 | 0 | 0 |

March's first/last original stamps are `2023-03-01 00:00:03.282Z` and
`2023-03-31 20:58:55.541Z`. July's are `2023-07-02 21:06:53.536Z` and
`2023-07-31 23:59:58.438Z`. All 744 hourly bins per month remain visible,
including month-edge empty hours. Gaps and empty hours receive no historical
session, closure or outage classification. Tied rows retain original order.

The independent checker re-read originals with manual timestamp construction
and exact rational price validation, without using primary-parser functions.
It matched every saved row count, valid count, endpoint, hour count, long gap,
tie, duplicate, backward count, member and uncompressed size. Separate outputs
are `reports/exness-024b-audit.json` and `reports/exness-024b-checks.json`, with
SHA256 seals and prefrozen source/input ledgers.

## Verification and next step

**318 tests pass**, including 19 new tests for format/calendar/month boundaries,
invalid/nonfinite/crossed/full-precision prices, symbols, ties, duplicates,
backward ordering, gap thresholds, bounded error samples, unsafe/oversized
archives, corrupt CRC/truncated ZIPs and exact version derivation. These tests
establish software behavior, not profitability or executable market prices.

The final review and snapshot are `reports/exness-024-review.json` and
`reports/exness-024-final-source.json/.zip`, each with a SHA256 seal. Acquired
market originals have their own binding group, separate from synthetic inputs.
Earlier frozen code/data/reports remain bound; only the four working handoff
documents change to describe this stage.

The next [fixed comparison plan 025](EXNESS-COMPARISON-025-PLAN.md) is declared
but not executed: March 26 UTC23 activity, July 14 quotes after the conditional
19:25:16.885 endpoint, and July 14 UTC20 activity. Old-source preflights and
exact selected input/code bindings must pass before comparison. No favorable
window search or overall eligibility pass follows from these observations.

Z labels are not independent absolute-clock certification. Historical sessions,
holidays/outages, provider upstream independence, permission and execution costs
remain unverified. Account-specific indicative quotes do not prove prices our
broker could execute. No providers are blended. The original annual gate still
fails; costs and profitable edge remain unestablished. Execution remains
unavailable, with no accounts, provider messages, live toggle or orders. Stopped
FXCM/Dukascopy acquisition and 2025/reserved late-2026 exclusions stay intact.
