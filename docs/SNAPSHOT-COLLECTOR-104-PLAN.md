# Snapshot collector104 — broker-free adapter and journal model

Read CONTEXT.md, PLAN.md and103 qualification contract/results. Verify103 closure
61 bindings/60 archive members and505 retained source hashes before implementation.
Preserve the four handoffs and predecessor evidence; no505 old source or frozen
102/103 file edits. No external research, source acquisition, provider retry,
terminal inspection/UI/settings, SDK/native/MT5/compiler/deployment or orders.
Existing portable Linux compiler checks may run within the offline regression.

Implement a separate standard-library broker-free collector boundary and SQLite
journal, CLI demonstration and meaningful tests. Accept only concrete invented
replay source/clock objects; do not accept SDK adapters or broker callbacks. The
broker entry always rejects without importing/querying/initializing anything.
No real-mode, feed-permission or admission bool toggle.103 config is not consumed
as runtime permission, and no admission gate is promoted by model results.

Use market-shaped records with fixed honest invented104 metadata, synthetic=true,
raw source seconds/milliseconds and exact native float encoding plus declared
Decimal text conversion. Do not relabel invented102 or104 as market data. No
provider tick ID, UTC/source-age/per-side freshness or tick-completeness claim.
Retain repeated polls, equal-time changed snapshots and original flag bits.
Missing/malformed observations get fixed codes without arbitrary payload text.

Injected demo-mode/connection/Algo-off/instrument guards surround each read;
private model identity is compared only in memory and never serialized. Before
guard failure means zero quote reads; after guard failure discards the quote and
stops. Read-boundary UTC/monotonic clocks are separate from guard completion.
Detect reversals/jumps/deadline overrun, without claiming in-flight abort ability.
Raw source-clock reversals, repetition and long gaps stay explicit diagnostics.

Persist an attempt reservation before a read and its outcome atomically afterward.
An interrupted/pending attempt blocks further acquisition after resume. Durable
outcome stop latches also survive restart; no automatic reconnect/retry/reset.
Exclusive creation, strict schema/metadata/replay/head/hash checks and bounded
policy/events/file sizes prevent silent replacement/reinitialization. New explicit
restart segments retain committed sequence/read budget and wall-clock watermarks;
monotonic values are never subtracted across segments. Persist restart-gap markers.

Test causal visibility using recorded model decisions after observation commit;
only prior committed observations with earlier receipt/guard boundaries are
visible. Late-history invented observations retain their later receipt, without
calling any history API or fabricating prior availability. No strategy/fill/P&L.

Test real/contest/unknown/bool account modes, account changes, terminal exit,
clock faults, equal/repeated/raw-clock-reversed snapshots, late receipts, session
boundaries, global read limits, interruption/disk/lock failure, pending/stop resume,
corruption and market relabeling. Save development attempts/failures separately.
Freeze source after repairs, run focused tests and corrected084R2 active regression
(same43 retired083/36 retired084; no new exclusions), and independently inspect
the invented CLI journal/evidence. No blanket discovery or unnecessary reruns.

Seal new source/test/demo evidence and closure, preserving prior handoff bytes
before prepending the latest status. H.10/native090 remain closed,103 safe-attach/
permission/clock/runtime gates unsatisfied, and broker/paper/order admission false.
Old failures/provider stops,003 costs,028/030 rules, historical gates,2025 exclusion,
November–December2026 reservation and October quarantine remain. Model persistence
does not prove native behavior, trusted clocks, source authenticity, production
throughput, power-loss recovery or profitability.
