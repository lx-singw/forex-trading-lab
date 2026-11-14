# History 009 — longer data and chronological selection

Protocol: [HISTORY-009-PLAN.md](HISTORY-009-PLAN.md), frozen before acquisition
and any 2020–2023 strategy performance. The targets are all 48 monthly EURUSD
tick archives from January 2020 through December 2023. Original source files
remain separate from normalized, performance-eligible datasets.

Completed 2026-10-01: all 48 archives downloaded and 110,069,388 raw quote rows
reviewed. Compressed originals total 668,974,175 bytes (about 669 MB). The data
eligibility gate failed; no new strategy returns were calculated. Software and
artifact-integrity checks passed, which is distinct from data eligibility.

| Year | Archives | Rows examined | Strict ordering failure |
| --- | ---: | ---: | --- |
| 2020 | 12 | 32,671,547 | October |
| 2021 | 12 | 16,766,837 | October |
| 2022 | 12 | 36,949,580 | October |
| 2023 | 12 | 23,681,424 | October |

44 months passed row/schema/order checks; four failed source-label ordering.
Passing those structural checks does not establish complete coverage. The
complete inventory records 878 raw gaps longer than one hour and all 47 month
seams. Many gaps may be legitimate closures; they remain unclassified here.

## Findings

The strict audit found a backward source timestamp in October 2020: row
2,255,002 moves from 2020-10-25 19:59:56.508 to 19:00:00.147, a reversal of
3,596.361 seconds. These are source labels, not UTC. This is consistent with
a clock adjustment but does not establish the correct offset or transition
rule. A constant offset cannot remove the reversal. Sorting by the repeated
labels would change quote order; deleting repeated-hour observations would
discard prices. Neither operation was performed.

The same type of reversal occurs on 2021-10-31, 2022-10-30 and 2023-10-29.
Each October contains one detected backward transition. Preserve these as
evidence of a recurring source-clock issue, not a verified normalization rule.

March 2020 also has a gap from source-label March 29 18:59:58.557 to 20:00:00.104.
This remains an unresolved observation; it is not automatically classified as
a market closure or evidence of a particular timezone rule.

The original strict reader and failure are preserved. A separate diagnostic
continuation, `scripts/audit-history-009-defects.py`, records defects and checks
later months without pretending failed months passed. It never creates repaired
ticks, reorders rows or grants simulation eligibility. Tests cover continuing
after a backward timestamp while retaining subsequent observations, as well as
malformed prices, timestamps and rows. Every diagnostic is linked to source
and metadata hashes. Raw bytes are never changed.

HistData's [published specification](https://www.histdata.com/f-a-q/data-files-detailed-specification/)
describes fixed EST without daylight-saving adjustments. The observed reversal
means that documentation alone is insufficient to interpret this archive.
Its correct clock mapping requires independent corroboration. Do not extrapolate
the limited 2024 mappings or present these raw labels as UTC.

## Independent reference

The existing guarded collector acquired 24,893 MT5 H1 candles across 53 request
windows, covering raw labels 2020-01-02 06:00 through 2023-12-29 23:00. The
request was 2020-01-01 through 2024-01-01 exclusive. This reference is in
`data/history-009-mt5-reference`, with source hashes and requested windows.
Its acquisition was declared in `HISTORY-009-REFERENCE.md` before capture.

The collector rechecked actual demo-account type around history reads. Automated
trading was off; no orders, login changes, account identifiers or credentials
were captured. Today's quote label was approximately three hours ahead of UTC;
this does not prove historical offsets. Reference candles are not automatically
trusted as a replacement feed, nor do two agreeing feeds prove independent
upstream sources. Comparison windows and checks must be fixed before comparing.

Eight windows were subsequently frozen before comparison: 08:00–19:00 source
labels on the dates below, comparing all relative offsets 0–9 hours. Every
offset needed all twelve closes; the best needed median difference <=1 pip,
maximum <=3 pips and mean advantage >=2 pips over the next candidate. These
are declared research screens, not feed certification standards.

