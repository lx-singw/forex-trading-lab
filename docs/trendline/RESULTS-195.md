# Sprint 195 · Phase 10 source feasibility

18 November 2026. Reviewed public archive documentation alongside the lab’s
retained source audits. Exness is the strongest route identified for the lab’s
local EURUSD counter. Its public documentation describes account-free bid/ask
downloads and explicitly discusses using the archive for backtesting. Specific
EURUSD coverage, historical clock and session evidence, and the terms covering
the proposed use still need confirmation. Historical feasibility is `UNAVAILABLE`.

## Candidate decisions

| Candidate | Evidence | Phase 10 disposition |
| --- | --- | --- |
| Exness public tick archive | The provider advertises bid/ask ZIP downloads without login and archive history back to 2015. The lab previously audited two EURUSD months with paired bid/ask fields and millisecond-stamped records. | First candidate for qualification. The two audited months cannot supply the warmup and 24-month development sample, and the advertised start is for the archive generally. [Provider guide](https://www.exness.com/blog/product/exness-tick-history-bid-ask-prices/) · [Retained audit](../EXNESS-024-RESULTS.md) |
| INFINITECH on Zenodo, version 1.0.1 | The deposit describes one price per tick from September 2020 to March 2022 and only hourly OHLC for the following period through September 2022. | The documented schema lacks bid/ask or an entry-spread field, so it cannot support either count input. [Versioned deposit](https://zenodo.org/records/7411148) |
| QuantConnect OANDA forex | QuantConnect distinguishes hosted research from downloads. Its documented dataset download license restricts local use to LEAN and prohibits format conversion. | The documented license cannot supply a converted input to the lab’s local Python counter. [Dataset](https://www.quantconnect.com/data/oanda-forex) · [Download terms](https://www.quantconnect.com/docs/v2/cloud-platform/datasets/licensing#Download) |

## Exness admission gaps

- **Use and retention.** The public guide describes downloading, extracting,
  parsing and backtesting the archive. The general site footer restricts copying.
  The Exness (SC) client agreement has separate provisions for storing and
  analyzing website information and for clients’ use of bid and offer prices.
  The applicability of those client terms to the public archive and anonymous
  local research is unverified. Identify the terms for acquiring the exact
  variant, retaining the originals and derived H1 data, and processing them
  locally for this study. [Public guide](https://www.exness.com/blog/product/exness-tick-history-bid-ask-prices/) · [Legal index](https://www.exness.com/legal-documents/) · [Client agreement, Part A §14.1(N) and Part C §4.3](https://www.exness.com/cdn/media/exnesssc/exness_sc_client_agreement.pdf)
- **Clock, feed and calendar.** Current help describes GMT+0 for Exness
  MetaTrader and identifies the archive’s serving feeds by account class.
  The retained files use `Z` labels. Together these are leads for interpreting
  the records. Historical applicability to the exact EURUSD variant and the
  dated calendar, including closures and irregular gaps, remain open.
  [Tick-history help](https://get.exness.help/hc/en-us/articles/360021547851-Tick-history) · [Platform clock](https://get.exness.help/hc/en-us/articles/360014390760-What-is-the-default-timezone-set-for-MetaTrader) · [Retained historical review](../EXNESS-EVIDENCE-026-RESULTS.md)
- **Scope, delivery and coverage.** Establish one exact EURUSD variant and
  which archive units are available for its proposed warmup and 24-month
  development window. Review only the chosen dates against the exposure log.
  The old diagnostics establish two known months and their recorded gaps.
  The provider describes larger archive units for older periods, so match the
  physical file boundaries to permitted dates before any fetch. Check completeness
  before admission. Derive bid OHLC and measure the spread from both sides of
  the same quote under the declared opening-availability model. Record gaps and
  late first quotes so elapsed openings cannot be filled retrospectively.
  [Archive packaging](https://get.exness.help/hc/en-us/articles/360021547851-Tick-history) · [Frozen protocol](PROTOCOL.md)

## Decision and verification

Prioritize Exness documentation for Level B development counts. The immediate
dependency is source-specific evidence covering permitted local use and
retention, historical UTC/session and variant mapping, and archive inventory
for a reviewable development and warmup scope. If that evidence supports the
scope, register the relevant calendar, input hashes and opening-availability
model before an actual count. The existing counter needs an admitted-input
boundary to consume those reviewed files. The archived quote fields alone do
not establish strategy-visible receipt times for Level Q.

This review used public documentation and retained summaries. It decoded no
price rows, requested no archives, and used no account or terminal. An illustrative
undated price example in the documentation was excluded from research and is
recorded for exposure review.

All 37 source/run preflight tests passed. The metadata-only status command still returns
`UNAVAILABLE` with `actual_counts` null and no historical market read. The
60-opportunity minimum, real viewer examples and DLY decision all require
admitted counts. The Phase 11 study remains gated.
[Canonical plan](../../config/trendline-study-v1.json) · [Sprint 194 counter](RESULTS-194.md)
