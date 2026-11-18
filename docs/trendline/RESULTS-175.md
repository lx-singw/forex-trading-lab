# Sprint 175 · FXR break setups

18 November 2026. The break replay now accepts `TRL_FXR_M`. Its action line
requires at least three qualifying touches, a 90-bar formation span, the
ATR slope gate and the normalized angle gate from 390 completed H4 bars.
The trigger still requires a prior formation and an inclusive one-tick
close-break. It consumes the opportunity before ranking and safety checks.

The opposing safety line is checked against the completed trigger wick and
ranked at the trigger close. The setup freezes its value four scheduled
indices ahead, then applies the ATR buffer and outward tick rounding. The
projection is arithmetic on existing geometry, so it is available when
the setup triggers. [Sprint 175 protocol note](PROTOCOL.md)

## Invented checks

| Case | Expected result |
| --- | --- |
| 389 then 390 completed H4 candles | Missing angle history blocks formation through index 388. The 390th candle allows formation at 389. |
| Touch span 89 then 90 | The 89-bar path fails even with complete angle history. The 90-bar path qualifies. |
| The oldest wide candle rolls out on the potential trigger | The angle ratio rises above one while the ATR slope still passes. The action geometry fails at that frontier. |
| Mirrored breaks at H4 index 390 | The current safety values are both 100. The projections at index 394 are 100.48 for LONG and 99.52 for SHORT. With ATR 1861/700, the rounded stops are 100.2 and 99.8. |
| First H1 bid 100.15 for LONG or 99.85 for SHORT | The exit-side price crosses the projected stop while still inside the current line. The attempt reports `STOP_ALREADY_CROSSED`. |
| First H1 open passes the price checks | The E2 request reports `E2_TARGET_SELECTION_UNAVAILABLE`. The consumed group remains in the journal. |
| Checkpoint continuation | Restoring the FXR prefix reproduces its decision. A later wick leaves the frozen projection and decision intact. |

## Replay

```sh
PYTHONPATH=src python3 scripts/trendline-breaks-173.py SOURCE.json HOURS.json NEW_DIRECTORY --tick-size 0.1 --profile TRL_FXR_M
```

Use the fixture's declared price tick. The output contains the setup journal,
price checks and source-bound checkpoint. Earlier checkpoints need their
matching checkout or a replay of the original fixture.

Phase 7 supplies the support and resistance finder and E2's fixed qualifying
target. Full FXR trade simulation depends on that target and the later account
and exit integration. Phase 6 continues with BRK2, bounce and disabled DLY.

## Verification

All 377 targeted tests passed. The 6 new FXR tests took 163.047 seconds,
the 33 acceptance and lifecycle tests took 296.908 seconds, and the 338
retained checks took 278.553 seconds. Two CLI exercises also passed. An
eight-bar prefix produced zero attempts. A complete 1,565-row H1 fixture
published 391 H4 bars, consumed the LONG trigger at index 390 and
reported that E2 target selection was unavailable.

```sh
PYTHONPATH=src:tests python3 -m unittest test_trendline_fxr_175 -v
PYTHONPATH=src:tests python3 -m unittest test_trendline_acceptance_171 test_trendline_engine_170 -q
PYTHONPATH=src:tests python3 -m unittest test_trendline_entries_174 test_trendline_breaks_173 test_trendline_context_172 test_trendline_selection_169 test_trendline_lines_168 test_trendline_geometry_167 test_trendline_pivots_166 test_trendline_study_165 test_trendline_fills_164 test_trendline_data_163 test_elliott_study_145 test_elliott_sessions_146 -q
```
