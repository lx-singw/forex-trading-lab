# Sprint 186 · Phase 7 accounting acceptance

18 November 2026. Phase 7 software acceptance is complete for the
invented Level B and Level Q adapters. A separate rational-arithmetic
calculation reconstructs the ordered Level Q quote tape, entry
eligibility, volume, commissions, marks, margin, equity, financing,
daily pauses and final position state. It compares receipt and
effective times for each projected account event.
[Phase 7 roadmap](../tori_trendline_strategy_full/TORI-TRENDLINE-BUILD-ROADMAP.md#phase-7-execution-risk-and-costs-size-m)

## Receipt-order correction

The restart audit found that a later entry could backfill flat-account
day references with availability timestamps earlier than the entry
receipt. Prefixes taken before that entry omitted those references.
The quote ledger now uses the receipt of the executable quote that
advances the account into a new UTC day, including idle periods.
If a quote is sourced just after midnight and received 600 milliseconds
after it, the day reference takes effect at midnight and appears at
the receipt. The audit then compares the shorter event stream with
the corresponding receipt prefix of the longer stream.
Checkpoints from the earlier quote replay source require their
matching checkout or a replay of the original tape.

## Observed results

| Area | Evidence |
| --- | --- |
| Quote order and price | Source order, the 2-second freshness limit, spread eligibility, and equal-timestamp sequence selected the expected entry. E2 filled at its limit before a later stop-side observation. |
| Capacity and sizing | A gap exit blocked another setup on that same quote. The realized pause blocked a later same-day setup, and the next valid day sized from reconciled cash. A minimum-volume skip and an expiry consumed their respective attempts. |
| Loss pause | A floating breach latched through recovery. Missing boundary equity evidence prevented a day reset until a valid subsequent day. |
| Costs and liquidation | Exact cash, equity, margin, commission and weekday financing matched on both profiles. The missing-liquidation replay kept the last mark and unpaid exit commission. An unpriceable slipped stop left an unresolved liability. |
| Retained quote accounting | The 120 LONG target and 125 SHORT gap matched on original executable bid, ask and timestamps under both costs. The retained stops and targets supplied the setup inputs. Entry and exit prices, sizes, price P&L, financing, net cash and closing-quote pauses agreed. |
| Restart | The full midpoint strategy matched independent account states before entry, while held and after close. Restoring the held and closed checkpoints reproduced the same result. A rehashed cash change and a reversed cursor failed. Changing a future quote changed the tape hash and preserved the earlier setup decisions and account events. |

Phase 7 acceptance combines this Level Q audit with the retained Level B
price, sizing, liquidation, restart and independent accounting checks.
The scope is software behavior on invented inputs. Quote coverage,
clock qualification, actual costs and market admission remain open.
Phase 8 starts with the causal replay viewer.
[Level B accounting audit](RESULTS-184.md) · [Level Q adapter](RESULTS-185.md)

## Verification

All 186 targeted tests passed. Nine new tests independently
reconciled 20 reports. The new and retained quote suites ran 19 tests
in 138.918 seconds. The retained Level B accounting suite ran 70 in
157.774 seconds. The entry and replay suites ran 71 in 290.924 seconds,
and the FXR, DLY and setup acceptance suites ran 26 in 561.700 seconds.

```sh
PYTHONPATH=src:tests python3 -m unittest test_trendline_quote_acceptance_186 test_trendline_quotes_185 -v
PYTHONPATH=src:tests python3 -m unittest test_trendline_account_parity_184 test_trendline_ledger_183 test_trendline_risk_182 test_trendline_exits_181 test_trendline_fills_164 -q
PYTHONPATH=src:tests python3 -m unittest test_trendline_entries_174 test_trendline_bounce_177 test_trendline_brk2_176 test_trendline_breaks_173 test_trendline_data_163 -q
PYTHONPATH=src:tests python3 -m unittest test_trendline_fxr_175 test_trendline_dly_178 test_trendline_setup_acceptance_179 test_trendline_levels_180 -q
```
