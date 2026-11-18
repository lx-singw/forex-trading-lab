# Sprint 187 · Level B receipt-time viewer

18 November 2026. The offline viewer reads the saved Level B run and
groups evidence by receipt time. The cursor starts at the partition
opening. A completed H4 candle, a confirmed pivot or a line revision
appears when its evidence is available. The H4 chart distinguishes
action and safety lines and marks a poked line at the penetrating
candle. The inspector shows the recorded setup and account facts
at the current receipt.

Account fills and marks use their recorded receipt times. Fill
markers are positioned by their modeled effective H4 time after
receipt. Stops and targets show for the visible held position. A
skipped entry appears when the gate resolves. The viewer exposes an
unresolved boundary liability at the saved report endpoint.

## Export

```sh
PYTHONPATH=src python3 scripts/trendline-breaks-173.py SOURCE.json HOURS.json SAVED_RUN --tick-size 0.0001 --ledger
PYTHONPATH=src python3 scripts/trendline-viewer-187.py SOURCE.json SAVED_RUN NEW_VIEW_DIRECTORY
```

Use the fixture's declared tick. Open `replay.html` in a browser.
`manifest.json` records the input file hashes, profile, geometry basis,
partition and HTML hash. The exporter checks that the source, setup,
entry, exit and account reports belong to the same run and code bindings.
It derives confirmed pivots using the bound H4 pivot detector and the
saved publications. Its line and account displays use saved events.

The bundled page uses a receipt slider, next and previous controls,
evidence filters and layer toggles. Select a receipt item or visible line
in the inspector, or use the recent evidence list to jump to an observed
event. The chart displays up to 120 received H4 candles, with gaps
positioned by their scheduled index.

## Verification

Seven viewer tests and 53 retained replay, entry, exit, risk and
ledger tests passed. The invented `TRL_BRK3_E1` example exported 64
receipt groups. The cursor shows a reservation before the entry fill,
then reveals the fill and its stop at receipt. The settled example
shows `$9,968.44` cash and `−$31.56` net. A separate invented example
reveals the crossed-stop skip at the opening row receipt. An earlier
saved replay agrees with the matching prefix of the full run, apart
from the earlier replay's explicit endpoint.

Chrome checks at 1440 × 1000 and 390 × 844 exercised receipt stepping,
the fills filter, the penetration inspector, account state and rewind.
The mobile viewport had no horizontal overflow. All inputs were
invented and the results describe viewer behavior.

Phase 8 continues with Level Q views, provisional pivots,
more detailed trade-linked explanations, retrospective browsing,
ledger exports and manual annotations.
