# Sprint 231 · EV development archive coverage

22 November 2026. Audit EV's listed EURUSD H1 and M5 files for the
previously seen 2020–2022 years. Check the proposed warmup and
development archive directly for hourly gaps and opening-price
agreement. The delayed-entry rule still needs qualified opening
and availability evidence for its historical feasibility count.
[EV qualification decision](RESULTS-229.md) · [Delayed-entry trial](RESULTS-230.md)

## Scope declared before download

Use the distributor's closed-year public downloads for this educational
source audit with attribution. Download H1 and then M5 once per year,
in 2020, 2021, 2022 order. Use direct anonymous HTTPS and the exact
advertised compressed sizes, row totals, and UTC edge labels retained
in Sprint 229. The diagnostic stops on an unexpected response or
inventory mismatch. Keep the file bodies and parsed prices in memory.
Retain only archive digests, timestamp discrepancies and comparison
counts. The calculation uses no strategy signals or returns.
[EV Trading Labs catalogue](https://evtradelabs.com/data) · [Retained inventory](RESULTS-229.md)

Use the DST-aware ordinary New York schedule without assigning holiday
exceptions. Record each missing or outside-schedule H1 interval. For
each published H1, compare both opening prices with its first published
M5 row and report the M5 label's offset. Keep an intrahour omission
distinct from an absent hourly bar. The source audit can establish
presence and consistency across products. It leaves original tick
pairing, finalization and the admissible study calendar for independent
review. [Opening method](RESULTS-223.md) · [Ordinary schedule](RESULTS-224.md)

## Observed file coverage

All six responses matched the advertised compressed size, row count,
and label bounds. Every published H1 and M5 timestamp fell within the
ordinary-hours schedule. Every published H1 had M5 children and there
were no M5-only hours.

| Year | Published H1 | Published M5 | Missing ordinary H1 | Missing M5 within published H1 | H1 opening pairs matching first M5 | First M5 label after the hour |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2020 | 6,250 | 74,984 | 38 | 16 | 6,250 | 5 |
| 2021 | 6,240 | 74,863 | 22 | 17 | 6,240 | 2 |
| 2022 | 6,240 | 74,872 | 0 | 8 | 6,240 | 0 |

The missing H1 intervals are below. The 2022 file covers every
ordinary H1 slot. Source notices establish that Christmas and New Year
have trading exceptions. The expected-hours model still treats these
specific intervals as gaps pending date-effective schedule evidence.
[December 2019 notice](https://www.dukascopy.com/swiss/english/about/ournews/market-closures-on-christmas-and-new-year-dbl201708) · [December 2020 notice](https://www.dukascopy.com/swiss/english/about/ournews/market-closures-on-christmas-and-new-year-2020)

| Start, UTC | End, exclusive, UTC | Absent H1 |
| --- | --- | ---: |
| 2020-01-01 00:00 | 2020-01-01 22:00 | 22 |
| 2020-12-25 08:00 | 2020-12-25 22:00 | 14 |
| 2020-12-31 22:00 | 2021-01-01 00:00 | 2 |
| 2021-01-01 00:00 | 2021-01-01 22:00 | 22 |

All 18,730 H1 bars match the bid and ask opens of their first published
M5 row exactly. Seven of the matched pairs have a first M5 label after
the hourly boundary. This includes six by five minutes and one by ten
minutes. The two development cases are 12 and 26 December 2021 at
22:00 UTC. These records leave the scheduled opening price unsupported.
For the other hours the labels align, and the original quote and
price availability still need evidence.

## Effect on the delayed-entry scenario

Use the observed coverage with the same two-second delay and UTC
parent buckets as the existing scenarios. Before the 2021 seam, the
2020 file supports 6,250 H1, 1,613 H4 and 311 D1 windows with every
scheduled H1 child present and modeled publication by the seam.
These are coverage totals from the ordinary-hours schedule.

For 2021–2022, select the first H1 strictly after the modeled decision
and before the next H4 close and liquidation. Require all H4 children
and the selected H1. Under the clock model, omit the two selected
openings whose first published M5 label is late. That leaves 3,152
potential slots. The model that waits for the first possible quote
leaves 3,154 and selects neither affected opening. Nominal UTC and
session-clipped H4 close definitions yield the same totals. These are
coverage-adjusted timing scenarios before setup and price filters.
[Timing assumptions](RESULTS-230.md)

## Verification and disposition

| Year | H1 gzip SHA-256 | M5 gzip SHA-256 |
| --- | --- | --- |
| 2020 | `580d8fee98be5e7b442df5860e37abe282d9944409d050f690dc01c9b056e66a` | `455157bff33742c33b801e84fea588a0903a0b3787b9242e52c6cbd7d3b1ebc1` |
| 2021 | `f074fea763636a313c8ec720190c201ba10f1c1cce7ee4ed75363cddafe0ebef` | `7de79a35247e7e0d58a30cbef1dedc361a647a89774c6848d812b5d23eff2810` |
| 2022 | `2105a72389c35861a54519211ae4d6a22bb8672aeebf42c9ec5185ffcc47cbbe` | `2add6689731ef10a4f54896c140fe0f76ff67a4618592e06943bed7ec5a67e3b` |

```sh
mkdir -p reports/trendline-source-231
for year in 2020 2021 2022; do
  PYTHONPATH=src python3 -m tools.ev_development_coverage_231 "$year" "reports/trendline-source-231/ev-$year-coverage.json" || break
done
```

All 17 targeted tests passed. Independent calculations agreed on the
coverage totals, the seven late labels and both timing results. The
canonical status matches Sprint 230 byte for byte and remains
`UNAVAILABLE` with null actual counts. Source-use qualification,
the date-effective session exceptions, and opening price construction
and strategy availability are still required for admission.
