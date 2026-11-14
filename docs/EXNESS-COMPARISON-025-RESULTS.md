# Fixed coverage comparison 025/025B — 2026-10-06

Exness contains quotes in all three disputed intervals. Independent original-file
reconstruction confirms the findings: **826 quotes in the March gap, 873 after
the July broker cutoff, and 969 in the following July hour**. This strengthens
the coverage diagnosis, while annual eligibility and profitability remain
unestablished. No new downloads, broker calls, strategy returns or orders.

## Frozen questions and observed coverage

The [025 plan](EXNESS-COMPARISON-025-PLAN.md) fixed two half-open windows before
comparison: March26 UTC22 through March27 UTC01, and July14 UTC19 through UTC21.
The [implementation contract](EXNESS-COMPARISON-025-PROTOCOL.md) bound original
files, selected rows, all five hours, empty/unavailable counterparts and metrics.
No windows, thresholds, clock hypotheses or strategy rules changed afterward.

| Stated/candidate UTC hour | Exness ticks | HistData candidate ticks | Broker ticks, conditional clock | Forexite literal minute records |
| --- | ---: | ---: | ---: | ---: |
| March26 22 | 590 | 3,499 | Unavailable | 60 |
| March26 23 | 826 | 0 | 2,118 | 60 |
| March27 00 | 1,512 | 4,776 | Unavailable | 60 |
| July14 19 | 1,566 | 3,321 | 592 | 60 |
| July14 20 | 969 | 0 | 0 | 60 |

The March broker capture covers only its original raw02..03 hour, conditionally
UTC23; neighboring hours were never captured in that probe. They are unavailable,
not observations of an empty market. The July capture covers both requested
hours; its UTC20 zero is an empty original capture under the same hypothesis.
Forexite numbers count minute bars, not ticks; ask/spread and quote side remain
unknown. Its literal labels retain unresolved start/end semantics.

The three answers are:

1. **March26 UTC23: yes.** Exness has 826 quotes from 23:00:01.522 through
   23:59:59.985 at its stated Z labels. HistData's frozen candidate has none;
   the conditional broker capture and Forexite reference also contain activity.
2. **July14 tail: yes.** Exness has 873 quotes strictly after 19:25:16.885 and
   before 20:00, continuing through 19:59:57.130. The original broker hour has
   592 ticks and stops at raw22:25:16.885, conditionally UTC19:25:16.885.
3. **July14 UTC20: yes.** Exness has 969 quotes from 20:00:00.618 through
   20:58:39.916. Both older tick sources have zero under the declared mappings;
   Forexite has 60 literal minute records.

These are provider-presence answers, not an overall data-approval pass. Under
the candidate alignment, the missing intervals cannot be assumed to represent
a universal market closure. Clock error, source-specific history gaps or other
source behavior remain possible. No quote was inserted into an older dataset.

## Price evidence and limitations

All hourly bid/ask OHLC and original endpoints remain in the review. Pairwise
price distances are descriptive; no new acceptance threshold or winner exists.
Exness versus HistData close differences are 0.2 pip in each of the three hours
where both have quotes. The disputed March hour's Exness/broker close distance
is 0.5 pip. July19's Exness/broker close distance is 4.4 pips, comparing a full
hour with the truncated broker endpoint; it is not a matched-time fill test.
Literal Forexite close distances range from 0.2 to 2.3 pips, with bar semantics
and quote side unresolved. Full precision, including float-like source decimals,
is preserved in the machine-readable statistics.

Relative price agreement supports this bounded diagnostic alignment. It cannot
independently certify absolute UTC, historical source sessions, contributor/feed
independence, executable prices, commissions or slippage. No blend or synthetic
replacement was created. The original annual gates remain failed.

## Implementation and independent verification

New pure coverage aggregation code distinguishes empty and unavailable inputs,
preserves tied events, enforces half-open boundaries and the strict tail cutoff,
and writes all Exness minute bins, hourly fields and selected-row provenance.
Canonical original-order event hashes retain path/member/record/raw label/time
and exact rational prices. HistData's frozen derivative inventory also matches
selected counts, endpoints and OHLC; originals remain unchanged.

The original independent checker stopped because it assumed each HistData ZIP
contained only its quote CSV. Metadata-only inspection found a same-basename
text companion in each. The failure, original checker and ledger remain sealed
in `reports/exness-comparison-025-check-attempt.json` and prior source bindings.
The [025B supplement](EXNESS-COMPARISON-025B-PLAN.md), declared before rechecking,
requires exactly those two members, declared size bounds, no encryption and a
bounded companion byte/CRC check. It changes no quote or comparison arithmetic.
Exact derivation checks retain the original source and separately version the
checker, its binding verification and output.

The separate checker rebuilt selected Exness and HistData quotes directly from
original ZIPs, broker quotes from original captures, and Forexite rows from its
three original daily ZIPs. Manual timestamp construction and rational arithmetic
matched **19,769 tick records plus 300 minute records**, all original-order event
hashes and lineage rows, **320 hourly/minute bins**, **30 pairwise hourly
comparisons**, and all three answers. It imports no primary comparison parser or
aggregation functions.

**330 tests pass**, including 12 new tests for exact interval/minute boundaries,
tied/order handling, unavailable versus empty captures, strict tail endpoints,
full-precision and malformed prices, separate reference semantics, missing
counterparts, exact checker derivation and companion member/size/encryption/CRC
rejection. All eight original dependency preflights pass before comparison and
at final review. Prior024 groups and all 548 archived members remain verified;
only the four working handoff documents change after the run.

Evidence is in `reports/exness-comparison-025-ledger.json`, `-review.json`,
`-lineage.csv`, the separate `025b-ledger.json`/`025b-checks.json`, and final
review/snapshot manifests, with SHA256 seals. The new final ZIP contains source,
text reports and small fixtures/metadata. Large cached market ZIP/gzip inputs,
timezone files and earlier complete source ZIPs remain externally hash-bound
and verified; this ZIP alone is not a self-contained market-data rerun bundle.
The previous full snapshots and original inputs remain intact on disk.

Next is the declared [historical evidence review 026](EXNESS-EVIDENCE-026-PLAN.md),
not executed: seek dated source-specific clock/session/feed/cost documentation
and report exactly what remains unavailable. No four-year acquisition or trading
approval follows by assumption. Demo order placement remains unavailable;
consumed2025 and reservedNov–Dec2026 exclusions and provider stops remain intact.
