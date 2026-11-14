# Research 005 results — 2026-10-01

The broader study evaluated April 2024 and blocked October 2024 on its declared
clock/price check. **April lost in all four frozen scenarios. Demo execution
remains unavailable.** No strategy parameters or quality thresholds were changed.

April and October were chosen before downloading their ticks to complement the
January/July samples with the first month of each calendar quarter. The old
2024 annual OHLC result was already examined, so these are development samples,
not an untouched holdout. See the immutable [protocol](RESEARCH-005-PLAN.md).

## April performance

Each scenario starts independently at $10,000 using the unchanged SMA20/50,
ATR14 times two stop, 2R target and existing risk controls. Both existing cost
configs retain modeled 1:10 leverage and UTC daily resets/rollovers. Base costs
are $7 per lot round trip, 0.2-pip slippage and long/short daily swaps of -$3/-$1.50;
adverse costs are $10, 0.5 pip and -$6/-$3. These remain hypothetical terms.

| Clock interpretation | Costs | Trades | Net P&L | Return | Win rate | Maximum tick-sampled drawdown |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Empirical New York | Base | 9 | -$51.01 | -0.5101% | 33.3% | 1.1143% |
| Empirical New York | Adverse | 9 | -$51.98 | -0.5198% | 33.3% | 1.0912% |
| Documented fixed EST | Base | 9 | -$51.01 | -0.5101% | 33.3% | 1.1143% |
| Documented fixed EST | Adverse | 9 | -$51.98 | -0.5198% | 33.3% | 1.0912% |

Within each cost scenario, clock variants have identical metrics and all trade
fields except timestamps, which differ by one hour. They reuse the same quotes;
four runs do not create four independent samples. Cost changes affect sizing
and fills as well as charges, so every individual loss or drawdown need not
increase monotonically in the adverse scenario.

The largest base-cost trade loss was $31.05. Its short position stopped at an
observed exit of 1.06739 versus a nominal stop of 1.0669357, illustrating that
adverse quote gaps and modeled slippage can exceed the estimated stop risk.
Stops are not guaranteed loss bounds. Quote replay still lacks executable
depth, order queues, latency and actual broker fill verification.

Together with 004, the baseline has only 26 trades across three noncontinuous
monthly samples. January and April lost; July's small gain was fragile under
cost stress. This does not establish a dependable profitable edge. No annualized
or combined continuous return is calculated from independently funded months.

## Data checks and the blocked month

Downloaded and preserved both free HistData archives. April contains 1,560,509
ticks and 528 observed hours; October contains 1,772,075 ticks and 552 hours.
Both clock versions pass the declared boundary, hour-count and large-gap checks;
each has four weekend-pattern gaps and no unresolved intertick gap over one hour.
This bounded review does not establish complete coverage of shorter intervals.
Every one of the 3,332,584 quotes was checked between clock versions: sequence,
bid and ask are unchanged; timestamps differ by exactly one hour.

Fresh CPI event screens passed against the official 08:30 Eastern releases
([April 10](https://www.bls.gov/news.release/archives/cpi_04102024.htm),
[October 10](https://www.bls.gov/news.release/archives/cpi_10102024.htm)):

| Event | Source 07:30 ticks / range | Source 08:30 ticks / range |
| --- | --- | --- |
| April 10 | 40 / 0.5 pip | 671 / 58.5 pips |
| October 10 | 45 / 1.2 pips | 788 / 45.4 pips |

These support the empirical New York hypothesis but do not certify a source
timezone. The guarded MT5 captures yielded 17,325, 14,696 and 19,290 ticks:

- April 9, declared broker UTC+3: all six hourly closes within 0.1 pip; passed.
- October 9, declared broker UTC+3: all six within 0.2 pip; passed.
- October 29, declared broker UTC+2: none of six within one pip; maximum
  discrepancy 21.6 pips; **failed**. Both October clock candidates are blocked.

A separately labeled, post-hoc October 29 diagnostic with broker UTC+3 matches
all six closes within one pip. This points to an offset issue, but cannot prove
which source clock convention applies throughout the month or establish a
year-wide DST rule. It does not amend the protocol, unblock October or authorize
a performance run. No October performance manifests or returns were generated.

## Implementation and verification

Added `scripts/research-005.py` with immutable build, review, freeze and run
phases, reusing the existing strategy engine. It checks source/provenance hashes,
event evidence, month coverage and independent hourly prices. A failed month
blocks both its clock variants; only eligible months receive cost manifests.
All eligible scenarios are frozen before any returns are computed.

The full Python suite passed **122 tests**. Five new tests cover coverage gaps,
missing/incorrect broker hours, insufficient clock evidence, blocked studies
and changed protocols. The five targeted tests passed again after strengthening
source/evidence hash checks. All four reports reconcile trade gross/net P&L,
commissions, swaps, return, final equity and counts. Frozen code, protocol,
archive contents and inputs were checked; the 004 engine and archive remain
unchanged.

Local, Git-ignored evidence:

- `reports/research-quality-005.json`: April eligible, October blocked, all
  predeclared comparisons and failures.
- `reports/research-005-summary.json` and four April reports/manifests:
  metrics, individual trades, hourly equity and frozen assumptions.
- `reports/research-005-integrity.json` and `research-005-reconciliation.json`:
  quote-preserving clock checks and accounting verification.
- `reports/research-005-october29-posthoc-clock.json`: diagnostic only.
- `reports/research-005-freeze.json` and `research-005-source.zip`: source snapshot;
  archive SHA-256 `48b28e0e773c64e3f4175c9501b2ede76162131c5062b4fc1a965e1846598e6d`.
- `data/research-005-*` and `data/histdata-eurusd-2024{04,10}-original`:
  preserved captures, normalized candidates and original archives.

## Next step and limits

Predeclare fresh late-October event-time and cross-source checks to distinguish
the competing clock explanations before any new October evaluation. Preserve
this failed hypothesis and avoid relaxing its gate after seeing the evidence.
Historical broker charges, source completeness, MT5 parity and execution-specific
safeguards remain unresolved. Keep the baseline unchanged while assessing it;
the consumed 2025 holdout stays excluded from optimization.

November–December 2026 is reserved as future unexamined validation data under
the 005 declaration. It has not been collected or evaluated; a later protocol
must fix acceptance criteria before examining its returns. No scheduling,
trading, EA deployment or terminal setting changes were made here. Captures
used the guarded read-only demo path. Real-money execution remains unavailable.
