# Sprint 228 · Historical EURUSD receipt sources

20 November 2026. Review public specifications for sources that could
support historical opening receipt and order for spot EURUSD. Compare
the proposed 2020 warmup and 2021–2022 development dates against the
published product scope. Use the actual receipt requirement for paired
quotes and keep the reviewed Level B bar-open model available as its own
route. [Proposed dates](RESULTS-199.md) · [Frozen entry rule](PROTOCOL.md#c4-entry-and-data-level-semantics) · [Receipt order contract](RESULTS-227.md)

## Source findings

| Source | What the specification establishes | Disposition |
| --- | --- | --- |
| LSEG Tick History PCAP for FX Matching | LSEG announced the FX Matching capture in September 2023. The product retains venue-network packets and records their capture at the exchange data centre with nanosecond timestamps. Public LSEG materials describe customer samples and limited Workbench trials. The AWS listing reviewed offers a US equities sample. | Strongest lead for a recorded arrival at a defined capture point. The first available EURUSD capture date and access to a suitable study extract remain unverified. The 1996 start advertised for general Tick History belongs to the broader normalized product. [FX Matching announcement](https://www.lseg.com/en/insights/fx/revolutionising-fx-price-transparency-with-tick-history-pcap) · [Product and samples](https://www.lseg.com/content/dam/data-analytics/en_us/documents/fact-sheets/lseg-tick-history-pcap-factsheet.pdf) · [AWS sample listing](https://aws.amazon.com/marketplace/pp/prodview-yi3aovwrufwua?applicationId=AWSMPContessa) · [General Tick History](https://www.lseg.com/content/dam/data-analytics/en_us/documents/fact-sheets/lseg-tick-history-factsheet.pdf) |
| CME DataMine EBS Ultra Spot FX | The catalogue lists EUR/USD and 5 ms spot history from 17 January 2017. The 16 May 2022 migration changed delivery from one daily file to separate New York and London engine files. The documented post-migration binary header includes `MsgSeqNum` and `SendingTime`. | Those fields can establish message send order within the declared stream. A receiving clock for the study remains unverified. This is a customer-delivery product with separate pre-migration and post-migration formats to qualify. [EBS Ultra specification](https://cmegroupclientsite.atlassian.net/wiki/spaces/EPICSANDBOX/pages/457226094/EBS%2BUltra) |
| Cboe FX Top of Order Book and ITCH history | The public product descriptions list timestamped spot order-book events or bid/offer quotes and archive availability from 2 January 2020. They list 5 July 2021 as unavailable. The legacy spot format uses the file date with a 17:00 Eastern boundary, and its records are sorted by raw time rather than reconstructed calendar order. | The available products describe one timestamp and omit a separate receipt field. A study would also need to resolve the missing 2021 date and the first day of the proposed warmup. Access is described as subscription or historical purchase. [Top of book](https://datashop.cboe.com/fx-top-of-order-book-historical-data) · [ITCH history](https://datashop.cboe.com/fx-itch-feed-historical-data) |
| Massive Forex historical quotes | The historical REST schema exposes bid, ask and `participant_timestamp` for quote generation. Massive explains that its forex quote times use whole-second resolution, even when the value is stored in nanoseconds. The individual free plan excludes historical quotes. The flat-file catalogue lists the proposed years under paid quote access. | The timestamp describes the provider-side event and leaves receipt order relative to an H4 decision unverified. The file inventory alone supplies no evidence about the first opening quote. [Forex REST schema](https://massive.com/docs/rest/forex/quotes/quotes) · [Forex timestamp explanation](https://massive.com/knowledge-base/article/how-are-massives-forex-bars-built-and-what-do-v-and-n-mean-on-a-forex-bar) · [Flat-file catalogue](https://massive.com/docs/flat-files/forex/quotes) |
| INFINITECH open deposit | The repository lists one price per tick through 9 March 2022, followed by hourly OHLC through 7 September 2022. It lists a one-second tick clock without a second timestamp or paired bid and ask. | Public access cannot supply a paired opening or the full proposed period. This confirms the earlier source decision. [Versioned deposit](https://zenodo.org/records/7411148) · [Sprint 195 review](RESULTS-195.md) |

## Consequence for the study

A captured packet can establish arrival at the recorded capture point.
A Phase 10 replay using that clock would still need the exact spot feed
and date inventory, a dated session calendar, packet and sequence
coverage, use and retention permission, and a separately reviewed mapping
from packet receipt to H4 completion and the opening decision. Same-time
entries still require an ordered decision and opening observation on the
declared replay clock. Venue prices and spread would describe the chosen
spot venue. Broker execution compatibility requires its own evidence.
[Historical input requirements](RESULTS-215.md) · [Per-opening order](RESULTS-227.md)

The review found no accessible capture archive with verified EURUSD
coverage for the proposed dates. Exness remains a source-time paired
quote candidate. EV remains an H1 bid/ask bar-open candidate. Each has
open qualification items and neither supplies a verified historical
receipt model today.
[Exness quote ceiling](RESULTS-222.md) · [EV publication review](RESULTS-226.md)

The review used public specifications and catalogue metadata. Search
results displayed illustrative EURUSD price rows labeled 1 February 2021
and 28 March 2023 UTC, both within already-recorded exposure years. A
Dukascopy client-library search result also displayed an undated EURUSD
example. Record it as incidental exposure without retaining the prices.
[Prior exposure](RESULTS-202.md)

## Verification

Verified the provider references and all eight repository links in
this report. All 18 targeted timing and admission-status tests passed.
The canonical Phase 10 report matched Sprint 227 byte for byte and
remains `UNAVAILABLE` with null actual counts.
