# Strategy combination115 — prepared next offline step

114 fixed C00/C05/C06/CASH comparisons are implemented. 203 focused tests pass.
All48 invented comparisons are reported; no strategy selected. Native market
evaluation, orders and real-money execution remain unavailable.

Next build a single-account decision-arbitration prototype, using the unchanged
fixed strategies on preceding completed bars and common201-hour warmup. Prepare
two predetermined rules: unanimous agreement (all three nonzero and same side),
and agreement by at least two with no opposing nonzero vote. Both otherwise choose
CASH. There is no weighting, optimization, winner selection or recovery sizing.
Freeze exact rule semantics, candidate/source/config/cost/fixture hashes and any
new disagreement fixtures before demonstration outputs in a new115 protocol.

For an admitted direction, use the largest positive stop distance among supporting
votes, then apply the inherited floor sizing and total single-account risk cap.
Keep one position, stops/targets, spread/margin guards, daily entry pause, gap
behavior, financing and corrected019B equity. Never add114 independent capital
or trades to create a portfolio. CASH decisions cannot alter an existing position's
exit protection. Record vote/reason/arbitration traces for review.

Test conflicts, all-zero/one-vote agreement, abstention, long/short entries, strictly
causal decisions, fresh-capital partitions, costs, corrected equity, gap loss and
restart. Bind checkpoints to the combination rule and all member definitions;
cross-rule restore rejects. Compare with independent predetermined rule calculations
and retained114 behavior. Report every invented outcome including losses and no
trades; mocks cannot establish that a combination is stronger or select weights.

No network, historical return reruns, reserved periods, source acquisition, MT5
launch, settings, accounts, support contact or orders. Private-demo/no-contact
scope persists. A later market-performance decision requires suitable market
evidence; synthetic success cannot unlock execution. This plan is prepared,
unimplemented and needs no manual MT5 launch.
