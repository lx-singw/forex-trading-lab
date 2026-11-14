# Offline read/write diagnostics056 — 2026-10-07

055 closure was verified before implementation: 1757 bindings and 1637 ZIP
members. Original051/054 failures, consumed permissions and unarmed repeats
remain unchanged. Stage056 permits offline injected APIs and temporary Linux
C++ pure-header checks only. No SDK, MT5 compiler, deployment, native pipe,
terminal-log reread, quote/history/order or strategy calls.

## Reviewed Windows derivative

`windows_pipe_diagnostics_056.py` inherits frozen047 security, logon DACL,
first-instance/remote rejection, process identity/full image hashing and both
peer checks unchanged. There is no mutable image hash cache. Its IO derivative
keeps ctypes OVERLAPPED/event/buffer lifetime, pending997, connect535,
2000ms maximum operation wait, 1000ms cancellation drain and short-write
rejection. New changes: closed frame/operation limits, immediate last-error
sampling before any further API, fixed stage/error categories, measured duration
(0..3000000us or explicit invalid/over-bound), and conservative retention if
completion cannot be proven. Failed waits are distinct from timeouts. A
completion racing cancellation never repairs a missed deadline. Cleanup may
take the separate existing1000ms drain; it is not an extended receipt window.
Unknown exception text/code and payload/identity are never exported. Event-close
failure is explicit and must reject success when integrating a future service.

The retained tuple stays in the existing047 pending registry, so existing
service cleanup can retain the associated pipe handle. Injected tests clear only
their synthetic tuples afterward; production code never frees uncertain IO.
This is a new candidate adapter, not a modification of frozen047/053/054 or
proof of actual Windows/MT5 interoperability. Manual long-connect integration
still needs its own reviewed derivative in a future preparation.

[Microsoft's error catalog](https://learn.microsoft.com/en-us/windows/win32/debug/system-error-codes--0-499-)
supports categories for5/6/87/109/232/233/234. The
[500–999 catalog](https://learn.microsoft.com/en-us/windows/win32/debug/system-error-codes--500-999-)
supports535/995/996/997. Unlisted numbers map to other; malformed/unavailable
codes map to unknown. A failed operation with code0 remains other, never success.
[GetOverlappedResult](https://learn.microsoft.com/en-us/windows/win32/api/ioapiset/nf-ioapiset-getoverlappedresult)
and [CancelIoEx](https://learn.microsoft.com/en-us/windows/win32/api/ioapiset/nf-ioapiset-cancelioex)
describe completion checks and cancellation requests. Uncertain completion
must retain all memory and the handle.

## Native read candidate and limitations

The new MQL header supplies pure numeric categories and duration bounds, plus
an uncompiled experimental read wrapper. It resets the error, samples the
microsecond clock, calls FileReadArray once for84 uchar elements, samples the
error immediately, then measures elapsed time. It leaves closure to the caller.
No receipt is issued or account proof supplied by this wrapper. It is not
connected to an EA/script or deployed terminal. Category0=none,2=invalid handle,
3=not opened for reading,4=nonbinary,5=read error,6=other,7=unknown. Duration
-1 means invalid/reversed or above900000000us; Python distinguishes these
statuses without exposing unbounded numbers.

[MQL runtime errors](https://www.mql5.com/en/docs/constants/errorswarnings/errorcodes)
define5007/5010/5011/5015. [GetLastError](https://www.mql5.com/en/docs/check/getlasterror)
does not reset the error; ResetLastError is needed before measurement.
[GetMicrosecondCount](https://www.mql5.com/en/docs/common/getmicrosecondcount)
supplies elapsed-time samples. [FileReadArray](https://www.mql5.com/en/docs/files/filereadarray)
returns elements read. Its API has no caller-specified timeout. Measuring a
blocking call cannot enforce an in-call deadline. Report bounds are not a
guarantee that the read returns within that bound.

Synthetic reads compare84/85 requests with zero/partial/extra/disconnected,
fast and delayed replies. There is one read and no partial-frame accumulation
or retry. An exact84 read cannot distinguish an84-byte message from its first84
bytes with an unread suffix unless native message/error semantics establish
that distinction. Consequently this count change is **not approved as a repair**.
Existing85 reads can detect a returned85th byte, but that does not explain why
MT5 returned zero in054. No inference that zero is an expiry or proven timeout.
An alternative FileReadInteger primitive is not implemented; no official
evidence establishes it would cure this failure.

054 helper pre-write work took3197324us after connection. Its receipt lifetime
began after final issuance guards; the2s receipt did not cover all prior work.
The injected delayed read preserves this distinction. Tests also reject ACK
after receipt expiry even when a full frame arrives.

## Bounded consumption acknowledgment assessment

The offline ACK candidate is40 bytes:8-byte fixed magic plus SHA256 of the exact
validated84-byte frame. Both client and server model recheck their supplied
guard and frozen047 receipt/phase/policy/clock validation; the server rejects
missing/partial/extra/mismatched ACK or elapsed time at/above2 seconds. SHA is
binding, not authentication; actual peer identity and guards remain mandatory.
Write completion alone is not evidence that MT5 consumed the frame.

A future implementation must allocate one remaining deadline across write/read
and ACK (no fresh2s for each loop), sample clocks after each guarded blocking
step, fail closed on late ACK, consume no further permission, and close only
after ACK or bounded failure with cancellation completion. This module only
validates injected samples; it contains no ACK IO loop or native SHA/ACK sender.
No claim of end-to-end consumption proof or enforced native read timeout.
The candidate is not ready for deployment.

[Microsoft's overlapped pipe example](https://learn.microsoft.com/en-us/windows/win32/ipc/named-pipe-server-using-overlapped-i-o)
explains why waiting for client consumption through FlushFileBuffers can block
this flow. No unbounded flush is added.

## Evaluation scope

Full existing800-test regression plus new meaningful injection/framing/privacy/
deadline/cancellation tests will be frozen before running. Actual pure MQL
category/duration code is compared with Python in42 cases through a temporary
Linux C++ shim; the native file-read wrapper is excluded from that shim and
remains uncompiled/untested in MT5. No native error for054 can be recovered
retrospectively. Eligibility and orders remain false; clock/cost/coverage/flags,
033/035, consumed2025, reservedNov–Dec2026 and provider stops remain.
