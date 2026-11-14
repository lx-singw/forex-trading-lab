# Fresh reader and Windows adapter source086

Offline source/callable-table preparation; UTC2026-10-08, fresh phase
86000000000000000000000000000001 and FXDL086S. Same085144-byte layout/windows,
fresh prefix/root/episode namespace; old085 and every older source stay immutable.
Verify085 final a4c4aefb22743ee6d73f7fe05d250fab0f14bfb1710977db0b81eaa962bb2549
(2696 bindings/2491 members/1769 active passing tests) before freeze.

## Reader and ABI

ForexDemoSynchronization086.mq5 uses the retained pure084 codec with a fresh086
prefix, pure085 close policy and fresh WindowsPipe086 DLL declarations. All
eight kernel32 exports use Win64 HANDLE/pointer long64, DWORD uint32, BOOL int32,
primitive refs/buffer arrays; NULL optional pointers are long zero. Imported
GetLastError is explicitly kernel32::GetLastError; MQL errors use ::GetLastError.
The compiler cannot validate external parameters; actual ABI/runtime behavior
remains unverified. A later source-bound MetaEditor build is required.

Default ReadSyntheticEvidence086=false branches before account/clock/file/pipe
calls. Imports are early-bound and may load kernel32 when the program loads,
even if disabled. Therefore no claim of zero library loads for a future loaded
default-off script. This phase never loads that script or changes DLL permissions.
Enabled source rejects non-x64/disallowed DLL use, actual real/contest/tester,
nonUSD/disconnected/Algo-on/changed account or terminal/metadata/date/clocks.
No quotes/history/orders/live toggle/recovery staking.

Client opens only its fresh local pipe with direct CreateFileW, explicitly sets
message-read/nonwaiting state3, and checks client message flags4, max/current
instances1 and state3. Read145 accepts only exact144 complete message; empty
FALSE/error232/count0 polls are separate from requests. Partial/extra/remainder
or other errors reject. Write144/TRUE/zero backpressure rejects without resend.
No pipe FileOpen/flush/seek/wait-for-peer. Modeled finite MQL guards1024/IO512/
read-polls512/request64, empty sleep100ms, three clocks/date/120s whole/60s episode.
No timing bounds are inferred from nonwaiting mode or advisory buffer sizes.

Once release opens relative synthetic.bin read-only/shareREAD in the MT5 sandbox,
checks exact84-byte pattern/size/position, and samples hold_start immediately at
successful FileOpen return before later guards/properties. The timestamp is not
shifted forward after validation. Own-clock close priority precedes each pipe
poll; at30s it checks properties/guards and attempts close once. A30–31s accepted
close can happen without a closed challenge. Late/error close invalidates output.
The source waits finitely for a fresh closed challenge to REPORT success, while
already-closed reader stays closed; no peer request is needed to perform close.
Cleanup attempts owned reader/pipe closes once despite guard rejection. OS/guard/
file-close stalls can still exceed deadlines; physical hold is not guaranteed.

