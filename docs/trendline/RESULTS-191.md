# Sprint 191 · Manual lines and Phase 8 acceptance

18 November 2026. The offline viewer compares the engine and manual
lines on the same EURUSD H4 candles, receipt or retrospective window,
and price axes. The panes sit side by side on wide screens and stack
on narrow screens. Annotations load from a local JSON file, using the
chart identity in the exported template.

## Load manual lines

Open **Manual annotations**, save a copy of `annotation-template.json`,
and fill in its `lines` array. The chart binding identifies the source,
symbol, timeframe, data level, geometry basis and partition. Each line
has two anchors on distinct saved H4 openings. The candle inspector's
**Recorded fields** shows each opening as `start` in epoch milliseconds.
Supply the anchor prices as positive decimal strings.

```json
{
  "label": "Manual support",
  "a": {"bar_start_ms": 947052000000, "price": "1.10002"},
  "b": {"bar_start_ms": 947138400000, "price": "1.1006"},
  "available_at_ms": 947469602003,
  "extend_right": true
}
```

The values shown belong to the invented Level Q stop example. In
**Receipt replay**, the drawing appears at the first cursor position
at or after its declared `available_at_ms`. That timestamp must be at
or after both anchor receipts. Use `null` for an undated
drawing to show it in **Retrospective** once its anchors are available.
`extend_right` projects the line beyond the second anchor through the
visible H4 window. **Clear** removes the comparison from the page. The
viewer accepts annotation files up to 256 KiB. The export manifest records the
template's hash. [Viewer export command](RESULTS-188.md#export)

## Phase 8 visual acceptance

| Invented run | Observed evidence |
| --- | --- |
| Level Q FXR target | The entry showed the original action and safety revisions and a fixed `1.1068` target. The `TARGET_QUOTE` exit appeared at `2000-03-07 02:00:00.702 UTC`, with net USD `49.06`. |
| Level Q BRK3 stop | The inspector showed the entry and exit quote source times and receipts, the original setup lines, and the `STOP_QUOTE` close at `2000-01-10 02:00:02.004 UTC`, with net USD `−37.02`. |
| Level B BNC skipped entry | The setup showed the contact line at its H4 receipt. The position stayed flat when the next H1 receipt resolved the reservation as `STOP_ALREADY_CROSSED`. |

All 52 targeted tests passed. Chrome checks verified the paired charts
at 1440 × 1000 and 390 × 844.
The dated annotation first appeared at its declared receipt. The undated
annotation appeared in retrospective mode, and returning restored the
original fill selection. An annotation from a different chart was rejected.

Phase 8 software acceptance is complete on invented inputs. Phase 9
starts with the success and failure verification matrix.
[Phase 9 test matrix](../tori_trendline_strategy_full/TORI-TRENDLINE-BUILD-ROADMAP.md#phase-9-verification-size-m)
