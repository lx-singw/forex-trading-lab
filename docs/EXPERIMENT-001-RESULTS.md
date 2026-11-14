# Experiment 001 results — 2026-09-30

**Subsequent data audit failed:** [tick audit 001](TICK-AUDIT-RESULTS.md) found
ticks for missing H1 hours and an adjacent OHLC mismatch. These original results
are preserved for traceability and must not be treated as validated performance.

The unchanged baseline produced **mixed results**, with a loss in development
and a gain in holdout. This is an exploratory OHLC simulation under hypothetical
costs and an unverified historical time mapping. It does not establish a
reliable trading edge or justify activating demo execution.

The [predeclaration](EXPERIMENT-001.md) was written before evaluation. The
timezone amendment was recorded after inspecting timestamp semantics but before
either performance report. No strategy parameters were changed or optimized.

| Measure | 2024 development | 2025 holdout |
|---|---:|---:|
| Completed H1 bars | 6,226 | 6,196 |
| Closed simulated trades | 113 | 98 |
| Net P&L on independent $10,000 starts | -$474.18 | +$288.84 |
| Net return after modeled costs | -4.74% | +2.89% |
| Maximum close-sampled drawdown | 5.54% | 4.27% |
| Winning trades | 29.20% | 38.78% |
| Average winning trade | $42.84 | $45.05 |
| Average losing trade | -$23.60 | -$23.72 |
| Bar exposure | 37.55% | 34.60% |
| Modeled commissions | $88.27 | $56.98 |
| Modeled swap debits | $24.68 | $18.02 |

These partitions start independently; their percentages are not a continuous
two-year compounded return. Drawdown is sampled at candle closes and can
understate intrabar losses. Neither run triggered the daily pause; its behavior
is exercised by adversarial software tests, not demonstrated by these samples.
Trade P&L reconciles with final equity to within $0.000000001 in both reports.

## Data and assumptions

Captured 12,422 EURUSD H1 bid candles from the connected demo terminal, in 27
read-only windows. Two captures produced identical raw data hashes. Retain the
second capture because its metadata includes the clock witness. Converted UTC
coverage is 2024-01-01 22:00 through 2025-12-31 21:00. No incomplete candle was
included. Dates use the provisional `Europe/Helsinki` interpretation.

The current quote label led system UTC by 10,797.8 seconds. Historical EET/EEST
was assumed with European DST; the exact historical mapping has not been
independently verified. The simulator's daily reset remains the predeclared UTC
hypothesis. Source-time uncertainty can change daily limits and swap attribution.

Cost assumptions: 1.2-pip fixed spread, $7/lot round-trip commission, 0.2-pip
adverse market/stop slippage, $3/long-lot and $1.50/short-lot daily swap debits,
Wednesday tripling, simplified 30:1 margin and a 1-lot cap. These are **not**
verified historical terms. The connected account actually reports 1:10 leverage;
the predeclared 30:1 simulation was left unchanged. Current symbol swaps also
differ from the modeled debits; current values do not prove historical costs.
Holding costs and gaps can add losses beyond the stop sizing estimate.

The source bar-spread statistic ranges from 0 to 11.2 pips. It is audited but
not used for entry decisions or fills because it is a within-bar minimum, not
the opening executable spread. Actual spread could therefore materially exceed
the fixed scenario; the positive holdout result is sensitive to unresolved costs.

## Coverage issues

There are 5,098 missing hours between the first and last normalized candle,
including 104 gaps of 48/49 hours consistent with weekly closures. These are
not all classified as data faults. Eight other gaps include holidays and
unexplained weekday interruptions:

| Last observed bar (provisional UTC) | Next observed bar | Missing hours |
|---|---|---:|
| 2024-07-02 09:00 | 2024-07-02 21:00 | 11 |
| 2024-12-24 22:00 | 2024-12-25 22:00 | 23 |
| 2024-12-31 21:00 | 2025-01-01 22:00 | 24 |
| 2025-01-07 02:00 | 2025-01-07 05:00 | 2 |
| 2025-07-03 00:00 | 2025-07-03 09:00 | 8 |
| 2025-07-04 01:00 | 2025-07-04 07:00 | 5 |
| 2025-10-23 17:00 | 2025-10-23 19:00 | 1 |
| 2025-12-24 21:00 | 2025-12-25 22:00 | 24 |

No gaps were filled or removed. New signals expire across gaps; existing
positions are marked at the next observed quote. Missing intragap paths can
hide stop/target events. Resolve unexplained gaps against another source before
treating any result as validation.

## Local artifacts and next step

Ignored market data: `data/mt5-2024-2025-capture-v2/` and
`data/eurusd-2024-2025-v1/`. Ignored reports:

- `reports/experiment-001-manifest.json`
- `reports/experiment-001-development.json`
- `reports/experiment-001-holdout.json`

The manifest embeds parameter, code, data and provenance fingerprints. Report
SHA-256 values at completion:

- Development: `f75ac99a6ed295d0f0078c73dcd7ec0c85d698766022392392d14e3cfa8d1cfb`
- Holdout: `c38ce8ea45cfba0cd13d67e7ff4293760fbee4a3076341e260f3a03180b6152b`

Next: resolve historical time/cost conventions and weekday coverage, then
validate the execution model against bid/ask ticks. The 2025 holdout is now
consumed: do not tune parameters against it and call a rerun unseen evidence.
No order was placed; Algo Trading was observed disabled and was not changed.
