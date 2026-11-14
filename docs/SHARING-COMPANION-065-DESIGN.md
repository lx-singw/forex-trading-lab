# Windows sharing companion065 preparation

New separate backend/core/private guard/session source; no062 instantiation,
old phase resets or permission refunds. Verify064 closure2037 bindings/1891
members. Freeze all source before one1091-test regression (1055 prior+36 new).
New native actions are limited to one private local synthetic compatibility
probe and, after successful evidence checks, one reserved signed MetaEditor
compilation of unchanged064 source. No deployment/SDK/MT5 script/log/market/
history/strategy/order/receipt actions in065. Compiler cannot run before tests
and native metadata compatibility pass. First failures remain immutable.

## Backend and guard

NativeFiles065 binds fixed-width Win32 APIs and registers successful handles
before post-call clock checks. It accepts an explicit local parent and either a
dedicated compatibility child or exact future terminal Files child. Both use
exclusive creation, long-path normalization, all-parent reparse rejection,
protected owner-only DACL, single-link identity and held directory handle.
No deletion/rename, fallback path or unrelated file overwrite. It writes84
synthetic064 bytes once, validates under a read seal once, then preserves an
attribute/READ_CONTROL metadata handle sharing read/write/delete. Metadata and
delete controls deliberately have no file-position capability; position=-1.
SetFilePointerEx requires generic read/write access, so they never call it.
[SetFilePointerEx](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-setfilepointerex).

Both successful write/delete control handles also request read attributes and
READ_CONTROL for same-file/owner/path proof. They are opened and closed only;
their write/delete capabilities never mutate a file. Same private identity,
size84, owner/path/reparse/link proof is checked around each control. A normal
MQL observation requires zero helper data readers; synthetic compatibility
explicitly holds ONE helper Win32 reader as a MQL-like stand-in and records its
presence. It cannot pass064's native MQL interval matcher.

FullGuard065 exposes only metadata SDK methods. It queries actual DEMO/USD/
Algooff/visibleEURUSD and stable private account identity. On every guard it
enumerates the unique terminal PID twice, checks native creation/image/session/
logon identity twice, rehashes terminal image twice plus editor and deployed
artifact once each, and checks stable terminal build/root. Nothing is cached
instead of a full check. A failed guard latches stop. Native identity query and
hash code is new; its actual MT5/process/SDK integration is not exercised by
the file-only compatibility probe. Signature trust must bind known signed
image hashes before runtime; equality alone does not establish a signature.
PROCESSENTRY32W uses explicit UTF16 fields and fixed ABI568/offset44.
[PROCESSENTRY32W](https://learn.microsoft.com/en-us/windows/win32/api/tlhelp32/ns-tlhelp32-processentry32w).

LaunchSession065 exclusively writes a source/EX5/terminal/editor hash-bound
reservation, permits one SDK attempt and disabled/enabled launches in order,
and never resumes a phase. SavedRange065 anchors private file identity/offset,
reads one fresh UTF16 range <=65536 bytes and rejects replacement/truncation/
growth/reparse/empty records; no repeat read. Final064 matcher must still verify
two records, exact hold windows, full private proof and cleanup. A single final
saved range gives retrospective disabled evidence, not pre-enabled log proof.
Interactive orchestration, deployed-artifact bootstrap and SDK attachment are
future work; these source components do not authorize a runtime.

## Frozen caps and accounting

Meter065 checks unchanged047 Oct7 date, UTC/monotonic/boot reversal/discontinuity
and900s measured session. Attempt counters burn before calls. Cleanup close/free
counts still increment after expiry and invalidate results if caps are exceeded;
uncertain handles/allocations remain owned until process teardown. No blocking
preemption or guaranteed deadlines, power-loss durability or peer authentication.

Caps: file/token-for-owner opens16, directories1, writes1, reads1, stamps64;
non-cleanup Win32 calls300000; native closes1600, LocalFree2048; guards192,
process opens384, identity tokens384, process snapshots384, process entries196608;
hash reads768, hash bytes103079215104 total/134217728 per file, hash-path stats16384;
SDK metadata queries2048, SDK connections1, manual arms2; one log read/65536 bytes,
one phase-reservation write; security queries512, file properties256, parent
queries512, token queries1024, clock samples610000. Hash reads count Python
stream opens/reads separately from direct Win32 calls; each owned stream closes
through its context. These caps are maximum allowed work, not expected latency.
SDK-internal IO is opaque; one connection cap does not quantify its internal IO.
Compiler metadata/owned staging/log/artifact operations have a separate one
compiler reservation and existing pinned compiler wrapper, outside file meters.

## Native compatibility and compiler

One current-date exclusive compatibility session uses user TEMP, a new protected
child and one84-byte file. It never touches the MT5 sandbox. Pre controls succeed
with only metadata handle, another GENERIC_READ/share-read handle opens alongside
it, held-read controls fail with actual error32, and controls succeed again after
that stand-in closes. One validation read, no further reading. All handles close,
directory/file retained, no private paths/SIDs/file IDs exported. Native report
binds source ledger, passed tests, runner, policy and pinned Windows Python hash.
CreateFile sharing rules and attribute access distinctions are documented;
installed behavior still requires the actual measured result.
[CreateFileW](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-createfilew).

After compatibility passes and its immutable report is checked, reserve one
signed6244 MetaEditor invocation in an exclusive owned build child. Copy only
ForexDemoSharing064.mq5/SharingHold064.mqh/ClockGuard042.mqh/CaptureReadiness060.mqh,
verify copies against frozen source, use existing hidden native compiler wrapper,
check output/log/error/warning counts and bind all build outputs. No settings
changes, retries, deployment or source edits. Preserve any compiler failure.

Next066 freezes interactive runtime orchestration/SDK/bootstrap/log/launch policy
before deployment or user script actions. Fixed064 source expires after Oct7;
later dates require new source/phase. All earlier failures/spent permissions,
market clock/cost/coverage/flags/033/035 failures, consumed2025, reserved Nov–Dec
2026/provider stops remain. Fresh/annual eligibility and orders stay false.
