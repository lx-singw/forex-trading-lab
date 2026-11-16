# Hand-authored trendline fixtures — sprint 161

All prices and timelines in golden-161.json are deliberately invented. They are
not captured EURUSD history, broker terms, prospective collection dates or market
performance. Forty scenarios have explicit LONG and SHORT inputs/expectations
(80 records). Expectations were written before a trendline engine existed.

Each case records its rule IDs, inputs, literal expected outcome and a readable
hand calculation. Component vectors deliberately supply pivots, candidate states
or preconditions; they do not prove a candle-to-trade engine. G02 has seven
explicit OHLC bars per direction; G35 has49 per direction with warmup and delayed
formation. No source prices were used to choose them. Their arithmetic and
existing batch-pivot crosschecks are verification of fixtures, not acceptance of
new strategy software. Independent human reading has not been performed.

Sprint162 performed a separate primary-agent rule/readability review. G01's
component formation was corrected from15/trigger30 to30/trigger31: age first
qualifies at30, so the trigger must follow. Its line/stop arithmetic is updated
and checked. The original161 bytes remain in Git; no rule or market result changed.

| Pair | Expected distinction |
| --- | --- |
| G01 | Valid three-touch close-break; opposing safety, stop and distance |
| G02-G03 | Delayed pivot, equal extrema and dual-extreme rejection |
| G04-G07 | Wick poison, correct-side tolerance, anchor conflict, spacing5/6/7 |
| G08-G10 | Exactly2/>=3, age29/30, span89/90, slope/angle boundaries |
| G11-G12 | No safety consumes attempt; stop/spread/window rejection |
| G13-G15 | Non-pivot bounce, missed/formation-bar break, simultaneous conflict/ranking |
| G16 | Gap loss4.2 versus planned2.3, excess1.9 per unit |
| G17-G20 | Every one of the eight D1 direction/bias outcomes |
| G21-G24 | Projected/current stop, sizing, restart, pre-fill/prospective protection |
| G25-G26 | Disabled DLY alternatives; anchored levels and physical duplicate removal |
| G27-G30 | Future invisibility, partition endpoint, adverse ambiguity, validated dedupe |
| G31-G34 | Poked safety, daily latch, cap/retirement, hypothetical financing/costs |
| G35 | Full49-candle prefix; formation at47, trigger48, ATR263/140 |
| G36-G40 | Tightening/replacement, E2 target, SMA/RMA, rounding,28 unavailable cells |

To inspect from WSL:

```sh
python3 scripts/verify-trendline-fixtures.py
```

The checker reads only the explicitly named source fixture/rulebook and existing
batch-pivot source. It checks JSON identity/references, OHLC bounds and selected
rational arithmetic. It neither imports market data nor runs an order path.
Failures should be investigated against the written rule, not fixed by blindly
changing expectations to match future implementation. Append decisions and bump
the protocol revision if the economic rule changes.

The source JSON is the canonical hand-authored test specification. Large local
authoring/verification output remains in ignored reports/, not Git. No trendline
production engine or fixture-derived performance claims are present in this sprint.
