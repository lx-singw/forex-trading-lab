# Elliott144 — common invented hourly observations

14 November 2026. The approved implementation remains in progress. This increment
adds a common **invented hourly-bar** input path for the fuller Elliott strategy
and its three frozen controls. It does not qualify prices or enable orders.
It follows the [control-adapter increment](ELLIOTT-EXPANSION-144-CONTROLS-RESULTS.md).

## Shared observations and derivations

The new `shared.py` input contains only H1 midpoint OHLC records, their declared
last-observation and publication times, an invented calendar, execution bid/ask
quotes and two chronological partitions. It cannot accept independent H4/D1
histories, supplied counts, signals or account marks.

Four complete H1 children form an H4 bar; 24 form a D1 bar. Opens/closes come from
the first/last child, highs/lows are exact Decimal extrema, and publication is
the latest child availability. Parent lineage binds its child records. Missing
or unavailable children cannot be interpolated or borrowed from a later suffix.
Equal-time publications reach the fuller strategy in D1/H4/H1 order.

Hourly lineage is an invented-record integrity check, **not source authentication**.
The input H1 OHLC is declared, not reconstructed from ticks. The existing strict
quote aggregator and its coverage threshold have not been relaxed. The earlier
sparse daily-quote format still cannot supply the fuller strategy's hourly
history; its four new-strategy cells remain unavailable in that older interface.
This new interface is deliberately labelled differently.

The full shared history exposed repeated rescanning in pivot detection. Strategy
now confirms only the newly observable center at each radius. The original batch
detector remains unchanged as a reference. Every-prefix comparisons at radii2/4/8
cover tied highs/lows, both directions, same-kind replacements and delayed
confirmation times. Additional checks cover fork isolation and bootstrap state.
Confirmation/ranking rules and source indices have not changed. Whole-engine
checkpoints still reconstruct caches from the bound input prefix. This reduces
repeated confirmation work; it does not bound total history, journal or snapshot
memory, or establish production throughput.

Execution quotes must agree with the supplied hourly price range and declared
last observation, when that hour exists. Contradictory session/quote states and
conflicting prices for a repeated source timestamp reject. The controls' float
price adapter requires exact decimal round-trip compatibility; otherwise the
input is unavailable rather than silently rounded into a different price series.

## Four original economic policies

`EW_FULL_V1` uses the existing whole-engine replay, causal counts, setup policy,
risk ledger and exact executable boundary finalization. `EWPB_D124`, `T12_D` and
`CASH` use their original 125/120 account engines. Both daily controls receive the
same D1 OHLC and publication times derived for the fuller strategy, through the
unchanged 118/124 feature engines. All four accounts receive the same observed
execution source/receipt times and bid/ask prices.

Each partition starts with fresh USD10,000 and no carried position or loss pause.
Prior observations warm the strategy but do not fund trades. At least 253 already
available bars of each required timeframe are necessary before the first execution
quote. The compiler requires all completed trading hours through its endpoint;
missing history or insufficient warmup yields unavailable cells with null results.
It does not turn missing data into a flat return.

All required observations must be received strictly before the partition end.
The endpoint must identify the actual last new, fresh, trading quote, and no later
bar can be used after that quote to justify finalization. The shared wrapper binds
checkpoints to the prepared partition and expected event prefix; the existing
engines reconstruct the economic state on restore. Invented account enum fields
inside legacy adapters are not evidence about a connected account. No native
account or order API is present.

The original source-day financing and other control rules are preserved. The
previously documented receipt-day financing timing differences, daily-pause/time
exit differences and off-tick rounding limits have not been erased by sharing data.

## Public example and verification

The public CLI generates one declared `short_gap` example. At the first funded
quote it has 6,072 H1 children, 1,518 derived H4 bars and 253 derived D1 bars. Its
calendar is continuously trading and explicitly invented; it is not a broker
session calendar. Daily-trend target/gap accounting in both directions and both
cost profiles is additionally checked in component replay cases. The older
Elliott control and CASH abstain in these shared examples; their active Elliott
accounting evidence remains in the earlier raw-quote control tests.

The example's smooth daily closes do not establish a resolved Elliott context.
The fuller strategy's zero entries are an expected abstention, not winning trades
or a measured advantage over the deliberately constructed trend-strategy gap.
The common-input positive Elliott-entry case remains outstanding; earlier
independently invented multi-timeframe examples retain their separate scope.

