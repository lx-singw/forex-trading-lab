# One-hour paired runs verified — 23 October 2026

**The one-hour duration collection check is satisfied.** Two new independent
runs reached the recorder's one-hour elapsed limit (code13). Both exports have
valid stopped-prefix framing, with no pending read, unfinished pair or partial
tail. They remain separate runs; the earlier19 October connection-stop prefix
is also preserved separately.

Code13 is the planned return-time limit. It does not mean the max-count E footer
was reached: guarding, reads, IO and waits consume time, so fewer than3,600 polls
fit. The final stop frame has no receipt marker. Exact stop-time overshoot is
not measured; the last recorded guard markers are just under one hour.

## Measured results

Dates/times below are nominal computer-GMT labels, not independently certified
UTC or broker-time conversions.

| Observation | 20 October run | 23 October run |
|---|---:|---:|
| Nominal start label | 15:15:17 | 02:09:56 |
| Last recorded elapsed marker | 59m59.608010s | 59m59.044037s |
| Complete quote/clock pairs | 3,496 | 3,483 |
| Clock groups | 6,992 | 6,966 |
| Recorded diagnostic attempts/outcomes | 10,488 | 10,449 |
| Distinct source-millisecond labels | 3,000 | 2,436 |
| Source-label advances | 2,999 | 2,435 |
| Source-label reversals | 0 | 0 |
| Adjacent identical snapshots | 496 of3,495 | 1,047 of3,482 |
| Longest observed identical-snapshot span | 9.295998 seconds | 11.181028 seconds |
| Quote-receipt gaps over two seconds | 0 | 2 |
| Owned native file bytes | 3,121,630 | 3,110,021 |
| Terminal stop code | 13 | 13 |

The23 October run has two adjacent polling pauses:4.919093 and6.497732 seconds
(quote sequences599→602→605, where each quote follows its own clock-before
diagnostic group). These are gaps between recorder quote-read starts, not
proof of missing market ticks, broker delay or disconnected terminal state.
No connection-stop code was recorded in either new run. The cause of the
polling pauses is not established by the export. The gaps remain explicit
quality warnings; do not interpolate observations or assume uniform spacing.

Actual first-clock start spacing is1.000098–1.931511 seconds on20 October and
1.000141–6.497748 seconds on23 October, satisfying the one-second minimum.
Quote-read markers can be slightly less than one second apart because they
follow varying first-clock/guard work. Repeated snapshots are observed repeated
native values; their duration is not certified quote age or executable freshness.
Different dates/windows prevent interpreting the differing repeat counts as a
strategy or feed improvement.

## Clock evidence and scope

In both runs, raw TimeTradeServer minus TimeGMT stays+10,800 seconds and
TimeLocal minus TimeGMT+7,200 seconds. TimeCurrent minus TimeGMT ranges+10,798
to+10,799 on20 October (286 adjacent changes), and+10,797 to+10,800 on23 October
(538 changes). No raw clock field has a numeric reversal. Full paired arithmetic
and native quote bits/flags are retained without timezone or age correction.

There is no join with each other, the19 October interrupted run, the earlier111
pilot, metadata127 or cost128. UTC/quote age, complete tick delivery, executable
prices, producer identity and complete costs remain unverified. The captures
exercise the read-only transport and numerical quality engine; they are not
strategy evaluations or evidence of profit. Market/paper/order/real-money
admission remains false.

## Preservation and independent verification

Two closed owned exports totaling6,231,651 bytes were read through exclusive
handles and copied into new canonical run folders without overwrite. Their
SHA256 values are:

- 20 October: a73ba48f06b1be591b74bd12953aa63b48f020bf037977179dd0f04e2d2b37b6
- 23 October: 54b2ea031f057c92c8c113454d651af16dccd68d5ab450f2dcfd014766be8ec4

See [copy record](../reports/paired-recorder-132-capture-002-native-copy.json),
[summary](../reports/paired-recorder-132-capture-002-summary.json),
[20 October quality](../reports/paired-recorder-132-capture-002-run-001-quality.md),
[23 October quality](../reports/paired-recorder-132-capture-002-run-002-quality.md)
and [independent review](../reports/paired-recorder-132-capture-002-independent-review.json).

JSON/Markdown CLI results match the frozen library separately for both runs.
An independent raw walk checks41,878 frames and chained digests,20,937
sequences/outcomes, all6,979 pair calculations, native double values, source
changes/repeats/reversals, polling gaps and spacing. Event details remain capped
at128 per run while full counters include every event. Producer identity is not
authenticated by a hash chain or a declared market label.

All615 source/config/test files and66 earlier native hashes remain unchanged;
the two new files make68 retained native inputs. Prior handoff bodies, the
interrupted39-minute prefix and all sealed evidence remain preserved. The73
Python and119,449 C++ checks are retained, not rerun because code did not change.
No MT5 build/deployment/launch, SDK, account/settings change, support contact,
historical/reserved strategy replay, P&L or financial/risk/cost/weight change.
October stays quarantined, November–December reserved/untouched,2025 consumed
and closed historical/provider/H.10/native090 routes closed.

## Next work

No further MT5 action is needed for this duration check. Next is offline replay
integration: keep each run separate, consume observations chronologically using
their actual receipt intervals, preserve the two polling gaps, and test replay/
risk behavior with invented fixtures. Strategy evaluation still needs adequate
warm-up, explicit cost assumptions and appropriate validation evidence; these
short captures do not supply those prerequisites. Automated orders stay
unavailable.
