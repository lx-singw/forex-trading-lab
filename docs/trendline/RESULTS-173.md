# Sprint 173 · BRK3 setup replay

17 November 2026. The baseline BRK3 and its D1 variant now detect breaks
from completed H4 candles. The previous scheduled close must be on or inside
the same ray at its previous index. The current close must reach one declared
tick beyond the ray. The line must have qualified before the trigger bar.
A close beyond a newly qualifying ray is recorded as `MISSED_BREAK`.
A prior wick through a line prevents a subsequent trigger on that geometry.

The replay consumes all qualifying groups before choosing a setup. Opposing
directions and equal economic ranks cause abstention. For a selected setup,
the safety search checks the full trigger candle and prioritizes distance
from the close, then touch count. A safety tie or absent safety line causes
abstention. A selected safety line provides an exact buffered stop, rounded
outward to the declared tick. The D1 variant evaluates the published daily
context after consumption and safety selection.
[Protocol revision 7](PROTOCOL.md)

## Verification cases

- Both G35 paths reach BRK3 formation at H4 index 47 and trigger at 48.
  The safety values are 102.8 for LONG and 97.2 for SHORT. With ATR 263/140,
  the rounded stops are 102.6 and 97.4 respectively.
- The original implementation reused the bounce profile for protection.
  Six assertions failed because it applied a 30-bar floor to G35's 28-bar
  safety line. The dedicated safety profile now applies the two-confirmed-touch,
  slope and full-wick rules. The action age and golden fixtures retain their
  original definitions.
- A one-tick close qualifies exactly. A close 0.0001 inside that threshold
  with a penetrating wick invalidates the line. An earlier poke or a missing
  H4 prevents a later break on the same geometry.
- An action break with a current safety wick consumes its opportunity and
  abstains. Checkpoints taken before and after that bar reproduce the decision
  and consumption. With insufficient D1 history the context variant consumes
  the trigger, finds safety and reports `CONTEXT_UNAVAILABLE`.
- A two-line candle path consumes both resistance groups before missing
  safety causes abstention. Opposing sides, equal economic rank and equal
  safety scores also have component tests. The checkpoint and CLI checks
  cover duplicate receipts, changed history, prefix continuation, exclusive
  output paths and market input refusal.

## Replay the invented setup

```sh
PYTHONPATH=src python3 scripts/trendline-breaks-173.py SOURCE.json HOURS.json NEW_DIRECTORY --tick-size 0.1
```

Use the declared tick for the supplied fixture. `--profile TRL_BRK3_E1_D1`
enables daily context. `--as-of` limits the receipt prefix. The replay writes
`setups.json` and `checkpoint.json`. To resume, pass `--restore-checkpoint`
with the same descriptor, input, tick and profile. Checkpoint restoration
replays the publications and compares the state digest. Previous engine
checkpoints need their matching checkout because the source bindings changed.

The `READY` state means the trigger and its protection geometry are ready
for entry-observation checks. Phase 6 still needs the stop-window, spread and
crossed-stop checks, entry expiry, FXR, BRK2, bounce and disabled DLY coverage.
Market-source admission and execution integration remain later milestones.

## Test commands

All 359 targeted tests passed across the three final runs. The 14 new BRK3
tests took 134.635 seconds, the 33 acceptance and lifecycle tests took
340.804 seconds, and the 312 retained tests took 195.886 seconds.

```sh
PYTHONPATH=src:tests python3 -m unittest test_trendline_breaks_173 -v
PYTHONPATH=src:tests python3 -m unittest test_trendline_acceptance_171 test_trendline_engine_170 -q
PYTHONPATH=src:tests python3 -m unittest test_trendline_context_172 test_trendline_selection_169 test_trendline_lines_168 test_trendline_geometry_167 test_trendline_pivots_166 test_trendline_study_165 test_trendline_fills_164 test_trendline_data_163 test_elliott_study_145 test_elliott_sessions_146 -q
```
