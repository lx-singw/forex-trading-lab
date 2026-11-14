# Longer collection design

Prepared 2 November 2026 from the five preserved October136 diagnostics. This
is a design for a new collector and its qualification pipeline, not a launch
instruction, schedule, broker integration or extension of136's expired dates.

## What the pilot established

The last136 run reached its four-hour elapsed cap and wrote a valid bounded
file. It also observed an unchanged latest quote for over two hours. Earlier
runs stopped on disconnection, including one aligned with Windows sleep/wake.
Collection duration alone cannot establish active-market coverage. The137
assessment reports sample blocks and geometric bounds, never usable H1 bars.

## Scope and partition boundary

Keep the actual account-enum DEMO guard, continuity checks in memory, EURUSD,
USD and Algo Trading off. Reject real/contest accounts and account changes;
no order API, credentials, login automation, account creation or live toggle.
The new collector must start disabled and have explicit bounded allowed dates,
elapsed time, storage and attempts. No dates are assigned by this document.

October2026 remains quarantined, November–December2026 reserved/untouched and
2025 consumed. Do not collect, open or retune using reserved validation prices
to solve this engineering problem. Implementation and fault tests can proceed
with invented data. Future acquisition dates and development/validation
boundaries must be frozen in a separate manifest before collection starts;
this document does not reallocate the reserved periods.

## Run lifecycle and persistence

Use explicit OFF, PREFLIGHT, RECORDING, INTERRUPTED and STOPPED states. A
bounded reconnect wait may return through PREFLIGHT into a **new segment**;
it must not append to or disguise an interrupted segment. Start with at most
three reconnect attempts per acquisition job, increasing waits of5,30 and120
seconds, and a four-hour total job budget including waits. These are initial
engineering limits to test, not observed availability guarantees. Default
reconnect behavior remains disabled until failure/recovery tests pass.

Persist the interruption reason, monotonic markers and last durable sequence
before waiting, when storage still permits it. Real/contest mode, identity
change, Algo Trading on, unsafe clocks or corrupt storage latch STOPPED and
are never handled as network retry conditions. Do not change terminals,
accounts, server choice, security settings or Windows power plans to pass a
guard. No repeated retry outside the job/date budget and no catch-up polling.

Rotate bounded files inside a process with one random job ID, monotonically
increasing segment numbers, hash-linked predecessor references and explicit
boundary markers. A proposed first limit is32MiB per file and128MiB per job;
reserve space for closing records before queries. Verify durable writes and
refuse overwrites, collisions and append/resume after a crash. Capture new
context at every segment start and before resuming observations. Rotation
must occur before beginning a new quote triple, never halfway through one.

A storage close/link failure stops the job. A restart creates a new job and
cannot assert cross-process account identity. Random job IDs identify files,
not accounts; never serialize account identifiers or identity-derived hashes.
Ordinary clean rotation can preserve process-local continuity only when the
boundary records, guards, clock evidence and sampling all support it. Any
missing boundary or unexpected active-session outage remains a real gap.

## Power and connection evidence

Request temporary process-scoped prevention of automatic idle sleep during a
bounded job, release it on normal/error exit, and let process termination
release it. Do not change permanent power-plan values. Record only whether
the request succeeded, elapsed markers and observed interruption categories;
avoid machine/network/account identifiers. Test release on cancellation and
failure, duration bounds and behavior when prevention fails. Do not claim it
prevents deliberate sleep, lid closure, shutdown, power loss or network loss.

Preserve disconnect/reconnect transitions and pauses even if the next quote
matches the previous one. A connected flag is an observation, not proof of
continuous broker connectivity. Windows power events may corroborate a gap;
do not infer its absence from absent events. Keep failed-after-guard values
discarded, as136 already does.

## Clock, session and context evidence

Keep source timestamp labels and receipt clocks distinct. Record monotonic
markers around UTC reads and quotes, clock synchronization/status evidence,
clock steps and declared uncertainty. Establish the source's documented time
convention and its applicable offset/DST rule before producing UTC-aligned H1
bars. An observed source-minus-computer difference is not that rule. When a
bound cannot be supported, serialize unknown; never fill it with zero or a
manually asserted certification flag. Clock steps start a new segment.

Refresh contract/session/cost context on elapsed-time boundaries as well as
after a discontinuity; poll-count refresh alone drifts with stalls. Context
queries are sequential and must retain their own markers and outcomes. Track
session timezone, effective date and holiday/rollover exceptions separately
from the reported weekly template. Unknown calendar membership stays unknown.

Repeated snapshots do not prove that a session closed, that a quote is stale,
or that the market was inactive. Record their spans and classify the session
only when separate time/calendar evidence supports it. Expected closures do
not create bars. Unexpected missing active-session hours follow a frozen
reject/reset policy; do not interpolate through them. How known closures
affect indicator state must be part of the fixed bar/strategy contract.

## Sampling, fills and costs

Declare a sampled-bid/ask research model. Latest-quote polling cannot claim
complete tick delivery or know the high/low between samples. Full tick capture
or third-party certification is not required for every possible research
model, but the chosen model's uncertainty and price-observation limits must be
explicit. A later simulator must use only observations available at decision
time, next-eligible-quote execution, declared latency and adverse gap/slippage
scenarios. Stop-loss triggers can execute beyond their trigger price.

Preserve spread, commission query states, financing/rollover conventions,
currency conversion, margin rules and effective scope. Empty or failed fee
queries do not imply zero cost. If contractual costs cannot be established,
explicit conservative hypothetical scenarios may support sensitivity work;
their results cannot be relabeled observed broker-account performance. No
financial engine admission through unchecked configuration flags.

## Qualification and evaluation

Keep a causal per-observation eligibility record distinct from retrospective
diagnostics such as137's completed repeat groups. Never remove trades or
samples after seeing strategy returns. Freeze coverage rules, cost scenarios,
candidate parameters, partitions and the handling of positions at boundaries
before comparing outcomes. Development exits cannot use validation quotes.

The existing fixed H1 adapter needs201 observed closed qualified H1 warm-up
bars. The previous engineering pilot target remains480 development followed
by480 untouched validation bars after warm-up (1,161 observed closed bars).
These counts are not a statistical sufficiency calculation, number of calendar
hours, or promise of an edge. Reaching them requires multiple separately
bounded jobs and an explicit source/clock/context continuity policy; repeated
manual short runs cannot be added into continuous history by assumption.

Before implementing native acquisition, test the new lifecycle offline with
invented disconnections, account changes, real/contest modes, sleep/resume,
clock steps, storage errors, partial frames, rotation/restart boundaries and
long unchanged quote sequences. Then test the temporary keep-awake lifecycle
separately. No fresh-price collection is authorized by those software tests.
Position sizing, loss limits, stops, duplicate orders and restart risk retain
their meaningful tests before any later demo execution. Automated orders
remain unavailable throughout this design phase.

The next implementation slice is the pure acquisition lifecycle and bounded
segment journal with invented inputs. Native APIs, future dates and reserved
prices are not needed for that work.
