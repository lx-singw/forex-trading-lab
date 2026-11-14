# Permission transport047 preparation results —2026-10-07

Implemented a closed56-byte request/84-byte reply protocol, a local Windows
named-pipe backend and a separately dated no-market MQL fixture.666 full software
tests pass (12 new);100 corrupted/boundary frames give identical Python/shared
MQL decoder decisions.046 remains unchanged;047's authority changes only its
explicit date/version. The native fixture defaults ExerciseTransport=false and
has no quote/history/order API. ActualDEMO/USD/Algooff/connection/private identity/
EURUSD guards are present, but are not native-runtime verified in this phase.

Fourteen Windows IPC cases pass: valid/parallel clients, short/long/wrong requests
and replies, rejected client/server peers, lost reply, first-instance collision,
missing/dead server, connect/read timeout and completed cancellation. Each uses
its own synthetic phase and a fake guard; no SDK or price API is imported. Valid
and eight-client parallel cases each return one receipt; all negative cases
return none. Reservations/repeated requests cannot refill after failure or close.
Private process/image creation time/session/logon identities are checked on both
Windows ends; SID/PID/pipe names and receipts are excluded from exported reports.
Remote rejection is configured, not tested using another host/principal.

The fixture compiled in one exclusive local MetaEditor invocation:0 errors,
0 warnings, an independently hash-checked EX5. Numeric exit code and compiler log
are recorded separately. Four staged source/header files match canonical source.
Restricted execution policy is observed unchanged. No terminal launch, attachment,
deployment, account/login/Algo/DLL setting change, MT5 runtime, SDK connection,
quote/history/strategy/order call occurred. The EX5 is staged outside canonical
source and has not been run in MT5.

Preflight history is preserved. Revision1 froze1,404 inputs, then a missing json
import was found statically before native work; its sources/ledger were archived.
Revision2 froze1,409 inputs, passed666 tests, but its native entry stopped with a
sanitized failure before its start marker. Exact original exception/cause was not
retained; subsequent read-only input/metadata/date/entry-boundary checks passed.
No native pipe/SDK call could occur before that marker under the frozen source.
Revision3 adds privacy-safe failure type/errno/source-frame/case bookkeeping and
uses exclusive new output names. Its1,416 frozen inputs precede all14 successful
native cases and the final666-test regression. Both earlier source archives,
original failure and ledgers remain unchanged; the old result is not rewritten.

Six primary opens reviewed Win32 peer-ID APIs, cancellation, pipe creation, token
information and MQL FileOpen. The CreateNamedPipeW page open failed and is preserved
as a failed lookup; implementation also uses the already-reviewed A-variant flag
documentation. These are research reads, not market HTTP requests. Primary links:
https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-getnamedpipeclientprocessid
https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-getnamedpipeserverprocessid
https://learn.microsoft.com/en-us/windows/win32/api/ioapiset/nf-ioapiset-cancelioex
https://learn.microsoft.com/en-us/windows/win32/api/securitybaseapi/nf-securitybaseapi-gettokeninformation
https://www.mql5.com/en/docs/files/fileopen
https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-createnamedpipea
Official cancellation requires observed completion before freeing IO memory;
this backend retains buffers if cancellation cannot drain and fails closed.

Limitations: Windows fixture peers share the test Python process, not an actual
MT5 process. MQL pipe framing,85-byte read/disconnection behavior, compiler runtime
and native account guards remain untested. MQL cannot independently call the
server-PID API without DLL imports; a later cooperating companion must own the
unique endpoint and check MT5's peer. The logon DACL grants mapped read/write
rights needed by FileOpen, including its unavoidable instance-creation bit;
first-instance/max-one-instance checks and peer validation constrain use, while
malicious same-user tampering/storage rollback are outside proven guarantees.
The2-second native connection deadline needs a separately tested lifetime adapter
for human UI steps; it must not be assumed suitable for an armed manual session.

Next NATIVE-PIPE-048-PLAN.md declares a separate bounded native no-market fixture
session, including expected rejection of a repeated enabled run. No real quote
observer is authorized by047. Old042 remains prohibited, old045 six captures and
044 timeout/incomplete stay unchanged. No profit/edge/clock certification or
historical correction follows; clock/coverage/cost/flags/033/035 failures remain.
Fresh/annual eligibility/orders false; consumed2025/reservedNov-Dec2026/provider
stops unchanged.
