# Sprint 181 · Chronological E1 and E2 exits

18 November 2026. The invented Level B replay follows each modeled fill
through scheduled H1 openings and completed ranges. It records whether
the path closes, remains open, or becomes unavailable because evidence
is missing. Declared session closures allow the path to continue to the
reopening gap. [Protocol](PROTOCOL.md)

- E1 keeps the held ray and hard stop. A completed H4 close beyond the
  ray latches an exit at the next eligible H1 opening. An opening that
  already crosses the stop uses the gap price with modeled slippage.
  A wick poke freezes the stop until a strictly better same-side line
  formed after entry qualifies. Ties preserve the held line.
- E1 stop updates apply from the H4 receipt in declared event order.
  An H1 range continues to use the protection effective at its opening.
  E2 keeps the original stop and target. A known opening reach takes
  precedence. Ambiguous intrahour stop and target hits resolve to the stop.
- The default liquidation cutoff is the final declared complete H1
  opening. The optional cutoff selects an exact scheduled open. New
  positions cannot start at or after that cutoff. If the liquidation row
  is still missing or its receipt falls after the partition end, the
  replay records `OPEN_AT_BOUNDARY` with the last exit-side mark.

## Invented results

| Scenario | Observed result |
| --- | --- |
| Late H4 receipt | The stop changes from 102.6 to 102.7. A low of 102.65 in the H1 already underway keeps the original protection. The next H1 opening gaps through the tightened stop and exits at 102.64998. |
| E1 LONG and SHORT close beyond | The exit latches on receipt. A normal next opening uses the scheduled exit. A stop-crossing next opening uses the gap price and records loss beyond the initial modeled price risk. |
| Poked line and replacement | A weaker stop and a line already eligible at entry leave the stop unchanged. Two equally ranked replacements preserve it. The sole qualifying later line replaces it and tightens the stop. |
| Declared 48-hour closure | The held path reaches the scheduled reopening and prices the gap at 101.99998. |
| Partition boundary | A declared opening can liquidate the position. A missing earlier hour blocks subsequent exit claims. A missing or late liquidation row preserves the last mark without a close price. |
| FXR E2 fixed protection | Stop and target in the same H1 range exit at 100.19998. A next opening above target exits at the fixed 106.8 target before an adverse range. |
| Restart | Restoring the setup checkpoint during the held path and replaying the supplied prefix reproduces the uninterrupted `exits.json` byte for byte. |

## Replay

```sh
PYTHONPATH=src python3 scripts/trendline-breaks-173.py SOURCE.json HOURS.json NEW_DIRECTORY --tick-size 0.1
```

Use the declared fixture tick. Add `--liquidation-at` with a scheduled
H1 opening in milliseconds to select an earlier liquidation slot. Read
`exits.json` for effective stop changes, exit prices and missing-data
states. `entries.json` still includes independent opening price
diagnostics, including observations at or after the liquidation cutoff.
The replay reconstructs exit paths from the H1 prefix and setup checkpoint.
Prior source-bound checkpoints require their matching checkout or a replay
of the original inputs.

The report uses hypothetical spread and slippage assumptions. Gap losses
can exceed the initial modeled stop distance. Each path is price-only.
Position limits, reservation, sizing, account charges, open liability and
independent ledger verification remain Phase 7 work. The fixtures provide
software evidence on invented candles.

## Verification

All 415 targeted tests passed. The seven new exit tests took 184.010
seconds. The retained suites ran five E2 level tests in 351.226 seconds,
33 lifecycle and engine tests in 562.379 seconds, 21 FXR, DLY and setup
acceptance tests in 685.841 seconds and 349 other checks in 624.226 seconds.

```sh
PYTHONPATH=src:tests python3 -m unittest test_trendline_exits_181 -v
PYTHONPATH=src:tests python3 -m unittest test_trendline_levels_180 -q
PYTHONPATH=src:tests python3 -m unittest test_trendline_acceptance_171 test_trendline_engine_170 -q
PYTHONPATH=src:tests python3 -m unittest test_trendline_fxr_175 test_trendline_dly_178 test_trendline_setup_acceptance_179 -q
PYTHONPATH=src:tests python3 -m unittest test_trendline_bounce_177 test_trendline_brk2_176 test_trendline_entries_174 test_trendline_breaks_173 test_trendline_context_172 test_trendline_selection_169 test_trendline_lines_168 test_trendline_geometry_167 test_trendline_pivots_166 test_trendline_study_165 test_trendline_fills_164 test_trendline_data_163 test_elliott_study_145 test_elliott_sessions_146 -q
```
