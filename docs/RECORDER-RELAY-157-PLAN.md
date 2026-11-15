# Recorder relay157 — implementation slice

15 November2026. Authorized continuation of the approved144 disabled-adapter
work, following156. This slice adds a measured-clock owner/relay runner and an
independent reader for156's diagnostic wire. It does not grant native collection.

The runner defaults off before clock, filesystem or channel activity. When
explicitly enabled by a caller it uses the existing143 channel's start/request/
close interface, checks contained start acknowledgement, waits for fresh healthy
142 readiness, and serves sequential requests from one explicit job folder.
The real channel still pins its owner/helper binaries. Verification uses a
scripted channel only; the public exercise CLI has no native-launch option.

Limits are30 seconds including startup,32 readiness probes,256 served requests
(stricter than156's512),4096 service/wait iterations,512-byte request/reply packets,1MiB native journal,
4096-byte native frames and1MiB final relay receipt. Every helper response is
bracketed by runner-owned monotonic readings. Deadline/reversal/freshness/IO/
protocol faults latch stop. There is no restart, reconnect, directory discovery,
catch-up, retry of a failed query or overwrite. Only absence of the next expected
request permits waiting. Blocked APIs cannot be preempted by elapsed-time checks.

An exclusive retained claim file prevents normal append/resume. Failed/partial
files remain. A final exclusive relay receipt records pending/published response
proofs and distinct cancellation, helper-exit, job-close, power-clear/close and
owner-exit acknowledgements. Cleanup is attempted after every start attempt,
including partial startup failure. It has the existing channel's separate bounded
timeouts; those are outside the30-second active budget. No process-name kills.

The reader independently validates hashes, exact frame grammar/order, all33
scalar fields, bounded sessions/commissions/margins, native float bits, query
intents and before/after lease brackets, replay/age checks and completion counts.
It retains raw source clocks, without imposing a UTC conversion. It cross-checks
each native lease against the explicit request/reply files and measured relay
receipts. A native footer alone cannot establish a completed relayed diagnostic.
The missing exported native clock origin remains an explicit proof limitation.

Tests will include full scalar/session/commission payloads, failed/empty metadata,
rehashed semantic corruption, truncated/oversized/unknown frames, missing intents,
bad after-read brackets, stale/replayed/changed helper samples, wrong job/challenge,
clock reversal/deadline, early completion, owner/helper/cleanup failure, partial
writes/fsync uncertainty, existing-output races, links and fresh-job restart.
Invented producer and reader will not share the frame recipe or parsing code.

Preserve156/136 and prior frozen sources. No MT5 deployment/start, account/price
read, helper launch or power-setting change is required by this verification.
No source/provider/dates assigned; October quarantine, consumed2025, reserved/
untouched November–December and closed routes persist. Market admission,138/140
commit integration, native runtime proof and all16 market cells remain open.
Review intended files, record source-bound evidence, commit descriptively and
push to main when this sprint passes its checks.
