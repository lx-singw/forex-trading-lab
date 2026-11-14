# Next offline early-read/lifecycle investigation060 — not executed

First verify059 final/completion closure and retain all057/058/054/051 failures,
one consumed permission in each executed phase, native disabled proofs and
unarmed repeats. Never rerun057 or refund/reset its allowance.

Observed057: native FileReadArray returned0 after11164us (measured), MQL error
category6=other, decoder1=wrong length, native reason23. Frozen source closes
its handle immediately after that read, before post-read guards/validation.
Helper pre-write work after connect was2788977us; Windows rejected WriteFile
immediately with category pipe_closing, no completed bytes. This is consistent
with the native client closing long before a reply was ready, and explains
the rejected write. Why the read returned early remains unknown. The exact
native error was deliberately not exported because it was outside the named
whitelist; category6 must not be called a specific MQL or Win32 error.

Research official native-pipe/FileReadArray/FileReadInteger and current runtime
error documentation before choosing a new read primitive or expanding closed
categories. Do not infer undocumented pipe behavior from generic file examples
or guessed error numbers. A new native diagnostic may need a more complete
reviewed code/category whitelist; never arbitrary error strings/account IDs.
Preserve unknown states. No raw or second terminal-log read to recover lost code.

Implement and test an offline candidate lifecycle that keeps the client handle
alive while the server performs realistic2.8–3.2s pre-issuance guard work, then
consumes an exact bounded reply. Do not extend the2s receipt/IO limits: receipt
starts after issuance; pre-issuance waiting belongs to the900s session. Consider
byte/integer read primitives, explicit framing/readiness/acknowledgment protocol
and server-delayed delivery models. Caller deadline checks between operations
do not enforce a timeout inside a blocking MQL function; state this limit and
do not describe a blocking primitive as guaranteed bounded. No unbounded flush.

Test early zero, delayed availability, disconnect, partial/extra frames and
unread suffix, lost response, failed read/write/event close, pending cancellation,
restart/repeated request, clock reversal/expired receipt and privacy. Native
actual acceptance must remain frozen047 exact frame/phase/policy/one permission/
clock bounds plus all actual DEMO/USD/Algooff/identity guards. Do not shorten
image-hash or account checks to make delivery appear successful. No mutable
identity cache, partial-frame acceptance, martingale or order APIs.

Only after an offline candidate is fully reviewed/tested, declare a new current
fixed-date native phase and freeze budgets/source before any compiler/deployment/
SDK/manual trial. Stage060 itself is offline: no MetaEditor, terminal/SDK/pipe
runtime, log content reread, quotes/history/order or strategy calls. Linux pure
header test shims and injected API models are allowed. Preserve failed revision
source and results if tests fail. Existing874 tests/87 new-phase wire frames/
42 pure read-category comparisons and6 Windows cases remain prior evidence.

All old clock/cost/coverage/flags/033/035 failures, consumed2025,
reservedNov–Dec2026/provider stops remain; fresh/annual eligibility and orders
false. This investigation does not establish profitability or a trading edge.
