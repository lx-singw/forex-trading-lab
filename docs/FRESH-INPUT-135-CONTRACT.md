# Fresh input135 contract

This is a bounded offline prototype for **invented fixtures only**. It has no
native-data conversion, broker/SDK/network interface, strategy entry, financial
simulator or order placement. Its positive result means one invented quote
meets declared input bounds; it does not qualify a feed or a strategy.

The JSON header has exactly `schema: fresh_input135_v1`,
`kind: invented_fixture`, `run` (integer1..64), `symbol: EURUSD` and `events`.
The fixture is at most8MiB and1..20,000 events. Event sequences start at1 and
are consecutive. All `observed_us` values use one run-local monotonic collector
clock, are nondecreasing and at most90 days from its origin. A monotonic reset
requires a different run; it cannot be repaired by sorting. The numeric run
label is an invented test case label, not an account identifier.

Each event has `type`, `sequence` and `observed_us`, followed by exactly its
type-specific fields. Unknown fields, booleans in integer fields, invalid
bounds, nonfinite values, duplicate JSON fields and native/market headers
reject. Context is used only after its event has been acknowledged; later
context never repairs earlier verdicts.

| Event | Additional fields |
| --- | --- |
| clock | receipt_basis, receipt_utc_us, receipt_drift_ppm, source_basis, source_to_utc_us, source_label_range_msc, valid_for_us |
| terms | contract_basis, contract_profile, cost_basis, cost_profile, valid_for_us |
| calendar | basis, sessions_utc_us, valid_for_us |
| quote | acquired_us, source_msc, bid_bits, ask_bits, raw_flags, delay_basis, post_marker_delay_us |

A basis is `unknown`, `declared_assumption` or `invented_measurement`.
The last label means a synthetic test measurement, never native evidence,
producer authentication or permission to claim certified UTC. An unknown
quantity must be null. Each bounded numeric interval is an inclusive two-item
integer list `[lower, upper]`, with lower <= upper.

Clock receipt UTC bounds apply at that clock event's observed marker. Drift
is an explicit assumed bound in parts per million, at most1,000ppm. For a
later marker with elapsed delta, receipt bounds widen outward by
`ceil(delta * ppm / 1,000,000)` microseconds on each side. The validity window
is inclusive and at most one hour; no extrapolation past its end is allowed.

`source_to_utc_us` gives the additive interval from the original source
millisecond label to UTC microseconds. It must cover **every source label in
source_label_range_msc**, not merely the calibration instant. Source offset
bounds are limited to +/-24 hours. A label outside their declared range is
unknown for age calculation. This is a hypothetical mapping in an invented
fixture; it does not apply a correction to the existing132 exports.

The quote retains original IEEE754 bid/ask bits as16 uppercase hex characters,
raw flags and the unmodified source millisecond label. Prices must be finite,
positive and not crossed. `acquired_us <= observed_us` preserves the acquisition
marker separately from the collector's completed-event marker. Post-marker
delay is separately bounded, at most60 seconds, or unknown. It represents an
explicit delivery/processing assumption after that marker; it is not silently
zero and is not a latency measurement. Its upper endpoint must still fit the
clock, terms and calendar validity windows.

Availability bounds map `observed_us + delay` through the receipt calibration.
Source bounds are `source_msc * 1000 + source_to_utc_us`. Then:

```text
age_lower = availability_lower - source_upper
age_upper = availability_upper - source_lower
```

Unknown inputs yield unknown age. An upper bound below0 is definitely future;
a lower bound below0 is possibly future. A lower bound above2,000,000us is
definitely stale; an upper bound above that limit is possibly stale. An
interval wholly inside0..2,000,000us is within declared bounds. Both endpoints
must also fit one UTC H1 bucket before one receipt-hour index can be assigned.
These are interval judgments under the supplied invented assumptions, not
point estimates, clock certification or measured executable quote age.

Terms must explicitly select `baseline_113` and `base_and_adverse_113` when
their respective bases are known. Otherwise their profiles must be null.
The policy binds the unchanged hypothetical Config and113 cost scenarios;
it does not import the separate127/128 observations. Terms have their own
validity window, at most24 hours. Unknown/expired terms cannot supply zero fees.

A calendar contains at most32 ordered, disjoint UTC session intervals.
Sessions are **half-open**, `[start, end)`. The entire inclusive availability
interval must fit inside one session; touching its closing boundary is
ambiguous or closed, not open. An empty known session list means closed;
an unknown calendar uses null. Its validity window is at most24 hours. The
calendar is an explicit invented assumption, not a certified holiday schedule.

Quote verdicts retain sampling gaps over2 seconds, repeated snapshots,
reversals, values below the source-label high-water mark and changed payloads
with the same source label. A repeated observation is not an idempotent ack
and its duration is not age. Clock recalibration increments a generation and
reports initial, overlapping, disjoint or unverifiable bounds. Overlap is a
consistency observation, not proof that two clocks are identical. Disjoint or
unverifiable mappings and quote continuity faults request history review.

Every structurally valid quote remains in the report for a future position-risk
consumer, even when unusable as fresh strategy input. This prototype does not
itself mark, exit or manage a position. A history-review signal must be handled
by that consumer; subsequent usable input does not restore warm-up or grant
entry permission. Spread, positions, stop handling, costs and loss limits
remain responsibilities of the unchanged downstream engines, which are not
constructed here. A stop is not a guaranteed maximum loss.

Collector event order is preserved. Hypothetical availability intervals do
not establish actual delivery order or implement a fill/delivery queue.
A future execution simulator must separately handle overlapping/reordered
availability, context changes before fills, no fills and latency scenarios.
No usable-input flag in this prototype substitutes for that work.

Peek returns a copy; ack processes only the next exact event. An immediate
repeat of the last committed ack returns the same verdict with no state change.
A rejected event leaves progress unchanged. Causal prefix identities depend
on the header, frozen policy/source and committed events, not a future suffix.
Only an exhausted cursor exposes the complete report.

Checkpoints bind exact fixture bytes, policy bytes, relevant source hashes,
cursor and prefix digest. Restore replays the committed prefix to rebuild
context and pending history reviews; it does not trust supplied derived state.
Unkeyed checksums are consistency checks, not authentication. External effects
still need consumer idempotence or atomic joint consumer/cursor persistence.

The policy cannot override age/cost/model rules through user flags. A future
collector must supply actual per-run evidence and retain unknown quantities
explicitly, using a separate reviewed native schema/reader. Existing captures,
calendar reservations and dated launch windows stay unchanged.
