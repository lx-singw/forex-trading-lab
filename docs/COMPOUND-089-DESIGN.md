# Compound acquisition feasibility 089

Review date: 2026-10-09 UTC. Phase: 89000000000000000000000000000001.
Historical prototype clock/wire date: 2026-10-08. This is new, injected source,
not a runnable dated reader, native admission or compilation authority. Verify
088 closure hash 87c3f8a2096f94ca78a8d274d4c73196e505f9cee17173b912f1c49371efce5e,
2,791 bindings and 2,580 archive members. Preserve all frozen sources, failures,
spent markers, old gates and excluded data.

## Acquisition changes

Api089 inherits the original per-call before/after clocks, registration before
post-acquisition rejection, once-only cleanup and all caps. For file/directory
security only, one GetKernelObjectSecurity call fills a caller-owned, aligned
65,536-byte buffer and reports required size. Reject failure, overflow or malformed
bytes without retry or growth. Parse copied Python bytes as the documented
self-relative format: revision, control, aligned offsets, bounded SID/ACL sizes,
no overlapping components or unrequested SACL. Retain the original private owner,
protected DACL, single allowed ACE, flags and exact full-access mask checks.
No opaque native output pointer is dereferenced by this parser.

The primary [GetKernelObjectSecurity reference](https://learn.microsoft.com/en-us/windows/win32/api/securitybaseapi/nf-securitybaseapi-getkernelobjectsecurity)
documents the caller buffer, required length, self-relative result and READ_CONTROL
requirement. The [Microsoft descriptor specification](https://learn.microsoft.com/en-sg/openspecs/windows_protocols/ms-dtyp/7d4dac05-9cef-4563-a058-f108abecce1d)
describes offsets and component bounds. The parser reads a returned copy and does
not modify a descriptor. Named-pipe acquisition keeps the old GetSecurityInfo/
length/control calls, following the specific [named-pipe documentation](https://learn.microsoft.com/en-us/windows/win32/ipc/named-pipe-security-and-access-rights).
No generic pipe API support is assumed from a model.

Each compound guard reacquires the complete file ancestry, including the root,
before raw inspection and again at its end. Both chains must match. Four current
root/file descriptor/path proofs retain separate identity, final path, attributes,
links, size and ACL acquisitions. Join those facts with the two freshly matched
ancestry chains inside this single guard only. No ancestor handles or proofs are
cached between guards. Persistent mid-composite replacement/reparse changes reject.
Finite observations cannot establish atomicity or detect every transient change
that is restored between observations; no such guarantee is made.

One fresh bridge checks owner/SDK/library graph, terminal/helper identities,
actual DEMO/USD/same-account/connected/Algo-off/instrument metadata, all nine roles,
40 retained source inputs and the new prototype source before raw acquisition.
It repeats source/image, identity, metadata and graph proofs after raw validation.
Fresh boot corroboration occurs at the bridge start and independently in each
raw pipe-peer acquisition. Nested scopes, detached clock/boot callbacks, changed
SDK/account/source and reentry after rejection fail. No proof-bearing capability
is retained for later guards. WMI remains last-restart corroboration, not a unique
kernel boot GUID; native provider/provenance/capture/timeout work stays unverified.

## Control boundaries

Every physical control open and close retains a full before/after guard pair.
The guard already reacquires the path before and after those operations, so
standalone duplicate path-inspection operations are removed. When a control is
owned, its actual handle's identity/path/attributes/links/size are acquired inside
the guard and compared with the same current file. Its ACL/complete ancestry are
joined from that same freshly proved object in the same scope. Stamp acquired
controls after open and again before close. No cached stamp is carried onward.

This avoids querying ACLs on a DELETE-only control handle, which need not grant
READ_CONTROL; the already-owned metadata handle supplies the current ACL for
the matching object. Desired access/share/creation/flags remain exact and unchanged.
The [file information API](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-getfileinformationbyhandle)
supports identity comparison using volume/file index; [final path](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-getfinalpathnamebyhandlew)
is queried independently. Actual driver/access behavior on each control mode
still needs a separately authorized native check; modeled success is not proof.

The new schedule has 38 real guards/37 raw inspections, not 70 relabeled spans:
two startup, 20 control, eight wire and eight wait guards. A base inspection costs
44 API calls with two complete three-parent chains. An owned control adds two.
All six controls and four canonical frames complete with 1,689 API calls,
3,379 API clock samples, 1,139 bridge clock samples, 38 bridge calls, 456 SDK
queries and 75 boot queries. Original 4,096/96/1,024/128 caps remain. Cleanup
makes seven once-only owned model closes and one SDK shutdown. Default off makes
no API/SDK/guard/source-proof calls.

## Remaining native blocker

These positive episodes use the existing model reader, whose hash callback has
no count cap and no physical cost. This bridge performs 4,100 hash reads: 3,800
role/source reads plus 300 boot-shell/script reads. The available NativeIdentity065
reader uses a different legacy meter with a 768-read cap and an expired date gate.
It cannot be silently reused or given a larger cap. Injecting JUST its unchanged
768-read count predicate into the historical model rejects bridge attempt eight
after seven valid spans and only one completed control; API clocks and SDK/query
budgets are still below their caps. This is not an execution of the old meter or
native reader, and does not bypass its date/bytes/path-stat/process/clock limits.

Thus API/SDK/boot count feasibility is established in the injected prototype;
the current native experiment still cannot proceed under the available reader
contract. Native source/hash/path/process budgets and cost remain open. A fresh
reader/build/runtime is deferred until all guard-acquisition obligations fit.
No native-ready flag is set. Do not treat a source archive hash as a substitute
for individually required current source proofs without an explicit reviewed
change that preserves the actual execution/provenance contract.

Zero-cost and 1ms-per-API model episodes complete in 30,256ms and 31,156ms.
A 100ms-per-API model rejects the 2s response freshness window. Hash, WMI, identity
and SDK costs remain free in those models. Actual latency/cleanup/preemption is
unproven; preserve the old 1,611ms / 60,870ms timing failure and all count failures.

## Verification and closure

31 targeted tests cover parser bounds, full raw/bridge/controls, substitutions,
current account/source/ACL/peer/ancestry changes, callbacks, interruption, uncertain
creator/control close, default off and the legacy hash cap. Preserve developer
fixture failures, then freeze once and run one full 084 R2 active suite and one
24-case evidence set. Audit, seal and review the source/archive/results/handoffs.
No actual DLL/WMI/SDK/MT5/compiler/deploy/log/market/order/receipt calls or grants.
Keep every data/cost/clock/coverage/consumed/reserved/provider exclusion and all
2s/10s/30–31s/250ms/60s/120s windows. Native entry rejects. No new reader, profit
guarantee, real-money path, martingale or user UI action.