- [Declaration before CLI outcomes](../reports/elliott-full-144-shared-demo-002/declaration.json)
- [Source and cell freeze](../reports/elliott-full-144-shared-demo-002/freeze.json)
- [All 16 cell statuses](../reports/elliott-full-144-shared-demo-002/run/comparison-status.json)
- [Development child/parent coverage](../reports/elliott-full-144-shared-demo-002/run/development/derived-bars.json)
- [Fuller-strategy decisions](../reports/elliott-full-144-shared-demo-002/run/development/EW_FULL_V1-base.json)
- [Daily-trend ledger](../reports/elliott-full-144-shared-demo-002/run/development/T12_D-base.json)

The focused shared-input checks cover exact aggregation/publication, delayed
children, same daily features/quotes, daily-trend target/gap accounting in both
directions and costs, partial/held/finished restart, rehashed state/prefix forgeries,
future-hour isolation, unavailable history/warmup, endpoint quality, quote/bar
contradictions, schema/precision/quote-count limits, duplicates and partition
binding. Existing independent Fraction-based auditors reconcile the control
accounts. No production sizing or fill function is used as that arithmetic oracle.

**159 tests passed together in 394.708 seconds** on the final runtime revision:
the143 existing checks,12 shared-input checks and4 incremental-confirmation checks.
The public CLI processed all16 invented cells; every market status remains
unavailable. Compilation and `git diff --check` also pass.

The final consolidated result is recorded in the
[test log](../reports/elliott-full-144-shared-verification-003/tests.txt) and
[completion record](../reports/elliott-full-144-shared-verification-003/completion.json).
The first combined run's tool session ended before completion; its partial log is
retained in `shared-verification-001` and is not counted as a passing run. The
second run was deliberately stopped during the public example to address repeated
full-history pivot scanning. Its partial log and `shared-demo-001` artifacts are
retained without a passing-run claim; the final revision uses the paths above.
Its stopped run also retains the verified pre-incremental runtime source.

The final [source archive](../reports/elliott-full-144-shared-verification-003/source.zip)
and [hash manifest](../reports/elliott-full-144-shared-verification-003/source_sha256.json)
cover the current Elliott package, tests/scripts/config/status documents and46
declared frozen-control dependencies. Source/archive hashes and the example's
freeze bindings were checked; the original repository remains the supported
reproduction environment. The46 frozen-control bindings match the previous
control increment unchanged.

```sh
PYTHONPATH=src:tests python3 -m unittest test_elliott_full test_elliott_full_policy test_elliott_full_rulebook test_elliott_full_boundary test_elliott_full_viewer test_elliott_full_discovery test_elliott_full_windows test_elliott_full_crosscheck test_elliott_full_controls test_elliott_full_shared test_elliott_full_incremental -v
```

Reproduce the public example with new paths:

```sh
PYTHONPATH=src python3 scripts/elliott-full-shared.py fixture NEW-INPUT.json --side -1 --outcome gap
PYTHONPATH=src python3 scripts/elliott-full-shared.py freeze NEW-INPUT.json NEW-FREEZE.json
PYTHONPATH=src python3 scripts/elliott-full-shared.py replay NEW-INPUT.json NEW-FREEZE.json NEW-OUTPUT-DIRECTORY
```

## Remaining scope and boundaries

The invented schema retains the legacy 2000–2003 clock, at most 20,000 hourly records,
512 total execution quotes and 256 execution quotes per partition, plus the input
file-size/calendar limits. It is not a scalable tick-history runner. The shared
positive Elliott-entry/restart scenario, wider nested/fault acceptance, qualified
source/aggregation/calendar/cost admission, and disabled native demo transport and
reconciliation remain unfinished. The full plan is not complete.

All 16 market statuses remain unavailable, with no market returns or strategy
selection. Artificial examples do not consume or certify a qualified market
comparison batch. The 2025 consumed, October quarantine and November–December
reserved boundaries remain unchanged. No reserved prices, MT5/account/settings,
native collection or orders were accessed. Frozen 117–126 source and declarations
remain unchanged; real-money execution and automated orders remain unavailable.
