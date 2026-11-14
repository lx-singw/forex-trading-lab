# Forward capture111 — implementation results

The one-hour read-only collector and linked-run inspector are built, tested,
compiled and deployed. No111 native collection has been run, so hour-scale timing,
native directory/rotation behavior and continuity still need the manual pilot.
The earlier109 result (120 samples in59.535833s) remains its separate evidence.

## Implementation

Six new canonical files provide a self-contained MQL script, shared portable run
state, C++ harness, read-only Python inspector/CLI and tests. The existing107
actual-account and quote guards are reused unchanged. New FXDL111_V1 framing
preserves prior107/109 formats, inspectors, deployments and observed exports.

Default **CollectOneHour=false**. The script reads exact already-visible EURUSD
only on actual DEMO/USD/connected/non-tester/Algo-off and stable private identity.
Identity stays in memory. Startup, read, after-read, rotation and completion guards
stop the whole run on failure; a failed after-read guard discards the quote.
No orders, real-money mode, DLL, pipe, SDK/login, network feed request, symbol
selection or terminal setting change is available.

Fresh nominal computer-GMT date2026.10.12; global limits:one hour,7,200 attempts,
64 files,4MiB output,500ms minimum spacing, including file boundaries. Rotate after
120 resolved valid attempts. Overall origin, counters, last-read time, bytes and
SHA256 chain never reset on rotation. No catch-up reads. Time-limit stop13 can end
the pilot with fewer than7,200 observations; it is not a reason to relax the cap.

Attempts persist/flush before reads. Full frame bytes reserve before IO; failed
writes have no refund/retry and can leave a partial frame/pending attempt.
Each new run uses a new directory, rejects pre-existing run/file paths and never
resumes old state. File handles are unshared and read/write mode does not truncate.
Checksums/flush do not prove producer authenticity, atomic account snapshots,
atomic directory reservation against outside interference or power-loss durability.
Blocked native calls are not hard-preempted.

The inspector validates sequential filenames, cross-file hash/header links,
origin/state continuity, global counts/clocks/bytes and stop/completion rules.
Incomplete final frames/headers and pending attempts remain visible. Missing,
reordered, mixed, malformed or tampered files reject. Raw native price bits, volume,
flags and source labels are preserved; receipt boundaries are separate. Repeats,
equal-time changes, source reversals and receipt gaps are diagnostic. It never
grants market/paper/order admission or silently resumes a run.

## Verification

**84 focused tests passed**, zero failures/errors/skips:38 new111 tests plus46
retained107/109 recorder/schedule tests. Shared account guard48 checks retained.
The actual shared run core passed more than43,000 checks in its portable harness,
including a modeled7,200-attempt/60-segment run and12 real/contest/disconnected/
identity-change scenarios before reads, after reads and at rotation. Global caps,
unsigned extremes, cross-segment spacing, partial writes, pending-state restart,
invalid/late outcomes and terminal-state rejection are covered. These are invented
facts and portable decisions, not hour-scale native runtime evidence.

Three read-only CLI demonstrations independently agree with the library and leave
input bytes unchanged: complete7,200/60-segment invented run, stopped121/2-segment
run and interrupted1-attempt/0-observation pending run. Invented data is explicitly
labelled and cannot enable market/order admission.

Existing MetaEditor compiled in a new isolated stage: **0 errors,0 warnings**,
nonempty22,232-byte EX5, process exit1 retained. Before/after compiler hashes match
for this invocation. No update was installed by the agent. Four matching artifacts
(script, two headers, EX5) deployed only into
**Scripts/ForexDemoLab111-9a123fec6e56**, with no old/unrelated files overwritten.

All518 old canonical source hashes remain unchanged; six new files make524.
The older2,095-test active-suite result is retained; no new full-suite claim.
No native111 script execution, SDK connection, market acquisition, orders, terminal
launch/settings/log/account inspection or support contact occurred in this turn.
Primary MQL file API documentation was read for implementation; no feed request or
licensing outreach. Earlier historical failures, costs/rules, provider stops,
H.10/native090 closures and reserved validation periods stay intact.

## Next

Launch the bounded pilot using [FORWARD-CAPTURE-111-USAGE.md](FORWARD-CAPTURE-111-USAGE.md),
then inspect the closed run and report hour-scale counts, continuity, intervals,
repeats, raw clock differences and spread distribution. Native desktop control is
unavailable, so the launch is a user step. No automatic monitor/schedule was created.

The source/receipt three-hour difference remains uncorrected. Source age, UTC,
complete tick delivery, executable costs and strategy edge are unproved. Private
engineering scope/no-contact direction continues; use rights are not certified.
This collector prepares longer evidence for fixed, chronological, cost-aware paper
experiments; it does not establish profitability or permit automated orders.

API references: [FolderCreate sandbox](https://www.mql5.com/en/docs/files/foldercreate),
[FileIsExist directory/error behavior](https://www.mql5.com/en/docs/files/fileisexist)
and [runtime file error definitions](https://www.mql5.com/en/docs/constants/errorswarnings/errorcodes).
