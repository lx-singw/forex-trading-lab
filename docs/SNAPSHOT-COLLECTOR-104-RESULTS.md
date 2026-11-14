# Snapshot collector104 — offline adapter and journal model verified

Implemented the broker-free collector boundary and separate market-shaped journal
with honest invented metadata. All51 focused tests and all2,095 corrected active
regression tests passed, with zero failures, errors or skips. The CLI demonstration
and independent read-only SQLite checks passed. No market source was connected,
no strategy or profit was evaluated, and no103 admission gate was promoted.

See [usage](SNAPSHOT-COLLECTOR-104-USAGE.md),
[adapter/journal](../src/forex_demo_lab/snapshot_collector_104.py),
[tests](../tests/test_snapshot_collector_104.py) and
[CLI](../scripts/snapshot-collector-104.py).

## Behavior and evidence

The collector accepts exactly fixed invented replay source/clock objects, with
no SDK adapters or callbacks. Its broker entry always rejects. Guards check
injected actual-type enum facts, connection, Algo Trading off, instrument/currency
and private identity around each modeled read. Before failures make zero quote
calls; after failures discard the quote and record a durable stop. Private
identity and arbitrary input/error fields are never saved.

A committed attempt precedes each read. Outcome and head updates commit together;
an interrupted or failed outcome write leaves the prior attempt pending. Both
pending attempts and completed stop outcomes block acquisition after reopening.
No automatic retry/reconnect, latch reset or pending-attempt completion is provided.
Existing files are never overwritten, and damaged/relabelled journals reject.

Raw source seconds/milliseconds, native float bits, declared Decimal conversion,
original flag fields, UTC/monotonic read boundaries and guard-completion clocks
are separate. Repeated snapshots and equal-time changes remain distinct records;
unknown flag bits are preserved. Missing/invalid quotes stay explicit events.
Raw-clock reversals, gaps and late-history model observations remain diagnostics,
without assumed timezone correction, fabricated ticks or source-age claims.

Explicit restart segments retain committed sequence, total attempt count and
wall/raw-clock watermarks. Monotonic values are compared only inside a segment;
restart-gap markers are persisted. Private identity continuity across restart
remains unproven. Recorded model decisions reference only already committed,
earlier received/guarded observations. Late recovered invented data stays hidden
from the earlier decision despite its earlier source label.

| Verification | Result |
| --- | --- |
| Development attempts001/002 |49 then51 passed; both retained, no development failures |
| Frozen focused attempt001 |51 passed; zero failures/errors/skips |
| Corrected084R2 active attempt001 |2,095 passed:2,044 retained plus51 new; zero failures/errors/skips |
| Main invented journal |20 events,8 attempts,6 recorded model snapshots,1 missing,1 invalid,2 decisions,2 sessions |
| Earlier/later decision visibility |[3,5,7] then[3,5,7,11,17,19]; recovered observation11 absent from earlier decision |
| Account-change journal |3 events; quote discarded; persistent stop and restart rejection verified |
| Unfinished-attempt journal |2 events; pending attempt2; restart acquisition rejection verified |
| Retained sources |All505 old hashes unchanged;3 new Python files,508 retained sources |

Meaningful tests cover real/contest/unknown/bool modes, pre/post account changes,
terminal exit, private/error redaction, malformed prices, unchanged/equal-time
snapshots, unknown flags, raw-clock reversals, UTC/monotonic faults, deadline
overrun, late receipts, causal visibility, restart segments, durable stops,
pending attempts, interrupted/disk/lock writes, read/event limits, multiple
instances, exclusive creation, corruption, triggers and market relabeling.
The same43 original083 and36 original084 fixtures remain retired; no new
exclusions were added. Portable Linux header compilation checks ran within the
full regression; existing injected compiler/runtime failures are test cases,
not actual MT5 runs. No actual MT5/native compiler, SDK/terminal connection,
deployment, log/UI/settings action, external request or order occurred.

Independently checked canonical metadata/event hashes, committed heads, native
float/Decimal correspondence, receipt ordering, expected statuses, decision
visibility and stopped/pending state in all three closed databases. The source
freeze, attempt-specific tests/logs and journals are sealed in
`reports/snapshot-collector-104-*`.103 predecessor61 bindings/60 members and
the four prior handoff contents are preserved in the closure.

## Limits and next step

All inputs, clock and guard facts are invented; the journal stays `synthetic=true`.
The market-shaped schema is not a qualified market collector.103 config grants
no runtime permission and is not used as an activation switch. Before/after
checks do not prove atomic native account identity, and injected clocks do not
certify a real machine/provider clock. Type restrictions are not hostile-code
isolation. A late return can be rejected but no in-flight native abort is proven.

SQLite/OS durability and local hashes do not establish source authenticity,
actual power-loss recovery or authenticity of an earlier valid snapshot. Full
history replay on append is bounded prototype behavior, without a throughput,
rotation or Windows MT5 integration claim. Repeated-snapshot duration does not
prove quote age, complete ticks, executable liquidity or per-side freshness.

The next task is a source/runtime feasibility decision: identify a permitted
attachment mechanism and the source-specific evidence needed for a bounded
diagnostic capture. The SDK attach-only claim remains blocked because initialization
can launch/use stored account state; native090 remains closed and old probes
cannot be retargeted. No new connection or external-search plan is declared here.
The old clock disagreement, source rights, delivery/repeatability and quality
gates remain unresolved. Fresh data cannot repair historical gaps.

H.10 stays closed under present evidence.003 costs,028/030 rules, all historical
gates, old failures/provider stops,2025 exclusion,November–December2026 reservation
and October quarantine remain. Broker connection, paper/market qualification
and automated orders remain unavailable; real-money execution stays unavailable.
