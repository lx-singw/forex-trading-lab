# Comparison 008 — fixed five-candidate development batch

Declared 2026-10-01 before any candidate performance. Implement exactly the five
rules in `config/research-candidates-008.json`; no parameter search, revised exit
rule, new candidate or weight fitting in this batch. Signal and warmup tests
precede the freeze. Original historical outputs and source archives are preserved.

Use three previously eligible samples: `research-004-january-mt5`,
`research-005-april-new-york` and `research-004-july-new-york`, each bound to its
original passing dataset-specific review. They are reused development data.
October is excluded, 2025 is excluded from optimization, and future reserved
Nov–Dec 2026 validation remains untouched.

For each dataset, the first 201 observed H1 bars are indicator warmup only.
Start evaluation at the opening of its 202nd observed hour, ending at its actual
last quote. Freeze exact boundaries and hashes before returns. Every candidate
gets the same warmup, quotes and evaluation window. No warmup positions or P&L
carry into evaluation. Keep the existing stale-entry rejection after missing
hours. Indicators use observed bars without inventing missing candles.

Run C00–C04 with both existing base/adverse configs, giving 30 declared scenarios.
Each starts independently from $10,000; no combined continuous annual return.
Preserve one-position sizing, 0.25% estimated trade-risk cap, 1% daily entry pause,
1.5-pip spread filter, modeled 1:10 leverage, stop/target logic and costs. A
selector chooses at most one component; it cannot add their positions together.
An idle USD/no-trade reference has zero modeled return, without modeled interest.

Freeze the whole batch, all source/scripts/tests, candidate specification and
protocol before evaluation. Publish all candidates and cost scenarios regardless
of returns, including zero-trade cases. Record each eligible flat-account decision
with its closed-history features and reason. Reconcile trades, commissions,
swaps, equity, counts and hashes. Exact checksums preserve the test ledger.

Default TickSimulator behavior must retain its before-change synthetic reference
results. Candidate tests must cover entry rules, current/future-price isolation,
warmup, selector boundaries, flat markets, stop gaps, daily pauses, one-position
limits and recovery with an open position. Changing a checkpoint's candidate or
evaluation boundary must fail. The package fingerprint changes with new modules;
old studies can be reproduced from their own preserved source archives.

No best-strategy selection, confidence claim or promotion follows from this
batch. Report its per-month P&L, trade counts, drawdowns, costs and concentration.
These short samples can identify implementation problems or research candidates,
not establish robust profitability. A longer, separately frozen chronological
evaluation is still required; no demo orders or real-money mode are authorized.