Microsoft primary references: [MQL import/early binding](https://www.mql5.com/en/docs/basis/preprosessor/import),
[external function scopes](https://www.mql5.com/en/docs/basis/function/extfunctions),
[pipe creation](https://learn.microsoft.com/en-us/windows/win32/api/namedpipeapi/nf-namedpipeapi-createnamedpipew),
[pipe state](https://learn.microsoft.com/en-us/windows/win32/api/namedpipeapi/nf-namedpipeapi-getnamedpipehandlestatew),
[pipe information](https://learn.microsoft.com/en-us/windows/win32/api/namedpipeapi/nf-namedpipeapi-getnamedpipeinfo),
[nonwaiting connect](https://learn.microsoft.com/en-us/windows/win32/api/namedpipeapi/nf-namedpipeapi-connectnamedpipe).
The first NOWAIT TRUE connect makes a pipe available, not connected. A later
FALSE/error535 is required; error536 is bounded pending. This choice and close
priority are design inferences, not measured Windows behavior.

## Concrete acquisition source and remaining runtime bindings

Api086 binds fixed-width ctypes signatures to injected MODEL-ONLY tables. It
provides concrete CreateDirectory/CreateFile/CreateNamedPipe, nonwaiting connect,
ReadFile/WriteFile, descriptor/path/ancestor FILEINFO/final-path, raw owner/control/
binary ACL/SID, client PID/process creation/session/token-logon SID acquisition.
WindowsAdapter086 creates private owner-only protected root/file/pipe descriptors,
CREATE_NEW synthetic84 bytes, first local/remote-rejecting message instance, and
share-all root/file metadata handles. CREATE_NEW identities are measured AFTER
creation, then frozen into private Bindings086 before the trailing bootstrap
guard. Only those three identities may be supplied by setup; source/artifact/
policy/episode/root/owner/peer bindings cannot change. No earlier file is reused
or overwritten. No directory deletion or unrelated settings/EA operations.

Every full guard calls uncached account/image/SDK/source guard plus fresh pipe/
peer/ACL/root/file descriptor/path/complete ancestor facts. Temporary handles are
registered before post-acquisition errors/clocks; no helper read/seal can hide in
the API pool (must exactly equal the companion's live handles after inspection).
Original held message and full transaction before/after guards remain as085.
Pipe first-instance/remote-reject flags are facts of the owned creation call,
not fields returned by GetNamedPipeInfo; current type/read/wait/max/instance
counts are queried. No invented query for immutable creation flags.

Calls16384/peak handles16/close attempts4096/allocations4096/token buffer65536
are finite, with4096 three-clock/date checks and unchanged120s time. Raw memory
reads validate pointer ranges, SID/ACL lengths and exact one ACE; uncertain
handle/free cleanup is retained and never retried. Session closes cap8; normal
six controls close four nonblocking control handles plus three base handles.
Independent write/delete errors32 must occur with helper blockers absent.

No native loader/entry is provided; native_entry086 unconditionally rejects.
Actual function tables are rejected before binding. Native runtime still needs
a separately reviewed fresh boot proof and exact full SDK/image/source/helper
guard wiring. The mandatory boot_reader hook is called afresh per peer query;
it is never filled from cached Bindings or a guessed OS boot timestamp. This
source does not implement a native boot-ID query, and declares that gap openly.
Those bindings must be resolved before native admission, not weakened or faked.

## Integration and checks

Fresh Transport086 inherits085 semantics as an explicit derivative, integrates
six ordered pre/independent/post write/delete controls with before/after path
identity checks, full guards, successful pre/post open/stamp/close, independent
error32, no helper seal and250ms margins. Strict duplicate-free redacted parser/
matcher requires default-off and success records, four original canonical frame
kinds, matching actual hold timestamps/counts and once-confirmed cleanup. Pending
frames preserve protocol state. Requests/releases cannot be retried after failure.

Developer targeted checks may refine source before freeze; preserve their actual
results separately. One frozen full suite uses084 R2 active_suite(), retaining
1769 prior tests and adding086 checks. Test raw ctypes buffers/signatures, private
ACL/SID/peer/path/ancestor acquisition, post-acquisition expiry, connect availability,
root collisions, once cleanup, six controls, budgets/protocol/record checks and
portable reader logic. g++ ports cannot establish MQL compilation or DLL ABI.

One declared evidence set: full_normal, full_small_guard, full_observed_guard,
full_wrong_error, full_account_change, full_close_uncertain, full_default_off,
adapter_ready, adapter_absent, adapter_close_uncertain. Full observed1611ms is
a scenario, not a bound or admission. Controls check the episode clock before
and after physical work as well as after trailing guards; expiry cannot start
another physical call. The final developer scenario stops before the last
post/delete control at60870ms episode elapsed (whole99534ms), preserving60s. Preserve all failures and evidence through
085; freeze source/controller/tests/design/policy/next plan before one full suite
and evidence set, audit/seal/review, then update four handoffs.

No native SDK/MT5/MetaEditor/deploy/log/market/order/receipt invocations or grants.
All2s/10s/30–31s/250ms/60s/120s limits persist. Profit/native sharing/ACK/070 cause
unproven;033/035/data/cost/clock/coverage/consumed2025/reservedNov–Dec2026/provider
exclusions and spent markers retained; eligibility/orders false. Next087 unexecuted.
