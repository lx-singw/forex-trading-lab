# Sprint 201 · Historical source and exposure review

18 November 2026. Reviewed primary Exness documents for the 2015–2019
archive candidate and the lab’s recorded exposure to those dates. The review
found contemporaneous evidence about platform time and quote handling.
Archive qualification remains open.

## What the historical documents establish

| Evidence | Finding for the archive review |
| --- | --- |
| Exness Limited General Business Terms, archived 5 December 2016, p. 21 | The document states that the trading platform’s server log used GMT+0 at release. The clock definition concerns server logs. The relation to the exported EURUSD CSV `Timestamp` still needs evidence. [Archived terms](https://web.archive.org/web/20161205180801/https://www.exness.com/media/files/documents/vc/general_business_terms_en.pdf#page=21) |
| Same terms, §1.1 | The terms distinguish quote provision for Interbank and Marketmaker accounts. They also allow the trading server’s quote database to be synchronized from another server or quotation source after an interruption. Ask which feed and any recovery or revision policy apply to the unsuffixed EURUSD exports. The clause describes a permitted procedure. Its use in the files is unverified. [Archived terms](https://web.archive.org/web/20161205180801/https://www.exness.com/media/files/documents/vc/general_business_terms_en.pdf#page=1) |
| Exness Limited Client Agreement, archived 10 May 2016, Part C §4.3, p. 35 | Clients may keep and process information made available through the website or platform, subject to restrictions on sharing it with third parties. Its applicability to today’s anonymous archive downloads and retention of derived H1 data remains open. [Archived agreement](https://web.archive.org/web/20160510063809/https://www.exness.com/media/files/documents/vc/client_agreement_en.pdf#page=35) |
| Exness trading sessions page, archived 5 July 2017 | It shows general financial-center hours and links to a separate forex market-hours page. Availability lookups for that linked page near July 2017 and January 2019 returned no snapshot. The general hours are insufficient for an instrument-specific exception calendar. [Archived sessions page](https://web.archive.org/web/20170705230724/https://www.exness.com/forex/trade_sessions/) |
| April 2019 Good Friday notice preserved in Exness’s platform-team deck | The notice gives GMT+0 hours for metal pairs and US oil and warns about liquidity for other instruments. It offers a dated use of GMT+0. EURUSD closure rules remain unresolved. [Exness presentation](https://presentations.clickhouse.com/meetup22/exness.pdf) |

The archived 2018 homepage and 2019 forex page preserved intermediary pages.
The 2019 Exness announcement index
lists Nymstar client agreement changes. It supplies entity and document history
for that year. The evidence still leaves the archive feed, timestamp mapping
and the EURUSD holiday, quote-only and outage schedule open. [2018 capture](https://web.archive.org/web/20180725233034/https://www.exness.com/) · [2019 capture](https://web.archive.org/web/20190825154809/https://www.exness.com/forex/) · [2019 announcements](https://www.exness.com/announcements-2019/)

## Recorded exposure

A whole-word search for `2018` and `2019` in tracked `docs/`, `config/` and
`data/README.md` at baseline `412b598` found eight files. Six discuss the
candidate or its dates. The other two describe the FXCM catalog’s 2019 start
and the failed request for 2023 metadata. A separate 2017 Darwinex reference
is also a catalog lead. The tracked records reviewed here contain no evidence of lab
price inspection or strategy results for the candidate 2018–2019 validation
span. This search covers the named paths and year strings. It leaves earlier
external or unrecorded exposure and undated examples open, so the canonical
prior-trial status remains incomplete. [FXCM review](../LABELS-017-RESULTS.md) · [Darwinex review](../SOURCE-ACCESS-021-RESULTS.md) · [Earlier inventory](RESULTS-200.md)

## Status

The next source evidence needs to cover the exact archive years, including
feed and revisions, timestamp semantics, dated session exceptions, and the
terms for retaining and processing the files. Prior-trial and exposure
completeness needs its own review before any validation access. Existing
provider questions await authorization. Public document captures are local
under the ignored `reports/trendline-source-201/` directory.

All 65 targeted preflight tests passed. The metadata status report is
`UNAVAILABLE` with null actual counts. This sprint used public documentation
and tracked metadata. No historical archive price rows were opened and no
study dates were assigned.
