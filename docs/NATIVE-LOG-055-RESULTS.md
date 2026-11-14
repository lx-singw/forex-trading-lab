# Separate051 failure record audit055 — 2026-10-07

Audit passed: True; native reason codes: [23]. Exactly 1 read(s), 430 bytes in frozen range [1520,1950). Sanitized closed records only; no raw log or account identifier exported.

Original054 remains failed: native_transport_rejected. Actual MT5 peer and 56-byte request passed, one permission consumed, Windows rejected the84-byte reply write immediately, response_written=false, pipe and SDK closed and cancellation drained. Its original stopped read was zero bytes/records; this later audit is separate evidence and cannot make the original collection successful. Disabled proof passed; no repeat was armed. No phase reset/refund/rerun.

Reason22 in the frozen native source means FileSeek failed after request flush; reason23 means the received frame failed validation. Other codes retain their exact source meanings. The new helper identifies reply_write/io_operation_rejected in94 microseconds. This is an immediate Win32 operation rejection, not a2s IO timeout. Raw Windows/MQL read error codes were not recorded, so exact cause remains unknown. Attempted84 bytes are not delivered84 bytes.

800 software tests, five Windows lifetime cases and one clean native compilation remain preparation evidence. No new SDK, permission, native run, compiler, quote/history/order or strategy call in055. Next review the observed native branch and add bounded fixed-reason transport diagnostics and offline reproduction tests before declaring another native phase. Frozen051 stays untouched. All earlier failed sessions, raw clock/cost/coverage/flags/033/035 gates, consumed2025, reservedNov–Dec2026 and provider stops remain; fresh/annual eligibility and orders false.
