# Daily fills120 — completed invented execution accounting

Implemented a separate offline daily fill/financing ledger using unchanged118
features and119 admission rules. Account marks now come from calculated cash,
side-specific open P&L and original-entry margin. Supplied equity/free margin/held
positions reject. Every accepted proposal records a reservation and hypothetical
entry fill; the slot releases only after accounted exit. This is invented execution,
not an actual broker fill, account lookup or order interface.

Entry and exit commissions debit once. Bid/ask and slippage are embedded in prices;
stops fill on observed quotes with adverse slippage, targets at original limits.
Held positions retain original lots/levels when daily signals change. Financing
walks every elapsed UTC rollover, including Wednesday triple and zero-debit weekend
records. Wide/stale-feature quotes can close positions; stale/repeated/closure quotes
cannot execute or reprice. Missing prices are never interpolated. Boundary liquidation
requires the final executable quote; an invalid held endpoint rejects without returns.

Corrected019B equity semantics are retained: open marks use observed side prices;
breached exits use the actual modeled price/fee, avoiding favorable overshoot marks.
Daily anchors precede gap/financing losses. Pauses latch through recovery within
the day, and entries also need immediate liquidation headroom. There is no guessed
margin-call fill, resizing after losses, real-money toggle or external execution.

**161 focused tests pass**, no final failures/errors/skips,69.259 seconds:56 new
accounting tests plus57 unchanged119 and48 unchanged118 tests. Independent rational
accounting checks every fill, lot, commission, financing debit, cash/margin/equity
mark and drawdown. Tests cover both sides/exit reasons, gaps, minimum/maximum volume,
exact margin boundary, daily headroom, financing-driven open losses and latched
pause after recovery, first opportunities, slot release, future invariance, strict
input/freeze types, duplicate/restart behavior and impossible slipped exit prices.

Three tested source versions and outputs are preserved. The first156-test run had
one failure and one error: a full-risk cost expectation for a half-risk fixture,
and an unavailable feature at a midnight-entry test. The second161-test run had
one failure because its calibrated headroom quote omitted financing. Correcting
those test calculations preserved risk/cost/pause rules. Review also added a
transactional rejection for nonpositive assumed exit prices and meaningful
margin/headroom/open-loss tests. No strategy parameters were tuned. Older116 and
broader suite results are retained, not rerun.

All43 matrix input/manifest/malformed/matrix artifacts and the separate independent
rational checker were frozen before demonstration outputs. Fourteen accepted paths
produce112 separate candidate/profile comparisons:64 closed invented positions,
128 entry/exit fills,128 reserve/release records,20 financing rollovers and280 quote
outcomes. All276 ledger records and280 outcomes match the independent checker.
CLI and saved reports agree. Demonstration duration109.960 seconds.
Rational checks allow an absolute1e-35 tolerance for precision50 Decimal division;
feature checks retain118's independent moment/true-range tolerances.

There are392 observed-prefix/finished restart checks, plus112 checks at the
unfinished final cursor before boundary liquidation:504 total, with identical
states/reports and no duplicate debits.314 forged/checksum-recomputed checkpoints
and14 malformed inputs reject with their specified reasons. All no-trade, gain,
loss and invalid cases are preserved.

The following **invented MIX50_D arithmetic examples** show both fixed cost
profiles. They are not market performance or a strategy ranking. Every comparison
has independent fresh capital; the minimum-capital fixture starts at$10, all others
at$10,000. Display rounding to cents does not change the decimal ledger.

| Invented path | Base closed positions | Base toy net USD | Adverse toy net USD |
| --- | ---: | ---: | ---: |
| long_target | 1 | 43.08 | 42.93 |
| short_target | 1 | 43.08 | 42.93 |
| long_stop | 1 | -51.05 | -51.60 |
| short_stop | 1 | -51.05 | -51.60 |
| long_gap | 1 | -1001.05 | -1001.60 |
| short_gap | 1 | -1001.05 | -1001.60 |
| half_risk | 1 | -1.47 | -2.24 |
| opposing | 0 | 0.00 | 0.00 |
| warmup | 0 | 0.00 | 0.00 |
| zero_range | 0 | 0.00 | 0.00 |
| weekend_financing | 1 | -0.72 | -1.09 |
| release_next_session | 2 | 60.31 | 60.10 |
| quality_guards | 1 | -51.05 | -51.60 |
| minimum_capital | 0 | 0.00 | 0.00 |

The full-risk$25 budget is an entry estimate: the intentionally severe base gap
loses$1,001.05. Stops and the1% daily pause do not guarantee a maximum loss. The
positive target examples were constructed to hit their targets; they prove no
forecasting ability, win rate, income or market edge. Do not add separate capitals.

All550 predecessor source/config/test files and62 native evidence hashes remain
unchanged; four new implementation files make554. Independent checker source is
separately bound. Full prior handoff body bytes are preserved. Final archive/closure
bind current source, tested versions, small invented fixtures/reports and previous
evidence; retained native/older files have verified external hash bindings.

Daily bars and quotes are still separate invented fixtures, not a coherent observed
quote aggregation or qualified feed. Source UTC, receipt age, calendar, coverage,
contract costs and financing remain unqualified. All11716 planned market cells are
unassigned/unrun. No market profitability or forward-paper validation is available.
No historical/reserved data, quote acquisition, provider/support contact, SDK,
MT5/settings/accounts/log operation, paid service, broker account or actual order.
Market/paper/order/real-money admission remains unavailable.

Read [the frozen contract](DAILY-FILLS-120-PROTOCOL.md),
[usage](DAILY-FILLS-120-USAGE.md) and
[saved verification](../reports/daily-fills-120-demonstration.json).
Next is [the prepared121 causal invented quote-to-bar adapter](DAILY-BARS-121-PLAN.md),
not implemented in120.
