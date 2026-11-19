# Sprint 223 · Historical bar-open source review

19 November 2026. Check whether EV Trading Labs’ closed-year EURUSD H1
and M5 downloads support the documented resampling relationship. Use 2024,
an already-seen development-only year. The distributor publishes both
products anonymously and offers use with attribution. The comparison
uses the distributor’s own products and keeps the upstream lineage and
study-use review open. [Catalogue and usage terms](https://evtradelabs.com/data) · [Prior chronology](RESULTS-202.md)

## Scope declared before download

Use one public HTTPS request per file in this order.

1. [2024 EURUSD H1](https://evtradelabs.com/api/simulator/data/EURUSD/H1/2024.json.gz), 195,309 compressed bytes in the catalogue.
2. [2024 EURUSD M5](https://evtradelabs.com/api/simulator/data/EURUSD/M5/2024.json.gz), 1,896,108 compressed bytes in the catalogue.

Use direct anonymous requests without redirects. Keep the two gzip
bodies and decoded rows in memory. Retain only hashes, row totals and
comparison aggregates. Check each H1 open against both sides of its
earliest published M5 row and note when that M5 label follows the hour.
This tests the published resampling relationship. Original tick order,
paired first-tick provenance and historical strategy receipt require
independent evidence. The diagnostic leaves the manifest review list
empty and uses no strategy counts or return calculations.

## Published EV bar comparison

All 6,247 EURUSD H1 rows matched both opening prices in the earliest
published M5 row for the same hour. Every one of those M5 rows carried
the exact H1 UTC opening label. There were 74,949 M5 rows across those
hours, 15 fewer than a complete 12-per-hour grid. Every M5 hour had an
H1 counterpart. The aggregate does not establish why the 15 slots
were absent.

| File | SHA-256 of the published gzip |
| --- | --- |
| H1 | `66fa719d8e7d75c11e1c691b232471fe3c9323e91ed998e8b82fe943f85d38b2` |
| M5 | `751c4210dd2db4cc1583d10d4e3609551b40f6e14026a01438f6962040df49b3` |

EV documents both resolutions as derived from Dukascopy-sourced M1.
The match verifies consistency across these published resolutions.
The labels mark bar boundaries. The underlying first-tick clock,
common observation for the opening bid and ask, and historical
strategy receipt remain unverified. The frozen rule still excludes
an H4 decision made after its scheduled first H1 opening.
[EV catalogue](https://evtradelabs.com/data) · [Frozen protocol](PROTOCOL.md)

## Exness native candle alternative

The documented candle endpoint can return bid and ask OHLC together
using `price_type=both`, with one candle opening timestamp. Requests
require signed, account-scoped access. The published H1 retention
description covers the available history without giving the oldest
EURUSD candle. Listed retention for M1 and M5 is one and two years,
respectively. The schema leaves the common opening-tick identity,
original quote timing and historical client receipt unspecified.
Exness separately documents that Exness Trade uses different historical
and real-time chart feeds. Lineage between the native API candles and
the public Exness quote archive remains unverified. This review used
public documentation only for the API route.
[Candle reference](https://www.exness-api.com/reference/trading/get-candle-history) · [Authentication](https://www.exness-api.com/documentation/authentication) · [Exness Trade chart feeds](https://get.exness.help/hc/en-us/articles/30553857642780-Why-can-chart-candles-differ-in-Exness-Trade)

The public source review incidentally displayed illustrative EURUSD API
schema quotes dated 13 April 2024, 16 March 2026 and 14 April 2026 UTC.
Record those dates for future exposure review. Only the 2024 EV
archive files were downloaded for the comparison.

## Verification and disposition

The diagnostic command writes a new local aggregate report. Compare the
digests in that report with the table above before using a repeat result.

```sh
mkdir -p reports/trendline-source-223
PYTHONPATH=src python3 -m tools.ev_opening_resample_223 reports/trendline-source-223/ev-2024-opening-resample.json
```

The 40 targeted tests passed, covering the diagnostic, strict opening
ceiling, 2022 calendar, historical input, and Phase 10 status. The
canonical status report matches Sprint 222 byte for byte. Phase 10
remains `UNAVAILABLE` with null actual counts. The exact study
source, its permitted use, its historical calendar and feed lineage,
and an independently supported opening availability model remain
open. [Eligibility and prior ceiling](RESULTS-222.md)
