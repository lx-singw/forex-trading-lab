# Offline transport diagnostics056 results — 2026-10-07

842 tests passed: the existing800 plus42 new tests. One frozen full regression,
zero failures/errors/skips.42 actual pure MQL category/duration cases match
Python through a temporary Linux C++ shim. This is not an MT5 compilation or
test of its blocking FileReadArray wrapper.

The new Windows adapter records fixed operation/error categories and duration,
distinguishes immediate from pending failures, preserves two-second waits and
one-second cancellation drain, retains uncertain IO memory/handle, and redacts
private exceptions. Existing047 security/identity hashing remains inherited.
Injected tests cover immediate/pending write/read errors, failed wait, cancelled
or raced completion, undrained/incomplete/unknown completion, short writes,
count/deadline bounds and cleanup/privacy. No frozen old backend was changed.

84/85-byte single-read models reject returned short/extra/error frames. An84-byte
read can miss an unread suffix, so changing the count is not approved as a fix.
The experimental native wrapper records the read error before cleanup and
measures duration; it does not enforce a timeout while a native call blocks.
The bounded consumption ACK is modeled and tested for exact frame/phase/policy,
guard, receipt and deadline checks. Native ACK IO/sender and long-connect
integration are unimplemented and are not deployment-ready.

Original054/051 stay failed with one consumed permission each;054 native reply
bytes0/code1 and immediate helper write rejection remain. Actual error/root
cause cannot be reconstructed by offline tests. No SDK/native MT5/compiler/
deployment/log-reread/price/history/order or strategy calls in056.

Next prepare a fresh diagnostic phase using original85-byte native read plus
new error/timing measurements, keeping all guards and original protocol bounds.
Do not adopt84-byte read or native ACK without further protocol proof. Read
NATIVE-TRANSPORT-057-PLAN.md before any future preparation. All earlier market
gates,033/035 failures, consumed2025/reservedNov–Dec2026/provider stops remain;
fresh/annual eligibility and orders false. No profitability claim follows
from transport unit tests. See NATIVE-TRANSPORT-056-DESIGN.md for limitations
and official API references.
