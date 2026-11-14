# Existing clock log audit045 results

Capture=true worked. The single bounded offline read found six schema-valid
accepted FXDL_CLOCK042 records after the enabled anchor, each quote_reads=1 and
guard_checks=5. Their GMT labels span18:56:01 through18:58:32UTC2026-10-06.
All six records are preserved; none is selected or discarded. The append region
was6,626 bytes, within the1MiB bound, and its SHA256 is recorded. The audit made
zero SDK connections, new quote reads, script invocations, HTTP/history/order
calls. Prior044 snapshot verification covered1,365 bindings/1,293 archived
members/72 external bindings before this read.

The original044 session remains incomplete and expired; its zero quote count
describes only the records collected by its companion before shutdown. Across
the later audited native records, six quote reads were observed, exceeding the
declared maximum of one. Protocol compliance is false. No single-record relative
clock comparison or retrospective companion completion guard is manufactured.
The audit report's stop_reason=null means bounded parsing succeeded, not that
044 completed or its budget passed. Original outputs are never overwritten.

The screenshot's reopened input dialog does not show what earlier invocations
used. The source defaults CollectClockEvidence=false for a new launch. MetaQuotes
explains that the manually entered input becomes the value for that execution,
and that script launches may show the default again:
https://www.mql5.com/en/book/intro/data_input (reviewed2026-10-06).
Cancel the reopened dialog; no further observer run is requested.

Known safety limitation: the042 native script checks actual account type,
connection, Algooff, instrument, date and identity within each invocation, but
does not enforce a durable cross-invocation capture count. The companion limits
arms and rejects multiple collected records, yet cannot prevent repeated manual
launches. There is no order API in this observer; this discrepancy concerns
read-only acquisition. CLOCK-UI-SAFETY-046-PLAN.md declares design and meaningful
tests of native session-budget enforcement before any future observation.

622 existing software tests passed before044; this offline audit adds no trading
implementation or new test count. Independent record/hash/count checks pass,
while acquisition budget compliance fails. No profit/strategy result, UTC or
historical offset certification, qualification promotion or correction follows.
Clock/coverage/cost/flags and033/035 failures remain; fresh/annual eligibility and
orders false, consumed2025/reservedNov-Dec2026/provider stops untouched.
