# Fresh input135 results

Completed 24 October 2026. The fresh-input contract prototype is implemented,
documented and demonstrated on15 frozen invented cases. It handles causal
clock/terms/calendar updates, uncertainty in quote age and availability, native
price bits, polling gaps, source anomalies and checkpoint recovery. It accepts
invented fixtures only; no saved native file is converted or qualified.

Read the [contract](FRESH-INPUT-135-CONTRACT.md),
[invented matrix](../reports/fresh-input-135-summary.md) and
[usage](FRESH-INPUT-135-USAGE.md).

The matrix has66 events and20 quote observations. Six observations meet all
declared invented bounds; others retain explicit unknown, expiry, stale/future,
session, gap or continuity reasons. **All20 quotes remain visible to a future
risk consumer.** The six are not wins, trades, executable-price confirmations
or market returns. No risk engine or financial simulator is constructed by135.

Receipt UTC and source-offset evidence have independent bases and validity
scope. Drift widens integer intervals outward. Unknown post-marker delay,
unknown clock mappings or expired context never become zero age or zero cost.
Only the whole availability interval can qualify under the0..2,000,000us
age bound, one H1 bucket and one open half-open session. Future context cannot
change earlier verdicts. Clock changes and gaps request history review;
subsequent usable input cannot grant full strategy entry permission.

Per-run hypothetical contract/cost profiles bind the existing baseline and
base/adverse113 scenarios. Real127/128 observations are not applied as these
runs' fees or account contract. Unknown context stays unknown. Positive input
usability remains a software judgment under declared assumptions; market,
paper, order and real-money availability remain false.

**55 Python tests passed**, including23 new contract tests plus133 replay and
existing execution-metric/tick tests. Tests cover exact age/session boundaries,
outward drift rounding, offset scope, unknown/expired data, delivery horizons,
ambiguous hour assignment, gaps/repeats/reversals, clock discontinuities, late
context, future-suffix causality, atomic rejection, duplicate ack and every
restart boundary in the selected paths. The retained engine tests exercise
cost-aware sizing, single positions, gap stops beyond estimated risk, daily
loss latching, target fills, slippage and duplicate/restart behavior.

The first revision passed54 tests. Review then found that dictionary insertion
order could change Markdown row order after sorted-JSON serialization. Its
source and passing-test evidence were preserved; the final revision sorts
case keys and adds a roundtrip-invariance test. Final55-test results are in
[test evidence](../reports/fresh-input-135-tests-002.json).

Default CLI JSON/Markdown match the library on all15 frozen input files,
repeat JSON is byte-identical and Markdown survives JSON roundtrip unchanged.
A separate Fraction/ceil arithmetic walk checks all66 causal prefix hashes,
20 quote intervals, age classifications and original quote payloads.
[Reference review](../reports/fresh-input-135-reference-review.json) records
that local synthetic check; it is not a second feed or producer attestation.

All623 older source/config/test and68 native hashes remain unchanged. Four
new implementation/config/test files make627. Prior handoff bodies, source
revisions, input matrix and verification evidence are preserved.

Limitations remain concrete: source/receipt bounds, costs, calendar and delay
are invented or declared assumptions in this prototype. It has no real clock
measurement, producer authentication, native reader/collector or full delivery/
fill queue. Availability intervals alone do not prove arrival order; handling
overlap/reordering, context updates before fills, no fills and latency belongs
to the later execution simulator. Warm-up and untouched market validation are
not supplied, and the existing native captures remain unqualified. No strategy
P&L, selection or profitability result is produced.

No MT5/SDK connection, launch/build/deployment, account/settings operation,
contact, service/account creation, actual order or financial-rule change
occurred. October remains quarantined, November–December reserved/untouched,
2025 consumed and closed routes/old dated scripts unchanged.

Next: prepare and test a separate default-off collector and native diagnostic
schema that records per-run context and clock evidence while preserving
unsupported source-offset, delay and fee quantities as unknown. Validate its
wire format before any native launch. No MT5 action is needed for135.
