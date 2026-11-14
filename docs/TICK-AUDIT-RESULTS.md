# Tick audit 001 — 2026-09-30

**Market-data validation failed.** The bounded development-period audit found
ticks for all 11 missing July H1 candles and a mismatch in an adjacent candle.
Experiment 001's annual returns remain exploratory, unvalidated results.
Original data, parameters and performance reports were preserved.

The [sampling plan](TICK-AUDIT-PLAN.md) selected diagnostic windows before their
execution analysis. This is not a representative performance sample or a full
tick backtest. All times below are raw source-clock labels, not verified UTC.

| Window | Ticks | Hourly comparison |
|---|---:|---|
| 2024-01-04 19:00 to Jan 5 09:00 | 73,104 | All 14 OHLC candles match |
| 2024-07-02 12:00 to Jul 3 01:00 | 27,856 | 11 missing H1 candles have ticks; one mismatch; one match |
| 2024-03-15 22:00 to Mar 16 00:00 | 899 | One matching candle; neither source has the following hour |

The 101,859 captured ticks contained no invalid bid/ask pairs. Matching two
representations from one terminal does not independently establish feed accuracy
or completeness. The Friday result does not prove historical DST conventions.

## July data failure

Ticks exist for source hours 13 through 23 on July 2, absent from the original
H1 dataset. For the preceding 12:00 candle, the original low/close were
1.07169/1.07202; reconstructed bid ticks give 1.07106/1.07108, differences of
-6.3 and -9.4 pips. Open and high match.

A bounded H1/M1/H1 re-request did not repair the gap. Both H1 requests returned
only two rows. The M1 request returned one candle labeled **2026-06-25 03:53**
for the requested July 2024 window, despite a success API code. The probe now
marks this `invalid_response` with `outside_requested_range`. That candle was
retained only as diagnostic evidence and never imported into research data.
The underlying cause (terminal cache, provider history or another issue) remains
unknown. Do not silently fill or overwrite the frozen dataset.

## Conditional first-trade check

Holding the original first development trade's entry, stop and target fixed,
the first observed boundary crossing was its stop at source label
2024-01-05 08:25:23.837. Bid was 1.09288. Applying the same assumed 0.2-pip
adverse slippage gives 1.09286, about 0.086 pip below the OHLC-modeled exit.
This checks one fixed position's exit ordering only: it does not recompute
signals, entry price, size, costs or net P&L.

The first opening quote arrived 49 ms after the hour, with a 0.1-pip spread;
that quote would pass the 1.5-pip entry filter. Across the whole first-trade
window, median spread was 0.3 pip, p95 3.3 pips and maximum 13 pips. About 5.97%
of tick events exceeded 1.5 pips. This is an event-weighted fraction, not the
fraction of time or trade entries with excessive spreads.

## Verification and artifacts

All **76 Python tests passed**, including 18 tick/probe tests for account guards,
chunk boundaries, same-millisecond ordering, empty versus failed reads, quote
validity, hashes, bid/ask exits, gaps and out-of-window successful API responses.
The terminal reported actual demo mode and Algo Trading off during capture.
No order API, EA deployment or terminal-setting change was used.

Local ignored artifacts:

- `reports/tick-audit-001-summary.json` and the three `tick-audit-001-*.json` audits.
- `data/tick-audit-001-first-trade/`, `data/tick-audit-001-july-gap/` and
  `data/tick-audit-001-dst-friday/`: compressed ticks and capture manifests.
- `data/tick-audit-001-july-rates-reread-v2.json`: validated re-request evidence;
  the first probe is also retained.
- `reports/experiment-001-source.zip`: original Python source, checked against
  the frozen experiment's code fingerprint before adding the tick module.

Capture/report hashes and audit-code fingerprints are recorded. The original
development and holdout reports were verified unchanged.

## Next milestone

Establish a trustworthy development dataset, investigate the history mismatch
and independently check any separate tick-reconstructed dataset. Resolve source
timezone/DST and historical costs before interpreting performance. Then evaluate
the complete strategy with bid/ask ticks, including entry filters and sizing.
The 2025 holdout remains consumed; do not tune against it. Execution stays
unavailable. See the [reproduction workflow](TICK-AUDIT-WORKFLOW.md).
