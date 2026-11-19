# Sprint 225 · EV H4 and daily resampling

20 November 2026. Compare EV Trading Labs' published 2024 EURUSD H4
and D1 bars against the hourly EURUSD file from Sprints
223 and 224. EV documents UTC bucket-open labels and precomputed M1
resampling. The frozen strategy derives H4 from H1 and uses completed
D1 for its context variant.
[EV data catalogue](https://evtradelabs.com/data) · [Frozen protocol](PROTOCOL.md)

## Scope declared before download

Make one direct anonymous HTTPS GET for each listed file in order.
Check the advertised compressed sizes. H1 must also match the Sprint
223 hash. Record the hashes of the new H4 and D1 files. Keep archives
and prices in memory and retain only hashes and diagnostic counts.

1. [H1 2024](https://evtradelabs.com/api/simulator/data/EURUSD/H1/2024.json.gz), 195,309 bytes.
2. [H4 2024](https://evtradelabs.com/api/simulator/data/EURUSD/H4/2024.json.gz), 55,333 bytes.
3. [D1 2024](https://evtradelabs.com/api/simulator/data/EURUSD/D1/2024.json.gz), 11,838 bytes.

For each UTC H4 and D1 bucket, build bid and ask OHLC from its
published H1 children in time order. Compare both sides exactly and
count absent or unmatched buckets separately. Track starts or ends
where the first or last published H1 child sits inside the parent
bucket. Compare coverage against the Sprint 224 ordinary-hours
model with its holiday omissions left unresolved. The comparison
uses the already-seen development year and the published products.
It yields no strategy counts or source admission.
[H1 file hash and scope](RESULTS-223.md) · [Ordinary-hours scenario](RESULTS-224.md)

## Results

The three archives matched their catalogue sizes, and the H1 digest
matched Sprint 223. All 1,616 H4 bars and all 314 D1 bars matched the
bid and ask OHLC rebuilt from the 6,247 published hourly bars. Every
bucket with published H1 children had a corresponding parent.

| Parent bucket characteristic | H4 | D1 |
| --- | ---: | ---: |
| Published buckets with exact bid and ask OHLC | 1,616 | 314 |
| Published buckets with a shorter ordinary session window | 104 | 104 |
| Published buckets missing at least one expected H1 child | 5 | 4 |
| Absent buckets with at least one ordinary H1 slot | 8 | 0 |
| Published buckets labeled before their first H1 child | 55 | 53 |
| Published buckets whose last H1 child ends before the UTC bucket end | 54 | 54 |

These characteristics can overlap. Under the ordinary schedule, for
example, a summer Sunday D1 bucket carries a 00:00 UTC label and its
first hourly interval begins at 21:00 UTC. A summer Friday H4 bucket
starting at 20:00 UTC has one scheduled hourly interval before the
21:00 close. This comparison measures the location of published H1
children within a UTC bucket. It cannot timestamp strategy receipt or
establish when a partial H4 or D1 bar was final. The published parent
bars also reproduce gaps in their hourly inputs. Admission still needs
an exact session calendar and publication model for the chosen source.
[Frozen entry semantics](PROTOCOL.md#c4-entry-and-data-level-semantics) · [Broker hours](https://www.dukascopy.com/swiss/english/forex/forex-trading-accounts/link/)

The D1 comparison confirmed that EV published nine H1 bars on 25
December UTC. Sprint 224's text had said seven. Its interval table
correctly accounts for 15 missing hours on 25 December and another
two on 24 December. The 41-hour annual total was correct.
[Corrected calendar findings](RESULTS-224.md)

| File | SHA-256 |
| --- | --- |
| H4 | `0cf8b60ef95165b52c60bbceac2d30820a433469b53b8bdfa1f1420b37921e93` |
| D1 | `c94a8d64cb2b683e1c9fdb439ae8b9a20f075f6fd91d1025dc26a08bc75535ea` |

## Verification and disposition

```sh
mkdir -p reports/trendline-source-225
PYTHONPATH=src python3 -m tools.ev_parent_resample_225 reports/trendline-source-225/ev-2024-parent-resample.json
```

All 44 targeted tests passed, including partial buckets, interior
gaps, price-field differences, and the existing historical input
and availability checks. The canonical Phase 10 status report matches
Sprint 224 byte for byte.
It remains `UNAVAILABLE` with null actual counts. The diagnostic
supports using the published higher-timeframe bars to cross-check
H1-derived geometry on this sample.
Historical opening availability, source-use qualification and the
full development and warmup inputs remain open.
