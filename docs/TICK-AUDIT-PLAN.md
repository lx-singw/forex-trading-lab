# Tick/data audit 001 — 2026-09-30

This is an execution/data diagnostic, not a new performance experiment or an
optimization. Experiment 001 and its consumed holdout remain unchanged. The
exact Python source matching its frozen hash was archived locally in
`reports/experiment-001-source.zip` before adding this audit code.

Initial one-hour availability probes returned ticks in 2024, 2025 and a recent
2026 control. In particular, ticks exist inside a July 2024 interval whose H1
bars were missing from the original capture. No rates are being replaced based
on results; audit the discrepancy and preserve both observations.

Bounded primary windows, in **unconverted API source labels**, selected before
tick-based execution analysis:

- 2024-01-04 19:00 through 2024-01-05 09:00: the first development trade's
  entry through the end of its reported closing candle (14 hours).
- 2024-07-02 12:00 through 2024-07-03 01:00: the development history gap,
  with an observed reference hour on each side (13 hours).
- 2024-03-15 22:00 through 2024-03-16 00:00: a shortened Friday session
  during the US/European daylight-saving mismatch (2 hours).

The first and gap windows were also touched by availability probes. Window
selection is diagnostic, not a random or representative performance sample.
There will be no new 2025 holdout evaluation or parameter adjustment.

Preserve millisecond timestamps and event ordering. Compare reconstructed bid
OHLC against the original H1 source labels, so no guessed UTC offset is needed
for that comparison. Record opening and distributional spreads, invalid quotes,
missing intervals and API errors. Equal-millisecond events are retained, and
inclusive API boundaries are filtered to disjoint half-open windows.

For the first trade only, inspect the first observed stop/target crossing using
the original fixed side/stop/target. Record the opening quote and spread filter
decision as diagnostics. This is not a full tick strategy simulation: original
entry, sizing, portfolio state, commissions and swaps are not reoptimized or
recomputed, and observed ticks do not prove executable liquidity.

Also re-request H1 and M1 data in the July gap. Record whether it remains absent
or changes after tick retrieval. A same-feed match cannot independently verify
the provider; a mismatch must remain a validation failure until explained.
Do not create broker accounts, send orders, enable Algo Trading or edit terminal
settings. Timestamp/DST and historical cost uncertainties remain explicit.
