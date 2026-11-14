# Fresh MT5 reader and Windows adapter source086 results

Prepared a fresh default-off MQL reader, Win64 DLL declarations and concrete
ctypes acquisition adapter source. All verification is offline or uses injected
callable tables; no actual DLL, SDK, MT5, MetaEditor, deployment or terminal log
was used. The native entry rejects unconditionally and real function tables
reject before binding. No market data, orders, receipts or permissions were used.

The reader uses message/nonwaiting mode, exact144-byte messages, bounded empty
polling and no response files, pipe flushes or seeks. Zero-byte successful writes
reject without resend. Its own-clock close precedes pipe reads and acts without
a peer challenge; success reporting still requires the fresh closed challenge.
Default-off performs no account/clock/file/pipe calls. Imports may load kernel32
early in a future loaded script; this phase does not load it or change settings.

The adapter source acquires raw private ACL/SID, current pipe/client modes,
process creation/session/logon, descriptor/path/ancestor identities and exact
ownership. Newly CREATE_NEW root/file/ancestor identities are measured after
creation and bound before the trailing bootstrap guard. No unrelated files are
overwritten or deleted. Temporary resources are owned before subsequent errors;
uncertain closes/free attempts remain unconfirmed and are never retried.
A fresh native boot proof and complete native SDK/image/source/helper guard
wiring remain mandatory open bindings. The injected boot callback is not a
native implementation; there is no cached or guessed boot-proof fallback.

One frozen full active suite passed1830 tests:1769 retained plus61 new, with
zero failures/errors/skips. Three earlier developer runs passed60/61/61 checks.
The first emitted one invalid-escape SyntaxWarning, fixed before freeze; the
later two emitted none. The new controller initially had one unterminated
result-string SyntaxError, corrected before freeze; its subsequent compile and
developer case audit passed. Eleven portable close-policy comparisons and six C++
ports of the actual reader control flow passed. The port confirms own-clock
close with no further peer request, backpressure rejection, actual real-account
rejection, once uncertain close and default-off calls. These are Linux g++
checks, not MQL compilation or Windows DLL ABI verification.

Ten injected evidence cases give3 modeled completions,6 rejections,1 default-off.
Normal and50ms-per-guard full six-control episodes complete with70 full guards,
original canonical ready/release/holding/closed frames, matching redacted records,
write/delete error sequence0/0/32/32/0/0 and once-confirmed cleanup. Their total
modeled durations are30561ms and33111ms. A raw callable-table adapter ready
transaction exercises all23 declared exports,230 injected calls and51 once
close attempts; it completes with no remaining model handles or allocations.

The full1611ms-per-guard scenario FAILS the unchanged60s episode deadline,
with60870ms episode elapsed (99534ms whole modeled duration),61 full/valid guards,
four canonical frames and only five completed controls. The last post/delete
control stops before further physical work at the expired deadline. Cleanup
completes once. This rejects even though the isolated ready transaction in085
passed. The guard duration is an illustrative historical observation, not a
worst-case bound; actual new-composite costs are unknown. No guard/window was
weakened or extended to make the episode pass.

Independent access-denied/error5, changed account and uncertain closes reject.
Missing adapter peer caps at64 connect attempts; initial nonwaiting TRUE means
availability, and later error535 establishes modeled connection. Uncertain
creator close is attempted once and leaves cleanup unconfirmed despite zero
remaining fake handles. Fake handle removal is not proof of native close.

All37 imported-source/header/design/policy bindings and fresh fixture/controller
inputs were frozen before the one full suite/evidence set. Prior0852696 bindings/
2491 archived members were verified; earlier failed083/084/R2 records and R3
correction remain immutable. Source/evidence hashes, archive members and model
counts were checked again at completion. Actual MQL compilation, DLL ABI,
Windows sharing/ACK and native timing remain unproven. Next087 prepares an exact
source-bound build and resolves native boot/guard bindings; it is unexecuted and
grants no native runtime authority. No user UI action is required now.

All2s/10s/30–31s/250ms/60s/120s windows, actual-DEMO/default-off guards and finite
budgets persist. Profit and070 cause remain unproven.033/035/data/cost/clock/
coverage/consumed2025/reservedNov–Dec2026/provider exclusions and old spent
markers remain; performance/annual eligibility and order availability are false.
API references and the precise changed source are in SYNCHRONIZATION-086-DESIGN.md.
