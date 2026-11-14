# Corrected-metric chronological runner 020

Declared 2026-10-06 before new fixture generation or replay. Preserve original
014 code, ledgers, data and reports, plus both 019 audit versions. Generate a
separate runner mechanically from frozen 014 with only corrected simulator
import, versioned metadata, explicit source inventory and ledger-version checks
changed. Use executable_fill_equity_019b_v1. Keep all annual input/review gates,
201-hour warmup, folds A/B, five C00–C04 candidates, two modeled costs,
training-only selection, capital resets, cost/strategy rules and numeric screens.
No automatic migration of legacy ledgers/checkpoints or older report revision.

Declare two software fixtures. First reuse byte-identical saved 014 invented
sinusoidal annual data (2020–2023) for compatibility: 40 corrected runs compared
with all 40 preserved reports. Old fixture has no targets, so add one fixed
challenge: 520 observed hourly bars per year, starting January 1. Flat bid 1.1
except hour 200/201 at 1.101 and hour 300/301 at 1.099. At hour 201+100ms add
bid/ask 1.111/1.1111; at hour 301+100ms add 1.089/1.0891. All other spreads
0.0001. No time/parameter changes after replay. Use explicit synthetic review
and provenance; lack of full-year market coverage must never be approved.

Freeze this plan, generator, generated runner, CLI/checker/tests, repaired
engine, original sources, prior report bindings and challenge bytes before
returns. Freeze three distinct experiments before any replay: corrected old
fixture (40), legacy challenge shadow (40), corrected challenge (40). These
120 runs are software controls, not a larger strategy search or optimization.
Compare 80 corrected scenario reports with their corresponding legacy controls.
Keep training choices locked before tests; publish every control and CASH.

Require matching configs/windows/data, cash P&L, all trades/fills/costs, marks,
annual/quarter statistics and non-drawdown metrics within 1e-8; prices/lots
1e-12. Report all drawdown changes, require no increase within 1e-12, and
require challenge target fills and at least one corrected difference. Validate
choices by the unchanged training selector; hashes can change because metrics
change. Disclose any choice/eligibility changes without interpreting synthetic
wins as an edge. Preserve earlier CASH decisions as historical evidence.

Independent checker reconstructs every trade charge and open quarter/year
mark with the existing independent 014 arithmetic checker. Additionally rebuild
post-fill tick equity, peak and drawdown from input quotes, recorded trades and
an independent Decimal cash ledger. Apply declared UTC weekday swap/triple rules
without simulator helpers. Check all 80 corrected accounts, not just target
examples; retain marks and final liquidation costs. Check ledger/version tags
on every corrected scenario, choice and summary. No false legacy labeling.

Meaningful tests: generated changes limited to declared sites; corrected class
is actually instantiated; legacy-ledger rejection; invalid/missing version;
market reviews/blocked years/gaps reject before output/data iteration; unchanged
choice-lock/future exclusion; injected changed P&L/fill/drawdown/bindings reject.
Run full suite after freezing. Publish any failed attempts; no overwrite/retry
without a declared repair. Existing labels/normalization/reference reviews must
be rejected by the actual 020 market path before performance. No dataset
approval, market download, broker call, MT5 run, orders or real-money capability.
2025 excluded; reserved November–December 2026 untouched. Future market replay
still requires independent chronology/coverage and cost evidence; readiness false.
