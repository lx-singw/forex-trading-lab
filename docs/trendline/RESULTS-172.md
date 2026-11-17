# Sprint 172 · Phase 5 daily context

17 November 2026. `TRL_BRK3_E1_D1` uses the completed daily close to find
the nearest eligible support below it and resistance above it. The same D1
line engine supplies confirmed anchors, a 15-bar minimum age, strict
penetration checks and lifecycle eligibility. The distance limit is three
daily ATRs, inclusive. An equal-price line is on neither side. If several
lines share the nearest distance, the diagnostic lists their IDs.
[Protocol revision 6](PROTOCOL.md)

| Completed D1 context | Long outcome | Short outcome |
| --- | --- | --- |
| Support only, BULLISH | ALLOW | CONTEXT_CONFLICT |
| Resistance only, BEARISH | CONTEXT_CONFLICT | ALLOW |
| Both, NEUTRAL | CONTEXT_NEUTRAL | CONTEXT_NEUTRAL |
| Neither or unavailable evidence, UNAVAILABLE | CONTEXT_UNAVAILABLE | CONTEXT_UNAVAILABLE |

The original eight expectations in G17–G20 and a separately expressed rule
agree with the production table. A 34-session invented channel gives
UNAVAILABLE at daily index 30, BULLISH at 31, NEUTRAL at 32 and BEARISH at 33
after a wick invalidates support. The same path aggregated from H1 shows
NEUTRAL at the first H4 close of session 33 and BEARISH when its D1 and final
H4 candles publish together. The H4 prefix and its context decisions match
the completed replay through that earlier H4 publication.

The tests cover exact distance and side boundaries, missing and delayed daily
receipts, declared closures, indicator warm-up, zero ATR, incomplete search,
future or reversed publications, and full H4 report equality for all four
baseline profiles with the gate off.

## Run the diagnostic

```sh
PYTHONPATH=src python3 scripts/trendline-context-172.py SOURCE.json HOURS.json NEW_REPORT.json
```

Use the sprint 163 invented-data format and a new output path. Optional
`--as-of` takes the receipt timestamp in milliseconds. For an invented
validation partition supply its matching `--unlock-receipt`. The output holds
the H4 replay and the matched daily snapshot with both table outcomes per H4
publication. Clock-only frames carry no setup evaluation. The existing H4
line reports are returned for the four other `--profile` values.

`DailyContext.observe`, `DailyContext.snapshot` and `context.outcome` expose
the same logic for Phase 6. Feed completed D1 publications before H4 at equal
receipt times. Phase 6 will apply the gate to the actual proposed trade
direction after trigger consumption. The sprint's diagnostics use invented
data and the historical source admission work remains open.

Protocol revision 6 and the public metrics accessor change the source
bindings. Use the corresponding checkout to restore earlier checkpoints,
or rebuild the prefix from its original invented data.

## Verification

All 345 targeted tests passed across three runs. The 9 Phase 5 tests took
54.316 seconds, the 33 line acceptance and lifecycle tests took 315.729
seconds, and the 303 retained checks took 84.239 seconds.

```sh
PYTHONPATH=src:tests python3 -m unittest test_trendline_context_172 -q
PYTHONPATH=src:tests python3 -m unittest test_trendline_acceptance_171 test_trendline_engine_170 -q
PYTHONPATH=src:tests python3 -m unittest test_trendline_selection_169 test_trendline_lines_168 test_trendline_geometry_167 test_trendline_pivots_166 test_trendline_study_165 test_trendline_fills_164 test_trendline_data_163 test_elliott_study_145 test_elliott_sessions_146 -q
```
