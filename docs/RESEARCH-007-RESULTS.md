# Research 007 — interval evidence, 2026-10-01

The proposed October interval mapping passed all 18 hourly price comparisons
and the quote-free weekend checks. Three of four event screens passed. The
fourth missed its declared tick-count threshold, so **dataset construction was
rejected and no October strategy returns were computed**. This is insufficient
evidence under the protocol, not proof that the proposed mapping is wrong.

The [declaration](RESEARCH-007-PLAN.md) preceded the new statistics. It tested
HistData UTC-4 / broker UTC+3 before the October 26–27 weekend and HistData UTC-5
/ broker UTC+2 afterward. The original 005/006 failed hypotheses and artifacts
remain unchanged. This is a month-specific hypothesis, not a certified timezone.

## Before-and-after evidence

Fresh guarded broker captures obtained 16,206 ticks on October 24, 13,881 on
October 25, 14,781 on October 28 and 21,334 across two contiguous weekend
requests: 66,202 new ticks total. The existing October 29 capture supplied
previously unexamined JOLTS event-minute statistics.

Official schedules anchor the [October 24 claims release](https://oui.doleta.gov/press/2024/102424.pdf)
at 08:30 Eastern and [October 29 JOLTS](https://www.bls.gov/news.release/archives/jolts_10292024.htm)
at 10:00 Eastern, corresponding to 12:30 and 14:00 UTC on those dates.

| Event / feed | Event ticks / bid range | Control ticks / bid range | Declared screen |
| --- | --- | --- | --- |
| Oct 24 HistData, 08:30 vs 07:30 | 530 / 14.7 pips | 89 / 1.3 pips | Passed |
| Oct 24 broker, 15:30 vs 14:30 | 129 / 12.6 pips | 37 / 1.3 pips | Passed |
| Oct 29 HistData, 09:00 vs 10:00 | 572 / 21.3 pips | 131 / 2.7 pips | Passed |
| Oct 29 broker, 16:00 vs 17:00 | 144 / 24.3 pips | 74 / 2.5 pips | Failed count |

Every screen required at least 3x control range and 2x control tick count.
The last row passes the range requirement but has 144 ticks against a required
148: approximately 1.946x instead of 2x. All four screens were required; no
rounding, threshold relaxation or replacement date was used after inspection.
Broker sampling rates and event responses differ, so this screen is a research
heuristic, not a statistical certificate of a timezone.

All six hourly closes on each fresh price-comparison day match the proposed
mapping: maximum differences are 0.2 pip on October 24, 0.3 pip on October 25
and 0.2 pip on October 28. No required hour was absent.

## Boundary and implementation

The source-label intervals declared empty were verified to contain no quotes:
HistData October 26 00:00–October 27 12:00, broker October 26 06:00–October 27
18:00. Both feeds contain quotes on either side. The nearest observed raw
labels are:

| Feed | Last quote before gap | First quote after gap |
| --- | --- | --- |
| HistData | Oct 25 16:59:59.388 | Oct 27 17:00:00.046 |
| Broker | Oct 25 23:58:57.047 | Oct 28 00:00:00.053 |

These are raw labels, not UTC timestamps. Under the candidate mapping the
reopening observations align at October 27 22:00 UTC. The evidence brackets a
quote-free interval; it cannot identify the exact instant a clock changed.
Different cutoffs inside the verified empty interval yield identical mapped
observations. Completeness of all possible market quotes is not established.

Added `scripts/research-007.py` with an October-only, explicitly bounded
converter and separate check/build phases. It preserves quote values, sequence
and same-millisecond ordering; rejects quotes in the declared quiet interval,
other months, missing sides, reordering and cutoffs outside the empty interval;
and records the mapping/evidence in provenance if construction is permitted.
It never infers an annual DST calendar or changes the existing parser.

The hypothetical mapping was used in memory for diagnostics. The failed event
screen prevented publication of a normalized 007 dataset. An actual build
attempt was rejected before writing a candidate. No performance manifests,
strategy runs or new profit estimates were produced.

## Verification and evidence

The full suite passed **136 tests**. Eight new tests cover both interval offsets,
empty-period rejection, cutoff equivalence, repeated timestamps, input order and
scope, required event checks and construction rejection. Prior 004/005 frozen
source/archive contents, 006 archived source and failed 005/006 reviews were
verified unchanged. The strategy engine remains unchanged.

Local, Git-ignored evidence:

- `reports/research-007-clock.json`: event counts/ranges, 18 price comparisons,
  raw gap endpoints, source/capture hashes and failed overall result.
- `reports/research-quality-007.json`: no eligible datasets;
  `performance_evaluation_ready: false`, `demo_execution_ready: false`.
- `reports/research-007-audit.json`: actual rejected build and prior-artifact checks.
- `reports/research-007-blocked-source.zip`: diagnostic source and tests.
- `data/research-007-mt5-*`: five new read-only capture directories.

## Next work

The interval hypothesis now has substantial supporting diagnostics, but it did
not satisfy its declared gate. Preserve that outcome. Before another October
performance study, seek authoritative source-clock metadata or calibrate the
event-screen method on a separately selected event set, lock its decision rule,
and test it on fresh evidence. Do not lower the count threshold to accommodate
144/74 or reuse the same observations as a fresh validation.

Observation-only MT5 signal-parity and runtime account-guard testing can proceed
independently while October stays quarantined. None of these checks establishes
a profitable strategy. Existing January/April losses and July's fragile gain
remain the only completed monthly tick evidence. The consumed 2025 holdout and
reserved November–December 2026 validation remain excluded. No orders, EA
deployment or terminal setting changes occurred; real execution is unavailable.
