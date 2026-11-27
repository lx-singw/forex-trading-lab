# Sprint 233 · EV publication sensitivity

27 November 2026. Measure how the assumed H4 publication time changes
the scheduled opening picked by the frozen delayed-entry trial. Use
only the retained EV timestamp receipts and reconciled holiday scenario
for 2020–2022. Count schedules in the 2021–2022 development partition.
[Delayed-entry trial](RESULTS-230.md) · [Timestamp receipts](RESULTS-231.md) · [Holiday scenario](RESULTS-232.md)

## Compare the opening selected by each model

For each of 3,224 development H4 closes, start the modeled delay at
the scheduled close or at the first possible quote. Represent the
first possible quote by the first scheduled H1 open at or after the
H4 close. Select the first H1 open strictly after the modeled decision.
Apply the next H4 close and partition liquidation as exclusive
cutoffs. Reject either of the two development openings whose first
published M5 label is late if the model selects it. The trial gives
that H4 decision no entry after a failed opening check.

Sweep the delay from zero through four hours. Selection can change
only when the delay reaches the difference between a model's release
time and a scheduled opening. The resulting breakpoints are zero,
one, two and three hours. Checks at each boundary, one millisecond
before the positive boundaries, and at intermediate delays reproduce
the bands below. The sweep describes model behavior. It supplies no
estimate of an actual publication delay.

| Modeled delay | Clock slots | First possible quote slots | Both select same opening | Both select different openings | Clock only | First possible quote only |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 to under 1 hour | 3,152 | 3,154 | 3,051 | 101 | 0 | 2 |
| 1 to under 2 hours | 3,117 | 3,084 | 3,016 | 68 | 33 | 0 |
| 2 to under 3 hours | 3,117 | 3,016 | 3,016 | 0 | 101 | 0 |
| 3 through 4 hours | 101 | 0 | 0 | 0 | 101 | 0 |

At two seconds, all 101 differences where both models find an opening
come from Friday H4 closes. The clock model selects the Sunday reopen.
The quote-dependent model selects one hour later. Two other Sunday
reopenings have late first M5 labels. The clock slots exclude them
and the quote-dependent scenario selects the following hour. Similar
aggregate slot counts can therefore conceal a different H1 opening,
which would change the price and cost inputs to the feasibility count.

## Calendar evidence and disposition

Dukascopy's December 2020 leverage notice identifies the Sunday
reopenings when leverage returned to normal. It leaves the exact FX
close and reopen clocks unresolved. JForex documents a method for
instrument-specific historical offline intervals. The documented
standalone SDK path uses account authentication. Whether the method
returns the exact holiday closures and corresponds to EV's archive
is unverified. The sprint used public documentation and retained
timestamp metadata.
[December 2020 leverage notice](https://www.dukascopy.com/europe/english/about/ournews/weekend-leverage-at-christmas-and-new-year/) · [Offline intervals API](https://www.dukascopy.com/client/javadoc3/com/dukascopy/api/IDataService.html#getOfflineTimeDomains-long-long-com.dukascopy.api.Instrument-) · [SDK connection documentation](https://www.dukascopy.com/wiki/en/development/get-started-api/use-jforex-sdk/sdk-client/)

The Phase 10 status remains `UNAVAILABLE` with null actual counts.
Source admission still needs date-effective closure evidence,
source-use qualification, and a reviewed model for H4 availability
and the selected H1 opening pair. Evidence that places Friday H4
publication and the Sunday reopening on the same clock would help
resolve the modeled difference. The frozen trial rule remains the
basis of the diagnostic.

## Verification

```sh
mkdir -p reports/trendline-source-233
PYTHONPATH=src python3 -m tools.ev_delay_sensitivity_233 reports/trendline-source-233/ev-delay-sensitivity.json
```

The command verifies the SHA-256 of the Sprint 232 scenario report and
all three Sprint 231 timestamp receipts. All 19 targeted tests passed.
A separate standard-library calculation used the retained calendar edges
and missing M5 spans to check all 11 delay rows, the four breakpoints
and the weekday and magnitude of the 101 shifts. The canonical Phase
10 status matches Sprint 232 byte for byte.
