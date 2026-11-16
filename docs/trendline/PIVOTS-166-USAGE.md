# Causal invented pivots — sprint166

Phase3 implements strict radius3 H4/D1 extrema on labelled invented163 bar
publications. It cannot load/admit market data or enable a strategy/account/order.
Radius2/4/8 Elliott implementations and frozen records remain unchanged.

```sh
PYTHONPATH=src python3 scripts/trendline-pivots-166.py SOURCE.json HOURS.json NEW-OUTPUT-DIRECTORY
PYTHONPATH=src python3 scripts/trendline-pivots-166.py SOURCE.json HOURS.json NEW-OUTPUT-DIRECTORY --timeframe H4 --as-of MILLISECONDS
```

The CLI reuses163's exact source/hour file binding, receipt-ordered validation,
calendar/aggregation and explicit invented-validation unlock checks. It writes a
new pivots.json with H4/D1 reports and refuses existing output directories. Market
kinds are rejected. --unlock-receipt applies only to invented validation fixtures;
it cannot authorize protected market prices. Valid future suffix values remain
hidden by the cursor; malformed full inputs still reject at the data boundary.

## Incremental semantics

PivotStream(source, timeframe) observes one typed completed Bar per publication.
It confirms a strict high/low only after three earlier and three later adjacent
scheduled bars exist. Equal extrema fail strict comparison; a centre that is
both a high and a low is unresolved and excluded. Advancing time alone cannot
supply missing bars or confirm a pivot.

Each frozen Pivot records kind, price, scheduled bar_index, confirmation_index,
occurred_at, confirmed_at, confirmed_ordinal, timeframe, radius and coverage
segment. occurred_at means the occurrence candle's close, not the unknown exact
intrabar wick time. confirmed_at is the confirming publication's availability;
the ordinal preserves same-clock observation order. The raw journal never rewrites
earlier pivots, even when a later same-kind pivot is more extreme.

The alternating view is diagnostic: a stronger same-kind pivot can replace its
latest display point. It is limited to the current contiguous coverage segment
and does not erase the raw journal or choose trades. Future line enumeration must
use confirmed raw pivots and its own complete validity/coverage rules.

Scheduled index gaps reset the seven-bar confirmation neighbourhood and display
view; already published pivots remain. Initial missing bars are reported too.
Declared weekend/holiday closures do not count as missing scheduled bars. Late or
reordered historical backfill rejects rather than retroactively forming pivots.
An identical latest observation is idempotent and does not refresh the clock;
a conflicting duplicate rejects without mutation.

Source/clock/frame/lineage and observation bounds are checked before mutation.
All price comparisons use exact stored Decimals, independently of caller precision.
Reports are detached copies; pivot values are immutable. Source/protocol changes
invalidate further publication. Earlier identities do not depend on a future
whole-file hash. These are ordinary local consistency checks, not authenticated
source provenance or account checkpoint/restart certification.

The implementation adapts the existing extrema algorithm with the new frozen
radius; every tested prefix matches unchanged patterns.confirmed(...,3) on H4
and D1. Segmented/gapped cases additionally enforce explicit-calendar continuity.
No line engine, ATR calculation, ranking, setup decision or risk account is added
here. Those remain the following roadmap phases.
