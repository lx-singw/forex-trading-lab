# Minute-label diagnosis 017 — completed 2026-10-06

The end-label interpretation has the smallest close-distance median in every
day/source comparison. Four of six broker screens pass; two January screens
fail the declared improvement margin. Five of six HistData screens pass;
July 7 has only 176 common labels because quotes are absent. The overall
six-day broker screen fails. Original-provider bar semantics and annual UTC
remain unverified. No earlier failed review was rewritten or approved.

Independent reconstruction checks 560,147 selected quotes, 3,480 minute bid/ask
aggregates, 3,576 day/source labels and 10,728 interval comparisons. All saved
arithmetic matches. 261 software tests pass, including seven new interval,
same-ms, missing-data and inference checks. No trading results were computed.

## Declared comparisons and results

Exactly the six 016 anchor days were reused. Each source comparison includes
298 reference labels, UTC10:01 inclusive to UTC14:59 exclusive. A label T was
compared with tick minutes [T-60s,T), [T,T+60s) and [T+60s,T+120s). Quote counts,
original source-row endpoints and bid/ask OHLC are retained. Missing quotes
stay missing; no interpolation, carried price or fabricated candle.

All medians below use the same common labels for all three interpretations.
The screen requires >=240 common labels, end-label median <=2 pips, and both
alternative medians at least 0.25 pip above it. Display values are rounded;
machine reports retain their original numeric values.

| Day | Source | Common labels | End median | Literal-start median | Future median | Screen |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| 2022-01-07 | Broker | 298 | 1.45 | 1.60 | 1.80 | Fail: 0.15 improvement |
| 2022-01-07 | HistData | 298 | 1.30 | 1.55 | 1.60 | Pass |
| 2022-07-08 | Broker | 298 | 1.50 | 2.40 | 3.00 | Pass |
| 2022-07-08 | HistData | 298 | 1.30 | 2.20 | 3.00 | Pass |
| 2022-11-04 | Broker | 298 | 1.50 | 2.25 | 2.95 | Pass |
| 2022-11-04 | HistData | 298 | 1.30 | 2.20 | 2.80 | Pass |
| 2023-01-06 | Broker | 298 | 1.60 | 1.80 | 2.15 | Fail: 0.20 improvement |
| 2023-01-06 | HistData | 298 | 1.40 | 1.70 | 2.05 | Pass |
| 2023-07-07 | Broker | 298 | 1.55 | 1.85 | 2.30 | Pass |
| 2023-07-07 | HistData | 176 | 1.40 | 1.65 | 2.30 | Insufficient coverage |
| 2023-11-03 | Broker | 298 | 1.40 | 1.80 | 2.10 | Pass |
| 2023-11-03 | HistData | 298 | 1.40 | 1.90 | 2.20 | Pass |

This evidence makes the end-label hypothesis plausible relative to the existing
clock hypotheses. It does not supply the original provider's label definition,
prove either tick stream's absolute UTC, or explain residual feed differences.
No minute shift was applied to the stored reference or 015 dataset. Stage 016's
literal-label comparisons and failed distance screen remain unchanged.

The cached broker labels use the earlier +2h winter/+3h summer hypothesis.
Selected HistData quotes use the unchanged 015 candidate clock. The independent
checker separately confirms selected raw-label calendar arithmetic. Neither
calculation proves the feed clock or source-specific historical session hours.

## Primary documentation and access feasibility

Reviewed [Forexite import instructions](https://www.forexite.com/free_forex_quotes/import_quoteroom.html),
[version history](https://www.forexite.com/free_forex_quotes/quoteroom_history.html)
and the [TradeRoom guide](https://www.forexite.com/forex_trading_forexite/Forexite_TradeRoom_User_Guide_EN.pdf)
did not establish an original MetaStock minute start/end definition. The guide
describes chart OHLC and selectable bid/ask views; that is not a statement about
the original downloadable format's price side or timestamp convention.

The [FXCM-owned TickData README](https://github.com/fxcm/MarketData/tree/master/TickData)
lists public weekly archives for 2019–2023, UTC timestamps and indicative
quotes. Its [main README](https://github.com/fxcm/MarketData) instead asks for
an email request for ticks. These conflicting access descriptions were retained.
Under a separate predeclared metadata-only plan, the first ordinary HEAD request
to `EURUSD/2023/12.csv.gz` returned HTTP403. Further FXCM archive requests stopped;
weeks 13/28 were not requested, no quote body was downloaded and no GET fallback
or changed identity was used. HEAD failure does not establish what an
authenticated or other supported download route would provide.

[TrueFX historical downloads](https://www.truefx.com/truefx-historical-downloads-2/)
advertise free tick data and require login/registration. Its public page did
not expose the needed authenticated 2023 download inventory. No registration,
login, new broker account, paid service or provider message occurred. Dukascopy
remains stopped after 011. See `SOURCE-ACCESS-017-PLAN.md` and preserved outcomes.

## Verification and artifacts

- Frozen scope/code/input hashes: `reports/labels-017-ledger.json`, seal and
  source ZIP; `docs/LABELS-017-PLAN.md` remains unchanged.
- Implementation: `src/forex_demo_lab/minute_labels.py` and `scripts/labels-017.py`.
- Tests: `tests/test_minute_labels.py`; independent stream checker:
  `scripts/check-labels-017.py`, which imports neither aggregator nor converter.
- All twelve minute/interpretation reports: `reports/labels-017/*.json`.
- Overall diagnostic review and separate arithmetic check:
  `reports/labels-017-review.json` / `labels-017-independent.json`.
- Source documentation and HEAD outcome: `data/source-access-017` and
  `reports/source-access-017-documents.json` / `source-access-017-review.json`.
- Actual market-gate rejection, prior evidence preservation and final checks:
  `reports/labels-017-market-gate.json`, preservation and checks JSON.
- Completed source/evidence snapshot: `reports/labels-017-final-source.json/.zip`.

All jobs finished. Before reuse verify 013/015, both 016 ledgers, then
`labels-017.py verify`. Completed run/check outputs use exclusive creation;
do not rerun over them. Original 008/010/013/014/015/016 report bindings,
016 reference inputs and 144 monthly 015 metadata hashes remain unchanged.

## Decision and next work

The 014 market gate rejects the diagnostic review before performance. Annual
clock, session coverage, historical costs and profitable edge remain unresolved.
The bot still has no order-placement or real-money mode. No terminal settings,
deployment, broker calls or source blending changed. 2025 remains excluded;
reserved November–December 2026 data remains untouched.

The user confirmed they have neither TrueFX access nor another historical tick
source. Acquisition remains deferred until original 2023 bid/ask ticks become
accessible. Once a real inventory/schema is available, declare bounded March/July
acquisition and verification before downloading or computing new statistics.
Retain that source separately and review full chronology, costs, session gaps
and lineage before any annual approval. Do not lower old thresholds or change
test periods to force a pass.

Independent engine work can continue: next declare an observation-only MT5
signal-parity and runtime account-guard test harness using fixed synthetic or
already-seen development inputs. Preserve the original compiled observer and
keep all order placement unavailable. Compilation is not runtime validation;
report exactly which checks actually execute. This does not approve market
data, produce fresh validation returns or activate demo trading.
