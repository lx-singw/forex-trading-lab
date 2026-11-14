# Daily risk119 — implemented admission and sizing

Built a separate invented-data daily adapter around unchanged118 features. It
recomputes bound prefix decisions, admits one eligible opportunity per session,
floors cost-aware lot proposals against one risk budget and available margin,
latches daily pauses, preserves held levels and reserves at most one entry slot.
No reservation is treated as a filled position. No fills, returns or equity curve
are calculated. The fixed117 rules and its16 market-performance cells are unchanged.

**105 focused tests pass:57 new and48 retained118 tests**, no final failures/errors/
skips,15.552 seconds. Independent rational sizing and hypothetical stop-debit checks
cover full/half budgets, fees/slippage/spread,0.01 volume floor, exact minimum risk/
margin boundaries,1-lot maximum,2R geometry, daily headroom, loss/gap pauses, held
and reserved slots, duplicate/conflicting quotes and session identities, future
invariance, synthetic demo guards and strict input/freeze/checkpoint validation.

The initial105-test run had one failure in the CLI smoke test: a missing list
terminator in summary output. The correction changes only that syntax. Both
tested source versions, the failure output and the successful output are preserved.
No test expectation or financial rule was weakened to resolve it. The older116269
focused and broader-suite results are retained, not rerun.

All61 input/manifest/matrix artifacts were frozen before demonstrations, along
with the independent review source. The22 fixed invented cases ×two cost profiles
×four candidates give176 comparisons and392 guard outcomes. All match independent
Decimal feature and rational guard/sizing calculations. There are66 proposed
entries; each comparison has at most one outstanding reservation. These are not
trades, wins, fees paid or profits. Different histories can produce different lot
sizes even when a budget is halved; stop distance, costs, margin and the lot cap
also determine volume.

All176 comparisons match both prefix and finished checked restarts, including
idempotent latest replay. All176 predeclared checkpoint faults reject:44 boolean
cursors,44 cross-profile bindings,44 cross-candidate bindings and44 rehashed pause
changes. Unit tests separately reject altered reservations, levels, consumed
sessions, marks and outcomes even with recomputed checksums. All16 malformed input
cases reject with their exact declared reasons and no invalid manifest/report.
CLI and stored summaries agree. Demonstration duration94.814 seconds.

The following table contains the fixed base MIX50_D guard sequences; the complete
report retains every candidate/profile outcome without selection.

| Invented case | Guard sequence |
| --- | --- |
| full_long | proposal_reserved, session_consumed |
| half_long | proposal_reserved, session_consumed |
| full_short | proposal_reserved, session_consumed |
| half_short | proposal_reserved, session_consumed |
| opposing | inactive_signal, session_consumed |
| warmup | inactive_signal, session_consumed |
| zero_range | inactive_signal, session_consumed |
| wide_then_valid | wide_quote, proposal_reserved, session_consumed |
| stale_then_valid | stale_quote, proposal_reserved, session_consumed |
| before_then_valid | before_feature, proposal_reserved, session_consumed |
| minimum_risk | minimum_lot_risk, session_consumed |
| minimum_margin | minimum_lot_margin, session_consumed |
| max_lot | proposal_reserved, session_consumed |
| pause_recovery | daily_pause, session_consumed |
| open_loss | held_position, session_consumed |
| daily_headroom | daily_headroom, session_consumed |
| held_signal_change | held_position, held_position |
| reservation_next_session | proposal_reserved, reserved_entry_slot |
| gap_pause | wide_quote, daily_pause |
| stale_feature | wide_quote, stale_feature, proposal_reserved |
| closed_then_valid | closed_quote, proposal_reserved |
| repeated_source | proposal_reserved, repeated_source, session_consumed |

At USD10,000 supplied equity, full and half entry budgets are$25 and$12.50.
Estimated stop risk includes the slipped-entry stop distance, exit slippage and
round-turn commission. Entry spread/slippage are represented in the proposed
entry and immediate liquidation estimate. Financing is metadata only here.
Neither these entry estimates nor the1% pause guarantee a maximum loss.

Executable-equity/free-margin marks and held snapshots are supplied inventions;
119 does not derive or reconcile them from positions, financing or fills. Synthetic
DEMO mode checks are not an actual broker-account lookup. Reservations never
release in this version; it cannot model a completed trading cycle. Source UTC,
age/feed/coverage, contract terms and actual execution costs remain unqualified.
These limitations prevent market or forward-paper evaluation and profitability claims.

All546 predecessor source/config/test hashes remain unchanged; four new
implementation files make550. The saved independent audit source is separately
hash-bound. All62 native evidence hashes and full previous handoff body bytes are
preserved. The final archive contains small invented inputs/results, both tested
versions and evidence; older/native graphs are external verified hash bindings.

No historical/reserved data consumption, new quotes, provider/support contact,
SDK, MT5 operation, account creation, paid service or orders. Market/paper/order/
real-money admission stays unavailable. Read [the protocol](DAILY-RISK-119-PROTOCOL.md)
and [usage](DAILY-RISK-119-USAGE.md). Next is
[the prepared120 invented fill/financing step](DAILY-FILLS-120-PLAN.md), not executed
in119.
