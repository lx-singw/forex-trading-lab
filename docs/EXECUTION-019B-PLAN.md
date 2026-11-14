# Executable fill equity metrics repair 019B

Declared 2026-10-06 after preserving 019 run and failed independent review.
30 cases ran across 518 checkpoint boundaries. All cash, position, fees, swap,
pause and restart checks pass. Only 20/30 complete cases pass: ten target
overshoot paths expose a peak/tick-drawdown mismatch. Unattainable target quote
profit enters peak tracking before the actual limit fill. Original 019 code,
event annotations, expected results and failure evidence remain frozen.

Implement a separate versioned tick/research simulator, inheriting original
execution rules. Change the equity-mark calculation only: when the current
exit quote triggers an existing stop or target, mark the equity of that modeled
fill including its exit fee and adverse stop slippage. For targets use the
fixed limit; for stops use observed bid/ask plus adverse slippage. For a held
position without a trigger, preserve quote equity. Actual opening/closing,
strategy rules, sizing, carry fees and loss limits are inherited unchanged.
Final liquidation still uses the inherited close then mark. Add a checkpoint
metric-version marker; reject legacy/mismatched checkpoints instead of silently
continuing with an inflated old peak. No automatic state migration.

Mechanically generate the supplemental audit runtime from the frozen original
driver with only simulator imports and injected probe class names changed.
Freeze this code, repair, tests, plan, original failed evidence and ledger before
the repair consumes any 019 quote path. Rerun all unchanged 30 cases and all 518
restart boundaries. Require every field to match the same Decimal expectations.
Additionally compare original/repaired traces excluding only peak/drawdown,
and compare all fills, costs, pause states, position sizes, C04 decisions and
restart flags exactly within the original tolerances. No selective reporting.

Add regression tests for both target directions, actual C04 diagnostic paths,
stop gaps with carry costs, legacy/mismatched checkpoint rejection, and retained
unrealized equity while no exit triggers. Require the complete suite to pass.
Do not alter the historical 014 runner to use the new engine: its version is
frozen, data remains rejected, and any future migration needs a separately
declared evaluation plan. Record the reporting defect's applicability to earlier
tick-derived drawdown without recalculating market returns. Equity/P&L does not
improve because of this metric repair. No new performance claim, broker API,
MT5 operation, order code, live toggle or market-data acquisition.
