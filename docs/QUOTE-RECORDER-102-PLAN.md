# Quote recorder102 — offline receipt journal

Read CONTEXT.md, PLAN.md and101 results; verify101 closure and501 retained source
hashes before implementation. Close the active H.10 historical research route
under the present evidence: dated availability, original versions and target-file
definitions/marks remain unverified. This is a project feasibility decision, not a
claim that the evidence cannot exist. Reconsider only on material new evidence.
No further external search, file acquisition, provider retry or native experiment.

Implement an isolated standard-library offline bid/ask recorder, a demo/inspection
CLI, invented fixture and meaningful tests. Keep existing501 source files unchanged.
Record explicit source labels/timestamps and UTC receipt timestamps separately.
Use fixed invented-source metadata; no market eligibility, real-mode or connection
switch. No credentials/account identifiers, SDK/network/process/terminal adapter,
order API, strategy execution or profit calculation in this prototype.

Validate types, finite positive uncrossed Decimal prices and aware timestamps.
Detect missing quotes, staleness/future source times, decreasing receipt/source
clocks, duplicate identities and conflicting duplicates. Preserve distinct quotes
with equal source timestamps. Flag long source/receipt gaps as diagnostics rather
than proof of a missing market tick; never interpolate or carry quotes forward.
Discard malformed input fields; save fixed diagnostic codes instead of arbitrary
payloads. Receipt time is injected solely for the offline fixture; a later qualified
collector must assign actual receipt time at its own acquisition boundary.

Persist events, statuses and integrity chain in one SQLite transaction per append.
Exclusive file creation, bounded policy/events/file size, schema/integrity checks,
immutable source metadata and strict resume prevent silent overwrite/reinitialization.
Recover from committed events, without a separate checkpoint that can diverge.
Exercise interrupted writes, rollback, corruption, concurrent recorder instances,
duplicate replay and restart equivalence. Hashes check local consistency only,
not publisher authenticity or timestamp truth. SQLite/OS durability assumptions
remain; no power-loss guarantee or production-scale claim.

Run focused tests and the invented CLI demo with a restart, then freeze source
and run the corrected084R2 active regression (retain the43 original083 and36
original084 retired fixtures; no new exclusions). That suite includes existing
portable Linux header compilation checks; no MT5/native compile/runtime/deploy.
Save attempt-specific reports/logs and hashes without overwriting prior failures.
If a failure requires edits, preserve its attempt and freeze a new revision before
the necessary rerun. No blanket unittest discovery outside the corrected selector.

Seal results, predecessor evidence, test/demo evidence and new-source hashes.
Preserve four handoffs before prepending the new result. Existing003 costs,
028/030 strategies, history gates, provider stops,2025 exclusion,Nov–Dec2026
reservation/October quarantine and native090 closure remain. Orders disabled,
real-money execution unavailable. Connecting a provider and comparing strategies
remain subsequent steps requiring qualified inputs; neither runs in102.
