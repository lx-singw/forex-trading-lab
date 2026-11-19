# Sprint 224 · EV 2024 calendar diagnostic

19–20 November 2026. Compare EV Trading Labs' already-seen 2024 EURUSD
file timestamps against a separately documented upstream broker
schedule. Dukascopy describes ordinary FX trading from Sunday 17:00
through Friday 17:00 New York time. The dated spring and autumn notices
confirm the 2024 US clock-change dates. EV labels its resampled bars on
the UTC grid. The ordinary-hours model contains no holiday overrides.
[Broker hours](https://www.dukascopy.com/swiss/english/forex/forex-trading-accounts/link/) · [March notice](https://www.dukascopy.com/swiss/english/about/ournews/daylight-saving-time-2024-in-the-us/) · [November notice](https://www.dukascopy.com/swiss/english/about/ournews/daylight-savings-time-ends-in-us-dbl202961) · [EV catalogue](https://evtradelabs.com/data)

## Scope declared before download

Make one anonymous HTTPS GET per Sprint 223 file in the original
H1 then M5 order. Use the same size and SHA-256 for each file and
stop on mismatch. Keep the source bodies and any parsed prices in
memory. Use timestamps only for the comparison. Retain file hashes,
counts and UTC discrepancy intervals in an ignored report. Use the
year's half-open UTC bounds and classify expected H1 absences,
observed H1 outside ordinary hours, and missing M5 slots within
each published H1 hour. Do not infer a closure from absent bars.
No new year, direct upstream archive request or strategy calculation.
[Pinned files and use scope](RESULTS-223.md)

Use January 1–2, December 24–26 and December 31 UTC as display
windows for the published Christmas and New Year notices. They are
broad diagnostic windows. The notices refer readers to a rolling
calendar whose accessible page did not list the exact 2024 EURUSD
holiday intervals for this comparison.
[2023–24 holiday notice](https://www.dukascopy.com/swiss/english/about/ournews/market-closures-on-christmas-and-new-year-dbl202761) · [2024–25 holiday notice](https://www.dukascopy.com/europe/english/about/ournews/market-closures-during-x-mas-and-new-year-dbl203022/) · [Trading Breaks Calendar](https://www.dukascopy.com/swiss/english/marketwatch/trading-breaks-calendar/)

## Results

The two downloads matched the Sprint 223 digests. EV published 6,247
of the 6,288 ordinary H1 slots, with no H1 or M5 rows outside ordinary
hours. All 41 missing H1 slots were inside the predeclared holiday
notice windows. The intervals below record absences in EV's file.

| Start UTC | End UTC, exclusive | Missing H1 slots |
| --- | --- | ---: |
| 1 January 00:00 | 1 January 22:00 | 22 |
| 24 December 22:00 | 25 December 00:00 | 2 |
| 25 December 04:00 | 25 December 05:00 | 1 |
| 25 December 08:00 | 25 December 22:00 | 14 |
| 31 December 22:00 | 1 January 2025 00:00 | 2 |

EV still published nine H1 bars on 25 December. Within the 6,247
published H1 hours, the 74,949 M5 bars leave 15 absent five-minute
slots. Nine fell on 25 December. The other six fell on 28 April,
12 May, 19 June, 24 June and 4 July. The full UTC discrepancy intervals
are recorded in the local aggregate report.

The calendar fits the observed ordinary H1 hours in this sample.
Holiday notices corroborate the dates of the hourly discrepancies
at a broad level. The exact closure boundaries and the reasons for
the intrahour omissions remain unverified. EV documents UTC-aligned
H4 and D1 buckets. Dukascopy's JForex documentation describes
session-aligned candle formation. Matching H1 labels are insufficient
to validate the H4 and D1 session boundaries for the study.
[EV catalogue](https://evtradelabs.com/data) · [JForex candle formation](https://wiki.dukascopy.com/en/manuals/jforex4-desktop/trading-sessions-logic)

## Verification and disposition

```sh
mkdir -p reports/trendline-source-224
PYTHONPATH=src python3 -m tools.ev_calendar_224 reports/trendline-source-224/ev-2024-calendar.json
```

The 38 targeted tests passed, including the US DST boundaries, H1
and M5 discrepancy accounting, historical input, and Phase 10 status.
The canonical status report matches Sprint 223 byte for byte.
Phase 10 stays `UNAVAILABLE` with null actual counts. The 2024
diagnostic leaves exact source use, opening quote and availability
evidence, and the full development and warmup calendar open.
