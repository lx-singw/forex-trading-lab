# Offline readiness and lifecycle investigation060

Stage059 closure verified: 1899 bindings, 1764 archive members, completion
review and next-plan binding. Original057/058 remains failed, its one permission
consumed, repeat unarmed and SDK/pipe closed. Native zero-byte read took11164us,
category6(other); helper pre-write work took2788977us. An early client close
explains the rejected Windows write, but the cause of that read is unknown.

## Primary-source review

[MetaQuotes' pipe article503](https://www.mql5.com/en/articles/503), linked by
[FileOpen](https://www.mql5.com/en/docs/files/fileopen), demonstrates checking
FileSize until enough data is available, then calling FileReadArray. Its
WaitForRead example sleeps between checks and only exits on availability or
stop/invalid handle; it has no session deadline. This supports testing a
readiness observation before consuming data. The2012 example does not establish
current build6244 behavior, our native error code, or a safe timeout. Do not
copy its indefinite loop or server flush.

[FileReadArray](https://www.mql5.com/en/docs/files/filereadarray) returns elements
read. [FileReadInteger](https://www.mql5.com/en/docs/files/filereadinteger) returns
an integer value with selectable1/2/4-byte width; a returned zero is a legitimate
value, not a byte count or pending indication. Neither interface takes a
caller-specified read timeout. Changing primitives cannot alone guarantee bounds.

The [official runtime error catalogue](https://www.mql5.com/en/docs/constants/errorswarnings/errorcodes)
defines file errors5001 through5027, including5015 read error and5027 end of
file. New060 maps all27 to distinct closed numeric categories while preserving
the older four categories and other/unknown. Categories are version-specific:
the old057 category6 cannot be retrospectively called5027 or any other code.
No arbitrary error strings or raw identifiers are exported. The
[AlgoBook array chapter](https://www.mql5.com/en/book/common/files/files_arrays)
describes EOF for files; it does not prove the behavior of our named-pipe call.

[Microsoft pipe modes](https://learn.microsoft.com/en-us/windows/win32/ipc/named-pipe-type-read-and-wait-modes)
distinguishes byte and message reads and separate client/server handle modes.
A client handle initially uses byte reads even on a message-type pipe. Empty
blocking reads wait for data; nonblocking reads return immediately. Our MQL
handle behavior was not measured, so Windows mode documentation cannot identify
the observed MQL error. Server configuration alone does not certify the client
message boundary. Overlapped completion and cancellation evidence must remain.

## Candidate and limits

transport_lifecycle_060.py is an injected offline state machine, not a native
adapter. Explicit pending observations leave the handle open while guard work
takes2.8–3.2seconds. A zero result from a read is terminal failure and is never
reinterpreted as pending or retried. The model consumes one exact84-byte response
only when its injected backend separately proves the entire message boundary.
FileSize84 or reading84 bytes alone cannot prove that no suffix remains or
arrives later. Without boundary proof the candidate rejects even a valid frame.

The unchanged047 issuer uses an exclusive temporary phase reservation, burns
one allowance before checks and never refunds delivery failures. Issuance follows
the full guards. Waiting before issuance uses the original900second session;
the receipt retains its original2second bounds. Exact frozen047 wire validation
precedes a40-byte frame-hash ACK. ACK uses the remaining receipt lifetime,
without restarting the deadline. Fresh clocks follow every injected operation
and each guard; receipt/clock checks also follow ACK and cleanup. A fixed poll
count prevents endless spinning when clocks do not advance.

Returned operation/guard/cleanup exceptions are redacted. Cleanup failure or
undrained pending IO prevents success and preserves ownership in the model.
Existing056/057 injected Windows cancellation, memory lifetime and event cleanup
tests remain unchanged; the lifecycle model does not implement CancelIoEx.

CaptureReadiness060.mqh has only uncompiled FileSize and byte-value diagnostic
helpers, with immediate error/timing capture. It neither accepts a receipt nor
places orders. Pure C++ tests exercise only its category function. No native
readiness, suffix proof, ACK integration or bounded blocking-call interruption
has been established. Deadline checks after a native function returns detect
overrun but cannot interrupt it. Native deployment remains unavailable.

Zero SDK, terminal, native pipe, MT5 compiler/deployment, log-content rereads,
quotes, history, strategy or orders in060. Actual demo/USD/Algooff/private stable
identity and full image hashes must remain in any future adapter; no cache or
weaker guards. Old clock/cost/coverage/flags/033/035 failures, consumed2025,
reservedNov–Dec2026 and provider stops remain. Transport tests establish no edge
or profitability; fresh/annual eligibility and orders remain false.
