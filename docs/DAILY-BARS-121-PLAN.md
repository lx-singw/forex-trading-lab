# Daily bars121 — prepared causal invented quote aggregation

After120 closes, connect the missing upstream piece: an offline invented bid/ask
to118 DailyBar adapter. Read117/118/119/120 contracts and results first. Preserve
all prior source and outcomes. This is a software integration step, not market
qualification, strategy tuning or an execution API.

Freeze exact invented session, coverage, freshness and bar availability rules
before outputs. Use side-valid observed quotes and midpoint OHLC; never derive
bid/ask costs from midpoint candles. Make a bar available only after session
completion and receipt of all required qualifying observations under that frozen
fixture policy. Declare scheduled closures in advance. Missing trading coverage,
late/conflicting/duplicate/out-of-order quotes and unfinished sessions need explicit
tests and unavailable outcomes; do not forward-fill or guess venue hours/offsets.
Do not claim an invented coverage threshold qualifies a broker source.

Create coherent invented histories whose daily bars actually come from the bound
quote prefix, then drive unchanged118 features and120 accounting through a small
predeclared chronological pipeline. Test future-price/receipt changes, boundary
quotes, held weekend gaps, first daily opportunities, duplicate/restart recovery
and partial sessions. Check bar lineage/OHLC independently and reuse120's independent
ledger reconciliation. Freeze a separate integration manifest binding all stages;
do not weaken risk/cost rules to produce profits or rank toy strategy outcomes.

Keep117's16 market cells unassigned. Actual source UTC, receipt age, venue calendar,
coverage, contract costs and financing remain prerequisites to a later distinct
market evaluation. Native107/109/111 remain inspect-only and are not inputs here.
No historical/reserved reads, quote acquisition, provider/support contact, SDK,
MT5/settings/accounts/logs, user launch, paid service, broker account or orders.
No real-money toggle. This step is prepared only in120.
