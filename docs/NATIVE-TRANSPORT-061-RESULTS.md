# Offline adapter feasibility061 results — 2026-10-07

945 tests passed:909 existing plus36 new, zero failures/errors/skips in one
frozen full regression.28 pure MQL readiness decisions match Python through a
temporary Linux C++ shim. This exercises pure logic, not the uncompiled FileSize
observer or native Windows/MQL sharing behavior.

The new adapter caps readiness observations at901 within900s, repeats guard/
availability before reading, burns one read attempt and latches failures.
Tests reject stale readiness, suffix arrival before/after observations, early
zero/partial/error reads, disconnect, unknown open errors, clock reversal and
overrun. Actual DEMO/USD/Algooff and stable private account/instrument guards are
tested with injected metadata. Diagnostics exclude private identities.

Pipe mode retains the85-byte diagnostic read and never claims a complete
boundary from84 bytes. A regular-file comparison requires continuously held
write/delete exclusion, trusted sandbox/owner/no-reparse evidence and identical
same-handle identity/size/position before and after consuming84 bytes. Missing
proofs default false. In the injected sharing model, existing writers prevent
sealing and sealed snapshots block new writers/deletion; replacement, growth
and lock loss reject. A delayed publication model integrates with unchanged047
one-use issuance and060 bounded remaining-lifetime ACK.

This is not a native repair: MQL sharing, Windows handle/path/ACL/reparse checks,
publication/ACK integration and blocking call limits remain unverified. No
SDK/native pipe/file handle/MT5 compiler/deployment/log-content reread/market/
history/strategy/order actions in061. Original058 stays failed with one spent
permission;059's0-byte/category6/11164us record and060's first failed fixture
remain. Source and evidence closure checked and archived.

Next062 is a separately frozen local Windows sharing probe on synthetic files;
no MT5 or receipt permission, quotes or orders. Read the061 design and062 plan.
Old market gates/033/035 failures/consumed2025/reservedNov–Dec2026/provider stops
remain; fresh/annual eligibility and automated orders false. Transport tests
establish no profit or trading edge.
