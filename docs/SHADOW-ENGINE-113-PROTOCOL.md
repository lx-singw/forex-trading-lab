# Shadow engine113 — implementation contract

Offline invented fixtures only. No acquisition, broker API, orders, real-money
mode, terminal settings or support contact. Existing baseline/model/simulator and
107/109/111 sources stay unchanged. Native capture inspection always returns
performance unavailable; declaring an invented kind in a capture cannot unlock it.

The new fixture format explicitly declares invented UTC millisecond receipt/source
clocks, EURUSD and chronological development/validation boundaries. At most 8MiB,
20,000 events. Strict fields and numeric types; sequences begin at 0 and are
consecutive. Receipt/source times cannot reverse, source cannot exceed receipt,
and invented quote age cannot exceed 2,000ms. Same-source-time changes reject;
unchanged latest quotes are retained with new receipt/sequence values. A duplicate
of the latest identical event is idempotent; missing/conflicting/older events reject.

Freeze fixture bytes, code dependencies, baseline JSON and exact scenario settings
before demonstration results. New files are created exclusively, never overwrite
old artifacts. Dataset labels/hashes are consistency declarations, not authenticity.
Fixture/schema validation can inspect a future suffix, but decisions cannot use it.

Reuse Config/TickSimulator with frozen SMA20/50 and ATR14 rules, through the
existing corrected ExecutableEquityTickSimulator019B equity mark. A target
overshoot cannot inflate peak equity beyond the actual modeled limit fill.
Checkpoints require the corrected metric version. Base costs are the
baseline's hypothetical $7 round trip/lot, 0.2pip adverse market slippage, swaps
-$3 long/-$1.50 short per lot/day. Adverse settings are fixed before results:
$10 commission, 0.5pip slippage, swaps-$4.50/-$2.25 and a 1.2pip minimum quote spread.
Other baseline settings are identical. These costs are assumptions, not demo feed
measurements. Preserve margin, floor sizing, one-position and daily-pause behavior.

Each partition starts with $10,000 and no position. Prior observations may warm up
completed-hour indicators with trading disabled until that partition starts.
Development cannot consume validation quotes for exits; close at its last observed
quote. Validation warms up on earlier prices without carrying development capital
or positions. The final partial hour is marked; finish does not create a signal.
The invented fixture contains two 96-hour blocks, mirrored long/short paths:
51 gradual hours, a fixed jump and continuation or reversal. Both predefined cases
are reported, never choose the one that wins. This is software testing, not strategy
selection or untouched market validation.

Audit actual trades by reconciling reference gross minus spread, slippage,
commission and financing with simulator net P&L. Entry reference is midpoint;
market/stop exit reference is contemporaneous midpoint. Modeled target-limit exit
reference equals its exact target fill, with zero extra exit price friction. This
is an accounting decomposition of actual simulated fills, not a frictionless
counterfactual or a claim about real target fills. Do not subtract costs twice.

Checkpoint bindings include fixture/manifest, source/config/scenario and partition.
Restore validates checksum, bindings, event cursor and simulator's latest tick;
restored replay must equal uninterrupted replay. Checksums are not malicious-tamper
proof and checkpoint restoration is not broker reconciliation. No invented state
can be restored into a native capture evaluation.

Focused checks cover causal prefixes/future suffix changes, warmup/missing hours,
quote validity/age/order/repeats, both spread sides, stops through gaps, costs,
daily pause, position/duplicate limits, changed configuration and restart. Retain
old checks/results. No historical or reserved-period returns are rerun in113.
