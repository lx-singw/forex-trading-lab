# Offline evidence summary129 results — 15 October 2026

The offline summary is implemented and generated from all 62 pinned native input
files, totaling 2,266,720 bytes. It reparses the actual saved exports, verifies
their SHA256 values and produces deterministic JSON and readable Markdown.
No terminal action or new data acquisition was needed.

Read the [summary](../reports/evidence-summary-129-summary.md) or
[structured output](../reports/evidence-summary-129-summary.json).

| Evidence source | Nominal computer-GMT origin | Observed scope |
|---|---|---|
| Quote pilot111 | 12 October 2026 18:15:59 | 7,188 snapshots in 60 linked files; stopped at time cap |
| Metadata127 | 14 October 2026 16:40:49 | 33 current reported properties, weekly template, two quotes and clocks |
| Costs128 | 14 October 2026 18:16:25 | Five successful queries; empty commission-rule response and directional margin factors |

The quote pilot retains 4,405 adjacent repeats, stop code 13 and its original
counter/timing outcomes. The metadata probe's two quote reads are kept separate.
Current reported leverage 10, contract size 100,000, point/tick size 0.00001,
EUR margin currency and swap values remain raw observations of that run.

The cost response remains reported_empty, with buy/sell initial factors 1.0 and
maintenance factors 0.0. No zero total cost, margin-free trading or historical
fee claim is inferred. Raw server/computer differences remain 10,800 seconds;
no UTC offset, quote age or dollar fee/margin conversion is computed.

Each source keeps its own original hashes, date, status and scope. The summary
does not claim authenticated account continuity or combine them into an atomic
contract or continuous quote history. Financial model assumptions are not
imported, applied or overwritten.

## Verification

All **104 tests pass**: 22 new summary tests and 82 retained inspector tests
(38 forward111, 19 metadata127, 25 cost128). There are zero failures, errors or
skips. The retained111 suite also compiles and checks its pure C++ recorder/guard
core without native calls; this is included in the 104 count.

The new checks cover pinned provenance, input/path/manifest limits, changed
hashes, invalid wire despite a new hash, source/run order, folder/header origin,
symlink rejection, duplicate keys, incomplete and stopped captures, empty final
quote segments, failed metadata/margin/commission queries, empty rule lists,
negative reported commission values, raw clock differences, deterministic
output and unchanged inputs. Valid market-declared input cannot enable any
availability flag, infer dollars or authenticate a cross-run identity.

The two real CLI formats and library agree. A repeated JSON CLI result is
byte-identical. All 62 input hashes remain unchanged. A separate comparison
against retained capture evidence matches all 60 quote-file bindings and
counters, 33 properties, two metadata quote reads, four clock groups, two margin
responses and the empty commission response.

All 593 prior source/config/test and 64 native input hashes remain unchanged.
Four new files (manifest, library, CLI and test) make 597 source/config/test files.
Financial strategy, risk, cost and weight rules remain fixed; the prior financial
simulation tests were not rerun. Prior handoff bodies and source/evidence records
are preserved. No new Windows build/deployment, MT5 run/settings/log/account
operation, SDK connection, support contact, service/account creation, historical/
reserved strategy replay or actual order occurred. No strategy returns,
ranking, parameter search or profitability result was produced.

Evidence: [source freeze](../reports/evidence-summary-129-development-source-001.json),
[tests](../reports/evidence-summary-129-tests-001.json),
[CLI/read-only review](../reports/evidence-summary-129-cli-readonly-review.json),
[retained-evidence comparison](../reports/evidence-summary-129-retained-evidence-review.json).
The [final source closure](../reports/evidence-summary-129-final-source.json) and
[completion review](../reports/evidence-summary-129-completion-review.json)
bind the final report and handoff.

## What is still missing

The report explicitly retains six gaps: producer/cross-run identity, UTC/quote
age, complete delivery/executable prices, cost completeness, calendar/coverage
and untouched strategy evaluation. A valid diagnostic format does not establish
a market edge. Market, paper, order and real-money availability remains false.

The next concrete source investigation is a short observation of quote and
server/computer clocks together at each poll. It should test the raw clock-domain
and liveness hypotheses using a separate fresh, bounded, default-off diagnostic.
That is future work, not implemented or launched here; no old dated probe is
renewed. Such observations alone will not repair historical gaps or provide
long chronological validation. Current source and cost observations remain
diagnostic; October stays quarantined, November–December 2026 reserved and 2025
consumed. Closed historical/provider/H.10/090 routes stay closed.

No MT5 clicks or other user action are needed for this completed summary.
