# Research 004 — declared before new comparisons or performance

The 003 candidates remain quarantined. January will be replaced wholesale by
a separately captured MT5 tick month; no HistData/broker splice. July will be
evaluated only if a fresh event-clock check supports a declared interpretation.
No strategy parameters are changed and no 2025 data are used.

1. Check January 11 and July 11 CPI activity against the official BLS 08:30
   Eastern release schedule. Compare source 07:30 and 08:30 for HistData and
   retain counts/ranges at both. Require the 08:30 minute to have at least three
   times the range and twice the ticks of 07:30 on both dates. This tests the
   empirically suggested New York wall clock, not the documented fixed EST rule.
   Event alignment is supporting evidence, not provider-certified timezone data.
2. Capture January MT5 ticks in bounded, guarded two-day chunks with source
   labels UTC+2, preserving raw chunks. Compare reconstructed hourly bid closes
   with every available January HistData hour; report all discrepancies. Require
   at least 95% of overlapping closes within 1 pip and none beyond 5 pips for
   this pilot. Classify missing weekday hours explicitly; do not fill them.
3. If checks pass, build a separate January MT5 dataset and July HistData dataset
   under the empirical New York clock. January source UTC+2 and July source
   UTC-4 apply only to these months, never as a year-wide DST claim. Also retain
   and evaluate July's documented fixed-EST interpretation as clock sensitivity.
4. Freeze these datasets, source code and the existing `tick-pilot-003.json` and
   `tick-pilot-003-adverse.json` assumptions before computing strategy results.
   Evaluate each month independently from $10,000 with separate warmup. Both are
   development samples; report every cost/clock scenario, including losses.

Passing means eligible for a bounded, explicitly provisional development
simulation, not validated profitability, full-market completeness or execution
authorization. Historical broker costs remain assumptions. Do not activate
demo execution on the basis of these short samples. Original 001/003 evidence,
failed hypotheses and normalized files remain unchanged.
