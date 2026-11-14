# Quote recovery 010 results — 2026-10-01

The separate February–July 2023 broker capture recovered **9,838,711 original
bid/ask ticks**. It addresses much of HistData's missing coverage, but it also
exposes an incomplete broker hour. **Data eligibility remains failed.** No
new strategy returns were calculated and execution remains unavailable.

## What was implemented and acquired

`RECOVERY-010-PLAN.md` was declared before the first new tick request. Its
twelve-hour July 11 sample returned 24,266 ticks; all twelve bid candles exactly
matched the previously stored broker reference. A separate SQL calculation
confirmed that aggregation. The sample passed the unchanged expansion screen.

`scripts/recovery-010.py` and `src/forex_demo_lab/recovery.py` then acquired
raw broker labels 2023-02-01 through 2023-08-01 exclusive in 91 disjoint chunks,
each at most 48h, with requests of at most six hours. Each actual demo-account
type was checked around every read. Algo Trading was off throughout. Original
event order, bid/ask quotes and 12,774 equal-millisecond transitions were
preserved. The compressed tick files total 76,799,922 bytes.

The new files are under `data/recovery-010`; no quotes were interpolated or
spliced into HistData. Completed chunks must pass hash, schema, bounds, account
type and request-inventory checks before resume. Partial failures cannot be
silently retried or overwritten. No terminal settings or other EAs changed.

| Raw broker month | Ticks | Hours with ticks | Additional hours versus HistData* |
| --- | ---: | ---: | ---: |
| February 2023 | 1,924,722 | 480 | 49 |
| March 2023 | 2,344,858 | 550 | 160 |
| April 2023 | 1,243,397 | 480 | 147 |
| May 2023 | 1,482,119 | 552 | 161 |
| June 2023 | 1,396,008 | 528 | 156 |
| July 2023 | 1,447,607 | 503 | 140 |
| Total | 9,838,711 | 3,093 | 813 |

*The coverage census assumes the previously observed relative mapping
`broker raw = HistData raw +7h`. This is conditional evidence, not proof of
absolute UTC or a full-period clock rule. One HistData hour has no broker
ticks under this mapping: broker raw March 12 23:00. It remains flagged.

## Complete audit and the remaining failure

All 4,344 requested hours were inventoried. Of the 3,093 hours with quotes,
3,092 match the reference within the declared 0.05-pip tolerance on every bid
OHLC value. One fails. There are no reference candles without ticks and no
tick hours without a reference candle. The other 1,251 hours are empty and
unclassified. Three fall on raw weekdays: March 17 23:00, March 24 23:00 and
July 14 23:00. No empty hour was automatically accepted as a market closure.

There are 26 inter-quote gaps over one hour and 77 seams between nonempty
chunks, including gaps through entirely empty chunks. Those gaps remain
unclassified. Source clocks and the difference between broker trading hours
and missing history still require evidence.

The failed candle is **July 14 22:00 in raw broker labels**, with 592 ticks:

| Bid value | Original and re-requested H1 | Full captured ticks |
| --- | ---: | ---: |
| Open | 1.12342 | 1.12342 |
| High | 1.12342 | 1.12342 |
| Low | 1.12302 | 1.12295 |
| Close | 1.12303 | 1.12301 |

The low differs by 0.7 pip and the close by 0.2 pip. A separately declared
two-hour tick re-request returned exactly the same 592 ordered timestamps,
bid/ask quotes and flags. A separately declared H1 re-request returned the
same disputed candle. It matches eight earlier tick prefixes, ending between
tick 210 and tick 244 of 592, consistent with an incomplete stored candle;
the mechanism is unproved. Both requests return no quotes/candle at 23:00.

More importantly, the broker ticks end at **22:25:16.885**. A post-failure
diagnostic of the original HistData hour, assuming +7h, finds **1,766 further
quotes**, through HistData label 15:59:59.185. All 26 overlapping minute closes
agree within 0.3 pip; median difference is 0.15 pip. This supports the alignment
and indicates that the broker history itself lacks the end of the hour, in
addition to the disputed H1 aggregation. Rebuilding from those broker ticks
alone would still leave an incomplete hour. No mixed replacement was made.

## Verification and reproducibility

**192 tests passed**, including twelve added recovery/SQL checks. They exercise
missing-hour handling, all-price matching, equal-ms ordering, both quote sides,
invalid quotes, wrong resume bounds/account type, incomplete hour inventories,
gaps across empty chunks, duplicate/invalid reference bars, changed file hashes
and detection of an incorrect reconstructed close. Existing risk-control and
account-guard tests remain passing.

`scripts/check-recovery-010.py` independently rebuilt every nonempty hour from
all 9,838,711 ticks using SQL; all counts, bid/ask OHLC and first/last event
timestamps match the acquisition audit. This verifies aggregation, not market
completeness. Prior 004/005 archives, all thirty 008 result hashes and the
original failed 009 reviews were verified unchanged.

Local artifact hashes:

- `recovery-010-ledger.json`: `55d851aba69e968f60cc049740f2b20f3bf08fb19be4925d8af5b1a04a86efc7`
- `recovery-010-review.json`: `9116a20bd252ad39af523b3c2155a0a60b4e64e56ce2090d83c77506601503e0`
- `recovery-010-checks.json`: `078b7e14228a2f5e088327666f31680ddf72252dcbb53ce525a597b6d814dccf`
- Frozen source ZIP: `f3c0892a65cddea20e351ff41e5daee1de66f30f90adac250238da1262cc95c7`

The source files bound by the 010 ledger and its original plan remain frozen.
Follow-ups have separate declarations/reports; use the preserved original
reference for reproduction. `scripts/diagnose-recovery-010-tail.py` reproduces
the conditional tail diagnostic. All acquisition/review jobs have completed.

## Next work

Resolve independent UTC evidence and the repeated October source hour, then
review a source capable of covering the July 14 tail and the flagged session
hours. Keep the 009 selection rules unchanged and implement the chronological
replay runner against separately reviewed normalized data. The 2025 holdout
remains consumed/excluded and future November–December 2026 remains reserved.
Historical costs are still unverified. This stage establishes no new strategy
profitability and authorizes no execution.
