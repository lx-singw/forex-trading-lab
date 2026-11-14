# Daily fills120 — prepared invented execution accounting

After119 closes, implement a separately frozen offline fill/financing/accounting
adapter for fixed117/118 daily decisions and119 admission semantics. Read those
protocols/results first. Preserve all old sources and outcomes. This is invented
software verification, not market validation, paper execution or an order API.

Freeze exact fill, reservation, quote, daily opportunity and session rules before
any outputs. Replace119's supplied account marks with independently reconciled
balance/free-margin/executable-equity calculations. A proposal is not a fill:
define explicit hypothetical acceptance, one-position reservation transition and
release only on observed closed-position accounting. Do not trust declared marks
or a freely constructed feature/position as a validated state.

Use inherited113 hypothetical base/adverse contracts, entry/exit commissions,
side-specific bid/ask/slippage,2R targets, observed stop/gap fills and conservative
target handling. Preserve qualifying first-opportunity consumption, half/full/zero
budgets and original held size/stop/target. Reconcile entry spread/slippage and
fees once; do not double-charge or silently omit costs. Stops can gap beyond their
entry estimate. Missing quotes are not interpolated; stale signals, scheduled
closures and missing required sessions follow frozen explicit policies.

Define financing accrual through every elapsed UTC rollover, including Wednesday
triple debit and weekends/missing days in the retained hypothetical convention.
These calendar/financing assumptions do not qualify a broker source. Retain corrected
019B executable-equity semantics or freeze any explicit deviation before outputs;
pause and drawdown must reflect the fill actually modeled on an observed quote.
No favorable stop fills, guessed broker offsets, future data or real-money mode.

Meaningful independent tests must cover long/short entry/exit, both stop/target
conditions and adverse gaps, commissions/spreads/slippage, financing and held
weekend gaps, minimum/maximum/margin sizing, duplicate prevention, daily loss and
open-equity pauses, first opportunity, multiple daily sessions, reservation release
and restart. Rebuild observed prefix only on restore; reject altered economic
state even with recomputed checksums. Independently reconcile each fill, lot,
fee/debit, balance and executable-equity mark. No-trade, loss and invalid cases
must remain reported. Never sum separate candidate capitals as a portfolio.

Demonstrate only a small predeclared invented matrix, frozen before output. Toy
returns, if produced for ledger reconciliation, prove arithmetic only and must
not rank strategies, tune weights or claim an edge. The117 market-performance
cells, development/untouched validation requirements and data qualification
remain unassigned. Existing native107/109/111 are not admitted as market inputs.

No contact/provider retries, historical/reserved acquisition or replay, SDK/MT5/
settings/accounts/log inspection, user launch, paid service, broker account or
orders. No real-money toggle. Actual DEMO checks/rechecks are required if a future
execution component ever becomes separately authorized and qualified;120 has no
broker execution. This step is prepared, not implemented in119.
