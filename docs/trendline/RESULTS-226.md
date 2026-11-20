# Sprint 226 · EV H4 publication timing scenarios

20 November 2026. Compare two H4 close definitions on the same 2024
EURUSD ordinary-hours schedule. One uses the nominal end of EV's UTC
H4 bucket. The other clips the bucket to the end of its last scheduled H1
child. Both use the first scheduled H1 opening at or after the
modeled close and expire the opportunity at the next scheduled H4
close. The test uses the 2024 sample as a scenario for the frozen
Level B entry rule.
[Calendar and gap evidence](RESULTS-224.md) · [UTC resampling evidence](RESULTS-225.md) · [Frozen entry rule](PROTOCOL.md#c4-entry-and-data-level-semantics)

## Scope

Read only the retained Sprint 224 timestamps and coverage summary.
Bind the summary by SHA-256 and reconstruct the same ordinary week
schedule. Retain all scheduled hours and parent buckets, even when
the publication omits them. Require published coverage of every
scheduled child and the first scheduled entry hour when calculating
the coverage-adjusted ceilings. Keep exact holiday closure times
unresolved. The coverage check establishes file-row presence. Price
availability and decision order remain separate evidence.

Compare clock-based publication at the scenario close and two
seconds after it. Repeat with a model that waits until the next
scheduled H1 open as the earliest possible quote. The two-second
delay is the existing illustrative sensitivity case. Count exact
ties separately and give a conditional ceiling if the decision can
be shown to precede the opening. Read no quote archives or prices
and run no strategy rules. [Prior publication model](RESULTS-211.md)

## Results

The 6,288 scheduled hours form 1,624 H4 buckets. Thirteen H4 buckets
have at least one missing H1 child. This independently reconciles with
Sprint 225's eight absent buckets and five published buckets with gaps.
Clipping advances 18 Friday closes by two hours and 34 by three hours.
The time from those closes to the next scheduled H1 rises from 45–46
hours to 47–49 hours. Both models select the same first H1 slots.
[Source coverage evidence](RESULTS-225.md)

| Publication model | Delay | Strictly early | Tied | Late | No following slot | Coverage complete and strictly early | Coverage complete and tied |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Clock at modeled close | 0 ms | 52 | 1,571 | 0 | 1 | 52 | 1,558 |
| Clock at modeled close | 2,000 ms | 52 | 0 | 1,571 | 1 | 52 | 0 |
| Wait for first possible quote | 0 ms | 0 | 1,623 | 0 | 1 | 0 | 1,610 |
| Wait for first possible quote | 2,000 ms | 0 | 0 | 1,623 | 1 | 0 | 0 |

At zero delay in either publication model, 13 otherwise timely or tied
slots are blocked by published coverage. Three lack an H4 child, one
lacks the first scheduled H1 row, and nine lack both. The audit keeps
the first scheduled H1 opening fixed in all cases. Each reported tie
requires a decision-before-opening order. If the opening quote itself
releases the H4 decision, that order is impossible for the same quote,
even at zero processing delay. [Quote-dependent model](RESULTS-209.md)

The 52 strictly early clock-based slots are a coverage-adjusted
timing ceiling for the 2024 scenario. Actual setup geometry, spread
and opening quote receipt still govern entry. The exact closure and
delivery model for the intended development period remains open.

## Verification and disposition

```sh
mkdir -p reports/trendline-source-226
PYTHONPATH=src python3 -m tools.ev_publication_timing_226 reports/trendline-source-226/ev-2024-h4-publication-timing.json
```

The command takes its input from the retained Sprint 224 report and
checks the SHA-256 before using its intervals. The 50 targeted tests
passed, including the fixed opening slot, close clipping, and blocking
on coverage gaps. The canonical Phase 10 status matches Sprint 225 byte
for byte and remains `UNAVAILABLE` with null actual counts.
