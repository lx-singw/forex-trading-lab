# Bounded line inspection

Sprint168,17 November2026. Explicit invented Level B prefixes only. This builds
on [167 geometry/ATR](GEOMETRY-167-USAGE.md); no setup, trade, account or market
qualification is implied by profile validity.

From the WSL repository root:

```sh
PYTHONPATH=src python3 scripts/trendline-lines-168.py /path/source.json /path/hours.json /path/new-output-directory --profile TRL_BRK3_E1 --role action_break
```

The source/hour contract and explicit invented-validation receipt are unchanged
from [163](DATA-163-USAGE.md). `--as-of INTEGER_MS` limits available publications;
`--unlock-receipt` supplies the existing invented-validation receipt. Market kinds
are refused. Output is an exclusively created directory containing `lines.json`;
existing output is never overwritten. No provider requests occur.

`--profile` supports all five frozen strategies. `D1_BRK3` selects a D1 diagnostic
using the existing BRK3 three-touch rule and15-D1-bar age; it does not implement
Phase5's context gate. All strategy profiles use H4. BRK2 requires exactly two
touches; BRK3 and its D1-gated variant require at least three. BNC requires at
least two prior confirmed touches. Their age minimum is30 H4 bars. FXR_M uses
at least three touches,90-bar formation span and both slope filters. Other
profiles use the ATR-slope test. The D1-gated strategy's H4 line inspection does
not supply a context decision.

`--role full` is the default and includes the evaluation bar in strict penetration
checks. `action_break` excludes only that bar and is accepted only for H4 break
profiles. It does not establish that a break happened, that the line was formed
earlier, or that an entry is available. BNC and D1_BRK3 cannot use this exception.
A protection-line check must include its current bar; this sprint does not select
safety lines or implement their setup integration.

## Snapshot API and bounds

```python
from forex_demo_lab.trendline.lines import inspect

report = inspect(source, completed_h4_bars,
                 profile="TRL_BRK3_E1", role="action_break", as_of=cursor_ms)
```

`source` is the strict invented Declaration and bars are an explicit list/tuple of
typed completed bars in receipt order. A supplied cursor rejects any future
publication in the prefix; it cannot silently backdate an inspection of later
bars. Rebuilding an identical prefix is deterministic. Identical latest retries
are idempotent; other duplicate/backfill/frame/finalization rules are inherited.
The prefix is bounded by166's20,000-bar software limit. This implementation is
stateless and rebuilds the geometry frontier per inspection; it is not a
performance-qualified streaming lifecycle engine.

Available pivots with index distance `now_index - pivot_index <= 600` are selected
before checking the256-per-kind cap. The inclusive distance follows the roadmap
Appendix A; it is recorded as `lookback_index_distance` rather than an ambiguous
row count. Exceeding either kind's cap marks `search_incomplete`, reports
`SEARCH_INCOMPLETE` and emits no candidate pairs or profile-valid ids. There is
no silent truncation. Old pivots fall outside the window as the cursor advances.
Only the current contiguous segment supplies candidate pairs, so unknown gaps
cannot be stitched into lines. Window counts remain visible before segment
filtering. The oversupply/cap test uses declared component metadata to stress a
boundary that ordinary radius3/600-bar candle paths need not reach.

Each same-kind pair must have the correct strict slope sign and spacing of at
least six bar indices. Touches process pivots chronologically from A, using each
pivot's frozen positive confirmation tolerance. Correct-side distance must be
nonnegative and within that tolerance. Earliest accepted touches win spacing;
if a prior accepted touch makes B too close, reject the pair with
`ANCHOR_SPACING_CONFLICT`. An unavailable/zero confirmation ATR cannot qualify an
anchor or be repaired by later volatility. No touch is exempt from wick checks.

Every completed extreme after A is tested with exact rational arithmetic. Any
strict penetration in the checked interval rejects the candidate, including a
wick later confirmed as a pivot. Rebuilding later never erases that earlier poke
for the same geometry. Missing interval coverage and overdue completed bars block
profile validity. Known closures keep calendar-index adjacency through the
unchanged source/pivot/indicator interfaces.

## Reading the debug dump

`pair_rejections` explains wrong slopes and spacing before geometry evaluation.
Each `candidate` includes canonical geometry/anchors, every touch decision and its
frozen tolerance/distance, touch indices, summed distance, age, formation span,
slope metrics, first penetration and ordered reason codes. Exact prices/distances
use numerator/denominator records. Source/code/protocol hashes and B/geometry
labels remain attached.

`profile_valid_ids` is the unranked, undeduplicated result of those checks.
Multiple geometries with the same touch set intentionally remain visible.
`entry_ready`, `orders_available`, `demo_eligible` and source qualification remain
false. There is no trigger/formation event, lifecycle revision, opportunity group,
consumption or economic selection. The lower-level pair/touch/profile kernels
also accept declared component fixtures; such metadata are not proof of actual
candle discovery or source provenance.

Next Phase4 work is profile-local deduplication, frozen ranking, immutable lifecycle
revisions and opportunity-group handling, followed by remaining golden/property
acceptance. Actual-source/run admission stays open before market work.
