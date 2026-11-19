# Sprint 219 · Full-window counter benchmark

19 November 2026. Benchmarked the Phase 10 Level B path with a fabricated
2020 warmup and 2021–2022 development window. The schedule uses UTC
weekdays and weekend closures. The price fixture uses a flat background
with spaced repetitions of the existing BRK3 test pattern. It exercises
the full calendar and receipt volume with sparse line activity.

## Replay work

The counter now takes one source-binding snapshot per run and verifies it
against fresh file contents before returning a report. Each caller gets a
copy of its binding map. The standalone replay and checkpoint tools still
perform their regular per-step checks.

Geometry calculations read the current pivot ordinal, segment and receipt
clock directly. This avoids serializing the growing pivot and indicator
reports at each update. Calendar coverage uses a search over ordered due
times, and the angle range converts only the two extrema to exact rational
values. The frozen strategy predicates and reporting thresholds apply.

The historical counter retains the H4 receipt, line revisions, lifecycle
events and first penetration facts it needs for the tallies. The setup
engine still evaluates the current bar for strategy decisions. The
counter skips rejected-pair diagnostics, and equal-priced anchors still
produce zero slope-valid pairs. Detailed replay remains available through
the existing inspection and checkpoint paths.

## Benchmark results

The 49-H4 BRK3 comparison took 5.750 seconds on Sprint 218 and
0.976–1.491 seconds in two runs during this sprint. The complete count
cells had the same SHA-256, including the monthly totals, skip reasons
and price-filter diagnostics.

Before reducing trace retention, the dense fixture hit the existing
32,000,000-byte trace limit after 29.930 seconds. The sparse full-window
fixture also reached that limit in the safety-line engine. The dense
fixture puts a repeated strict high and low in each 12-H4 cycle and
exercises the rejected-pair volume at sustained pivot density.

Both full-window fixtures completed with the smaller trace. Each used
18,792 H1 rows, including 6,288 warmup rows and 12,504 development rows.
Every strategy and cost cell observed all 3,126 scheduled development H4
bars across 24 months.

| Fabricated fixture | Wall time | Peak resident memory | Eligible opportunities |
| --- | ---: | ---: | --- |
| Sparse recurring setups | 627.554 seconds | 245 MiB | Five BRK3 per cost profile |
| Dense equal-price pivots | 404.796 seconds | 175 MiB | Zero across all cells |

The sparse fixture exercised recurring setups and lifecycle state. The
dense fixture stressed rejected pairs. Throughput on a source with
sustained varied-price candidates remains unmeasured.

All 209 targeted tests passed. The compact and full traces produced
identical complete cells for all five strategies and both costs on the
comparison fixture. The canonical Phase 10 status report matched Sprint
218 byte for byte.

## Reproduce

```sh
mkdir -p reports/trendline-source-219
PYTHONPATH=src:tests python3 scripts/trendline-benchmark-219.py reports/trendline-source-219/full.json
PYTHONPATH=src:tests python3 scripts/trendline-benchmark-219.py reports/trendline-source-219/short.json --short
PYTHONPATH=src:tests python3 scripts/trendline-benchmark-219.py reports/trendline-source-219/dense.json --dense
```

The benchmark writes fabricated counts and software measurements into an
ignored report. The temporary manifest is pinned only within that run.
Historical feasibility remains `UNAVAILABLE` pending independent source
qualification. [Historical development counter](RESULTS-218.md)
