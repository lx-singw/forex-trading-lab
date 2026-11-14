# Held message and autonomous close redesign085

Offline preparation only, phase85000000000000000000000000000001, UTC date2026-10-08.
Read085 POLICY and086 PLAN with this declaration. Preserve084 R3 final SHA
0cecf20b988c1f99d1af50ae81715ec7b26a380f3ca2e41a8141f3fcd658202e,
2666 bindings/2463 members, original084 fixture failure and R2 checker exit1.
The failed1611ms084 scenario started75 guards, recorded74 spans and reached
120827ms before release. It did not complete a75th valid span. Finite observed
native082 guard durations are scenarios, never worst-case bounds.

## Changed boundary and explicit grouping

Transport085 retains the083 logical exchange/084 transfer full guard before
and after one bounded pipe transaction. Every guard acquires fresh account,
image/SDK/source/private peer and root/file descriptor/path/ancestor/ACL facts.
The caller's full uncached Guard083 callback runs, then injected inspect() raw
facts are checked during the same composite guard. No account or proof cache.
The native acquisition of those facts is not implemented or measured here.

The response is the original144-byte consumed message copied into immutable
bytes while the physical private server handle remains owned. The lease holds
that boundary across the trailing full guard; it must be closed logically before
another challenge. Physical pipe closure occurs once at session cleanup. No
response file is created, written, opened, stamped or closed; the former file
publication guards disappear with those removed IO operations. No guard around
a surviving sensitive operation is silently dropped. Logical lease close has
no IO and no added physical handle. There is no signal-file identity claim.

The private first-instance local pipe declaration requires message type4,
message read2, nonwaiting mode1, one instance, first-instance creation flag and
remote-client rejection. Fresh client PID/creation/session/logon/boot and raw
owner-only protected DACL/ACE facts are checked every composite. Owned root
and synthetic metadata handles use META/shareREAD|WRITE|DELETE only. Descriptor
and pathname identities, root identity and ancestor chains must agree; no
companion synthetic read/seal/control handle may remain owned. Preparation of
the new root/synthetic bytes and six independent controls remains separate.
This transport module alone cannot establish native sharing or a full episode.

Exactly one message write precedes at most16 read attempts/15 ten-ms waits per
transaction. Nonwaiting empty reads are accepted only as False/error232/zero
bytes/empty immutable payload. No read aggregation: short/extra/message remainder
error234/other errors reject. Buffer145 with exact successful144 bytes rejects
a145-byte message even without234. Zero-byte successful message write is
backpressure, not successful delivery; reject without resend. Release is spent
before its guard/write, including failures. No FlushFileBuffers/FileFlush/seek.
Polling clocks and IO caps are checked inside the transaction; full trailing
guard still applies. Elapsed checks do not interrupt a native call.

085 frames use fresh phase/magic/source/candidate-artifact/episode/sequence.
Protocol state is ready, once-only release, holding, closed, done; pending5 can
only preserve holding/closed state. A response must be issued after the actual
request write completion and remain <=2000ms old AFTER the trailing full guard.
No retimestamp, normalization or fabricated hold times. Freshness,10s start,
30–31s close,250ms independent-control margins,60s episode,120s whole-run caps
remain unchanged. Session guards96/transactions64/writes64/reads256/waits256/
closes8/cleanup1 are finite; the0834096 three-clock/date checks remain.

## Close independent of messages

AutonomousClose085 and pure Synchronization085.mqh choose the close action from
the reader's own clock before any future pipe poll. At30s it attempts once-only
close even with no peer request or with peer backpressure. An uncertain close
is never retried, avoiding numeric handle reuse. A late close is attempted but
cannot be accepted. Full actual-DEMO/default-off account guards surround the
modeled close; clock/account rejection still attempts owned cleanup once and
invalidates success. Guard/OS scheduling/native-close latency may push closure
beyond31s; no physical maximum hold/preemption guarantee is claimed.

This pure policy has no MQL entry point or DLL import. The old084 MQL reader
still blocks; it is retained unchanged and cannot run085. A future fresh reader
must implement nonwaiting acquisition and autonomous priority, reviewed DLL
ABI/permissions if required, default-off before native IO, independently checked
actual account type and clocks, finite ownership and a source-bound build.
Do not infer such a reader exists from this portable header or injected model.

Microsoft documents [message/nonwaiting pipe semantics](https://learn.microsoft.com/en-us/windows/win32/ipc/named-pipe-type-read-and-wait-modes),
[read/wait mode configuration](https://learn.microsoft.com/en-us/windows/win32/api/namedpipeapi/nf-namedpipeapi-setnamedpipehandlestate)
and [pipe flush blocking](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-flushfilebuffers).
PIPE_NOWAIT is a legacy nonwaiting mode, not overlapped/asynchronous IO. Choosing
it for this finite polling contract is a design inference, not native validation
or a claim that calls cannot stall due to scheduling. No buffering defaults
are assumed. Future SDK/full hashes remain expensive and must be remeasured
with new composite proof acquisition before any timing admission.

## Verification declared before freeze

Developer tests before freeze are permitted and separately reported. One fresh
frozen full suite inherits084 R2 active_suite(), including the8 R3 auditor tests
(1728 prior active checks) and the new085 tests. Do not execute retired08343 or
08436 fixture tests, or rerun consumed old action controllers. New tests exercise
account/proof/identity changes, exact messages, freshness after slow guards,
bounded no-data polls, backpressure/no resend, lease ownership, factory/close
interruptions, once cleanup and autonomous empty-peer/overrun behavior. Portable
g++ comparison validates only the pure close policy against Python.

Declared injected evidence cases: default_off, normal, observed_guard,
slow_guard, no_data_then_reply, no_data_exhausted, backpressure, stale,
changed_peer, replaced_path, changed_account, close_uncertain,
autonomous_absent_peer, autonomous_slow_guard, autonomous_scheduler_late.
All dependencies injected, no native outcomes. Report each transport's real
started/valid guard counts separately; never fabricate a missing span.

Freeze sources/design/policy/next plan/tests/controller and complete retained
inputs before one full suite and one evidence set, then audit/seal/review and
update the four handoff files. Failed frozen actions remain immutable and need
separate declared corrections. No new native SDK/MT5/compiler/deploy/log/market/
order/receipt authority. Profit remains unproven; all033/035/data/cost/coverage/
consumed2025/reserved Nov–Dec2026/provider exclusions and prior spent markers
remain. No live-mode toggle or recovery staking.
