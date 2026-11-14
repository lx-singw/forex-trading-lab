# Daily bars121 — completed coherent invented pipeline

Implemented causal midpoint aggregation and connected it to unchanged118 features
and120 accounting. Daily bars now come from the same bid/ask messages used by fills.
The adapter retains quote hashes/exact midpoints, source and receipt times, coverage
dispositions, observed finalizer identity, calendar/message prefixes and118 lineage.
Execution keeps original bid/ask prices; midpoint candles are never turned into
execution quotes. All117 rules, candidates, weights and cost profiles are unchanged.

Bars publish only after the session and its2-second receipt grace period, at the
actually observed finalizer time. Source intervals are half-open; a boundary quote
belongs to the next day. Fresh late receipts can contribute before the deadline;
finalized bars never revise. Repeated/stale/closure quotes are excluded from bars,
but execution retains them so a bad final quote cannot become an earlier good fill.
Missing required coverage makes the pipeline unavailable with no return report.
An unfinished final session supplies no feature; boundary accounting can still use
its actual executable quote. No prices/extrema, closures or clocks are inferred.

**199 focused tests pass**, no failures/errors/skips,93.353 seconds:38 new adapter/
integration tests and161 unchanged118/119/120 tests. Tests independently reconstruct
midpoint OHLC, quote coverage, publication timing/lineage and full aggregation state
using Fraction arithmetic, then reuse120's rational fill/financing checker. Exact
age, edge and gap limits, post-end receipts, source/receipt ordering, conflicts,
closures/missing sessions, partial sessions, future invariance, held weekends,
feature availability, derived quote identity, duplicates and restart forgery are
covered. Stale/repeated held endpoints remain unavailable instead of falling back.

The first198-test version also passed in113.804 seconds. Review added one connector
test exercising two bad endpoints; both tested source versions/results are saved.
No unit test failed and no financial rule or expectation was weakened. The initial
demonstration reviewer had a Python generator-parenthesis syntax error before it
executed or created outputs. Both reviewer versions and the repair record are
preserved; implementation, fixtures and frozen rules were unchanged. Older116 and
broader suite results remain retained, not rerun.

All33 input/manifest/malformed/matrix files, component hashes and separate independent
review sources froze before aggregation outputs. Derived120 inputs and their own
freezes preceded ledger outputs. Eight predeclared paths produce six usable invented
pipelines and two unavailable ones. Demonstration duration285.002 seconds.

Independent checks reconcile all11,053 messages,2,045 completed bars,816 scheduled
closure dispositions, two incomplete sessions and one pending unfinished session.
Six usable paths produce48 separate candidate/profile accounts:34 closed invented
positions,68 entry/exit fills,68 reserve/release records,80 financing rollovers and
568 quote outcomes. All216 ledger records and568 outcomes reconcile. Bar/state
comparisons are canonical;120's rational accounting checks retain their1e-35
precision50 division tolerance and118 independent feature tolerances.

The72 sampled aggregation restart boundaries include pending samples, publication,
warmup/execution transition and final cursor, with guards against stepping future
messages.664 accounting prefix/unfinished-endpoint/finished restarts also match:
736 total. Small-fixture unit tests cover every message prefix.72 checkpoint
forgeries/input substitutions and16 malformed inputs reject with exact reasons.
CLI/saved reports, original execution quotes and all derived file hashes agree.

These are **invented MIX50_D ledger examples**, not market performance or a strategy
ranking. Each account starts fresh at$10,000. Prices deliberately exercise targets,
gaps, costs and unavailable history; no income/win-rate conclusion follows.

| Invented path | Status | Base closed positions | Base toy net USD | Adverse toy net USD |
| --- | --- | ---: | ---: | ---: |
| long_path | usable invented pipeline | 2 | 42.84 | 42.56 |
| short_path | usable invented pipeline | 2 | 42.85 | 42.59 |
| weekend_gap | usable invented pipeline | 1 | -1001.35 | -1002.05 |
| half_risk | usable invented pipeline | 1 | -1.89 | -2.87 |
| no_signal | usable invented pipeline | 0 | 0.00 | 0.00 |
| missing_coverage | unavailable history | unavailable | unavailable | unavailable |
| stale_coverage | unavailable history | unavailable | unavailable | unavailable |
| partial_session | usable invented pipeline | 1 | -4.69 | -5.67 |

Unavailable is not zero performance. The weekend gap exceeds the$25 initial entry
budget; stops and daily pauses do not guarantee maximum losses. Display rounding
does not alter decimal accounting. Do not sum separate candidate/profile capitals
or treat the combination as demonstrated diversification.

All554 predecessor source/config/test files and62 native hashes remain unchanged;
four new implementation files make558. Independent review sources are separately
bound. Working handoffs preserve their entire previous body bytes. Final archive/
closure binds tested versions, sources, small invented inputs/outputs and prior
evidence, with verified external bindings for retained older/native files.

The sparse four-quote/edge/gap coverage policy and weekday calendar are invented
software conventions, not certification of a feed, tick completeness or broker
hours. Source UTC, receipt age, venue calendar/coverage, contract costs and financing
remain unqualified. The short toy partitions do not meet117's24-month development
and24-month untouched validation requirements. All16 market cells remain unassigned.
Market profitability, forward paper evaluation, strategy selection and actual
orders remain unavailable. Synthetic DEMO rejection is not an actual account lookup.

No historical/reserved data, quote acquisition, provider/support contact, SDK,
MT5/settings/accounts/log operation, paid service, broker account or actual order.
No real-money toggle. Read [the frozen contract](DAILY-BARS-121-PROTOCOL.md),
[usage](DAILY-BARS-121-USAGE.md) and
[saved verification](../reports/daily-bars-121-demonstration.json).
Next is [the prepared122 chronological run controls/reporting](DAILY-RUNS-122-PLAN.md),
not implemented in121.
