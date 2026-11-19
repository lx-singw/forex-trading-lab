# Sprint 212 · First-quote opening approximation

19 November 2026. Evaluate whether the first archived quote inside a
scheduled H1 interval supplies a paired bid and spread for a Level B
opening proxy. The source timestamp stays attached to the quote for the
timing check. A late first quote does not establish that price at the
scheduled opening. [Frozen entry order](PROTOCOL.md#c4-entry-and-data-level-semantics)

## Scope declared before archive access

Use one ordinary HTTPS GET for the [same January 2022 EURUSD ZIP](https://ticks.ex2archive.com/ticks/EURUSD/2022/01/Exness_EURUSD_2022_01.zip)
inspected in Sprint 203. Require HTTP 200, ZIP media type, 5,412,286 bytes
and SHA-256 `d98fc8a0d7b7fb144b8b4be78810e18498e7d43cf1da889c7eb09db5fed07873`
before parsing. Use a ten-second socket timeout, a 45-second response
deadline, one expected CSV member and the prior 256 MiB decompressed bound.
Stop on a mismatch. Keep the ZIP and selected quote pairs in memory. Retain
only file hashes and diagnostic aggregates. No credentials, redirects,
retries, new market dates or strategy runs. The publisher describes local
scripted backtesting with these downloads. Full-study use and retention
remain unresolved. [Previous audit](RESULTS-203.md) · [Public archive guide](https://www.exness.com/blog/product/exness-tick-history-bid-ask-prices/)

Use only H1 windows wholly inside January on the Sprint 208 ordinary
hours grid. For each window keep the first source row in archive order and
calculate its spread from its own ask minus bid. Report opening lags of
zero, positive below one second and at least one second. Treat these as
descriptive buckets. Report nearest-rank median and 95th-percentile paired
spreads. For the four Friday-to-Sunday pairs from Sprint 203, also check
whether each scheduled child H1 of the shortened Friday H4 contains at
least one source quote. This is presence within archive scope. Completeness,
historical receipt and strategy availability require independent evidence.
[Candidate calendar](RESULTS-208.md)

## Results

The response matched the pinned size and hash. The CSV header, single
member, decompressed bound and CRC checks passed. All 748,560 archived rows
fell within the 506 modeled H1 windows. Every window supplied a paired
opening proxy. Every scheduled H1 child in the four preceding shortened
Friday H4 bars contained at least one quote.

| Sample | Paired proxies | Exactly at scheduled open | Later by less than one second | Later by at least one second | Median spread in pips | 95th-percentile spread in pips |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| All modeled January H1 | 506 | 0 | 303 | 203 | 0.6 | 0.7 |
| Four sampled Sunday reopenings | 4 | 0 | 0 | 4 | 3.7 | 3.8 |

The source-label categories for all H1 windows match the retained Sprint 203
wall-hour aggregates, despite the candidate grid clipping the Sunday opening
to `:05`. The four first Sunday quotes had markedly wider spreads than the
all-hour sample. Those spreads describe quotes labeled after the scheduled
opening. They supply no spread or bid observed at the boundary.
[Prior audit](RESULTS-203.md) · [Clock publication model](RESULTS-211.md)

## Disposition

The first-pair construction supplies a retrospective opening proxy for the
sample. The file supplies no observation at the modeled first H1 opening on
the four weekends. The Friday presence result supports testing modeled H4
publication there once coverage is qualified. Historical receipt order, the
defensible use of a Level B opening price and spread, and full archive
admission remain open. Phase 10 is `UNAVAILABLE` with null actual counts.

The diagnostic command is pinned to this one archive and makes one request
for a new report path. The sprint retained an ignored aggregate receipt with
the pre-request scope hash. The archive hash and opening counts matched the
prior diagnostic. All 80 targeted opening, timing, fill, source coverage and
signal-count tests passed. No raw quote pairs or strategy outcomes were saved.

```sh
PYTHONPATH=src python3 -m tools.exness_opening_212 new-opening-report.json
```
