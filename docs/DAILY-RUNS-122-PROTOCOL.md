# Daily runs122 — frozen invented chronological controls

Implement an offline coordinator/reporter around unchanged118/119/120/121.
Preserve all earlier sources/outcomes and fixed117 strategies/costs. This is
invented software verification, not market holdout research, source qualification,
forward paper testing or an order API. No optimization, support/provider contact,
acquisition, historical/reserved data, SDK, MT5/settings/accounts/log operation,
paid service, broker account or real-money toggle. All117 market cells stay unassigned.

Strict JSON `FXDL_DAILYRUNS122_V1` contains invented clock/symbol/case, one121 stream
with execution_start_msc=null, and exactly two partitions named development and
later_validation in that order. Each declares start_msc,end_msc,endpoint_source_msc.
Bounds are half-open, positive-length, disjoint and inside the declared calendar.
The planned endpoint lies within its partition. Later means chronological, not
certified unseen data. No input flag can claim qualification or untouched validation.
Retain121 strict types, clock/calendar/quote limits, synthetic integer DEMO mode0
and no external marks/positions/identifiers. Fresh capital is fixed at USD10,000.

Freeze all inputs, partition/endpoint bounds, component/rule/profile/source/test
hashes and independent reviewers before outputs. For each partition derive only
the message prefix with receipt < end, trimming the predeclared calendar through
the day containing end-1. Include prior observations for warmup, with no funded
execution before start. Set that derived121 stream's execution start/account
availability to the partition start. No future messages, timer at the cutoff or
assumed closing price are injected. Valid future continuation cannot change an
earlier partition's derived prefix, economic state or descriptive statistics;
full-run manifest hashes still bind the entire input, including future structure.

Run121 aggregation on that prefix. Retain original quotes with source >= start;
their receipts are already < end. The last quote must exactly match the declared
endpoint, be new-source, age0..2000ms and on a declared trading day. This common
endpoint preflight applies to all candidates, including cash; it is stricter than
120's flat-account allowance. A missing/late/stale/repeated/closed endpoint makes
all eight partition comparisons unavailable, without fallback to an earlier quote.
Wide executable endpoints remain allowed for exits. Missing required completed
history/feature availability also makes the partition unavailable, never zero return.

Write derived121 input/freeze before aggregation and derived120 input/freeze before
ledger outputs. Each partition/candidate/profile starts with new flat cash; no
equity, held position, reservation, consumed opportunity, pause or funded history
is transferred. Later warmup may include development prices, never profits.
Keep120's sizing, fees/spreads/slippage, financing, original held levels, daily
pause, one-position/opportunity rules and liquidation on the actual final quote.
No financing or execution is advanced beyond that quote. Stops and pauses are
estimates/controls, not guaranteed maximum losses.

Reports are per account, with no funded portfolio total or ranking. Reconcile
cash change = gross fills - commissions + financing = sum closed trade net.
Describe trades/wins/losses/breakeven, mean net expectancy, payoff/profit factor
when their denominators exist, largest loss, loss beyond entry estimate and019B
drawdown. No-trade expectancy/ratios are null, not manufactured successes.
Report EUR units and USD notional turnover from both sides of actual modeled fills.
Holding exposure is elapsed source time between entry and observed exit, including
gaps/weekends, divided by declared partition duration; flat intervals complement it.
No prices are interpolated to calculate that time. Retain observed quote-gap details.

Price-adjustment memos describe modeled entry half-spread/slippage and stop/boundary
exit half-spread/slippage in USD. Targets fill original limits, so no separately
observable target exit-spread decomposition is claimed. Memos are embedded in
fill prices and must not be debited again or presented as a cost-free P&L estimate.
Commissions/financing are actual modeled ledger debits, summarized separately.

Enumerate every touched UTC month and quarter. Cash-flow buckets book each ledger
record at its triggering source quote (retain rollover timestamps separately).
Use the last executable observed equity mark per bucket, with actual boundary
liquidation included in the final mark. Opening anchor is initial cash for the
first bucket, or the previous bucket's observed closing mark; an unobservable
intervening bucket breaks that anchor. Empty buckets/unknown or nonpositive anchors
have null observed returns. Label partial calendar periods and observation windows;
do not claim the last sparse quote certifies a calendar-close return. Cash-flow
totals reconcile even when equity marks are unavailable. Never attribute all of a
multi-month trade's net P&L to its exit month as a monthly equity return.

Always report market assessment unavailable for invented/unqualified inputs and
untouched_validation_confirmed=false. Retain117's24-calendar-month duration,
50-active-candidate closed-trade and24 monthly-mark requirements as descriptive
insufficiency checks, without lowering them. These short toy windows cannot pass
market validation. Profit positivity is not an execution or selection gate here.

Output roots are new and bound to input/manifest. Partition attempts are exclusive
directories with ownership markers. A failed/uncommitted attempt is preserved and
not counted; resume can recompute that offline partition in a new numbered attempt.
No file deletion/overwrite, external order or capital transfer occurs. A completed
partition advances the controller once. Repeated completed run is idempotent.
Checkpoints bind completed partition records/file hashes. Restore verifies/rebuilds
only those completed prefixes, re-derives inputs/bars/fills/statistics and compares
full state; no later partition is computed. Reject altered statistics, hashes,
cursor, partition bounds, or artifacts even with a recomputed checkpoint checksum.
Checksums are local consistency checks, not source authentication.

Predeclare six invented demonstration cases: targets,weekend_gap,no_signal,
missing_history,missing_endpoint,stale_endpoint. Each has16 planned toy account
comparisons; preserve all unavailable cells. Additional unit tests cover repeated/
closed/late endpoints, restart after interruption, monthly/quarterly boundaries,
missing marks, causal late publication and isolation of later funded state.
Independent review reconstructs aggregation, fill accounting and descriptive
statistics from the quote/ledger evidence. No strategy parameters change from results.
