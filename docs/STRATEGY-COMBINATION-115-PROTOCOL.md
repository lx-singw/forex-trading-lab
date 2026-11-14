# Strategy combination115 — implementation contract

Offline invented quotes only; no connection, execution API, live mode, acquisition,
MT5/settings/account/log inspection, support contact or orders. Preserve all532
predecessor source/config/test files and earlier evidence. Native107/109/111 remain
diagnostic with performance unavailable. No historical or reserved market returns.

Freeze members C00/C05/C06 in this order, using unchanged028 decisions on preceding
completed bars. All rules require common201 completed observed hours and the
partition's evaluation boundary. Reuse114's strict invented fixture grammar and
immediate missing-hour entry suppression; no imputed bars/quotes or clock offsets.

Rules, in fixed order:

- UNANIMOUS: all three nonzero votes must have the same side.
- AGREE2: at least two nonzero votes must have the same side, and no vote may oppose.
- CASH: always abstain, no interest or trading costs.

Opposing nonzero votes cause abstention even when two agree. Insufficient votes
cause abstention. Validate exact members, integer sides -1/0/+1, finite nonnegative
stop distances (strictly positive for nonzero votes), string reasons and dictionary
features; malformed votes reject. No weights, optimization, winner selection or
recovery stakes. Admission uses the largest positive stop distance among supporting
votes. Apply the inherited risk budget once to that single position, never sum
member positions/capital/risk. Decision traces retain every member's side, distance,
reason/features, supporters and arbitration reason.

One independent $10,000 single-position account per rule/cost/partition, including
CASH. Do not aggregate their balances as a portfolio. Development ends before
validation, using its last quote for liquidation. Validation has fresh capital,
no carried positions and prior prices only for warmup. Last observed hour is partial.

Reuse114/113 fill lineage, costs, floor sizing, position/margin/spread limits,
daily entry-pause latch, gap stops/financing and corrected019B target-fill equity.
Cost scenarios are unchanged113 base/adverse assumptions, not feed measurements.
Stops and the daily pause cannot guarantee maximum loss through gaps. Votes cannot
remove or change an existing position's stop/target; inherited exits still run.
Record entry attempts, estimated entry risk/budget and the admitted entry votes
alongside actual costs/trades/lineage. Estimated risk is not a guaranteed loss cap.

Five predefined 576-hour invented cases: reuse114 continuation/reversal/flat prices
unchanged; add partial_agreement and conflicting_votes in a separately versioned
115 generator using the same114 data format. Each has two mirrored288-hour blocks,
four quotes/hour, development at201 and validation at288. Partial-agreement prices
are 1.25 through offset150, 1.125 at151..199, 1.1875 at200, 1.2 at201..223,
1.23 at224..226 and1.16 afterward, mirrored about block base1.1/1.102.
Conflict prices are1.1 through149,1.0 at150,1.103 at151..179,1.1 at180..199,
1.1001 at200,1.104 at201..223,1.108 at224..226 and1.096 afterward, mirrored
the same way. Keep114 quote times/spread/wiggles and invented50ms source lag.
These paths construct known vote cases, not market samples or performance claims.

Freeze all five fixture bytes/manifests, rule/member definitions, source/test/
protocol/config hashes, common warmup and cost scenarios before demonstrations.
Report every60 predefined case/rule/cost/partition outcome, including no trades,
cash and losses. No selected strategy or combination weights. Never claim mocks
prove a stronger engine or use them to unlock market evaluation or orders.

Checkpoints bind the rule plus all members/source/config/fixture/manifest/scenario/
partition. Cross-rule and legacy restore reject. Check latest cursor/quote/repeats,
corrected metric version, entry/cost/fill/position state and stored vote semantics.
Restart and latest-duplicate replay equal uninterrupted behavior. Hashes are
consistency checks, not authentication or broker reconciliation.

Focused tests cover the27 vote-side combinations, invalid inputs, maximum supporting
stop, independent reference arbitration on actual fixed decisions, causal suffixes,
partial/conflicting votes, warmup/gaps/cash, position/risk/spread limits, gap loss,
daily pause, target overshoot, costs/financing and long/short/rule-bound restarts.
Retain earlier results and preserve any development failures. No user launch needed.
