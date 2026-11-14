# Independent data check 003 — predeclared 2026-09-30

Order: cross-source checks, separate development data, full tick simulation,
then consideration of demo forward execution only if the evidence supports it.

Before calculating cross-source differences or new performance:

- Use HistData Generic ASCII EURUSD bid/ask ticks for January and July 2024.
  The July archive has downloaded; only its first row/schema has been inspected.
  Keep original ZIPs with hashes. Provider documents fixed EST (UTC-05:00),
  without DST: https://www.histdata.com/f-a-q/data-files-detailed-specification/.
- Compare existing MT5 winter and summer tick windows against this provider.
  Test raw MT5 labels minus 0, 1, 2, 3 and 4 hours. Expected hypotheses are
  January +2 and July +3. Report every candidate, not just the best alignment.
- Diagnostic corroboration requires all sampled hours present, median absolute
  bid-close difference <=1 pip, maximum <=3 pips and the expected candidate
  better than every alternative by >=2 pips in mean absolute close difference.
  These are research screening thresholds, not a feed certification.
- Compare July original H1 and reconstructed ticks separately. Never merge feeds
  or repair the original experiment. Cross-provider agreement does not establish
  common upstream independence, broker fill quality or entire-year DST rules.
- If those checks pass, normalize these two months as separate development
  samples, not an annual dataset. Audit all rows and gaps; no interpolation.
  Reuse baseline SMA20/50, ATR14 x2, 2R, 0.25% risk, 1% daily entry pause,
  1.5-pip spread cap, with independent $10,000 starts and 1:10 model leverage.
  Warm up separately. Both months are development, not unseen holdouts.
- Before performance, freeze source/config/dataset hashes. Costs remain explicit
  assumptions: $7/lot round-trip, 0.2-pip adverse entry/stop/final-exit slippage,
  long/short swaps -$3/-$1.50 per lot, Wednesday triple, UTC daily reset.
  Also report a predeclared adverse-cost scenario: $10/lot, 0.5-pip slippage,
  long/short swaps -$6/-$3. Do not select parameters based on these outcomes.
- A short two-month simulation alone cannot authorize demo forward execution.
  Data integrity, runtime execution guards, reconciliation and restart/loss
  safeguards must all pass before any order capability is activated. If evidence
  fails a stage, report the failure and keep later dependent stages inactive.

## Timestamp amendment — before fresh-window comparisons

The original January check passed; July +3 failed. July +2 had mean absolute
close difference 0.1231 pip, versus 5.3000 for +3. Preserve both reports and the
failed original gate. This is evidence against extrapolating today's observed
+3 clock back into 2024, not proof of either provider's full historical rules.

Additional third-provider access attempts: the Dukascopy public widget's history
endpoint returned HTTP 429; the FXCM 2024 sample endpoint returned HTTP 403.
No retries, access bypass, paid services or messages to providers were used.

New diagnostic hypothesis, declared before requesting/comparing these windows:
MT5 source labels are +2 relative to documented fixed-EST HistData in both
2024-01-09 08:00–20:00 and 2024-07-09 08:00–20:00. These are the same weekday
and source hours one week into each month. Use the same five candidate offsets
and unchanged numerical screening thresholds. These windows were not used in
the first comparisons. Do not tune strategy parameters from this exercise.

If both fresh checks pass, record bounded corroboration and permit a separate
HistData development pilot using its documented fixed UTC-05:00 conversion.
Do not reinterpret or repair the MT5 annual dataset, claim year-wide clock
verification or discard the original failed hypothesis. A failed fresh check
continues to block the dependent stages.

Runtime amendment before fresh price comparisons: MT5 is no longer running.
Both selected windows have all 12 hours in the preserved original H1 capture.
Use these frozen H1 candles for the fresh timestamp checks instead of collecting
new ticks. Report this weaker evidence explicitly. This cannot validate tick
ordering or completeness, and the original raw-file hash must remain recorded.
