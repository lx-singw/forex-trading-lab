# Daily runs122 — completed chronological controls and reporting

Built a separately frozen offline coordinator around unchanged118/119/120/121.
Development and later periods use predeclared bounds and exact required endpoint
timestamps. Aggregation receives only messages observed before each cutoff and
the matching calendar prefix. Warmup prices remain separate from funded execution.
Each candidate/profile/partition starts with fresh flat$10,000, no inherited
position, profit, reservation, consumed opportunity or daily pause.

Endpoint preflight requires the declared final quote to be fresh, new-source and
on a trading day for every comparison, including cash. Missing/late/stale/repeated/
closed endpoints stay unavailable without an earlier-price fallback. Missing required
history also stays unavailable. Derived input/stage freezes precede their outputs.
Interrupted uncommitted attempts are preserved; recovery creates a new attempt and
counts each completed partition once. Checked restore rebuilds only completed
prefixes and verifies artifacts/statistics. Completed repeated runs are idempotent.

Reports reconcile gross P&L, commissions and financing against cash and closed
trade net. They describe expectancy, payoff/profit factor where defined, largest
loss, loss beyond entry estimate, drawdown, holding/flat intervals, turnover and
observed monthly/quarterly windows. Embedded spread/slippage memos are not extra
debits. Empty observation buckets break subsequent opening anchors rather than
creating returns. Partial periods and uncertified calendar closes remain explicit.
No funded portfolio total, strategy ranking or market success flag is produced.

**24 new tests pass** in253.616 seconds; **199 unchanged stage tests also passed**
in the retained first run:223 passing focused checks across these two runs, no
final failures/errors/skips. The first222-test run took344.385 seconds and had one
new test-expectation failure: its funded-stream fixture requested funding before
account availability, so the earlier account-time guard rejected it correctly.
The corrected fixture reaches the intended unfunded-stream guard. Review also
added a regression that forges statistics and recomputes artifact/report/checkpoint
hashes; restore still rejects by recomputation. Only the new test file changed.
Both tested versions/output logs are preserved. Runtime, financial/strategy rules
and all199 retained stage sources stayed unchanged; those passing suites were not
repeated. Older116 and broader suite results remain retained, not rerun.

Tests cover fresh later capital after development gains, zero incoming funded
state, cutoff/future invariance, late/repeated/closed endpoints, unavailable history,
no observation prefix, exact partition/type/freeze guards, interruption/recovery,
duplicate roots/runs, artifact and rehashed-state forgery, observed month/quarter
boundaries, missing/nonpositive anchors, no-trade null ratios, gap-loss estimates,
cost memos, exposure/flat time and turnover. Independent Fraction reviewers check
aggregation, fills and descriptive statistics; accounting division tolerance
remains1e-35 with precision50 and retained118 feature tolerances.

All29 input/manifest/malformed/matrix files, component hashes and independent
review sources froze before demonstration outputs. Six paths contain96 planned
toy account cells:56 available reports and40 unavailable cells. Demonstration
duration199.984 seconds. All available samples are insufficient for market
validation; later_validation is a chronological toy label, not certified unseen data.

Independent review reconstructs16,882 prefix messages,3,117 completed bars,
1,236 scheduled closure dispositions, three incomplete sessions and12 pending
sessions at cutoffs. Available accounts contain24 closed invented positions,
48 entry/exit fills,48 reserve/release records,60 financing rollovers and928 quote
outcomes. All156 ledger records,56 account statistics,88 monthly windows and88
quarterly windows reconcile. No warmup profits or development positions transfer.

Eighteen controller restores cover initial, completed-development and finished
states. A guard prevents later computation during prefix restore; all states/reports
match.36 checkpoint forgeries/input substitutions and16 malformed inputs reject
with exact reasons. Six duplicate CLI runs reject without changing outputs. Unit
tests separately prove preservation/exclusion of interrupted attempts and rejection
of statistics whose full artifact/checkpoint hash chain has been recomputed.

The following **invented MIX50_D ledger examples** retain both cost profiles and
all unavailable periods. Every row is a separate fresh account, not cumulative
profits. Display rounding does not alter the decimal ledger.

| Invented path | Partition | Base trades | Base toy net USD | Adverse toy net USD |
| --- | --- | ---: | ---: | ---: |
| targets | development | 2 | 42.66 | 42.29 |
| targets | later_validation | 1 | -0.24 | -0.36 |
| weekend_gap | development | 1 | -1001.35 | -1002.05 |
| weekend_gap | later_validation | 0 | 0.00 | 0.00 |
| no_signal | development | 0 | 0.00 | 0.00 |
| no_signal | later_validation | 0 | 0.00 | 0.00 |
| missing_history | development | unavailable | unavailable | unavailable |
| missing_history | later_validation | unavailable | unavailable | unavailable |
| missing_endpoint | development | unavailable | unavailable | unavailable |
| missing_endpoint | later_validation | 1 | -1.68 | -2.56 |
| stale_endpoint | development | unavailable | unavailable | unavailable |
| stale_endpoint | later_validation | unavailable | unavailable | unavailable |

These constructed paths prove arithmetic/control behavior only. Positive development
does not ensure positive later outcomes. Stops and1% pauses do not guarantee a maximum
loss; the weekend gap exceeds its$25 entry budget. Zero-trade observed accounts
are distinct from unavailable periods. Do not sum their capital or claim income,
a guaranteed win rate, diversification or a selected winning strategy.

All558 predecessor source/config/test files and62 native hashes remain unchanged;
four new implementation files make562. Independent review sources are separately
bound. Full prior handoff bodies are preserved. Closure binds current/tested sources,
invented inputs/output attempts/reports and earlier evidence, with verified external
bindings for retained older/native files.

Input clocks, sparse coverage, calendar, contract costs and financing remain invented
or unqualified. Neither short partition meets117's24-month requirements; active
trade/monthly samples are insufficient. All16 market cells remain unassigned.
Market profitability, untouched validation, forward paper evaluation, selection,
actual orders and real-money execution remain unavailable. Synthetic DEMO checks
are not actual broker-account lookups. No live-mode toggle exists.

No acquisition, historical/reserved data, provider/support contact, SDK, MT5/settings/
accounts/log operation, paid service, broker account or actual order. Read
[the frozen contract](DAILY-RUNS-122-PROTOCOL.md), [usage](DAILY-RUNS-122-USAGE.md) and
[saved verification](../reports/daily-runs-122-demonstration.json).
Next is [the prepared123 consolidated local package/readiness audit](ENGINE-READINESS-123-PLAN.md),
not implemented in122.
