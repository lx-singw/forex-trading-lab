# Fresh-data readiness 031 — complete

The running terminal passed actual DEMO and USD checks, Algo Trading off, and the private identity remained stable around all120 reads and the completion guard. 120 accepted snapshots span 2026-10-06T10:39:04.392000+00:00 through 2026-10-06T10:40:04.188000+00:00; 53 repeat the preceding timestamp/bid/ask. Maximum measured quote-read latency is 1ms. Raw-label minus receipt ranges from 10795.879 to 10798.642 seconds (approximately three hours ahead). Receipt timing, polling delay and stale quotes prevent interpreting this as an exact offset or historical UTC certification.

## Local qualification inventory

The fixed catalog covers14 canonical provenance/review files and the data-directory names at freeze. None supplies a qualified fresh validation dataset. The2024 windows are reused development;2025 is consumed; annual2020–2023 sources remain blocked on clock/coverage/cost evidence. This is a scoped inventory, not proof that other sources do not exist. No historical quote rows or strategy returns were read or recomputed.

## What changed

Separate fresh_data_031.py and fresh-data-031.py add a receipt-clock probe. It connects only to the already-running installed terminal, with the pinned existing Windows Python/MetaTrader5 files. It has no history request, order API, terminal launch, login, symbol selection or settings/deployment action. It checks actual account type and connection around every quote, rejects Algo Trading on, and compares private account/server identity without exporting either. Source labels, bid/ask and receipt/monotonic bounds remain separate.

Maximum120 reads at500ms spacing; a60-second monotonic budget prevents starting a new read at the deadline and rejects a late return. Native in-flight calls cannot be forcibly time-limited by this sampler. Date, reversed-clock, raw-label24-hour bound, invalid quote and identity errors stop and preserve accepted observations without retry. Exception details are redacted.

## Verification and preservation

400 software tests pass (16 new), before any MT5 connection. New cases include demo/real/contest/unknown/boolean modes, disconnect/identity/server changes, Algo Trading/currency/symbol rejection, invalid quotes, tied/repeated snapshots, clock reversal/reserved receipt dates, elapsed/read bounds, partial preservation and privacy. Existing strategy/risk tests remain intact.

Preflight verified all900 prior bindings,864 archived members and36 external inputs. New ledger freezes67 bindings,14 metadata files and exclusive outputs. Independent checker recomputes all accepted observation ordering, clocks, bounds, repeats and arithmetic; fixed metadata evidence exactly matches originals. Original031 code is frozen;030 and earlier evidence is preserved.

Runtime account checks are performed by the collector. The independent checker validates its sealed evidence and arithmetic, not a second broker connection or independent proof of account/session identity. Local-clock accuracy and complete provider tick delivery remain uncertified.

Artifacts: reports/fresh-data-031-{ledger,tests,inventory,probe-reservation,probe,checks,review,final-source}.json with seals. Probe contains only approved current contract fields and quote/receipt observations; current contract properties do not establish historical fees/swaps or real fills. Final ZIP archives sources/reports/small fixtures. Prior ZIPs, large cached data, timezone files and pinned Windows runtime files remain verified external bindings; it is not a self-contained replay bundle.

## Next step and limits

Read FRESH-TICKS-032-PLAN.md: one exact bounded full-tick sample and independent original-row/witness audit, not executed. Polling can miss intervening quotes; 53 repeated snapshots in a completed run are not missing-tick or market-closure evidence. Do not subtract an assumed three-hour offset and call the data UTC.

Fresh performance and annual eligibility remain false. No profits, strategy selection, performance replays, broker accounts, provider contacts, credentials, paid access, stopped-provider retries, execution mode or orders. Consumed2025 and reservedNovember–December2026 remain excluded. Demo-forward trading is unactivated; this is collection infrastructure only.
