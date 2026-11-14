# Elliott standalone execution125 — results (2026-10-14 local)

The separate offline simulator now derives EWPB_D124 signals and executable quotes
from the same invented bid/ask stream. It sizes each entry from the observed
structural stop, includes costs and financing, and keeps both chronological
periods in fresh separate USD10,000 accounts. Existing117–124 rules and outcomes
remain unchanged. This implements hypothetical accounting; it establishes no
market profitability and has no broker/order API.

Read [usage](ELLIOTT-EXECUTION-125-USAGE.md),
[the frozen contract](ELLIOTT-EXECUTION-125-PROTOCOL.md) and
[every account comparison](../data/elliott-execution-125-invented-demo/REPORT.md).

The fixed20-case demonstration plans160 toy accounts:136 are computed and24 have
no returns because required history or safe endpoints/exits are unavailable.
Each available period runs EWPB_D124 and CASH separately under base/adverse costs.
All68 available CASH controls have zero P&L and no trades. Do not combine accounts
or infer probabilities from these deliberately constructed paths.

| Invented path | Development/base net USD | Development/adverse net USD | Later/base net USD | Later/adverse net USD |
|---|---:|---:|---:|---:|
| long_target | 48.54 | 48.68 | -0.78 | -1.18 |
| short_target | 48.54 | 48.60 | -0.60 | -0.91 |
| long_stop | -26.42 | -26.64 | -0.78 | -1.18 |
| short_stop | -26.42 | -26.64 | -0.60 | -0.91 |
| long_gap | -244.48 | -244.73 | -0.78 | -1.18 |
| short_gap | -244.45 | -244.685 | -0.60 | -0.91 |
| boundary_hold | -0.78 | -1.18 | -0.78 | -1.18 |
| wide_exit | -27.32 | -27.54 | -0.78 | -1.18 |
| quote_guards | 48.54 | 48.68 | -0.78 | -1.18 |
| delayed_publication | 48.94 | 49.08 | -0.78 | -1.18 |
| minimum_lot | 0.00 | 0.00 | 0.00 | 0.00 |
| max_lot | 21.30 | -33.04 | -29.10 | -33.04 |
| financing_pause | -92.70 | -126.28 | -29.10 | -33.04 |
| held_signal_change | 48.18 | 48.14 | -0.78 | -1.18 |
| invalid_geometry | 0.00 | 0.00 | -0.78 | -1.18 |
| no_signal | 0.00 | 0.00 | 0.00 | 0.00 |
| missing_history | unavailable | unavailable | unavailable | unavailable |
| missing_endpoint | unavailable | unavailable | -0.78 | -1.18 |
| stale_endpoint | unavailable | unavailable | unavailable | unavailable |
| nonpositive_exit | unavailable | unavailable | -0.78 | -1.18 |

These are all EWPB_D124 net outcomes, including commissions and financing.
Full gross/net, fees, rollovers, returns, observed drawdown, trade counts, entry
estimate breaches and unavailable accounts are retained in the readable full
comparison and raw reports. Ordinary missing-history affects both periods;
missing endpoint affects development only; a stale development endpoint also
leaves later completed history incomplete. A positive raw quote producing a
nonpositive slipped exit rejects development transactionally. No earlier endpoint,
filled return or fabricated closure is substituted.

The long target was intentionally constructed to cross the limit: base net
USD48.54 (gross48.68, fees0.14). This demonstrates limit-fill accounting, not a
successful market test. Adverse entry costs can move this entry-dependent2R target
farther from the unchanged structural stop, so a constructed target payoff can
be slightly higher under adverse costs. Lot flooring also changes exposures.
This is no claim that worse costs improve an economic strategy.

