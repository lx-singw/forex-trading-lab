# Fresh input135 contract plan

Reserved 24 October 2026. Preserve all623 previous source/config/test files,
68 native inputs, earlier evidence and the four handoff bodies. This phase
implements an offline, invented-input contract prototype; it collects no data
and converts no existing native capture. Real/contest execution and automated
orders remain unavailable, with no live-mode or qualification override.

Use one ordered run with causal clock, contract/cost, calendar and quote events.
Record when each event becomes known on one monotonic collector clock. Receipt
UTC bounds, source-label-to-UTC offset bounds and validity scope must have
separate explicit bases: unknown, declared_assumption or invented_measurement.
The last basis describes synthetic test measurements only, never authentication.
Keep original source labels/native bid/ask bits and declared post-marker delay
bounds. Unknown delay or expired calibration must not become zero quote age.

Propagate integer microsecond intervals with outward rounding for drift.
Age lower = availability lower minus source upper; age upper = availability
upper minus source lower. Distinguish definite/possible future source time,
definite/possible stale age and usable bounds inside0..2,000,000us. Do not
substitute repeat duration for age. Preserve gaps, repeats, reversals, changed
same-source payloads and clock-bound discontinuities without sorting or repair.
Only an unambiguous whole availability interval can establish an H1 bucket or
an open session under the declared bounds; sessions are half-open intervals.

Bind explicit per-run hypothetical contract and base/adverse cost profiles to
the unchanged113/114 model. Unknown, missing or expired terms remain distinct.
An empty known session list means closed, while an unknown calendar stays
unknown. No separate127/128 account/contract observation is silently joined.
Usable invented input is a software result, not strategy or market admission.
Valid quotes remain visible to a future position-risk consumer even when
unsuitable for new input; gaps/clock changes request history review. No risk
engine, simulated position, order or P&L is constructed in this phase.

Validate strictly bounded JSON, event schemas and chronology. A rejected event
must not partially mutate state. Immediate exact ack replay is idempotent.
Checkpoints bind input/policy/source, cursor and causal chain; restore rebuilds
the committed prefix rather than trusting arbitrary serialized derived state.
Changing a valid future suffix cannot change earlier verdicts. No exactly-once
external-side-effect promise; consumer/cursor persistence still needs an atomic
joint commit or consumer idempotence.

Freeze policy, implementation, CLI, tests and invented case inputs before
testing. Cover positive bounded-assumption input, unknown/expired timing and
terms, interval and session boundaries, drift rounding, post-marker delay,
gaps, source anomalies, clock resets, late context, duplicate delivery, invalid
schemas and checkpoint recovery. Demonstrate deterministic CLI/library output
on the fixed invented matrix; retain all failures if repairs are needed.
Recheck old hashes and preserve source/evidence closure and handoff. October
stays quarantined; November–December reserved/untouched;2025 consumed; closed
routes and dated native scripts remain closed. No MT5 action is needed.
