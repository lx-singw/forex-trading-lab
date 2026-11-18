# Sprint 194 · Development-only signal counter

18 November 2026. `tools/signal_count.py` runs the frozen setup engine
and entry-price checks on invented Level B bars and Level Q quotes.
It counts entry-eligible opportunities before occupancy, position sizing,
exit evaluation or loss pauses, following Protocol C6. The counter
assesses the original first scheduled B opening or first qualifying
Q quote. The FXR target-distance rule is evaluated at entry.

## Run and interpret

```sh
PYTHONPATH=src python3 tools/signal_count.py bars SOURCE.json HOURS.json NEW-B-COUNT.json --tick-size 0.0001
PYTHONPATH=src python3 tools/signal_count.py quotes TAPE.json NEW-Q-COUNT.json --tick-size 0.0001
PYTHONPATH=src python3 tools/signal_count.py status config/trendline-study-v1.json NEW-STATUS.json
```

Use the declared tick size. Omit `--profile` and `--cost-profile` to run
all five initial strategies under base and adverse costs. Repeat either
option to select a subset. `--as-of` bounds the receipt prefix and defaults
to the partition end. The B entry cutoff defaults to the final scheduled
H1 opening and can be set with `--liquidation-at`. The Q tape supplies its
entry cutoff.
Reports identify their data level, geometry basis, scope and input hashes.

Monthly counts use the UTC month of the H4 setup receipt even when the
first opening or quote arrives in the next month. Scheduled H4 counts
use the month of their due time. The report separates new valid action
lines, eligible line observations, breaks, bounces, `READY` setups,
abstentions, consumed groups, and each entry status and reason. A group
is counted at its trigger, using the alias state available at that point.

Diagnostics include the per-H4 action-line histogram and average age,
strict penetration counts, `NO_SAFETY_LINE` break numerator and denominator,
and trigger touch counts. Price-check denominators show how many
opportunities reached and passed each check. Exact stop/ATR and
spread/stop histograms use entry-eligible observations. Q reports also
give received, executable and entry-spread-qualified quote counts by cost.

## Verification

All 67 targeted tests passed. The eight new tests cover both input levels,
cost and receipt filtering, month rollup, a `NO_SAFETY_LINE` abstention,
validation rejection, and FXR entry eligibility before the target receipt.
Opportunity counts agree across variants of post-entry prices. The tests block
account, exit and risk evaluation calls.

The invented Level B smoke report ran all five strategies under both costs.
Its BRK3 setup counted one eligible opportunity in each cost profile. The
invented Level Q smoke report likewise counted one BRK3 opportunity in each
cost profile. These counts verify the software path.

## Historical feasibility

The canonical plan still has an unassigned source and development
window. The status report records `UNAVAILABLE` and `actual_counts` is
null. D15 sets the threshold at 60 entry-eligible opportunities per
strategy. The initial count excludes DLY pending development evidence.

The next dependency is a permitted EURUSD H1 bid-plus-entry-spread
export or a synchronized bid/ask tape. Admission needs the declared
development and warmup scope, clock and session rules, coverage and
lineage, and the corresponding price and spread semantics. These are
the outstanding source checks for real counts and the viewer review.
[Canonical plan](../../config/trendline-study-v1.json) · [Retained source review](SOURCE-165-FINDINGS.md)
