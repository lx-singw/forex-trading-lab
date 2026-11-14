# Public archive feasibility 021 — 2026-10-06

Exness is a promising new publisher to investigate. No new source has passed
the annual data gate. This review acquired no quotes and produced no returns.

The [declared plan](SOURCE-ACCESS-021-PLAN.md) limited discovery to 12 search
queries and 20 primary-page opens/context reads. Both budgets were used; four
additional find operations read page context. Queries, every page outcome,
evidence strength and unknowns are in `reports/source-access-021-notes.json`.
Failed reads are retained. This bounded search is not exhaustive.

| Candidate | Evidence found | Decision for this project |
| --- | --- | --- |
| Exness | Public monthly archive described as free bid/ask ticks; CSV ZIP and millisecond Z examples | Inspect actual EURUSD inventory, clock, sessions and terms next |
| Darwinex | EURUSD advertised from October 2017; live-account clients generate FTP credentials | Outside current access constraints |
| Pepperstone | Tool exports ticks collected since startup; old archive URL returns account content | Multi-year archive not established |
| OANDA | Authenticated trading candles and commercial data API are different offerings | Free unauthenticated historical ticks not established |
| GAIN Capital | Primary archive root inaccessible through the web tool | Current coverage unknown; no archive status inferred |
| FXOpen | Indexed provider article describes connected Quotes Downloader | Access, years and tick schema unverified; no installation |
| Tick Data LLC | Commercial forex bid/ask product advertised from 2008 | Free complete target archive not established |

The [Exness archive page](https://www.exness.co.za/tick-history/) describes
public indicative prices from its real-time pricing. Prior months require
whole-month downloads. Extracted selectors did not expose instrument/year/month
inventory. Initial reading succeeded; later context extraction failed, without
an archive request. Its [historical-data article](https://insights.exness.global/trading-basics/forex-historical-data/)
describes free downloads and illustrates EURUSD raw-spread ticks. Its
[format article](https://insights.exness.com/trading-basics/forex-data/) describes
CSV inside ZIP and shows millisecond Z timestamps. These examples do not
certify the 2020–2023 clock. Its separate Europe/London candle example must not
be applied to ticks. No later-period quotes were acquired for evaluation.

Exact EURUSD variant, all 48 target months, schema continuity, historical
sessions/holidays/outages, upstream independence and permitted uses remain
unknown. A different publisher is not proof of an independent feed. Indicative
prices also do not establish executable broker costs. No annual substitution.

[Darwinex's provider page](https://www.darwinex.com/global/algorithmic-trading/tick-data)
requires live-account FTP access in indexed primary text; direct open failed.
Its [German page](https://www.darwinex.com/de/algorithmic-trading/tick-data)
advertises EURUSD's start in indexed text only. Its
[own API repository](https://github.com/darwinex/darwinexapis) documents separate
bid/ask operations. A code license is not an archive data license.

[Pepperstone's manual](https://assets.pepperstone.com/Smart-Trader-Tools/Tick-Chart-Trader.pdf),
overview page 2 and export page 8, distinguishes startup collection from
historical access. [OANDA's data service](https://www.oanda.com/foreign-exchange-data-services/en/exchange-rates-api/)
offers trial keys and commercial plans; its [trading API guide](https://help.oanda.com/us/en/faqs/rest-v20-api-troubleshooting-guide.htm?Highlight=api)
explains authentication and historical candle versus account-specific live
prices. [FXOpen's indexed article](https://support.fxopen.com/portal/pt/kb/articles/baixar-cota%C3%A7%C3%B5es)
redirected on direct open. [Tick Data's product page](https://www.tickdata.com/product/historical-forex-data/)
describes a commercial product. These do not establish our free target archive.

No stopped FXCM/Dukascopy archive endpoints were retried. No archive GET/HEAD,
API calls, accounts, credentials, payments or provider messages. TrueFX's prior
login requirement remains unresolved; the user has no access. No code changed.

Verification checks the plan hash, budgets, note consistency, local links and
previous 020 bindings/archive. Existing 020 verification passes. The software
suite was not rerun; its latest recorded result remains 299 passing tests.
Documentation checks are not market-data approval. Review, seals and source
snapshot are `reports/source-access-021-*`; only four editable handoff files
change against the preceding snapshot. Frozen code, evidence and datasets stay
preserved.

Next: declare a small public Exness selector/inventory review without pressing
download, authenticating or accessing quotes. Establish the exact variant,
target monthly listing, archive-domain ownership and public terms/session
documentation. Only then plan a bounded diagnostic quote sample if access
permits. Diagnose the timing/coverage questions before a four-year acquisition.
No strategy tuning or market returns while annual data remains rejected. Costs,
profitability and actual broker observer integration remain unverified. Demo
execution and orders remain unavailable.
