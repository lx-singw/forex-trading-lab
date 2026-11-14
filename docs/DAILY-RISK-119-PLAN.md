# Daily risk119 — prepared invented admission and sizing prototype

After118 closes, implement a separate offline adapter from its immutable daily
features to cost-aware entry proposals on invented bid/ask quotes and invented
account/position state. Read117's fixed declaration/protocol and118's results,
protocol and usage. Preserve existing118 features and hourly113–116 sources.
This step is admission/sizing only: no fills, trade returns, equity curve,
broker/native data, quote aggregation or order-placement API.

Freeze the exact admission contract and fixtures before outputs. Use inherited113
hypothetical base/adverse fees, slippage, spreads, contract/volume/margin and risk
defaults; these are not discovered broker terms. At an active signal, multiply
the0.25% cap by118's fixed multiplier. Opposing, cash, warmup and zero-ATR outputs
abstain directly without constructing Config with zero risk. Floor volume and
abstain below the minimum; include fee/spread/slippage risk estimates and margin.
Do not increase stakes after a loss or add budgets for member signals.

Require bound rule/schema/prefix lineage and an explicitly invented source/receipt
clock. Recompute the feature decision from its bound observed prefix; do not trust
a freely constructed dataclass or a recomputed checksum as semantic validation.
A quote must be observable only after the feature's availability/decision
time and meet a frozen freshness/entry spread policy. Specify the first eligible
quote and at most one opportunity per completed session. If held or paused at
that opportunity, consume it without later reentry. Identical replay must be
idempotent; conflicting quotes/session identities reject. Held positions retain
their original size/stop/target when a new signal changes.

Use meaningful independent tests for half/full/zero budgets, floor sizing and
minimum/maximum/margin boundaries, spread/slippage/fee assumptions, long/short
proposals, daily loss and open-equity pause, existing-position rejection, duplicate
and conflicting replay, availability/future leakage, gaps and restart state.
If checkpoint support is added, reconstruct only the observed prefix and reject
altered state even with recomputed checksums; hashing is not authentication or
broker reconciliation. Do not invent fills to prove a stop loss cap.

Preserve rejected and insufficient cases and both tested source versions if
review changes code. A proposed stop-risk bound is only an entry estimate; future
gaps can exceed it. Position proposals and admission decisions are not trades or
profitability evidence. A later independently tested fill/financing adapter needs
its own frozen step before any return simulation. No mutation of117 market trials.

No provider/contact/retries, market/history/reserved acquisition, native clock
promotion, SDK/MT5/settings/accounts/log inspection, user launch, paid service,
account creation or orders. Market/paper/order/real-money admission stays false.
119 is prepared, not executed in118.
