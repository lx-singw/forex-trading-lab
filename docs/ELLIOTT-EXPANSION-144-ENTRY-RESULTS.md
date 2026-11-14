# Elliott144 — shared entry acceptance

14 November 2026. Work continues under the approved plan. Market admission and
native execution remain unavailable. No market observations are used here.

## Context-selection correction declared before replay

The first common hierarchical fixture exposed two shortcuts in higher-timeframe
context selection: newest-terminal filtering occurred before the approved
economic ranking, and any later small parsed node could mark a resolved active
parent obsolete. This blocked a resolved parent merely because its next leg had
smaller, incompletely resolved internal structure. Section6 of the approved plan
requires ranking relevant counts by resolved evidence and unresolved requirements,
and explicitly permits a still-valid active motive leg to supply context.

The correction applies only to higher-timeframe context selection. H1 opportunity
selection, setup identity, expiry, confirmation, stops, sizing and costs retain
their declarations. Frozen117–126 controls remain unchanged. This changes144
prototype decisions, so previous evidence keeps its original source bindings;
it is not presented as identical behavior or applied to an exposed market holdout.

The executable definition for the corrected context is:

1. Retain candidate contexts whose terminal boundary has not been breached by
   any already observed bar after that terminal; a later price rebound cannot
   revive the same count. Missing source coverage also makes that history unusable.
2. Retire a wave-2 context when an open, fully resolved wave-4 context extends the
   same side, families and source-anchor prefix. An unresolved extension does not
   supersede it. Compare remaining open interpretations by the existing economic rank, without
   treating recency as a higher-priority economic rule. Preserve all best-rank
   alternatives; unresolved members or conflicting directions prevent context.
3. A later node marks a future parent leg complete/unresolved only when it is
   at least as subdivided as the parent's required legs and is rooted at the
   parent count origin or its current terminal. An unrelated small node inside
   the developing next leg is not, by itself, proof of parent completion.
4. Fully resolved conflicting alternatives, anchored completed legs, unsupported
   evidence and incomplete search still prevent entry. No future bar or expected
   wave completion is supplied by a fixture.

Dedicated regressions and the shared public-input fixtures check this. The fixture
generator produces only invented H1 records
and quotes; H4/D1 bars, counts and signals must be derived by the actual pipeline.
Construction probes vary invented paths to exercise software states, not trading
parameters or observed market returns. An entry example is not market validation.

The original opposition component fixture included a short count whose boundary
was already breached by the supplied price. It now explicitly supplies two still
valid opposing hypotheses, preserving the ambiguity-abstention requirement. A
separate regression checks removal of an already-invalid opposed count.

Context evaluation is cached only while the parent analysis, parent direction
and last observed parent bar are unchanged. Freshness deadlines remain checked on
every decision. New parent publications invalidate the cache; fork isolation and
permanent historical breaches are tested. The cache is rebuilt from the bound
event prefix during checkpoint restore, rather than trusted as serialized state.
Coverage here still assumes the declared continuous invented observations. A
qualified venue calendar is required before legitimate market closures could be
distinguished from missing source history.

## Shared hierarchical inputs

The generator in `scripts/elliott-full-shared-entry.py` lifts a nested daily
pattern into H1 observations, places a smaller H4-scale pattern in its active
next leg, then a still smaller H1-scale pattern. H4 and D1 bars are derived by
the existing shared compiler; independent higher-timeframe histories are not
supplied. Prices, last-observation times and execution quotes remain invented.
The warmup is unfunded. Each comparison account starts with fresh USD10,000;
this is not a USD20 account study.

Only the input construction was adjusted to reach the intended software states.
The fixed accepted path uses a 0.9 H1 template compression and zero phase offset;
unresolved and parent-completion variants remain negative tests. Those construction
probes are not a strategy parameter search or a qualified comparison trial. The
source code, input and declaration are retained before the formal CLI outcomes.

| Declared example | Setup | Direction | Deliberately constructed exit |
| --- | --- | --- | --- |
| `EW3-long-target` | EW3 | Long | Target limit |
| `EW3-short-gap` | EW3 | Short | Observed adverse gap stop |
| `EW5-long-gap` | EW5 | Long | Observed adverse gap stop |
| `EW5-short-target` | EW5 | Short | Target limit |

Each case declares both cost profiles and both chronological partitions for all
four strategies: 64 invented comparison cells in total. The eight development
EW_FULL_V1 accounts are the primary entry/restart checks. Later partitions start
with fresh capital and no incoming position; all their outcomes are also retained.
These are correlated constructed examples, not 64 independent market discoveries.

The trigger candle is published before the first eligible execution quote.
Prior observations can form an unfilled setup, but there are no funded warmup
trades, incoming positions or carried profits. Future exit quotes and their
unpublished hourly price ranges cannot change the pending setup. The entry
occurs on the actual quote in the declared partition, including latency/cost checks.

