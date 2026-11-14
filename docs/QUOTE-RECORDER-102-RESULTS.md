# Quote recorder102 — offline prototype verified

The read-only recorder prototype is implemented and verified with invented
bid/ask observations. It saves source and UTC receipt timestamps separately,
classifies quote-quality problems, and resumes from committed SQLite events.
The formal focused run passed all 33 tests; the corrected active regression
passed all 2,044 tests with zero failures, errors or skips.

## Data-source decision

Close the active H.10 historical route under the present evidence. The completed
099–101 assessments did not establish original 2020–2023 release versions,
actual publication/channel availability, target-period calendar exceptions or
the complete target-file definition and reuse evidence. The verified 2026 euro
quotation direction does not supply those missing facts. Reconsider this route
only if material new evidence arrives; this is a feasibility decision, not a
claim that the evidence cannot exist. No further search or acquisition ran here.

Fresh quotes would support future paper evaluation. They cannot repair the
historical clock, coverage or provenance gaps, establish a historical edge, or
make the old datasets eligible for strategy tuning.

## Implementation and demonstration

See [usage](QUOTE-RECORDER-102-USAGE.md),
[recorder](../src/forex_demo_lab/quote_recorder_102.py), and
[CLI](../scripts/quote-recorder-102.py). Source metadata is fixed to an invented
EUR/USD fixture; there is no broker connection, market-mode switch or order API.

The recorder validates aware timestamps and finite, positive, uncrossed Decimal
prices. It detects duplicates, conflicting identities, stale/future quotes and
decreasing source/receipt clocks. Distinct identities sharing a source timestamp
are retained. Missing quotes remain explicit missing events; malformed input
fields are discarded in favor of fixed diagnostic codes. Long source/receipt
intervals are diagnostic flags, without interpolation or invented market ticks.

The CLI demonstration recorded 14 invented events, closed after seven, and
resumed for the remainder. Six quotes were accepted; one duplicate, one missing
observation, one invalid observation and five rejected observations remain
auditable. Independent read-only SQLite checks verified the expected decisions,
separate timestamps, accepted-quote chronology, event chain and committed head.
These counts are software observations, not trading results.

Each append saves its event and head in one transaction. Resume verifies schema,
metadata, integrity hashes and replayed decisions, rebuilding duplicate identities
and clock watermarks from committed history. A new file is created exclusively;
damaged/existing journals are not overwritten or silently reinitialized. Immutable
policy, event and file-size bounds keep this prototype finite.

## Verification

| Check | Observed result |
| --- | --- |
| Initial development run | 31 passed; retained separately |
| Frozen-source focused run | 33 passed; zero failures/errors/skips |
| Corrected 084R2 active regression | 2,044 passed; zero failures/errors/skips |
| CLI demonstration and independent inspection | 14 invented events; restart and journal checks passed |
| Existing bot/test/script/configuration sources | All 501 retained hashes unchanged |

Tests cover interrupted writes and rollback, restart equivalence, duplicate replay,
clock watermarks, writer-lock failures, multiple recorder instances, corrupted or
rehashed inconsistent history, unexpected schema objects, bounded policy and
refusal to overwrite. The same 43 original 083 and 36 original 084 retired fixtures
remain retired; no new exclusions were added. Existing portable Linux header
compilation checks ran within the full regression. Test-injected compiler/runtime
failures are fixtures, not actual MT5 runs. No MT5 compilation, deployment, runtime,
terminal action or actual broker/SDK connection occurred.

Attempt-specific logs, source freeze, demo database and summaries are retained in
`reports/quote-recorder-102-*`. Final bindings and archive preserve the predecessor
closure and the four prior handoff contents. The three new Python files bring the
retained source set to 504; no previous source was edited.

## Limits and next step

Receipt times are injected for offline tests. Hashes establish local consistency,
not publisher authenticity or clock truth; an earlier valid snapshot or entirely
rewritten history cannot be authenticated by these hashes. Real power-loss
recovery and Windows MT5 integration remain untested. Full-history verification
on every append is bounded prototype behavior, with no throughput or rotation
claim. No market data, returns or profitability evidence was produced.

Next, prepare a source-qualification contract before connecting a collector:
identify a permitted read-only demo feed, verify timestamp/clock and quote identity
semantics, check actual demo account type, and stamp UTC receipt time at the read
boundary. Reconcile disconnects, restarts and data-quality diagnostics before
paper strategy comparisons. A separate market collector must retain honest
source metadata; the invented journal must never be relabeled as market data.
Native090 remains closed; this result does not authorize another native experiment.

Later comparisons require fixed rules and costs, separate development periods
and untouched validation, with qualification gates still enforced. Existing003
costs, 028/030 rules, provider stops and old failures remain. 2025 stays consumed
and excluded; November–December2026 stays reserved and October quarantined.
Automated orders remain disabled and real-money execution unavailable.
