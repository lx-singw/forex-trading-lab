# Strategy adapter114 — frozen implementation contract

Offline invented quotes only. Preserve all 528 predecessor source/config/test
files and the original 113 fixtures. No network, MT5 launch, broker API, acquisition,
settings, accounts, support contact or orders. Native 107/109/111 captures remain
diagnostic and cannot enter performance evaluation. No market period is rerun.

Compare C00, C05, C06 and CASH, in that fixed order. Reuse unchanged
`strategy_experiment_028.decision`: C00 SMA20/50; C05 the existing trend-mode
channel breakout; C06 the existing breakout with SMA50/200 direction agreement.
CASH always abstains, earns no interest and incurs no trading costs. There is no
candidate selection or portfolio/combination in this phase. Each candidate/cost/
partition starts an independent $10,000 single-position account. Never add those
balances together as portfolio capital.

Require 201 completed observed hours before an eligible decision, for every
candidate including C00 and CASH. Use only preceding completed bars. Preserve
the inherited immediate missing-hour entry guard; no imputed bars or quotes.
Development receives no validation quotes even for exits, and is liquidated at its
last observed quote. Validation starts fresh capital/positions and uses earlier
prices solely for indicator warmup. The final observed hour is partial.

Reuse 113 cost instrumentation and corrected019B fill-equity simulator, with the
original floor position sizing, margin/spread limits, one position, gap fills,
financing and daily entry-pause latch. Stops do not guarantee maximum loss.
Base/adverse settings are exactly 113's frozen assumptions: base $7 round trip
per lot, 0.2pip adverse market slippage, swaps -$3/-$1.50; adverse $10, 0.5pip,
swaps -$4.50/-$2.25 and minimum 1.2pip spread. Other baseline parameters unchanged.
Costs reconcile with actual simulated net; do not subtract them twice.

The new FXDL_STRATEGY114_V1 fixture retains strict invented UTC receipt/source
milliseconds, exact fields and 113's limits (8MiB, 20,000 events, consecutive
sequences, no clock reversal, noncrossed positive finite quotes, maximum invented
age 2,000ms). Both partition boundaries must have at least 201 observed prior hours.
This is a declared synthetic-clock test, not source or UTC certification.

Predefine continuation, reversal and flat, each with 576 hours in two mirrored
288-hour blocks and four observations/hour. Development starts at hour201;
validation starts at hour288. For nonflat paths each block declines gradually
through offset200, jumps at201, changes at204, jumps at224 and changes at227.
Continuation extends the move; reversal falls back. The flat path has no movement.
Exact prices/times are fixed in the new versioned generator. Report all 48
candidate/cost/partition/case checks, including abstention and losses. These
constructed paths can test implementation, never establish edge, weights or winners.

Freeze all three fixture bytes and manifests before any demonstration results.
Manifests bind all candidates, common warmup, starting capital, baseline, costs,
fixture/source hashes and this protocol. Create artifacts exclusively. A future
suffix may be validated as input but is invisible to earlier strategy decisions.

Checkpoint bindings include candidate, manifest/fixture, code/config, scenario and
partition. Cross-candidate restore rejects. Validate corrected metric version,
cursor/latest quote, repeat counts, evaluation boundary, cost/fill lineage and
position/audit state. Restart and latest duplicate replay must equal uninterrupted
results. Checksums are consistency checks, not authentication or broker reconciliation.

Focused tests compare decisions, fills and metrics with the unchanged 028 engine;
cover causal suffix changes, common warmup, abstention, gaps, quote grammar,
cost reconciliation, target overshoot equity, risk/position limits, gap losses,
daily pause and candidate-bound restarts. Retain predecessor test results and
archive development failures if any. Market/paper/order/real-money availability
flags remain false. No MT5 user launch is required.
