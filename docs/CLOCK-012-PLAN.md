# Sequence-aware clock diagnosis 012 — before fresh statistics

Public reference probe 011 failed: WSL transport error, then a separately
declared ordinary Windows request returned HTTP429. No archive bytes acquired.
Stop that provider. Preserve both attempts and all 007/009/010 failed gates.

Use original 2020–2023 HistData archives and actual-demo guarded broker reads.
This stage tests a hypothesis and software conversion, not annual data
eligibility, strategy returns, source blending or execution. The proposal is
post-hoc with respect to already recorded discontinuities; fresh anchor
statistics below have not been inspected. Do not present it as independent
strategy validation or change the frozen 009 selection criteria.

## Sequence hypothesis

In each March archive, apply +5h before the recorded late-Sunday jump, +4h
after it. In October apply +4h before the recorded backward transition, +5h
after it. Define each change by the exact adjacent raw timestamps from the
009 review, bound to the original monthly archive hash. Preserve every row,
price and same-ms event. Never sort or delete the repeated October hour.
Reject any other backward timestamp, a changed boundary, a missing boundary,
wrong month/sequence, nonfinite/crossed quotes or nonmonotonic candidate UTC.
Serialize these as candidate timestamps, not certified UTC or simulator data.
Test mapping and restoration across the boundary before running archives.

Review all eight March/October archives. Record row counts, mapped first/last
labels, every transition, payload hashes and mapped gaps. For each transition
compare the six candidate UTC hours Sunday21:00 through Monday02:00 inclusive
against the stored H1 reference, interpreting broker labels as +3h in that
spring window and +2h in that autumn window. Report missing hours and every
close difference, including alternatives one hour earlier/later. These are
diagnostics; no missing candle is filled or date replaced.

## Independently timed anchors

Employment releases at 08:30 US Eastern:

| Day | Official UTC | Proposed HistData event label | Proposed broker event label |
| --- | --- | --- | --- |
| 2020-01-10 | 13:30 | 08:30 | 15:30 |
| 2020-07-02 | 12:30 | 08:30 | 15:30 |
| 2021-01-08 | 13:30 | 08:30 | 15:30 |
| 2021-07-02 | 12:30 | 08:30 | 15:30 |
| 2022-01-07 | 13:30 | 08:30 | 15:30 |
| 2022-07-08 | 12:30 | 08:30 | 15:30 |
| 2023-01-06 | 13:30 | 08:30 | 15:30 |
| 2023-07-07 | 12:30 | 08:30 | 15:30 |
| 2021-11-05 | 12:30 | 07:30 | 14:30 |
| 2022-11-04 | 12:30 | 07:30 | 14:30 |
| 2023-11-03 | 12:30 | 07:30 | 14:30 |

Primary releases are at
`https://www.bls.gov/news.release/archives/empsit_MMDDYYYY.htm` for these dates.
UTC conversion uses the historical America/New_York rule (record the timezone
database). November anchors distinguish European from US clock dates; do not
assume the provider's published fixed-EST claim is correct.

Capture each broker day at raw12:00–18:00 into a separate new folder, with
actual demo guards and no settings changes. The event and both controls at
exactly +/-60min use half-open one-minute intervals. Each source's screen
requires both controls to have positive range/count, and the event >=3x both
control ranges and >=2x both counts. Missing controls, failures and ambiguity
are reported and retained. Do not lower thresholds, pick another date or
reuse the 007 result as validation. All eleven dates are required for an
all-anchor pass. Selected anchors never certify a full-year clock mapping.

Freeze code/tests/plan and source bindings before fresh statistics/captures.
No eligible normalization, performance run or order activation follows from
these diagnostics. July14 and other source holes still need reviewed coverage.
2025 remains excluded from optimization; Nov–Dec2026 stays untouched.
