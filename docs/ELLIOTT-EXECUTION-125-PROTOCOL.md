# Elliott standalone execution125 — frozen invented contract

Connect unchanged EWPB_D124 to a distinct offline ledger and pipeline. Keep117–124
sources, thresholds, candidate definitions and outcomes unchanged. No mixture or
parameter search. All prices/clocks/calendars are invented; no actual broker,
account lookup, order API, source acquisition/contact, historical/reserved replay,
SDK, MT5/settings/accounts/log operation, paid service, account creation or live
toggle. All old16 and additional four market cells remain unassigned/unrun.

Strict wrapper `FXDL_EWEXEC125_V1` is kind `invented_elliott_execution`, invented UTC,
EURUSD, case, one121 stream with execution_start_msc=null and exactly122's two
chronological partitions: development/later_validation, half-open disjoint bounds
and declared endpoint source times. Retain all121/122 quote, chronology, size,
account and schema guards, including invented2000–2003 bounds, strict integer
synthetic DEMO mode0 and fixed fresh USD10,000. No supplied bars, pivots, signals,
positions/equity or credentials/identifiers. This is not an actual account check.

For each partition, retain only messages with receipt<end and calendar through
the day containing end−1; derive121 account availability/execution start=start.
Freeze derived input before aggregation. Keep same sparse invented coverage/grace
policy and publication timing. Missing required completed history makes all four
partition accounts unavailable, with null metrics. Do not invent closures/prices.
The last execution quote must exactly equal the declared endpoint, be new-source,
fresh age<=2000ms and on a trading session; no earlier-quote fallback, including cash.

Freeze the complete derived124 bundle before wave outputs. Use its full completed
bar history and exact unchanged detector. Associate each execution quote with
the latest completed bar available by its receipt and only that bar's breakout
observation. An older observation expires when a newer completed bar publishes.
Bind original bid/ask, source/receipt, message identity, feature/session identity
and signal lineage. Serialized future bars/signals are not applied to an earlier
event. A later valid continuation cannot alter earlier features/economic state.

Entry eligibility requires source strictly after feature availability, new source,
age<=2000ms, trading session, effective spread<=1.5pip and latest observed feature.
Bad-quality/early quotes do not consume an opportunity. First eligible quote per
completed feature session consumes it even if held, paused, inactive, insolvent,
invalid geometry or below minimum risk/margin volume. A position held on arrival
prevents same-quote reentry even when that quote exits it. Keep one position and
one reservation, original held size/levels and no loss-recovery sizing. Compare
EWPB_D124 and CASH in separate fresh accounts for each profile/partition.

Base/adverse profiles remain119/120's hypothetical values: fees$7/$10 per lot round
turn, slippage0.2/0.5pip per entry/stop/boundary fill, adverse1.2pip spread floor,
100,000 units,30:1 leverage,0.01 min/step,1 max lot,0.25% maximum risk and1% UTC-day
entry pause. Entry=effective ask+slip long, bid−slip short. Stop is the observed124
prospective invalidation, unchanged by entry cost. Distance=side*(entry−stop)>0;
it must exceed spread+entry slip. Entry/stop/2R target must remain positive.
Target=entry+side*2*distance, not a level inferred from a future wave.

At precision50 over validated JSON number spellings, budget=positive executable
equity*.0025. Estimated stop debit per lot=(distance+exit slip)*100000+round-turn fee.
Floor to0.01 the minimum of budget/stopDebit, freeMargin/(entry*100000/30+halfFee)
and1. Abstain below minimum; never round up. Recheck risk/margin inequalities.
Immediate hypothetical liquidation debit per lot=(effective spread+2slips)*100000
+round-turn fee; reject if equity−that debit<=99% of day anchor. Do not separately
subtract embedded spread/slip from gross P&L. Financing and gaps can exceed entry
estimates; stops/pauses are not guaranteed loss caps. Worse entry costs also move
an entry-dependent2R target; do not assume every constructed adverse target payoff
must be lower. Lot-floor changes also prevent a general monotonic P&L claim.

Reuse unchanged120's record/financing/exit/mark/finish primitives, with a separate
125 entry admission/sizer/ledger schema. Independently verify them in this adapter.
Each entry records atomic invented reserve/accept/fill; release follows accounted
exit. Long uses bid, short effective ask. Stops fill first observed breached side
quote with adverse slip; targets fill original limits without favorable overshoot.
No fill/mark on stale/repeated/closure quotes; financing still walks all elapsed
UTC rollovers (prior Wednesday triple, weekends zero). Use actual modeled breach
fill/fee for equity, raw side marks otherwise, original-entry margin and latched
daily pause. No guessed margin-call fill or interpolation. Boundary liquidation
uses only the final executable quote and includes costs; no accrual beyond it.

Derived compiled input/manifest binds quote/bar/wave artifacts, exact source,
rules/profiles, session/feature identities and fresh account before ledgers. The
public CLI accepts only raw-stream wrappers; supplied compiled signals are not
public input. Account checkpoints bind compiled input/manifest/profile/candidate,
cursor, finished flag and complete state. Restore replays only completed quote
prefixes, then finishes only if the checkpoint says so. Reject rehashed cash,
held protection, consumed opportunities, finance, reservation or identity edits.
Hashes are local consistency, not signed authenticity or broker reconciliation.

New output roots/partition artifacts are exclusive. Preserve failed/unavailable
results. Low-level account restore is checked; the batch CLI does not resume a
partially written root and never overwrites one. Frozen sources/inputs/reviewers
precede demonstrations. Independent rational review must check aggregation,
detector timing, structural-stop sizing, each fill/debit/mark and cash reconciliation.
Tests cover both sides, risk/min/max/margin/headroom, gaps and nonpositive slipped
exits, financing/pauses, first opportunities, held levels/release, delayed/missing
quotes, duplicates, causal prefixes and forged restart state.

Report all case/profile/partition/candidate accounts, no-trade/held/rejected outcomes,
gross/net/fees/financing/drawdown and losses above entry estimates. No ranking or
capital summing. Short invented windows are insufficient for qualified24-month
development/24-month actually untouched validation. Sample counts are not wins,
market probabilities or economic edge. All market/paper/order/real-money availability
remains false; only hypothetical offline accounting becomes available.
