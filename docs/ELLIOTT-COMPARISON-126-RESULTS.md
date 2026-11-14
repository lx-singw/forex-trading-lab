# Five-strategy comparison126 — results (2026-10-14 local)

The offline comparison runs five unique fixed candidates on identical invented
quotes, source/receipt times and latest published feature identities: EWPB_D124,
T12_D, MR20_D, MIX50_D and CASH. CASH is already one of the four117 candidates;
it is not duplicated. Each model retains its own fixed stop/sizing method.
Initial capital, chronological bounds and cost profiles match, while actual
exposure differs. This compares complete hypotheses, not entry signals alone.

Read [usage](ELLIOTT-COMPARISON-126-USAGE.md),
[the frozen contract](ELLIOTT-COMPARISON-126-PROTOCOL.md) and
[every account outcome](../data/elliott-comparison-126-invented-demo/REPORT.md).

All26 paths are frozen, unchanged inventions:20 execution125 and six run122
cases, with only the outer wrapper/case changed. The520 planned accounts produce
414 computed results and106 unavailable cells, with no fabricated returns.
All84 available CASH controls have zero P&L and no trades.
No capital or P&L is added as a portfolio; no candidate is ranked or selected.

The development/base netUSD overview follows. Every later/adverse account is
also shown in the full comparison. Values here are rounded to cents; original
precision and every ledger remain in raw reports.

| Invented path | Elliott | Trend | Mean reversion | Fixed mixture | Cash |
|---|---:|---:|---:|---:|---:|
| ew_long_target | 48.54 | 39.96 | -0.57 | 13.23 | 0.00 |
| ew_short_target | 48.54 | 40.11 | -0.72 | 13.29 | 0.00 |
| ew_long_stop | -26.42 | -40.35 | -0.57 | -13.54 | 0.00 |
| ew_short_stop | -26.42 | -40.20 | -0.72 | -13.48 | 0.00 |
| ew_long_gap | -244.48 | -366.93 | -0.86 | -122.24 | 0.00 |
| ew_short_gap | -244.45 | -366.88 | -1.08 | -122.22 | 0.00 |
| ew_boundary_hold | -0.78 | -1.17 | -0.86 | -0.39 | 0.00 |
| ew_wide_exit | -27.32 | -41.70 | -0.57 | -13.99 | 0.00 |
| ew_quote_guards | 48.54 | 39.96 | -0.57 | 13.23 | 0.00 |
| ew_delayed_publication | 48.94 | 39.96 | -0.57 | 13.23 | 0.00 |
| ew_minimum_lot | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| ew_max_lot | 21.30 | -19.47 | -18.60 | -8.16 | 0.00 |
| ew_financing_pause | -92.70 | -124.47 | -49.10 | -94.74 | 0.00 |
| ew_held_signal_change | 48.18 | 40.14 | -132.86 | 13.38 | 0.00 |
| ew_invalid_geometry | 0.00 | 39.96 | -0.57 | 13.23 | 0.00 |
| ew_no_signal | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| ew_missing_history | unavailable | unavailable | unavailable | unavailable | unavailable |
| ew_missing_endpoint | unavailable | unavailable | unavailable | unavailable | unavailable |
| ew_stale_endpoint | unavailable | unavailable | unavailable | unavailable | unavailable |
| ew_nonpositive_exit | unavailable | unavailable | 0.00 | unavailable | 0.00 |
| daily_targets | 0.00 | 41.82 | 43.08 | 42.66 | 0.00 |
| daily_weekend_gap | 0.00 | -1001.35 | -1001.35 | -1001.35 | 0.00 |
| daily_no_signal | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| daily_missing_history | unavailable | unavailable | unavailable | unavailable | unavailable |
| daily_missing_endpoint | unavailable | unavailable | unavailable | unavailable | unavailable |
| daily_stale_endpoint | unavailable | unavailable | unavailable | unavailable | unavailable |

The constructed long-target example gains USD48.54 with Elliott,39.96 with trend,
13.23 with the fixed mixture, while mean reversion loses0.57 and cash remains flat.
Those are deliberate software paths, not market profits. The later, gap, stop,
wide-spread and financing losses are retained alongside all gains and abstentions.
A favorable constructed example cannot establish a win rate, advantage or robust
combination. These paths have already been seen and cannot become untouched
validation. Worse entry costs can move an entry-dependent2R target; a toy payoff
need not decrease monotonically under the adverse profile.

