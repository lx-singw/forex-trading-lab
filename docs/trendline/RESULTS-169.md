# Sprint169 — selection and explicit lifecycle journal

17 November2026 (Africa/Johannesburg). **303 tests pass together:42 new and261
existing**, zero failures/errors, in119.167seconds. Seven invented CLI selections
and two source-bound lifecycle-interface exercises match expectations.
Baseline92ce402 was pushed before this sprint began. Phase4 remains in progress.

## Delivered

New `trendline/selection.py` reduces only already validated geometries. Exact-touch
deduplication prefers the existing earliest/latest anchor pair, then exact summed
distance, then canonical geometry id. It never fabricates a reanchored line.
Strict subsets, aliases and tie diagnostics remain profile/frame local; BRK2 is
not erased by a BRK3 superset. Frozen lexicographic ranking separates its economic
key from the final canonical display key and explicitly reports economic ties.
No trade is selected. Identical duplicate metadata are idempotent, conflicts and
mixed evaluation frontiers reject, and reduction is permutation independent.

New `trendline/lifecycle.py` implements a source/profile/frame/code-bound,
append-only journal of explicit commands. Registration/validation, strict pokes,
500/501-bar retirement, selected strict-superset retirement, simultaneous declared
trigger consumption, same-kind alias merging and bounded checkpoint replay are
verified. Commands stage all state before committing, terminal instances cannot
reset, and retries remain idempotent after later transitions and restart.
Consumed groups stay consumed through merges. New touch sets create new instances
and groups; exact-touch aliases share a group. Causal ids exclude whole-file hash,
while checkpoint continuation remains bound to the frozen source declaration.

The [169 CLI](SELECTION-169-USAGE.md) retains explicit163 loading, invented B
labels, protected-validation ordering, prefix cursors and exclusive output.
Optional `--journal` records current full-check survivors as CANDIDATE then VALID;
action-break exceptions cannot seed that journal. This is a single-snapshot
storage exercise, not automatic historical transition inference.

Existing source/runtime code, original80 fixtures, source configs, protocol and
prior evidence are unchanged. No economic parameter or rule changed. Source
qualification, entry readiness, trigger detection and orders remain unavailable.

## Verification

```sh
PYTHONPATH=src:tests python3 -m unittest test_trendline_selection_169 test_trendline_lines_168 test_trendline_geometry_167 test_trendline_pivots_166 test_trendline_study_165 test_trendline_fills_164 test_trendline_data_163 test_elliott_study_145 test_elliott_sessions_146 -q
```

42 new tests include G35 mirrored candle-derived selection, G30's no-invalid-
reanchor rule, exact distance fallback, profile-local pruning,30 seeded input
permutations, total/transitive rank keys, economic ties, defensive immutable
snapshots, source identity, CLI overwrite/source refusal, full-check journal
registration, terminal transitions, strict sub-tick penetration,500/501 retirement,
simultaneous declared consumption, atomic failures, alias merge/reconsumption,
new-pivot groups, source/profile/code guards, event/byte bounds and checkpoint
restart at candidate, valid, triggered, poked, retired and merged states. Duplicate,
reordered, edited and wrong-source/code checkpoints reject. Existing261 checks
cover168/167/166/165/164/163/145/146. Unchanged broad/120 accounting suites are not
rerun. Test elapsed time is a local run observation, not a replay benchmark.

The initial36-test run caught two new test-fixture errors: one list supplied two
conflicting touch sets for a single geometry at the same frontier, and a purported
equality wick used the wrong line value. Fixtures were corrected to distinct
geometries and the exact evaluated price; frozen rules and original golden
expectations were unchanged. Later review added profile-scoped diagnostics,
mixed-frontier rejection, opposing-kind merge refusal and causal instance ids.
The final303-test run includes those changes.

| Invented CLI exercise | Ranked survivors | Journal registration/validity events |
| --- | ---: | ---: |
| H4 LONG G35, first age-valid full snapshot | 1, anchors17/29 | 2 |
| H4 SHORT G35, first age-valid full snapshot | 1, anchors17/29 | 2 |
| H4 G35 action-break inspection | 1 | journal seeding refused for this role |
| H4 G35 including current poked bar | 0 | 0 |
| H4 G35 age29 | 0 | 0 |
| H4 G35 missing scheduled bar40 | 0 | 0 |
| D1 BRK3 diagnostic | 1 | 2 |

Two additional G35 interface exercises register/validate at47, checkpoint/restart,
then either record the strict poke at48 or an explicitly supplied trigger at48.
They end POKED/unconsumed or TRIGGERED/consumed, respectively, with three events;
another restart reproduces each report. The trigger exercise is not evidence of
a detected/certified setup, trade, fill or return.

Generated inputs, checkpoints, reports and helper remain ignored under
`reports/trendline-169/examples-001/`. Portable counts/hashes and filtered Git
identity audit are recorded in [verification-169.json](verification-169.json).
No actual market/provider/account/native access or order placement occurred.

## Remaining work

Next Phase4 sprint: integrate automatic per-bar candidate/revision history,
penetration/retirement ordering, gaps/caps and alias/group replacement decisions,
then complete remaining golden/generated-path acceptance. The journal deliberately
does not infer those decisions or trigger predicates. Setup detection, missed
breaks, bounce contacts and economic tie abstention require later setup integration.
Checkpoint integrity is not source authentication or permission. Current snapshot
selection still rebuilds its prefix and is not performance-qualified for long
repeated replays. Actual-source admission stays open before market counts/studies;
all28 new/16 prior market cells, protected dates/routes, native grants and orders-off
status persist. No full Phase4 completion is claimed.
