# Sprint 200 · Earlier EURUSD archive inventory

18 November 2026. Check calendar-year archive metadata for an earlier
study shape, following the date gap found in [sprint 199](RESULTS-199.md).
Use 2015 as a candidate warmup, 2016–2017 as candidate development, and
2018–2019 as candidate validation. The choice follows the earliest five
consecutive years shown in the retained selector inventory. The dates
are proposals for a metadata check, without a new study designation.

Use the public Exness selector for the exact unsuffixed `EURUSD` instrument
and the `All months` option for each year. Record the displayed archive
links without activating the download control. Check each displayed link
at most once with `HEAD`, in chronological order, using a short timeout
and no redirects. Stop the request batch on access denial, rate limiting
or transport failure. The check uses only public metadata.

## Observed source links

The [public selector](https://www.exness.co.za/tick-history/) showed `EURUSD`
and `All months` for each selected year and provided these exact links.

1. [2015 annual archive](https://ticks.ex2archive.com/ticks/EURUSD/2015/Exness_EURUSD_2015.zip)
2. [2016 annual archive](https://ticks.ex2archive.com/ticks/EURUSD/2016/Exness_EURUSD_2016.zip)
3. [2017 annual archive](https://ticks.ex2archive.com/ticks/EURUSD/2017/Exness_EURUSD_2017.zip)
4. [2018 annual archive](https://ticks.ex2archive.com/ticks/EURUSD/2018/Exness_EURUSD_2018.zip)
5. [2019 annual archive](https://ticks.ex2archive.com/ticks/EURUSD/2019/Exness_EURUSD_2019.zip)

## Header results

Each exact annual URL returned HTTP 200, `application/zip` and a content
length, with no redirect. All five reported a last-modified date of
5 June 2024 UTC. The combined advertised size was **422,723,013 bytes**.

| Year | Metadata role | Advertised bytes |
| --- | --- | ---: |
| 2015 | Candidate development warmup | 48,255,068 |
| 2016 | Candidate development | 111,316,640 |
| 2017 | Candidate development and validation warmup | 92,221,463 |
| 2018 | Candidate validation | 108,298,897 |
| 2019 | Candidate validation | 62,630,945 |

The server responses establish file delivery metadata. Exact first and last
quote dates, completeness, and session coverage remain open. In particular,
the 2015 header gives no count of eligible development warmup bars.

## Chronology and eligibility

The preflight evaluated a copy of the canonical plan with the following
half-open date intervals. Both funded intervals span 24 calendar months.
Each warmup ends at the start of its funded interval. The date checks found
no overlap between funded periods or with a frozen restricted interval.

| Role | Start UTC | End UTC, exclusive |
| --- | --- | --- |
| Development warmup | 2015-01-01 | 2016-01-01 |
| Development | 2016-01-01 | 2018-01-01 |
| Validation warmup | 2017-01-01 | 2018-01-01 |
| Validation | 2018-01-01 | 2020-01-01 |

The earlier inventory is a candidate for a complete chronological study.
Sprint 199 established the separate date constraint on validation after
the 2021–2022 development proposal. For the earlier plan, establish the
historical feed and timestamp mapping, session exceptions and permissions
for the exact years, and review prior exposure before assigning dates. An
archive audit must establish eligible H1, H4 and D1 warmup
counts. Validation prices need the distinct validation scope and access
qualification in the frozen protocol. [Date finding](RESULTS-199.md) · [Frozen protocol](PROTOCOL.md)

All 65 targeted preflight tests passed. The local evidence check matched
the displayed URL sequence, declaration hash and header sizes. It verified
the proposed dates in a copy and the exact canonical plan bytes on disk.
The five local receipts and date report are ignored under
`reports/trendline-source-200/`. This sprint accessed no price bodies and
assigned no development input or holdout. Phase 10 remains `UNAVAILABLE`
with null actual counts. The earlier candidate preflight is also `UNAVAILABLE`.
