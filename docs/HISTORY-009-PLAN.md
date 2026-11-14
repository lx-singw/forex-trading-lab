# History 009 — longer-history acquisition and chronological evaluation

Declared 2026-10-01 before acquiring or evaluating 2020–2023. This stage freezes
the data scope and selection rules; it does not authorize performance on raw,
unreviewed files or any broker orders. Keep comparison 008 immutable.

## Acquisition and eligibility

Acquire every EURUSD Generic ASCII tick month January 2020–December 2023 from
HistData's public download forms. Preserve original ZIP bytes and download
metadata, hash each, bound archive sizes, request sequentially and stop on
access errors. No retries after denial/rate limits, paid services or accounts.
Resume only by verifying existing complete archives; never overwrite them.
The current provider format is documented at
[HistData specifications](https://www.histdata.com/f-a-q/data-files-detailed-specification/).
It supplies bid/ask ticks and claims fixed EST without DST. Our 2024 evidence
contradicts using that claim universally, so do not extrapolate either fixed
EST or a New York mapping to these years without review.

Audit all raw rows for schema, finite positive noncrossed prices, volume,
source-month membership, ordering and archive identity. Preserve same-ms events
and exact duplicate observations; count them, do not silently delete them.
Record every gap over an hour, every month seam, hourly coverage and spread
diagnostics. Source labels remain explicitly naive, not UTC. Do not interpolate,
drop a losing/sparse month or substitute a different year to obtain a pass.

Structural success is insufficient for simulation eligibility. A separate,
versioned data review must establish a defensible clock mapping and investigate
missing sessions/gaps, including holidays and month boundaries; it must bind
all normalized dataset hashes. Require zero unresolved gaps over one hour in
expected open sessions, zero invalid/reordered rows, all declared months, and
independent price/clock corroboration. Define the corroboration windows and
numeric checks before reading those comparisons. Any failed year blocks its
dependent folds. Publish deficiencies without changing gates to fit them.
Freeze exact normalized UTC bounds and warmup coverage before performance.

## Fixed research budget and folds

Use C00–C04 from comparison 008, unchanged exits and base/adverse risk/cost
configs. No new parameters, learned weights, exit rules or candidate variants.
Maximum five candidates, two cost scenarios, two training windows and two
later test windows: 40 candidate/window/cost runs, including all controls.
The hypothetical cash candidate always remains available with zero interest.

| Fold | Selection history | Subsequent test |
| --- | --- | --- |
| A | 2020-01-01 to 2022-01-01 exclusive | Calendar 2022 |
| B | 2021-01-01 to 2023-01-01 exclusive | Calendar 2023 |

Use each calendar bound in reviewed UTC. Every simulation window has an
independent $10,000 start and no carried position. Supply the preceding 201
observed closed H1 bars for warmup when available (including prior-year bars
for 2021/2022/2023). The earliest 2020 window must warm up on its first 201
observed bars; exclude them from evaluation for all candidates and record its
shorter first quarter. Carry positions across quarters/years inside a training
window, but close at that window's final quote. No annualized concatenation of
restarted windows. Retain actual spread, modeled adverse fills, swap and gaps.

## Deterministic selection, including abstention

For each fold, a candidate must satisfy ALL of these on its selection history
under BOTH cost scenarios: positive net P&L in each of the two calendar years;
at least 60 closed trades total and 20 in each year; at least five of eight
quarters with positive equity change; net-trade profit factor >=1.10; maximum
tick equity drawdown <=10%. Assign closed trades by closing time. Measure yearly
and quarterly P&L by marked-to-market equity at the last observed quote before
each boundary; reconcile them with overall P&L. Require at least one loss to
compute profit factor; do not rank undefined ratios. These are chosen research
screens, not industry standards or statistical proof.

Among qualifying candidates rank by the smaller of their two adverse-cost
calendar-year percentage returns; highest wins, exact ties by ascending candidate
ID. If none qualifies, select cash for that entire subsequent year. Record the
chosen candidate and training-only input hashes BEFORE evaluating its test year.
Do not revise fold A after seeing 2022. Fold B may use 2022 only as declared
selection history; do not use 2023 anywhere in its choice. Publish all control
results and every rejection after choices are locked. No discretionary override.

Historical screening succeeds only if both selected annual test windows have
positive net return under both costs, at least 20 closed trades per year and
tick drawdown <=10%. Cash is a valid abstention but does not meet that positive
edge screen. Any failure means insufficient evidence; it does not justify more
stake, another unrecorded search or modifying the rule on the same test years.
Even success would require more uncertainty/robustness analysis and separate
execution safeguards; it never authorizes deployment or guarantees profit.

## Evidence limits and reserved data

These are retrospective tests of strategies chosen after seeing 2024 samples.
2020–2023 were not previously loaded here, but that does not recreate decisions
actually made in 2020 or make two test years proof of a stable future edge.
Record the full research history. Exclude blocked October 2024 and consumed
2025 from optimization; reserved November–December 2026 stays untouched.

Acquisition/audit 009 has no strategy-return command. The chronological runner,
training-only selection tests and final normalized-data/code manifest must be
implemented and frozen before performance, after data eligibility. Keep real
execution unavailable and demo order placement disabled.
