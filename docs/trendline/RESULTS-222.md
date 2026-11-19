# Sprint 222 · Exness strict-opening ceiling

19 November 2026. Under the 2022 ordinary-hours scenario, unresolved
tie order and the strict paired-quote rule, at most **42** H4 decisions
could still reach an eligible opening before strategy and price filters.
The archived CSV supplies source timestamps and paired prices. Historical
strategy receipt and decision order need separate evidence.
[Calendar scenario](RESULTS-220.md) · [Opening input contract](RESULTS-221.md)

## Bound from retained diagnostics

Use the 2022 calendar from Sprint 220 and the four source and coverage
receipts bound by Sprint 214. Match each reported Sunday opening to the
first scheduled H1 slot after its preceding Friday H4 close. The four
January and five July samples match nine distinct strictly early H4
decisions. Their first Sunday source quotes come after the scheduled
open by 17.540 to 268.088 seconds. Those nine windows cannot meet the
strict paired-quote rule under this schedule. The remaining openings have
unknown eligibility. [Retained weekend bounds](RESULTS-214.md)

| H4 finalization delay | Strictly early | Same-time and unresolved | Already late | No following slot | Sampled late openings among the early slots | Remaining ceiling |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 ms | 51 | 1,560 | 0 | 1 | 9 | 42 |
| 2,000 ms | 51 | 0 | 1,560 | 1 | 9 | 42 |

This is a conditional upper bound on 2022 alone under the declared schedule
and opening rule. Even if all 42 remaining openings yielded an eligible
opportunity for a given strategy, 2021 would have to supply at least 18 to
reach that strategy's 60-opportunity gate for the two-year development
candidate. The bound leaves the 2021 calendar, archive admission and
strategy counts unresolved. [Candidate chronology](RESULTS-199.md) · [Counting rule](PROTOCOL.md#c6-signal-counting)

## Opening evidence decision

- **Exness archive alone.** Keep it as a candidate for bid geometry and
  paired price diagnostics. The archived source-time field leaves the
  independent historical receipt required by `paired_quote` unavailable.
  Earlier archive audit confirms the public CSV format, and the strongest
  zero-delay result in July still depended on unresolved same-time order.
  [Archive audit](RESULTS-203.md) · [July timing](RESULTS-213.md)
- **MetaTrader standard history.** MetaQuotes documents the stored M1
  spread as the minimum bid–ask difference during that minute. Generated
  ticks may use that fixed bar spread. Historical `CopyTicksRange` returns
  `MqlTick`, whose millisecond field timestamps the price update and
  provides no separate strategy receipt field. Ordinary candle history
  leaves the paired opening spread unverified. [Price history](https://www.metatrader5.com/en/terminal/help/trading_advanced/price_data) · [Tester ticks](https://www.metatrader5.com/en/terminal/help/algotrading/tick_generation) · [CopyTicksRange](https://www.mql5.com/en/docs/series/copyticksrange) · [Tick structure](https://www.mql5.com/en/docs/constants/structures/mqltick)
- **Reviewed bar-open approximation.** This route still needs an identified
  series, a defensible opening bid and spread, and an independently
  reviewed availability model for the frozen first-slot rule.
  [Opening semantics](PROTOCOL.md#c4-entry-and-data-level-semantics)

## Reproduce

```sh
PYTHONPATH=src python3 -m tools.exness_source_ceiling_222 NEW-REPORT.json
```

The command uses the four exact retained JSON receipts in the ignored
reports tree. It verifies their hashes and archived source bindings,
recomputes the calendar and names the nine excluded slots. It reads
retained metadata only. The nine distinct dates and lags also reconciled
against the Sprint 214 summary and Sprint 220 calendar digest. All 57
targeted tests passed. The canonical Phase 10 status matched Sprint 221
byte for byte and remains `UNAVAILABLE` with null actual counts. Archive
use, historical calendar and opening-method qualification remain open.
