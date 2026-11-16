# Exact geometry and indicator inspection

Sprint167, 16 November2026. Research software for explicitly invented Level B
inputs only. This component calculates geometry; it does not declare a line valid,
select a setup, calculate returns or place orders.

From the WSL repository root:

```sh
PYTHONPATH=src python3 scripts/trendline-geometry-167.py /path/source.json /path/hours.json /path/new-output-directory --timeframe both
```

The files follow [163's invented source/hour contract](DATA-163-USAGE.md).
`--timeframe H4`, `D1` or `both` (default) chooses the output frames.
`--as-of INTEGER_MS` restricts processing to publications available at that
cursor. The existing loader's explicit invented-validation receipt can be supplied
with `--unlock-receipt`; there is no market-data unlock. Output is an exclusively
created directory containing `geometry.json`. Existing output is never overwritten.

The report retains source/code/protocol hashes, B/geometry labels, every immutable
indicator snapshot, confirmed raw pivots, and their frozen confirmation metrics
and touch tolerances. All rational quantities use integer `numerator` and
`denominator` fields; unavailable values are null. No decimal rounding or epsilon
is used to accept a boundary.

## Python geometry interface

```python
from forex_demo_lab.trendline.geometry import Ray, GeometryStream

ray = Ray("resistance", 17, "110", 23, "108.8", "H4")
assert str(ray.slope) == "-1/5"
assert str(ray.value(48)) == "519/5"
assert str(ray.project(48, 14)) == "101"
```

`Ray` is pure coordinate geometry, requiring positive anchors, at least six bars
between anchors, and rising support or falling resistance. It does not establish
touch count, penetration history, age, eligibility or consumption. Floats are
refused; use exact decimal strings, Decimal, integers or Fraction.

Feed completed typed bars from163's `BarStream` into a `GeometryStream(source,
"H4")` or `"D1"`. `ray(a_id,b_id)` accepts same-kind, same-segment confirmed
pivots from that stream. `Ray.from_pivots` is a lower-level typed-metadata adapter
with a frame/time/publication-ordinal cursor; external construction is not proof
of source provenance. `test_ray(ray, require_angle=True)` assesses the current
ATR/angle slope filters only. `False` selects the profile without angle filtering.
These results are not complete line validity.

## Timing and exact rules

True range is `max(high-low, abs(high-prior_close), abs(low-prior_close))`.
`ATR_SMA14` is the simple mean of the last14 true ranges, not Wilder's RMA or
TradingView's default ATR. The first observed bar supplies a prior close; a first
ATR therefore needs15 contiguous scheduled bars. No assumed earlier close or
high-low-only seed is invented. G38's ranges `[14, 0, ..., 0]` yield SMA1 at14
ranges and SMA0 at15, while a seeded RMA gives13/14 on that last observation.

Slope uses the evaluation bar's ATR and requires `abs(m)/ATR <= 1/2`.
Touch tolerance uses one quarter of ATR at that pivot's confirmation publication
and remains frozen. An unavailable or zero confirmation ATR yields no usable
tolerance; later volatility cannot repair it. Touch acceptance itself is pending.

For the angle profile, the current390-bar window supplies `max(high)-min(low)`.
The fixed-aspect normalized ratio is `abs(m)*390*(1/2)/range`. Because atan is
monotone and tan45degrees equals1, ratio `<=1` implements the frozen45degree
threshold exactly. This is the specified normalized chart-angle approximation,
not a universal visual angle. Short history and zero ATR/range fail closed.

Missing scheduled bars reset ATR/angle warmup and pivot neighbourhoods. Declared
calendar closures preserve adjacency; the next true range includes the price
gap from the preceding observed close. Advancing past an unobserved completed
scheduled bar blocks a current slope assessment. Historical snapshots remain
unchanged. Identical latest retries are idempotent; backfill, conflicting/reused
lineage, wrong frames, premature finalization and receipt reversal reject before
publishing either pivot or indicator state. A staged pivot fork provides atomicity.

Phase4 still needs pair enumeration, chronological touches, strict penetration,
profile validity, deduplication, ranking, bounds and immutable lifecycle revisions.
Actual-source/run qualification remains open before market work; orders remain
unavailable.
