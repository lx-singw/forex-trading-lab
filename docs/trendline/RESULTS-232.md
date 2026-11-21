# Sprint 232 · EV holiday calendar scenario

22 November 2026. Trace the four missing-hour intervals in the
2020–2022 EV EURUSD files to date-specific schedule evidence. The
archived pages establish that Dukascopy published holiday notices.
The corresponding historical EURUSD schedule table remains unverified.
[Observed gaps](RESULTS-231.md) · [December 2019 notice](https://www.dukascopy.com/swiss/english/about/ournews/market-closures-on-christmas-and-new-year-dbl201708) · [December 2020 notice](https://www.dukascopy.com/swiss/english/about/ournews/market-closures-on-christmas-and-new-year-2020)

## Evidence from the calendar archive

The Wayback capture on 31 December 2019 preserves Dukascopy's
Trading Breaks Calendar page and the parameters for its embedded
widget. The closest capture returned for December 2020 and January
2021 was from October 2021. Both pages load a separate trading-breaks
widget. The archived loader constructs the widget address. Availability
queries for that address and two parameter variants returned no
captures. A separate archive index query timed out. The snapshots
therefore establish the publication route and leave its dated
schedule rows open.
[December 2019 capture](https://web.archive.org/web/20191231024017/https://www.dukascopy.com/swiss/english/marketwatch/trading-breaks-calendar/) · [October 2021 capture](https://web.archive.org/web/20211009152554/https://www.dukascopy.com/swiss/english/marketwatch/trading-breaks-calendar/)

Dukascopy's December 2013 FX notice gives a Christmas break from
08:00 to 22:00 UTC and a New Year break from 31 December at 22:00
to 1 January at 22:00. Applying those times as an analogy accounts
for each EV absence in the proposed scope. The notice applies to
2013–2014. Another lead is JForex's `IDataService`, which documents
instrument-specific past offline intervals. Its output for these
dates and the correspondence to EV's archive remain unverified.
[Dated FX schedule](https://www.dukascopy.com/europe/english/about/ournews/holiday-trading-hours-schedule-dbl199995/) · [Market Hours documentation](https://wiki.dukascopy.com/en/development/strategy-api/instruments/market-hours/) · [Instrument-specific offline intervals](https://www.dukascopy.com/client/javadoc3/com/dukascopy/api/IDataService.html)

## Scenario reconciliation

Apply the older notice's clock times to the affected dates as a
retrospective scenario. Keep the ordinary weekly schedule and UTC
parent grid. Clip the first proposed holiday to the warmup start.
Keep the December 2020–January 2021 break as a single closure across
the development seam.

| Candidate closure start, UTC | End, exclusive, UTC | Ordinary H1 slots removed |
| --- | --- | ---: |
| 2020-01-01 00:00 | 2020-01-01 22:00 | 22 |
| 2020-12-25 08:00 | 2020-12-25 22:00 | 14 |
| 2020-12-31 22:00 | 2021-01-01 22:00 | 24 |

The historical calendar parser accepts the scenario and its 18,730
H1 slots match the published timestamps exactly. The 4,839 H4 and
938 D1 windows match EV's advertised totals for the three years.
The comparison verifies parent counts. The parent file contents for
these years remain outside the audit. With two-second publication,
the modeled 2020 warmup has 6,250 H1, 1,615 H4 and 314 D1 complete
windows at the seam.
[Archive observations](RESULTS-231.md) · [Parent inventory](RESULTS-229.md)

The delayed-entry scenario retains 3,152 potential slots under
clock-based publication and 3,154 when the decision waits for the
first possible quote. The H4 child and selected-opening coverage
checks still exclude the two late 2021 opening labels whenever those
slots are selected. Holiday classification has no effect on these
two timing totals. [Earlier timing comparison](RESULTS-231.md#effect-on-the-delayed-entry-scenario)

## Verification and disposition

```sh
mkdir -p reports/trendline-source-232
PYTHONPATH=src python3 -m tools.ev_holiday_calendar_232 reports/trendline-source-232/ev-holiday-calendar-scenario.json
```

The command pins the exact Sprint 231 coverage receipts and generates
an unqualified calendar with canonical digest
`2c87061d7dd6dd24d21460427ff32c08108a02509067b6c583132b27f20a36db`.
All 16 targeted tests passed. The canonical Phase 10 report matches
Sprint 231 byte for byte. Phase 10 remains `UNAVAILABLE`
with null actual counts. Admission still needs date-effective
calendar evidence, source-use qualification and a reviewed opening
availability model. Work used public calendar documentation and
retained coverage metadata.
