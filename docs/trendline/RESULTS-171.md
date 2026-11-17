# Sprint 171 · Phase 4 line-engine acceptance

17 November 2026. The acceptance boundary is a line observed at a particular
publication. Each candle path below uses invented OHLC. A declared trigger
supplies a test input to the lifecycle interface. Phase 6 owns setup detection.

**Phase 4 software accepted.** All 336 targeted tests passed after the two
repairs. The three final runs comprised 9 new acceptance tests (365.324 s),
24 lifecycle tests including checkpoint and CLI exercises (678.285 s), and
303 retained regression tests (264.694 s). The next milestone is the optional
Phase 5 D1 context gate and its eight direction/bias outcomes.

## Replay evidence

| Case | Expected and observed result |
| --- | --- |
| Invalid reanchor (G30), both directions | The line through pivots 20 and 44 penetrates pivot 32 by exactly 0.01. BRK3 keeps the valid geometry through 20 and 32 with all three touches. At the same frontier BRK2 keeps the two-touch line through 32 and 44. |
| Wick and replacement (specification §9.3), both directions | Twelve warm-up bars precede the example clock. The old BRK2 line is eligible before the wick at example bar 52. Its group stays open and the line stays poked. The replacement uses pivots 40 and 52, has its own ID and group, and reaches minimum age at bar 70. The close beyond the old line cannot revive it. |
| Exact-union aliases, both directions | In the BNC profile, pivots 20 and 32 form the first line. A supplied trigger consumes its group. The narrow recent ranges admit the line through 32 and 72 at publication index 75. A wider candle at 76 admits the line with all three touches. Replay merges all three groups, preserves consumption and retires the strict subset. Restart produces the same next frame. |
| Competing support and resistance | Three deterministic seeds and their mirrors provide six paths of 60 bars. At every prefix an independent interpolation checks each valid candidate against every wick. Every candidate rejected before or during selection has an explanation. Reversing the valid candidates preserves the reduction. The final four-touch line outranks the three-touch line on every path. A second replay reproduces the first 56 frames, and a duplicate final bar reproduces the final frame. |
| FXR warm-up, both directions | A 90-bar formation span and three confirmed touches are already present after 389 bars. The angle-history test blocks the line. The 390th complete bar supplies the required range and the same three pivots qualify. |

## Golden fixtures and remaining boundaries

| Frozen fixture | Phase 4 assertion and verification |
| --- | --- |
| G04, G31 | Strict wick penetration, later confirmation, current-bar safety and the action-break exception. The 168 tests read both fixture directions. The §9.3 path and the 170 G35 replay exercise the resulting lifecycle. |
| G05, G06, G07 | Frozen correct-side tolerance including equality, earliest spaced touch and skipped second anchor. The 168 tests cover the touch decisions. The 171 table reads both G07 directions and checks each spacing independently. |
| G08, G09 | Exactly two versus three or more touches, core age 29/30 and FXR formation span 89/90. The 168 and 171 tables exercise the profile gates. G30 exercises the two break profiles on the same candles. |
| G10, G38 | Both signed slopes pass at the inclusive ATR and angle limits. Both golden range series give simple ATR values of 1 and then 0. The retained 167 check also calculates the alternative RMA value of 13/14. |
| G30 | Invalid earliest/latest geometry and profile-local subsets, exercised from candles above. |
| G33 | The 168 component test supplies 256 and 257 same-kind pivots, checks whole-search refusal and recovery as the inclusive window moves. A radius-three candle stream cannot supply 257 same-kind extrema in 601 contiguous indices. The 170 long path verifies retirement at 501 bars since first validation and poke precedence. The 167/168 tests cover zero ATR. |
| G35 | Both 49-candle paths supply action and safety geometry, confirmation, ATR, first eligibility at 47 and the strict wick outcome at 48. The setup, fill and exit expectations belong to later phases. |

Sprint 169 also checks rank transitivity, exact-distance tie breaking, shuffled
duplicates and display-only canonical IDs. Sprint 170 checks immutable prior
frames under a changed suffix, clock advancement, gaps, source bindings and
checkpoint continuation. Candidate diagnostics before initial eligibility are
recorded in the per-bar dump. The lifecycle journal starts when a selected line
is first admitted. FXR history is tested through the inspector and selection
API. The cap stress case uses declared pivot metadata.

## Publication and ownership review

A separate primary-agent pass traced publication time, current coverage,
selection, group consumption and terminal revisions across the engine, inspector
and journal. Two failures reproduced against the sprint 170 code.

* A completed wick can arrive when a later scheduled bar is already overdue.
  The journal's coverage check rejected the poke and aborted the entire
  publication. A poke or age retirement now accepts that observed bar at its
  actual receipt clock. The later bar stays missing, trigger admission stays
  blocked, and a clock-only snapshot cannot supply a late observation.
* The incremental inspector returned its internal code-binding dictionary by
  reference. Clearing it in a diagnostic report made the next valid observation
  fail. Each report now returns a copy.

The checkpoint carries executable-source hashes. Use the matching checkout when
restoring older checkpoints. The fixtures, thresholds and protocol revision 5
remain the basis for the checks. Market-source qualification remains open for
Phase 10.

## Reproduction

Run each command from the repository root.

```sh
PYTHONPATH=src:tests python3 -m unittest test_trendline_acceptance_171 -v
PYTHONPATH=src:tests python3 -m unittest test_trendline_engine_170 -q
PYTHONPATH=src:tests python3 -m unittest test_trendline_selection_169 test_trendline_lines_168 test_trendline_geometry_167 test_trendline_pivots_166 test_trendline_study_165 test_trendline_fills_164 test_trendline_data_163 test_elliott_study_145 test_elliott_sessions_146 -q
```
