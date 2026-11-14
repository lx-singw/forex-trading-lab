# Forward capture111 — next implementation plan

The109 native retest completed120 guarded snapshots in59.535833 recorded seconds.
This establishes one working bounded recording run, not a strategy edge, complete
market history, source-age/UTC certification or a hard scheduling guarantee.

Next build a separate read-only collector for one explicitly started private demo
run of at most **one hour**, **7,200 attempts**, **64 file segments** and **4MiB
total output**. Collection remains off by default. No order API, DLL, pipe,
SDK/login, symbol selection, new account/service, support contact or settings change.
Use the already-running terminal and actual DEMO/USD/connected/non-tester/Algo-off/
stable-identity guards; private identity stays in memory. Preserve107/109 artifacts.

Use short terminal-local segments with raw source/native fields and receipt
boundaries, chained checksums and strict stop/completion records. Preserve at least
500ms between read starts, including segment boundaries. Do not catch up with
closely spaced reads. Overall time/attempt/byte caps must span all segments, never
reset when a file rolls. Preserve pending attempts and partial segments after faults.
Clock/guard/write faults stop the whole run; restarting requires a new run and
does not silently continue the stopped segment. Keep the source labels raw.

Reuse107-format segments only where their fixed120/60-second/header/date/count
requirements actually hold. Otherwise use an explicitly versioned new format and
inspector; never weaken107 inspection or relabel old files. Assign a fresh policy
date at implementation rather than silently extending old dated diagnostics.

Add meaningful portable tests of rotation, cross-segment spacing and clock ordering,
global caps, account switches at boundaries, disconnects, partial writes, interruption
and separate-run restart. Record linkage without claiming producer authentication
or crash/power-loss durability. Native blocked calls are not hard-preemptible.
Compile/deploy separately only after focused checks; manual native launch remains
necessary because native desktop control is unavailable.

The one-hour pilot should report quality and continuity, not optimize a strategy or
use tiny observed demo spreads as historical/executable cost estimates. Adequate
longer development data would then support a separately specified causal shadow
engine with fixed rules, conservative cost scenarios and untouched future validation.
No performance selection on these one-minute probes. Historical gaps, old costs/
rules/provider stops, H.10/native090 closures and reserved Nov–Dec2026 stay intact.

This plan is prepared, not implemented or run. No automated schedule/monitor or
order execution is authorized by it. The user's no-contact direction continues;
no further support/licensing search is required for private engineering.
