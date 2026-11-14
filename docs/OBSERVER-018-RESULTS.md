# Observation-only MT5 runtime results 018/018B

Completed 2026-10-06. The original observer remains byte-for-byte unchanged.
Its existing function bodies now have compiled runtime evidence on 38 fixed
synthetic cases in an isolated MT5 Math calculations test. Supplemental 018B
passes all 304 behavior comparisons and 82 native enum checks. The complete
Python suite passes 275 tests, including 14 new checker/input tests. This is
software validation, with no new market returns or profitability claim.

## Measured behavior

Seven direct guard cases verify connected DEMO acceptance, REAL/CONTEST/unknown
rejection, disconnected rejection without querying account mode, query-error
rejection and stale-error reset. Thirty-one observation cases cover baseline
BUY/SELL/flat decisions, true-range gap handling, a BUY cross with zero ATR,
50-bar warmup, copy failure, attachment/restart suppression, repeat closed
candles, closed/current-hour gaps, absent/nonpositive/crossed quotes, spread
below/above 1.5 pips, an existing position, pending order and initialization
on wrong symbol/timeframe or invalid account responses.

Simulated REAL/CONTEST switches at the next tick stop the observer. A switch
or query error at its final account read suppresses the suggestion. Native
account-read counts and last-closed state match the frozen expectations. The
adapter confirms the original requested shift 1 and 51 closed candles.

Four observation cases emit a suggestion, with correct direction and Python
baseline ATR distance within 1e-12. BUY/SELL and spread-below-limit distances
are 0.0013428571428571; the synthetic gap case is 0.0019142857142856. Repeated
closed candles emit no duplicate suggestion. These are generated prices,
not observed market trades, profits, filled stops or risk-sizing validation.

## Preserved first failure and correction

First attempt `1605d50e22c5413e97da4784a8dccdf1` compiled with zero errors and
warnings and completed all 38 cases. Its original strict review **failed**:
302/304 fields matched, but wrong-symbol and wrong-period initialization
returned 32767 while our Python fixture had assumed numeric 2 for parameter
rejection. Both cases correctly rejected initialization. The original failed
review, ledger, fixture expectations and raw output remain unchanged.

The separately frozen [018B plan](OBSERVER-018B-PLAN.md) changes diagnostic
serialization only. It uses named MQL initialization constants to produce the
existing canonical categories and exports every native value/name plus the
compiler enum constants. The checker validates both outputs, with no hardcoded
acceptance of 32767. Runtime evidence confirms this build's
INIT_PARAMETERS_INCORRECT=32767. The [official initialization contract](https://www.mql5.com/en/docs/event_handlers/oninit)
defines named rejection outcomes and nonzero failure; our first numeric
assumption was unsupported. No original observer decision was changed.

Repeat `37c21a8302064aa69437b50d94c14c7c` compiled with zero errors and warnings,
completed and passed the independent Python comparison. MT5 terminal/tester
binary versions were 5.0.0.6231; their hashes are recorded. Both terminal
processes exited within the 60-second limit, and no terminal/tester process
remained at the completion check. Both builds and Common/Files outputs remain
in uniquely named task directories; primary terminal profiles and EAs were
not deployed or edited.

The first direct PowerShell invocation was rejected because the UNC script was
unsigned. The trusted local script ran with an execution policy confined to a
new PowerShell process; no persistent execution policy was changed.

## Reproduction and evidence

- Frozen inputs: `reports/observer-018-fixtures.json` (January 2024 synthetic).
- Original freeze: `reports/observer-018-ledger.json`, `.sha256`, source ZIP.
- Supplemental freeze: `reports/observer-018b-ledger.json`, `.sha256`, source ZIP.
- First attempt: `reports/observer-018-attempts/1605d50e22c5413e97da4784a8dccdf1/`;
  `failed-review.json` explicitly preserves the rejected check.
- Passing attempt: `reports/observer-018b-attempts/37c21a8302064aa69437b50d94c14c7c/`;
  `results.csv`, `native.csv`, `review.json`, compiler diagnostics and launch
  receipt bind the config, inputs and output hashes.
- Full suite: `reports/observer-018b-checks.json`.
- Completed source/evidence snapshot: `reports/observer-018-final-source.json`,
  `.sha256` and `.zip`; binds the updated handoff and both runtime attempts.

From the repository, verify without replaying the completed experiment:

```sh
PYTHONPATH=src python3 scripts/observer-018b.py verify
PYTHONPATH=src python3 -m unittest discover -s tests
```

The checker writes review files exclusively; do not rerun it into the completed
attempt. A new isolated runtime attempt can be made with
`pwsh.exe -NoProfile -ExecutionPolicy Bypass -File scripts/run-observer-018b.ps1`.
Never attach this synthetic harness to a broker chart. It is tester diagnostics.

## Limits and next step

Actual terminal/account APIs are replaced by controlled responses inside the
compiled original functions. This proves their handling of those responses;
it does not certify actual account connection/switch behavior, account-query
failure semantics or broker feeds. Initialization, OnTick and removal are
called/captured by the harness. No real tick callbacks, orders, fills, position
management, loss caps, margin, restart persistence of execution or slippage
were exercised. Math mode and disabled local trading do not make this a market
backtest. The original observer has no order submission code.

Annual history remains ineligible after 017; absolute UTC/bar semantics and
open-session gap classification remain unresolved. TrueFX access is absent;
FXCM returned 403; Dukascopy remains stopped after 429. No acquisition retry,
broker account creation, market-data blending, strategy/cost change or new
return calculation occurred. Previous report bindings remain intact. Consumed
2025 and reserved November–December 2026 were not used. Both performance and
demo-execution readiness remain **false**.

Next independent work: audit the simulator's execution assumptions using fixed
synthetic quote paths (gaps through stops, entry/exit slippage, spread, fees,
rollover and shared loss limits) and strengthen only genuinely missing tests.
Freeze that software experiment before running it. Actual observer platform
integration and independent historical-source acquisition still require their
own bounded plans; neither may be promoted from these harness results.
