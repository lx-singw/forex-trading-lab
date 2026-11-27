# Sprint 236 · Level B opening evidence deadline

28 November 2026. Apply the historical Level B counter's completed
opening-bar receipt deadline to the retained Exness and EV calendars.
Sprint 233 and Sprint 234 tested whether the opening itself preceded
expiry. A completed-bar opening assumption also depends on when the
opening bar is available to the counter.
[EV timing sensitivity](RESULTS-233.md) · [Exness weekend comparison](RESULTS-234.md) · [Historical opening contract](RESULTS-221.md)

## Timing calculation

Select the first scheduled H1 open strictly after the H4 decision
under the frozen delayed-entry trial. For the clock scenario, place
the decision two seconds after the scheduled H4 close. For the
quote-dependent scenario, place it two seconds after the first
possible quote, represented by the first scheduled H1 open at or
after the close. Require entry strictly before next-H4 expiry and
before partition liquidation.
[Frozen delayed-entry trial](RESULTS-230.md)

For a `bar_open_assumption`, the loader sets the earliest available
time to the selected H1 end plus the calendar finalization delay.
The resolver accepts opening evidence available exactly at expiry.
Evidence any later expires the attempt. Use a two-second minimum
opening-bar delay, consistent with the candidate schedules. A slot
whose H1 ends exactly at expiry is therefore already too late under
this assumption. Preserve the original slot selection when timing
evidence fails.
[Opening input and expiry behavior](RESULTS-221.md)

| Calendar scenario | H4 release | Selected H1 slots before expiry and liquidation | Too late as completed bars | Completed-bar timing ceiling |
| --- | --- | ---: | ---: | ---: |
| Exness 2022 ordinary hours | Clock | 1,576 | 17 | 1,559 |
| Exness 2022 ordinary hours | First possible quote | 1,576 | 34 | 1,542 |
| EV 2021–2022 holiday scenario | Clock | 3,154 | 35 | 3,119 |
| EV 2021–2022 holiday scenario | First possible quote | 3,154 | 70 | 3,084 |

These are schedule ceilings for the specified release times and
minimum receipt delay. They precede the source, opening-price,
coverage and strategy filters. Sprint 233 separately flags two
EV clock-selected slots whose first M5 labels are late. This
calculation uses calendar metadata for both candidates, so that
source-specific exclusion is outside the table.
[Exness scenario](RESULTS-220.md) · [EV scenario](RESULTS-232.md) · [EV source checks](RESULTS-233.md)

The Exness clock exclusions are Friday 21:00 UTC openings. The
quote-dependent scenario also excludes winter Sunday 23:00 slots.
The same Sunday restriction applies to all four January weekends
in Sprint 234. Their observed source-label lags plus two seconds
still select Sunday 23:00 under the quote-dependent scenario.
The H1 bar ends at 00:00, the next H4 expiry, and can only become
available later under the assumed delay. All five sampled July
weekends have time before expiry under this schedule. Eligibility
of the selected price pairs and actual receipt remain open.
[Exness source labels and sample scope](RESULTS-234.md)

## Implication and verification

A source review for the completed-bar route needs to establish that
the selected opening price and spread are supported and that their
evidence can reach the counter by expiry. The `paired_quote` route
has its own boundary timestamp and receipt requirements.
Phase 10 remains `UNAVAILABLE` with null actual counts.
[Historical opening contract](RESULTS-221.md) · [Exness provenance review](RESULTS-235.md)

```sh
mkdir -p reports/trendline-source-236
PYTHONPATH=src python3 -m tools.level_b_opening_deadline_236 reports/trendline-source-236/opening-deadline.json
```

The diagnostic verifies the two retained scenario report hashes and
their embedded calendar digests. An independent calculation used the
raw calendar edges and fabricated opening prices to check each
selected slot against the historical opening resolver. It reproduced
all four ceiling calculations and the four January exclusions.
All 55 targeted tests passed. The canonical Phase 10 status report
matches Sprint 235 byte for byte. The audit used calendar and source
metadata.
