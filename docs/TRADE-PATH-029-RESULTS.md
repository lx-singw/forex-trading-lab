# Frozen trade-path diagnosis 029 — complete, 2026-10-06

Most stopped trades had a small favorable move, but substantially fewer had
meaningful progress. Across all 30 overlapping scenario paths: **184 stops;
178 with prior positive net liquidation; 79 reaching +0.5R; 36 reaching +1R**.
Six never became positive; 105 never reached +0.5R. This does not mean an engine
could have known when to close profitably. These are descriptions of completed
paths, not new strategy returns or a recoverable-profit forecast.

The audit covers **all 266 trades**, with exact source entry/exit sequences,
21,279,255 inclusive trade-quote observations over 8,732,543 distinct cached
source rows. Same quotes recur across cost/candidate paths; observations and
cases are not independent trials. Windows are the same post-warmup partial
January/April/July2024 development slices, not continuous monthly accounts.

Net liquidation includes bid/ask, modeled exit slippage, full round-trip fees
and financing accrued to that quote. Initial R excludes those costs. Actual
modeled target fills cap endpoint excursions; overshooting quotes are not
credited. Positive mark is strictly >0; 0.5R/1R comparisons use the declared
literal thresholds, and progress must occur before the stop exit sequence.

| Window | Candidate | Stops base / adverse | Prior positive base / adverse | Prior +0.5R base / adverse | Prior +1R base / adverse |
| --- | --- | ---: | ---: | ---: | ---: |
| January | C00 | 6 / 6 | 6 / 6 | 2 / 1 | 0 / 0 |
| January | C02 | 14 / 14 | 13 / 12 | 5 / 3 | 2 / 2 |
| January | C04 | 6 / 6 | 6 / 6 | 4 / 3 | 3 / 3 |
| January | C05 | 3 / 3 | 3 / 3 | 1 / 0 | 0 / 0 |
| January | C06 | 6 / 6 | 6 / 5 | 2 / 0 | 0 / 0 |
| April | C00 | 4 / 4 | 4 / 3 | 1 / 1 | 0 / 0 |
| April | C02 | 9 / 9 | 9 / 9 | 6 / 5 | 2 / 2 |
| April | C04 | 8 / 8 | 8 / 8 | 5 / 5 | 3 / 3 |
| April | C05 | 5 / 5 | 5 / 5 | 3 / 3 | 1 / 1 |
| April | C06 | 6 / 6 | 6 / 6 | 5 / 4 | 2 / 2 |
| July | C00 | 4 / 4 | 4 / 4 | 3 / 3 | 1 / 1 |
| July | C02 | 10 / 10 | 10 / 9 | 2 / 2 | 1 / 1 |
| July | C04 | 3 / 3 | 3 / 3 | 2 / 2 | 1 / 1 |
| July | C05 | 3 / 3 | 3 / 3 | 2 / 2 | 1 / 1 |
| July | C06 | 5 / 5 | 5 / 5 | 1 / 1 | 1 / 1 |

## Implication for the new challengers

At base costs C05 has 11 stops: all became positive, six reached +0.5R and two
reached +1R before failing. Under adverse costs those counts become 11/5/2.
C06 has 17 stops: base counts 17/8/3; adverse 16/5/3. Thus the adverse model
has only **10 of 28** stopped challenger cases reaching +0.5R, and five reaching
+1R. A late protective stop cannot address most of these stopped entries.

April has three C05 and four C06 adverse stopped cases with prior +0.5R.
That supports testing whether a single protective adjustment can reduce a
particular reversal mechanism, while retaining the negative evidence elsewhere.
It does not prove that this would eliminate April's loss. Newly closed trades
would change later exposure, sizing and entry opportunities.

All eight profitable C05/C06 scenario cells become negative when their largest
winner is removed. This is a concentration sensitivity, not a rule to remove
that winner or a causal performance estimate. The relatively few target winners
matter; a protection rule could cut them short and damage the existing gains.
Full all-30 concentration/excursion summaries are in the sealed summary and CSV.

## Verification and limitations

Preflight verified all 786 prior bindings, 752 archive members and 34 external
bindings, including the exact 028 code/input/report links. The new ledger freezes
212 bindings and the first/last trade indices in every scenario before extraction.
**368 tests pass, including 12 new path tests.** Independent source/Fraction
checking verifies all 266 endpoints and 1,509 reported witnesses. All 60 fixed
first/last full paths recompute the same extrema and first-hit sequences under
a separate calculation. No extraction/check failures or missing/ambiguous source
matches. Original trades, returns, strategies and costs remain unchanged.

Each window used one extraction pass plus one independent verification pass
over the same cached input. No new market acquisition or strategy replay.
These tests establish arithmetic and lineage consistency, not retrospective
source-clock/session certification, broker costs, executable guarantees or an
unseen edge. Annual eligibility remains failed; 2025 stays excluded and reserved
Nov–Dec2026 stays unexamined. Orders remain unavailable.

Next: `EXIT-EXPERIMENT-030-PLAN.md` declares **one** fixed stop-protection
hypothesis after +0.5R net liquidation, for C05/C06 against unchanged controls.
It takes effect on subsequent sequences, estimates costs at arming, and allows
gap/slippage/further-financing losses. It is not implemented or evaluated here.
The trigger is informed by reused development evidence; every result, including
lost target winners and altered entry paths, must be reported in the next batch.
