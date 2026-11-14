# Invented supervision140 contract

3 November2026. Compose the frozen138 lifecycle with a synthetic139 helper
port, without native launches or price reads. Default OFF. The port is strictly
in-memory and has no binary-path/process/native option. No future dates or
reserved-price access is introduced. Readiness is a simulated acknowledgement,
not proof of effective or uninterrupted idle-sleep prevention.

A start request includes a random non-identity job token and bounded duration.
Start acknowledgement alone cannot start recording. Require a live, token-
matched report with create/set/readiness acknowledgements on mains power,
valid non-future monotonic observation marker and at most1s status age. Allow
at most10s for readiness; the exact deadline rejects late readiness. The
overall138 duration budget includes startup and reconnect waiting, even though
the frozen138 lifecycle's own origin starts later. Check helper/owner before
context and triple boundaries, including after modeled reads. Require new
context after ordinary138 reconnect/rotation. Do not restart a lost helper.

Observe helper exit, lost readiness/power, bad protocol/token, stale markers,
owner loss, unsafe clocks, account guards and deadline as distinct stop causes.
Abort pending138 work via its public stop API before requesting helper cleanup.
The frozen138 stop reason may be external cancellation; the separate140
journal retains the specific supervision cause and binds138's acknowledged
head/counter. Keep account/identity checks simulated and explicitly unverified.

Persist typed, digest-linked, exclusive supervisor transitions before starting
the helper or lifecycle, with bounded64KiB/32 frames and closure reserve.
Write/flush/fsync failure poisons the supervisor journal and still stops138
and attempts cleanup. Cleanup requests cancellation and confirms helper exit
once each, even when cancellation fails/throws. Acknowledgements are separate;
unknown cleanup must not be called complete. Present frames do not prove fsync
acknowledgement, source authenticity, actual power release or future liveness.
Restart cannot append/resume either journal or claim cross-job continuity.

Owner death is an injected observation here. Actual process-lifetime binding
(for example a native job-object boundary), helper IPC/receipt authentication,
blocked-call containment and power-request effectiveness remain unimplemented.
This model cannot protect against a real supervisor process dying, or certify
that supplied readiness remains current between observations. Do not label its
test results native supervision. No actual139 helper is started by140.

Test delayed/late/contradictory readiness, exact expiry/status-age boundaries,
foreign tokens, future/reversed markers, owner/helper loss during pending work,
pre/post context gating, failed start, cancellation/exit acknowledgement faults,
ledger/lifecycle IO faults, lost helper during reconnect, stale repeated
reports, linked-prefix reconciliation, rehashed invalid transitions and
deterministic fixture-only CLI. Prior136–139 sources stay unchanged. October
remains quarantined, November–December reserved/untouched and orders unavailable.
