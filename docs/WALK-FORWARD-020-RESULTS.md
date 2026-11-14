# Corrected-metric runner migration 020

Completed 2026-10-06. A separate chronological runner now explicitly uses the
019B executable-fill equity metric. **All 80 corrected scenario comparisons
pass**; independent Decimal reconstruction checks **107,280 tick marks**.
The full Python suite passes **299 tests** (nine new). Existing rejected market
reviews still fail before data iteration or performance. No market returns,
broker calls, MT5 run, order code or trading activation occurred.

## What changed

`src/forex_demo_lab/walk_forward_metrics.py` is generated from preserved 014.
The only changed function bodies are source inventory, freeze, verify,
replay-window report metadata and run metadata. The simulator import points to
`ExecutableEquityResearchTickSimulator`. Gate, tick iterator, warmup/window
logic, annual/quarter reconciliation and training selector are unchanged.
The generator and a structural regression test enforce those edit boundaries.

Every new ledger, scenario, training choice and summary identifies runner 020
and metric contract `executable_fill_equity_019b_v1`. Scenario reports also
include peak tick equity. Legacy 014 ledgers reject with a new freeze required;
wrong or missing version metadata rejects. There is no silent checkpoint or
report migration. The new command is `scripts/walk-forward-020.py`; original
014 and other older commands still represent their frozen legacy versions.

The fixed research rules remain five candidates, two hypothetical cost profiles,
fold A training 2020–2021/test 2022 and fold B training 2021–2022/test 2023.
Each window has 201 closed warmup hours, independent starting capital and an
exclusive training-choice lock before test replay. All ten test controls are
published, including when the choice is CASH. No strategy/parameter search.

## Full software comparison

The plan and all three experiments were frozen before any new replay. Original
014 invented inputs/reports remain byte-preserved. Its compatibility fixture has
no target fills, so a separately fixed target challenge tests the actual repair.
The latter contains 520 hourly bars per synthetic year, all in January, with
declared long/short breaks and two 100ms overshoot quotes. It is intentionally
not full-year market coverage and cannot be used as market evidence.

| Software control | Replays this stage | Paired scenarios | Unchanged nonmetric checks | Drawdown changes |
|---|---:|---:|---:|---:|
| Corrected replay of saved 014 sinusoidal fixture | 40 | 40 vs preserved 014 | 8,180 | 0 |
| Legacy shadow plus corrected target challenge | 80 | 40 | 3,084 | 28 |
| Total | 120 | 80 | 11,264 | 28 |

All matched fields include cash P&L, full trades, fills, fees, carry, quantities,
open period marks, annual/quarter statistics and every nondrawdown metric. Every
changed drawdown decreases; no cash improvement is attributed to the correction.
The challenge records **66 target fills** across its corrected scenarios.

For example, synthetic A-test C00/base reports old tick drawdown 8.090544% versus
corrected 0.140777%, with identical cash/trades. This shows the old phantom-peak
effect under the deliberately large generated overshoot; it is not an observed
market drawdown improvement or evidence of profitability.

Both folds select **CASH** for compatibility, legacy challenge and corrected
challenge. The choice is recomputed from the same unchanged training-only
selector, and remains locked before tests. New training hashes can differ where
corrected drawdown changes, so they are independently checked rather than
treated as identical legacy evidence. CASH returns zero in the software control
and fails the positive-edge screen. No winner is promoted from invented prices.

## Independent checks and gates

The preserved 014 checker reconstructs every trade charge and open quarter/year
mark. A new Decimal ledger reconstructs lot rounding, adverse entry/stop/end
fills, limit target fills, commissions, skipped UTC weekday/triple swap and
after-fill equity at every quote, without using a simulator/strategy helper.
It validates all **80 corrected accounts**, peak equity, tick drawdown and
period totals. Compatibility covers **69,930** tick marks and **178** open
boundary marks; challenge covers **37,350** tick marks and **8** open boundary
marks. The legacy challenge gets its own independent original arithmetic check.

The actual new freeze path rejects normalization 015, reference 016B and labels
017 review files before touching their sentinel dataset paths or creating an
experiment directory. These are negative gate probes, not fabricated annual
datasets or approvals. All three record `blocked_before_data_iteration_and_performance`.
Existing annual clock/bar semantics/session coverage and cost limitations stay
unresolved. No numerical threshold, failed review or eligibility gate was relaxed.

The nine new tests cover exact migration boundaries, actual corrected-class
construction for all ten accounts, ledger/version rejection, blocked-year/gap
rejection before input iteration, choice locking, future exclusion, corrupted
but rebound peak/drawdown/fill/version reports, comparison inventories and
declared challenge quotes. **299 tests pass**. The completed artifact snapshot
binds updated documentation, generated source and all reports.

## Evidence and use

- Migration freeze: `reports/walk-forward-020-ledger.json`, `.sha256`, source ZIP.
- Corrected compatibility: `reports/walk-forward-020-compat/`.
- Legacy challenge shadow: `reports/walk-forward-020-challenge-legacy/`.
- Corrected challenge: `reports/walk-forward-020-challenge/`.
- Challenge inputs: `data/walk-forward-020-challenge/`, explicit synthetic role.
- Comparison: `reports/walk-forward-020-review.json`; independent check files
  `walk-forward-020-{compat,corrected_challenge,legacy-challenge}-independent.json`.
- Negative market path: `reports/walk-forward-020-market-gates/review.json`.
- Full suite: `reports/walk-forward-020-checks.json`.
- Completed source/evidence: `reports/walk-forward-020-final-source.json`,
  `.sha256`, `.zip`.

Verify the completed stage without replaying it:

```sh
PYTHONPATH=src python3 scripts/migrate-walk-forward-020.py verify
PYTHONPATH=src python3 -m unittest discover -s tests
```

For a separately declared future input with appropriate evidence, the versioned
CLI retains `freeze`, `verify`, `run` and `check-review` commands. Never rerun
into an existing experiment or overwrite a partial run. Synthetic review remains
distinct from market review. Neither a checker nor a hash proves market-source
quality; that requires independent evidence before the gate may pass.

## Remaining work

The evaluation engine is ready for properly reviewed inputs, but the existing
annual history is still ineligible. The next priority is a bounded public-source
feasibility review for an independently usable 2020–2023 bid/ask archive, plus
historical clock/session evidence. Research documentation first, stop at access
restrictions, and preserve FXCM/TrueFX/Dukascopy limitations without replaying
stopped endpoints or creating accounts. Do not return to strategy tuning or
compute market returns until input evidence is sufficient. Actual MT5 account
API integration remains a separate observation-only task. Consumed 2025 and
reserved November–December 2026 were untouched. Performance, profitability and
demo-execution readiness remain **false**; orders remain unavailable.
