# Synthetic MQL sharing064 preparation

064 is source preparation and offline matching only. Freeze source before one
full regression:1017 prior plus38 new tests and114 shared pure MQL/C++ decisions
(28 hold cases and86 synthetic byte boundaries). No native MetaEditor compiler,
SDK, deployment, scripts, saved-log read, quote/history/strategy/order calls or
receipt permissions. The C++ shim tests pure header logic only. Prior063 closure
2011 bindings/1867 archived members and062 native evidence remain immutable.

## Concrete reader

ForexDemoSharing064.mq5 has ReadSyntheticEvidence=false. Disabled code reports
zero IO before checking clocks/accounts or opening anything. Enabled source
requires actual DEMO mode, USD, connected/non-tester/Algooff, visible exact
EURUSD with EUR/USD currencies and stable private account identity. Build,
terminal path and data root are privately compared on every guard; they never
enter output. The future companion must still recheck full signed image hashes,
process, account, logon, boot and sandbox identity on every guard. The MQL
metadata checks cannot establish these Windows proofs and are not substitutes.

The only file is ForexDemoSharing064-64000000000000000000000000000001\synthetic.bin
inside this terminal's MQL5\Files sandbox. Exactly84 deterministic bytes use
(index*41+23)%256 and deliberately lack047 receipt magic. FileOpen flags are
exactly FILE_READ|FILE_BIN|FILE_SHARE_READ. One open attempt, one uchar-array read
and one close attempt per enabled invocation. Require exact sizes84, positions
0 then84, zero native error categories and correct bytes. No request, ACK,
market data, receipt decoding or order API. Native categories are captured
immediately after calls. FileClose returns void; its error category alone does
not prove native release.

Before and after each file operation and finite Sleep(50) interval, full MQL
metadata guards and boot/microsecond/UTC consistency checks run. The session
measured after-return limit is900s. The handle remains open through a30s hold,
at most601 iterations, with a31s maximum accepted measured duration. Overruns,
halt, expired date, reversal, discontinuity or any guard failure stop acceptance
and attempt cleanup. No native interruption/deadline guarantee. Forced script
termination can prevent a final record; that must fail the later audit.

Source is fixed to UTC2026-10-07. It is UNCOMPILED and UNDEPLOYED. A new date
requires a new source/phase, not editing this frozen preparation. Per-invocation
limits do not enforce a cross-invocation launch cap by themselves; the companion
must reserve and count launches and reject extra/missing records. Unexpected
manual invocations may violate the total IO budget; report them as a failure.

## Independent sharing observation

Use six non-mutating Windows open attempts on the same protected file:

| Stage | Write-access open | Delete-access open |
| --- | --- | --- |
| Before MQL opens | succeeds, closes once | succeeds, closes once |
| MQL holding, helper data readers closed | actual Win32 error32 | actual Win32 error32 |
| After MQL closes | succeeds, closes once | succeeds, closes once |

Do not write, delete or rename through those control handles. A helper seal
would itself block write/delete and mask MQL sharing. All six accepted controls
therefore require zero blocking companion handles. A held metadata-only handle
must share read/write/delete and its compatibility must be independently tested
before using it for identity proof. Keep a protected no-reparse directory handle;
check private file identity/path/owner/sandbox/single-link before and after each
operation with full uncached Windows image/account/process guards. Pre/post
successful opens also distinguish ACL denial and uncleared readers from the
claimed MQL exclusion. Error5/access denial or unknown codes never equal32.

The frozen script logs hold-start and hold-end GetTickCount64 values around the
interval in which it keeps its handle. After a separately bounded saved-log
collection, both independent Windows operation intervals must lie strictly
inside those boot timestamps with250ms margins; pre/post controls must lie
strictly outside. Strict ordering, no overlap, one disabled record and one
successful enabled record, exact phase and all cleanup/file/guard/artifact
proofs are required. Missing, duplicate, stale, wrong-phase or malformed evidence
fails. Log arrival time cannot move the hold window. The250ms comparison margin
is declared, not a calibration of this machine's timer; native timing and stable
boot evidence remain required.

GetTickCount64 reports system uptime in milliseconds; MetaQuotes describes
usual10–16ms resolution. Sleep pauses a script and provides halt checks; neither
API promises timely return from subsequent IO. FileReadArray returns elements
read, so uchar items correspond to bytes. FileClose has no return value.
[GetTickCount64](https://www.mql5.com/en/docs/common/gettickcount64),
[Sleep](https://www.mql5.com/en/docs/common/sleep),
[FileReadArray](https://www.mql5.com/en/docs/files/filereadarray),
[FileClose](https://www.mql5.com/en/docs/files/fileclose).

Python match_evidence is an injected audit, with native_mql_verified=False even
on a match. PrivateProof fields are test capabilities, not native attestations.
Same-owner malicious log/process activity is outside owner-only ACL protection;
timestamps do not authenticate a peer. No proof is generated by importing this
module. A future companion must produce and bind actual evidence before an
actual native outcome can be reported.

Next065 prepares that companion and its metadata-only-handle controls, clock/
budget handling, full private guards, exact source/build bindings and exclusive
session/log range. Only after frozen tests/phase/budgets pass may it reserve one
native compiler invocation. No native actions in064. All market qualification
failures, consumed2025, reserved Nov–Dec2026/provider stops and spent prior
permissions remain; fresh/annual eligibility and automated orders stay false.
