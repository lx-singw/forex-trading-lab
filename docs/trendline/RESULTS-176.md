# Sprint 176 · BRK2 replay

18 November 2026. `TRL_BRK2_E1` now runs through the shared break and
invented Level B entry replay. The existing line profile requires exactly
two accepted confirmed touches and at least 30 H4 bars since the first
touch. The line must qualify before the trigger, maintain the two-touch
count at the trigger, and pass the existing close-break checks. Its
opportunity is consumed at the trigger.

BRK2 ranks the opposing safety lines at the trigger close and freezes
the current, buffered safety value with outward tick rounding. Its first
scheduled H1 opening uses the shared E1 price checks, hypothetical costs,
and expiry. The action touch count applies to each geometry. Safety
selection retains its separate two-or-more-touch requirement.
[Frozen protocol](PROTOCOL.md)

## Invented checks

| Fixture | Expected outcome |
| --- | --- |
| Mirrored two-touch adaptations of G35 | Remove the pivot at index 23 while keeping 17 and 29. BRK2 first qualifies at 47 and triggers at 48. The long and short stops are 102.6 and 97.4. |
| Same ray under BRK2 and BRK3 | BRK2 accepts the two-touch path. BRK3 accepts the original three-touch G35 path. The other profile reports `TOUCH_COUNT` for that ray in each case. |
| Late third confirmation on the trigger bar | A pivot at index 45 confirms at index 48. A close beyond the original ray still produces zero BRK2 triggers because its accepted touch count has increased to three. The wick marks the old line poked. |
| Invented bid opens 104.4 and 95.6 | With base costs and 1.2 pips of spread, the respective E1 prices are 104.40014 and 95.59998. |
| Replay resumes from a pending entry | The attempt ID stays stable. Entry, setup and checkpoint files match the uninterrupted replay byte for byte. |

## Replay

```sh
PYTHONPATH=src python3 scripts/trendline-breaks-173.py SOURCE.json HOURS.json NEW_DIRECTORY --tick-size 0.1 --profile TRL_BRK2_E1
```

Use the price tick declared for the invented fixture. The command writes
`setups.json`, `checkpoint.json`, and `entries.json`. Restore earlier
source-bound checkpoints in their matching checkout or replay their
original inputs.

The BRK2 outputs model setup eligibility and entry prices. Phase 7 covers
the account and exit simulation. Phase 6 continues with bounce and disabled
DLY. FXR's E2 target finder remains part of Phase 7.

## Verification

All 381 targeted tests passed. The four new BRK2 tests took 87.892 seconds,
the 33 acceptance and lifecycle tests took 352.550 seconds, and the 344
retained checks took 442.855 seconds.

```sh
PYTHONPATH=src:tests python3 -m unittest test_trendline_brk2_176 -v
PYTHONPATH=src:tests python3 -m unittest test_trendline_acceptance_171 test_trendline_engine_170 -q
PYTHONPATH=src:tests python3 -m unittest test_trendline_fxr_175 test_trendline_entries_174 test_trendline_breaks_173 test_trendline_context_172 test_trendline_selection_169 test_trendline_lines_168 test_trendline_geometry_167 test_trendline_pivots_166 test_trendline_study_165 test_trendline_fills_164 test_trendline_data_163 test_elliott_study_145 test_elliott_sessions_146 -q
```
