# Comparison 008 — five fixed strategies on reused development data

Declared protocol: [COMPARISON-008-PLAN.md](COMPARISON-008-PLAN.md).
Research rationale: [STRATEGY-RESEARCH-008.md](STRATEGY-RESEARCH-008.md).
The first batch tests entry alternatives with shared exits and risk controls.
It does not select a strategy for deployment or establish a profit guarantee.

Completed 2026-10-01: all 30 scenarios and their final audit passed. Twelve
scenarios gained money and eighteen lost money. Every candidate lost in at
least one window under both cost assumptions. The slower crossover has just
three trades across the three windows; its two wins cannot establish an edge.
The selector improved on breakout alone in all three windows, but lost in
January and April and did not consistently improve on range re-entry.

## Observed results

Exact normalized UTC windows below include the final quote. The April/July
source-month labels extend into the next UTC month under the scoped mapping.

| Sample | Evaluation begins UTC | Last quote UTC | Evaluated observed H1 bars |
| --- | --- | --- | ---: |
| January | 2024-01-12 07:00 | 2024-01-31 23:59:58.068 | 329 |
| April | 2024-04-11 13:00 | 2024-05-01 03:59:55.269 | 327 |
| July | 2024-07-11 13:00 | 2024-08-01 03:59:55.131 | 351 |

B/A means base/adverse costs. Net P&L includes modeled costs. With each starting
balance at $10,000, $100 is one percentage point of return. Tick drawdown is the
largest observed peak-to-trough equity decline including open positions.
Win rates with one trade describe that single observation only.

| Candidate | Window | Trades B/A | Net USD B/A | Tick drawdown % B/A | Win % B/A |
| --- | --- | ---: | ---: | ---: | ---: |
| C00 | January | 7 / 7 | -99.11 / -104.37 | 1.548 / 1.591 | 14.3 / 14.3 |
| C00 | April | 7 / 7 | -0.08 / -3.23 | 0.875 / 0.879 | 42.9 / 42.9 |
| C00 | July | 7 / 7 | +36.43 / +25.52 | 0.889 / 0.909 | 42.9 / 42.9 |
| C01 | January | 1 / 1 | +44.90 / +44.54 | 0.158 / 0.158 | 100.0 / 100.0 |
| C01 | April | 1 / 1 | -24.22 / -26.11 | 0.584 / 0.590 | 0.0 / 0.0 |
| C01 | July | 1 / 1 | +46.05 / +42.18 | 0.200 / 0.185 | 100.0 / 100.0 |
| C02 | January | 18 / 18 | -158.09 / -163.82 | 1.813 / 1.875 | 22.2 / 22.2 |
| C02 | April | 11 / 11 | -166.49 / -170.33 | 2.036 / 2.084 | 18.2 / 18.2 |
| C02 | July | 13 / 13 | -109.32 / -121.49 | 1.503 / 1.569 | 23.1 / 23.1 |
| C03 | January | 11 / 11 | +6.92 / +0.79 | 1.256 / 1.275 | 36.4 / 36.4 |
| C03 | April | 10 / 11 | -168.46 / -197.08 | 1.784 / 2.066 | 10.0 / 9.1 |
| C03 | July | 8 / 8 | +49.34 / +41.68 | 0.898 / 0.909 | 50.0 / 50.0 |
| C04 | January | 9 / 9 | -12.81 / -14.36 | 1.212 / 1.199 | 33.3 / 33.3 |
| C04 | April | 11 / 11 | -86.24 / -99.84 | 1.750 / 1.792 | 27.3 / 27.3 |
| C04 | July | 7 / 7 | +51.72 / +37.29 | 0.823 / 0.838 | 42.9 / 42.9 |

The selector's July base result is $2.38 above range re-entry, but its adverse
result is $4.39 below range re-entry. It also loses more than range re-entry in
January. This batch therefore does not show a consistent combination benefit.
Breakout alone loses in every window, even before commissions and swap (gross
still includes spread/slippage). Simply reducing commissions would not repair it.

Profits are concentrated. Each positive C01 window consists of one winning
trade. Removing the largest winner from base C03 January or C00 July changes
the window to a loss. Base C03/C04 July retain only $5.01/$5.27 respectively
after removing their largest winner. This is a descriptive sensitivity check,
not a valid substitute return or a statistical confidence interval. Per-trade
expectancy and this calculation for all scenarios are in the audit artifact.

For the base selector, January's range/trend entries earned -$28.23/+$15.42;
April's earned -$53.33/-$32.91; July's earned +$32.62/+$19.10. These are the
selector's actual trades, not full standalone component returns: being in one
position prevents later entries. The condition labels are fixed indicator
rules, not verified descriptions of the market's true regime.

