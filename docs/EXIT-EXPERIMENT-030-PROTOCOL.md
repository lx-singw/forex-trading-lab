# Protective-stop replay protocol 030

Implements the unchanged EXIT-EXPERIMENT-030-PLAN.md. No market returns were
read for C07/C08 before this protocol and its implementation/tests were frozen.
The threshold is informed by reused 029 development diagnostics.

C00/C05/C06 controls retain exact 028 decisions, fills, costs and corrected
metrics. C07 maps decisions to C05; C08 to C06. All share the same 201 closed-hour
warmup, original three evaluation boundaries, initial capital and two costs.
R is the initial entry-to-stop price distance times filled volume; fees are
included in sizing and in the net trigger, not added to the definition of R.

Each tick follows inherited financing, pre-fill equity marking, eligible entry,
stop/target processing and post-fill marking. Only then may a surviving
challenger position arm once. Its bid/ask liquidation includes exit slippage,
full commission and accrued swap. At >=0.5R the stop estimates zero net with
current costs and must tighten behind the current closing quote and before
the original target. The quote which arms cannot fill the moved stop; the next
source sequence can, including one with the same timestamp. Later financing
does not update it. Gaps can lose more than original estimated risk.

Reports retain original trade fields (including final stop) and provide separate
protection_lineage with trade index, initial stop/distance/dollar R, and nullable
arm sequence/time/old stop/new stop/swap/net. Fill lineage remains source ordered.
The checkpoint requires both inherited corrected metric/028 strategy markers
and single_protective_stop_030_v1; candidate, costs and evaluation start must match.

Before returns: all previous 815 bindings, 780 archive members and 35 external
inputs must verify. Freeze the exact new modules, scripts, tests, specification,
protocol, data/reviews/configuration and original control report seals. Run
exactly ten accounts per window, one ordered pass per window; exclusive report
paths forbid overwrite or rerun. Any control mismatch is a preserved failure.

The independent checker reconstructs all cash, financing, both equity marks per
quote, hourly exposure and daily pauses from quote sequences. It starts each
trade at the separate initial stop, checks entry risk/margin bounds and each
stop/target crossing, tests every surviving quote until the first eligible arm,
and changes the level only after that quote's marks/fills. It checks all reported
arms, final levels, net/commission arithmetic, and original controls. Independent
closed-bar feature checks cover all C05–C08 decision records. Sixteen synthetic
checker cases cover both challengers, both sides, targets, original stops,
protected gap stops and end-of-sample liquidation before any market replay.

Report all 30 cells and zero CASH reference, protected exits and their losses,
net differences from parents, costs/exposure/drawdown and base/adverse sensitivity.
Entry identities are (opened timestamp, side); identify shared, new and omitted
entries. List original target winners which share an entry and instead hit a
protected stop; report omitted original targets separately. Endogenous cash and
position availability preclude causal attribution by subtracting old losses.

This stage cannot approve selection, annual eligibility or execution. The reused
windows and provisional clock/cost assumptions cannot establish unseen edge.
Consumed 2025 and reserved November–December 2026 remain excluded. No downloads,
accounts, provider messages, MT5 changes, execution toggle or automated orders.
