# Sprint 180 · FXR levels and fixed E2 targets

18 November 2026. Phase 7 now has an invented FXR entry path with a fixed
E2 target. The break replay freezes the confirmed level candidates at the
trigger. The price model first applies spread, slippage and stop checks
at the declared opening. It then selects the nearest eligible level whose
rounded target is at least twice the exact initial stop distance from the
modeled entry. It returns `NO_VALID_TARGET` when every level fails.
[Sprint 180 protocol note](PROTOCOL.md)

## Level evidence

- The window includes the most recent 500 scheduled H4 indices through the
  trigger. The candidate band is one quarter of that bar's ATR. The lowest
  price anchors each cluster and at least two physical observations qualify
  its median as a level.
- The normal FXR CLI reads completed H4 and D1 publications. An observed
  D1 extreme must match a unique H4 child at the same price. Matching H4
  and D1 pivots count once and retain both confirmations in the report.
  Equal prices from separate H4 occurrences count separately. The report
  records incomplete, ambiguous or mismatched daily evidence when it
  cannot identify the child.
- LONG uses high clusters and SHORT uses low clusters. Rounding is toward
  entry. A closer level can fail the 2R check after rounding, in which case
  the model tests the next level. The selected raw median and the fixed
  rounded target are both recorded.

## Invented results

| Scenario | Expected and verified behavior |
| --- | --- |
| G26 anchor and occurrence rules | A price outside the lowest-anchored tolerance starts a new cluster. Same-occurrence H4 and D1 evidence shares a member. |
| 500-bar boundary and confirmation receipt | Index 2 is retained at frontier 501. A pivot confirmed after that frontier is excluded. |
| G37 E2 target and rounding boundary | Exactly 2R qualifies for both directions. A raw near level that rounds inside 2R is skipped in favor of the next qualifying level. |
| Invented LONG FXR H1 replay | At H4 index 390 the 106.8 cluster includes indices 64, 112 and 136. Index 112 holds one occurrence with two source confirmations. One ambiguous daily pivot is omitted. The fill is 102.20014 with stop 100.2 and target 106.8. The restored replay reproduces the same attempt. |
| Invented SHORT FXR CLI replay | The fill is 97.79998 with stop 99.8 and target 93.2. The report identifies the selected low cluster. |
| Prior FXR fixture with no qualifying level | The passing opening gates now lead to `NO_VALID_TARGET`. A crossed projected stop still takes precedence. |

## Replay

```sh
PYTHONPATH=src python3 scripts/trendline-breaks-173.py SOURCE.json HOURS.json NEW_DIRECTORY --tick-size 0.1 --profile TRL_FXR_M
```

Use the fixture's declared tick. The setup report stores the frozen level
members under `target_levels`. The entry report stores the fixed E2 position
geometry and original median for a modeled fill. Earlier source-bound
checkpoints require their matching checkout or a replay of the original inputs.

These are price-model outputs. Phase 7 still needs chronological exit
integration, reservation and sizing, accounting and costs, and the
independent ledger comparison.

## Verification

All 408 targeted tests passed. The five new level and E2 tests took
231.690 seconds, including the SHORT CLI run. The retained suites ran
33 lifecycle tests in 382.791 seconds, 21 FXR, DLY and setup checks in
496.981 seconds, and 349 other checks in 449.859 seconds.

```sh
PYTHONPATH=src:tests python3 -m unittest test_trendline_levels_180 -v
PYTHONPATH=src:tests python3 -m unittest test_trendline_acceptance_171 test_trendline_engine_170 -q
PYTHONPATH=src:tests python3 -m unittest test_trendline_fxr_175 test_trendline_dly_178 test_trendline_setup_acceptance_179 -q
PYTHONPATH=src:tests python3 -m unittest test_trendline_bounce_177 test_trendline_brk2_176 test_trendline_entries_174 test_trendline_breaks_173 test_trendline_context_172 test_trendline_selection_169 test_trendline_lines_168 test_trendline_geometry_167 test_trendline_pivots_166 test_trendline_study_165 test_trendline_fills_164 test_trendline_data_163 test_elliott_study_145 test_elliott_sessions_146 -q
```
