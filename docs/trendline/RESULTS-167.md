# Sprint167 — exact geometry and causal ATR

16 November2026 (Africa/Johannesburg). **227 tests pass together:29 new and198
existing**, zero failures/errors, in9.526seconds. Six invented CLI exercises match
declared expectations. Baselinef849011 was pushed before this sprint began.
Phase4 is in progress; this sprint delivers its geometry/indicator increment.

## Delivered and reviewed

New `trendline/geometry.py` implements exact rational interpolation, slope,
projection, signed correct-side distance, strict anchor sign/spacing and confirmed
same-frame/segment anchor construction. Pure rays are explicitly geometry only.
The current-bar ATR and390-bar normalized-angle slope filters preserve inclusive
boundaries without floating-point rounding. The45degree threshold uses the exact
equivalence between normalized ratio<=1 and atan(ratio)<=45degrees.

`GeometryStream` computes simple14-true-range ATR from prior closes, records
immutable snapshots and freezes each pivot's touch tolerance at confirmation.
An unavailable confirmation ATR stays unavailable. Missing scheduled bars reset
warmup; declared closures preserve adjacency and gap-aware true range. A missing
completed bar blocks current slope assessment. The small `PivotStream.fork()`
addition stages mutations independently so rejected input cannot partially publish
indicator or pivot state; the entire166 suite is rerun.

The [inspection CLI](GEOMETRY-167-USAGE.md) reuses163's loader, chronological
aggregation and protected-partition boundary, rejects market kinds and output
overwrite, and emits exact numerator/denominator values. Labels remain invented B
with no returns, demo eligibility or orders. No existing economic parameter or
protocol rule changed. Original80 fixtures, source declarations, frozen Elliott
code and prior evidence are unchanged.

## Verification

```sh
PYTHONPATH=src:tests python3 -m unittest test_trendline_geometry_167 test_trendline_pivots_166 test_trendline_study_165 test_trendline_fills_164 test_trendline_data_163 test_elliott_study_145 test_elliott_sessions_146 -q
```

29 new tests cover handwritten mirrored G35 geometry/ATR, G38 SMA versus RMA,
true range in both gap directions, H4/D1 warmup, six-bar spacing, signed tiny
penetration, slope/angle equality and exact near-boundary rejection,390-bar
rolling range, immutable confirmation tolerance/history, same-clock cursor gates,
future-suffix independence, low Decimal precision, missing/closed periods,
staleness, atomic rejection, fork isolation, duplicate retries, source bindings,
labels and the CLI/source/validation boundary. Existing suites contribute198.
Unchanged broad/120 accounting suites are not rerun.

| Invented CLI exercise | Bars | Latest ATR | Angle range | Gaps |
| --- | ---: | --- | --- | ---: |
| H4 LONG golden35 | 49 | 263/140 | unavailable | 0 |
| H4 SHORT golden35 | 49 | 263/140 | unavailable | 0 |
| H4 before seventh confirming bar | 6 | unavailable | unavailable | 0 |
| H4 missing scheduled bar40 | 48 | unavailable after reset | unavailable | 1 |
| D1 warmup | 15 | 2 | unavailable | 0 |
| H4 rolling angle window | 391 | 2 | 2; first-bar extreme rolled off | 0 |

Inputs, exercise helper and exports remain ignored under
`reports/trendline-167/examples-001/`; portable counts/hashes are in
[verification-167.json](verification-167.json). No market/provider/account/native
access occurred. This is software evidence only, with no performance claim.

## Remaining work

Next Phase4 sprint: bounded pair enumeration, chronological touch acceptance and
strict penetration/profile validity; deduplication, ranking and lifecycle follow.
Full Phase4 acceptance needs all golden line fixtures and generated-path properties,
which are not yet claimed. Actual source/run admission remains open before Phase10
market counts and studies. All28 new/16 prior market cells, protected dates/routes,
native grants and orders-off status persist.