## Scope and interpretation

Each scenario starts with its own $10,000 simulated account. The first 201
observed H1 bars are warmup only; no positions or profit carry into evaluation.
These are partial-month windows, so even C00 differs from earlier whole-month
baseline reports. The same quotes and boundaries are used for every candidate
within a sample. January uses the scoped MT5 tick dataset; April/July use their
scoped HistData clock interpretations. Absolute clock metadata and historical
broker costs remain unverified. October remains quarantined.

All samples were already examined during development. Five candidates and two
cost assumptions reuse observations; 30 scenarios are not 30 independent trials.
Monthly capital restarts, gaps between samples and the short windows prevent
treating these as a continuous portfolio or annual return. Idle USD cash has
zero modeled return, without interest. The consumed 2025 holdout is excluded
from optimization and reserved November–December 2026 remains untouched.

## Shared implementation and costs

- C00: original SMA20/50 entry rule.
- C01: slower SMA50/200 crossover.
- C02: 20-bar channel breakout, confirmed by a closed candle.
- C03: re-entry from a two-standard-deviation price excursion over 20 bars.
- C04: fixed trailing-efficiency selector using C02 in its trend condition,
  C03 in its range condition, and no trade between the two conditions.

The selector chooses one component at entry and never stacks positions. All
candidates retain the ATR14-times-two stop, 2R target, 0.25% estimated trade-risk
cap, 1% daily entry pause, 1.5-pip spread limit and modeled 1:10 leverage. A stop
is not a guaranteed maximum loss: gaps and modeled slippage can exceed it.

Base costs are $7 per lot round trip, 0.2-pip modeled slippage, and daily long/
short swaps of -$3/-$1.50 per lot. Adverse costs are $10, 0.5 pip and -$6/-$3.
Both use an assumed UTC reset and Wednesday triple swap. Bid/ask spreads come
from quotes. These are cost scenarios, not verified historical broker terms.
Quote replay does not establish executable broker fills, latency or liquidity.

Costs can alter the trading path. April C03 took ten trades at base costs and
eleven at adverse costs. Its April 23 short stopped on April 25 at 10:17 UTC in
the base run but 08:13 UTC in the adverse run, allowing an extra adverse-case
entry at 10:00 UTC that lost $23.70. Entry slippage changes entry-relative stop/
target prices, and fees also affect sizing/equity. Stress outcomes therefore
cannot be reproduced by simply subtracting extra fees from base trades.

## Reproducibility

The batch ledger, `reports/comparison-008-ledger.json`, froze all 30 scenarios,
input hashes, quality-review bindings, evaluation windows, cost/risk configs,
implementation and protocol before returns. `reports/comparison-008-source.zip`
preserves the source, scripts, tests, specification and protocol. Outputs are
immutable; the runner rejects existing output paths and changed bindings.

Individual outputs follow `reports/comparison-008-{month}-{candidate}-{cost}.json`.
They contain trades, evaluated hourly equity and decisions made while flat,
with closed-history features and reasons. `reports/comparison-008-summary.json`
binds their hashes to the ledger. Generated reports/data are local, Git-ignored
artifacts. No parameter or exit adjustment is permitted within this batch.

`reports/comparison-008-audit.json` verifies all 30 report hashes, accounting,
trade counts, warmup/evaluation coverage, nonoverlapping positions, decision
boundaries and final equity. Source archive bytes and frozen data/review bindings
still match. All runs finished; no background comparison process remains.

158 tests passed before freezing. They include current/future-data isolation,
common warmup, signal boundaries, flat markets, risk controls, gap losses,
duplicate replay, checkpoint mismatch rejection and open-position recovery.
The default tick engine matched its saved pre-change synthetic trades, equity
and metrics exactly. Old 004/005 archives and diagnosed reports are preserved.

## Next research step

Acquire and independently review longer contiguous history, with 2020–2023 as
a proposed acquisition target rather than an existing validated dataset. Freeze
actual chronological development/test windows, a bounded candidate budget and
numeric selection criteria before evaluating returns. Any weights or parameters
must be chosen from earlier data only and held fixed for each later test window.
Record every attempt and failure. Compare combinations with their components
and cash; require evidence across periods and higher-cost assumptions.

Do not tune a selector to rescue this batch or call its highest result a proven
winner. A different selector, exit rule or horizon requires a new experiment.
No broker orders, EA deployment, terminal changes or execution activation are
part of comparison 008. Reliable profitability remains an open research question.
