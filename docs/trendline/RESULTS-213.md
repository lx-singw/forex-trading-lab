# Sprint 213 · Exact opening quotes at H4 decision boundaries

19 November 2026. Check whether the three exact-hour July quotes identified
in Sprint 204 occur at the first H1 opening after an H4 close. This is a
source and schedule diagnostic for the frozen first-open rule.
[July archive audit](RESULTS-204.md) · [Entry rule](PROTOCOL.md#c4-entry-and-data-level-semantics)

## Scope declared before archive access

Make one ordinary HTTPS GET of the [previously audited July 2022 EURUSD ZIP](https://ticks.ex2archive.com/ticks/EURUSD/2022/07/Exness_EURUSD_2022_07.zip).
Require HTTP 200, ZIP media type, 11,300,072 bytes and SHA-256
`b6ea0b6122cd87cd922eaccc19e2ce896f1004f70ce32243a944fea8cf2b7bd6` before
parsing. Use the Sprint 212 ten-second socket timeout, 45-second response
deadline, single CSV member and 256 MiB decompressed cap. Stop on a
mismatch. Use no credentials, redirects or retries. Retain only hashes and
diagnostic aggregates. The published archive guide covers private diagnostic
analysis. Full-study use, retention and source admission remain unresolved.
[Archive guide](https://www.exness.com/blog/product/exness-tick-history-bid-ask-prices/) · [January method](RESULTS-212.md)

Use the ordinary-hours H1/H4 calendar from Sprint 208. Check H4 intervals
wholly inside July. Select the first scheduled H1 opening under the frozen
rule and keep it in the comparison only if its H1 interval is wholly in
July. Report quote presence in the trigger's children before comparing the
first opening quote's source timestamp with the scheduled edge. Test the
preexisting zero and 2,000 ms publication-delay cases. Keep same-time
decision order conditional. Report paired opening spreads for descriptive
comparison with January, including the five sampled Sunday reopenings.
This diagnostic uses no new market dates, strategy rules, trade outcomes or
validation prices. [Calendar scenarios](RESULTS-208.md)

## Results

The response matched the prior archive hash and contained 1,626,091 rows.
Every row fell within the 504 modeled H1 intervals, with a first pair in
every interval. The opening-lag buckets reproduced the Sprint 204 counts.

| Sample | H1 pairs | Exact source opening | Median spread, pips | 95th-percentile spread, pips |
| --- | ---: | ---: | ---: | ---: |
| All July H1 | 504 | 3 | 0.6 | 1.5 |
| Five July Sunday reopenings | 5 | 0 | 3.8 | 8.6 |
| All January H1 | 506 | 0 | 0.6 | 0.7 |
| Four January Sunday reopenings | 4 | 0 | 3.7 | 3.8 |

Each scheduled H1 child of all five sampled shortened July Friday H4 bars
contained a quote. All five corresponding Sunday first pairs came more than
one second after the opening. Their spreads describe those later quotes.
[January diagnostic](RESULTS-212.md)

Of 131 H4 intervals wholly inside July, 130 had their first scheduled entry
H1 within the month. All 130 had a quote in every scheduled trigger child.
The remaining July H4 close pointed to an H1 outside the sample. The first
quote was labeled after the opening in 128 of the 130 in-scope pairs. Two
of the three exact-hour H1 quotes matched these H4 entry windows.

| Modeled publication delay | Exact edges with time to decide strictly before open | Exact edges with unverified same-time order | Exact edges reached too late |
| --- | ---: | ---: | ---: |
| 0 ms | 0 | 2 | 0 |
| 2,000 ms | 0 | 0 | 2 |

The zero-delay case would need both a timely receipt and the declared
decision-before-open order. At 2,000 ms, the two exact labels fall at
the scheduled open before the modeled decision is available. Neither month
supplies a qualifying weekend opening under this exact-quote method.
These diagnostics establish no actual strategy counts. [Frozen entry order](PROTOCOL.md#c4-entry-and-data-level-semantics)

## Verification and disposition

The diagnostic reused the pinned download and CSV validators from Sprint
212 and the existing H4 timing comparison. An ignored receipt retains the
scope hash and aggregates. Raw quote pairs were processed in memory. All 81
targeted opening, timing, fill, source coverage and signal-count tests passed.
The canonical Phase 10 status remains `UNAVAILABLE` with null actual counts.
Historical use still needs source admission and a justified Level B price,
spread and availability model. The exact-quote examples leave same-time
receipt order unverified.

```sh
PYTHONPATH=src python3 -m tools.exness_h4_opening_213 new-july-report.json
```
