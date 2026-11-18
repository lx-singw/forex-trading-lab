# Sprint 177 · BNC bounce replay

18 November 2026. `TRL_BNC_E1` now evaluates completed H4 candles against
already eligible support and resistance. A candidate's wick must stay on the
correct side within a quarter of the current ATR. The close must finish
strictly on that side. The candidate needs six scheduled indices of spacing
from its last confirmed touch and earlier approach. An in-band, close-confirmed
approach updates that spacing even when formation or spacing blocks a trigger.
[Sprint 177 protocol note](PROTOCOL.md)

A group is consumed at the contact before ranking or price checks. Opposing
contacts consume both groups and abstain. A selected contact supplies its
own E1 stop geometry, with the usual buffer and rounding. Its Level B attempt
uses the existing next-opening, expiry, cost and protection checks.

## Invented checks

| Case | Expected outcome |
| --- | --- |
| Mirrored contact at a distance of 0.5 with ATR 2 | Both trigger at index 51. Stops are 102.9 and 97.1. Base fills at the invented opens are 104.50014 and 95.49998. |
| Distance 0, 0.5001, or −0.0001 | Equality at the wick can qualify with a correct-side close. Outside the band produces no contact. Strict penetration pokes the line. |
| Close exactly at the line | No contact. |
| Last confirmed touch at index 46 | Index 51 is too close. In the independent path with the first approach at 52, six indices suffice. |
| Formation approach at 50 and another at 55 | Formation and then spacing block the two approaches. Spacing from 55 permits a contact at 61, including after restore. |
| Ordinary candle contact and a later wick | An equal neighboring low excludes pivot confirmation for the contact. It triggers immediately at the completed bar and the spent group stays consumed across restart. |
| Opposing contacts on the same candle | Both consume their groups and the replay abstains. |
| Pending CLI attempt resumed through the first H1 receipt | The resumed and uninterrupted entry reports match byte for byte. |

## Replay

```sh
PYTHONPATH=src python3 scripts/trendline-breaks-173.py SOURCE.json HOURS.json NEW_DIRECTORY --tick-size 0.1 --profile TRL_BNC_E1
```

Use the tick declared for the invented fixture. The setup report records
approaches under `contacts` and ties the protection to the selected action
line. The checkpoint reconstructs contact history along with the original
bar prefix. Earlier checkpoints require their source-matched checkout or a
replay from the original input.

Phase 6 still has disabled DLY and the remaining setup acceptance checks.
Account simulation and management of protection after entry are Phase 7.

## Verification

All 388 targeted tests passed. The 7 BNC tests took 68.023 seconds, the 33
lifecycle tests took 431.210 seconds, the 6 FXR tests took 233.914 seconds,
and the remaining 342 checks took 452.973 seconds.

```sh
PYTHONPATH=src:tests python3 -m unittest test_trendline_bounce_177 -v
PYTHONPATH=src:tests python3 -m unittest test_trendline_acceptance_171 test_trendline_engine_170 -q
PYTHONPATH=src:tests python3 -m unittest test_trendline_fxr_175 -q
PYTHONPATH=src:tests python3 -m unittest test_trendline_brk2_176 test_trendline_entries_174 test_trendline_breaks_173 test_trendline_context_172 test_trendline_selection_169 test_trendline_lines_168 test_trendline_geometry_167 test_trendline_pivots_166 test_trendline_study_165 test_trendline_fills_164 test_trendline_data_163 test_elliott_study_145 test_elliott_sessions_146 -q
```
