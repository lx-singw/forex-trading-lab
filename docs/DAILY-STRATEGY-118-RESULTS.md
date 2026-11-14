# Daily features118 — implemented pure daily decisions

Implemented four fixed117 candidates over a distinct validated DailyBar and
predeclared invented calendar: T12_D252-session price trend, MR20_D20-session
population-SD reentry, MIX50_D equal signal weights and CASH. All active rules
share253-session warmup and14-session arithmetic true range times2 for a stop
distance. No parameter changes to117; the historical declaration stays preserved.

Decisions expose component sides, raw score, stop distance, risk multiplier,
reason, causal availability and observed-prefix lineage. Scheduled invented
closures require no bar; missing trading sessions reject. Future complete bars
do not affect earlier decisions. Qualification booleans and market/native labels
cannot enable admission. There is no quote aggregation, position sizing, order
API, return simulator or account connection in this prototype.

**48 focused tests pass**, no failures/errors/skips,1.751 seconds. Tests use
independent Decimal moments/true-range calculations, actual nine-pair histories,
exact2-sigma strict/inclusive boundaries, zero variance/range, all mixture pairs,
lookback indexing, warmup, future invariance and immutable/idempotent decisions.
They check missing/closure distinctions, completion/availability, chronology,
OHLC/types/nonfinite/lineage, native/market labels, strict JSON, source/schema/rule
freeze bindings, boolean substitutions, artifact limits and CLI behavior.

The first47-test version also passed in1.748 seconds. Review added a controlled
rejection for a wrong fixture shape with a recomputed checksum and one regression
test. Both tested source versions and outputs are preserved. No executed test
failed. The prior116269 focused tests and older suite results are retained,
not rerun; they do not certify a future daily execution adapter.

All41 accepted-input/manifest/invalid-input/matrix artifacts were frozen before
feature reports. The11 accepted fixtures produce44 candidate decisions, each
matching independent feature audits;18 malformed cases reject with their exact
predeclared reasons and no invalid manifest/report. The CLI and stored report
agree. Demonstration duration0.493 seconds. There are18 active feature decisions
and26 inactive decisions; these counts are not trades, wins or profits.

| Invented case | Trend side | Reentry side | Mix side | Mix risk multiplier |
| --- | ---: | ---: | ---: | ---: |
| trend_up_reentry_long | 1 | 1 | 1 | 1 |
| trend_up_reentry_none | 1 | 0 | 1 | 0.5 |
| trend_up_reentry_short | 1 | -1 | 0 | 0 |
| trend_flat_reentry_long | 0 | 1 | 1 | 0.5 |
| trend_flat_reentry_none | 0 | 0 | 0 | 0 |
| trend_flat_reentry_short | 0 | -1 | -1 | 0.5 |
| trend_down_reentry_long | -1 | 1 | 0 | 0 |
| trend_down_reentry_none | -1 | 0 | -1 | 0.5 |
| trend_down_reentry_short | -1 | -1 | -1 | 1 |
| zero_range | 0 | 0 | 0 | 0 |
| warmup | 0 | 0 | 0 | 0 |

Cash is inactive in every case. Multipliers are feature outputs only; a future
cost-aware lot sizer must independently enforce one risk budget, minimum-volume
abstention and existing caps. A zero-ATR decision keeps its raw signal score for
diagnostics while admitting zero side/risk. Stops are not guaranteed maximum losses.

All542 predecessor source/config/test hashes remain unchanged; four new files
make546. The62 retained native evidence hashes remain unchanged. Working README,
CONTEXT, PLAN and VERIFICATION preserve the full previous body bytes below their
latest entry. Prior117 evidence and current sources/reports/fixtures are hash-bound
at closure. The source archive retains small invented inputs and reports; older
source/evidence graphs and native files are explicitly external hash bindings.

The11716 planned market-performance cells remain unassigned/unrun. Actual clock,
feed, coverage, execution cost and financing qualification remain unresolved.
No historical/reserved data use, new quote acquisition, provider/support contact,
SDK, MT5 operation, paid service, broker account or order. Market/paper/order/
real-money admission stays unavailable. Passing software tests establishes no edge.

Read [the protocol](DAILY-STRATEGY-118-PROTOCOL.md) and
[usage](DAILY-STRATEGY-118-USAGE.md). Next is
[the prepared119 invented risk-admission prototype](DAILY-RISK-119-PLAN.md),
not implemented in118.
