# Elliott149 — common session paper comparison

14 November 2026. Adds a separately typed, invented-input comparison adapter for
EW_FULL_V1, frozen EWPB_D124, frozen T12_D and CASH, each with base/adverse costs
and two chronological software partitions. The16 cells are independent paper
accounts. This does not admit a market dataset or enable native submissions.

## Common input and chronology

`elliott_session_comparison_149.py` freezes the complete input bytes, source graph,
calendar, policy, candidates, profiles, partitions and explicit endpoints before
paper evaluation. The strict schema accepts only invented EURUSD data within the
146 calendar domain, anonymous cases, bounded decimal-string H1 OHLC/observation
records and bounded bid/ask quotes. It accepts no account, credential, live-mode
or source-permission field. Duplicate JSON keys, nonfinite values, symlink inputs,
unknown fields, conflicting source prices and cross-partition quotes reject.

The146 component derives all published H1/H4/D1 observations from the same H1
records. At each execution quote every due scheduled observation must exist and
be available. At least253 complete prior observations are required in each
timeframe at the first funded quote. Missing children, ambiguous same-clock
publication and source-order backfill make the partition unavailable. No missing
period is filled, removed or turned into zero return.

Quotes must have both source and receipt inside one declared half-open funded
partition. Each endpoint must be the declared last fresh executable quote;
repeated, stale, closed, missing or borrowed marks are unavailable. An observation
after that endpoint but before the partition ends also rejects the partition.
Prior observations can warm each new account, but no prior position, cash,
financing or pause state is carried. Each cell starts with synthetic USD10,000.

These short constructed partitions do not meet the24-calendar-month qualified
study requirement or establish untouched validation. Their labels remain software
partition names; no unseen-market claim follows from them.

## Frozen-control bridge

The controls keep their original118/120/124/125 implementations and entry points.
The bridge accepts only the calendar/availability profile those entry points can
represent: full24-hour UTC-midnight sessions, exact H1/H4 edges, the2000ms
finalization profile and explicitly declared whole UTC closure days. Closure
intervals are split into their declared days; absent sessions are never inferred.

Shifted opens,23/25-hour or partial sessions, unsupported calendar sizes or timing,
source/receipt session disagreement, explicit session flags the old interface
cannot represent, and prices that cannot round-trip through its float fields
leave the affected control cells unavailable with null summaries. CASH follows
the same control-input boundary. Nothing is reanchored, rounded or loosened to
manufacture a comparable control result.

Only the current partition's observable price prefix and execution quotes reach
the legacy input. A later partition's unsupported precision cannot invalidate an
earlier otherwise representable price prefix. The predeclared calendar remains
immutable. The legacy sequence is renumbered locally as its interface requires;
quote source/receipt times and bid/ask values remain exact.

Both conversion paths are bound in prepared artifacts. The bridge compares every
bar's timeframe, span, availability and OHLC, then both original control event
streams' execution timestamps and prices against the new stream. Lineage recipes
are interface-specific, with both versions bound to the same frozen source;
their hashes are not presented as identical or as provider authentication.

The fuller strategy uses148 paper execution. The controls run their original
engines through the retained shared interface. Existing clock, stop and financing
differences remain explicit; no whole-strategy timing/accounting parity is claimed.
Original risk rules, hypothetical costs and conservative loss handling are intact.

## Binding and outputs

Prepared files are limited to known adapter artifacts, with symlinks and foreign
paths rejected. Replay accepts only its expected source event prefix. Checkpoints
bind the prepared partition, candidate, cost profile, cursor, finished state,
source graph, prepared calendar and original inner checkpoint. A rehashed outer envelope cannot
relabel a base-cost account as adverse or a T12 account as CASH. Source, artifact,
cursor, prefix, partition and state changes reject.

Every declared cell is retained. Failed common coverage makes all eight cells in
that partition unavailable. A control-interface limitation leaves the control
cells unavailable while eligible EW_FULL paper cells can still be computed. Each
cell's market status is always `UNAVAILABLE` and market returns remain null.
There is no portfolio sum, automatic strategy selection or qualified-run grant.

Input/source bindings, prepared artifacts and generated account-report hashes are
checked again before the final status is published. Changed inputs, artifacts or
reports abort that publication. Partial output from a failed run is not a final
comparison. The report keeps descriptive paper summaries and original ledgers,
with a hash map identifying its generated account reports.

