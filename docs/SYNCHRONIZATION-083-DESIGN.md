# Offline synchronization083 integration

This phase implements an injected protocol proposal and pure MQL timing header.
It does not implement a Windows transport or runnable MQL script. No native SDK,
compiler, deployment, terminal log, market, orders or receipt grants. Source072,
075 artifact, 076 schedule, 077 model and spent081 observations stay immutable.

The new protocol explicitly replaces the blind5-second delay with a fresh
holding witness. It preserves the inclusive10-second release-to-hold start gate,
full30-second hold, strict250ms margins and2-second signal freshness. A challenge
sequence is issued after the full before-guard; the peer produces a fresh
snapshot, not an old announcement with a refreshed client timestamp. The lease
stays held with write/delete exclusion until the full after-guard and repeated
same-snapshot/private-identity check. Old077 failed when two guards aged an
already-issued signal. Here both guards remain; freshness starts at the actual
peer response. Native challenge authenticity/boundary/ACL proof remains future
work, never inferred from injected assertions or byte counts.

144-byte exact little-endian signals bind magic, phase83, source proposal SHA,
retained build reference SHA (not a new compiled artifact), private episode,
monotonic sequence/kind, zero padding, issued/deadline and hold start/end. No
partial/trailing/duplicate/cross-source/build/episode signals. Four kinds:
ready, release-to-start-hold, holding, closed. Closed must corroborate a full
30–31-second hold; future native matcher also needs actual private close proof.
No response/ACK receipt authority is granted by these synthetic signals.

Full-guard purpose mapping:

| Existing guard purpose | New location |
| --- | --- |
| Same actual DEMO/USD/connected/Algooff account and owned SDK | Every operation's before/after guard; final guard |
| Uncached helper/terminal creation/logon/boot and image/SDK/source hashes | Same complete guard proof at every call; no cached guard |
| Preparation and command state | Guarded bootstrap, pre controls and ready read before hold |
| One-use arm/launch | Guarded release write; attempt spent before its before-guard |
| Probe and wait5 safety | Guarded fresh holding read; blind wait explicitly replaced |
| Six independent metadata/open operations | All12 full guards retained inside hold |
| Wait35 safety | Before/after guards around bounded clock-checked hold-close wait |
| Post controls and final account check | All20 post-operation guards and final full guard |
| Cleanup after expiry/interruption | Once-owned cleanup independent of guard/clock availability |

Pre/post controls retain metadata-before/open/stamp/close/metadata-after for each
write/delete access: ten operations/twenty guards per stage. Independent controls
retain metadata-before/open/metadata-after: six operations/twelve guards, actual
modeled error32 and no opened handle. Metadata must share all; helper blockers
must be0. Regular84-byte same-file/private-owner/no-reparse/single-link proof,
both file/signal identities and held signal exclusion are required. Signal and
fixture identities are private; reports/markers contain only hashed identity.
Pre/post probe windows keep the same strict margins around the witnessed hold.

The60-second handshake episode begins after guarded pre controls and ends at
the guarded closed witness. Post controls occur afterwards under a separately
declared120-second whole-model cap. This outer cap is new model scope, not a
change to077/072 or the30-second hold. Three clocks must agree within1000ms,
never reverse, and remain UTC Oct8. Fixed96 guards/96 operations/64 polls/64 wait
chunks/64 lease closes/4096 clock samples/one reservation/one owned cleanup;
all native/SDK/market/order/receipt counts0. A blocked call cannot be preempted;
after-return checks reject overrun and still attempt cleanup. Sleeps stay in a
bounded clock loop with full guards around the wait, as in071; not per sleep.

Exclusive/fsynced model reservation prevents same-path restart. Default-off
does not reserve, construct a peer or call guards. Owner exists before factory
entry; a factory can register its peer before interruption. Release is spent
before any attempt, never retried/refunded. Failed leases still receive close
attempts and peer cleanup; unconfirmed cleanup invalidates completion.

Freeze source/declaration/policy/next plan and inherited082 closure before one
full regression: expected1679 tests,43 new,34 C++/pure-MQL header comparisons.
C++ is a portability shim, not MetaEditor compilation or MQL runtime proof.
Then run13 fixed injected evidence cases: normal, observed_guard1611, slow2001,
pending100, stale2001, changed source, changed private identity, real account
after release, blocked-return, wait overshoot, cleanup failure, interruption,
default-off. Independently check success order, guard counts, critical windows,
caps, raw reservations/cleanup and flags. Observed1611ms is a scenario input,
not a bound. Preserve failed pre-freeze model findings in results: zero-cost
guards initially exposed strict-margin edges; explicit bounded margin waits
were added before freezing. No native action was involved.

Separate source/archive/check/review closure follows. Historical033/035/data/
clock/cost/coverage failures, consumed2025, reserved Nov–Dec2026/provider stops,
retired grants, spent markers and070 unknown cause remain. Profit, native
sharing/publication/ACK and eligibility remain unproven/false. No real/contest,
live toggle, martingale, paid service or broker-account creation.
