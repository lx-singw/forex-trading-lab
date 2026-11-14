# Shadow engine113 — next offline integration

The native111 one-hour pilot is now inspected in112: 7,188 valid snapshots,
60 linked files, clean elapsed-limit stop, no pending records or receipt gaps
over two seconds. Collection and rotation worked in this run. Clock alignment,
source age, full tick delivery and executable costs remain unknown. This permits
software integration work with invented data; it does not qualify this feed for
paper performance evaluation or establish a strategy edge.

## Concrete scope

Build a read-only offline adapter and CLI around the existing simulation engine.
Reuse the frozen `config/baseline.json` and its documented SMA20/SMA50, simple
ATR14, 2ATR stop, 2R target, 0.25% risk and 1% daily entry-pause rules. Reuse existing
tick/risk/checkpoint logic where its assumptions apply; do not create another
trading engine or silently alter old parameters. No new strategy selection,
combination weights, optimization or return-based threshold changes in this step.

Start with an explicitly invented chronological quote fixture long enough to
exercise completed-hour warmup, entry, exit and cost accounting. The fixture must
have declared clock semantics and separate development/validation spans. Include
profitable and losing paths for software checks; neither is a market forecast.
Freeze fixture/config/source hashes before reporting the demonstration.

Inspect111 exports through the existing strict inspector. Preserve their raw
source/native fields and receipt boundaries; mark them as latest-quote snapshots,
never complete market ticks. A declared market kind is not producer proof.
Native107/109/111 observations with unresolved clock/age/quality prerequisites
must produce a clear unavailable result before reaching performance evaluation.
Do not guess the three-hour offset, convert per-run monotonic origins into a
shared clock, turn receipt-relative buckets into certified calendar H1 bars,
forward-fill gaps or relabel this one-hour run as sufficient warmup.

Signals must use completed bars only. New prices can influence only their own
and later decisions. Entries occur on a subsequent usable bid/ask observation,
with the existing correct long/short sides and adverse cost handling. Keep costs
explicit and independent of the unusually small observed demo spreads. Preserve
the baseline's hypothetical commission/slippage/financing assumptions and a
separately declared adverse scenario; show gross result, every cost and net result.
Do not select a strategy or cost scenario from which demonstration wins.

## Meaningful verification

- Compare incremental prefix decisions with batch replay, including a changed
  future suffix that cannot alter earlier signals/fills.
- Exercise insufficient warmup, missing hours, stale/repeated/out-of-order input,
  crossed/invalid quotes, run boundaries and partial/pending111 captures. Missing
  coverage cannot be synthesized into successful trades.
- Check long/short spread sides, gap-through-stop fills, adverse slippage, loss
  pauses, position limits and duplicate events. A stop is not a guaranteed loss cap.
- Check uninterrupted versus checkpoint/restart replay, changed configuration,
  conflicting duplicates and already-processed events. Never restore an invented
  checkpoint into a market run or claim broker reconciliation.
- Reject native unqualified exports before any simulated performance computation.
  Confirm no network/broker/order API or real-money mode exists in the new adapter.

Run focused new integration checks and relevant existing simulator/guard checks.
Report exact results and any modeling limits. Preserve all old source evidence,
configs, observed captures, failed cases and prior tests; do not rerun the whole
suite or historical return experiments without a change that requires it.

## Boundaries and later evaluation

This plan is prepared, not implemented. The next turn can build it without another
MT5 launch or support/contact request. Native acquisition remains separately
default-off and bounded; this work creates no scheduler, service or automatic run.
No orders, terminal settings, account creation, credentials or account identifiers.

Later comparisons require fixed strategies, adequate qualified development data
and untouched chronological validation. 2024 remains reused development, 2025
consumed/excluded, October2026 quarantined, and Nov–Dec2026 reserved untouched.
Do not select/tune on112. Historical provider stops and H.10/native090 closures
remain. The user's private-demo/no-contact instruction continues. No guarantee of
winning every time, a win rate or income can be made from this software work.
