# Elliott144 — rulebook, discovery directions, boundaries and viewer

14 November 2026. The approved research implementation has progressed; **the full
plan is still in progress and market/demo execution admission is unavailable**.

## Implemented in this increment

The executable `elliott_full/rulebook.py` now diagnoses the18 declared families.
It distinguishes structural rules from project conventions, child-grammar and
endpoint failures, parent locations, insufficient resolution, unsupported depth,
and observation-only forms. Reports export the machine-readable `rulebook.json`.
Rule definitions link to the primary sources already specified in the approved
plan; their existence is not evidence of profitability.

The finite-profile test matrix covers a positive and bearish mirror for every
family, plus broken parent/child endpoints. Focused negative tests cover flats,
triangle/diagonal parent locations, unknown locations, unsupported families,
depth claims without children, and nonconverging diagonal boundaries. These are
component grammar examples, not exhaustive acceptance of every possible nesting.

This caught a real earlier implementation error: flat children were checked as
3–3–3. They now require3–3–5. A parent cannot gain validity from a label without
the appropriate child evidence. Pattern height is checked independently of the
minimum resolved-child depth, and resource-cap exits retain diagnostics.

## EW5 and competing parent counts

A resolved1/2/3/4 prefix used to tie mechanically with restarting wave1/2 inside
that same prefix. The new count record keeps that restart interpretation but
requires an additional unresolved parent relabelling. This implements the plan's
preference for fewer unresolved structural requirements; Fibonacci guidelines
cannot override it. The additional requirement is visible in the record and
cannot itself supply an entry context or arm a setup.

Counts that begin outside that resolved parent window are not automatically
penalized. This is our declared mechanical interpretation policy, not a claim
that the preferred count is uniquely correct or has a calibrated probability.

The parser now prunes impossible motive/corrective grammar routes and memoizes
completed routes. The4,096 limit counts grammar expansions and cached route
construction; empty interval probes no longer consume that hypothesis budget.
Interval probing remains bounded by the256-pivot input limit, and candidate/depth
limits remain active. Exhaustion still prevents entries. This is a clarified
engineering work budget, not a proven wall-clock or production-throughput bound.
The old unpruned traversal exhausted its budget on the constructed EW5 prefix;
the new traversal resolves it without increasing the4,096 expansion ceiling.

## Automatic discovery and verification

**120 tests passed together in94.500 seconds on the final source revision.**

[Full test log](../reports/elliott-full-144-rules-verification-004/tests.txt):

```sh
PYTHONPATH=src:tests python3 -m unittest test_elliott_full test_elliott_full_policy test_elliott_full_rulebook test_elliott_full_boundary test_elliott_full_viewer test_elliott_full_discovery -v
```

The four discovery tests cover EW3/EW5 in both directions using only the public
invented bars/quotes interface. No signals, counts, positions or context states
are supplied. The pending-signal restart and independent Fraction cash checks
remain included. The earlier91 legacy124–126 checks were not rerun here; their
implementation and frozen declarations were not edited.

A separately declared six-case public-input demonstration completed: four base
cases (both setups/directions), plus adverse-cost short cases for both setups.
Every case discovered one signal and executed one invented trade followed by a
deliberately constructed gap exit. All six outcomes are retained:

- [Declaration](../reports/elliott-full-144-discovery-matrix-002/declaration.json).
- [Outcomes](../reports/elliott-full-144-discovery-matrix-002/results.json).
- [EW3 long](../reports/elliott-full-144-discovery-matrix-002/EW3-long-base/replay.html).
- [EW3 short](../reports/elliott-full-144-discovery-matrix-002/EW3-short-base/replay.html).
- [EW5 long](../reports/elliott-full-144-discovery-matrix-002/EW5-long-base/replay.html).
- [EW5 short](../reports/elliott-full-144-discovery-matrix-002/EW5-short-base/replay.html).

The matrix was completed before the final display-only changes described below.
Its original HTML is retained. Its timeframe histories are independently invented,
not certified aggregation from one underlying quote feed. These are software
coverage cases, not six market trials or estimates of win rate/returns. No source
prices were acquired and no existing reserved dates were inspected.

## Declared partition boundaries

