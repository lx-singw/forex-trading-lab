# Sprint168 — bounded enumeration and strict profile validity

17 November2026 (Africa/Johannesburg). **261 tests pass together:34 new and227
existing**, zero failures/errors, in141.808seconds. Seven invented CLI exercises
match declared candidate/profile-valid counts. Baselinef1c7096 was pushed before
this sprint began. Phase4 remains in progress; no complete strategy or market
result is claimed.

## Delivered and reviewed

New `trendline/lines.py` and [inspection CLI](LINES-168-USAGE.md) rebuild a single
source-bound snapshot from an explicit completed-bar prefix. Available pivots
inside the frozen600-index-distance window are counted before the256-per-kind
cap. Either kind exceeding the cap blocks the whole snapshot search without
truncation. Current-segment candidate pairs satisfy strict slope sign and six-bar
spacing. Missing scheduled bars cannot bridge the line history.

Touch detection processes pivots chronologically with their frozen confirmation
tolerances. Earliest accepted touches win; B gets no spacing override. Missing or
zero confirmation ATR cannot qualify an anchor. Strict wick penetration has no
touch/pivot exemption, and a later confirmation cannot restore the same poked
geometry. Age, formation span, touch count and slope filters are applied per
profile. All five strategies remain present; the D1_BRK3 diagnostic inherits the
existing three-touch rule with15-bar D1 age, without claiming the Phase5 context
decision table or choosing an unstated two-touch context threshold.

Current-bar penetration is included by default. Only explicit `action_break`
inspection of H4 break profiles excludes the evaluation bar; this does not prove
a pre-existing formation or a qualifying trigger. BNC/D1 inspection cannot use
that exception. Every candidate includes touch decisions, tolerance/distance,
age/span/slope metrics, first poke and rejection reasons. Wrong-sign/short pairs
have their own debug rejection records. Canonical ids never select an entry.

No existing economic rule, parameter, protocol, source config, fixture or runtime
code changed. All implementation source/script additions are separate168 files.
Reports retain invented B labels, source/protocol hashes, false entry readiness,
false qualification/demo eligibility/orders and zero market cells/returns.

## Verification

```sh
PYTHONPATH=src:tests python3 -m unittest test_trendline_lines_168 test_trendline_geometry_167 test_trendline_pivots_166 test_trendline_study_165 test_trendline_fills_164 test_trendline_data_163 test_elliott_study_145 test_elliott_sessions_146 -q
```

34 new tests include mirrored handwritten G04-G10/G31 boundaries, G33 cap
oversupply/recovery, G35 full candle discovery and first age eligibility, frozen
confirmation-tolerance use, strict sub-tick pokes, same-clock metadata ordering,
missing/late bars, source identity, deterministic retries, future-suffix/history
independence, six seeded path/mirror checks with independently checked no-poke
geometry, all profiles, low Decimal precision, CLI overwrite and source/validation
refusal. Cap oversupply is declared component-metadata stress, not a claim that a
radius3/600-bar market path produced257 same-kind pivots. Existing227 tests cover
167/166/165/164/163/145/146. Unchanged broad/120 accounting suites are not rerun.

The initial new-suite run found one test-harness error: the already mirrored
G06_SHORT literal was initially passed to a resistance helper. The test now uses
the fixture's literal support geometry. Original expected values and production
rules were not changed to accommodate it. Final metadata review additionally
requires Decimal pivot prices and independently bounded publication ordinals;
the final combined run above includes these checks and the revised D1 diagnostic.

| Invented CLI exercise | Evaluation index | Candidates | Profile-valid before dedupe |
| --- | ---: | ---: | ---: |
| H4 LONG G35, action-break role | 48 | 4 | 2 |
| H4 SHORT G35, action-break role | 48 | 4 | 2 |
| H4 LONG G35, full penetration | 48 | 4 | 0 |
| H4 LONG G35, age29 | 46 | 4 | 0 |
| H4 LONG G35, age30 | 47 | 4 | 2 |
| H4 G35, missing scheduled bar40 | 48 | 0 | 0 |
| Invented D1 BRK3 diagnostic | 49 | 3 | 2 |

The two G35 passing geometries share touches17,23,29 and intentionally remain
visible before deduplication. None is an entry signal. Final source-bound exports
and generated inputs remain ignored under `reports/trendline-168/examples-003/`;
the earlier pre-final-review exports remain in examples-001/002. Review removed
an unfrozen two-touch D1 context assumption in favour of the explicitly named
BRK3 diagnostic before any commit or market use; its final test refuses two touches.
Portable counts/hashes and unchanged-path audit are in
[verification-168.json](verification-168.json). No prices/provider/account/native
access or order placement occurred.

## Remaining work

Next Phase4 sprint: profile-local deduplication, frozen lexicographic ranking,
immutable revisions and lifecycle/opportunity-group history. Snapshot validity
does not yet establish formation time, trigger order, consumed attempts, safety
selection or entry readiness. Full golden line/property acceptance remains
pending. The current inspector rebuilds the prefix and is not performance-qualified
for repeated long historical replays. Actual source/run admission stays open
before Phase10 market counts/studies;28 new/16 prior market cells, protected
dates/routes, native grants and orders-off remain unchanged.
