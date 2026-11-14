# Strategy adapter114 — completed offline checks

Implemented fixed C00/C05/C06 comparisons and a CASH reference on frozen invented
quotes. All candidates receive 201 completed observed hours before decisions;
development and validation have independent fresh $10,000 accounts. No portfolio
balances or strategy weights are inferred from independent runs.

The adapter reuses unchanged `strategy_experiment_028.decision`, 113 event replay
and cost instrumentation, and corrected019B fill-equity/risk mechanics. It adds
candidate-bound checkpoints and fill sequence lineage. New fixture/schema/CLI/test
files leave all 528 predecessor source/config/test hashes unchanged; total532.
Old 113 fixtures and historical evidence remain intact.

**203 focused tests passed** in 27.212 seconds: 34 new integration tests and
169 retained (155 from113 plus 14 fixed-challenger028 tests), no failures/errors/
skips. Checks compare adapter prefixes and final decisions/fills/metrics/lineage
with the unchanged028 engine, base/adverse costs, fresh-capital partitions, common
warmup, causal future changes, range/direction abstention, missing-hour suppression,
cash, strict quotes and duplicate replay. Restart checks cover long/short positions,
losses/financing, completed runs, cost scenarios and candidate identity. Position
caps/floor sizing, gap stops, daily pause and target overshoot equity are exercised.
Older 2,095 active-suite results are retained, not rerun.

The first 33-test run had one test-setup error: native111's encoding helper returns
a list of files, not file bytes. The initial source/output is preserved. Corrected
the helper usage and expanded short/adverse/loss restart coverage. The final run
above has no exclusions. No trading-engine repair or strategy tuning was needed.

All three 576-hour invented fixtures and their manifests were frozen before the
first demonstration report. Each has four observations/hour, two mirrored blocks,
development starting at hour201 and validation at288. Reported all48 predefined
case/candidate/cost/partition combinations: 12 positive, 12 negative, 24 zero.
CLI summaries agree with stored reports. Every trade reconciles reference gross
minus spread/slippage/commission/financing with net; no double subtraction.

Below are hypothetical USD net results, with closed-trade counts in parentheses.
Each cell starts an independent $10,000 account. Do not sum cells as a portfolio
return. These are constructed software fixtures, not observed market profits.

| Invented path | Candidate | Base development | Base validation | Adverse development | Adverse validation |
| --- | --- | ---: | ---: | ---: | ---: |
| Continuation | C00 | +41.64 (1) | +16.50 (2) | +37.95 (1) | +11.46 (2) |
| Continuation | C05 | +117.86 (4) | +94.82 (5) | +102.70 (4) | +79.31 (5) |
| Continuation | C06 | +32.42 (2) | +33.95 (2) | +24.87 (2) | +27.17 (2) |
| Continuation | CASH | 0 (0) | 0 (0) | 0 (0) | 0 (0) |
| Reversal | C00 | -94.98 (2) | -57.19 (3) | -92.51 (2) | -60.85 (3) |
| Reversal | C05 | -317.66 (2) | -279.87 (3) | -302.76 (2) | -271.10 (3) |
| Reversal | C06 | -224.57 (1) | -224.57 (1) | -213.12 (1) | -213.12 (1) |
| Reversal | CASH | 0 (0) | 0 (0) | 0 (0) | 0 (0) |
| Flat | C00 | 0 (0) | 0 (0) | 0 (0) | 0 (0) |
| Flat | C05 | 0 (0) | 0 (0) | 0 (0) | 0 (0) |
| Flat | C06 | 0 (0) | 0 (0) | 0 (0) | 0 (0) |
| Flat | CASH | 0 (0) | 0 (0) | 0 (0) | 0 (0) |

All three strategies lose on the constructed reversal. Some adverse-cost losses
are smaller because cost-aware position sizing floors to a smaller lot quantity;
that is not a benefit from higher costs. Gap losses exceed the estimated entry
risk budget, and the daily entry-pause latch cannot prevent a gap already held.
Stops are not guaranteed maximum losses. CASH assumes no interest or carrying fee.
Costs/daily calendar and limit fills remain hypothetical, not broker measurements.

No market winner, combination weights, trading readiness or reliable win rate was
established. The final partial hour is marked and does not create a new signal.
Observed-hour warmup does not establish continuous or complete real tick coverage.
Full fixture schema validation may inspect future records; the strategy engine
uses preceding completed bars only. Checkpoint hashes enforce consistency, not
authentication or broker reconciliation.

Native107/109/111 performance remains unavailable. Diagnostic routes are tested
with invented capture encodings; predecessor native files and their62 hashes stay
unchanged. No guessed clock offsets, raw native return calculation, acquisition,
SDK, MT5 launch/settings/log/account inspection, support contact or orders.
Native source/receipt UTC, quote age, costs and market qualification remain unresolved.
The user's private-demo/no-contact scope persists. Market/paper/order/real-money
availability flags remain false. No user MT5 launch is needed for this phase.

Evidence: `reports/strategy-adapter-114-reservation.json`, two development source
archives and test outputs, `strategy-adapter-114-frozen-demonstration.json`,
`strategy-adapter-114-demonstration.json`, and final source/completion review.
The nine invented files are under `data/strategy-adapter-114-invented-demo/`.
Reports/data are ignored local artifacts; canonical new implementation and docs
are in the repository. Prior prepared114 plan remains historical to completion.

Usage: [STRATEGY-ADAPTER-114-USAGE.md](STRATEGY-ADAPTER-114-USAGE.md).
Next prepared step: [STRATEGY-COMBINATION-115-PLAN.md](STRATEGY-COMBINATION-115-PLAN.md).
