# Separate native054 reply diagnosis — 2026-10-07

Original054 final source SHA
16282400c79901ded9bddd0c632382291564c4f070304fcd664d6d1a1cb3339f,
1748 bindings/1629 archive members. Freeze prior closure and new audit/checker/
sealer before one separate existing-log read. Original054 stays failed:
native_transport_rejected; disabled proof passed, enabled arm consumed one
permission, repeat unarmed; SDK/pipe closed and cancellation drained.

The diagnostic identifies reply_write/io_operation_rejected after successful
peer, guard,56-byte request, issue and84-byte encoding. Write returned failure
in94 microseconds, before a pending IO wait; not the2s timeout.84 is attempted
write length, not delivered length. The raw Windows error was not captured.
The original stopped-log read at offset1520 returned zero bytes/rows.

User replied done after the enabled run and Experts Open instruction. A later
metadata-only observation found1950 bytes, last write2026-10-07T07:45:10.234384Z.
Declare exactly one content read of [1520,1950),430 bytes, fixed20261007.log.
Parse only new eight-field FXDL_PIPE054 rows with frozen054 parser. No raw log or
identity export, poll, altered range, SDK/native run/compiler/grant/market calls.
No original collection promotion, refund/reset/retry or repeat arm.

Primary documentation opened before this audit: MQL FileReadArray (returns element
count), FileReadInteger (explicit byte size), Microsoft WriteFile (use GetLastError
on failure). They do not diagnose the exact failing call here. Source/record may
identify native decoder category; distinguish observations from hypotheses.
Existing800 software tests cover the parser; independent checker verifies source
and counters without a second terminal-log read. All older failures, market gates
and reserved-data/provider exclusions stay; eligibility/orders false.
