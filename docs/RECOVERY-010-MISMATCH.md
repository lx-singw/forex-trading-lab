# Follow-up to the preserved 010 candle disagreement

All 91 original chunks have completed. The acquisition audit reports one
OHLC disagreement: raw broker label 2023-07-14 22:00, in chunk 081. Original
tick-built low is 0.7 pip lower and close 0.2 pip lower than the frozen H1
reference; open/high match. This is an explanatory follow-up after that failure,
not a changed gate, selected-date substitution or performance trial.

Before a new request: capture raw labels 2023-07-14 22:00 through July 15 00:00
exclusive into `data/recovery-010/mismatch-repeat`, using the existing demo-only
read-only collector. Compare every tick in this interval with the original
chunk, preserving same-ms order and bid/ask/flags; sequence numbers may differ
only because the new bounded capture starts at zero. Rebuild both original
and repeat candles against the original reference. Record whether a
chronological tick prefix matches the disputed candle. A prefix match is
consistent with truncation but does not prove its cause. Keep the original
data, mismatch and quality failure unchanged. No returns or orders.
