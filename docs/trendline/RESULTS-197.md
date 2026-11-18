# Sprint 197 · Historical Exness clock and session evidence

18 November 2026. Reviewed dated Exness documents for the candidate 2020–2022
EURUSD archive. The evidence establishes what Exness published for its
platform clock and ordinary forex hours in 2022. Archive admission also
needs a dated link to the exact EURUSD files and the session exceptions.

| Evidence | Finding | Application |
| --- | --- | --- |
| Exness (SC) General Business Terms, 29 January 2022, version 010, page 22 | Server log event times used GMT+0 at the document release. The terms refer to instrument contract specifications for trading hours. | Dated primary evidence for the platform clock in January 2022. [SC terms](https://my.exness.com/cdn/media/nymstarLimited/nymstar_limited_general_business_terms.pdf#page=22) |
| Exness (VG) General Business Terms, 28 January 2022, version 003, page 22 | The same server-log time convention appears in the VG terms. | Corroborates the contemporaneous platform convention across two Exness entities. [VG terms](https://www.exness.com/cdn/media/venico/venico_capital_limited_general_business_terms.pdf#page=22) |
| Exness Forex page, captured 18 January and 3 July 2022 | January lists Sunday 22:05 through Friday 21:59. July lists Sunday 21:05 through Friday 20:59. Both use GMT+0 server time and omit EURUSD from the list of instruments with different hours. | Dated ordinary weekly-hours evidence for winter and summer 2022. The one-hour schedule shift occurs against the same published clock offset. [January capture](https://web.archive.org/web/20220118223244/https://www.exness.com/forex/) · [July capture](https://web.archive.org/web/20220703093843/https://www.exness.com/forex/) |
| Third-party repost dated 22 December 2021 | The repost gives two holiday-adjusted forex weekends. It lists early Friday closures at 20:00 on 24 and 31 December and Sunday reopenings at 22:05 on 26 December and 2 January, in GMT+0. | Candidate dates for corroboration. The repost does not establish primary closure or quote-only rules for the unsuffixed archive. [Reposted notice](https://exn.fxsignup.com/fr/news/2021122201.html) |

The current Exness schedule widget showed November 2026 when opened. One
Previous month click displayed October 2026 and disabled further backward
navigation. The public control did not expose 2020–2022. The captured help
article from October 2024 corroborates UTC+0 for trading servers and has a
2024 holiday list. These are useful dated observations for their own periods.
[Current widget](https://get.exness.help/hc/en-us/articles/4405235684498-Instrument-trading-hours) · [2024 capture](https://web.archive.org/web/20241008002506/https://get.exness.help/hc/en-us/articles/4405235684498-Instrument-trading-hours)

The January 2022 tick-history page describes downloading bid/ask ZIPs. The
January 2023 capture explicitly describes backtesting with the indicative
history. This corroborates the public product use described today. Applicable
retention and processing terms for the proposed study still need evidence.
Neither capture’s product description specifies the `Timestamp` encoding
or how its archive feed maps to the server-log clock across these three years.
[2022 capture](https://web.archive.org/web/20220122170122/https://www.exness.com/tick-history/) · [2023 capture](https://web.archive.org/web/20230114130047/https://www.exness.com/tick-history/) · [Use review](RESULTS-195.md)

## Source qualification still needed

- Confirm which historical feed supplies the public unsuffixed `EURUSD` series
  and what its CSV `Timestamp` represents across 2020–2022, including any
  feed, time conversion or schema changes.
- Obtain dated session rules for those files, including seasonal transitions,
  holiday closures, quote-only intervals and documented outages. Use the
  dated weekly windows as comparison evidence during coverage review.
- Establish the scope for private storage of the three originals and processing
  and retention of derived bid OHLC and entry spreads for backtesting. Then
  review source scope and audit actual warmup and development coverage.

**Provider question prepared for future use.** Can Exness identify the feed
and timestamp convention of the 2020–2022 public unsuffixed EURUSD annual
archives, point to the dated forex schedule and exceptions, and confirm the
terms for keeping the originals and derived hourly bars for private local
strategy backtesting? The research would keep source data private. No provider
message was sent.

The archive timestamp mapping for all three years, a dated exception calendar
and actual bar coverage remain unverified. Search extracts included
a published example for a different, already excluded 2025 variant. No prices
were carried into the results. The local evidence uses saved public document
captures under the report ignore rules. No tick archives were downloaded or
decoded. The Phase 10 preflight remains `UNAVAILABLE` and `actual_counts` is
null. All 37 source/run preflight tests passed.
