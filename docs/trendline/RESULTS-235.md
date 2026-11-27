# Sprint 235 · Exness archive provenance

28 November 2026. Review the 2020–2022 public Exness EURUSD archive
for the frozen Level B delayed-entry trial. Recovered copies of the
legacy public portal establish what Exness offered during the study
period. They leave the exact ZIP-to-feed and timestamp mapping open.
[Source handoff](RESULTS-234.md) · [Frozen trial](RESULTS-230.md)

## Legacy public portal

Query the Internet Archive availability index for the legacy
`ticks.exness.com` landing page and retrieve the three returned HTML
captures. Read their displayed text, download links and embedded page
initialization times.

| Capture, UTC | Embedded page time, UTC | HTML SHA-256 |
| --- | --- | --- |
| [5 Dec 2020](https://web.archive.org/web/20201205022354id_/https://ticks.exness.com/) | 22 May 2020 09:41:33.016 | `06adea69d939611ebdb8dbde653abaea03937194ec8816b75abbdcefad2261a4` |
| [18 Jun 2021](https://web.archive.org/web/20210618115311id_/https://ticks.exness.com/) | 22 May 2020 09:41:33.016 | `06adea69d939611ebdb8dbde653abaea03937194ec8816b75abbdcefad2261a4` |
| [19 Jan 2022](https://web.archive.org/web/20220119104820id_/https://ticks.exness.com/) | 13 Jul 2021 12:24:52.630 | `4cc76f933a8920121450ec7b11b88af96e8209ead7ecd637bf697e3a07bff8fb` |

The first two bodies are identical. All three display `EURUSD` and
describe choosing a period and downloading a bid/ask ZIP for local
analysis. Each contains three distinct ZIP link templates with an
empty symbol, including a year-level template. The embedded page
state supplies locale and runtime initialization data. The availability
index returned no capture for either linked application script. The
portal evidence establishes an advertised product and instrument label.
Sprint 196 supplies the exact annual links observed in the later
selector. [Exact file inventory](RESULTS-196.md)

## Feed, clock and quote sessions

- **Feed identity.** The current public archive describes bare symbols
  as Pro with some Zero exceptions. Exness lists bare `EURUSD`
  specifically as a Pro example. Its Personal Area documentation
  identifies MT4 Real 1 for Pro and a separate server for Zero.
  This supports a Pro/Real 1 hypothesis. The documentation leaves
  historical server assignment for the three public ZIPs open.
  [Public archive](https://www.exness.com/tick-history/) · [Account suffixes](https://get.exness.help/hc/en-us/articles/360014560220-Account-type-suffixes) · [Personal Area feed](https://get.exness.help/hc/en-us/articles/360021547851-Tick-history)
- **Clock.** The provider's current public guide describes millisecond
  precision and defines `Timestamp` as the recorded update time.
  The dated 2022 terms establish GMT+0 for platform server logs,
  and the January and July 2022 samples carry `Z` labels that
  align with the expected weekend shift. These sources leave the
  exact historical archive clock, the recording point and the
  H4 decision and opening receipt order unverified. The archived
  portal supplies no timestamp definition. [Public archive guide](https://www.exness.com/blog/product/exness-tick-history-bid-ask-prices/) · [Dated server evidence](RESULTS-197.md) · [Sample alignment](RESULTS-204.md)
- **Calendar.** Availability lookups for the examined 2020 and 2021
  dates on the official Forex page returned the already retained
  January 2022 capture. Lookups for the current Tick History help
  URL returned a 2025 capture. The contemporaneous 2021 holiday
  reposts report Forex closes at 20:00 GMT on 24 and 31 December,
  with reopenings at 22:05 GMT on 26 December and 2 January. The
  retained January 2022 summary starts at a source label of
  22:06:28.681 on 2 January, 88.681 seconds after the reported
  reopen when compared on the stated clocks. This agrees with the
  expected opening hour. It leaves the exact quote effective time
  and behavior during any quote-only interval open.
  [December 2021 repost](https://exn.fxsignup.com/zh/news/2021122201.html) · [January 2022 summary](RESULTS-203.md) · [Prior schedule review](RESULTS-197.md)
- **Study use.** The legacy portal describes local quote analysis
  and carries a general copying restriction in its footer. Exness's
  current public guide expressly describes local parsing and backtesting.
  The provisions reviewed leave the scope for retaining annual ZIPs
  and privately retaining derived H1 bars and spreads unresolved.
  [Public guide](https://www.exness.com/blog/product/exness-tick-history-bid-ask-prices/) · [Legal index](https://www.exness.com/legal-documents/) · [Prior use review](RESULTS-199.md)

## Decision and verification

Keep Exness as a candidate and Phase 10 at `UNAVAILABLE` with null
actual counts. A dated export specification or archive manifest
that ties the exact public symbol and files to their feed and timestamp
convention would resolve the current lineage question. Full admission
also needs the applicable quote calendar and research-use terms, plus
evidence supporting H4 availability and the selected H1 opening pairs.
Keep the holiday repost as a comparison lead for the two named weekends.

The HTML parser and an independent markup check agreed on the symbol,
the three distinct link templates in each body and the product-use
wording. The calculation bound the January receipt by SHA-256 and
verified the 88.681-second label difference. The canonical Phase 10
metadata report matches Sprint 234 byte for byte. All 52 targeted
tests passed.

The sprint read public documentation and retained diagnostics.
Search extracts incidentally displayed illustrative price material
from January 2020 and November 2025 and an undated EURUSD example.
Those examples were excluded from the analysis. The sprint retrieved
no quote archive and opened no trading account. [Exposure review](RESULTS-202.md)
