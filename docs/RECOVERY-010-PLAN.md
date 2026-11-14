# Quote recovery 010 — declared before new tick capture

This is a separate data diagnostic, not an amendment to history 009. Preserve
all failed reviews and frozen selection rules. No strategy returns, orders,
terminal settings changes or normalization into simulator input in this stage.

First request raw MT5 labels 2023-07-11 15:00 through 2023-07-12 03:00
exclusive, using the existing guarded read-only collector. These are the twelve
hours corresponding to the failed history-009 window under its observed +7h
relative mapping. The labels are not certified UTC. Use a new folder under
`data/recovery-010`, and the original `history-009-mt5-reference/rates.csv`.

Before expansion require all twelve hours to contain valid chronological
bid/ask quotes, no API errors, all twelve reference candles present, and every
rebuilt bid OHLC within 0.05 pip of that reference. Preserve equal-millisecond
events and actual spreads. Do not interpolate, sort, replace an empty capture,
change the day, or relax a failed gate. Same-feed agreement verifies this
reconstruction, not independent historical truth or absolute UTC.

If this screen passes, acquire a separate continuous MT5 tick source for raw
labels 2023-02-01 through 2023-08-01 exclusive in disjoint chunks of at most
48 hours, with requests of at most six hours. This addresses the six defective
months without splicing alternative ticks into HistData. Record each request,
hash, empty interval and failure; resume only completed hash-verified chunks.
Stop on API/guard failures and preserve partial files. Recheck the actual demo
account around every request; do not log identifiers or credentials.

Review every captured hour against the previously acquired raw H1 reference.
Report reference-only hours, tick-only hours, empty hours and OHLC mismatches
individually. Record quote gaps and month/chunk seams, including same-ms events.
An empty hour is unclassified, not automatically a market closure. Report all
failures; any mismatch remains a blocker for automatic data eligibility.

This plan contains no strategy or cost choices. The previously frozen five
candidates and chronological selection gates remain unchanged. The new source
needs independent clock/coverage evidence before performance evaluation.