## Verification

**155 tests passed together, with zero failures or errors, in425.531 seconds.**
The invocation covers38 new comparison checks and117 relevant existing policy,
boundary, cross-accounting, session and preflight checks. Source hashes stayed
unchanged throughout the recorded run.
The source files and graph retained from the prior156-test paper revision are
checked byte for byte, including the unchanged258-test strategy graph and all46
frozen-control bindings. Those full suites are not rerun or added to this run's
test count.

Final review added an explicit match between the paper checkpoint's calendar and
the prepared comparison calendar. The regression constructs an otherwise
self-consistent checkpoint using a different declared calendar and confirms it
rejects. Verification002 is the current155-test evidence. The earlier154-test
run/source remain archived under001; no wave, sizing, cost or exit rule changed.

The new checks cover calendar capability, exact source/bar/quote conversion,
future-price independence, common unavailable partitions, strict endpoints,
checkpoint identity/reconstruction, corrupt inputs/artifacts/reports and admission
remaining closed. The public UTC-calendar example must compute all16 paper cells;
independent rational auditors check every control account and direct original
engine summaries must agree. EW_FULL abstention in that trend example is explicit.

A separate shifted-calendar example must retain12 unavailable control cells and
four computed EW_FULL cells. A separate automatic EW3 long example must derive
one entry and a gap stop through the common adapter; no counts or signals are
injected. Its gap loss must exceed estimated entry risk and latch the pause.
This positive entry coverage is one base-cost account, not a full wave matrix.

All16 UTC-profile paper cells were computed and retained. All12 control accounts
passed independent rational auditing and matched the direct original-engine
summaries. The shifted example computed four EW_FULL paper cells and retained12
unavailable control cells with null summaries and the explicit UTC-boundary reason.
The separate automatic wave account entered once, stopped on a gap beyond its
estimated risk and latched its loss pause. All market statuses remain unavailable.

The [portable verification record](evidence/elliott-session-comparison-149/README.md)
contains the full log, completion and three example summaries. Full source and
generated artifacts remain under ignored local reports:

- [Verification/source summary](../reports/elliott-session-comparison-149-verification-002/verification-summary.json)
- [All16 UTC paper cells](../reports/elliott-session-comparison-149-verification-002/utc-trend/run/comparison-status.json)
- [Shifted-calendar unavailable cells](../reports/elliott-session-comparison-149-verification-002/shifted/run/comparison-status.json)
- [Automatic wave account](../reports/elliott-session-comparison-149-verification-002/wave/report.json)

The generated-artifact inventory identifies104 files totaling281,001,551 bytes.
It excludes itself and its referencing verification summary. Source/archive bytes
and all generated account-report hashes were verified. Large reports, source
archives and runtime artifacts remain outside Git.

```sh
PYTHONPATH=src:tests python3 scripts/elliott-session-comparison-149.py fixture NEW-INPUT.json --case trend
PYTHONPATH=src:tests python3 scripts/elliott-session-comparison-149.py freeze NEW-INPUT.json NEW-FREEZE.json
PYTHONPATH=src:tests python3 scripts/elliott-session-comparison-149.py replay NEW-INPUT.json NEW-FREEZE.json NEW-OUTPUT-DIRECTORY
PYTHONPATH=src:tests python3 -m unittest test_elliott_session_comparison_149 test_elliott_full_policy test_elliott_full_boundary test_elliott_full_crosscheck test_elliott_sessions_146 test_elliott_study_145 -v
```

## Remaining work

The qualified-input runner, source/use/clock/coverage/cost/prior-trial qualification,
genuinely unseen partitions, broader EW5/short/nested/fault acceptance, native demo
reconciliation and new-adapter viewer integration remain unfinished. Unsupported
control calendars remain unavailable. Neither declared OHLC nor these sparse
quotes establish complete intrabar stop paths or true tick-level drawdown.

No market source, acquisition window, account or terminal is assigned or accessed.
No reserved prices, credentials or terminal settings are read or changed. Closed
routes/capture restrictions and protected dates are retained. All16 actual market
cells and order submissions remain unavailable. These are constructed software
checks, not a win rate, market advantage, broker-performance or income estimate.
