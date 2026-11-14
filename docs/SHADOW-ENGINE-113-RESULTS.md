# Shadow engine113 — offline integration results

The offline adapter, fixture generator, CLI and integration tests are implemented.
**155 focused tests passed**: 36 new integration tests and 119 relevant existing
simulator/model/inspector tests, with zero failures, errors or skips in 5.250s.
These results verify software behavior. **No market profitability was evaluated.**

The adapter reuses the fixed baseline and existing corrected019B executable-fill
equity engine. It retains SMA20/SMA50, simple ATR14, 2ATR stop, 2R target, 0.25% risk,
1% daily entry pause and existing position/sizing/margin rules. Frozen baseline,
old simulator/strategy and native sources remain unchanged. Four new source files
provide the adapter, generator, CLI and tests.

## What was checked

- Incremental adapter prefixes, trades and final metrics match the existing
  corrected baseline engine. Changed future prices cannot alter earlier entries.
  Warmup/current-hour values cannot create early signals; missing hours are not filled.
- Development exits cannot read validation prices. Validation warms up on preceding
  observations with fresh $10,000 capital and no carried position or trades.
- Typed fields, sequence, receipt/source order, invented quote age, crossed/nonfinite
  quotes, same-source-time conflicts, size/count limits and duplicate fields reject.
  Repeated latest quotes are retained; identical latest-event replay is a no-op.
- Both trade directions, spread/slippage sides, fees, rollover financing, target
  limits, stops through gaps, daily pauses, position caps and restart are checked.
  Reference gross minus all costs reconciles with simulator net and final balance.
- Mid-position, empty and completed checkpoints restore consistently. Changed
  fixture/config/scenario/partition, damaged cursor/state/checksum and legacy metric
  versions reject. Public event/fixture/manifest views cannot mutate frozen inputs.
- Valid complete, stopped, incomplete and invented-labelled native captures never
  construct a simulator. Their raw clock/age/quality prerequisites remain unresolved.

Relevant retained checks include 48 actual-account guard decisions and more than
43,000 shared native-run core decisions on invented facts. No terminal execution
or current-account assessment is inferred from those portable tests. The older
2,095-test active-suite result is retained; this was not a new full-suite run.

## Invented demonstrations only

Two paths were predefined in the generator: a continuation and a reversal, each
with 192 invented hours and 768 quotes, development starting after 51 warmup hours
and validation at hour 96. The clocks are explicitly invented UTC milliseconds in
2001. These are shaped software fixtures, not market records or forecasts.

Both fixture byte hashes, source bindings and exact scenario settings were frozen
before the final demonstration. All eight scenario/partition results were retained.
The CLI and direct library agree; inputs remain byte-for-byte unchanged.

| Invented path | Cost scenario | Span | Trades | Net invented USD |
|---|---|---|---:|---:|
| Continuation | Base | Development | 1 | +39.28 |
| Continuation | Base | Validation | 2 | +79.00 |
| Continuation | Adverse | Development | 1 | +35.18 |
| Continuation | Adverse | Validation | 2 | +10.14 |
| Reversal | Base | Development | 1 | -125.19 |
| Reversal | Base | Validation | 1 | -196.20 |
| Reversal | Adverse | Development | 1 | -119.52 |
| Reversal | Adverse | Validation | 1 | -176.54 |

The positive figures come from deliberately invented continuation prices. They
establish that the profit path works in software, not that a strategy predicts
markets. The validation label separates invented chronological spans; it is not
untouched market validation. No strategy was selected from these results.

Base uses the existing hypothetical $7 round trip per lot, 0.2pip adverse market
slippage and -$3/-$1.50 long/short financing. Adverse uses predeclared $10, 0.5pip,
-$4.50/-$2.25 financing and a 1.2pip minimum spread. Costs can reduce position size,
so larger assumed costs do not guarantee a more negative dollar loss on every path.
Neither scenario derives costs from the tiny native demo spreads.

An invented stop-gap check estimates at most $25 trade risk under its assumptions,
then gaps beyond the stop and loses more. The next observed quote supplies the fill;
the pause latches. This demonstrates why a stop or daily entry-pause threshold is
not a guaranteed maximum loss. All targets remain modeled limit fills, not assured
broker fills. Quote/depth/latency/margin and rollover details remain model assumptions.

## Review corrections and retained evidence

The initial test loader imported a nonexistent fixture helper. It ran no integration
cases; the error/source snapshot was retained and the import corrected. Subsequent
28-case, 145-case and 146-case passing runs remain recorded separately. Final 155
includes the additional corrected-equity regressions and seven existing019B tests.

Review also made public input views defensive copies. A second review found that
the prototype initially inherited the old pre-target quote mark, despite the
repository having a corrected019B engine. Final integration uses that existing
correction and requires its metric version in checkpoints. Five of eight invented
drawdown results change; all fills, costs and net P&L remain identical. Earlier
source archives, fixtures, reports and drawdown comparisons remain preserved.
This does not recalculate or alter any historical market result.

Final demonstrations: `data/shadow-engine-113-invented-demo-r3/` and
`reports/shadow-engine-113-demonstration-003.json`. Tests:
`reports/shadow-engine-113-tests-003.json`. Prior variants stay in their own paths;
their manifests correctly reject the changed code instead of silently resuming.

The actual107,109 and111 copied exports were inspected read-only by the new CLI
and library, which agree. All 62 input hashes remain unchanged. The111 run still
contains 7,188 observations, 60 files and a clean time-limit stop, but all three
return `performance_unavailable` without native metrics. No guessed three-hour
offset, market simulation, acquisition, account/settings/log inspection, MT5 launch,
SDK, provider contact or order was performed.

All 524 old implementation/config/test hashes remain unchanged; four new files make
528 retained sources. Earlier handoff bodies and predecessor evidence are preserved.
No historical provider route, H.10/native090 closure, old strategy/cost rule or
reserved validation period was reopened. UTC, source age, executable costs, feed
qualification and market/paper/order admission remain unresolved/unavailable.

## Next

Integrate the existing fixed C00/C05/C06 research decisions under the same offline
fixture, cost and restart discipline, with common 201-hour warmup and a CASH
reference. Scope is prepared in [STRATEGY-ADAPTER-114-PLAN.md](STRATEGY-ADAPTER-114-PLAN.md).
Do not add a winning combination by selecting on these fixtures or on112.
Later market comparisons still require adequate qualified development data and
untouched chronological validation. No further MT5 launch is needed for this step.
