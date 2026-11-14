# Diagnostic source-lineage normalization 015 — 2026-10-02

All 48 original 2020–2023 archives were processed into separate monthly
diagnostic bundles. **110,069,388 original rows became 110,056,709 retained
rows**, with exactly the 12,679 already-proven second October replay rows
collapsed. Canonical archives retain both copies. Every other quote, volume,
same-ms event and gap stays in original order, with its original source row
number. No prices or missing candles were fabricated, and no broker data was
inserted into HistData.

The source, 48 archive/metadata bindings, previous reviews, replay proof/ranges
and timezone bytes were frozen before this run. The output records naive
source labels and candidate milliseconds under the representative European
calendar hypothesis. It remains explicitly **unapproved for performance**:
kind `diagnostic_candidate_ticks_015`, `absolute_utc_verified=false` and
`performance_evaluation_ready=false`. The annual 014 reader rejects its format
and review; that rejection was actually exercised and preserved.

## Coverage findings

All 47 month seams, including three year seams, preserve chronological order.
Fourteen seams have more than an hour between quotes; all remain unclassified.
There are 878 intra-month gaps over one hour. Weekend-looking intervals have
not been automatically certified as closures.

Within candidate 2020–2023, 24,097 hourly slots have quotes and 10,967 have none.
The weekday quote-free watchlist contains 1,449 slots:

| Candidate year | Retained quotes | Weekday quote-free hourly slots |
| --- | ---: | ---: |
| 2020 | 32,667,747 | 195 |
| 2021 | 16,765,142 | 182 |
| 2022 | 36,944,955 | 138 |
| 2023 | 23,678,865 | 934 |

These are quote inventories, not an authoritative forex session calendar.
Holidays and Friday session breaks contribute to weekday counts, so the table
cannot be interpreted as 1,449 missing trading hours. The large 2023 watchlist
directs further investigation without proving every flagged slot is a defect.
The known candidate 2023-03-26 hour 23 and 2023-07-14 hour 20 remain quote-free;
July 14 hour 19 is present. Earlier failed clock/coverage reviews remain unchanged.

First candidate quote: 2020-01-01 22:00:00.065 UTC. Last: 2023-12-29
21:59:59.385 UTC. Candidate-year edge handling retains out-of-scope edges rather
than trimming them; this actual run has no quotes outside the declared bounds.
The full watchlist, observed-hour OHLC/count/spreads and every gap are available
in the review and monthly inventories.

## Verification and artifacts

**239 tests passed**, including 14 added checks for exact lineage and volume,
same-ms events, ordinary duplicates, March gaps, candidate year edges, altered
and incomplete replays, failed publication, tampered resume, missing/duplicate
months, seam reversal, quote-free watchlists and performance-reader rejection.
An independent checker rejects an incorrect hourly close even if its inventory
hash is updated. Existing risk/account/stop/restart tests remain passing.

Full independent CSV/calendar/payload/hourly checks passed for all four years
and all 48 monthly files, covering every one of the 110,056,709 retained rows.
All normalization, review and independent-check jobs have finished.

The independent checker uses last-Sunday European transition arithmetic instead
of the normalizer's IANA conversion. It checks every row's sequence, original
row correspondence, candidate milliseconds and finite bid/ask/volume, then
reconstructs hourly bid/ask OHLC/count/endpoints and gaps, and compares payload
hashes. This is independent software arithmetic on the same feed, not another
market-data source or UTC certification. Completed-month provenance/seals and
both old/new source preflights protect reuse; partial months are not overwritten.

Implementation: `src/forex_demo_lab/normalization.py`.
CLI: `scripts/normalize-history-015.py`.
Independent checker: `scripts/check-normalization-015.py`.
Tests: `tests/test_normalization.py`.
Commands and resume limits: `NORMALIZATION-015-WORKFLOW.md`.

Evidence:

- `reports/normalization-015-ledger.json`, source ZIP and seal: frozen inputs/code.
- `data/normalization-015/YYYYMM`: diagnostic CSV, inventory, provenance and seal.
- `reports/normalization-015-review.json`: 48 months, 47 seams and hourly watchlist.
- `reports/normalization-015-independent-YYYY.json`: separate full CSV checks.
- `reports/normalization-015-market-gate.json`: actual pre-performance rejection.
- `reports/normalization-015-preservation.json`: unchanged prior report bindings.
- `reports/normalization-015-checks.json`: consolidated final verification.
- `reports/normalization-015-final-source-02.json`: completed source/report snapshot.

Prior results remain unchanged: 30 comparison 008 reports, 100 recovery 010
bindings, 25 clock/correction 013 bindings and 48 runner 014 bindings. Original
reader/correction source files match their archived versions.

Next: obtain independent absolute-UTC corroboration and source-specific session
hours/holiday evidence, investigate the 2023 gaps, then issue a separate annual
review only if the unchanged eligibility requirements are met. Normalization
alone cannot provide that approval. Historical costs remain modeled and
unverified. No new market returns, downloads, broker calls, terminal changes,
orders or deployment occurred. 2025 stays excluded; Nov–Dec 2026 stays reserved.