The long gap loses USD244.48 base and244.73 adverse, despite a risk budget near
USD25 at entry. Stop overshoot, wider spreads and financing can also exceed the
entry estimate. Both gap directions and losses remain reported. Stops and a1%
daily entry pause are not guaranteed maximum losses. The financing-pause path
contains39 explicitly invented closures; it is not a qualified venue calendar.
Min/max-volume paths also use deliberately scaled prices, not real EURUSD evidence.

A completed bar can affect only a later eligible quote. Quotes retain original
source/receipt times and only the latest published bar's observation; old signals
expire when a newer bar becomes available. Stale/repeated/closed/wide-entry/early
quotes do not manufacture entry opportunities. First eligible opportunities are
consumed even when held, paused, inactive or inadmissible. A held-at-arrival
position prevents reentry on its exit quote, and held stops/targets/lots stay fixed.

33 new tests pass, with237 retained checks passing in the saved initial run:
270 distinct checks across two runs. The initial270-test run had one fixture error:
a later test quote's receipt preceded an earlier stale quote's receipt. Only three
guard-fixture timestamps were repaired; the33 new tests then passed. Both source
versions, failed/passing logs and seals remain preserved. Strategy, risk, costs,
core simulator and retained tests were unchanged. This is not a claim that a
second complete270-test suite was run; older broad suites were not rerun.

Independent Fraction reviewers reconstruct aggregation, causal wave detection,
each entry opportunity and every financial debit/credit. They check61,420 messages,
11,337 completed bars, three incomplete bars,4,558 closures and40 pending bars
across repeated case/period prefixes. On usable paths they check9,670 wave bars,
152 pivots,51 observations and139 setup actions, then491 ledger rows,
2,732 account quote outcomes and58 closed positions. These replicated software
counts are not independent market samples or wins.

All544 checked initial/prefix/unclosed/finished restores reproduce exact state;
restore cannot process an event beyond the completed cursor. Latest-event and
finished replay are idempotent. All544 checkpoint faults and14 malformed inputs
reject. A reviewer originally expected account_fields instead of121's actual
fill_account_fields for a supplied-position input; the rejection itself was
correct. The failed reviewer and all993 existing CLI/checkpoint/log files were
sealed before correcting only that expected label and rechecking saved outputs.
No economic output, source/rule or frozen input matrix was changed.

55 input/matrix/manifest files,46 tested source bindings and independent reviewers
were frozen before outputs. The successful audit binds953 generated data files.
The readable REPORT.md was added afterward from those checked results. Local
hashes show consistency, not signed authenticity or broker reconciliation.

All571 retained implementation/config/test and62 native input hashes remain
unchanged. Four new implementation/test files make575. Prior README/context/plan/
verification bodies remain intact. The synthetic integer DEMO guard is not an
actual broker account-type lookup. No market/native admission, historical or
reserved replay, source acquisition/contact, SDK, MT5/settings/accounts/log
operation, paid service, account creation or actual order occurred.

Account-level checked restore is available. The batch CLI preserves an existing
or partially written root and requires a new output name; it does not resume that
root. Derived compiled signals are internal artifacts, not public raw input.
This is not a crash-durability, broker-reconciliation or outside-interference
guarantee.

All16 old plus four separately planned Elliott market cells remain unassigned
and unrun. Source clock/feed/calendar/coverage, actual contract/cost/financing and
sufficient24-month development/24-month genuinely untouched validation evidence
remain unresolved. Market/forward-paper/order/real-money availability stays false.

Next is [prepared comparison/reporting126](ELLIOTT-COMPARISON-126-PLAN.md), not
implemented here: compare the unchanged hypotheses descriptively on identical
invented quotes and costs before any combination or market claim. The125 toy
paths favor exercises of an Elliott-inspired rule and cannot select a winner.

Evidence:
[focused checks](../reports/elliott-execution-125-focused-verification.json),
[independent audit](../reports/elliott-execution-125-demonstration.json),
[final source](../reports/elliott-execution-125-final-source.json) and
[completion review](../reports/elliott-execution-125-completion-review.json).