An invented input can optionally declare a `boundary` with `end_time` (exclusive),
`quote_sequence`, `quote_source` and `quote_time`. It must identify the actual last
quote in that input. All observations must fit before the declared end and no
later bar can be borrowed to justify that endpoint.

Finalization requires the latest quote to have been executable when received.
Stale, repeated-source, closed-session, missing or mismatched endpoints reject;
there is no earlier-price fallback, even for a flat account. A held long exits on
bid minus slippage, a short on effective ask plus slippage, including commission.
Financing is not charged twice. Stops/targets already reached at the endpoint
retain their ordinary exit precedence. Repeating the identical finish is
idempotent; different endpoints or further events after finish reject. Both
ledger and whole-engine checkpoints reproduce finalization.

Boundary tests independently reconcile both directions/profiles, cover widened
exit spreads, invalid slipped prices with atomic rejection, stale/missing tails,
double finishes, financing and rehashed endpoint forgeries. They also check that
a development partition cannot use a later quote/bar to close a position.

An input without a boundary retains its prior unfinished-replay semantics. The
presence of this feature does not assign real development/holdout dates or admit
a source to the still-unavailable market study.

## Viewer verification and artifact roles

The first visual inspection exposed a presentation gap: the cursor stopped at
the last bar and could never reach entries/exits a few seconds later. The viewer
now includes execution events as separate cursor stops, preserves their order at
equal timestamps, and never borrows a future count snapshot for an earlier event.

It plots the actual prospective count (EW3/EW5), distinct alternatives rather than
three radius copies of one pattern, original protection levels, and entry/exit
fills. Scaling includes observed fills so a gap beyond the stop remains visible.
The cursor gates fill visibility as well as completed candles. Four viewer-data
tests cover these timeline behaviours.

[Final visually inspected replay](../reports/elliott-full-144-reviewed-viewer-001/replay.html)
is an adverse-cost short EW5 example generated after the presentation fix. Its
[structured report](../reports/elliott-full-144-reviewed-viewer-001/report.json)
and [compressed checkpoint](../reports/elliott-full-144-reviewed-viewer-001/checkpoint.json.gz)
retain numerical/source evidence. The screenshot is linked from the final handoff.

Through the browser computer-use tools, warmup, signal, entry/protection and exit
states were inspected. The final state showed the preferred EW5 count, unresolved
EW3 parent alternative, original stop/target and gap exit fill. The page labels all
data invented and market/orders unavailable. The temporary loopback-only HTTP
inspection server was stopped; the self-contained HTML needs no running server.

The compact viewer is approximately1.2MB; full trees/events remain in the separate
checkpoint artifact. The original matrix numerical outcomes were not changed by
the display fix. The final120-test run includes all numerical and viewer checks
together, so it is not a sum of partial test runs.

## Reproduction and source snapshot

The CLI accepts `--setup EW3|EW5`, `--side 1|-1`, `--profile base|adverse` and a
constructed `--outcome gap_stop|target`. Always use a new output directory.

```sh
PYTHONPATH=src:tests python3 scripts/elliott-full-discovery-matrix.py NEW_MATRIX_OUTPUT
PYTHONPATH=src:tests python3 scripts/elliott-full-bar-demo.py NEW_VIEWER_OUTPUT --setup EW5 --side -1 --profile adverse
```

The fixture templates live in the test module, hence the explicit `src:tests`
path. They remain invented test inputs, not a back door for market data. The final
verification directory contains a source ZIP and a per-file SHA256 manifest for
this implementation's source/config/tests/scripts/docs. Local hashes establish
consistency, not broker authentication or signed provenance.

## Remaining work

The approved plan remains in progress. Remaining acceptance includes broader
nested/ambiguous-pattern cases and long-history/window handling; differential
accounting and unchanged control adapters; separately typed qualified-input/run
admission; native demo transport, actual enum guards, reconciliation and protection
failure tests; and bounded shadow/demo trials when historical evidence permits.

The current native boundary is still inert. All16 market cells and every order
route remain unavailable. Existing data partitions, source closures and expired
capture windows are preserved. No MT5/account/settings operation, paid service,
broker-account creation or real-money capability was added. Stops can lose beyond
their entry estimate through gaps, as the invented gap cases intentionally show.
