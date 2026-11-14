# Daily strategy118 — prepared pure feature prototype

After117 closes, implement its declarative T12_D/MR20_D/MIX50_D/CASH decisions as
pure offline functions over completed daily-session bars. Read
[the117 review](STRATEGY-EVIDENCE-117-REVIEW.md),
[protocol](STRATEGY-EVIDENCE-117-PROTOCOL.md) and
[candidate ledger](../config/research-candidates-117.json) first. Preserve existing
hourly strategies,113–116 engines, their costs and frozen sources.

Implement a distinct validated DailyBar representation and explicit decision
availability/lineage. The prototype accepts invented, explicitly labelled
completed-session fixtures only. It cannot admit historical or native market data
by trusting a boolean qualification flag. No quote aggregation, broker/calendar
inference, return simulation, equity curve, risk sizing execution or order API in118.

Use fixed252-session price trend, exact20-session population-SD reentry,14-session
true-range stop distance and the fixed50/50 signal/risk calculation. Decisions
must expose component sides, score, stop distance, risk multiplier and reason.
Represent abstention directly; do not construct a Config with zero risk. Cash is
always inactive. All active rules share253-session warmup.

Meaningful tests must independently calculate trend/reentry/ATR, exercise exact
threshold boundaries and zero variance/range, all nine component-side pairs,
positive/negative/flat histories and half/full/cancelled risk. Prove invariance
to future price changes, rejection of open/unavailable sessions, strict chronology,
missing required trading sessions, OHLC/nonfinite/type/lineage violations and
market/native labels. Distinguish a qualified invented calendar closure from a
missing invented trading session without synthesizing prices. Bind rule/schema
hashes to fixture demonstrations; preserve every rejected case. No tuning from
invented decisions, no returns and no claim of market qualification.

Position sizing, spread/entry opportunities, fills, financing, loss pauses,
duplicate execution and restart are deferred to a separately frozen adapter step
with independent meaningful risk tests. Retained hourly tests do not automatically
validate a new daily adapter.118 may run necessary feature tests, not unrelated
full-suite repeats after passing without a material change.

No provider contact/retries, historical/reserved data consumption, native clock
promotion, SDK, MT5 launch/settings/accounts/log inspection, manual user launch,
paid service, account creation or orders. Market/paper/order/real-money admission
stays unavailable. This is a prepared next step, not implemented in117.
