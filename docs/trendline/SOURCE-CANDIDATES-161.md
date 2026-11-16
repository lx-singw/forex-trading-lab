# Source reconnaissance for the forthcoming Phase 2

16 November 2026, responding to the user's instruction to use any available
permitted source or consider collection. This is a documentation review; no new
dataset, archive, API price response, broker account or capture window is assigned.
It does not complete Phase 2 or reopen an old stopped provider route.

## Existing records

[Local-data notes](../../data/README.md), [historical evidence095](../HISTORICAL-EVIDENCE-095-RESULTS.md),
[alternatives096](../ALTERNATIVE-SOURCES-096-RESULTS.md) and
[source decision105](../SOURCE-DECISION-105-RESULTS.md) document unresolved saved
history clocks/coverage/use/cost qualification and closed access/SDK routes.
No local price rows were opened. A Level B tier relaxes execution precision, not
those date/access restrictions. Old diagnostic files are not newly admitted input.

## Distinct public documentation leads

Three discovery searches covered OANDA candles, Alpha Vantage FX_INTRADAY and
Twelve Data history. Primary documentation search results show OANDA requires
authenticated API access and has bid/ask/mid candle components; no existing access
was established and no broker account will be created. Alpha Vantage marks
FX_INTRADAY premium; no paid route was pursued. These remain leads, not newly
qualified datasets. [OANDA guide](https://help.oanda.com/us/en/faqs/api-user-guide.htm),
[Alpha Vantage documentation](https://www.alphavantage.co/documentation/).

Twelve Data is the next metadata candidate because its
[forex overview](https://twelvedata.com/forex) advertises a free tier and historical
rates. This is an access lead, not proof of bid/ask semantics or complete history.
Its [history guide](https://support.twelvedata.com/en/articles/5656039-how-to-get-historical-prices)
supports H1 and date-window requests, with symbol-specific history needing a
metadata check. Its [Forex inventory](https://twelvedata.com/exchanges/physical_currency)
advertises intraday history since2019, but also displays a generic24/7 schedule and
Sydney timezone. Do not adopt those as a historical EURUSD session calendar.

Its [terms, sections2.2-2.3](https://twelvedata.com/terms) make internal storage and
non-display use subject to plan permissions and retention restrictions. We have
not established the applicable free-tier entitlement for this private research
scope. This is an unresolved applicability question, not a finding that research
is prohibited. No contact, signup, credential read or account change occurred.

Four primary Twelve Data pages were opened and four text finds performed; no API
links or displayed example requests were executed. Incidental undated website
ticker banners were encountered, not used or copied as research prices. Their
uncertain exposure is recorded in DECISIONS.md for future validation review.

## Concrete next evidence

Check whether an existing permitted Twelve Data export/access can establish:

1. EURUSD H1 date coverage and exact candle price/time semantics, without requesting
   protected dates or decoding a holdout during development.
2. Permission/retention for the intended local research use and a private credential
   configuration if API access is needed; never paste a key into chat or Git.
3. Bid plus meaningful entry-spread data, or separately supplied executable-side
   bars, before a B ledger. Aggregate-only mid data can support geometry research
   but cannot invent bid/ask execution or fulfil the entire Phase 2 contract.
4. A declared source-specific calendar, availability assumptions, warmup and
   chronological development/validation scope preserving earlier exposure records.

If this candidate cannot meet these requirements, record that result and assess a
distinct permitted alternative. Do not repeatedly retry stopped access routes.
Fresh prospective collection can contribute to future Q evidence, but years of
new snapshots do not already exist today. The native recorder still needs the
separate runtime and source/date/run qualification described in159; this source
choice is not a native collection grant. Orders remain unavailable.
