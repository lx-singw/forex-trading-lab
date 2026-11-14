# Bounded strategy experiment 028 — not executed

Use the failure mechanisms recorded in 027 to test two fixed hypotheses. This
is one new development experiment, not a promise or search for a strategy that
wins every time. The already reviewed trend-family literature in
`STRATEGY-RESEARCH-008.md` motivates direction confirmation; it does not validate
these hourly EURUSD implementations.

## Declare candidates before new returns

- C00: unchanged SMA20/50 control.
- C02: unchanged 20-bar close-confirmed channel breakout control.
- C04: unchanged ER20 selector control, including range and neutral branches.
- C05: C04 trend-only ablation. Use exactly the existing ER20 >=0.35 breakout
  branch; all ER <0.35 values abstain, including previously eligible range signals.
  Zero-path/invalid/warmup handling stays conservative. No threshold optimization.
- C06: C02 breakout plus slow direction confirmation. Compute SMA50 and SMA200
  from preceding completed closes, using the existing C01 periods. A positive
  C02 signal requires SMA50 > SMA200; a negative signal requires SMA50 < SMA200.
  Equality or disagreement abstains. Do not require a new SMA crossover. This
  tests a slower directional context rather than fitting an additional period.

C05 tests whether the selected range exposure harms this engine; C06 tests
whether fast breakouts improve with slow direction agreement. Both hypotheses
are informed by already-seen data and may fail. New combinations can create
different entries because abstention frees capital; simply removing old losing
trades is not an acceptable performance calculation. C01/C03 original results
remain visible as context and are not deleted from the research record.

## Budget, data and unchanged constraints

Exactly five active candidates × January/April/July 2024 × base/adverse costs =
30 scenario outputs, plus an arithmetic CASH reference. Only 12 scenarios use
new challengers; 18 are control replays. Common 201 observed closed-bar warmup,
008 evaluation start boundaries and exact quality/provenance/data hashes stay
fixed. These are reused development windows with independent monthly capital
starts, not continuous annual results or unseen evaluation. No extra candidate,
parameter grid, date change or rerun after seeing outcomes within this budget.

Risk, lots, spread guard, ATR14 ×2 stop, 2R target, commissions, slippage,
financing, daily loss pause and one aggregate position remain unchanged. No
martingale, recovery stakes, account creation or execution capability.
2020–2023 annual gate remains failed. No 2025 optimization or reserved
Nov–Dec 2026 quote access; no new public acquisition or provider contact.

## Implementation and pre-return declaration

Implement separately versioned pure challengers and offline research simulator;
preserve 008 implementations/specification/reports. Apply the independently
verified corrected executable-equity marking from 019B/020 in a separately
declared adapter; ensure checkpoints reject legacy metric state. Do not silently
rewrite legacy drawdown outputs or weaken annual-runner eligibility checks.
Create an exact specification/protocol and immutable code/data/config/output
ledger before quote replay. State which development reviews authorize it.

Meaningful tests: closed-bar prefix causality, ER and SMA equality boundaries,
warmup/zero path, direction conflict/abstention, inherited risk/duplicate/restart
and corrected marking behavior. Preflight all 027 bindings and original cached
datasets. Control replay cash, fills, costs and entry decisions must match exact
008 reports; drawdown changes are expected only from the documented metric
correction and independently checked. Preserve any mismatch and stop evaluation
claims until explained under a separately declared repair; do not tune strategy
rules to eliminate a discrepancy.

Report all 30 outcomes, every abstention/path difference, net expectancy, trade
count, corrected drawdown and base/adverse sensitivity. Independently reconcile
cash/fees/risk and check control parity. No automatic winner selection,
deployment or promotion. End with whether either hypothesis merits further
chronological testing once suitable data qualify; insufficient observations or
mixed outcomes must remain explicit. Orders remain unavailable.
