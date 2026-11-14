# Offline adapter feasibility061

Verified060 revision2 closure:1933 bindings/1795 archive members, complete1917
frozen-input coverage and next061 plan. The first060 failed fixture/source and
all original057/058/059 failures and consumed permissions remain preserved.
No SDK, native pipe/file handles, MT5 compiler/deployment, terminal log content,
quotes/history/strategy or orders in061. Models and Linux pure-header shims only.

## Reviewed API contracts

[FileSize](https://www.mql5.com/en/docs/files/filesize) exposes a byte size and
GetLastError for errors; it does not certify a pipe message boundary, future
arrival, or call timeout. The declaration uses ulong although its return-value
prose says int; reject oversized/invalid observations, do not rely on a cast.
[FileSeek](https://www.mql5.com/en/docs/files/fileseek) reports success/failure
but has no caller timeout. Neither establishes our failed057 error's identity.

[FileOpen](https://www.mql5.com/en/docs/files/fileopen) permits sandboxed files
and named pipes, and requires flush/seek between pipe direction changes.
[FileFlush](https://www.mql5.com/en/docs/files/fileflush) returns no value and
flushes buffered data; its documentation exposes no timeout. A flush-based
consumption handshake cannot be called bounded. Existing057 flush/seek/read
failure remains unchanged; do not deploy another indefinite flush.

[PeekNamedPipe](https://learn.microsoft.com/en-us/windows/win32/api/namedpipeapi/nf-namedpipeapi-peeknamedpipe)
reports available and message bytes without consuming them. It can block on
synchronous handles in a multithreaded process. A Windows server peeks incoming
client bytes, not the client's unread server reply. MQL FileOpen's handle is not
a documented Win32 HANDLE. No DLL imports, handle reinterpretation or guessed
PeekNamedPipe substitute are introduced. Client/server read modes are separate
as documented in [pipe modes](https://learn.microsoft.com/en-us/windows/win32/ipc/named-pipe-type-read-and-wait-modes).

[MQL file flags](https://www.mql5.com/en/docs/constants/io_constants/fileflags)
offer read/write sharing. Opening read-only attempts an existing file; opening
for writing can truncate it. No write flag, shared-write or common folder is
needed for a future terminal-local response snapshot. These flags alone do not
prove actual Windows sharing, deletion behavior, reparse handling or owner.

[CreateFileW sharing](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-createfilew)
requires compatibility with existing handles. Omitting share-write blocks new
writers and conflicts with existing write handles; omitting share-delete blocks
delete/rename access. Sharing remains in effect until the handle closes. This
suggests a regular-file alternative: close the producer's writer, acquire a
read-only handle denying write/delete, verify exact size/identity and retain
that handle while the client validates the receipt and ACK. This is an inference
from the documented sharing contract, not evidence of MT5 behavior.

## Finite readiness experiment

The pure061 decision allows at most901 observations within the original900s
session:0..83 bytes wait,84 is a read candidate, more than84 stops, any error or
invalid state stops. Before consuming, repeat the full guard and availability
check. A reduced size or newly arrived suffix rejects the stale observation.
Burn the one consumption attempt before read and latch all failures; never
retry a zero/partial/error read or infer missing-file/pending from5004.

The uncompiled MQL observer measures a single FileSize call and session elapsed,
captures the error immediately into060's closed categories, and returns a pure
decision. It neither loops indefinitely nor reads/accepts a receipt or emits
orders. A future caller must enforce901 probes, fixed date, UTC/boot/monotonic
clocks, cancellation/cleanup and full guards. Checks after return detect an
overrun; no function here can interrupt a blocking native call.

Pipe comparison preserves the original85-byte diagnostic read. Returned84
bytes still produce boundaryFalse, so060 refuses ACK/receipt acceptance. A
length header, checksum, commit trailer or repeated size snapshot detects some
corruption but cannot prove no later/unread suffix on an open byte stream.
The arrival-race tests explicitly retain this failure instead of relaxing it.

## Regular-file comparison

The injected regular branch requires an opaque same-handle identity, size84,
position0, and independent proof of writer/delete exclusion, sandbox/owner and
reparse rejection. Proof defaults are false. Read exactly84 once, then repeat
the full guard and check identical identity/size, position84 and retained
exclusion. This gives a complete-file boundary in the model; the unmodified060
lifecycle still performs frozen047 phase/policy/permission/clock validation and
its ACK within the remaining2s lifetime. Publication waits before issuance use
the900s session; guard work never gets a cached identity or reduced image hash.

The sharing compatibility model checks both existing-access versus new-sharing
and new-access versus existing-sharing. An existing writer prevents acquisition
of the proposed seal; a seal denies subsequent writers/deletion. This is not an
OS lock test. Native handle ownership, MQL share mapping, trustworthy publication
and ACK transport, local-only paths/ACLs/no-reparse verification and crash
cleanup remain unimplemented. Same-logon owner trust remains a limitation.

Snapshot boundary evidence must stay held through receipt/ACK/cleanup; merely
hashing a mutable file or observing the same size twice is insufficient. Old
one-use authority/reservations and frozen047 acceptance are unchanged. No
regular-file transport is deployed, and native_adapter_ready remains false.

Next062 measures local Windows file-sharing on synthetic bytes only, after a
fresh source/date/budget freeze. That separate experiment cannot certify MQL,
authorize a receipt/quote or activate capture. All clock/cost/coverage/flags/
033/035 failures, consumed2025, reservedNov–Dec2026 and provider stops remain.
Fresh/annual eligibility and automated orders false; no profitability evidence.
