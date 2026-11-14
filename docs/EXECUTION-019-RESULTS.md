# Synthetic execution audit and metric repair 019/019B

Completed 2026-10-06. The audit found and repaired a tick-drawdown reporting
defect in a separate versioned simulator. The unchanged original engine and
failed audit remain preserved. **30/30 repaired synthetic cases pass**, with
**518 restart boundaries** and **290 passing Python tests** (15 new). None of
these paths contains market data; no new historical returns or orders occurred.

## Defect and measured correction

The frozen tick engine marks an existing position at the current bid/ask before
applying stop/target execution. When a quote jumps beyond a target, this gives
peak tracking the full favorable quote price. The simulator then fills its
limit exactly at the target. The earlier peak contains equity unavailable under
that same fill model; returning to the executed balance creates false drawdown.
Pre-exit fees can also make a transient mark exceed executable exit equity.

The independent Decimal ledger specifies events and reconstructs after-fill
cash, marked equity and drawdown without calling production sizing/exit helpers.
Original 019 passes **20/30 complete cases**. All 30 pass cash, position, costs,
pause and restart checks; ten target paths fail peak/drawdown fields. The strict
review remains failed. Its fixtures and expected outcomes were not changed.

| Fixed synthetic path | Original peak | Corrected peak | Original tick drawdown | Corrected tick drawdown |
|---|---:|---:|---:|---:|
| Long/short target overshoot | $10,084.59 | $10,042.46 | 0.417766% | 0.034100% |
| Actual C04 long/short trend probe | $10,346.05 | $10,019.414286 | 3.157106% | 0.139500% |

These numbers illustrate software arithmetic. The C04 probes use fixed generated
201-hour histories, not observed strategy profits or evidence of a trading edge.
Final balances and trade P&L are identical between the two versions.

The [separately declared repair](EXECUTION-019B-PLAN.md) adds
`ExecutableEquityTickSimulator` and `ExecutableEquityResearchTickSimulator` in
`src/forex_demo_lab/execution_metrics.py`. Their mark previews the existing fill
model on a triggering quote: stop at the observed exit quote with adverse
slippage, target at its limit, both including exit commission. Without a
trigger, held positions retain quote equity. The inherited opening/closing
code and fixed strategies are unchanged.

Both classes tag checkpoints with `executable_fill_equity_019b_v1`. They reject
legacy/mismatched snapshots, requiring replay instead of importing an inflated
peak. This is simulated state handling; no broker reconciliation is implemented.
The repair is available as a new offline class. Existing CLI and frozen 014
runner still use the original engine; there is no automatic migration or
retroactive replacement of old results.

## Interaction coverage

Fourteen annotated quote paths are applied to both baseline and research
engines, using injected decisions only to isolate execution. Two additional
paths exercise the actual unchanged C04 selector on 201 closed hourly bars.
The annotations, reference ledger and inputs were frozen before execution.

| Interaction | Evidence from fixed software paths |
|---|---|
| Wednesday rollover plus stop gap | Long/short fees, swap and quote fills reconcile; the pause latches. A long case loses $226.60 despite its approximately $23.98 estimated ordinary stop budget. |
| Variable ask spread | Ask-only widening leaves the long position open but stops the short at its ask plus adverse slippage. |
| Carry costs and recovery | Zero-spread/slippage probes isolate swap: carry relatches the new-day pause; later equity recovery does not clear it. |
| Skipped dates and restart | Wednesday triple plus Thursday/Friday charges give five units through Monday; weekend adds none. Duplicate replay adds no swap or fees. |
| Entry-cost loss pause | Spread, adverse entry slippage and entry commission breach a deliberately tighter diagnostic cap. Targets still operate; later profit does not unlock same-day entries. |
| Large stop loss and next-day reset | Recovery quotes cannot unlock same-day entry. New-day sizing falls from 0.22 to 0.21 lots on the reduced balance. |
| End-of-sample liquidation | Remaining positions use the appropriate bid/ask, adverse slippage and exit fee, exactly once. |

A pause blocks new entries; it does not cap losses or forcibly liquidate a
position. These gap losses are expected modeled behavior, not a stop-safety
guarantee. Swap, leverage, margin, fees, lot rules and slippage remain hypothetical.

Every input boundary is restored, its last tick replayed as a no-op, and its
remaining suffix compared with uninterrupted execution. All **518** final
checkpoints match; repeated finalization is idempotent. The repaired audit uses
the identical reference expectations and passes every field. A second comparison
checks **6,332 nonmetric fields** against the preserved original run: cash,
fills, costs, lots, position limits, pauses, fixed C04 decisions and restart
results are unchanged within the declared tolerances.

The 15 new Python tests independently check hand-calculated costs/carry,
executable target peaks, pause interactions, descending sizing after loss,
malformed/mutated results and inputs, both corrected target directions, actual
C04 paths, checkpoint versions and duplicate replay after rollover. The full
suite passes **290 tests**. A passing unit suite did not hide the original
failed integration audit: both outcomes are recorded separately.

## Reproducible evidence

- `reports/execution-019-fixtures.json`: all 30 input paths, annotations and
  Decimal expectations.
- `reports/execution-019-ledger.json`, `.sha256`, source ZIP: original freeze.
- `reports/execution-019-run.json` and `execution-019-review.json`: original
  20/30 failed integration review, preserved without editing.
- `reports/execution-019b-ledger.json`, `.sha256`, source ZIP: repair freeze.
- `reports/execution-019b-run.json` and `execution-019b-review.json`: repaired
  30/30 review, 518 restart boundaries and 6,332 unchanged nonmetric checks.
- `reports/execution-019-checks.json` and `execution-019b-checks.json`: 283-test
  original stage and 290-test repaired stage evidence.
- `reports/execution-019-final-source.json`, `.sha256`, `.zip`: completed source,
  handoff and evidence snapshot with prior report bindings.

Verification without re-executing completed paths:

```sh
PYTHONPATH=src python3 scripts/execution-019b.py verify
PYTHONPATH=src python3 -m unittest discover -s tests
```

Run/check outputs are exclusive. Do not replay those commands into completed
report names or edit any frozen fixture/plan/engine. Every case was published;
no parameter search or market interval selection was performed.

## Implications and next work

Earlier tick-derived peak/drawdown values can contain this reporting defect.
Do not use them as accurate execution drawdown for selection or approval until
a separately frozen replay with the corrected engine. This does not explain or
erase earlier realized losses: trade P&L is unchanged in this audit. Existing
market history and costs were already unvalidated; their rejection stays intact.
The OHLC simulator's close-sampled metric is a separate measure and was not
changed here.

Next: declare a new evaluation-runner version that explicitly imports the
corrected diagnostic engine, preserve 014, and compare its synthetic controls
without changing strategy/cost/selection rules. The market-data gate must still
reject unapproved history before any return evaluation. Independent source
access/clock/session validation and actual MT5 account API integration remain
separate unresolved work. No MT5 run, broker call, data download, live-money
capability or order activation occurred. Consumed 2025 and reserved
November–December 2026 remain untouched. Performance and demo-execution readiness
are **false**.
