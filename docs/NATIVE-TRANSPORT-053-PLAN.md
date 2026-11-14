# Next offline transport diagnostics — not executed

First verify052 final snapshot and its completion review. Preserve051's one
consumed permission, generic helper failure, empty stopped read, and separate052
native reason23 record. Do not reuse051's phase or reinterpret it as a pass.

Observed facts: MT5 connected; peer/request validation passed; the journal records
one consumption; helper response_written=false; native requests=1 and
receipt_valid=false. Reason23 covers all Decode047 failures, so current evidence
cannot separate missing/partial bytes, binding/schema failure, or receipt expiry.
The helper catches every serving exception into one boolean, preventing exact
stage/error identification. This missing diagnostic is a confirmed source issue;
no particular transport root cause is proven.

Prepare a new offline-tested diagnostic layer before declaring another native
run. Track fixed stages (connect, peer, guard, request read/decode, issue, encode,
reply write, close), strict whitelisted reasons, bounded byte counts and elapsed
durations. Never record raw frames, exception text, account identity or log text.
Expose native reply length and exact pure-decoder rejection category with closed
fields, while retaining all account/receipt/date guards and no quote/order APIs.

Use injected failures to test every stage and cleanup path, one-use burn before
failure, disconnection, two-second IO/receipt deadlines, wrong/short/extra frames,
clock reversal and schema/privacy rejection. Add a fake duplex peer that requires
the entire response before closing; retain cancellation memory until completion.
Do not solve a suspected timing issue by extending receipts, removing guards or
blocking unboundedly. No compiler/SDK/native MT5 fixture in this offline phase.
After diagnosis passes, declare a fresh fixed date/phase and separately budgeted
manual experiment. Do not silently alter the frozen051 fixture.

Official documentation reviewed after052 (two queries):

- [MQL5 FileOpen](https://www.mql5.com/en/docs/files/fileopen) requires FileFlush
  and seeking to the start between pipe writing and reading.051 contains these;
  reason23 does not establish a seek failure (that has separate reason22).
- [Microsoft named-pipe operations](https://learn.microsoft.com/en-us/windows/win32/ipc/named-pipe-operations)
  documents that server FlushFileBuffers waits for client consumption.
- [Microsoft overlapped server example](https://learn.microsoft.com/en-us/windows/win32/ipc/named-pipe-server-using-overlapped-i-o)
  warns that flushing blocks the server while waiting for the client. Therefore
  do not add an unbounded flush as a speculative fix; delivery/close behavior
  needs a bounded reproduction and explicit completion evidence.

Neither documentation identifies the exact051 failure. All clock/cost/coverage/
flags gates, old failed phases, consumed2025/reservedNov–Dec2026/provider stops
remain. Fresh/annual eligibility and orders are false; no return or profit claim.
