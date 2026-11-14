# Research 006 — blocked absolute-clock checks, 2026-10-01

**The fresh October 30/31 checks failed. No October strategy returns were
computed.** Relative price agreement passed, but the independent release-time
checks failed in both feeds. October remains unsuitable for this declared
performance study; demo execution remains unavailable.

The [006 protocol](RESEARCH-006-PLAN.md) was declared before examining these
event statistics or collecting the new broker windows. It required every
event and price check to pass. The old 005 failed hypothesis and blocked gate
are preserved, not amended. The underlying archive had already been parsed;
these are fresh diagnostics, not previously unseen prices or a holdout.

## Observed evidence

Read-only, guarded captures returned 20,309 ticks for October 30 and 21,555 for
October 31, raw labels 12:00–18:00. Every capture passed exact date/boundary and
API integrity checks. The official BEA releases were scheduled at 08:30 EDT,
or 12:30 UTC ([October 30 GDP](https://www.bea.gov/news/2024/gross-domestic-product-third-quarter-2024-advance-estimate),
[October 31 personal income](https://www.bea.gov/news/2024/personal-income-and-outlays-september-2024)).
Other releases can coincide; quote activity is not proof of one event's effect.

| Date / feed | Earlier comparison minute: ticks / bid range | Predicted event minute: ticks / bid range |
| --- | --- | --- |
| October 30 HistData | 07:30: 409 / 9.3 pips | 08:30: 83 / 0.9 pip |
| October 30 MT5 | 14:30: 106 / 9.2 pips | 15:30: 55 / 0.7 pip |
| October 31 HistData | 07:30: 463 / 17.0 pips | 08:30: 157 / 3.8 pips |
| October 31 MT5 | 14:30: 129 / 15.8 pips | 15:30: 74 / 3.7 pips |

The declared event minute had to contain at least twice the comparison-minute
tick count and three times its range. All four screens failed. The stronger
activity occurred one hour earlier in each feed than the tested hypothesis
predicted. Broker 16:30 was also recorded as diagnostic context, as declared.

Under the paired assumptions HistData UTC-4 and MT5 UTC+3, all six hourly closes
per window match within 0.4 pip on October 30 and 0.2 pip on October 31. Changing
only the broker assumption to UTC+2 while retaining that HistData reference
produces maximum discrepancies of 29.4 and 20.3 pips. Those comparisons establish
relative alignment; they do not determine absolute UTC time.

## What this means

Two feeds can match each other while both normalized timelines are one hour
wrong. The event observations are consistent with a different paired late-month
mapping: HistData UTC-5 and broker UTC+2, which would both put the stronger
activity at 12:30 UTC. **That is an inference, not a certified convention or a
passing 006 hypothesis.** The checks here do not locate an exact transition,
prove its cause or establish an annual DST rule.

The early-October evidence supported HistData UTC-4. A single constant offset
for the entire month is therefore questionable. Do not silently apply the new
inference to October, reinterpret the earlier relative match as absolute proof,
or relax 006's thresholds. Both old constant-clock candidates remain quarantined.
January, April and July results are preserved as the provisional samples they
were; no returns were recomputed or strategy parameters changed.

## Implementation and verification

Added `scripts/research-006.py` for exact capture-window validation, paired
event/price checks, source-bound quality review and conditional freeze/run.
The actual freeze attempt rejected the failed review before creating a
performance manifest. No new normalized October dataset or source-for-performance
freeze was published. A separate blocked-study source archive preserves the
diagnostic implementation and tests.

The full Python suite passed **128 tests**. Six new tests cover minute boundaries,
missing/weak event activity, exact capture dates, all-required-check behavior,
blocked freeze rejection and the critical case where matching prices cannot
override failed absolute-clock evidence. Source engine, frozen 004/005 archive
contents and the 005 blocked quality report were verified unchanged.

Local, Git-ignored evidence:

- `reports/research-006-clock.json`: every minute statistic, both relative
  offset comparisons, coverage checks and source/capture hashes.
- `reports/research-quality-006.json`: `performance_evaluation_ready: false`,
  `demo_execution_ready: false`, no eligible datasets.
- `reports/research-006-audit.json`: actual rejected freeze, absence of new
  performance manifests/datasets, preserved prior artifacts and hashes.
- `reports/research-006-blocked-source.zip`: diagnostic source snapshot.
- `data/research-006-mt5-october30` and `...october31`: original broker captures.

## Next step

Before another performance study, predeclare a date-dependent clock hypothesis
and fresh before/after event anchors that can distinguish both feeds' absolute
offsets. Establish the transition boundary rather than selecting a constant
offset by price fit. If evidence supports it, construct a separate version with
explicit per-interval provenance and meaningful tests at the transition. A
failed hypothesis remains failed even when it suggests a useful next test.

Historical broker costs, completeness and execution parity remain unresolved.
The consumed 2025 holdout stays out of optimization; reserved November–December
2026 validation remains untouched. No EA was deployed, terminal setting changed
or order submitted. Real-money execution remains unavailable.