Unavailable reasons/counts are retained: {"invalid_endpoint_quote": 20, "missing_declared_endpoint": 20, "missing_required_session": 60, "nonpositive_exit_price": 6}.
Missing history or safe declared endpoint affects all ten period cells, including
cash. Nonpositive modeled exits affect only the failing account. This is explicit
and differs from125's all-four-period transaction; partial ledgers are not reported.
Unexpected binding or engine errors stop instead of being relabeled unavailable.
An empty received prefix also reports no_observed_prefix for every period cell.

Reporting reuses unchanged122 definitions for both adapters. Cash change reconciles
with gross fills−commissions+financing and closed-trade nets. Embedded half-spread/
slippage memos describe price effects and are not debited again. Target exits have
no separately observable spread decomposition. Reports include observed drawdown,
turnover, exposure/flat intervals, quote gaps, largest losses and entry-estimate
breaches. Gaps, spreads and financing can exceed stop/risk and daily-pause
estimates; these controls are not guaranteed maximum losses.

Monthly/quarterly returns use last executable observed equity and include actual
boundary liquidation in the final mark. Missing windows break their return anchor;
unknown/nonpositive anchors and no-trade ratios remain null. These are sparse
observed windows, not certified calendar closes. All sample assessments are
insufficient under retained24-month/50-active-trade/24-monthly-mark checks.

The initial complete313-test suite passed:19 new comparison checks and294 retained
118–125 checks. Review then identified a valid no-received-prefix edge that stopped
rather than reporting unavailable. The final refinement changes only that common
empty-window guard and adds its regression. That new check plus CLI evaluate/
verify/collision and rehashed-summary regressions pass on the final source.
There are314 distinct passing checks across the saved runs,20 new and294 retained.
A complete314-test final suite was not run; unchanged broad tests were not repeated.
Both source versions/logs remain preserved. Financial and strategy rules, weights,
risk and cost parameters are unchanged.

The67 input/matrix/manifest files,52 tested source bindings and independent reviewers
were frozen before demonstration outputs. Independent reviewers check78,302
messages,14,454 completed bars,6 incomplete bars,
5,794 closures and52 pending bars over repeated case/period
prefixes. On available paths they check11,759 wave bars,
159 pivots,52 observations and
141 setup actions. Fraction reviewers reconstruct both
financial adapters and statistics: 2,127 ledger rows,
8,070 account quote outcomes,288 closed
positions,474 monthly and464 quarterly
observed windows. Replicated software counts are not independent market samples.

All52 actual CLI evaluate/read-only-verify runs pass. Verification re-derives raw
prefixes, bars, signals, both ledgers and metrics, leaving all
632 generated run files unchanged.
All124 applicable earlier125 Elliott
account summaries and122 legacy economic statistics match exactly; only binding/
position identities are excluded where old prefix names differ. All14 malformed
inputs reject. The independent audit binds632 generated data files;
the consolidated readable overview was added afterward.

All575 retained source/config/test and62 native hashes are unchanged. Four new
implementation/test files make579. Prior README/context/plan/verification bodies
are preserved. Existing account-level restart remains in120/125, including the
retained meaningful position, duplicate, stop, loss and restart checks.126 adds
exclusive output roots and read-only verification, not batch resume, crash
durability, signed provenance or broker reconciliation.

All16 retained plus four Elliott market cells remain unassigned/unrun. Source
clock/feed/calendar/coverage, actual contract/cost/financing and sufficient
chronological development/genuinely untouched market validation remain unresolved.
There was no market/native admission, source contact/acquisition, historical or
reserved replay, SDK, MT5/settings/accounts/log operation, paid service, account
creation, actual broker account lookup or actual order. Synthetic DEMO mode is
not an actual account check. Market/paper/order/real-money availability remains false.

Next research must address qualified evidence before strategy selection or a new
combination. More gains on engineered paths would not resolve those missing
requirements. The code and reporting are ready for further offline verification;
this stage assigns no market dataset or source.

Evidence:
[checks](../reports/elliott-comparison-126-focused-verification.json),
[independent audit](../reports/elliott-comparison-126-demonstration.json),
[final source](../reports/elliott-comparison-126-final-source.json) and
[completion review](../reports/elliott-comparison-126-completion-review.json).
