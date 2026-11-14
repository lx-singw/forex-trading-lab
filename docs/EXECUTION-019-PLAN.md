# Synthetic execution interaction audit 019

Declared 2026-10-06 before running the new paths. Research/demo only. No market
data, broker calls, MT5 launch, strategy selection, return optimization or orders.
Preserve the frozen baseline, tick simulator, research engine and C00–C04 rules.

Static review finds existing tests for individual stops, slippage, quote sides,
rollover, fees, single positions, daily pauses and restarts. Add interaction
coverage rather than repeat those unit cases. Freeze synthetic January 2024
quotes, annotated events and independently calculated expectations before the
production engines consume any new path.

Audit both TickSimulator and ResearchTickSimulator with injected fixed decisions
to isolate execution: long/short stop gaps after Wednesday rollover; long/short
target overshoots; ask-only spread widening; carry costs triggering a pause;
skipped weekday/weekend rollovers with restart/duplicate replay; entry costs
triggering a pause while exits remain active; large losses, price recovery,
blocked same-day reentry and smaller next-day sizing. Also exercise the actual
C04 selector on two fixed 201-hour synthetic histories (long/short trend),
without injecting its decisions. One position and one common budget per account.
This does not combine candidate account balances or tune a strategy.

Use a separate Decimal reference ledger. Event annotations specify opening,
stop/target/end fills and rollover charge units, without calling production
pricing/sizing/loss helpers. Reconstruct lot rounding, entry/exit fees, adverse
fills, swap, marked equity, daily reference and pause after every tick and final
liquidation. Compare all positions, trades and money within 1e-8 (prices/lots
1e-12). Compare peak equity and tick drawdown with the executable post-fill
equity path. Static review identifies a potential transient-mark issue: a
target overshoot is marked at the full quote before filling at the limit. Test
whether that credits a peak that the target execution cannot realize. Preserve
any difference as a failure; do not silently relabel the metric.
Record expected stop budgets and actual gap losses; a stop or daily pause
is not a guaranteed maximum loss. Treat all money here as diagnostic arithmetic,
never historical strategy profit.

For every case, replay uninterrupted and after restoration at every input
boundary; replay the latest tick as a no-op and compare the complete checkpoint
after finalization. Stop must remain active while paused; restoration must not
duplicate fills, fees or swap. Publish every case including failures; no subset
selection. New tests must reject changed directions, costs, volumes, pauses and
input/order inventories. Freeze test/reference code, inputs, original engines,
plan and previous evidence bindings in an exclusive ledger/source ZIP. Checker
reconstructs expectations from frozen annotations and binds the report.

If behavior differs, preserve the failed run and document the defect before a
separate repair plan; do not rewrite the frozen original engine or expected
events to make the audit pass. Software passes cannot approve market data,
historical costs, actual MT5 APIs or execution readiness. Both readiness flags
remain false; prior failed market gates stay unchanged. Consumed 2025 and
reserved November–December 2026 are untouched.
