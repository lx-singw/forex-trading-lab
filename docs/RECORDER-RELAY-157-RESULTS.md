# Recorder relay157 — measured runner and independent checker

15 November2026. The [157 slice](RECORDER-RELAY-157-PLAN.md) implements a default-off
owner/relay runner and an independent checker for156's diagnostic journal. All
verification inputs are invented. **No native helper or MT5 process was launched;
no account, actual price, source permission or collection date was accessed or
assigned.**156's immutable false run grant and136's expired window are unchanged.

## Delivered

`recorder_runner_157.Runner` owns one channel's start, health requests and cleanup.
Its default clock measures `time.monotonic_ns()` locally around each request;
callers do not supply receipt timestamps to individual operations. Tests substitute
controlled clocks, including the default-clock call path. The explicit enabled
API can bind143's existing channel; that channel retains its pinned Windows
owner/helper checks. The exercise CLI imports only a scripted channel and offers
no native-launch option. No MT5 launch or deployment facility is added.

The runner claims one existing, explicitly named `Job156-<nonce>` folder, refuses
normal append/resume, validates a contained start acknowledgement and waits for
fresh healthy142 status before serving sequential156 requests. Readiness sample
history carries into serving; polling cannot renew a repeated sample. It checks
response age after storage as well as before it, so delayed IO cannot earn a
published acknowledgement. It retains an unpublished attempt when a response
fails. Missing next requests permit waiting; malformed/partial/failed requests
do not trigger a query retry. Stopped/disabled runners cannot serve again.

| Bound | Rule |
| --- | --- |
| Active budget | At most30 seconds, including claim/startup; equality stops |
| Readiness | At most32 probes, all inside the active budget |
| Served requests | At most256, stricter than156's512 |
| Service/wait loop | At most4096 iterations, even if the clock stops advancing |
| Transport frames |512 bytes per request/reply |
| Native journal |1MiB,4096 bytes per frame;156 grammar/query/tier limits |
| Relay receipt |1MiB, exclusive creation, checked write/fsync/close |

The separate receipt cap is not included in156's native writer reservation.
Checks use regular-file descriptors with no-follow/nonblocking opens on POSIX;
parents are checked for links. No discovery, deletion, overwrite, recovery,
catch-up, order/history API or SDK/pipe route is added. These checks do not
establish a Windows ACL/reparse or hostile same-user security boundary.

Every start attempt reaches cleanup, including partial startup failure. CANCEL,
EXIT/job closure, power-clear/close and observed owner exit remain separate
acknowledgements. An EXIT failure does not skip EOF/close. No process-name kill
or blind retry is used. The existing143 channel has separate cleanup timeouts;
cleanup is outside the active30-second budget. Blocked system calls, writes or
suspension cannot be preempted by this Python loop.

## Independent reconciliation

`native_journal_157` independently parses bounded ASCII frames and SHA256 chains.
It checks the exact context/triple grammar,33 scalar fields, session indices,
commission rule/tier limits, native finite float bits, explicit failures, query
intents, lease timing/sequence/challenges and footer counts. It shares no frame
recipe or parsing code with the invented producer. Raw source clocks remain raw;
wall-marker reversal is reported without assuming a UTC conversion.

`relay_audit_157` independently reconciles all named request/reply files and the
measured relay receipt, including health packets, sample history, receipt times,
publication acknowledgements and cleanup claims. The receipt binds the complete
native file hash and each request/reply hash. Rehashing a changed native journal
and transport files cannot silently retain the original receipt binding.
Only validated, allow-listed status fields are persisted; rejected schemas,
bindings and arbitrary strings are not copied into receipts.

A footer without matching transport and a successful receipt is insufficient.
A failed/absent API result is not zero fees, a closed market or qualified data.
All results explicitly retain `market_eligible=false` and
`native_runtime_certified=false`; nothing is admitted into145/155 or138/140's
commit lifecycle. The reader certifies internal consistency, not a producer's
identity, a true account/power state or an authentic quote.

Final receipt bytes may exist despite missing caller fsync/close acknowledgement.
The offline checker explicitly reports `caller_acknowledgement_known=false`;
the runner's returned acknowledgement is separate. Neither is promoted into a
durable lifecycle commit. Claim/partial files are retained and block resume.

## Verification

**205 targeted checks pass:35 new and170 existing, zero failures/errors/skips.**
The largest declared profile passes with104 source queries,209 leases, all63
session responses, eight commission rules and128 tiers. A normal example has53
queries/107 leases; a failed-metadata example has48/97 and43 failed or absent
responses. All remain invented diagnostics. Tests include rehashed semantic
corruption, nonfinite/native numeric fields, missing intents, replay and age
equality, clock reversal/deadline/frozen-clock bounds, resource limits, startup/
owner/power/protocol faults, cleanup failures, links/FIFOs, exclusive-creation
races inherited from156, partial writes, missing fsync acknowledgement and fresh
job restart. The separate checker CLI is also exercised in fresh processes.

Ten fixed public-CLI cases retain physical files under ignored reports: clean,
failed metadata, delayed readiness, power loss, stale status, wrong challenge,
owner death, partial startup failure, failed power-clear acknowledgement and a
held request. A separate checker process confirms three consistent completions
and seven rejections. These are scripted protocol failures, not physical native
fault tests. Prior170 recorder checks run alongside the new35; unrelated strategy
suites are not rerun. All recorded156 source bindings and46 frozen controls match.
No new MetaEditor build is needed: all156 native sources/build bindings remain
unchanged from its clean isolated compilation.

See [portable evidence](evidence/recorder-relay-157/README.md) for the final source
hashes, declaration, test log, counts and independent outcomes. Full source ZIP,
physical job files and their manifest stay under ignored
`reports/recorder-relay-157-verification-002/`. Earlier001 retains its204-check
revision before status-persistence tightening; it is not mixed into the final
count. UUID challenges vary on replay;
the expected outcomes and source bindings are reproducible, not every receipt byte.

```sh
PYTHONPATH=src python3 scripts/recorder-relay-157.py
PYTHONPATH=src python3 scripts/recorder-relay-157.py --exercise-invented --output NEW-DIRECTORY
PYTHONPATH=src python3 scripts/check-native-journal-157.py --folder EXPLICIT-JOB-FOLDER --job JOB-NONCE
PYTHONPATH=src:tests python3 -m unittest test_recorder_relay_157 test_recorder_lease_156 test_recorder_boundary_155 test_acquisition_138 test_supervision_140 test_helper_health_142 test_native_supervision_143 test_context_recorder_136 test_elliott_study_145 -v
```

## Remaining work

Next verify the157 runner with the pinned native owner/helper and an invented file
producer, under a separate bounded helper-only trial. This can test actual process
cleanup and response timing without starting MT5 or collecting prices. The actual
MQL file-sharing/flush, account-switch, blocked-call and power behaviour remains
unverified. The native clock origin is absent from156's export; the checker bounds
only the visible span. Startup must also fit156's one-second lease exchange;
missing next requests currently terminate by runner budget, not a native stop
acknowledgement. Those operational handshakes need proof before an MT5 trial.

Actual MT5 reading still requires a distinct frozen build and source/date/run
qualification. Preserve156's closed entry and136's expiry. October remains
quarantined,2025 consumed, November–December reserved and untouched,2024 seen
development evidence and2020–23 unqualified. Qualified historical admission/
runner,138/140 native commit integration, broader Elliott acceptance, remaining
viewer/visual review and native reconciliation remain open. All16 actual-market
cells stay unavailable/null. Orders and real-money execution remain unavailable;
no profitability, win-rate or income conclusion follows.
