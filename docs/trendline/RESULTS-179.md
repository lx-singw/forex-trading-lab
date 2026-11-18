# Sprint 179 · Phase 6 setup acceptance

18 November 2026. Phase 6 setup and Level B entry software has been verified
on invented candles and the frozen component fixtures. The five initial
profiles are available for invented replay. DLY requires a separate
invented-replay opt-in and stays outside the initial study grid.

The review found that a repeated bounce contact on an unpoked, spent group
reported a generic no-line reason. It now reports `ALREADY_CONSUMED`.
The diagnostic cannot trigger the group or reset the spacing of a future
opportunity. A line with a prior wick through it still fails strict validity.

## Fixture coverage

| Frozen case | Phase 6 evidence |
| --- | --- |
| G01 and G35 | Both signed G01 pairs pass their declared component calculations. The actual G35 candles verify pre-existing formation, safety, consumption and the rounded stop. Level B applies its declared slippage after the G01 quote-distance calculation. |
| G04, G05, G06, G07, G08, G09 and G10 | The prior verified line fixtures establish strict penetration, tolerance, spacing, touch count, formation span, and both slope gates. BRK2 and FXR replay exercise those gates in setup context. |
| G11 and G23 | Missing safety abstains after consumption. In a candle path where the line remains unpoked, a later bounce after restart reports `ALREADY_CONSUMED` and creates no second attempt. |
| G12, G29 and G39 | The inherited Level B price kernel and setup entry tests verify opening order, stop distance, spread, already-crossed protection, and outward stop rounding. The post-fill adverse-order and target-rounding checks remain component evidence for Phase 7. |
| G13 | Mirrored ordinary H4 contacts, strict wick and close checks, and six-bar spacing from both touch and approach pass. |
| G14 and G31 | Formation-bar breaks are discarded. Prior wick penetration blocks a later break. A trigger-bar wick through safety still prevents entry. |
| G15 | Opposing close-breaks on one invented H4 candle consume both groups and abstain, with matching results after restore. Retained component tests cover economic rank and an unresolved tie. |
| G17 through G20 and G27 | The retained eight D1 decisions pass. Full H1-derived BRK3 paths exercise aligned, conflicting and neutral bias after group consumption. Only completed daily bars influence the decision. The retained unavailable and prefix tests cover the remaining gate outcome. |
| G21 | Actual FXR candles verify directional four-index safety projection. Core profiles take their stop from the current safety value. |
| G25 | DLY waits only after a consumed break without safety. Terminal guards precede safety. The first eligible decision and terminal paths reconstruct from checkpoints. |
| G30, G33 and G40 | Profile-local selection, bounds, retirement, and study admission retain their earlier verification. DLY stays outside the five initial strategies. |

## Restart evidence

| Boundary | Replay check |
| --- | --- |
| Formation and trigger | BRK3 and the new opposing-break path restore a pre-trigger prefix. Triggered groups and the decision match uninterrupted replay. |
| Discarded and poked | Restore before and after the terminal observation. No entry appears after continuation. |
| Abstained and skipped | Restore consumed no-safety, opposing and D1-skipped outcomes. The original journal and decision remain reproducible. |
| Awaiting safety and delayed decision | DLY restarts with explicit opt-in and retains the original trigger and scheduled deadline. |
| Ready, pending and filled | The retained BRK2, BRK3 and BNC CLI checks reconstruct the same first opening and stable attempt. |
| Expired and unrecoverable | The first-hour deadline and DLY waiting deadline stay terminal. Missing, delayed or later observations cannot generate a replacement opening. |

Phase 7 adds the account ledger, reservation and risk checks, protection
management, and the causal E2 target finder. The FXR price path currently
reports `E2_TARGET_SELECTION_UNAVAILABLE` when an opening passes the earlier
gates. The complete cross-phase verification matrix remains Phase 9.
Earlier source-bound setup checkpoints require their matching checkout or a
replay from the original inputs.

## Verification

All 403 unique targeted tests passed across the retained runs and the
focused G01 rerun. The 33 acceptance and lifecycle tests took 416.171
seconds, the 15 FXR and DLY tests took 371.354 seconds, and the other 349
retained checks took 479.018 seconds. The new suite passed five of six
tests in 234.520 seconds. Its G01 test passed in a focused rerun after
converting the H1 fixture to the opening type required by the price
model. The correction affected only that test fixture adapter.

```sh
PYTHONPATH=src:tests python3 -m unittest test_trendline_setup_acceptance_179 -v
PYTHONPATH=src:tests python3 -m unittest test_trendline_acceptance_171 test_trendline_engine_170 -q
PYTHONPATH=src:tests python3 -m unittest test_trendline_fxr_175 test_trendline_dly_178 -q
PYTHONPATH=src:tests python3 -m unittest test_trendline_bounce_177 test_trendline_brk2_176 test_trendline_entries_174 test_trendline_breaks_173 test_trendline_context_172 test_trendline_selection_169 test_trendline_lines_168 test_trendline_geometry_167 test_trendline_pivots_166 test_trendline_study_165 test_trendline_fills_164 test_trendline_data_163 test_elliott_study_145 test_elliott_sessions_146 -q
```
