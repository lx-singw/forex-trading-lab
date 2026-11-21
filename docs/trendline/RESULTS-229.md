# Sprint 229 · EV qualification decision

22 November 2026. EV Trading Labs lists EURUSD files spanning the
proposed 2020 warmup and 2021–2022 development window. The public
evidence falls short of qualifying the original first-opening rule.
The remaining questions are the exact calendar, construction of the
opening price pair, and when a completed H4 decision becomes available.
[Proposed dates](RESULTS-199.md) · [Frozen entry rule](PROTOCOL.md#c4-entry-and-data-level-semantics) · [EV catalogue](https://evtradelabs.com/data)

## Exact catalogue coverage

Read only file metadata from the public catalogue page. Compare the
12 EURUSD file entries with the retained Sprint 223 catalogue. Their
compressed sizes, row counts, and first and last UTC labels all match.
The figures are advertised row counts.

| Year | H1 rows | M5 rows | H4 rows | D1 rows | First H1 label, UTC | Last H1 label, UTC |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| 2020 | 6,250 | 74,984 | 1,615 | 314 | 1 Jan 22:00 | 31 Dec 21:00 |
| 2021 | 6,240 | 74,863 | 1,612 | 312 | 3 Jan 22:00 | 31 Dec 21:00 |
| 2022 | 6,240 | 74,872 | 1,612 | 312 | 2 Jan 22:00 | 30 Dec 21:00 |

Apply Sprint 224's ordinary Sunday-to-Friday, 17:00 New York
schedule to each UTC calendar year, without adding holiday exceptions.
The start and end labels bound hours absent at the edges. Within
those labels, subtract the published row count from the ordinary
slots to get the minimum number of additional absences.

| Year | Ordinary H1 slots | Absent before first label | Absent after last label | Minimum additional absences | Minimum total absences |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2020 | 6,288 | 22 | 2 | 14 | 38 |
| 2021 | 6,262 | 22 | 0 | 0 | 22 |
| 2022 | 6,240 | 0 | 0 | 0 | 0 |

These are differences from the ordinary-hours scenario. The 2022
row count and edge labels align with it. Row-level continuity and any
hours outside the schedule remain unknown. The 2020 and 2021 edge
absences overlap the year-end holiday period. Dated Dukascopy notices
identify holiday effects and direct readers to the trading-breaks
calendar. The public material reviewed leaves the exact EURUSD
exceptions for EV's files unresolved.
[Ordinary-hours method](RESULTS-224.md) · [Dukascopy trading hours](https://www.dukascopy.com/swiss/english/forex/forex-trading-accounts/link/) · [December 2020 notice](https://www.dukascopy.com/swiss/english/about/ournews/market-closures-on-christmas-and-new-year-2020) · [December 2021 notice](https://www.dukascopy.com/europe/english/about/ournews/market-closures-on-christmas-and-new-year-2022/) · [December 2022 notice](https://www.dukascopy.com/europe/english/about/ournews/market-closures-during-x-mas-and-new-year/)

## Use, opening prices and publication

EV expressly offers the historical resamples for educational use with
attribution and describes them as suitable for local backtesting. This
supports the intended private research use at the distributor level.
Dukascopy's website terms separately restrict copying and derivative
use of its website materials. Which upstream terms apply to EV's
published distribution remains unresolved.
[EV catalogue](https://evtradelabs.com/data) · [EV methodology overview](https://evtradelabs.com/about) · [Dukascopy website terms](https://www.dukascopy.com/swiss/english/legal-pages/terms-of-use/)

EV identifies the in-house cleaning and resampling pipeline from
Dukascopy ticks through M1 to H1. Its research article explains its
midpoint calculation and bid fallback. The download specifications
leave the rule for deriving both opening sides from a common first
observation unspecified. Sprint 223 verified the agreement of EV's
published H1 and M5 opens for 2024. The bucket labels and matching
prices leave original quote order and availability unresolved.
[EV research method](https://evtradelabs.com/blog/eurusd-seasonality-day-month-session) · [Opening price comparison](RESULTS-223.md)

The catalogue publishes finalized historical bars with UTC opening
labels. A reviewed bar-open approximation would still need evidence for
its H4 finalization delay, including partial sessions, and for the order
of an H4 decision and H1 open that share a timestamp. The Sprint 226
clock and quote-dependent cases illustrate the consequence of the
different models. Neither was qualified for EV's actual archive.
[Parent resampling](RESULTS-225.md) · [Timing scenarios](RESULTS-226.md)

## Disposition

EV remains unqualified for the original first-opening rule in the
proposed window. Phase 10 stays `UNAVAILABLE` with null actual counts.
The public catalogue comparison resolves file inventory. It leaves
source admission, opening construction and availability open.

The proposed delayed-entry variant would select the first scheduled H1
open strictly after the H4 decision becomes available and retain the
next-H4 expiry. A gap in the selected opening would remove the entry.
This removes dependence on ordering a tied opening event. Qualified
historical input and a reviewed availability model would still be
required. The change to the strategy requires approval and its own
feasibility count before any outcome evaluation.

The public search displayed EV's aggregate EURUSD research metrics
across multiple years. These are incidental exposure for future review.
The qualification pass used catalogue metadata and specifications.
[Prior exposure review](RESULTS-202.md)

## Verification

The retained Sprint 223 catalogue snapshot has SHA-256
`3020a031ff94d5a63d750dfd434ddc6311e1e88b66ba80c01b551bd29f1e351c`.
The new catalogue snapshot has SHA-256
`092529d0cb89842412b68759dcdb4f63387930ae7da3d77dde0dc3c5d9c4247a`.
The 12 selected records match across those snapshots. Independent
JavaScript and Python calculations agree on the calendar totals.
All 16 targeted tests passed. The Phase 10 status report matches
Sprint 228 byte for byte.
