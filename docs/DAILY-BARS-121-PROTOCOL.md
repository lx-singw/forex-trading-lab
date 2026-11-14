# Daily bars121 — frozen invented causal aggregation

Build an offline quote-to-bar adapter and coherent integration of unchanged118
features and120 accounting. Preserve117/118/119/120 sources. This is invented
software verification only. No qualified market inputs, strategy tuning, source
acquisition, provider/support contact, historical/reserved data, SDK, MT5/settings/
accounts/log operation, paid service, broker account, actual orders or live toggle.
117's16 market cells remain unassigned. No win-rate or income claim.

Strict JSON `FXDL_DAILYBARS121_V1` contains invented clock/symbol/case, a predeclared
118 calendar, an initial invented flat USD DEMO cash record, an execution_start_msc
(or null for aggregation only), and sequential messages. No supplied bars, features,
held positions, equity/free-margin marks, identifiers or credentials. Synthetic
trade_mode must be integer0; this is not an actual broker-account lookup. Retain
118's2000–2003 interval,800-session/8MiB limits and120's price/cash bounds. At most
5000 messages. Unknown fields, boolean/nonfinite numbers and duplicate JSON reject.

Quote messages contain sequence,kind=quote,source_msc,receipt_msc,bid,ask. Advance
messages contain sequence,kind=advance,receipt_msc and represent explicit invented
clock observations, not prices. Receipts never decrease; quote sources never
decrease. Receipt cannot precede source. Same-source prices must agree exactly.
Quotes belong to half-open UTC sessions [start,end); a boundary quote belongs to
the following day. All source/receipt times must lie inside the declared calendar.
An advance cannot manufacture a quote, extend calendar coverage or interpolate.

Before applying each message, finalize sessions whose end+2000ms <= current
receipt time. Availability is this actually observed finalizer receipt, never
backdated to the scheduled deadline. A fresh last quote before end can arrive up
to end+1999ms and contribute before finalization. A later old-session quote cannot
revise a finalized bar. Reject backward source arrivals structurally; record
otherwise well-formed late/finalized, stale, repeated and closure quotes as excluded
observations. New source, age0..2000ms inclusive and trading status qualify a quote
for aggregation. There is no aggregation spread cap; observed wide quotes remain
part of midpoint history while unchanged120 applies its entry cap.

The frozen invented coverage policy requires at least4 distinct qualifying source
quotes, first source no later than start+60000ms, last source no earlier than
end-60000ms, and no successive qualifying-source gap greater than12 hours inclusive.
These sparse toy thresholds do not certify tick completeness, a feed or broker
hours. Every qualifying quote contributes observed midpoint=(bid+ask)/2. OHLC is
first/max/min/last midpoint in source order; no intra-gap extrema are invented.
Calculate midpoint from exact input Decimal spelling at precision50; convert OHLC
to the float fields required by unchanged118. Retain exact midpoint strings and
individual quote digests in publication evidence for independent reconstruction.

Finalize a trading session as completed only if all coverage conditions pass;
otherwise publish an explicit incomplete disposition with coverage details and
no DailyBar. Scheduled closure finalization creates a closure disposition and no
bar. An unfinished session remains pending and cannot supply features. Completed
bars carry118's observation, availability and content lineage, plus separate121
evidence binding accepted quote sequences/digests/midpoints, observed finalizer,
calendar prefix and processed message-prefix digest. No full future-file digest
is part of an earlier bar's identity. Hashes are consistency records, not origin
authentication. Altering valid future prices/receipts cannot alter an earlier state.

For execution integration, the partition start is declared before outcomes.
Quotes with source >= that start retain their actual bid/ask/source/receipt,
including excluded aggregation quotes. Do not turn midpoint candles back into
execution prices. Assign each quote the latest completed bar actually available
by its receipt, with feature decision time equal to that bar's observed publication
time. Exact target identities remain fixed. Recompute118 decisions from those
prefixes and pass quotes to unchanged120; warmup or zero signals may abstain.
Missing any required completed trading session makes the integration unavailable,
with no return report; do not fall back across missing coverage. Future finalized
bars can exist in the serialized120 bundle but are not used before availability.

Initial account is flat fresh cash, with availability <= the first execution quote.
No warmup profits/positions are imported. T12_D,MR20_D,MIX50_D,CASH ×base/adverse
remain separate accounts; do not sum their capitals. Keep all120 sizing, costs,
financing, first-opportunity, held-level, gap, reservation and boundary rules.
A partition can end within a still-open daily session: that session supplies no
feature, and120 liquidates only on the actual final executable quote. A stale/
repeated/closed held endpoint remains unavailable. Aggregation never advances
financing past the last execution quote. Stops/pauses are not guaranteed loss caps.

Freeze an integration manifest binding input, all component/source/test/protocol
hashes, exact aggregation/feature/accounting rules and profiles before aggregation
outputs. Write derived120 input and its own freeze before ledger outputs. Output
directories/files are new only. Preserve aggregation dispositions and unavailability
reasons when integration cannot run; unavailable is not a numerical zero return.
No fixture flag or manifest field can enable market/paper/order/real-money admission.

Checkpoint restore reconstructs only messages through its observed cursor and
compares complete canonical state, including pending samples, finalized bars,
coverage evidence, excluded outcomes and prefix digests. Reject altered state even
with recomputed checksums, boolean cursors, source/rule/input substitutions and
changed finalizer times. Latest exact message replay is idempotent; older or changed
duplicates reject. Restarts cannot publish future sessions or duplicate a bar.

Predeclare eight invented paths: long_path,short_path,weekend_gap,half_risk,
no_signal,missing_coverage,stale_coverage,partial_session. The last unfinished session
is explicitly tested; missing/stale coverage produces unavailable integration.
Generate all daily OHLC from these same quotes, never import manually declared
bars into the adapter. Freeze this small matrix and independent review sources
before reports; preserve gains, losses, no-trades and invalid/unavailable cases.
Do not rank candidates or tune rules from constructed results.

Independent tests/review must reconstruct midpoint OHLC/coverage/lineage and causal
publication times from raw messages, then reuse120's separately frozen rational
fill/financing checker. Test boundaries, exact coverage/age limits, late receipts,
duplicates/conflicts, closures/missing days, partial sessions, future invariance,
held weekends, first opportunities, derived-source identity and checked restarts.
