# Sprint 206 · Historical H1 candle source review

19 November 2026. The lab has a saved H1 bid series. A public catalogue also
advertises precomputed H1 bid and ask data across more than the required
calendar span. Neither is qualified for the Phase 10 entry counter.

## Candidate evidence and decisions

| Source | Verified evidence | Phase 10 decision |
| --- | --- | --- |
| Saved 2024–2025 MT5 H1 export | The named provenance declares EURUSD H1 bid data, 12,422 source rows, an unverified historical timezone and a fixed 1.2-pip spread hypothesis. MetaQuotes documents that M1 records the minute’s minimum spread and that larger bars build on M1. | The saved spread cannot establish the historical entry spread. The series spans one year of already-seen development and an excluded 2025 holdout. Even with the clock and spread resolved, that eligible span falls short of 24 development months and the required warmup. [Lab workflow](../HISTORICAL-DATA.md) · [Exposure review](RESULTS-202.md) · [MetaQuotes bar construction](https://www.metatrader5.com/en/terminal/help/trading_advanced/price_data) |
| EV Trading Labs EURUSD H1 catalogue | The publisher lists 2003–2026 EURUSD coverage, with closed-year H1 files advertised without signup. H1 comes from Dukascopy tick-derived M1 resamples. The catalogue specifies UTC opening labels, OHLC and ask OHLC fields, and free use with attribution. | Best new anonymous bar lead. Confirm that the H1 bid and ask opens describe the same first underlying observation, and check missing-minute and session handling. Verify that source-use terms cover the distributed resample and intended private workflow. Dukascopy’s website terms restrict copying and derivative use of website material. Their applicability to this distinct publication and any separate publisher rights remain open. [Publisher catalogue and terms](https://evtradelabs.com/data) · [Dukascopy website terms](https://www.dukascopy.com/swiss/english/legal-pages/terms-of-use/) |
| FXCM public CandleData | FXCM describes hourly EURUSD weekly archives, UTC timestamps and indicative Active Trader pricing. Its two READMEs list different year ranges, and the linked UK EULA landing page routes to a form. | Documentation lead only. The exact file coverage, common opening observation and applicable use terms remain unverified. The previous FXCM archive-request stop remains in place. [Candle README](https://github.com/fxcm/MarketData/blob/master/CandleData/README.md) · [Repository README](https://github.com/fxcm/MarketData/blob/master/README.md) · [Linked EULA](https://www.fxcm.com/uk/forms/eula/) · [Earlier access outcome](../LABELS-017-RESULTS.md) |
| OANDA v20 candles | OANDA defines hour-aligned H1 with bar start, complete flag and optional bid and ask candle components. The unsmoothed opening uses the first price in the interval. API access requires an account token. | Stronger documented format if suitable access becomes available. Confirm paired opening construction, retained history and permitted local use. The lab has no established access for this route. [Candle definition](https://developer.oanda.com/rest-live-v20/instrument-df/) · [Pricing and smoothing](https://developer.oanda.com/rest-live-v20/pricing-ep/) · [Access guide](https://help.oanda.com/us/en/faqs/api-user-guide.htm) |
| Candl Replay public CSV | The publisher advertises EURUSD H1 with UTC candle times, a one-year per-file limit and a single OHLC set in the CSV. | The published schema lacks a second opening side or entry-spread field. [CSV format](https://candlreplay.com/free-forex-data/) |

## Consequence for the opening model

Retain Exness as the lead tick source because the archived quote rows already
give both sides from one observation. EV Trading Labs is the next candidate
to assess for the protocol’s native bar-open approximation. If its opening
fields come from the same underlying observation, the candidate calculation
is bid open from `o` and spread in pips from `(ao - o) / 0.0001`. That relies
on the exact field mapping and resampling method being verified. Matching
bar labels alone cannot establish the pairing. A bar-open label supplies
the bucket start, and strategy availability needs a separate declared model.
Any positive H4 finalization delay misses a same-timestamp H1 opening under
the frozen rule. Where a declared closure leaves time before the next
scheduled H1 open, its actual timing governs eligibility. [Protocol C4](PROTOCOL.md#c4-entry-and-data-level-semantics) · [Opening prototype](RESULTS-205.md)

The immediate source check is to establish opening-side alignment, missing-bar
policy and applicable lineage/use terms for the EV H1 files. If those hold,
choose an already-seen development-only file for a bounded coverage diagnostic
before considering full warmup and development coverage. Keep Exness and EV
as separate candidates. The earlier 2018–2019 validation proposal remains
unassigned, and direct Dukascopy archive access stays closed.

## Verification and scope

Compared public provider documentation with the saved provenance and reran
the canonical Phase 10 metadata status. It reported `UNAVAILABLE` with null
actual counts and no source assignment. Ten opening tests passed, covering
delayed receipts, same-time order, late decisions, and the entry window after
a declared closure. The local filename inventory was
broader than the protocol's named-file approach. Only the preidentified MT5
metadata was opened from local data. No quote files, terminal, market replay
or protected history were opened. Candl Replay’s format page displayed example
EURUSD rows dated November 2025, within the already-excluded year. The example
prices were neither retained nor used. No provider message was sent.
