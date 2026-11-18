# Sprint 199 · Source decision and validation date check

18 November 2026. The proposed 2020 warmup and 2021–2022 development
archives remain candidates for Phase 10. A separate check found no full
24-month validation period after that development block in history through
18 November 2026 under the frozen date restrictions.

## Phase 10 source decision

Exness’s order-execution page explicitly directs readers to its **public** tick
history for backtesting. Its archive guide also describes local file analysis
and suggests scripts for repeated backtests. This supports the proposed
backtesting use. The applicability of the general website copying restriction
to retaining the raw downloads and locally derived H1 data still needs
resolution. The separate API Key Terms apply when a client or partner creates
access credentials for that API. The public selector route in sprint 196 uses
anonymous ZIPs. The reviewed API terms offer no archive-specific retention rule
for that route. [Backtesting guidance](https://www.exness.com/order-execution/) · [Archive guide](https://www.exness.com/blog/product/exness-tick-history-bid-ask-prices/) · [Legal documents](https://www.exness.com/legal-documents/) · [API Key Terms, §1](https://www.exness.com/cdn/media/docs/exness-api-terms-of-use.pdf)

Exness’s dated announcements identify Exness (SC) Ltd as the successor name
to Nymstar Limited. The announcement indexes document agreement changes
through the candidate period. They provide entity and document chronology.
The current public specifications still leave the 2020–2022 archive’s exact
feed, timestamp mapping and historical session exceptions unresolved.
[2020 announcements](https://www.exness.com/announcements-2020/) · [2021 announcements](https://www.exness.com/announcements-2021/) · [2022 announcements](https://www.exness.com/announcements-2022/) · [Historical clock evidence](RESULTS-197.md)

**Decision.** Keep Phase 10 at `UNAVAILABLE`. Obtain archive-specific
terms or written clarification and date-effective feed, clock and session
evidence before acquisition and coverage audit. The archive context and
published support address are ready for the inquiry below.

### Provider inquiry ready for authorization

**To** `support@exness.com`

**Subject** Public EURUSD tick archive format and private backtesting use

> Hello Exness Support,
>
> I’m assessing the public, unsuffixed EURUSD annual tick-history ZIPs for
> 2020, 2021 and 2022 for a private, offline strategy study. Could you confirm
> which feed these files represent and how their CSV `Timestamp` field is
> encoded, including any changes to the clock or feed during that period?
> Could you also point me to the historical EURUSD quote schedule and known
> exceptions, including holidays, maintenance and quote-only intervals?
>
> Your public guide describes backtesting with the archive. May I retain
> the three original downloads and keep locally derived H1 bid bars and
> opening spreads for this study? The data and derived bars would stay
> private. Please point me to any applicable terms or retention limits.
>
> Thank you.

The draft is unsent and awaits the user’s authorization. It includes the
public symbol, dates and research purpose.
[Published support address](https://www.exness.com/legal-documents/)

## Phase 11 chronology

The original plan requires a later, contiguous 24-calendar-month funded
validation period. Even before checking prior exposure and data quality,
only two later blocks survive the frozen date restrictions as of this sprint.

| Block | Calendar months | Qualification status |
| --- | ---: | --- |
| January–December 2023 | 12 | March and July also have documented prior exposure from the retained Exness audits. |
| January–September 2026 | 9 | This is a date-policy upper bound. Source and exposure qualification are open. |

The frozen policy marks 2024 as development-only, 2025 as consumed, October
2026 as quarantined, and November–December 2026 as reserved. The gaps above
are too short even if treated as fully available. Combining them into one
validation period would cross excluded dates. The chronology check passed no
data to a strategy. [Frozen protocol](PROTOCOL.md) · [2023 audit](../EXNESS-024-RESULTS.md) · [2023 exposure examples](../EXNESS-COMPARISON-025-RESULTS.md)

2021–2022 can still be used for a Phase 10 count if qualified. For Phase 11,
an earlier chronological pair or later qualifying history would need review.
The retained selector advertised 2015–2019 as well. That gives a catalog lead
for an earlier warmup and two sequential 24-month periods. The earlier archive
files, warmup sufficiency and exposure status remain unverified. This review
assigns neither a new development scope nor a holdout. [Retained selector review](../SOURCE-INVENTORY-022-RESULTS.md)

The existing preflight reproduced the rejection reasons for the 2023–2024,
2024–2025 and 2025–2026 validation examples using copies of the canonical plan.
All 65 targeted preflight tests passed. The local chronology report is under
the ignored `reports/trendline-source-199/` directory. The canonical preflight
still shows `UNAVAILABLE` with null actual counts. This sprint used metadata
and public documentation only.