## Verification and artifacts

The [portable verification record](evidence/elliott-144-entry/README.md) is tracked
in Git. Full reports, viewers, checkpoints and archives linked below are generated
local artifacts under the ignored `reports/` directory; the CLI commands recreate
them in new directories. They are not included in the source push.

**172 tests passed together in 1,350.090 seconds** on the final runtime revision.
The four declared public cases computed all 64 invented comparison cells. All
eight primary entry accounts passed pending/held restart and Fraction accounting
checks; the earlier no-entry shared example also passed on this revision.
Compilation and `git diff --check` pass. No market cell was run.

For each primary setup/direction/profile, the acceptance check discovers a signal
from the common H1 input, restores a checkpoint while that signal is pending,
restores another while the position is held, and compares the completed ledger
and decision snapshots with uninterrupted replay. Full pending/held checkpoints
are retained as compressed JSON, bound to source and prepared observations.

An independent Fraction oracle derives the slipped entry, protective tick
rounding, target rounding, floored volume, commissions, observed exit, trade net,
cash and entry-risk estimate. It does not call production sizing or fill helpers.
Gap cases must exceed the estimated entry loss and latch the daily entry pause.
A stop is not a guaranteed maximum loss. Target cases retain the original limit
instead of receiving the later, more favorable quote price.

The as-known-then viewers use the existing renderer on the shared bars and saved
decision/ledger records. Viewer-data checks require both entry and exit events.
These new HTML files have not been separately inspected in a native browser.

- [Declaration before formal outcomes](../reports/elliott-full-144-entry-demo-001/declaration.json)
- [All primary entry/restart/accounting results](../reports/elliott-full-144-entry-demo-001/results.json)
- [EW3 long target viewer](../reports/elliott-full-144-entry-demo-001/EW3-long-target/replay-base.html)
- [EW3 short gap viewer](../reports/elliott-full-144-entry-demo-001/EW3-short-gap/replay-adverse.html)
- [EW5 long gap viewer](../reports/elliott-full-144-entry-demo-001/EW5-long-gap/replay-base.html)
- [EW5 short target viewer](../reports/elliott-full-144-entry-demo-001/EW5-short-target/replay-adverse.html)

The full final test result is recorded in the
[test log](../reports/elliott-full-144-entry-verification-002/tests.txt) and
[completion record](../reports/elliott-full-144-entry-verification-002/completion.json).
The earlier verification001 run was stopped after the short-EW5 phase-transition
regression; its partial log and runtime source archive remain without a passing
claim. The phase correction has its own regression and does not change the frozen
controls. The original no-entry shared example is rerun separately on this revision.

The verification directory also contains the final source archive, source hash
manifest and published artifact hashes. The snapshot includes the current
package, scripts/tests/config/status documents and 46 frozen-control dependencies;
their hashes match the earlier control increment. Full input/decision/ledger
records are retained, including large JSON reports and compressed restart files.
This is research evidence, not a standalone native distribution or a performance
benchmark for production restart time.

```sh
PYTHONPATH=src:tests python3 -m unittest test_elliott_full_shared_entry test_elliott_full_context_lifecycle test_elliott_full test_elliott_full_policy test_elliott_full_rulebook test_elliott_full_boundary test_elliott_full_viewer test_elliott_full_discovery test_elliott_full_windows test_elliott_full_crosscheck test_elliott_full_controls test_elliott_full_shared test_elliott_full_incremental -v
```

Reproduce one example with new paths; include the tests directory because the
fixture generator reuses declared pattern templates solely to construct prices:

```sh
PYTHONPATH=src:tests python3 scripts/elliott-full-shared-entry.py fixture NEW-INPUT.json --setup EW3 --side 1 --outcome target
PYTHONPATH=src:tests python3 scripts/elliott-full-shared-entry.py freeze NEW-INPUT.json NEW-FREEZE.json
PYTHONPATH=src:tests python3 scripts/elliott-full-shared-entry.py replay NEW-INPUT.json NEW-FREEZE.json NEW-OUTPUT-DIRECTORY
```

## Remaining limits and activation

The wider finite nesting/alternative catalogue still needs broader acceptance;
there is no uniquely true count or calibrated count probability. A qualified
market input, calendar, costs/contracts and complete run admission remain absent.
The previously documented financing-clock differences remain. Native demo
transport, reconciliation, native build/enum guards and bounded shadow/demo runs
are unfinished. The approved plan is not complete.

All market cells and orders remain unavailable. No MT5/account/settings action,
reserved-price inspection or native collection occurred. The 2025 consumed,
October quarantine and November–December reserved boundaries are unchanged.
Frozen 117–126 code and declarations are unchanged. These software cases do not
estimate income, a win rate or a trading advantage, and do not enable real money.
