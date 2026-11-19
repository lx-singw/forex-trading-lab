# Sprint 220 · Source review and opening calendar compatibility

19 November 2026. Exness remains the lead candidate for paired EURUSD
ticks. Its opening-price and receipt evidence still falls short of Phase
10 admission. The historical reader can now represent the existing
2022 scenario’s Sunday reopening at `:05` without shifting later H1 or
H4 edges. [Ordinary-hours model](RESULTS-208.md)

## Source review

| Route | Evidence and disposition |
| --- | --- |
| Exness public archives | The provider explicitly describes anonymous bid/ask downloads, spread analysis and backtesting. Its separate Personal Area documentation names different server sources by account type. The mapping to the public unsuffixed 2020–2022 archives and the retention terms for the full private study remain open. [Public archive guide](https://www.exness.com/blog/product/exness-tick-history-bid-ask-prices/) · [Personal Area documentation](https://get.exness.help/hc/en-us/articles/360021547851-Tick-history) · [Retention review](RESULTS-199.md) |
| Exness 2021 holiday lead | A dated FXPLUS affiliate notice lists 20:00 GMT+0 Forex closes on 24 and 31 December 2021 and 22:05 reopenings the following Sundays. The affiliate identifies itself as the operator. These are dates to corroborate with provider evidence for the exact series. Neither closure was imported into the calendar. [Dated affiliate notice](https://exn.fxsignup.com/en/news/2021122201.html) |
| Existing HistData | The publisher’s paired tick schema and fixed-EST statement are public. The existing 2020–2023 work found conflicting clock evidence and left session gaps unresolved. The retained files stay diagnostic. [Publisher specification](https://www.histdata.com/f-a-q/data-files-detailed-specification/) · [Clock evidence](../EXNESS-EVIDENCE-026-RESULTS.md) · [Normalization results](../NORMALIZATION-015-RESULTS.md) |
| TrueFX | TrueFX advertises millisecond top-of-book data and its terms describe internal use of the historical service. Access still goes through sign-in or registration, and the lab has no established access or verified year inventory. [Downloads](https://www.truefx.com/truefx-historical-downloads-2/) · [Terms](https://www.truefx.com/truefx-terms-and-conditions/) · [Earlier access review](../LABELS-017-RESULTS.md) |
| EV Trading Labs | The catalogue provides UTC bid and ask OHLC labels. The reviewed material still leaves the joint first observation, opening receipt, and upstream terms unresolved. [Catalogue](https://evtradelabs.com/data) · [Earlier methodology review](RESULTS-207.md) |

The nine retained January and July 2022 Sunday pairs first appear after the
modeled opening. Their paired spreads describe those later observations.
MetaQuotes documents that its native bar label stays on the time grid even
when the first tick comes later. The Level B opening assumption still needs
its own reviewed price, spread, and event order at the first scheduled open.
[Opening alignment](RESULTS-213.md) · [Prior quote bounds](RESULTS-214.md) · [MetaQuotes timeseries](https://www.mql5.com/en/book/applications/timeseries)

## Calendar verification

A historical session can use `leading_partial: true` together with
`partial: true` for a shortened first H1 or H4 interval. Its following
full-length intervals and optional shortened final interval must still
cover the explicit session. H4 edges still have to match H1 child edges.
Previous calendar records use the original terminal-shortening rule.

The metadata-only scenario repeats the dated ordinary weekly schedule
under the 2022 US DST model and splits D1 at UTC midnight. This models
312 D1 windows, including short Sunday and Friday sessions. Actual
archive holiday exceptions and D1 boundaries still need review. All
6,240 H1 and 1,612 H4 start and end pairs matched Sprint 208, including
52 shortened H1 openings and 52 shortened H1 closings. At a two-second
publication delay, the original 51 strictly early closes, 1,560 late
closes and one close with no following slot reproduced.

```sh
PYTHONPATH=src python3 -m tools.exness_2022_calendar_220 NEW-SCENARIO.json
```

The command writes the illustrative segments, calendar digest and timing
totals. It carries the `schedule_qualified: false` label and null strategy
counts. All 55 targeted tests passed. The canonical Phase 10 status
matched Sprint 219 byte for byte and remains `UNAVAILABLE`.
[Historical reader](RESULTS-217.md)

For the full-source path, preserve completed H1 geometry when opening
evidence is missing and pass separate opening eligibility into the
counter. The current Level B hour binds bid OHLC and spread together.
This review opened no new quote archives. Search snippets displayed a
dated 17 July 2026 example and separate undated EURUSD price examples,
which are recorded as incidental exposure for future partition review.
No values from those snippets entered the calendar or the counter.
[Dated catalogue snippet source](https://tickdatadownload.com/en/) · [Undated example source](https://www.dukascopy-node.app/instrument/eurusd)
