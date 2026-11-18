# Sprint 174 · BRK3 Level B entries

18 November 2026. The BRK3 replay now passes each READY decision to the
invented Level B price model. The decision carries the exact frozen ATR,
rounded safety stop, trade direction and H4 receipt time. The price model
checks the exit-side bid or ask against the stop, then checks the
slippage-adjusted distance and effective spread. It still accepts the
decimal ATR inputs used by earlier price-model callers.

| Invented evidence | Entry result |
| --- | --- |
| H4 decision and scheduled H1 open share a timestamp | The declared sequence puts the completed decision before the assumed open. |
| H4 decision arrives 2 seconds after the scheduled opening | `LATE_DECISION` immediately. A later hourly price cannot rescue the attempt. |
| The first completed H1 row has yet to arrive | Pending until the next scheduled H4 close. |
| The first H1 row is missing at the deadline | Expired with `MISSING_ENTRY_BAR`. A row received after the deadline leaves that result intact. |
| A closure follows the trigger | The scheduled reopening supplies the candidate H1 open. |
| The partition ends at the trigger | `NO_SCHEDULED_ENTRY`. |
| The opening bid reaches a long stop or the opening ask reaches a short stop | `STOP_ALREADY_CROSSED`, including equality. |
| The opening price fails the ATR distance or spread test | `STOP_OUT_OF_WINDOW` or `SPREAD_TOO_WIDE`. |

The mirrored G35 replay uses ATR 263/140 without decimal rounding. With
invented bid opens 104.4 and 95.6 and spread 1.2 pips, the base fills are
104.40014 and 95.59998 respectively. Their fixed stops are 102.6 and 97.4.
Changing the opening hour's later high, low and close preserves the price
result. Mid-only geometry has no executable side. A setup skipped by D1
context never reaches the entry model.
[Protocol revision 8](PROTOCOL.md)

## Replay

```sh
PYTHONPATH=src python3 scripts/trendline-breaks-173.py SOURCE.json HOURS.json NEW_DIRECTORY --tick-size 0.1 --cost-profile base
```

The replay writes `entries.json` alongside the setup report and checkpoint.
Use the declared tick of the fixture. Select `base` or `adverse` to apply
the corresponding frozen hypothetical price costs. `--as-of` limits both
setup publications and the hourly evidence available for pricing.

Restoring a setup checkpoint with the same fixture and cost profile
re-derives the entry report from the supplied receipt prefix. A pending
attempt retains its ID when its terminal outcome becomes visible.
Earlier source-bound checkpoints can be read with their matching checkout,
or the original fixture can be replayed with the current code.

The report models entry prices. Account reservation, position sizing,
commissions, financing and lifecycle reconciliation belong to Phase 7.
FXR, BRK2, bounce and disabled DLY remain in Phase 6.

## Verification

All 371 targeted tests passed across three runs. The 12 new entry tests
took 125.150 seconds, the 33 lifecycle and acceptance tests took 360.291
seconds, and the 326 retained tests took 297.391 seconds.

```sh
PYTHONPATH=src:tests python3 -m unittest test_trendline_entries_174 -v
PYTHONPATH=src:tests python3 -m unittest test_trendline_acceptance_171 test_trendline_engine_170 -q
PYTHONPATH=src:tests python3 -m unittest test_trendline_breaks_173 test_trendline_context_172 test_trendline_selection_169 test_trendline_lines_168 test_trendline_geometry_167 test_trendline_pivots_166 test_trendline_study_165 test_trendline_fills_164 test_trendline_data_163 test_elliott_study_145 test_elliott_sessions_146 -q
```