| Source day | Best complete relative offset | Maximum difference, pips | Screen |
| --- | ---: | ---: | --- |
| 2020-01-14 | +7 hours | 0.2 | Pass |
| 2020-07-14 | +7 hours | 0.2 | Pass |
| 2021-01-12 | +7 hours | 0.2 | Pass |
| 2021-07-13 | +7 hours | 0.7 | Pass |
| 2022-01-11 | +7 hours | 0.7 | Pass |
| 2022-07-12 | +7 hours | 1.8 | Pass |
| 2023-01-10 | +7 hours | 1.2 | Pass |
| 2023-07-11 | None: only six source hours present | — | Fail |

Offset means MT5 raw labels minus HistData raw labels, not an offset from UTC.
Seven passing windows cover 84 matching closes. They do not validate the
October transitions or demonstrate full-year clock correctness.

July 11, 2023 is missing source hours 08, 11, 12, 14, 16 and 18 inside the
twelve-hour window. The reference contains all twelve corresponding hours under
the +7 hypothesis. The six available matches differ by at most 0.9 pip, but
partial matches do not pass the frozen requirement. July has only 370 distinct
source hours and 123 raw gaps over one hour. An independent raw-byte hour-prefix
count confirms 1,535,263 rows and 370 hours, without using the timestamp parser.
Do not fill the absent hours with candles or substitute a different test day.

Additional coverage flags occur in February–June 2023: 48, 134, 106, 137 and
133 raw gaps between one and 36 hours respectively (July has 119). These counts
do not classify every gap, but show why a row-valid file is not automatically
usable for strategy testing. Clock corrections alone cannot establish whether
the missing observations are recoverable from another source.

## Selection implementation

`src/forex_demo_lab/selection.py` implements the frozen selection rule using
training aggregates only. Fold A uses 2020–2021 for a 2022 choice; fold B uses
2021–2022 for a 2023 choice. All five candidates at both cost settings must be
present. Missing runs or inconsistent aggregates are errors, not permission to
select a convenient available result.

Candidates need positive net results in both training years, at least 60 trades
total and 20 in each year, five positive quarters, profit factor at least 1.10
and tick drawdown no higher than 10%, under both costs. Eligible candidates are
ranked by their weaker adverse-cost annual return, with a deterministic tie
break. If none qualifies, the selection is cash. This is a research screen,
not a claim of statistical significance or future income.

The module reconciles quarterly/yearly/trade totals and annual starting equity,
rejects nonfinite values, duplicate/missing scenarios and future-period inputs,
and records a deterministic training-input hash. Its tests include a candidate
with greater total profit losing to one with a stronger weaker year. This pure
module does not validate market data or calculate training aggregates. The
chronological replay runner, dataset review and performance manifest remain
required before applying it to historical returns.

## Verification and remaining work

180 tests pass: 158 previous checks plus six raw-audit tests, eleven selection
tests, two diagnostic-continuation tests and three corroboration tests. No strategy rules, costs or risk
limits were tuned. No 009 strategy return was calculated. Source archives for
earlier experiments remain preserved; adding the selection module changes the
current package fingerprint, so old runs require their archived implementations.

Final local evidence: `reports/history-009-review.json`, `history-009-boundaries.json`,
`history-009-corroboration.json`, `history-009-july-coverage-check.json` and
`history-009-checks.json`. Per-month reports retain input hashes and exact
defects. The checks verify all 48 archive/metadata bindings, report hashes,
complete review inventory, seams and independent July coverage count. Earlier
004/005 archives and all 30 comparison-008 results remain unchanged. Acquisition,
review, corroboration and boundary-inventory processes have all finished.

Next: use the preserved reference and predeclared independent clock/price checks
to resolve source chronology and the February–July 2023 coverage deficiencies,
distinguish missing observations from clock transitions, review gaps and month
boundaries, and build separately versioned
normalized datasets only where supported. Never loosen a failed gate to obtain
performance. Then implement/freeze the chronological replay and apply the fixed
selection rule. 2025 remains excluded from optimization; future reserved
November–December 2026 is untouched. Order placement remains unavailable.
