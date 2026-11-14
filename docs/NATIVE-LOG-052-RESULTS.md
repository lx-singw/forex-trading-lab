# Separate051 failure record audit052 — 2026-10-07

Audit passed: True; native reason codes: [23]. Exactly 1 read(s), 362 bytes in frozen range [726,1088). Sanitized closed records only; no raw log or account identifier exported.

Original051 remains failed: native_transport_rejected. Actual MT5 peer and 56-byte request passed, one permission consumed, response_written=false, pipe and SDK closed and cancellation drained. Its original stopped read was zero bytes/records; this later audit is separate evidence and cannot make the original collection successful. No repeat was armed. No phase reset/refund/rerun.

Reason22 in the frozen native source means FileSeek failed after request flush; reason23 means the received frame failed validation. Other codes retain their exact source meanings. A generic helper exception was reduced to native_transport_rejected; its exact failing operation cannot be recovered from that report. Do not infer a proven Python exception from a native code.

742 software tests, five Windows lifetime cases and one clean native compilation remain preparation evidence. No new SDK, permission, native run, compiler, quote/history/order or strategy call in052. Next review the observed native branch and add bounded fixed-reason transport diagnostics and offline reproduction tests before declaring another native phase. Frozen051 stays untouched. All earlier failed sessions, raw clock/cost/coverage/flags/033/035 gates, consumed2025, reservedNov–Dec2026 and provider stops remain; fresh/annual eligibility and orders false.
