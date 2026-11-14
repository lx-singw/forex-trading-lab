# Local permission transport047 protocol — declared before native tests

Fixed date2026-10-07; a new047 authority derives046 exactly by changing only its
declared date/version.046/042 are untouched. This phase has no price/history/order
APIs. Windows transport fixtures inject an explicitly synthetic guard; they are
not evidence of an actual MT5 account check or quote authorization.

Wire v1: little-endian request56 bytes,8-byte FXDL047Q magic,16-byte public phase
UUID,32-byte policy SHA256. Reply84 bytes: FXDL047R,phase,digest,uint32 permission=1,
uint64 issued uptime,uint64 expires uptime,uint64 expires UTCms. Exact lengths,
magic/bindings/integers/date and shared046 receipt bounds required. Production
must request anew each invocation and verify private actual account guards before
and after; the fixture never reads prices. No response/permission inputs.

One local pipe instance with FIRST_PIPE_INSTANCE/OVERLAPPED, message request mode
and REJECT_REMOTE_CLIENTS. Explicit protected DACL admits the current logon SID;
never default/Everyone/anonymous ACL. MQL FileOpen requires generic read/write,
whose mapped rights include pipe-instance creation. Grant only that necessary
mask to the logon SID; max_instances=1/first-instance ownership plus exact peer
process/image SHA/creation time/session/logon checks remain mandatory. This
compatibility choice cannot remove the mapped creation right. Same-user tampering
is outside demonstrated guarantees. Private SIDs/PIDs/pipe names and receipts
are never exported in native fixture reports.

Each operation deadline at most2 seconds; cancellation must be requested AND
observed complete before releasing its OVERLAPPED/buffer/event. If cancellation
does not drain in1 second, retain memory/handles and fail the fixture; an outer
owned-process bound stops work. Windows client verifies server identity, server
verifies client identity. No retries on peer/state/framing/delivery errors. Same
canonical phase reservation cannot restart/refund; an uncertain response burns
the allowance. Native MQL cannot directly call peer PID APIs without DLL imports;
its fixture does not claim independent server identity authentication. A later
native run requires the companion owning the unique endpoint and checking the
MT5 peer; no DLL enabling/settings changes. No production capture is available.

Offline tests cover wire corruption/boundaries/closed schemas and exact047
derivation; Windows fixtures cover request/response, rejected peers/missing pipe,
first-instance collisions, partial/oversized/wrong messages, deadlines, server
death, lost reply, repeated/parallel requests and restart refusal. At most three
development fixture revisions; freeze each revision's exact sources before its
native suite, preserve original outcomes if repaired. No market acquisition
retry/retarget. Full Linux regression once after source repairs. Final source
freeze and one exclusive staged MetaEditor fixture build at most; no compile
retry. No MT5 launch/login/attachment/deployment or native MQL runtime in this
preparation until transport/build evidence independently passes. A manual native
MQL fixture session needs a separate bounded declaration; not an observer rerun.

Review primary Win32/MetaQuotes docs (maximum12 opens/six finds), preserve any
failed opens. Preserve046 snapshot13f03bb324da51b2464b3084eb62802b04dd35c6bce8abda7565efdae4bf1056,
all old failures/six captures/timeout, consumed2025/reservedNov-Dec2026/provider
stops. No timezone correction, clock certification or eligibility promotion;
fresh/annual eligibility/orders false.
