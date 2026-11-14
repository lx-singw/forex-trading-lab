# Coverage137 results

Completed 2 November 2026. The new offline assessment reads exactly five
manifest-pinned October136 files. It does not open MT5, read fresh prices,
change collector dates, construct a simulator or place orders.

| Separate capture | Paired quotes | Marker span, seconds | Maximum full1h intervals by span alone | Qualified H1 bars |
| --- | ---: | ---: | ---: | ---: |
| 27 October | 124 | 127.320876 | 0 | 0 |
| 28 October | 6,839 | 7,055.298690 | 1 | 0 |
| 29 October, morning | 7,333 | 8,392.809486 | 2 | 0 |
| 29 October, afternoon | 8,157 | 8,602.562718 | 2 | 0 |
| 30 October | 13,941 | 14,399.963491 | 3 | 0 |

Span endpoints are the first/last completed paired after-guard markers. A
pending or partial final quote cannot extend them. In particular, the last
run's time-cap stop is a collection milestone, but even its entire span is
slightly shorter than four hours between paired observations. The geometry
column is an upper bound for an arbitrary hourly grid, not actual aligned
bars, observed active sessions or sufficient market history. Runs are not
joined and the bounds are not added into continuous warm-up.

The five runs contain1,1,2,40 and8 diagnostic sample blocks respectively after
breaking at quote-request gaps strictly over2s or source-label anomalies.
Their gap counts remain0,0,1,39 and7. The longest block in the final run is
10,802.804060 seconds, but that block includes repeated snapshots. The longest
identical-quote group in that run spans7,232.333952 seconds and contains the
final6,987 observations. Repetitions remain in the report; their duration is
not a source-age estimate and their cause remains unknown. All detail lists
are capped at128 while counts and maxima use every completed pair.

**No input qualifies for the fixed H1 comparison.** Source/receipt UTC bounds,
source-age/delivery assumptions, applicable session/holiday evidence and full
costs remain unresolved. All context commission responses reported empty;
that does not mean zero cost. The fixed adapter needs201 observed closed
qualified H1 bars for warm-up before evaluation, far beyond even the best
geometric bound in any run. No strategy return, win rate or profitability
result was computed.

Verification: **43 tests passed, including14 new137 tests**, using invented
inputs for hour/gap boundaries, repeated groups across gaps, source anomalies,
partial prefixes, details beyond truncation, cost states, strict manifests,
origin/hash/provenance/symlink rejection, separation, no financial-engine
construction, and deterministic read-only CLI behavior. The unchanged136
reader and134 assessment tests are included. Actual-input CLI and library
JSON agree. A separate walk of physical136 fields matches paired counts,
sampling gaps, repeats, marker spans and segment geometry. Every run matches
its previously saved quality report and pinned canonical SHA256. The tests
and source stayed unchanged while the actual assessment ran.

The [longer collection design](LONGER-COLLECTION-DESIGN.md) defines bounded
process/segment lifecycles, explicit interruption records, a temporary
keep-awake request, session/clock/context evidence, sampled-quote execution
assumptions, cost scenarios and frozen chronological partitions. It does not
assign future dates or authorize reserved-price collection. Next implement
the pure lifecycle and bounded segment journal with invented inputs; no native
APIs or reserved data are needed for that implementation slice.

October remains quarantined, November–December reserved/untouched and2025
consumed. No expired source was renewed and no Windows setting changed.

Evidence: [full assessment](../reports/coverage-137/assessment.json),
[readable assessment](../reports/coverage-137/assessment.md),
[test output](../reports/coverage-137/tests.txt),
[independent reconciliation](../reports/coverage-137/verification.json).

To reproduce the offline report from the WSL repository:

```sh
python3 scripts/coverage-137.py --format markdown
python3 scripts/coverage-137.py --format json
PYTHONPATH=src:tests python3 -m unittest test_coverage_137 test_context_recorder_136 test_forward_eligibility_134
```

The report is retrospective. It cannot be used as a causal eligibility stream
or to discard samples/trades after observing strategy results.
